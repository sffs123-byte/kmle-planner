#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const crypto = require('node:crypto');
const { DatabaseSync } = require('node:sqlite');

const ROOT = __dirname;
const HOST = process.env.PLANNER_LOCAL_HOST || '127.0.0.1';
const PORT = Number(process.env.PLANNER_LOCAL_PORT || 8796);
const DB_PATH = process.env.PLANNER_LOCAL_DB_PATH || path.join(ROOT, '.local', 'planner-local.sqlite');
const AUTH_TOKEN = (process.env.PLANNER_LOCAL_TOKEN || '').trim();
const USER_ID = process.env.PLANNER_LOCAL_USER_ID || 'gangryeol-main';
const SEED_STATE_PATH = process.env.PLANNER_LOCAL_SEED_STATE || path.join(ROOT, 'data', 'planner_state_cardiology_content_handoff_v2_import.json');

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.mjs', 'text/javascript; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'],
  ['.jpeg', 'image/jpeg'],
  ['.gif', 'image/gif'],
  ['.svg', 'image/svg+xml'],
  ['.ico', 'image/x-icon'],
  ['.webp', 'image/webp'],
  ['.pdf', 'application/pdf'],
  ['.txt', 'text/plain; charset=utf-8'],
  ['.md', 'text/markdown; charset=utf-8']
]);

fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
const db = new DatabaseSync(DB_PATH);
db.exec(`
  PRAGMA journal_mode = WAL;
  PRAGMA busy_timeout = 5000;
  CREATE TABLE IF NOT EXISTS planner_user_state (
    user_id TEXT PRIMARY KEY,
    state_json TEXT NOT NULL,
    state_version TEXT NOT NULL,
    updated_by TEXT,
    updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS planner_sync_slots (
    sync_code TEXT PRIMARY KEY,
    state_json TEXT NOT NULL,
    state_version TEXT NOT NULL,
    updated_by TEXT,
    updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    state_json TEXT NOT NULL,
    state_version TEXT,
    updated_by TEXT,
    updated_at TEXT NOT NULL,
    captured_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
  );
`);

const clients = new Set();

function nowIso() {
  return new Date().toISOString();
}

function safeJsonParse(raw, fallback = null) {
  try { return raw ? JSON.parse(raw) : fallback; } catch { return fallback; }
}

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET,POST,OPTIONS',
    'access-control-allow-headers': 'content-type,x-planner-local-token'
  });
  res.end(body);
}

function sendText(res, status, text, type = 'text/plain; charset=utf-8') {
  res.writeHead(status, { 'content-type': type, 'cache-control': 'no-store' });
  res.end(text);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let totalBytes = 0;
    req.on('data', (chunk) => {
      const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      chunks.push(buffer);
      totalBytes += buffer.length;
      if (totalBytes > 20 * 1024 * 1024) {
        reject(new Error('request body too large'));
        req.destroy();
      }
    });
    req.on('end', () => resolve(safeJsonParse(Buffer.concat(chunks).toString('utf8'), {})));
    req.on('error', reject);
  });
}

function tokenFrom(req, url) {
  return req.headers['x-planner-local-token'] || url.searchParams.get('token') || url.searchParams.get('localToken') || '';
}

function authorized(req, url) {
  if (!AUTH_TOKEN) return true;
  const supplied = Buffer.from(String(tokenFrom(req, url)));
  const expected = Buffer.from(AUTH_TOKEN);
  if (supplied.length !== expected.length) return false;
  return crypto.timingSafeEqual(supplied, expected);
}

function requireAuth(req, res, url) {
  if (authorized(req, url)) return true;
  sendJson(res, 401, { ok: false, error: 'unauthorized' });
  return false;
}

function getUserState(userId) {
  const row = db.prepare('SELECT user_id, state_json, state_version, updated_by, updated_at FROM planner_user_state WHERE user_id = ?').get(userId);
  if (!row) return null;
  return {
    user_id: row.user_id,
    state_json: safeJsonParse(row.state_json, {}),
    state_version: row.state_version,
    updated_by: row.updated_by,
    updated_at: row.updated_at
  };
}

function pediatricsAssignmentCount(stateJson) {
  return Number(stateJson?.clerkshipBundles?.['pediatrics-2026-05-track-bca']?.assignments?.length || 0);
}

function replacementCharCount(stateJson) {
  return (JSON.stringify(stateJson || {}).match(/�/g) || []).length;
}

