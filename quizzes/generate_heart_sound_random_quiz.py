#!/usr/bin/env python3
"""심음 청진 APTM 랜덤 감별 퀴즈 생성기."""

import base64
import io
import json
import os
from pathlib import Path
from pdf2image import convert_from_path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "quizzes" / "심음청진_APTM_랜덤퀴즈.html"
PDF_CANDIDATES = [
    os.environ.get("HEART_SOUND_PDF"),
    str(ROOT / "심음_청진_정리.pdf"),
]

POSITIONS = ["A", "P", "T", "M"]
DISEASES = [
    {
        "id": "AS",
        "name": "AS",
        "full": "Aortic Stenosis",
        "primary": "A",
        "pattern": {
            "A": "Systolic murmur, 주 위치",
            "P": "Systolic murmur",
            "T": "Systolic murmur",
            "M": "Systolic murmur",
        },
        "keywords": ["A부터 이상", "systolic", "A가 주 위치", "전 구역 systolic"],
        "tip": "A부터 systolic murmur가 들리고 PDA 기차소리가 아니면 AS/PS 후보. A가 주 위치면 AS 쪽으로 잡는다.",
    },
    {
        "id": "AR",
        "name": "AR",
        "full": "Aortic Regurgitation",
        "primary": "A",
        "pattern": {
            "A": "Diastolic murmur, 주 위치",
            "P": "Diastolic murmur",
            "T": "Diastolic murmur",
            "M": "거의 정상",
        },
        "keywords": ["A부터 이상", "diastolic", "M 거의 정상"],
        "tip": "A부터 들리는데 diastolic이면 AR로 확정에 가깝다. AR은 M에서 거의 정상으로 빠지는 흐름이 포인트.",
    },
    {
        "id": "MS",
        "name": "MS",
        "full": "Mitral Stenosis",
        "primary": "M",
        "pattern": {
            "A": "정상",
            "P": "정상",
            "T": "Diastolic rumbling murmur, 작게 들림",
            "M": "Opening snap + Mid-diastolic rumbling murmur, 주 위치, 두두두두",
        },
        "keywords": ["P까지 정상", "T부터 diastolic rumbling", "M 두두두두", "opening snap"],
        "tip": "P까지 정상인데 T/M에서 diastolic rumbling이 나오고 M에서 두두두두가 주 위치면 MS.",
    },
    {
        "id": "MR",
        "name": "MR",
        "full": "Mitral Regurgitation",
        "primary": "M",
        "pattern": {
            "A": "정상",
            "P": "Systolic murmur, Dub 들림",
            "T": "Pansystolic murmur, Dub 안 들리기 시작",
            "M": "Pansystolic murmur, 주 위치",
        },
        "keywords": ["A 정상", "P부터 systolic", "T에서 Dub 사라짐", "M pansystolic 주 위치"],
        "tip": "A 정상이고 P부터 이상이면 MR/ASD 후보. T에서 Dub가 사라지고 pansystolic으로 변하면 MR.",
    },
    {
        "id": "TR",
        "name": "TR",
        "full": "Tricuspid Regurgitation",
        "primary": "T",
        "pattern": {
            "A": "정상",
            "P": "정상",
            "T": "LubDub 들리며 Pansystolic murmur, 주 위치",
            "M": "LubDub 들리면서 Pansystolic murmur",
        },
        "keywords": ["P까지 정상", "T부터 pansystolic", "LubDub 남아 있음", "T 주 위치"],
        "tip": "P까지 정상인 T-start 질환. LubDub가 남아 있는 끊기는 pansystolic이 T에서 제일 크면 TR.",
    },
    {
        "id": "PS",
        "name": "PS",
        "full": "Pulmonary Stenosis",
        "primary": "P",
        "pattern": {
            "A": "Mid-systolic murmur",
            "P": "Mid-systolic murmur, 주 위치이나 A와 비슷",
            "T": "Mid-systolic murmur",
            "M": "Lub 크게 들리고 정상",
        },
        "keywords": ["A부터 이상", "mid-systolic", "P 주 위치", "M 정상에 가까움"],
        "tip": "A부터 systolic이면 AS/PS. P가 주 위치이고 mid-systolic이며 M은 Lub 크게 들리고 정상 쪽이면 PS.",
    },
    {
        "id": "PDA",
        "name": "PDA",
        "full": "Patent Ductus Arteriosus",
        "primary": "P",
        "pattern": {
            "A": "기차소리",
            "P": "Continuous murmur, 주 위치",
            "T": "기차소리",
            "M": "기차소리",
        },
        "keywords": ["기차소리", "continuous", "P 주 위치", "A부터 이상"],
        "tip": "기차소리/continuous가 보이면 PDA. 특히 P에서 최대다.",
    },
    {
        "id": "ASD",
        "name": "ASD",
        "full": "Atrial Septal Defect",
        "primary": "P",
        "pattern": {
            "A": "정상",
            "P": "Pansystolic murmur with fixed S2 splitting, 주 위치",
            "T": "Fixed S2 splitting이 더 뚜렷한 Systolic murmur",
            "M": "정상",
        },
        "keywords": ["A 정상", "P부터 이상", "fixed S2 splitting", "M 정상"],
        "tip": "A 정상, P부터 이상이면 MR/ASD. fixed S2 splitting이 들리면 ASD로 간다.",
    },
    {
        "id": "VSD",
        "name": "VSD",
        "full": "Ventricular Septal Defect",
        "primary": "T",
        "pattern": {
            "A": "정상",
            "P": "정상",
            "T": "Lub만 들리는 Holosystolic murmur, 주 위치, 부우욱",
            "M": "Holosystolic murmur",
        },
        "keywords": ["P까지 정상", "T부터 holosystolic", "Lub만 들림", "부우욱"],
        "tip": "P까지 정상이고 T에서 Lub만 들리는 holosystolic, 부우욱이면 VSD.",
    },
]

