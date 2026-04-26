#!/usr/bin/env python3
"""심장진찰 임상술기 대본 암기 HTML 생성기."""

import base64
import html
import io
import json
import os
from pathlib import Path
from pdf2image import convert_from_path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "quizzes" / "심장진찰_임상술기_암기.html"
PDF_CANDIDATES = [
    os.environ.get("CARDIAC_EXAM_PDF"),
    str(ROOT / "심장진찰_임상술기.pdf"),
]

CARDS = [
    {
        "id": "c1",
        "num": 1,
        "title": "대사 주의사항: 인사·확인·동의",
        "page": 1,
        "cue": "처음 들어가서 학생의사 소개, 환자 확인, 심장진찰 동의까지 말하기",
        "lines": [
            "안녕하세요. 학생의사 OOO입니다.",
            "환자분 성함과 나이 어떻게 되시나요?",
            "지금부터 심장 진찰을 하려 합니다. 괜찮겠습니까?",
        ],
        "actions": [
            "밝게 인사하고 본인 역할을 먼저 밝힌다.",
            "성함과 나이로 환자 확인을 한다.",
            "검사 목적과 동의를 명확히 말한다.",
        ],
    },
    {
        "id": "c2",
        "num": 2,
        "title": "맥박수 측정",
        "page": 1,
        "cue": "맥박수 측정한다고 말하고, 정상 결과를 말한 뒤 측정법을 떠올리기",
        "lines": [
            "맥박수를 측정해보도록 하겠습니다.",
            "맥박수는 60회며 규칙적으로 정상입니다.",
        ],
        "actions": [
            "집게, 가운데, 반지 손가락으로 맥박을 측정한다.",
            "양측 맥박 차이가 있는지 확인한다.",
            "규칙적이면 한쪽 손목에서 15초간 측정하고 4를 곱한다.",
            "비정상적으로 빠르거나 느리면 60초 동안 측정한다.",
        ],
    },
    {
        "id": "c3",
        "num": 3,
        "title": "목 진찰 시작: 자세·노출·목정맥 관찰",
        "page": 1,
        "cue": "목 진찰 시작 멘트와 자세, 목/복장뼈 노출, 목정맥 관찰 순서",
        "lines": [
            "목을 진찰하겠습니다.",
            "베개를 베고, 천장을 보며 편하게 누워주세요.",
            "목과 복장뼈가 충분히 보이도록 옷을 젖혀주세요.",
        ],
        "actions": [
            "양쪽 바깥 목정맥을 찾아낸다.",
            "깊은 곳에서 피부로 전달되는 속목정맥 박동을 확인한다.",
        ],
    },
    {
        "id": "c4",
        "num": 4,
        "title": "목정맥압 JVP 측정",
        "page": 1,
        "cue": "JVP 측정 멘트, 정상값 보고, 측정 방법과 증가 기준",
        "lines": [
            "목정맥압 측정하도록 하겠습니다.",
            "목정맥압 2cm로 정상입니다.",
        ],
        "actions": [
            "속목정맥의 파형 파동 지점을 찾아낸다.",
            "오른쪽 목정맥 박동의 가장 높은 지점을 찾는다.",
            "직각 자를 이용해 그 지점부터 복장뼈 상부까지의 수직 거리를 측정한다.",
            "목정맥압 3~4cm 이상이면 증가 소견이다.",
        ],
    },
    {
        "id": "c5",
        "num": 5,
        "title": "목동맥 촉진·청진",
        "page": 2,
        "cue": "목동맥은 어떻게 촉진하고, 어떤 멘트로 청진하는지",
        "lines": [
            "목동맥 청진하겠습니다. 청진기 차가울 수 있습니다.",
            "불편하면 말씀해주세요.",
        ],
        "actions": [
            "집게와 가운데 손가락을 반지연골에서 목빗근 안쪽으로 압력을 가하며 목동맥을 찾아 촉진한다.",
            "목동맥 촉진은 반드시 양쪽을 순차적으로 시행한다.",
            "양쪽 목동맥을 청진기 종 부분으로 청진한다.",
        ],
    },
    {
        "id": "c6",
        "num": 6,
        "title": "시진: 전흉부 관찰",
        "page": 2,
        "cue": "가슴 노출 멘트 후 전흉부에서 무엇을 보는지",
        "lines": [
            "가슴을 보겠습니다. 윗옷을 벗어주세요.",
        ],
        "actions": [
            "전흉부를 관찰하여 심장 끝 박동과 최대 박동 지점을 찾는다.",
            "손을 따뜻하게 한 후 손가락을 길게 흉벽에 갖다 댄다.",
            "이상 진동이나 밀어 올림이 있는지 촉진한다.",
        ],
    },
    {
        "id": "c7",
        "num": 7,
        "title": "촉진: 심장 끝 박동",
        "page": 2,
        "cue": "심장을 눌러보겠다고 말하고 apex beat 위치와 평가법 말하기",
        "lines": [
            "심장을 눌러보겠습니다.",
        ],
        "actions": [
            "5번째 갈비 사이 높이, 빗장뼈 중간 위치에서 손가락 끝으로 심장 끝 박동을 촉진한다.",
            "심장 끝 박동을 확인하면 한 손가락만 이용하여 박동을 평가한다.",
        ],
    },
    {
        "id": "c8",
        "num": 8,
        "title": "촉진: 우심실·폐동맥·대동맥 박동",
        "page": 3,
        "cue": "숨 내쉬고 멈춘 뒤 왼쪽 복장뼈 옆, 폐동맥, 대동맥 촉진 순서",
        "lines": [
            "숨을 내쉬고, 숨을 잠시 멈춰주세요.",
        ],
        "actions": [
            "손가락을 왼쪽 복장뼈 옆 3, 4, 5번째 갈비 사이에 위치시킨다.",
            "숨을 내쉬고 잠시 멈추게 한 후 우심실 수축기 박동의 위치, 직경, 강도, 기간을 본다.",
            "왼쪽 두 번째 갈비 사이 아래를 촉진해 폐동맥 박동을 확인한다.",
            "폐동맥 박동이 두드러지면 폐동맥 혈류 증가 또는 폐동맥 확장을 의심한다.",
            "오른쪽 두 번째 갈비 사이 아래에서 대동맥 박동을 확인한다.",
            "촉진 가능한 제2심음은 고혈압을 시사하고, 박동이 느껴지면 대동맥 동맥류를 시사한다.",
        ],
    },
    {
        "id": "c9",
        "num": 9,
        "title": "타진: 심장 탁음 경계",
        "page": 3,
        "cue": "심장 두드려보겠다고 말하고 3~6번째 갈비 사이 타진 순서",
        "lines": [
            "심장 두드려보겠습니다.",
        ],
        "actions": [
            "흉부 왼쪽에서 시작한다.",
            "공명음에서 심장 탁음이 들릴 때까지 3, 4, 5, 6번째 갈비 사이를 타진한다.",
            "심장의 크기를 확인하는 데 도움이 된다.",
        ],
    },
    {
        "id": "c10",
        "num": 10,
        "title": "청진: 기본·좌측와위·전굴 자세",
        "page": 4,
        "cue": "청진 멘트, 좌측와위, 앉아서 앞으로 숙이기, 숨 내쉬고 참기까지",
        "lines": [
            "심장 소리 들어보겠습니다. 청진기가 조금 차가울 수 있습니다.",
            "왼쪽 옆으로 돌아 누워주세요.",
            "앉으시고, 상체를 약간 앞으로 숙여 주세요.",
            "숨을 내쉬고, 참아주세요.",
        ],
        "actions": [
            "흉벽에 진동판을 밀착시켜 심음을 청진한다.",
            "좌측와위에서 청진기 종을 이용해 심장 끝을 청진한다.",
            "왼쪽 제3, 4심음과 승모판 잡음 등을 확인한다.",
            "앉아서 상체를 앞으로 숙인 자세에서 진동판으로 심음을 청진한다.",
        ],
    },
    {
        "id": "c11",
        "num": 11,
        "title": "마무리와 전체 순서 회상",
        "page": 4,
        "cue": "마무리 멘트와 전체 진찰 순서 한 번에 회상",
        "lines": [
            "심장 진찰을 마쳤습니다. 협조해주셔서 감사합니다.",
        ],
        "actions": [
            "전체 순서: 인사·동의 → 맥박수 → 목/JVP → 목동맥 → 시진 → 촉진 → 타진 → 청진 → 마무리",
            "실제 시험에서는 말할 대사와 손동작을 끊지 않고 연결한다.",
        ],
    },
]