function setUserState({ userId, stateJson, stateVersion = 'planner-user-state.v1', updatedBy = 'unknown', updatedAt = nowIso() }) {
  const existing = getUserState(userId);
  const existingPedsAssignments = pediatricsAssignmentCount(existing?.state_json);
  const nextPedsAssignments = pediatricsAssignmentCount(stateJson || {});
  const trustedOpenClawWrite = String(updatedBy || '').startsWith('openclaw-main-peds-schedule-patch')
    || String(updatedBy || '').startsWith('openclaw-main-peds-clean-rebuild');
  if (existingPedsAssignments >= 20 && nextPedsAssignments < existingPedsAssignments && !trustedOpenClawWrite) {
    return { ...existing, ignored_stale_pediatrics_push: true, ignored_updated_by: updatedBy, ignored_updated_at: updatedAt };
  }
  const existingReplacementChars = replacementCharCount(existing?.state_json);
  const nextReplacementChars = replacementCharCount(stateJson || {});
  if (existing && nextReplacementChars > existingReplacementChars && nextReplacementChars > 0 && !trustedOpenClawWrite) {
    return { ...existing, ignored_replacement_char_push: true, ignored_updated_by: updatedBy, ignored_updated_at: updatedAt };
  }
  const stateRaw = JSON.stringify(stateJson || {});
  db.prepare(`
    INSERT INTO planner_user_state (user_id, state_json, state_version, updated_by, updated_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
      state_json=excluded.state_json,
      state_version=excluded.state_version,
      updated_by=excluded.updated_by,
      updated_at=excluded.updated_at
    WHERE planner_user_state.updated_at <= excluded.updated_at
  `).run(userId, stateRaw, stateVersion, updatedBy, updatedAt);
  db.prepare('INSERT INTO state_history (scope, key, state_json, state_version, updated_by, updated_at) VALUES (?, ?, ?, ?, ?, ?)')
    .run('user', userId, stateRaw, stateVersion, updatedBy, updatedAt);
  broadcast({ type: 'planner_user_state', user_id: userId, updated_by: updatedBy, updated_at: updatedAt });
  return getUserState(userId);
}

function getSyncSlot(syncCode) {
  const row = db.prepare('SELECT sync_code, state_json, state_version, updated_by, updated_at FROM planner_sync_slots WHERE sync_code = ?').get(syncCode);
  if (!row) return null;
  return {
    sync_code: row.sync_code,
    state_json: safeJsonParse(row.state_json, {}),
    state_version: row.state_version,
    updated_by: row.updated_by,
    updated_at: row.updated_at
  };
}

function setSyncSlot({ syncCode, stateJson, stateVersion = 'kmlePlannerState.v2', updatedBy = 'unknown', updatedAt = nowIso() }) {
  const stateRaw = JSON.stringify(stateJson || {});
  db.prepare(`
    INSERT INTO planner_sync_slots (sync_code, state_json, state_version, updated_by, updated_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(sync_code) DO UPDATE SET
      state_json=excluded.state_json,
      state_version=excluded.state_version,
      updated_by=excluded.updated_by,
      updated_at=excluded.updated_at
    WHERE planner_sync_slots.updated_at <= excluded.updated_at
  `).run(syncCode, stateRaw, stateVersion, updatedBy, updatedAt);
  db.prepare('INSERT INTO state_history (scope, key, state_json, state_version, updated_by, updated_at) VALUES (?, ?, ?, ?, ?, ?)')
    .run('sync', syncCode, stateRaw, stateVersion, updatedBy, updatedAt);
  broadcast({ type: 'planner_sync_slot', sync_code: syncCode, updated_by: updatedBy, updated_at: updatedAt });
  return getSyncSlot(syncCode);
}

function seedIfEmpty() {
  const existing = getUserState(USER_ID);
  if (existing) return;
  if (!fs.existsSync(SEED_STATE_PATH)) return;
  const seed = safeJsonParse(fs.readFileSync(SEED_STATE_PATH, 'utf8'), null);
  if (!seed) return;
  const stateJson = seed.plannerState || seed;
  setUserState({
    userId: USER_ID,
    stateJson,
    stateVersion: 'planner-user-state.v1',
    updatedBy: 'local-seed',
    updatedAt: nowIso()
  });
  console.log(`Seeded ${USER_ID} from ${SEED_STATE_PATH}`);
}

function broadcast(payload) {
  const body = `event: update\ndata: ${JSON.stringify(payload)}\n\n`;
  for (const res of [...clients]) {
    try { res.write(body); } catch { clients.delete(res); }
  }
}