ORDER_TIPS = [
    "A에서 이상 → AS, AR, PS, PDA",
    "A 정상, P부터 이상 → MR 또는 ASD를 먼저 의심",
    "P까지 정상, T부터 이상 → VSD, MS, TR",
    "A부터 systolic → AS or PS. A 주 위치면 AS, P 주 위치면 PS",
    "A부터 diastolic → AR",
    "기차소리/continuous → PDA, 특히 P에서 최대",
    "fixed S2 splitting → ASD",
    "T에서 Lub만 들리는 holosystolic, 부우욱 → VSD",
    "M에서 opening snap + mid-diastolic rumbling, 두두두두 → MS",
    "LubDub 남아 있는 pansystolic이 T에서 최대 → TR",
]


def resolve_pdf():
    for c in PDF_CANDIDATES:
        if c and Path(c).exists():
            return Path(c)
    raise FileNotFoundError("HEART_SOUND_PDF=/path/to/pdf 로 심음 청진 PDF를 지정하세요.")


def page_image(pdf):
    img = convert_from_path(str(pdf), dpi=170)[0]
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=86)
    return base64.b64encode(buf.getvalue()).decode()


def build_html(source_image):
    data_json = json.dumps(DISEASES, ensure_ascii=False)
    tips_json = json.dumps(ORDER_TIPS, ensure_ascii=False)
    css = r'''
:root{--bg:#101827;--panel:#182136;--panel2:#222d49;--text:#edf2ff;--muted:#a6adbb;--line:#334155;--pri:#8ab4ff;--green:#4ade80;--red:#fb7185;--orange:#fbbf24;--blue:#60a5fa;--paper:#fffdf7;--ink:#1f2937}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,#1e3a8a33,transparent 34%),linear-gradient(135deg,#0f172a,#1e1b4b);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.app{display:grid;grid-template-columns:310px 1fr;min-height:100vh}.side{background:rgba(15,23,42,.96);border-right:1px solid var(--line);padding:18px;position:sticky;top:0;height:100vh;overflow:auto}.title{font-size:20px;font-weight:950}.sub{color:var(--muted);font-size:13px;line-height:1.55;margin-top:7px}.main{padding:24px;max-width:1220px;width:100%;margin:0 auto}.card{background:rgba(24,33,54,.96);border:1px solid rgba(148,163,184,.24);border-radius:24px;box-shadow:0 24px 90px rgba(0,0,0,.28);overflow:hidden}.head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:20px 22px;border-bottom:1px solid var(--line)}.h{font-size:24px;font-weight:950}.cue{color:#cbd5e1;font-size:14px;margin-top:5px}.score{font-size:13px;color:#bfdbfe}.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(360px,.9fr);gap:18px;padding:18px}.panel{background:rgba(15,23,42,.7);border:1px solid var(--line);border-radius:18px;padding:16px}.panel h3{margin:0 0 12px;font-size:15px;color:#bfdbfe}.aptm{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.slot{background:#0f172a;border:1px solid #334155;border-radius:16px;min-height:130px;padding:12px;position:relative}.slot.revealed{background:#fffdf7;color:#1f2937;border-color:#facc15}.pos{font-size:28px;font-weight:950;color:#93c5fd}.slot.revealed .pos{color:#1d4ed8}.kw{font-size:16px;line-height:1.5;margin-top:8px}.hidden{color:#64748b;font-size:14px;margin-top:14px}.controls{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.controls button,.choice,.topbtn{border:0;border-radius:12px;padding:10px 12px;font-weight:850;cursor:pointer}.controls button{background:#334155;color:#e2e8f0}.controls .primary{background:var(--pri);color:#0f172a}.choices{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px}.choice{background:#24324e;color:#e5e7eb;border:1px solid #3d4d70}.choice.correct{background:#bbf7d0;color:#14532d;border-color:#22c55e}.choice.wrong{background:#fecdd3;color:#881337;border-color:#fb7185}.answer{margin-top:14px;background:#ecfdf5;color:#14532d;border-radius:16px;padding:14px;line-height:1.65;display:none}.answer.visible{display:block}.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.chip{font-size:12px;border-radius:999px;padding:4px 9px;background:#dbeafe;color:#1e3a8a;font-weight:800}.tipBox{background:#fef3c7;color:#78350f;border-radius:14px;padding:12px;margin-top:12px;line-height:1.6}.imageBox{background:#0b1220;border-radius:18px;padding:10px}.imageBox img{width:100%;border-radius:12px;background:white;display:block}.imageLabel{font-size:12px;color:#cbd5e1;margin-bottom:8px}.tips{display:flex;flex-direction:column;gap:8px;margin-top:14px}.tips div{background:#111827;border:1px solid #334155;border-radius:10px;padding:9px;color:#dbeafe;font-size:13px;line-height:1.4}.mode{display:flex;gap:8px;margin-top:12px}.mode button{flex:1}.small{font-size:12px;color:var(--muted)}@media(max-width:900px){.app{display:block}.side{height:auto;position:relative}.grid{grid-template-columns:1fr}.aptm{grid-template-columns:1fr 1fr}.choices{grid-template-columns:1fr 1fr}.main{padding:12px}}
'''
    js = r'''
const DISEASES = __DATA__;
const ORDER_TIPS = __TIPS__;
const SRC_IMG = '__IMG__';
let current = null;
let revealed = 0;
let answered = false;
let score = JSON.parse(localStorage.getItem('heart_sound_aptm_score_v1') || '{"ok":0,"total":0}');
function esc(s){return String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));}
function shuffle(arr){return [...arr].sort(()=>Math.random()-0.5);}
function pick(){current = DISEASES[Math.floor(Math.random()*DISEASES.length)]; revealed = 0; answered = false; render();}
function revealNext(){if(revealed<4) revealed++; render();}
function revealAll(){revealed=4; render();}
function clueHtml(){return ['A','P','T','M'].map((p,i)=>{const show=i<revealed; return `<div class="slot ${show?'revealed':''}"><div class="pos">${p}</div>${show?`<div class="kw">${esc(current.pattern[p])}</div>`:`<div class="hidden">${p} 위치 키워드 숨김</div>`}</div>`}).join('');}
function choicesHtml(){const choices=shuffle(DISEASES.map(d=>d.id)); return choices.map(id=>`<button class="choice" data-id="${id}" onclick="guess('${id}')">${id}</button>`).join('');}
function updateScore(){document.getElementById('score').textContent=`정답 ${score.ok} / ${score.total}`; localStorage.setItem('heart_sound_aptm_score_v1', JSON.stringify(score));}
function guess(id){if(answered)return; answered=true; score.total++; if(id===current.id) score.ok++; document.querySelectorAll('.choice').forEach(b=>{if(b.dataset.id===current.id)b.classList.add('correct'); else if(b.dataset.id===id)b.classList.add('wrong');}); document.getElementById('answer').classList.add('visible'); updateScore();}
function render(){if(!current) current=DISEASES[0]; document.getElementById('quiz').innerHTML=`<div class="head"><div><div class="h">APTM 랜덤 청진 퀴즈</div><div class="cue">A → P → T → M 순서로 키워드를 열고 질환명을 맞히기</div></div><div class="score" id="score"></div></div><div class="grid"><section class="panel"><h3>청진 위치 키워드</h3><div class="aptm">${clueHtml()}</div><div class="controls"><button class="primary" onclick="revealNext()">다음 위치 보기 (${Math.min(revealed+1,4)}/4)</button><button onclick="revealAll()">APTM 모두 보기</button><button onclick="pick()">랜덤 새 문제</button><button onclick="score={ok:0,total:0};updateScore()">점수 초기화</button></div><h3 style="margin-top:18px">정답 선택</h3><div class="choices">${choicesHtml()}</div><div class="answer" id="answer"><b>정답: ${current.id} · ${esc(current.full)}</b><div class="chips"><span class="chip">주 위치 ${current.primary}</span>${current.keywords.map(k=>`<span class="chip">${esc(k)}</span>`).join('')}</div><div class="tipBox">${esc(current.tip)}</div></div></section><section class="panel imageBox"><div class="imageLabel">원문 표 이미지</div><img src="data:image/jpeg;base64,${SRC_IMG}" alt="심음 청진 정리 원문 표"></section></div>`; updateScore();}
function renderTips(){document.getElementById('tips').innerHTML=ORDER_TIPS.map(t=>`<div>${esc(t)}</div>`).join('');}
window.addEventListener('keydown',e=>{if(e.key===' ') {e.preventDefault();revealNext();} if(e.key==='Enter') revealAll(); if(e.key.toLowerCase()==='n') pick();});
pick(); renderTips();
'''.replace('__DATA__', data_json).replace('__TIPS__', tips_json).replace('__IMG__', source_image)
    return f"""<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>심음청진 APTM 랜덤퀴즈</title><style>{css}</style></head><body><div class=\"app\"><aside class=\"side\"><div class=\"title\">심음청진 APTM 랜덤퀴즈</div><div class=\"sub\">A → P → T → M 순서로 키워드를 확인하고 질환을 맞히는 청진 위치 리허설.<br><b>Space</b>: 다음 위치 · <b>Enter</b>: 모두 보기 · <b>N</b>: 새 문제</div><div class=\"mode controls\"><button onclick=\"pick()\">랜덤 시작</button></div><div class=\"tips\" id=\"tips\"></div></aside><main class=\"main\"><div class=\"card\" id=\"quiz\"></div></main></div><script>{js}</script></body></html>"""


if __name__ == "__main__":
    pdf = resolve_pdf()
    image = page_image(pdf)
    OUT.write_text(build_html(image), encoding="utf-8")
    print(f"✅ 생성 완료: {OUT} ({OUT.stat().st_size/1024/1024:.1f} MB, {len(DISEASES)} diseases)")
