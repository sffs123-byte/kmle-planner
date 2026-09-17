// Runs before the shared engine's DOMContentLoaded bootstrap.
const scopedOriginalStart = startQuizWith;
startQuizWith = function(ids, options = {}) {
    const allowed = new Set(studyIds());
    const scopedOptions = {...options,
        pending: sanitizeQuizPending(options.pending || []).filter(i => allowed.has(i.id)),
        restoreCurrentId: allowed.has(options.restoreCurrentId) ? options.restoreCurrentId : null,
        bonusSrs: Object.fromEntries(Object.entries(options.bonusSrs || {}).filter(([id]) => allowed.has(id)))
    };
    const result = scopedOriginalStart(sanitizeQuizQueue(ids).filter(id => allowed.has(id)), scopedOptions);
    document.getElementById('undoBtn').disabled = bonusMode || !options.restoreState || history.length === 0;
    return result;
};
const originalScopeUpdate = updateReviewBtn;
updateReviewBtn = function() {originalScopeUpdate();updateScopeControls();};
const originalScopeSave = saveQuizSession;
saveQuizSession = function() {originalScopeSave();updateScopeControls();};
const originalScopeResume = resumeSavedQuizIfAny;
resumeSavedQuizIfAny = function() {
    if (loadQuizSession()) originalScopeResume();
    else if (studyHashScope()) startReview('ordered');
    deckStorage.setItem(STUDY_SCOPE_KEY, JSON.stringify(deckStudyScope));
    if (studyHashScope()) window.history.replaceState(null, '', location.pathname + location.search);
};
const originalScopedUndo = undoLast;
undoLast = function() {
    if (bonusMode) return;
    const allowed = new Set(studyIds());
    history = history.filter(h => allowed.has(h.id));
    const entry = history[history.length - 1];
    if (entry) {
        entry.queueSnapshot = sanitizeQuizQueue(entry.queueSnapshot).filter(id => allowed.has(id));
        entry.pendingSnapshot = sanitizeQuizPending(entry.pendingSnapshot).filter(i => allowed.has(i.id));
    }
    return originalScopedUndo();
};
const previousScopedBonus = startBonus;
startBonus = function() {previousScopedBonus();document.getElementById('undoBtn').disabled=true;};
function switchStudyScope(scope, start = false) {
    if (scope !== 'all' && !DECK_EXAM_SETS[scope]) return;
    if (scope !== deckStudyScope) {
        finishDeckInteraction();
        exitQuiz(); // Saves current scope before changing keys, and stops the wait timer.
        deckStudyScope = scope;
        SRS_KEY = scopeStorageKey('srs_v1');
        HIST_KEY = scopeStorageKey('hist_v1');
        QUIZ_SESSION_KEY = scopeStorageKey('quiz_session_v1');
        srs = deckStoredJson(SRS_KEY, {});
        history = deckStoredJson(HIST_KEY, []);
        queue = []; pending = []; activeQuizCardId = null; resumeQuizUiState = null;
        bonusMode = false; bonusSrs = {};
        document.getElementById('undoBtn').disabled = true;
    }
    deckStorage.setItem(STUDY_SCOPE_KEY, JSON.stringify(scope));
    // Selecting a tab does not begin a quiz until the user presses Start/Resume.
    window.history.replaceState(null, '', location.pathname + location.search);
    updateReviewBtn(); updateStats();
    if (start) {
        if (loadQuizSession()) originalScopeResume();
        else startReview('ordered');
    }
}
function updateScopeControls() {
    document.querySelectorAll('[data-study-scope]').forEach(button => {
        button.setAttribute('aria-pressed', String(button.dataset.studyScope === deckStudyScope));
    });
    const title = document.querySelector('.review-hero-title');
    if (title) title.textContent = studyLabel() + ' · ' + studyIds().length + '문제';
    const description = document.querySelector('.review-hero-sub');
    if (description) description.textContent = '정답 보기 → 원문 필기 → 색상 버튼으로 평가. 복습할 카드는 먼저 나와요.';
    const resume = document.getElementById('btnStudyResume');
    if (resume) resume.hidden = !loadQuizSession();
    const note = document.getElementById('studyScopeNote');
    if (note) note.textContent = deckStudyScope === 'all'
        ? '전체 56개 질문군 · 시험지 원문 질문 · 기존 학습 기록을 그대로 사용합니다.'
        : '원문 1–20번 순서 · 질문 문구 그대로 · 정답은 원문 필기 서식';
    const badge = document.getElementById('studyScopeBadge');
    if (badge) badge.textContent = studyLabel() + ' ' + studyIds().length + '문제';
    const resetTitle = document.getElementById('deckResetTitle');
    if (resetTitle) resetTitle.textContent = studyLabel() + ' ' + studyIds().length + '문제의 학습 기록을 초기화할까요?';
    const reset = document.getElementById('btnReset');
    if (reset) reset.innerHTML = studyLabel() + ' 다시 풀기<br><small>선택 범위 학습 기록 초기화</small>';
}
const previousConfirmReset = deckConfirmReset;
deckConfirmReset = function() {updateScopeControls();previousConfirmReset();};
document.addEventListener('DOMContentLoaded', () => {
    const panel = document.createElement('section');
    panel.className = 'study-scope-panel'; panel.setAttribute('aria-label', '풀 문제 선택');
    panel.innerHTML = '<strong>풀 문제 선택</strong><div class="study-scope-tabs">' +
        [['all','전체 · 56문제'],['2','2세트 · 20문제'],['C','C세트 · 20문제']].map(([id,label]) =>
            '<button type="button" data-study-scope="'+id+'" aria-pressed="false">'+label+'</button>').join('') +
        '</div><p id="studyScopeNote"></p><small>학습 진도·초기화는 세트별로 분리됩니다. 수정 답안·필기는 공통으로 유지됩니다.</small>';
    document.getElementById('reviewHero').before(panel);
    panel.querySelectorAll('button').forEach(b => b.onclick = () => switchStudyScope(b.dataset.studyScope));
    const resume = document.createElement('button');resume.id = 'btnStudyResume';resume.type='button';
    resume.className='review-hero-btn';resume.textContent='이어풀기';resume.onclick=originalScopeResume;
    document.getElementById('reviewHero').lastElementChild.prepend(resume);
    const badge = document.createElement('span');badge.id='studyScopeBadge';badge.className='study-scope-badge';
    document.getElementById('quizHeader').prepend(badge);
    // The old reset callback cleared every card-view marker; limit it to this scope.
    document.getElementById('deckResetConfirm').onclick = () => {
        document.getElementById('deckResetDialog').close();finishDeckInteraction();
        studyIds().forEach(id => {doneSet.delete(id);
            document.getElementById('card-'+id)?.classList.remove('done');
            const b=document.getElementById('done-'+id);if(b){b.classList.remove('checked');b.textContent='✓ 완료';}
        });
        updateProgress();document.getElementById('undoBtn').disabled=true;
        doResetQuiz();updateReviewBtn();
    };
    updateScopeControls();
});
window.addEventListener('hashchange', () => {
    const scope = studyHashScope();
    if (scope) {document.getElementById('deckBrowseDialog')?.close();switchStudyScope(scope, true);}
});
document.addEventListener('DOMContentLoaded', () => {
    const dialog=document.createElement('dialog');dialog.id='originalTermDialog';
    dialog.innerHTML='<h3 id="originalTermTitle"></h3><p id="originalTermText"></p><button type="button">닫기</button>';
    dialog.setAttribute('aria-labelledby','originalTermTitle');document.body.appendChild(dialog);
    dialog.querySelector('button').onclick=()=>dialog.close();
    function showTerm(event) {
        const term=event.target.closest?.('.original-note abbr[title]');
        if(!term || term.closest('[contenteditable="true"]')) return;
        if(event.type==='keydown' && !['Enter',' '].includes(event.key)) return;
        event.preventDefault();
        document.getElementById('originalTermTitle').textContent=term.textContent;
        document.getElementById('originalTermText').textContent=term.title;
        dialog.showModal();
    }
    document.addEventListener('click',showTerm);document.addEventListener('keydown',showTerm);
});