function serveStatic(req, res, url) {
  let pathname = decodeURIComponent(url.pathname);
  if (pathname === '/') pathname = '/index.html';
  const filePath = path.resolve(ROOT, `.${pathname}`);
  if (!filePath.startsWith(ROOT)) {
    sendText(res, 403, 'Forbidden');
    return;
  }
  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) {
      sendText(res, 404, 'Not found');
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      'content-type': MIME.get(ext) || 'application/octet-stream',
      'cache-control': ext === '.html' || ext === '.js' ? 'no-store' : 'public, max-age=300'
    });
    fs.createReadStream(filePath).pipe(res);
  });
}

async function handleApi(req, res, url) {
  if (req.method === 'OPTIONS') {
    sendJson(res, 204, {});
    return;
  }

  if (url.pathname === '/api/health') {
    sendJson(res, 200, {
      ok: true,
      mode: 'kmle-planner-local-db',
      localDb: true,
      dbPath: DB_PATH,
      userId: USER_ID,
      authRequired: Boolean(AUTH_TOKEN),
      now: nowIso()
    });
    return;
  }

  if (url.pathname === '/api/events') {
    if (!requireAuth(req, res, url)) return;
    res.writeHead(200, {
      'content-type': 'text/event-stream; charset=utf-8',
      'cache-control': 'no-store',
      connection: 'keep-alive',
      'access-control-allow-origin': '*'
    });
    res.write(`event: hello\ndata: ${JSON.stringify({ ok: true, now: nowIso() })}\n\n`);
    clients.add(res);
    req.on('close', () => clients.delete(res));
    return;
  }

  if (!url.pathname.startsWith('/api/')) return false;
  if (!requireAuth(req, res, url)) return true;

  try {
    const body = req.method === 'GET' ? {} : await readBody(req);

    if (url.pathname === '/api/planner-user-state/pull') {
      const userId = body.user_id || url.searchParams.get('user_id') || USER_ID;
      sendJson(res, 200, { ok: true, row: getUserState(userId) });
      return true;
    }

    if (url.pathname === '/api/planner-user-state/push') {
      const row = setUserState({
        userId: body.user_id || USER_ID,
        stateJson: body.state_json || {},
        stateVersion: body.state_version || 'planner-user-state.v1',
        updatedBy: body.updated_by || 'unknown',
        updatedAt: body.updated_at || nowIso()
      });
      sendJson(res, 200, { ok: true, row });
      return true;
    }

    if (url.pathname === '/api/planner-sync/pull') {
      const syncCode = body.sync_code || url.searchParams.get('sync_code') || '';
      sendJson(res, 200, { ok: true, row: syncCode ? getSyncSlot(syncCode) : null });
      return true;
    }

    if (url.pathname === '/api/planner-sync/push') {
      const syncCode = body.sync_code || '';
      if (!syncCode) {
        sendJson(res, 400, { ok: false, error: 'sync_code required' });
        return true;
      }
      const row = setSyncSlot({
        syncCode,
        stateJson: body.state_json || {},
        stateVersion: body.state_version || 'kmlePlannerState.v2',
        updatedBy: body.updated_by || 'unknown',
        updatedAt: body.updated_at || nowIso()
      });
      sendJson(res, 200, { ok: true, row });
      return true;
    }

    if (url.pathname === '/api/export') {
      const rows = db.prepare('SELECT user_id, state_json, state_version, updated_by, updated_at FROM planner_user_state ORDER BY user_id').all();
      sendJson(res, 200, { ok: true, rows: rows.map((row) => ({ ...row, state_json: safeJsonParse(row.state_json, {}) })) });
      return true;
    }

    sendJson(res, 404, { ok: false, error: 'unknown api path' });
    return true;
  } catch (error) {
    sendJson(res, 500, { ok: false, error: error.message || String(error) });
    return true;
  }
}

seedIfEmpty();

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || `${HOST}:${PORT}`}`);
  if (url.pathname.startsWith('/api/')) {
    const handled = await handleApi(req, res, url);
    if (handled !== false) return;
  }
  serveStatic(req, res, url);
});

server.listen(PORT, HOST, () => {
  console.log(`KMLE Planner local DB server running: http://${HOST}:${PORT}/`);
  console.log(`SQLite DB: ${DB_PATH}`);
  console.log(AUTH_TOKEN ? 'Auth token: required via ?localToken=... or x-planner-local-token' : 'Auth token: disabled');
});
