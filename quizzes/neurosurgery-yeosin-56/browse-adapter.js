// Read-only collection built from the shared deck. Does not grade, reset or
// replace the active SRS queue; the original cards keep editing/drawing tools.
window.addEventListener('DOMContentLoaded', function () {
    const dialog = document.createElement('dialog');
    dialog.id = 'deckBrowseDialog';
    dialog.setAttribute('aria-labelledby', 'browseTitle');
    dialog.innerHTML = `<div class="browse-head">
      <div><h2 id="browseTitle">퀴즈 모아보기 <small>56문제</small></h2>
      <p id="browseDescription">문제를 골라 펼치세요. 정답은 버튼을 누르면 보여요.</p></div>
      <button id="browseClose" type="button" aria-label="퀴즈 모아보기 닫기">닫기 ×</button>
    </div>
    <div class="browse-toolbar">
      <label class="browse-set-label">시험지<select id="browseSet"><option value="">전체 56문제</option></select></label>
      <label class="browse-search-label">문제 검색<input id="browseSearch" type="search" placeholder="문제 번호 또는 검색어" autocomplete="off"></label>
      <label class="browse-category-label">주제<select id="browseCategory"><option value="">전체 주제</option></select></label>
      <button id="browseClear" type="button">검색 지우기</button>
      <p id="browseCount" role="status" aria-live="polite"></p>
    </div>
    <p id="browseSetNote" hidden>시험지 원문 질문과 기존 원문 필기를 사용합니다.</p>
    <div id="browseList"></div><p id="browseEmpty" hidden>일치하는 문제가 없어요. 검색어나 주제를 바꿔보세요.</p>`;
    document.body.appendChild(dialog);
    const search = document.getElementById('browseSearch');
    const category = document.getElementById('browseCategory');
    const set = document.getElementById('browseSet');
    Object.entries(DECK_EXAM_SETS).forEach(([id, exam]) => {
        const option = document.createElement('option');
        option.value = id; option.textContent = exam.label + ' · ' + exam.items.length + '문제'; set.appendChild(option);
    });
    [...new Set(Object.values(DECK_CATEGORIES))].forEach(name => {
        const option = document.createElement('option');
        option.value = name; option.textContent = name; category.appendChild(option);
    });
    const list = document.getElementById('browseList');
    const rows = ALL_IDS.map(id => {
        const data = QUIZ_DATA[id];
        const source = document.createElement('div'); source.innerHTML = data.q;
        const question = source.querySelector('.source-question-text')?.textContent || source.textContent.trim();
        const row = document.createElement('details');
        row.className = 'browse-item'; row.dataset.cardId = id;
        const summary = document.createElement('summary');
        const number = document.createElement('span'); number.className = 'browse-num'; number.textContent = data.num;
        const title = document.createElement('span'); title.className = 'browse-question'; title.textContent = question;
        summary.append(number, title); row.appendChild(summary);
        row.addEventListener('toggle', () => {
            if (!row.open || row.dataset.loaded) return;
            row.dataset.loaded = 'true';
            const body = document.createElement('div'); body.className = 'browse-content';
            const fullQuestion = document.createElement('div'); fullQuestion.innerHTML = studyQuestion(id, set.value || 'all');
            // Main wording is already in the summary; retain source details/media.
            fullQuestion.querySelector('.source-question')?.remove();
            body.appendChild(fullQuestion);
            const actions = document.createElement('div'); actions.className = 'browse-actions';
            const reveal = document.createElement('button'); reveal.type = 'button';
            reveal.className = 'browse-reveal'; reveal.textContent = '정답 보기';
            reveal.setAttribute('aria-expanded', 'false');
            const go = document.createElement('button'); go.type = 'button'; go.textContent = '원래 카드 · 필기';
            go.onclick = () => { dialog.close(); exitQuiz(); scrollToCard(id); };
            actions.append(reveal, go); body.appendChild(actions);
            const answer = document.createElement('div'); answer.className = 'browse-answer'; answer.hidden = true;
            answer.id = 'browse-answer-' + id; reveal.setAttribute('aria-controls', answer.id);
            reveal.onclick = () => {
                const show = answer.hidden;
                answer.hidden = !show;
                reveal.textContent = show ? '정답 숨기기' : '정답 보기';
                reveal.setAttribute('aria-expanded', String(show));
                if (show) {
                    answer.innerHTML = Object.prototype.hasOwnProperty.call(edits, id) ? edits[id] : data.a;
                    if (data.g) {
                        const guide = document.createElement('details'); guide.className = 'browse-guide';
                        const label = document.createElement('summary'); label.textContent = '상세 해설 · 용어 풀이';
                        const text = document.createElement('div'); text.innerHTML = data.g;
                        guide.append(label, text); answer.appendChild(guide);
                    }
                }
            };
            body.appendChild(answer); row.appendChild(body);
        });
        list.appendChild(row);
        return {row, id, number, title};
    });
    const hashForSet = () => '#browse';
    function filter() {
        const term = search.value.normalize('NFKC').trim().toLocaleLowerCase();
        const number = term.match(/^(?:#|q)?\s*(\d+)\s*번?$/i);
        const words = term.split(/\s+/).filter(Boolean);
        const exam = DECK_EXAM_SETS[set.value];
        const numbers = new Map((exam ? exam.items : ALL_IDS.map(id => ({id, num: Number(QUIZ_DATA[id].num)}))).map(i => [i.id, i.num]));
        const total = numbers.size;
        document.getElementById('browseTitle').textContent = (exam ? exam.label + ' 모아보기' : '퀴즈 모아보기') + ' · ' + total + '문제';
        document.getElementById('browseDescription').textContent = exam ? exam.source + ' · 원래 문항 순서 / 정답은 눌러서 확인' : '전체 중복통합 56문제 · 문제를 골라 펼치세요.';
        document.getElementById('browseSetNote').hidden = !exam;
        document.getElementById('browseSetNote').textContent = '시험지 원문 질문과 기존 원문 필기를 사용합니다.';
        search.placeholder = exam ? exam.label + ' 문항 번호 또는 검색어' : '문제 번호 또는 검색어';
        let count = 0;
        [...rows].sort((a, b) => (numbers.get(a.id) || 999) - (numbers.get(b.id) || 999)).forEach(({row, id, title, number: badge}) => {
            const source = document.createElement('div');source.innerHTML = studyQuestion(id, set.value || 'all');
            title.textContent = source.querySelector('.source-question-text')?.textContent || source.textContent;
            const question = title.textContent.normalize('NFKC').toLocaleLowerCase();
            list.appendChild(row);
            const n = numbers.get(id);
            badge.textContent = n || QUIZ_DATA[id].num;
            row.dataset.examNumber = n || '';
            const match = Boolean(n) && (!category.value || DECK_CATEGORIES[id] === category.value) &&
                (number ? n === Number(number[1]) : words.every(word => question.includes(word)));
            row.hidden = !match; if (match) count++;
        });
        document.getElementById('browseCount').textContent = (exam ? exam.label + ' · ' : '') + count + ' / ' + total + '문제';
        document.getElementById('browseEmpty').hidden = count !== 0;
    }
    function hideAnswers() {
        rows.forEach(({row}) => {
            row.open = false;
            const answer = row.querySelector('.browse-answer');
            if (answer) answer.hidden = true;
            const reveal = row.querySelector('.browse-reveal');
            if (reveal) {reveal.textContent = '정답 보기'; reveal.setAttribute('aria-expanded', 'false');}
        });
    }
    set.addEventListener('change', () => {
        search.value = ''; category.value = ''; hideAnswers();
        rows.forEach(({row}) => {row.querySelector('.browse-content')?.remove();delete row.dataset.loaded;});filter();
        if (dialog.open) window.history.replaceState(null, '', hashForSet());
    });
    search.addEventListener('input', filter); category.addEventListener('change', filter);
    document.getElementById('browseClear').onclick = () => {search.value = ''; category.value = ''; filter(); search.focus();};
    document.getElementById('browseClose').onclick = () => dialog.close();
    let previousOverflow = '';
    function open(scope = '') {
        set.value = scope;
        search.value = ''; category.value = '';
        hideAnswers();
        rows.forEach(({row}) => {row.querySelector('.browse-content')?.remove();delete row.dataset.loaded;});filter();
        if (dialog.open) return;
        // Hide answers left open on the previous visit; never expose them merely
        // by opening the collection. Existing study state stays untouched.
        previousOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        filter(); dialog.showModal();
        window.history.replaceState(null, '', hashForSet());
        document.getElementById('browseClose').focus();
    }
    dialog.addEventListener('close', () => {
        document.body.style.overflow = previousOverflow;
        if (['#browse', '#browse-set2'].includes(location.hash)) window.history.replaceState(null, '', location.pathname + location.search);
    });
    function button(id, parent, css, scope = '') {
        const b = document.createElement('button'); b.id = id; b.type = 'button';
        b.className = css; b.textContent = scope === '2' ? '2세트 모아보기 · 20문제' : '퀴즈 모아보기'; b.onclick = () => open(scope);
        parent.appendChild(b);
    }
    button('btnBrowseHero', document.getElementById('reviewHero').lastElementChild, 'review-hero-btn browse-entry');
    button('btnBrowseSidebar', document.querySelector('.sb-quiz-btns'), 'btn-review');
    button('btnBrowseQuiz', document.getElementById('quizHeader'), 'undo-btn');
    function openHash() {
        if (location.hash === '#browse') open();
    }
    window.addEventListener('hashchange', openHash);
    filter();
    openHash();
});
