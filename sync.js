const STORAGE_KEY = 'kmlePlannerState.v2';
const CONFIG_KEY = 'kmlePlannerSyncCodeConfig.v1';
const META_KEY = 'kmlePlannerSyncMeta.v3';
const PLANNER_STATE_VERSION = 'kmlePlannerState.v2';
const PLANNER_USER_STATE_VERSION = 'planner-user-state.v1';
const PLANNER_USER_ID = 'gangryeol-main';

const urlParams = new URLSearchParams(window.location.search);
const isStandaloneMode = urlParams.get('mode') === 'standalone' || urlParams.get('guest') === 'true';
const LOCAL_TOKEN_KEY = 'kmlePlannerLocalToken.v1';
const LOCAL_API_BASE_KEY = 'kmlePlannerLocalApiBase.v1';
const LOCAL_DB_REQUIRED_KEY = 'kmlePlannerLocalDbRequired.v1';
const DEFAULT_LOCAL_API_BASE = '';
const urlLocalToken = urlParams.get('localToken') || urlParams.get('token') || '';
const urlLocalApiBase = urlParams.get('localApiBase') || urlParams.get('localApi') || '';
const urlLocalDbMode = urlParams.get('localDb') || '';
if (urlLocalToken) localStorage.setItem(LOCAL_TOKEN_KEY, urlLocalToken);
if (urlLocalApiBase) localStorage.setItem(LOCAL_API_BASE_KEY, urlLocalApiBase.replace(/\/+$/, ''));
if (urlLocalDbMode) localStorage.setItem(LOCAL_DB_REQUIRED_KEY, urlLocalDbMode === 'off' || urlLocalDbMode === '0' ? 'false' : 'true');

const defaultConfig = {
  supabaseUrl: 'https://fqvmubjivjyohrwqfbdk.supabase.co',
  supabaseAnonKey: 'sb_publishable_x9mnaYjAMbFGGBacRbWmww_3GPRftzR',
  syncCode: '',
  autoSync: !isStandaloneMode
};

function generateRandomCode() {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  const raw = Array.from(bytes, (b) => alphabet[b % alphabet.length]).join('');
  return raw.match(/.{1,4}/g).join('-');
}

function sanitizeSyncCode(value) {
  const compact = String(value || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (!compact) return '';
  return compact.match(/.{1,4}/g).join('-');
}

function getOrCreateDeviceId() {
  const key = 'kmlePlannerDeviceId.v1';
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  const created = globalThis.crypto?.randomUUID?.() || `device-${Math.random().toString(36).slice(2, 10)}`;
  localStorage.setItem(key, created);
  return created;
}

function defaultMeta() {
  return {
    deviceId: getOrCreateDeviceId(),
    lastHash: '',
    lastLocalChangeAt: 0,
    pendingUserStateHash: '',
    pendingLegacyHash: '',
    lastUploadedAt: 0,
    lastRemoteAppliedAt: 0,
    lastRemoteSeenAt: 0,
    lastUserStateUploadedAt: 0,
    lastUserStateAppliedAt: 0,
    lastUserStateSeenAt: 0,
    lastStatus: '로컬 전용 모드',
    lastStatusAt: 0
  };
}

function readJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? { ...fallback, ...JSON.parse(raw) } : { ...fallback };
  } catch {
    return { ...fallback };
  }
}

function writeJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function normalizeConfig(config) {
  return {
    ...defaultConfig,
    ...config,
    supabaseUrl: config?.supabaseUrl?.trim?.() ? config.supabaseUrl.trim() : defaultConfig.supabaseUrl,
    supabaseAnonKey: config?.supabaseAnonKey?.trim?.() ? config.supabaseAnonKey.trim() : defaultConfig.supabaseAnonKey,
    syncCode: sanitizeSyncCode(config?.syncCode || ''),
    autoSync: config?.autoSync !== false
  };
}

function readConfig() {
  const config = normalizeConfig(readJSON(CONFIG_KEY, defaultConfig));
  saveConfig(config);
  return config;
}

function saveConfig(config) {
  writeJSON(CONFIG_KEY, normalizeConfig(config));
}

function readMeta() {
  return readJSON(META_KEY, defaultMeta());
}

function saveMeta(meta) {
  writeJSON(META_KEY, meta);
}

function hashString(value) {
  let hash = 5381;
  for (let i = 0; i < value.length; i += 1) {
    hash = ((hash << 5) + hash) + value.charCodeAt(i);
    hash |= 0;
  }
  return String(hash >>> 0);
}

function stableSerialize(value) {
  if (value === null || typeof value !== 'object') {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableSerialize(item)).join(',')}]`;
  }
  const keys = Object.keys(value).sort();
  return `{${keys.map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`).join(',')}}`;
}

function hashStateRaw(raw) {
  if (!raw) return hashString('');
  try {
    return hashString(stableSerialize(JSON.parse(raw)));
  } catch {
    return hashString(raw);
  }
}

function hashStateObject(obj) {
  return hashString(stableSerialize(obj));
}

function getRawPlannerState() {
  return localStorage.getItem(STORAGE_KEY) || '';
}

function setRawPlannerState(raw) {
  localStorage.setItem(STORAGE_KEY, raw);
}

function nowIso() {
  return new Date().toISOString();
}

function formatDateTime(value) {
  if (!value) return '없음';
  try {
    return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value));
  } catch {
    return value;
  }
}

