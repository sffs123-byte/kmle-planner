import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

const STORAGE_KEY = 'kmlePlannerState.v2';
const CONFIG_KEY = 'kmlePlannerSyncConfig.v1';
const META_KEY = 'kmlePlannerSyncMeta.v1';
const PLANNER_STATE_VERSION = 'kmlePlannerState.v2';

const defaultConfig = {
  supabaseUrl: '',
  supabaseAnonKey: '',
  email: '',
  autoSync: true
};

function defaultMeta() {
  return {
    deviceId: getOrCreateDeviceId(),
    lastHash: '',
    lastLocalChangeAt: 0,
    lastUploadedAt: 0,
    lastRemoteAppliedAt: 0,
    lastStatus: '로컬 전용 모드',
    lastStatusAt: 0
  };
}

function getOrCreateDeviceId() {
  const key = 'kmlePlannerDeviceId.v1';
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  const created = globalThis.crypto?.randomUUID?.() || `device-${Math.random().toString(36).slice(2, 10)}`;
  localStorage.setItem(key, created);
  return created;
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

function readConfig() {
  return readJSON(CONFIG_KEY, defaultConfig);
}

function saveConfig(config) {
  writeJSON(CONFIG_KEY, config);
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
    return new Intl.DateTimeFormat('ko-KR', {
      dateStyle: 'short',
      timeStyle: 'short'
    }).format(new Date(value));
  } catch {
    return value;
  }
}

const ui = {
  statusPill: null,
  modal: null,
  statusText: null,
  emailInput: null,
  urlInput: null,
  keyInput: null,
  autoSyncInput: null,
  sessionText: null,
  openButton: null,
  saveButton: null,
  signInButton: null,
  signOutButton: null,
  pushButton: null,
  pullButton: null
};

