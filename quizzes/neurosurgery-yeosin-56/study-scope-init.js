// Scope only learning state; answers, personal edits and ink keep canonical IDs.
const STUDY_SCOPE_KEY = STORAGE_PREFIX + 'study_scope_v1';
function studyHashScope() {
    const match = location.hash.match(/^#(?:study|browse)-set(2|C)$/i);
    return match ? match[1].toUpperCase() : location.hash === '#study-all' ? 'all' : null;
}
let storedStudyScope = deckStorage.getItem(STUDY_SCOPE_KEY);
try {storedStudyScope = JSON.parse(storedStudyScope);} catch (_) { /* early raw-key compatibility */ }
let deckStudyScope = studyHashScope() || (storedStudyScope ? String(storedStudyScope) : 'all');
if (deckStudyScope !== 'all' && !DECK_EXAM_SETS[deckStudyScope]) deckStudyScope = 'all';
if (/^#browse-set/i.test(location.hash)) window.history.replaceState(null, '', '#study-set' + deckStudyScope);
function scopeStorageKey(suffix) {
    return STORAGE_PREFIX + (deckStudyScope === 'all' ? '' : 'set_' + deckStudyScope + '_') + suffix;
}
function studyIds() {return DECK_EXAM_SETS[deckStudyScope]?.items.map(i => i.id) || ALL_IDS;}
function studyLabel() {return DECK_EXAM_SETS[deckStudyScope]?.label || '전체';}
function studyNumber(id) {return DECK_EXAM_SETS[deckStudyScope]?.items.find(i => i.id === id)?.num ?? QUIZ_DATA[id]?.num;}
function studyQuestion(id, scope = deckStudyScope) {return DECK_SOURCE_QUESTIONS[scope]?.[id] || QUIZ_DATA[id]?.q || '';}