function maskCode(code) {
  if (!code) return '없음';
  const parts = code.split('-');
  if (parts.length < 2) return code;
  return `${parts[0]}-••••-••••-${parts[parts.length - 1]}`;
}

const ui = {
  statusPill: null,
  modal: null,
  statusText: null,
  syncCodeInput: null,
  autoSyncInput: null,
  sessionText: null,
  openButton: null,
  saveButton: null,
  generateButton: null,
  copyButton: null,
  pushButton: null,
  pullButton: null,
  clearButton: null
};

let supabase = null;
let createSupabaseClient = null;
let localDbMode = false;
let localEventSource = null;
let pollingTimer = null;
let remoteTimer = null;
let realtimeChannel = null;
let immediateSyncTimer = null;
let immediateSyncReason = '';
let localHash = hashStateRaw(getRawPlannerState());
let syncing = false;

function injectStyles() {
  if (document.getElementById('planner-sync-style')) return;
  const style = document.createElement('style');
  style.id = 'planner-sync-style';
  style.textContent = `
    .sync-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 11px 14px;
      border-radius: 999px;
      border: 1px solid var(--line, #dbe4f0);
      background: rgba(255,255,255,0.9);
      color: var(--text, #18212f);
      font-weight: 600;
      font-size: 13px;
    }
    .sync-pill-dot { width: 9px; height: 9px; border-radius: 999px; background: #94a3b8; flex: none; }
    .sync-pill.connected .sync-pill-dot { background: #16a34a; }
    .sync-pill.pending .sync-pill-dot { background: #d97706; }
    .sync-pill.error .sync-pill-dot { background: #dc2626; }
    .sync-modal {
      position: fixed; inset: 0; display: none; align-items: center; justify-content: center;
      padding: 20px; background: rgba(15, 23, 42, 0.45); z-index: 999;
    }
    .sync-modal.show { display: flex; }
    .sync-card {
      width: min(680px, 100%); max-height: min(90vh, 920px); overflow: auto;
      background: rgba(255,255,255,0.96); border: 1px solid #dbe4f0; border-radius: 24px;
      box-shadow: 0 18px 45px rgba(27, 40, 69, 0.18); padding: 24px; color: #18212f;
    }
    .sync-grid { display: grid; gap: 14px; margin-top: 18px; }
    .sync-field { display: grid; gap: 8px; }
    .sync-field label { font-size: 13px; color: #64748b; font-weight: 700; }
    .sync-field input {
      width: 100%; border: 1px solid #dbe4f0; border-radius: 14px; padding: 12px 14px;
      font: inherit; background: #fff; color: #18212f;
    }
    .sync-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
    .sync-note { margin-top: 14px; color: #64748b; font-size: 13px; line-height: 1.65; white-space: pre-line; }
    .sync-block {
      margin-top: 16px; padding: 16px; border-radius: 18px; border: 1px solid #dbe4f0; background: #f8fbff;
    }
    .sync-status-text { white-space: pre-line; line-height: 1.6; color: #334155; font-size: 13px; margin-top: 10px; }
    .sync-inline { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
    .sync-code-preview {
      display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 12px;
      background: #eef4ff; color: #1d4ed8; font-weight: 700; letter-spacing: 0.06em;
    }
  `;
  document.head.appendChild(style);
}