let supabase = null;
let currentSession = null;
let pollingTimer = null;
let remoteTimer = null;
let localHash = hashString(getRawPlannerState());
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
    .sync-pill-dot {
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: #94a3b8;
      flex: none;
    }
    .sync-pill.connected .sync-pill-dot { background: #16a34a; }
    .sync-pill.pending .sync-pill-dot { background: #d97706; }
    .sync-pill.error .sync-pill-dot { background: #dc2626; }
    .sync-modal {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
      background: rgba(15, 23, 42, 0.45);
      z-index: 999;
    }
    .sync-modal.show { display: flex; }
    .sync-card {
      width: min(680px, 100%);
      max-height: min(90vh, 920px);
      overflow: auto;
      background: rgba(255,255,255,0.96);
      border: 1px solid #dbe4f0;
      border-radius: 24px;
      box-shadow: 0 18px 45px rgba(27, 40, 69, 0.18);
      padding: 24px;
      color: #18212f;
    }
    .sync-grid {
      display: grid;
      gap: 14px;
      margin-top: 18px;
    }
    .sync-field {
      display: grid;
      gap: 8px;
    }
    .sync-field label {
      font-size: 13px;
      color: #64748b;
      font-weight: 700;
    }
    .sync-field input, .sync-field textarea {
      width: 100%;
      border: 1px solid #dbe4f0;
      border-radius: 14px;
      padding: 12px 14px;
      font: inherit;
      background: #fff;
      color: #18212f;
    }
    .sync-field textarea { min-height: 104px; resize: vertical; }
    .sync-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }
    .sync-note {
      margin-top: 14px;
      color: #64748b;
      font-size: 13px;
      line-height: 1.65;
    }
    .sync-block {
      margin-top: 16px;
      padding: 16px;
      border-radius: 18px;
      border: 1px solid #dbe4f0;
      background: #f8fbff;
    }
    .sync-status-text {
      white-space: pre-line;
      line-height: 1.6;
      color: #334155;
      font-size: 13px;
      margin-top: 10px;
    }
    .sync-inline {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
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
  statusPill.innerHTML = '<span class="sync-pill-dot"></span><span>로컬 전용 모드</span>';
  heroSide.appendChild(statusPill);

  const modal = document.createElement('div');
  modal.className = 'sync-modal';
  modal.id = 'syncModal';
  modal.innerHTML = `
    <div class="sync-card">
      <div class="sync-inline">
        <div>
          <div class="panel-title" style="font-size:24px;font-weight:800;">자동 동기화 설정</div>
          <div class="panel-subtitle" style="margin-top:6px;color:#64748b;">GitHub Pages로 배포한 뒤 Supabase에 연결하면 맥·태블릿 간 상태를 자동 동기화할 수 있다.</div>
        </div>
        <button class="btn btn-ghost btn-small" id="syncCloseBtn">닫기</button>
      </div>

      <div class="sync-grid">
        <div class="sync-field">
          <label for="syncSupabaseUrl">Supabase URL</label>
          <input id="syncSupabaseUrl" placeholder="https://xxxx.supabase.co" />
        </div>
        <div class="sync-field">
          <label for="syncSupabaseKey">Supabase anon key</label>
          <textarea id="syncSupabaseKey" placeholder="eyJ... anon public key"></textarea>
        </div>
        <div class="sync-field">
          <label for="syncEmail">동기화용 이메일</label>
          <input id="syncEmail" type="email" placeholder="같은 이메일로 맥/태블릿 둘 다 로그인" />
        </div>
        <label style="display:flex; gap:10px; align-items:center; color:#334155; font-size:14px;">
          <input id="syncAutoMode" type="checkbox" checked />
          자동 동기화 켜기 (상태가 바뀌면 자동 업로드, 다른 기기 변경도 주기적으로 반영)
        </label>
      </div>

      <div class="sync-actions">
        <button class="btn btn-primary" id="syncSaveBtn">설정 저장</button>
        <button class="btn btn-secondary" id="syncSignInBtn">이메일 로그인 링크 보내기</button>
        <button class="btn btn-ghost" id="syncPushBtn">지금 밀어넣기</button>
        <button class="btn btn-ghost" id="syncPullBtn">지금 다시 받기</button>
        <button class="btn btn-danger" id="syncSignOutBtn">로그아웃</button>
      </div>

      <div class="sync-block">
        <div style="font-weight:700;">현재 상태</div>
        <div id="syncSessionText" class="sync-note"></div>
        <div id="syncStatusText" class="sync-status-text"></div>
      </div>

      <div class="sync-note">
        초기 1회는 supabase/SETUP.md와 supabase/schema.sql을 보고 Supabase 프로젝트를 만들어야 한다.\n
        그다음 같은 이메일로 맥과 태블릿에서 로그인하면 자동 동기화된다.
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  ui.openButton = openButton;
  ui.statusPill = statusPill;
  ui.modal = modal;
  ui.statusText = modal.querySelector('#syncStatusText');
  ui.sessionText = modal.querySelector('#syncSessionText');
  ui.emailInput = modal.querySelector('#syncEmail');
  ui.urlInput = modal.querySelector('#syncSupabaseUrl');
  ui.keyInput = modal.querySelector('#syncSupabaseKey');
  ui.autoSyncInput = modal.querySelector('#syncAutoMode');
  ui.saveButton = modal.querySelector('#syncSaveBtn');
  ui.signInButton = modal.querySelector('#syncSignInBtn');
  ui.signOutButton = modal.querySelector('#syncSignOutBtn');
  ui.pushButton = modal.querySelector('#syncPushBtn');
  ui.pullButton = modal.querySelector('#syncPullBtn');

  openButton.addEventListener('click', () => ui.modal.classList.add('show'));
  modal.querySelector('#syncCloseBtn').addEventListener('click', () => ui.modal.classList.remove('show'));
  modal.addEventListener('click', (event) => {
    if (event.target === modal) ui.modal.classList.remove('show');
  });

  ui.saveButton.addEventListener('click', async () => {
    const config = {
      supabaseUrl: ui.urlInput.value.trim(),
      supabaseAnonKey: ui.keyInput.value.trim(),
      email: ui.emailInput.value.trim(),
      autoSync: Boolean(ui.autoSyncInput.checked)
    };
    saveConfig(config);
    setStatus('설정 저장 완료. URL/key가 있으면 연결을 다시 시도한다.', 'pending');
    await initializeSupabase();
  });

  ui.signInButton.addEventListener('click', async () => {
    try {
      const config = readConfig();
      if (!config.supabaseUrl || !config.supabaseAnonKey) {
        setStatus('먼저 Supabase URL과 anon key를 저장해줘.', 'error');
        return;
      }
      if (!config.email) {
        setStatus('동기화용 이메일을 먼저 입력해줘.', 'error');
        return;
      }
      await initializeSupabase();
      if (!supabase) {
        setStatus('Supabase 연결이 아직 안 잡혔다.', 'error');
        return;
      }
      const { error } = await supabase.auth.signInWithOtp({
        email: config.email,
        options: {
          shouldCreateUser: true,
          emailRedirectTo: `${location.origin}${location.pathname}`
        }
      });
      if (error) throw error;
      setStatus('로그인 링크를 이메일로 보냈다. 맥과 태블릿 모두 같은 이메일로 링크를 눌러 로그인하면 된다.', 'pending');
    } catch (error) {
      setStatus(`로그인 링크 발송 실패: ${error.message || error}`, 'error');
    }
  });

  ui.signOutButton.addEventListener('click', async () => {
    if (!supabase) return;
    await supabase.auth.signOut();
    currentSession = null;
    setStatus('로그아웃 완료. 현재는 로컬 전용 모드다.', 'pending');
    renderSessionText();
  });

  ui.pushButton.addEventListener('click', async () => {
    await pushLocalState('수동 업로드');
  });

  ui.pullButton.addEventListener('click', async () => {
    await pullRemoteState({ force: true, reason: '수동 새로받기' });
  });
}

function renderConfigToUI() {
  if (!ui.urlInput) return;
  const config = readConfig();
  ui.urlInput.value = config.supabaseUrl || '';
  ui.keyInput.value = config.supabaseAnonKey || '';
  ui.emailInput.value = config.email || '';
  ui.autoSyncInput.checked = config.autoSync !== false;
}

function renderSessionText() {
  if (!ui.sessionText) return;
  if (!currentSession?.user) {
    ui.sessionText.textContent = '로그인 전 — 로컬 저장만 사용 중';
    return;
  }
  const meta = readMeta();
  ui.sessionText.textContent = [
    `로그인됨: ${currentSession.user.email || currentSession.user.id}`,
    `device: ${meta.deviceId}`,
    `마지막 업로드: ${formatDateTime(meta.lastUploadedAt)}`,
    `마지막 원격 반영: ${formatDateTime(meta.lastRemoteAppliedAt)}`
  ].join('\n');
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

async function initializeSupabase() {
  const config = readConfig();
  renderConfigToUI();

  if (!config.supabaseUrl || !config.supabaseAnonKey) {
    supabase = null;
    currentSession = null;
    renderSessionText();
    setStatus('Supabase URL/anon key를 넣으면 자동 동기화를 켤 수 있다.', 'default');
    stopRemoteLoop();
    return;
  }

  if (!supabase || supabase.__plannerUrl !== config.supabaseUrl || supabase.__plannerKey !== config.supabaseAnonKey) {
    supabase = createClient(config.supabaseUrl, config.supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true
      }
    });
    supabase.__plannerUrl = config.supabaseUrl;
    supabase.__plannerKey = config.supabaseAnonKey;

    supabase.auth.onAuthStateChange((_event, session) => {
      currentSession = session;
      renderSessionText();
      if (session?.user) {
        setStatus('동기화 연결됨. 원격 상태를 확인 중이다.', 'connected');
        kickOffLoops();
        void reconcileState('auth-change');
      } else {
        stopRemoteLoop();
        setStatus('로그인 전 — 로컬 저장만 사용 중', 'default');
      }
    });
  }

  const { data, error } = await supabase.auth.getSession();
  if (error) {
    currentSession = null;
    renderSessionText();
    setStatus(`세션 확인 실패: ${error.message || error}`, 'error');
    return;
  }

  currentSession = data.session;
  renderSessionText();

  if (currentSession?.user) {
    kickOffLoops();
    setStatus('동기화 연결됨. 마지막 저장 상태를 맞추는 중이다.', 'connected');
    await reconcileState('init');
  } else {
    stopRemoteLoop();
    setStatus('설정은 저장됨. 같은 이메일로 로그인하면 자동 동기화가 시작된다.', 'pending');
  }
}

function kickOffLoops() {
  const config = readConfig();
  if (pollingTimer) clearInterval(pollingTimer);
  if (remoteTimer) clearInterval(remoteTimer);

  pollingTimer = setInterval(() => {
    void checkLocalStateChange();
  }, 2000);

  if (config.autoSync !== false) {
    remoteTimer = setInterval(() => {
      void pullRemoteState({ reason: '자동 폴링' });
    }, 30000);
  }
}

function stopRemoteLoop() {
  if (pollingTimer) clearInterval(pollingTimer);
  if (remoteTimer) clearInterval(remoteTimer);
  pollingTimer = null;
  remoteTimer = null;
}

async function checkLocalStateChange() {
  const raw = getRawPlannerState();
  const nextHash = hashString(raw);
  if (nextHash === localHash) return;

  localHash = nextHash;
  const meta = readMeta();
  meta.lastHash = nextHash;
  meta.lastLocalChangeAt = nowIso();
  saveMeta(meta);

  if (currentSession?.user && readConfig().autoSync !== false) {
    await pushLocalState('자동 업로드');
  } else {
    setStatus('로컬 데이터가 바뀌었지만, 아직 동기화 로그인은 안 된 상태다.', 'pending');
  }
}

async function reconcileState(reason = 'manual') {
  await checkLocalStateChange();
  await pullRemoteState({ reason });
  const remoteApplied = sessionStorage.getItem('kmlePlannerRemoteApplied');
  if (!remoteApplied) {
    await pushLocalState(`초기 동기화 (${reason})`);
  }
}

async function fetchRemoteRow() {
  if (!supabase || !currentSession?.user) return null;
  const { data, error } = await supabase
    .from('planner_states')
    .select('user_id, state_json, state_version, updated_at, updated_by')
    .eq('user_id', currentSession.user.id)
    .maybeSingle();

  if (error) throw error;
  return data;
}

async function pushLocalState(reason = '수동 업로드') {
  if (syncing || !supabase || !currentSession?.user) {
    if (!currentSession?.user) setStatus('로그인 후 업로드할 수 있다.', 'pending');
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
    const meta = readMeta();
    const updatedAt = meta.lastLocalChangeAt || nowIso();
    const { error } = await supabase
      .from('planner_states')
      .upsert({
        user_id: currentSession.user.id,
        state_json: payload,
        state_version: PLANNER_STATE_VERSION,
        updated_at: updatedAt,
        updated_by: meta.deviceId
      });
    if (error) throw error;

    meta.lastUploadedAt = updatedAt;
    saveMeta(meta);
    sessionStorage.setItem('kmlePlannerRemoteApplied', updatedAt);
    setStatus(`${reason} 완료 — 다른 기기에서도 같은 이메일로 로그인하면 반영된다.`, 'connected');
    renderSessionText();
  } catch (error) {
    setStatus(`업로드 실패: ${error.message || error}`, 'error');
  } finally {
    syncing = false;
  }
}

async function pullRemoteState({ force = false, reason = '수동 새로받기' } = {}) {
  if (syncing || !supabase || !currentSession?.user) return;
  syncing = true;
  try {
    const row = await fetchRemoteRow();
    if (!row?.state_json) {
      if (force) setStatus('원격에 아직 저장된 플래너 상태가 없다.', 'pending');
      return;
    }

    const remoteRaw = JSON.stringify(row.state_json);
    const remoteHash = hashString(remoteRaw);
    const remoteUpdatedAt = row.updated_at || nowIso();
    const meta = readMeta();
    const localRaw = getRawPlannerState();
    const localCurrentHash = hashString(localRaw);
    const localUpdatedAt = meta.lastLocalChangeAt || 0;

    const remoteIsNewer = !localUpdatedAt || new Date(remoteUpdatedAt).getTime() > new Date(localUpdatedAt).getTime();
    const localIsDirty = Boolean(meta.lastLocalChangeAt) && (!meta.lastUploadedAt || new Date(meta.lastLocalChangeAt).getTime() > new Date(meta.lastUploadedAt).getTime());

    if (force || (remoteHash !== localCurrentHash && remoteIsNewer && !localIsDirty)) {
      setRawPlannerState(remoteRaw);
      localHash = remoteHash;
      meta.lastHash = remoteHash;
      meta.lastRemoteAppliedAt = remoteUpdatedAt;
      meta.lastUploadedAt = remoteUpdatedAt;
      saveMeta(meta);
      sessionStorage.setItem('kmlePlannerRemoteApplied', remoteUpdatedAt);
      setStatus(`${reason} 완료 — 원격 상태를 이 기기에 반영했다.`, 'connected');
      setTimeout(() => location.reload(), 300);
      return;
    }

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
  const currentHash = hashString(raw);
  if (!meta.lastHash) {
    meta.lastHash = currentHash;
    meta.lastLocalChangeAt = nowIso();
    saveMeta(meta);
  }
  localHash = currentHash;
}

window.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    void initializeSupabase();
    if (currentSession?.user && readConfig().autoSync !== false) {
      void pullRemoteState({ reason: '포그라운드 복귀' });
    }
  }
});

window.addEventListener('storage', (event) => {
  if (event.key === STORAGE_KEY) {
    localHash = hashString(event.newValue || '');
    renderSessionText();
  }
});

injectUI();
bootstrapMetaFromCurrentState();
renderConfigToUI();
renderSessionText();
setStatus('로컬 전용 모드 — 원하면 자동 동기화를 연결할 수 있다.', 'default');
void initializeSupabase();
