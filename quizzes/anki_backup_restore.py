#!/usr/bin/env python3
"""Inject versioned, site-scoped Anki progress backup/restore controls."""

from __future__ import annotations

import json


CSS = r'''
/* BACKUP_RESTORE_V1 */
.backup-tools { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--card-border); display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.backup-tools button { min-height: 42px; padding: 9px 6px; border: 1px solid var(--card-border); border-radius: 8px; background: var(--card-bg); color: var(--text); cursor: pointer; font-weight: 700; }
.backup-tools button:hover { border-color: var(--accent); color: var(--accent); }
.backup-help { grid-column: 1 / -1; color: var(--text-dim); font-size: 11px; line-height: 1.45; text-align: center; }
'''


UI = r'''
            <!-- BACKUP_RESTORE_UI_V1 -->
            <div class="backup-tools" aria-label="수정본 백업 및 복원">
                <button type="button" id="btnExportBackup" onclick="exportBackup()">📤 수정본<br>내보내기</button>
                <button type="button" id="btnImportBackup" onclick="document.getElementById('backupFileInput').click()">📥 수정본<br>불러오기</button>
                <input type="file" id="backupFileInput" accept="application/json,.json" hidden onchange="importBackupFile(this.files && this.files[0]); this.value=''">
                <div class="backup-help">수정 해설·자기답안·SRS·랜덤 세션·필기를 JSON 파일로 옮깁니다.</div>
            </div>
'''


JS = r'''
// ── Versioned backup / restore ──
const BACKUP_SITE_ID = __SITE_ID__;
const BACKUP_DOWNLOAD_PREFIX = __DOWNLOAD_PREFIX__;
const BACKUP_FORMAT = 'openclaw-anki-backup';
const BACKUP_VERSION = 1;
const BACKUP_MAX_BYTES = 64 * 1024 * 1024;

function flushEditableChangesForBackup() {
    ALL_IDS.forEach(id => {
        const content = document.getElementById('ans-content-' + id);
        if (content && content.contentEditable === 'true') edits[id] = content.innerHTML;
    });
    const quizContent = document.getElementById('quizAnsContent');
    if (activeQuizCardId && quizContent && quizContent.contentEditable === 'true') edits[activeQuizCardId] = quizContent.innerHTML;
    saveEdits();
}

function collectBackupStorage() {
    flushEditableChangesForBackup();
    saveQuizSession();
    const data = {};
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(STORAGE_PREFIX)) {
            data[key.slice(STORAGE_PREFIX.length)] = localStorage.getItem(key);
        }
    }
    return data;
}

function exportBackup() {
    try {
        const payload = {
            format: BACKUP_FORMAT,
            version: BACKUP_VERSION,
            siteId: BACKUP_SITE_ID,
            storagePrefix: STORAGE_PREFIX,
            exportedAt: new Date().toISOString(),
            cardCount: ALL_IDS.length,
            data: collectBackupStorage()
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const day = payload.exportedAt.slice(0, 10).replaceAll('-', '');
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = BACKUP_DOWNLOAD_PREFIX + '_' + day + '.json';
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    } catch (err) {
        console.error('Backup export failed', err);
        alert('수정본 내보내기에 실패했습니다. 브라우저 저장공간을 확인해 주세요.');
    }
}

function validateBackupPayload(payload) {
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) throw new Error('JSON object required');
    if (payload.format !== BACKUP_FORMAT || payload.version !== BACKUP_VERSION) throw new Error('Unsupported backup format');
    if (payload.siteId !== BACKUP_SITE_ID || payload.storagePrefix !== STORAGE_PREFIX) throw new Error('Wrong site backup');
    if (!payload.data || typeof payload.data !== 'object' || Array.isArray(payload.data)) throw new Error('Invalid data block');
    const clean = {};
    for (const suffix of Object.keys(payload.data)) {
        const value = payload.data[suffix];
        if (!suffix || suffix.length > 100 || suffix.includes('__proto__') || typeof value !== 'string') throw new Error('Invalid storage entry');
        JSON.parse(value);
        clean[suffix] = value;
    }
    return clean;
}

function replaceSiteStorage(data) {
    const before = {};
    const existingKeys = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(STORAGE_PREFIX)) existingKeys.push(key);
    }
    existingKeys.forEach(key => { before[key] = localStorage.getItem(key); });
    try {
        existingKeys.forEach(key => localStorage.removeItem(key));
        Object.keys(data).forEach(suffix => localStorage.setItem(STORAGE_PREFIX + suffix, data[suffix]));
    } catch (err) {
        Object.keys(data).forEach(suffix => localStorage.removeItem(STORAGE_PREFIX + suffix));
        Object.keys(before).forEach(key => localStorage.setItem(key, before[key]));
        throw err;
    }
}

async function importBackupFile(file) {
    if (!file) return;
    try {
        if (file.size > BACKUP_MAX_BYTES) throw new Error('Backup file too large');
        const payload = JSON.parse(await file.text());
        const clean = validateBackupPayload(payload);
        const when = payload.exportedAt ? new Date(payload.exportedAt).toLocaleString('ko-KR') : '날짜 정보 없음';
        if (!confirm(`이 기기의 현재 수정 내용과 학습 기록을 백업 파일로 교체할까요?\n\n백업 시각: ${when}\n복원 후 페이지가 새로고침됩니다.`)) return;
        replaceSiteStorage(clean);
        alert('수정본을 불러왔습니다. 페이지를 새로고침합니다.');
        location.reload();
    } catch (err) {
        console.error('Backup import failed', err);
        alert('이 사이트에서 만든 올바른 수정본 JSON 파일이 아닙니다. 기존 데이터는 변경되지 않았습니다.');
    }
}
// BACKUP_RESTORE_JS_V1
'''


def inject_backup_restore(html_text: str, *, site_id: str, download_prefix: str) -> str:
    """Return HTML with backup/restore UI and site-scoped validation."""
    if "BACKUP_RESTORE_V1" in html_text:
        return html_text

    js = JS.replace("__SITE_ID__", json.dumps(site_id, ensure_ascii=False))
    js = js.replace("__DOWNLOAD_PREFIX__", json.dumps(download_prefix, ensure_ascii=False))
    anchors = {
        "</style>": CSS + "\n</style>",
        '            <button class="btn-reset" id="btnReset" onclick="handleResetTap()">전체 다시 풀기<br><small>[3연타 시 초기화]</small></button>':
            '            <button class="btn-reset" id="btnReset" onclick="handleResetTap()">전체 다시 풀기<br><small>[3연타 시 초기화]</small></button>\n' + UI.rstrip(),
        "// ── Init ──": js + "\n\n// ── Init ──",
    }
    for anchor, replacement in anchors.items():
        if html_text.count(anchor) != 1:
            raise RuntimeError(f"backup/restore injection marker mismatch: {anchor[:60]}")
        html_text = html_text.replace(anchor, replacement, 1)
    return html_text