function injectUI() {
  injectStyles();
  if (ui.openButton) return;

  const topActions = document.querySelector('.top-actions');
  const heroSide = document.getElementById('heroStats')?.parentElement;
  if (!topActions || !heroSide) return;

  const openButton = document.createElement('button');
  openButton.className = 'btn btn-ghost';
  openButton.id = 'syncConfigBtn';
  openButton.textContent = '자동 동기화';
  topActions.appendChild(openButton);

  const statusPill = document.createElement('div');
  statusPill.className = 'sync-pill';
  statusPill.innerHTML = isStandaloneMode ? '<span class="sync-pill-dot"></span><span>공유용 모드 (로컬저장)</span>' : '<span class="sync-pill-dot"></span><span>로컬 전용 모드</span>';
  heroSide.appendChild(statusPill);

  const modal = document.createElement('div');
  modal.className = 'sync-modal';
  modal.id = 'syncModal';
  modal.innerHTML = `
    <div class="sync-card">
      <div class="sync-inline">
        <div>
          <div class="panel-title" style="font-size:24px;font-weight:800;">자동 동기화 설정</div>
          <div class="panel-subtitle" style="margin-top:6px;color:#64748b;">이메일 로그인 대신 개인용 sync code 하나를 공유해서 맥과 iPad 상태를 맞춘다.</div>
        </div>
        <button class="btn btn-ghost btn-small" id="syncCloseBtn">닫기</button>
      </div>

      <div class="sync-grid">
        <div class="sync-field">
          <label for="syncCodeInput">동기화 코드</label>
          <input id="syncCodeInput" placeholder="예: Q7RM-4K2P-B8XN-6JHT" autocapitalize="characters" />
        </div>
        <label style="display:flex; gap:10px; align-items:center; color:#334155; font-size:14px;">
          <input id="syncAutoMode" type="checkbox" checked />
          자동 동기화 켜기 (상태가 바뀌면 자동 업로드, 다른 기기 변경도 자동 확인)
        </label>
      </div>

      <div class="sync-actions">
        <button class="btn btn-primary" id="syncSaveBtn">설정 저장</button>
        <button class="btn btn-secondary" id="syncGenerateBtn">새 동기화 코드 생성</button>
        <button class="btn btn-ghost" id="syncCopyBtn">코드 복사</button>
        <button class="btn btn-ghost" id="syncPushBtn">지금 밀어넣기</button>
        <button class="btn btn-ghost" id="syncPullBtn">지금 다시 받기</button>
        <button class="btn btn-danger" id="syncClearBtn">연결 해제</button>
      </div>

      <div class="sync-block">
        <div style="font-weight:700;">현재 상태</div>
        <div id="syncSessionText" class="sync-note"></div>
        <div id="syncStatusText" class="sync-status-text"></div>
      </div>

      <div class="sync-block">
        <div style="font-weight:700;">앱 새로받기 / 캐시 정리</div>
        <div id="syncAppInfoText" class="sync-note"></div>
        <div class="sync-actions" style="margin-top:10px;">
          <button class="btn btn-ghost" id="syncSoftRefreshBtn">앱 새로고침</button>
          <button class="btn btn-ghost" id="syncHardRefreshBtn">캐시 초기화 후 새로받기</button>
        </div>
      </div>

      <div class="sync-note">추천 사용 순서\n1. 맥에서 새 동기화 코드 생성\n2. 지금 밀어넣기\n3. iPad에서 같은 코드를 입력하고 설정 저장\n4. 지금 다시 받기\n5. 홈화면 앱이면 안 바뀔 때 캐시 초기화 후 새로받기\n\n초기 운영은 맥을 정본(primary writer)으로 두는 것이 안전하다.</div>
    </div>
  `;
  document.body.appendChild(modal);

  ui.openButton = openButton;
  ui.statusPill = statusPill;
  ui.modal = modal;
  ui.statusText = modal.querySelector('#syncStatusText');
  ui.sessionText = modal.querySelector('#syncSessionText');
  ui.appInfoText = modal.querySelector('#syncAppInfoText');
  ui.syncCodeInput = modal.querySelector('#syncCodeInput');
  ui.autoSyncInput = modal.querySelector('#syncAutoMode');
  ui.saveButton = modal.querySelector('#syncSaveBtn');
  ui.generateButton = modal.querySelector('#syncGenerateBtn');
  ui.copyButton = modal.querySelector('#syncCopyBtn');
  ui.pushButton = modal.querySelector('#syncPushBtn');
  ui.pullButton = modal.querySelector('#syncPullBtn');
  ui.clearButton = modal.querySelector('#syncClearBtn');
  ui.softRefreshButton = modal.querySelector('#syncSoftRefreshBtn');
  ui.hardRefreshButton = modal.querySelector('#syncHardRefreshBtn');

  openButton.addEventListener('click', () => ui.modal.classList.add('show'));
  modal.querySelector('#syncCloseBtn').addEventListener('click', () => ui.modal.classList.remove('show'));
  modal.addEventListener('click', (event) => {
    if (event.target === modal) ui.modal.classList.remove('show');
  });

  ui.syncCodeInput.addEventListener('input', () => {
    ui.syncCodeInput.value = sanitizeSyncCode(ui.syncCodeInput.value);
  });

  ui.saveButton.addEventListener('click', async () => {
    saveConfig({ syncCode: ui.syncCodeInput.value, autoSync: Boolean(ui.autoSyncInput.checked) });
    setStatus('동기화 코드 저장 완료. 연결 상태를 다시 확인한다.', 'pending');
    await initializeSupabase();
  });

  ui.generateButton.addEventListener('click', async () => {
    const code = generateRandomCode();
    ui.syncCodeInput.value = code;
    saveConfig({ syncCode: code, autoSync: Boolean(ui.autoSyncInput.checked) });
    renderConfigToUI();
    setStatus('새 동기화 코드를 만들었다. 맥에서 정본을 밀어넣고, iPad에는 같은 코드를 넣으면 된다.', 'pending');
    try {
      await navigator.clipboard.writeText(code);
      setStatus(`새 동기화 코드 생성 완료. 클립보드에 복사했다: ${code}`, 'connected');
    } catch {
      setStatus(`새 동기화 코드 생성 완료: ${code}`, 'connected');
    }
    await initializeSupabase();
  });

  ui.copyButton.addEventListener('click', async () => {
    const code = sanitizeSyncCode(ui.syncCodeInput.value || readConfig().syncCode);
    if (!code) {
      setStatus('복사할 동기화 코드가 없다. 먼저 새 코드를 만들거나 입력해줘.', 'error');
      return;
    }
    try {
      await navigator.clipboard.writeText(code);
      setStatus('동기화 코드를 클립보드에 복사했다.', 'connected');
    } catch {
      setStatus(`클립보드 복사가 안 되면 이 코드를 직접 써줘: ${code}`, 'pending');
    }
  });

  ui.softRefreshButton.addEventListener('click', () => {
    if (typeof window.__kmlePlannerSoftRefresh === 'function') {
      void window.__kmlePlannerSoftRefresh();
    }
  });

  ui.hardRefreshButton.addEventListener('click', () => {
    if (typeof window.__kmlePlannerHardRefresh === 'function') {
      void window.__kmlePlannerHardRefresh();
    }
  });

  ui.pushButton.addEventListener('click', async () => {
    await pushLocalState('수동 업로드');
  });

  ui.pullButton.addEventListener('click', async () => {
    await pullRemoteState({ force: true, reason: '수동 새로받기' });
  });

  ui.clearButton.addEventListener('click', async () => {
    saveConfig({ syncCode: '', autoSync: Boolean(ui.autoSyncInput.checked) });
    renderConfigToUI();
    stopLoops();
    setStatus('동기화 코드 연결을 해제했다. 현재는 로컬 전용 모드다.', 'pending');
    renderSessionText();
  });
}

