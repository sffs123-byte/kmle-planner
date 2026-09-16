/* 신경외과 여신 56 · 2026-09-16.1 · no dependencies */
(() => {
  'use strict';
  const VERSION = '2026-09-16.1';
  const STORAGE_PREFIX = 'neurosurgery_yeosin_56_v1:';
  const STATE_KEY = `${STORAGE_PREFIX}study`;
  const MEMO_PREFIX = `${STORAGE_PREFIX}memo:`;
  const rawDeck = Array.isArray(window.YEOSIN_DECK) ? window.YEOSIN_DECK : [];
  const $ = id => document.getElementById(id);
  const deck = rawDeck.map((card, i) => ({ ...card, id: String(card.id ?? i + 1), num: Number(card.num) || i + 1, question: String(card.question ?? '') }));
  const byId = new Map(deck.map(card => [card.id, card]));
  const memory = new Map();
  let storageOK = true;
  let pendingConfirm = null;
  function storageFailure() { storageOK = false; $('storage-warning').hidden = false; }
  function readStorage(key) {
    if (!storageOK) return memory.get(key) ?? null;
    try { const value = localStorage.getItem(key); if (value !== null) memory.set(key, value); return value; }
    catch (_) { storageFailure(); return memory.get(key) ?? null; }
  }
  function writeStorage(key, value) {
    memory.set(key, value);
    if (storageOK) { try { localStorage.setItem(key, value); } catch (_) { storageFailure(); } }
  }
  function removeStorage(key) {
    memory.delete(key);
    if (storageOK) { try { localStorage.removeItem(key); } catch (_) { storageFailure(); } }
  }
  const defaults = () => ({ schema: 1, version: VERSION, mode: 'ordered', filter: 'all', category: 'all', queue: [], index: 0, revealed: false, complete: false, records: {}, runStartedAt: Date.now() });
  let state = defaults();

  function shuffle(ids) {
    const result = [...ids];
    for (let i = result.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [result[i], result[j]] = [result[j], result[i]]; }
    return result;
  }
  function candidates() {
    return deck.filter(card => (state.category === 'all' || card.category === state.category) && (state.filter !== 'again' || state.records[card.id]?.status === 'again')).map(card => card.id);
  }
  function save() { writeStorage(STATE_KEY, JSON.stringify(state)); }
  function beginRun() {
    const ids = candidates();
    state.queue = state.mode === 'random' ? shuffle(ids) : ids;
    state.index = 0; state.revealed = false; state.complete = false; state.runStartedAt = Date.now();
    save(); render();
  }
  function loadState() {
    const saved = readStorage(STATE_KEY);
    if (!saved) return false;
    try {
      const parsed = JSON.parse(saved);
      if (parsed.schema !== 1 || !Array.isArray(parsed.queue)) return false;
      state = { ...defaults(), ...parsed };
      state.mode = state.mode === 'random' ? 'random' : 'ordered';
      state.filter = state.filter === 'again' ? 'again' : 'all';
      if (state.category !== 'all' && !deck.some(c => c.category === state.category)) state.category = 'all';
      state.records = Object.fromEntries(Object.entries(state.records && typeof state.records === 'object' ? state.records : {}).filter(([id, entry]) => byId.has(id) && entry && ['known', 'again'].includes(entry.status)).map(([id, entry]) => [id, { status: entry.status, reviews: Math.max(1, Number(entry.reviews) || 1), last: Number(entry.last) || Date.now() }]));
      const validQueue = state.queue.length > 0 && state.queue.every(id => typeof id === 'string' && byId.has(id) && (state.category === 'all' || byId.get(id).category === state.category)) && new Set(state.queue).size === state.queue.length;
      if (!validQueue) return false;
      state.index = Math.max(0, Math.min(state.queue.length - 1, Math.floor(Number(state.index) || 0)));
      state.revealed = Boolean(state.revealed); state.complete = Boolean(state.complete);
      return true;
    } catch (_) { state = defaults(); return false; }
  }
  function currentCard() { return byId.get(state.queue[state.index]); }
  function statusLabel(id) { return state.records[id]?.status === 'known' ? '외웠어요' : state.records[id]?.status === 'again' ? '다시 볼 문제' : '아직 평가 전'; }
  function stats(ids = deck.map(c => c.id)) {
    return ids.reduce((s, id) => { const status = state.records[id]?.status; if (status === 'known') s.known++; if (status === 'again') s.again++; return s; }, { known: 0, again: 0 });
  }
  function announce(message) { $('announcement').textContent = message; }

  // Stored note HTML is content, not application code. Keep rich text; discard active content.
  const allowedTags = new Set('P BR STRONG B EM I U S DEL MARK SPAN DIV UL OL LI H1 H2 H3 H4 H5 H6 TABLE THEAD TBODY TR TH TD BLOCKQUOTE A IMG HR SUP SUB CODE PRE DETAILS SUMMARY'.split(' '));
  function safeUrl(url, image = false) {
    const value = String(url || '').trim();
    if (image && /^data:image\/(?:png|jpeg|webp|gif);base64,/i.test(value)) return value;
    try { const parsed = new URL(value, location.href); return ['http:', 'https:'].includes(parsed.protocol) ? value : null; } catch (_) { return null; }
  }
  function richFragment(html) {
    const parsed = new DOMParser().parseFromString(String(html || ''), 'text/html');
    const fragment = document.createDocumentFragment();
    function copy(node, target) {
      if (node.nodeType === Node.TEXT_NODE) { target.append(document.createTextNode(node.textContent)); return; }
      if (node.nodeType !== Node.ELEMENT_NODE) return;
      if (['SCRIPT', 'STYLE', 'IFRAME', 'OBJECT', 'EMBED', 'FORM', 'INPUT', 'BUTTON', 'TEXTAREA', 'SELECT', 'SVG', 'MATH'].includes(node.tagName)) return;
      if (!allowedTags.has(node.tagName)) { [...node.childNodes].forEach(child => copy(child, target)); return; }
      const element = document.createElement(node.tagName.toLowerCase());
      if (node.tagName === 'A') { const href = safeUrl(node.getAttribute('href')); if (href) { element.href = href; element.target = '_blank'; element.rel = 'noopener noreferrer'; } }
      if (node.tagName === 'IMG') { const src = safeUrl(node.getAttribute('src'), true); if (!src) return; element.src = src; element.alt = node.getAttribute('alt') || ''; element.loading = 'lazy'; }
      if (['TD', 'TH'].includes(node.tagName)) for (const key of ['colspan', 'rowspan']) { const n = Number(node.getAttribute(key)); if (n > 0 && n <= 10) element.setAttribute(key, String(n)); }
      if (node.tagName === 'OL') { const n = Number(node.getAttribute('start')); if (n > 0 && n < 1000) element.start = n; }
      for (const key of ['color', 'background-color', 'font-weight', 'text-decoration']) { const value = node.style?.getPropertyValue(key); if (value && !/url\s*\(|expression|var\s*\(/i.test(value)) element.style.setProperty(key, value); }
      [...node.childNodes].forEach(child => copy(child, element)); target.append(element);
    }
    [...parsed.body.childNodes].forEach(node => copy(node, fragment)); return fragment;
  }
  function setRich(id, html) { $(id).replaceChildren(richFragment(html)); }

  function renderAnswer(card) {
    $('reveal').hidden = state.revealed;
    $('reveal').setAttribute('aria-expanded', String(state.revealed));
    $('answer').hidden = !state.revealed;
    if (!state.revealed) {
      for (const id of ['answer-body', 'explanation', 'terms']) $(id).replaceChildren();
      $('memo').value = ''; $('source').removeAttribute('href'); return;
    }
    setRich('answer-body', card.answerHtml || '<p>원본에서 정답을 확인해 주세요.</p>');
    const hasExplanation = Boolean(card.explanationHtml && String(card.explanationHtml).trim());
    $('explanation-wrap').hidden = !hasExplanation; setRich('explanation', card.explanationHtml || '');
    const terms = Array.isArray(card.terms) ? card.terms.filter(t => t && t.term && t.definition) : [];
    $('terms-wrap').hidden = terms.length === 0; $('terms-count').textContent = `· ${terms.length}`; $('terms').replaceChildren();
    terms.forEach(term => { const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = term.term; dd.textContent = term.definition; $('terms').append(dt, dd); });
    const memo = readStorage(`${MEMO_PREFIX}${card.id}`) || '';
    $('memo').value = memo; $('memo-indicator').textContent = memo ? '· 있음' : '';
    $('memo-status').textContent = storageOK ? '이 브라우저에 자동저장 · 기록 초기화 후에도 보존' : '이번 화면에만 보관됩니다.';
    const url = safeUrl(card.sourceUrl); if (url) { $('source').href = url; $('source').hidden = false; } else $('source').hidden = true;
  }
  function render() {
    $('mode').value = state.mode; $('filter').value = state.filter; $('category').value = state.category;
    const total = state.queue.length, global = stats();
    $('study-stats').textContent = `외움 ${global.known} · 다시 ${global.again} / ${deck.length}`;
    $('run-progress').textContent = total ? (state.complete ? `${total} / ${total} · 회차 완료` : `${state.index + 1} / ${total} · ${state.mode === 'random' ? '랜덤' : '순서대로'}`) : '0개 선택됨';
    $('progress').max = Math.max(1, total); $('progress').value = state.complete ? total : state.index;
    $('card').hidden = !total || state.complete; $('complete').hidden = !total || !state.complete; $('empty').hidden = total > 0;
    $('navigation').hidden = !total;
    $('previous').disabled = !total || (!state.complete && state.index === 0);
    $('next').disabled = !total || state.complete;
    $('next').textContent = state.index === total - 1 ? '회차 마치기 →' : '다음 →';
    if (!total) { $('empty-title').textContent = state.filter === 'again' ? '다시 볼 문제가 없어요' : '표시할 문제가 없어요'; $('empty-description').textContent = state.filter === 'again' ? '정답을 본 뒤 “다시 볼게요”로 표시한 문제가 여기에 모여요.' : '다른 범위를 선택해 주세요.'; }
    if (state.complete) {
      const run = stats(state.queue);
      $('complete-summary').textContent = `이번 범위 ${total}문제 중 외움 ${run.known} · 다시 ${run.again} · 평가 전 ${total - run.known - run.again}\n평가 기록은 남아 있어요. 필요한 문제만 다시 보세요.`;
      const againCount = deck.filter(c => (state.category === 'all' || c.category === state.category) && state.records[c.id]?.status === 'again').length;
      $('review-again').disabled = !againCount; $('review-again').textContent = againCount ? `다시 볼 ${againCount}문제 복습` : '다시 볼 문제 없음';
    }
    // Clear hidden answer text on non-card screens as well: no stale front-side leakage.
    if (!total || state.complete) { for (const id of ['answer-body', 'explanation', 'terms']) $(id).replaceChildren(); $('memo').value = ''; return; }
    const card = currentCard();
    $('question-number').textContent = `문제 ${String(card.num).padStart(2, '0')}`;
    $('question').textContent = card.question;
    $('card-status').textContent = statusLabel(card.id); $('card-status').className = `status ${state.records[card.id]?.status || ''}-text`;
    $('question-images').replaceChildren();
    // Optional answer-neutral images supplied by the audited deck builder.
    for (const img of Array.isArray(card.questionImages) ? card.questionImages : []) {
      const source = typeof img === 'string' ? img : img.src, url = safeUrl(source, true); if (!url) continue;
      const element = document.createElement('img'); element.src = url; element.alt = typeof img === 'object' ? img.alt || '문제 영상' : '문제 영상';
      const link = document.createElement('a'); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.setAttribute('aria-label', '문제 영상 새 탭에서 크게 보기'); link.append(element); $('question-images').append(link);
    }
    const questionSource = card.sourceRequired ? safeUrl(card.sourceUrl) : null;
    $('question-source').hidden = !questionSource; if (questionSource) $('question-source').href = questionSource; else $('question-source').removeAttribute('href');
    renderAnswer(card);
  }
  function move(delta) {
    if (!state.queue.length) return;
    if (state.complete) { if (delta < 0) state.complete = false; else return; }
    else {
      if (state.index + delta < 0) return;
      if (state.index + delta >= state.queue.length) { state.complete = true; }
      else state.index += delta;
    }
    state.revealed = false; closeFolds(); save(); render();
    $('study').focus({ preventScroll: true }); $('study').scrollIntoView({ block: 'start', behavior: 'instant' });
    announce(state.complete ? '이번 회차를 모두 확인했습니다.' : `문제 ${currentCard().num}. 정답은 숨겨져 있습니다.`);
  }
  function closeFolds() { ['explanation-wrap', 'terms-wrap', 'memo-wrap'].forEach(id => { $(id).open = false; }); }
  function reveal(value = true) { if (!currentCard() || state.complete || !state.queue.length) return; state.revealed = value; save(); renderAnswer(currentCard()); announce(value ? '정답이 공개되었습니다.' : '정답을 숨겼습니다.'); }
  function rate(status) {
    if (!state.revealed || state.complete || !currentCard()) return;
    const id = currentCard().id; state.records[id] = { status, reviews: (state.records[id]?.reviews || 0) + 1, last: Date.now() };
    save(); move(1);
  }
  function confirmAction(title, description, label, action) {
    pendingConfirm = action; $('confirm-title').textContent = title; $('confirm-description').textContent = description; $('confirm-ok').textContent = label;
    $('confirm-dialog').showModal(); $('confirm-cancel').focus();
  }
  function requestRestart() {
    confirmAction('현재 범위를 처음부터 풀까요?', '평가와 내 메모는 그대로 두고, 현재 범위의 진행만 처음으로 돌아가요.\n랜덤 모드에서는 새로운 순서로 섞어요.', '다시 시작', () => { if ($('menu-dialog').open) $('menu-dialog').close(); beginRun(); announce('현재 범위의 새 회차를 시작했습니다.'); });
  }
  function requestReset() {
    confirmAction('학습 기록을 초기화할까요?', '이 신경외과 덱의 평가·진행·공개 상태·선택 범위를 지워요.\n내 메모와 다른 퀴즈의 기록은 지우지 않아요.', '초기화', () => { removeStorage(STATE_KEY); state = defaults(); if ($('menu-dialog').open) $('menu-dialog').close(); beginRun(); announce('학습 기록을 초기화했습니다. 내 메모는 보존했습니다.'); });
  }
  function renderList() {
    const query = $('search').value.trim().toLocaleLowerCase();
    const cards = deck.filter(card => (state.category === 'all' || card.category === state.category) && (state.filter !== 'again' || state.records[card.id]?.status === 'again') && (!query || `${card.num} ${card.question}`.toLocaleLowerCase().includes(query)));
    $('search-count').textContent = `${cards.length}개 문제 · 정답은 목록에 표시하지 않아요.`;
    $('question-list').replaceChildren();
    cards.forEach(card => {
      const li = document.createElement('li'), button = document.createElement('button');
      button.type = 'button'; if (card.id === currentCard()?.id && !state.complete) button.className = 'current';
      const number = document.createElement('span'), question = document.createElement('span'), status = document.createElement('span');
      number.className = 'q-number'; number.textContent = String(card.num).padStart(2, '0'); question.className = 'q-text'; question.textContent = card.question; status.className = 'q-state'; status.textContent = statusLabel(card.id);
      button.append(number, question, status); button.addEventListener('click', () => {
        let index = state.queue.indexOf(card.id);
        if (index < 0) { const ids = candidates(); state.queue = state.mode === 'random' ? shuffle(ids) : ids; index = state.queue.indexOf(card.id); }
        if (index < 0) return;
        state.index = index; state.complete = false; state.revealed = false; closeFolds(); save(); $('menu-dialog').close(); render(); $('study').focus({ preventScroll: true });
      }); li.append(button); $('question-list').append(li);
    });
  }

  $('reveal').addEventListener('click', () => reveal()); $('hide-answer').addEventListener('click', () => reveal(false));
  $('previous').addEventListener('click', () => move(-1)); $('next').addEventListener('click', () => move(1));
  $('rate-again').addEventListener('click', () => rate('again')); $('rate-known').addEventListener('click', () => rate('known'));
  for (const key of ['mode', 'filter', 'category']) $(key).addEventListener('change', event => { state[key] = event.target.value; closeFolds(); beginRun(); announce('선택한 범위로 새 회차를 시작했습니다. 평가와 메모는 보존됩니다.'); });
  $('show-all').addEventListener('click', () => { state.filter = 'all'; state.category = 'all'; beginRun(); });
  $('review-again').addEventListener('click', () => { state.filter = 'again'; beginRun(); });
  $('restart').addEventListener('click', requestRestart); $('restart-complete').addEventListener('click', requestRestart); $('reset').addEventListener('click', requestReset);
  $('confirm-cancel').addEventListener('click', () => { pendingConfirm = null; $('confirm-dialog').close(); });
  $('confirm-dialog').addEventListener('cancel', () => { pendingConfirm = null; });
  $('confirm-ok').addEventListener('click', () => { const action = pendingConfirm; pendingConfirm = null; $('confirm-dialog').close(); action?.(); });
  $('open-menu').addEventListener('click', () => { $('search').value = ''; renderList(); $('menu-dialog').showModal(); $('close-menu').focus(); });
  $('close-menu').addEventListener('click', () => $('menu-dialog').close()); $('search').addEventListener('input', renderList);
  $('memo').addEventListener('input', () => { const card = currentCard(); if (!card || !state.revealed) return; writeStorage(`${MEMO_PREFIX}${card.id}`, $('memo').value); $('memo-indicator').textContent = $('memo').value ? '· 있음' : ''; $('memo-status').textContent = storageOK ? '저장됨 · 이 브라우저에 보관' : '이번 화면에만 보관됩니다.'; });
  document.addEventListener('keydown', event => {
    if ($('menu-dialog').open || $('confirm-dialog').open || event.altKey || event.ctrlKey || event.metaKey || event.repeat) return;
    const target = event.target; if (target instanceof Element && (target.closest('input,textarea,select,button,a,summary') || target.isContentEditable)) return;
    if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); reveal(!state.revealed); }
    if (event.key === 'ArrowRight') { event.preventDefault(); move(1); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); move(-1); }
  });

  $('deck-count').textContent = String(deck.length);
  if (deck.length !== 56 || byId.size !== deck.length || deck.some(c => !c.question.trim() || !c.answerHtml)) {
    $('app-error').hidden = false; $('app-error').textContent = '56개 문제 데이터를 온전히 불러오지 못했어요. 새로고침해 주세요.';
    for (const id of ['mode', 'filter', 'category', 'open-menu']) $(id).disabled = true;
    $('run-progress').textContent = '불러오기 오류'; $('study-stats').textContent = ''; return;
  }
  [...new Set(deck.map(card => card.category).filter(Boolean))].forEach(category => { const option = document.createElement('option'); option.value = category; option.textContent = category; $('category').append(option); });
  if (loadState()) { render(); save(); } else beginRun();
})();
