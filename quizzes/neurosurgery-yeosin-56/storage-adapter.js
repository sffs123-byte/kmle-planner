// Deck-scoped storage facade: storage failure must not prevent studying.
const deckMemory = new Map();
let deckPersistenceFailed = false;
function warnDeckStorage() {
    deckPersistenceFailed = true;
    const show = () => {
        if (document.getElementById('deck-storage-warning')) return;
        const b = document.createElement('div'); b.id = 'deck-storage-warning';
        b.textContent = '이 브라우저에서 저장이 차단되어, 새로고침하면 이번 학습 기록이 사라질 수 있습니다.';
        document.body.appendChild(b);
    };
    if (document.body) show(); else document.addEventListener('DOMContentLoaded', show, {once:true});
}
const deckStorage = {
    getItem(k) {try {const v = window.localStorage.getItem(k); if(v!==null) deckMemory.set(k,v); return v;} catch(e){warnDeckStorage();return deckMemory.get(k) ?? null;}},
    setItem(k,v) {deckMemory.set(k,String(v));try{window.localStorage.setItem(k,v);}catch(e){warnDeckStorage();}},
    removeItem(k) {deckMemory.delete(k);try{window.localStorage.removeItem(k);}catch(e){warnDeckStorage();}},
    key(i) {try{return window.localStorage.key(i);}catch(e){return [...deckMemory.keys()][i] ?? null;}},
    get length() {try{return window.localStorage.length;}catch(e){return deckMemory.size;}}
};
function deckStoredJson(key, fallback) {
    try {const value=JSON.parse(deckStorage.getItem(key));return value ?? fallback;}
    catch(e) {warnDeckStorage();return fallback;}
}