function renderConfigToUI() {
  if (!ui.syncCodeInput) return;
  const config = readConfig();
  ui.syncCodeInput.value = config.syncCode || '';
  ui.autoSyncInput.checked = config.autoSync !== false;
}

function renderSessionText() {
  if (!ui.sessionText) return;
  const config = readConfig();
  const meta = readMeta();
  const appInfo = typeof window.__kmlePlannerAppInfo === 'function' ? window.__kmlePlannerAppInfo() : null;

  const lines = isStandaloneMode ? [
    `mode: Standalone (Guest)`,
    `device: ${meta.deviceId}`,
    `저장위치: 이 기기 브라우저 (LocalStorage)`,
    `동기화: 비활성화됨 (개인 정보 보호)`
  ] : [
    `user state: ${PLANNER_USER_ID}`,
    `device: ${meta.deviceId}`,
    `마지막 로컬 변경: ${formatDateTime(meta.lastLocalChangeAt)}`,
    `마지막 user state 업로드: ${formatDateTime(meta.lastUserStateUploadedAt)}`,
    `마지막 user state 반영: ${formatDateTime(meta.lastUserStateAppliedAt)}`,
    `마지막 user state 확인: ${formatDateTime(meta.lastUserStateSeenAt)}`,
    `user state 업로드 대기: ${meta.pendingUserStateHash ? '있음' : '없음'}`,
    `legacy 업로드 대기: ${meta.pendingLegacyHash ? '있음' : '없음'}`,
    config.syncCode ? `legacy sync code: ${maskCode(config.syncCode)}` : 'legacy sync code: 없음'
  ];

  ui.sessionText.textContent = lines.join('\n');

  if (ui.appInfoText) {
    ui.appInfoText.textContent = [
      appInfo ? `앱 모드: ${appInfo.modeLabel}` : '앱 모드: 확인 불가',
      appInfo ? `현재 버전: ${appInfo.versionLabel}` : '현재 버전: 확인 불가',
      `Local DB API: ${getLocalApiBase() || 'same-origin'}`,
      '홈화면 앱에서 변경이 늦게 반영되면 캐시 초기화 후 새로받기를 먼저 시도해줘.'
    ].join('\n');
  }
}

function stateStoreLabel() {
  return localDbMode ? 'Local DB' : 'Supabase';
}

function setStatus(message, tone = 'default') {
  const meta = readMeta();
  meta.lastStatus = message;
  meta.lastStatusAt = nowIso();
  saveMeta(meta);

  if (ui.statusText) {
    ui.statusText.textContent = `${message}\n상태 갱신: ${formatDateTime(meta.lastStatusAt)}`;
  }
  if (ui.statusPill) {
    const label = ui.statusPill.querySelector('span:last-child');
    label.textContent = message.length > 34 ? `${message.slice(0, 34)}…` : message;
    ui.statusPill.classList.remove('connected', 'pending', 'error');
    if (tone === 'connected') ui.statusPill.classList.add('connected');
    if (tone === 'pending') ui.statusPill.classList.add('pending');
    if (tone === 'error') ui.statusPill.classList.add('error');
  }
}


function getLocalApiBase() {
  const raw = localStorage.getItem(LOCAL_API_BASE_KEY) || DEFAULT_LOCAL_API_BASE || '';
  return raw.replace(/\/+$/, '');
}

function localDbRequired() {
  return localStorage.getItem(LOCAL_DB_REQUIRED_KEY) === 'true';
}

function localApiHeaders() {
  const token = localStorage.getItem(LOCAL_TOKEN_KEY) || '';
  return token ? { 'x-planner-local-token': token } : {};
}

function localApiUrl(path) {
  const base = getLocalApiBase();
  const rawPath = path.startsWith('/') ? path : `/${path}`;
  const url = base ? `${base}${rawPath}` : rawPath;
  const token = localStorage.getItem(LOCAL_TOKEN_KEY) || '';
  if (!token) return url;
  const sep = url.includes('?') ? '&' : '?';
  return `${url}${sep}localToken=${encodeURIComponent(token)}`;
}

async function requestLocalApi(path, payload = {}) {
  const response = await fetch(localApiUrl(path), {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...localApiHeaders() },
    body: JSON.stringify(payload),
    cache: 'no-store'
  });
  const json = await response.json().catch(() => ({}));
  if (!response.ok || json?.ok === false) throw new Error(json?.error || `local API ${response.status}`);
  return json;
}

async function detectLocalApi() {
  if (isStandaloneMode) return false;
  const host = location.hostname || '';
  const hasLocalToken = Boolean(localStorage.getItem(LOCAL_TOKEN_KEY));
  const hasLocalApiBase = Boolean(getLocalApiBase());
  const isLoopback = host === 'localhost' || host === '127.0.0.1' || host === '::1';
  if (!hasLocalToken && !isLoopback && !hasLocalApiBase) return false;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 1200);
    const response = await fetch(localApiUrl('/api/health'), { cache: 'no-store', signal: controller.signal, headers: localApiHeaders() });
    clearTimeout(timer);
    if (!response.ok) return false;
    const data = await response.json();
    if (data?.authRequired && !localStorage.getItem(LOCAL_TOKEN_KEY)) return false;
    return data?.ok === true && data?.localDb === true;
  } catch {
    return false;
  }
}

async function getSupabaseCreateClient() {
  if (!createSupabaseClient) {
    const mod = await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
    createSupabaseClient = mod.createClient;
  }
  return createSupabaseClient;
}