def resolve_pdf():
    for c in PDF_CANDIDATES:
        if c and Path(c).exists():
            return Path(c)
    raise FileNotFoundError("CARDIAC_EXAM_PDF=/path/to/pdf 로 심장진찰 PDF를 지정하세요.")


def page_images(pdf):
    images = convert_from_path(str(pdf), dpi=170)
    out = {}
    for i, img in enumerate(images, 1):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=84)
        out[i] = base64.b64encode(buf.getvalue()).decode()
    return out


def first_letters(lines):
    hints = []
    for line in lines:
        tokens = [tok for tok in line.replace(".", "").replace(",", "").split() if tok]
        hints.append(" ".join(tok[0] for tok in tokens if tok))
    return hints


def progressive_masks(line):
    words = line.split()
    if len(words) <= 2:
        return [line]
    masks = []
    for ratio in (0.3, 0.6, 0.9):
        keep_every = max(1, round(1 / max(0.05, 1 - ratio)))
        masked = []
        for i, w in enumerate(words):
            masked.append(w if i % keep_every == 0 else "▢" * min(4, max(1, len(w))))
        masks.append(" ".join(masked))
    return masks


def build_html(pages):
    payload = []
    for c in CARDS:
        item = dict(c)
        item["firstLetters"] = first_letters(c["lines"])
        item["masks"] = [progressive_masks(line) for line in c["lines"]]
        payload.append(item)
    data_json = json.dumps(payload, ensure_ascii=False)
    pages_json = json.dumps(pages, ensure_ascii=False)
    css = r"""
:root{--bg:#111827;--panel:#172033;--panel2:#202a44;--text:#eef2ff;--muted:#9ca3af;--line:#334155;--pri:#8ab4ff;--green:#4ade80;--red:#fb7185;--orange:#fbbf24;--blue:#60a5fa;--paper:#fffdf7;--ink:#1f2937}*{box-sizing:border-box}body{margin:0;background:linear-gradient(135deg,#0f172a,#1e1b4b);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.app{display:grid;grid-template-columns:280px 1fr;min-height:100vh}.side{background:rgba(15,23,42,.94);border-right:1px solid var(--line);padding:18px;position:sticky;top:0;height:100vh;overflow:auto}.title{font-weight:900;font-size:19px;margin-bottom:6px}.sub{color:var(--muted);font-size:13px;line-height:1.5}.progress{height:8px;background:#263244;border-radius:999px;overflow:hidden;margin:14px 0 8px}.fill{height:100%;background:linear-gradient(90deg,var(--pri),#c084fc);width:0}.nav{display:flex;flex-direction:column;gap:8px;margin-top:16px}.nav button{border:1px solid var(--line);background:#111827;color:var(--text);padding:10px 11px;border-radius:10px;text-align:left;cursor:pointer}.nav button.active{border-color:var(--pri);background:#1d2b4a}.main{padding:24px;max-width:1180px;width:100%;margin:0 auto}.card{background:rgba(23,32,51,.96);border:1px solid rgba(148,163,184,.25);border-radius:24px;box-shadow:0 24px 80px rgba(0,0,0,.25);overflow:hidden}.head{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:18px 22px;border-bottom:1px solid var(--line)}.hleft{display:flex;gap:12px;align-items:center}.num{background:#31415f;color:#c7d2fe;font-weight:900;padding:7px 10px;border-radius:10px}.h{font-size:21px;font-weight:900}.cue{color:#cbd5e1;font-size:14px;margin-top:4px}.grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr);gap:18px;padding:18px}.panel{background:rgba(15,23,42,.72);border:1px solid var(--line);border-radius:18px;padding:16px}.panel h3{margin:0 0 12px;font-size:15px;color:#bfdbfe}.script{background:var(--paper);color:var(--ink);border-radius:16px;padding:16px;line-height:1.75;font-size:18px;min-height:180px}.line{margin:0 0 12px}.hidden{filter:blur(5px);user-select:none}.hint{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#eef2ff;border:1px dashed #94a3b8;border-radius:12px;padding:10px;margin:8px 0;color:#334155}.mask{background:#fef3c7;border-radius:10px;padding:8px;margin:8px 0;color:#78350f}.actions{display:none;background:#ecfeff;color:#164e63;border-radius:14px;padding:14px;line-height:1.65}.actions.visible{display:block}.actions li{margin:5px 0}.controls{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.controls button,.rating button,.topbtn{border:0;border-radius:11px;padding:10px 12px;font-weight:800;cursor:pointer}.controls button{background:#334155;color:#e2e8f0}.controls button.primary{background:var(--pri);color:#0f172a}.imageBox{background:#0b1220;border-radius:18px;padding:10px}.imageBox img{width:100%;border-radius:12px;display:block;background:white}.imageLabel{font-size:12px;color:#cbd5e1;margin:0 0 8px}.rating{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:0 18px 18px}.rating button{color:#111827}.again{background:var(--red)}.hard{background:var(--orange)}.good{background:var(--green)}.easy{background:var(--blue)}.seq{display:flex;gap:8px}.topbtn{background:#293548;color:#e5e7eb}.small{font-size:12px;color:var(--muted);margin-top:10px}.doneBadge{font-size:12px;color:#86efac;margin-left:8px}.kbd{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#fef08a}@media(max-width:900px){.app{display:block}.side{height:auto;position:relative}.grid{grid-template-columns:1fr}.rating{grid-template-columns:repeat(2,1fr)}.main{padding:12px}.h{font-size:18px}}
"""
    js = r"""
const CARDS = __DATA__;
const PAGE_IMAGES = __PAGES__;
const PREFIX = 'cardiac_exam_memory_v1_';
let idx = Number(localStorage.getItem(PREFIX+'idx')||0);
let state = JSON.parse(localStorage.getItem(PREFIX+'state')||'{}');
let hidden = true;
let hintMode = 'first';
function save(){localStorage.setItem(PREFIX+'idx',idx);localStorage.setItem(PREFIX+'state',JSON.stringify(state));}
function card(){return CARDS[idx];}
function esc(s){return String(s).replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));}
function dueLabel(id){const s=state[id]; if(!s||!s.next)return ''; const d=s.next-Date.now(); if(d<=0)return '복습 가능'; if(d<3600000)return Math.ceil(d/60000)+'분 후'; return Math.ceil(d/3600000)+'시간 후';}
function renderNav(){const nav=document.getElementById('nav');nav.innerHTML=CARDS.map((c,i)=>`<button class="${i===idx?'active':''}" onclick="idx=${i};hidden=true;render()">${c.num}. ${esc(c.title)} ${state[c.id]?.done?'✓':''}<br><span class="small">${dueLabel(c.id)}</span></button>`).join(''); const done=CARDS.filter(c=>state[c.id]?.done).length; document.getElementById('progText').textContent=`${done} / ${CARDS.length} 완료`; document.getElementById('fill').style.width=(done/CARDS.length*100)+'%';}
function scriptHtml(c){return c.lines.map((line,i)=>`<p class="line ${hidden?'hidden':''}">${esc(line)}</p>`).join('');}
function hintHtml(c){if(!hidden)return '<div class="hint">정답 표시 중</div>'; if(hintMode==='first')return c.firstLetters.map(h=>`<div class="hint">${esc(h)}</div>`).join(''); if(hintMode==='mask30')return c.masks.map(m=>`<div class="mask">${esc(m[0])}</div>`).join(''); if(hintMode==='mask60')return c.masks.map(m=>`<div class="mask">${esc(m[1])}</div>`).join(''); return c.masks.map(m=>`<div class="mask">${esc(m[2])}</div>`).join('');}
function render(){const c=card(); document.getElementById('card').innerHTML=`<div class="head"><div class="hleft"><span class="num">${c.num}</span><div><div class="h">${esc(c.title)} ${state[c.id]?.done?'<span class="doneBadge">완료</span>':''}</div><div class="cue">${esc(c.cue)}</div></div></div><div class="seq"><button class="topbtn" onclick="prev()">←</button><button class="topbtn" onclick="next()">→</button></div></div><div class="grid"><section class="panel"><h3>대사 암기</h3><div class="script">${hintHtml(c)}${scriptHtml(c)}</div><div class="controls"><button class="primary" onclick="hidden=!hidden;render()">${hidden?'정답 보기':'다시 가리기'}</button><button onclick="hintMode='first';render()">첫 글자</button><button onclick="hintMode='mask30';render()">30% 가림</button><button onclick="hintMode='mask60';render()">60% 가림</button><button onclick="hintMode='mask90';render()">90% 가림</button><button onclick="toggleActions()">주의사항</button></div><div class="actions" id="actions"><b>행동/주의사항</b><ul>${c.actions.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div></section><section class="panel imageBox"><div class="imageLabel">원문 이미지 앵커 · PDF ${c.page}페이지</div><img src="data:image/jpeg;base64,${PAGE_IMAGES[c.page]}" alt="PDF page ${c.page}"></section></div><div class="rating"><button class="again" onclick="rate('again')">다시<br><small>1분</small></button><button class="hard" onclick="rate('hard')">어려움<br><small>5분</small></button><button class="good" onclick="rate('good')">보통<br><small>10분</small></button><button class="easy" onclick="rate('easy')">완료/내일<br><small>1일</small></button></div>`; renderNav(); save();}
function toggleActions(){document.getElementById('actions')?.classList.toggle('visible');}
function rate(r){const c=card(); const mins={again:1,hard:5,good:10,easy:1440}[r]; state[c.id]={rating:r,next:Date.now()+mins*60000,done:r==='easy'||r==='good'}; save(); next();}
function next(){idx=(idx+1)%CARDS.length;hidden=true;render();}
function prev(){idx=(idx-1+CARDS.length)%CARDS.length;hidden=true;render();}
function resetAll(){if(confirm('암기 진행 상태를 초기화할까요?')){state={};idx=0;hidden=true;save();render();}}
window.addEventListener('keydown',e=>{if(e.key===' ') {e.preventDefault();hidden=!hidden;render();} if(e.key==='ArrowRight')next(); if(e.key==='ArrowLeft')prev();});
render();
""".replace("__DATA__", data_json).replace("__PAGES__", pages_json)
    return f"""<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>심장진찰 임상술기 암기</title><style>{css}</style></head><body><div class=\"app\"><aside class=\"side\"><div class=\"title\">심장진찰 임상술기 암기</div><div class=\"sub\">대사 + 행동 순서 + PDF 원문 이미지 앵커<br><span class=\"kbd\">Space</span>: 정답 보기/가리기 · ←/→ 이동</div><div class=\"progress\"><div class=\"fill\" id=\"fill\"></div></div><div class=\"sub\" id=\"progText\"></div><div class=\"controls\"><button onclick=\"resetAll()\">진행 초기화</button></div><nav class=\"nav\" id=\"nav\"></nav></aside><main class=\"main\"><div class=\"card\" id=\"card\"></div></main></div><script>{js}</script></body></html>"""


if __name__ == "__main__":
    pdf = resolve_pdf()
    pages = page_images(pdf)
    OUT.write_text(build_html(pages), encoding="utf-8")
    print(f"✅ 생성 완료: {OUT} ({OUT.stat().st_size/1024/1024:.1f} MB, {len(CARDS)} cards, {len(pages)} page images)")
