// Source-format answers replace summaries; keep earlier personal edits accessible.
(function migrateOriginalAnswers() {
    const flag=STORAGE_PREFIX+'original_answer_format_v1';
    if(deckStorage.getItem(flag)) return;
    if(Object.keys(edits).length) {
        deckStorage.setItem(STORAGE_PREFIX+'previous_summary_edits_v1', JSON.stringify(edits));
        for(const id of Object.keys(edits)) {
            if(!QUIZ_DATA[id]) continue;
            const previous=edits[id];
            if(!previous.includes('class="original-note"'))
                edits[id]=QUIZ_DATA[id].a+'<details class="previous-answer-edit"><summary>이전 Anki 수정 답안 (보존)</summary>'+previous+'</details>';
        }
        saveEdits();
    }
    deckStorage.setItem(flag,JSON.stringify(true));
})();
// Retain former app data; copy notes without treating its ratings as SRS.
function preserveLegacyNotes() {
    const flag=STORAGE_PREFIX+'legacy_import_v1';
    if(deckStorage.getItem(flag)) return;
    const legacy={};
    for(let i=0;i<deckStorage.length;i++) {
        const k=deckStorage.key(i);
        if(k && k.startsWith('neurosurgery_yeosin_56_v1:')) legacy[k]=deckStorage.getItem(k);
    }
    ALL_IDS.forEach(id=>{
        const memo=legacy['neurosurgery_yeosin_56_v1:memo:'+id];
        if(memo && !edits[id]) edits[id]=QUIZ_DATA[id].a+'<details class="legacy-memo"><summary>기존 개인 메모</summary><p>'+escapeHtmlText(memo)+'</p></details>';
    });
    if(Object.keys(legacy).length) deckStorage.setItem(STORAGE_PREFIX+'legacy_snapshot_v1',JSON.stringify(legacy));
    saveEdits();
    deckStorage.setItem(flag,JSON.stringify({version:1}));
}
preserveLegacyNotes();

// Close editing/drawing safely before the shared engine switches cards.
function finishDeckInteraction() {
    const content=document.getElementById('quizAnsContent');
    if(activeQuizCardId && content && content.contentEditable==='true') toggleQuizEdit(activeQuizCardId);
    saveDrawData();
    clearTimeout(shapeSnapTimer); clearTimeout(longPressTimer); clearTimeout(laserFadeTimer);
    activeDrawId=null; quizDrawCardId=null; drawCtx=null; isDrawing=false;
    currentStroke=null; selectedStrokes=null; selectionPath=[]; laserStrokes=[];
    isMovingSelection=false; moveStartPos=null; activeResizeRect=null; resizeDragHandle=null;
    shapeSnapMode=null; shapeSnapData=null;
    document.body.classList.remove('drawing-active');
}
const sharedShowNextCard=showNextCard;
showNextCard=function(){finishDeckInteraction();return sharedShowNextCard();};
const sharedExitQuiz=exitQuiz;
exitQuiz=function(){finishDeckInteraction();return sharedExitQuiz();};
const sharedStartQuizWith=startQuizWith;
startQuizWith=function(ids,options={}){finishDeckInteraction();return sharedStartQuizWith(ids,options);};

function deckConfirmReset(){document.getElementById('deckResetDialog').showModal();}
document.addEventListener('DOMContentLoaded',()=>{
    const button=document.getElementById('btnReset');
    button.setAttribute('onclick','deckConfirmReset()');
    button.innerHTML='전체 다시 풀기<br><small>학습 기록 초기화</small>';
    const reset=document.createElement('button'); reset.id='btnQuizReset';
    reset.className='undo-btn';reset.type='button';reset.textContent='초기화';
    reset.onclick=deckConfirmReset;
    document.getElementById('quizHeader').insertBefore(reset,document.getElementById('undoBtn'));
    const dialog=document.createElement('dialog');dialog.id='deckResetDialog';
    dialog.setAttribute('aria-labelledby','deckResetTitle');
    dialog.innerHTML='<h3 id="deckResetTitle">56문제 학습 기록을 초기화할까요?</h3><p>복습 일정·평가·진도만 지우고 처음부터 시작합니다.<br>수정 답안·개인 메모·필기는 유지됩니다.</p><div class="reset-actions"><button id="deckResetCancel">취소</button><button id="deckResetConfirm">초기화하고 시작</button></div>';
    document.body.appendChild(dialog);
    document.getElementById('deckResetCancel').onclick=()=>dialog.close();
    document.getElementById('deckResetConfirm').onclick=()=>{
        dialog.close();finishDeckInteraction();doneSet.clear();
        document.querySelectorAll('.card.done').forEach(el=>el.classList.remove('done'));
        document.querySelectorAll('.done-btn').forEach(el=>{el.classList.remove('checked');el.textContent='✓ 완료';});
        updateProgress();
        document.getElementById('undoBtn').disabled=true;
        doResetQuiz();updateReviewBtn();
    };
});