async function initializeSupabase() {
  if (isStandaloneMode) {
    supabase = null;
    stopLoops();
    setStatus('공유용 Standalone 모드 (로컬 저장)', 'connected');
    return;
  }
  const config = readConfig();
  renderConfigToUI();

  if (await detectLocalApi()) {
    localDbMode = true;
    supabase = null;
    renderSessionText();
    kickOffLoops();
    setStatus('Local DB 연결됨. Mac mini SQLite 상태를 확인 중이다.', 'connected');
    await pullPlannerUserState({ reason: '초기 확인' });
    if (config.syncCode) await pullRemoteState({ reason: 'legacy 초기 확인' });
    return;
  }

  localDbMode = false;

  if (localDbRequired()) {
    supabase = null;
    renderSessionText();
    setStatus('Local DB 연결이 필요하다. local DB 서버 URL/token을 확인해줘.', 'error');
    stopLoops();
    return;
  }

  if (!config.supabaseUrl || !config.supabaseAnonKey) {
    supabase = null;
    renderSessionText();
    setStatus('Supabase 연결값이 비어 있다. 배포본이 최신인지 확인해줘.', 'error');
    stopLoops();
    return;
  }

  if (!supabase || supabase.__plannerUrl !== config.supabaseUrl || supabase.__plannerKey !== config.supabaseAnonKey) {
    const createClient = await getSupabaseCreateClient();
    supabase = createClient(config.supabaseUrl, config.supabaseAnonKey, {
      auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false }
    });
    supabase.__plannerUrl = config.supabaseUrl;
    supabase.__plannerKey = config.supabaseAnonKey;
  }

  renderSessionText();

  kickOffLoops();
  setStatus('Supabase 연결됨. planner_user_state를 확인 중이다.', 'connected');
  await pullPlannerUserState({ reason: '초기 확인' });
  if (config.syncCode) {
    await pullRemoteState({ reason: 'legacy 초기 확인' });
  }
}

function startRealtimeSubscription() {
  if (localDbMode) {
    if (localEventSource) {
      try { localEventSource.close(); } catch {}
      localEventSource = null;
    }
    if (getLocalApiBase()) {
      setStatus('Local DB polling 연결됨. Cloudflare tunnel은 15초 주기로 변경을 확인한다.', 'connected');
      return;
    }
    try {
      localEventSource = new EventSource(localApiUrl(`/api/events?user_id=${encodeURIComponent(PLANNER_USER_ID)}`));
      localEventSource.addEventListener('update', (event) => {
        try {
          const payload = JSON.parse(event.data || '{}');
          if (payload.updated_by && payload.updated_by === readMeta().deviceId) return;
        } catch {}
        void pullPlannerUserState({ reason: 'Local DB 실시간 반영' });
      });
      localEventSource.addEventListener('open', () => setStatus('Local DB realtime 연결됨. 다른 기기 변경을 반영한다.', 'connected'));
      localEventSource.addEventListener('error', () => setStatus('Local DB realtime 재연결 중이다.', 'pending'));
    } catch {}
    return;
  }
  if (!supabase) return;
  if (realtimeChannel) {
    try { supabase.removeChannel(realtimeChannel); } catch {}
    realtimeChannel = null;
  }

  realtimeChannel = supabase
    .channel(`planner-user-state-${PLANNER_USER_ID}`)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'planner_user_state',
        filter: `user_id=eq.${PLANNER_USER_ID}`
      },
      (payload) => {
        const changedBy = payload?.new?.updated_by || payload?.old?.updated_by || '';
        const myDeviceId = readMeta().deviceId;
        if (changedBy && changedBy === myDeviceId) return;
        void pullPlannerUserState({ reason: '실시간 반영' });
      }
    )
    .subscribe((status) => {
      if (status === 'SUBSCRIBED') {
        setStatus('Supabase realtime 연결됨. 다른 기기 변경을 바로 반영한다.', 'connected');
      }
    });
}

function kickOffLoops() {
  const config = readConfig();
  if (pollingTimer) clearInterval(pollingTimer);
  if (remoteTimer) clearInterval(remoteTimer);

  pollingTimer = setInterval(() => {
    void checkLocalStateChange();
  }, 1000);

  startRealtimeSubscription();

  if (config.autoSync !== false) {
    remoteTimer = setInterval(() => {
      void pullPlannerUserState({ reason: '백업 폴링' });
      if (config.syncCode) void pullRemoteState({ reason: 'legacy 자동 폴링' });
    }, 15000);
  }
}

function stopLoops() {
  if (pollingTimer) clearInterval(pollingTimer);
  if (remoteTimer) clearInterval(remoteTimer);
  if (realtimeChannel && supabase) {
    try { supabase.removeChannel(realtimeChannel); } catch {}
  }
  if (localEventSource) {
    try { localEventSource.close(); } catch {}
  }
  pollingTimer = null;
  remoteTimer = null;
  realtimeChannel = null;
  localEventSource = null;
}

async function checkLocalStateChange() {
  const config = readConfig();
  const raw = getRawPlannerState();
  const nextHash = hashStateRaw(raw);

  if (nextHash !== localHash) {
    markLocalStateDirty(nextHash, { includeLegacy: Boolean(config.syncCode) });
    if (config.autoSync === false) {
      setStatus('로컬 데이터가 바뀌었다. 자동 동기화는 꺼져 있으니 필요하면 수동 업로드를 눌러줘.', 'pending');
      return;
    }
    await retryPendingSync('자동 업로드');
    return;
  }

  const meta = readMeta();
  const needsUserStatePush = Boolean(meta.pendingUserStateHash) && meta.pendingUserStateHash === nextHash;
  const needsLegacyPush = Boolean(config.syncCode && meta.pendingLegacyHash) && meta.pendingLegacyHash === nextHash;
  if (!needsUserStatePush && !needsLegacyPush) return;

  if (config.autoSync !== false) {
    await retryPendingSync('자동 재시도 업로드');
  } else {
    setStatus('로컬 데이터가 바뀌었다. 자동 동기화는 꺼져 있으니 필요하면 수동 업로드를 눌러줘.', 'pending');
  }
}

async function flushImmediateSync(reason = '즉시 업로드') {
  const config = readConfig();
  const raw = getRawPlannerState();
  const nextHash = hashStateRaw(raw);
  const changed = nextHash !== localHash;
  if (changed) {
    markLocalStateDirty(nextHash, { includeLegacy: Boolean(config.syncCode) });
  }

  if (config.autoSync === false) {
    setStatus('로컬 데이터가 바뀌었다. 자동 동기화는 꺼져 있으니 필요하면 수동 업로드를 눌러줘.', 'pending');
    return;
  }

  if (!supabase && !localDbMode) {
    await initializeSupabase();
    if (!supabase && !localDbMode) return;
  }

  await retryPendingSync(changed ? reason : `${reason} 재시도`);
}

function scheduleImmediateSync(reason = '즉시 업로드') {
  const config = readConfig();
  const raw = getRawPlannerState();
  const nextHash = hashStateRaw(raw);
  const meta = readMeta();
  const hasPendingPush = (Boolean(meta.pendingUserStateHash) && meta.pendingUserStateHash === nextHash)
    || (Boolean(config.syncCode && meta.pendingLegacyHash) && meta.pendingLegacyHash === nextHash);
  if (nextHash === localHash && !hasPendingPush) return;

  if (nextHash !== localHash) {
    markLocalStateDirty(nextHash, { includeLegacy: Boolean(config.syncCode) });
  }

  immediateSyncReason = reason;
  if (immediateSyncTimer) clearTimeout(immediateSyncTimer);
  immediateSyncTimer = setTimeout(() => {
    immediateSyncTimer = null;
    void flushImmediateSync(immediateSyncReason || reason);
  }, 250);
}

async function plannerSyncPull(syncCode) {
  if (localDbMode) {
    const json = await requestLocalApi('/api/planner-sync/pull', { sync_code: syncCode });
    return json.row;
  }
  const { data, error } = await supabase.rpc('planner_sync_pull', { p_sync_code: syncCode });
  if (error) throw error;
  return Array.isArray(data) ? data[0] : data;
}

async function plannerSyncPush(syncCode, payload, updatedAt, deviceId) {
  if (localDbMode) {
    const json = await requestLocalApi('/api/planner-sync/push', {
      sync_code: syncCode,
      state_json: payload,
      state_version: PLANNER_STATE_VERSION,
      updated_by: deviceId,
      updated_at: updatedAt
    });
    return json.row;
  }
  const { data, error } = await supabase.rpc('planner_sync_push', {
    p_sync_code: syncCode,
    p_state_json: payload,
    p_state_version: PLANNER_STATE_VERSION,
    p_updated_by: deviceId,
    p_updated_at: updatedAt
  });
  if (error) throw error;
  return Array.isArray(data) ? data[0] : data;
}

async function plannerUserStatePull(userId = PLANNER_USER_ID) {
  if (localDbMode) {
    const json = await requestLocalApi('/api/planner-user-state/pull', { user_id: userId });
    return json.row;
  }
  const { data, error } = await supabase.rpc('planner_user_state_pull', { p_user_id: userId });
  if (error) throw error;
  return Array.isArray(data) ? data[0] : data;
}

async function plannerUserStatePush(payload, updatedAt, deviceId, userId = PLANNER_USER_ID) {
  if (localDbMode) {
    const json = await requestLocalApi('/api/planner-user-state/push', {
      user_id: userId,
      state_json: payload,
      state_version: PLANNER_USER_STATE_VERSION,
      updated_by: deviceId,
      updated_at: updatedAt
    });
    return json.row;
  }
  const { data, error } = await supabase.rpc('planner_user_state_push', {
    p_user_id: userId,
    p_state_json: payload,
    p_state_version: PLANNER_USER_STATE_VERSION,
    p_updated_by: deviceId,
    p_updated_at: updatedAt
  });
  if (error) throw error;
  return Array.isArray(data) ? data[0] : data;
}

function markLocalStateDirty(nextHash, { includeLegacy = false } = {}) {
  localHash = nextHash;
  const meta = readMeta();
  meta.lastHash = nextHash;
  meta.lastLocalChangeAt = nowIso();
  meta.pendingUserStateHash = nextHash;
  if (includeLegacy) {
    meta.pendingLegacyHash = nextHash;
  } else if (!readConfig().syncCode) {
    meta.pendingLegacyHash = '';
  }
  saveMeta(meta);
  renderSessionText();
  return meta;
}

async function retryPendingSync(reason = '자동 재시도 업로드') {
  const config = readConfig();
  const raw = getRawPlannerState();
  const currentHash = hashStateRaw(raw);
  const meta = readMeta();
  const needsUserStatePush = Boolean(meta.pendingUserStateHash) && meta.pendingUserStateHash === currentHash;
  const needsLegacyPush = Boolean(config.syncCode && meta.pendingLegacyHash) && meta.pendingLegacyHash === currentHash;
  if (!needsUserStatePush && !needsLegacyPush) return false;

  if (!supabase && !localDbMode) {
    await initializeSupabase();
    if (!supabase && !localDbMode) return false;
  }

  if (needsUserStatePush) await pushPlannerUserState(reason);
  if (needsLegacyPush) await pushLocalState(`legacy ${reason}`);
  return true;
}

async function pushPlannerUserState(reason = '수동 업로드') {
  if (syncing) return;
  if (!supabase && !localDbMode) {
    setStatus('동기화 서버 연결이 아직 안 잡혔다.', 'error');
    return;
  }

  const raw = getRawPlannerState();
  if (!raw) {
    setStatus('업로드할 플래너 데이터가 없다.', 'error');
    return;
  }

  syncing = true;
  try {
    const payload = JSON.parse(raw);
    const currentHash = hashStateObject(payload);
    const meta = readMeta();
    const updatedAt = meta.lastLocalChangeAt || nowIso();
    await plannerUserStatePush(payload, updatedAt, meta.deviceId);
    meta.lastUserStateUploadedAt = updatedAt;
    meta.lastUserStateSeenAt = updatedAt;
    if (meta.pendingUserStateHash === currentHash) {
      meta.pendingUserStateHash = '';
    }
    saveMeta(meta);
    setStatus(`${reason} 완료 — ${stateStoreLabel()} user state에 현재 상태를 저장했다.`, 'connected');
    renderSessionText();
  } catch (error) {
    setStatus(`user state 업로드 실패: ${error.message || error}`, 'error');
  } finally {
    syncing = false;
  }
}

async function pushLocalState(reason = '수동 업로드') {
  if (syncing) return;
  const config = readConfig();
  if (!config.syncCode) {
    setStatus('먼저 동기화 코드를 만들거나 입력해줘.', 'error');
    return;
  }
  if (!supabase && !localDbMode) {
    setStatus('동기화 서버 연결이 아직 안 잡혔다.', 'error');
    return;
  }

  const raw = getRawPlannerState();
  if (!raw) {
    setStatus('업로드할 플래너 데이터가 없다.', 'error');
    return;
  }

  syncing = true;
  try {
    const payload = JSON.parse(raw);
    const currentHash = hashStateObject(payload);
    const meta = readMeta();
    const updatedAt = meta.lastLocalChangeAt || nowIso();
    await plannerSyncPush(config.syncCode, payload, updatedAt, meta.deviceId);
    meta.lastUploadedAt = updatedAt;
    meta.lastRemoteSeenAt = updatedAt;
    if (meta.pendingLegacyHash === currentHash) {
      meta.pendingLegacyHash = '';
    }
    saveMeta(meta);
    setStatus(`${reason} 완료 — 같은 동기화 코드를 가진 다른 기기에서 바로 가져올 수 있다.`, 'connected');
    renderSessionText();
  } catch (error) {
    setStatus(`업로드 실패: ${error.message || error}`, 'error');
  } finally {
    syncing = false;
  }
}

async function pullPlannerUserState({ force = false, reason = '수동 새로받기' } = {}) {
  if (syncing) return;
  if (!supabase && !localDbMode) return;

  syncing = true;
  try {
    const row = await plannerUserStatePull(PLANNER_USER_ID);
    const meta = readMeta();

    if (!row?.state_json) {
      if (force) setStatus(`${stateStoreLabel()} user state에 아직 저장된 상태가 없다.`, 'pending');
      return;
    }

    const remoteRaw = JSON.stringify(row.state_json);
    const remoteHash = hashStateObject(row.state_json);
    const remoteUpdatedAt = row.updated_at || nowIso();
    const localRaw = getRawPlannerState();
    const localCurrentHash = hashStateRaw(localRaw);
    const localUpdatedAt = meta.lastLocalChangeAt || 0;
    const remoteIsNewer = !localUpdatedAt || new Date(remoteUpdatedAt).getTime() > new Date(localUpdatedAt).getTime();
    const localIsDirty = Boolean(meta.lastLocalChangeAt) && (!meta.lastUserStateUploadedAt || new Date(meta.lastLocalChangeAt).getTime() > new Date(meta.lastUserStateUploadedAt).getTime());
    const firstSync = !meta.lastUserStateUploadedAt && !meta.lastUserStateAppliedAt;

    meta.lastUserStateSeenAt = remoteUpdatedAt;

    if (force || (remoteHash !== localCurrentHash && (remoteIsNewer || !localIsDirty || firstSync))) {
      setRawPlannerState(remoteRaw);
      localHash = remoteHash;
      meta.lastHash = remoteHash;
      meta.lastUserStateAppliedAt = remoteUpdatedAt;
      saveMeta(meta);

      let appliedInPlace = false;
      try {
        if (typeof window.__kmlePlannerApplyRemoteState === 'function') {
          appliedInPlace = window.__kmlePlannerApplyRemoteState(row.state_json) === true;
          if (appliedInPlace) window.__kmlePlannerState = row.state_json;
        }
      } catch (error) {
        console.error('in-place planner_user_state apply failed', error);
      }

      setStatus(
        appliedInPlace
          ? `${reason} 완료 — ${stateStoreLabel()} user state를 현재 화면에 바로 반영했다.`
          : `${reason} 완료 — ${stateStoreLabel()} user state를 이 기기에 반영했다.`,
        'connected'
      );
      renderSessionText();

      if (!appliedInPlace) {
        setTimeout(() => location.reload(), 250);
      }
      return;
    }

    saveMeta(meta);
    if (force) {
      setStatus(`${stateStoreLabel()} user state는 확인했지만, 현재 기기 데이터가 더 최신이거나 동일하다.`, 'connected');
    }
  } catch (error) {
    setStatus(`${stateStoreLabel()} user state 불러오기 실패: ${error.message || error}`, 'error');
  } finally {
    syncing = false;
    renderSessionText();
  }
}

async function pullRemoteState({ force = false, reason = '수동 새로받기' } = {}) {
  if (syncing) return;
  const config = readConfig();
  if (!config.syncCode || (!supabase && !localDbMode)) return;

  syncing = true;
  try {
    const row = await plannerSyncPull(config.syncCode);
    const meta = readMeta();

    if (!row?.state_json) {
      if (force) setStatus('이 동기화 코드에는 아직 원격 상태가 없다. 맥 정본에서 먼저 밀어넣기를 눌러줘.', 'pending');
      return;
    }

    const remoteRaw = JSON.stringify(row.state_json);
    const remoteHash = hashStateObject(row.state_json);
    const remoteUpdatedAt = row.updated_at || nowIso();
    const localRaw = getRawPlannerState();
    const localCurrentHash = hashStateRaw(localRaw);
    const localUpdatedAt = meta.lastLocalChangeAt || 0;
    const remoteIsNewer = !localUpdatedAt || new Date(remoteUpdatedAt).getTime() > new Date(localUpdatedAt).getTime();
    const localIsDirty = Boolean(meta.lastLocalChangeAt) && (!meta.lastUploadedAt || new Date(meta.lastLocalChangeAt).getTime() > new Date(meta.lastUploadedAt).getTime());
    const firstSync = !meta.lastUploadedAt && !meta.lastRemoteAppliedAt;

    meta.lastRemoteSeenAt = remoteUpdatedAt;

    if (force || (remoteHash !== localCurrentHash && ((remoteIsNewer && !localIsDirty) || firstSync))) {
      setRawPlannerState(remoteRaw);
      localHash = remoteHash;
      meta.lastHash = remoteHash;
      meta.lastRemoteAppliedAt = remoteUpdatedAt;
      saveMeta(meta);

      let appliedInPlace = false;
      try {
        if (typeof window.__kmlePlannerApplyRemoteState === 'function') {
          appliedInPlace = window.__kmlePlannerApplyRemoteState(row.state_json) === true;
          if (appliedInPlace) {
            window.__kmlePlannerState = row.state_json;
          }
        }
      } catch (error) {
        console.error('in-place remote apply failed', error);
      }

      setStatus(
        appliedInPlace
          ? `${reason} 완료 — 원격 상태를 현재 화면에 바로 반영했다.`
          : `${reason} 완료 — 원격 상태를 이 기기에 반영했다.`,
        'connected'
      );
      renderSessionText();

      if (!appliedInPlace) {
        setTimeout(() => location.reload(), 250);
      }
      return;
    }

    saveMeta(meta);
    if (force) {
      setStatus('원격 상태는 확인했지만, 현재 기기 데이터가 더 최신이거나 동일하다.', 'connected');
    }
  } catch (error) {
    setStatus(`원격 불러오기 실패: ${error.message || error}`, 'error');
  } finally {
    syncing = false;
    renderSessionText();
  }
}

function bootstrapMetaFromCurrentState() {
  const meta = readMeta();
  const raw = getRawPlannerState();
  const currentHash = hashStateRaw(raw);
  if (!meta.lastHash) {
    meta.lastHash = currentHash;
    saveMeta(meta);
  }
  localHash = currentHash;
}

function resumeAggressiveSync(reason = '포그라운드 복귀') {
  void initializeSupabase();
  void flushImmediateSync(`${reason} 업로드`);
  void pullPlannerUserState({ reason });
  if (readConfig().syncCode) {
    void pullRemoteState({ reason: `legacy ${reason}` });
  }
}

window.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    if (immediateSyncTimer) {
      clearTimeout(immediateSyncTimer);
      immediateSyncTimer = null;
      void flushImmediateSync(immediateSyncReason || '백그라운드 전환 업로드');
    }
    return;
  }
  if (!document.hidden) {
    resumeAggressiveSync('포그라운드 복귀');
  }
});

window.addEventListener('focus', () => {
  resumeAggressiveSync('창 포커스 복귀');
});

window.addEventListener('pageshow', () => {
  resumeAggressiveSync('페이지 복귀');
});

window.addEventListener('online', () => {
  resumeAggressiveSync('온라인 복귀');
});

window.addEventListener('storage', (event) => {
  if (event.key === STORAGE_KEY) {
    localHash = hashStateRaw(event.newValue || '');
    renderSessionText();
  }
});

window.addEventListener('pagehide', () => {
  if (immediateSyncTimer) {
    clearTimeout(immediateSyncTimer);
    immediateSyncTimer = null;
    void flushImmediateSync(immediateSyncReason || '페이지 종료 직전 업로드');
  }
});

window.__kmlePlannerNotifyLocalChange = function notifyPlannerLocalChange(reason = '앱 저장') {
  scheduleImmediateSync(reason);
  return true;
};

injectUI();
bootstrapMetaFromCurrentState();
renderConfigToUI();
renderSessionText();
setStatus('Local DB / planner_user_state 연결 준비 중이다.', 'default');
void initializeSupabase();
