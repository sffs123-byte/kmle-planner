#!/usr/bin/env python3
"""심음 청진 APTM 랜덤 감별 퀴즈 생성기."""

from __future__ import annotations

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUIZ_DIR = ROOT / "quizzes"
ASSET_DIR = QUIZ_DIR / "assets" / "heart_sound_random"
OUT = QUIZ_DIR / "심음청진_APTM_랜덤퀴즈.html"
META = ASSET_DIR / "meta.json"
POSITIONS = ["A", "P", "T", "M"]
POS_NAMES = {"A": "대동맥", "P": "폐동맥", "T": "삼첨판", "M": "승모판"}
NORMAL_AUDIO_KEY = "S2 split(-)"

NORMAL_DISEASE = {
    "id": "정상",
    "name": "정상",
    "full": "Normal heart sound",
    "primary": "APTM",
    "audioKey": NORMAL_AUDIO_KEY,
    "pattern": {
        "A": "정상 S1/S2, murmur 없음",
        "P": "정상 S1/S2, fixed splitting 없음",
        "T": "정상 S1/S2, murmur 없음",
        "M": "정상 S1/S2, murmur 없음",
    },
    "keywords": ["정상 심음", "murmur 없음", "fixed S2 splitting 없음", "APTM 전체 정상"],
    "tip": "APTM 전 위치에서 특별한 murmur 없이 S1/S2만 들리면 정상 심음으로 본다.",
}


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def load_source() -> tuple[list[dict], list[str], dict, dict, str, str]:
    meta = json.loads(META.read_text(encoding="utf-8"))
    diseases = meta["diseases"]
    if not any(d["id"] == NORMAL_DISEASE["id"] for d in diseases):
        diseases = diseases + [NORMAL_DISEASE]
    order_tips = meta["order_tips"]
    timestamps = meta["timestamps"]
    audio = {
        disease["audioKey"] if disease.get("audioKey") else disease["id"]: data_uri(
            ASSET_DIR / ("normal.mp3" if (disease.get("audioKey") or disease["id"]) == NORMAL_AUDIO_KEY else f"{disease['id']}.mp3"),
            "audio/mp3",
        )
        for disease in diseases
    }
    study_img = data_uri(ASSET_DIR / "study_notes.jpg", "image/jpeg")
    source_img = data_uri(ASSET_DIR / "source_table.jpg", "image/jpeg")
    return diseases, order_tips, timestamps, audio, study_img, source_img


def build_html() -> str:
    diseases, order_tips, timestamps, audio, study_img, source_img = load_source()

    css = r'''
:root{--bg:#101827;--panel:#182136;--text:#edf2ff;--muted:#a6adbb;--line:#334155;--pri:#8ab4ff;--green:#4ade80;--red:#fb7185;--orange:#f59e0b;--paper:#fffdf7;--ink:#1f2937}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at top left,#1e3a8a33,transparent 34%),linear-gradient(135deg,#0f172a,#1e1b4b);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh}
.app{display:flex;flex-direction:column;min-height:100vh}
.topbar{background:rgba(15,23,42,.97);border-bottom:1px solid var(--line);padding:14px 20px;display:flex;align-items:center;gap:16px;position:sticky;top:0;z-index:20}
.logo{font-size:17px;font-weight:950;color:var(--pri)}
.modetabs{display:flex;gap:6px;margin-left:auto}
.modetab{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:20px;padding:7px 18px;font-size:13px;font-weight:700;cursor:pointer;transition:all .2s}
.modetab.active{background:var(--pri);color:#0f172a;border-color:var(--pri)}
.circles{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
.circle{width:24px;height:24px;border-radius:50%;border:2px solid var(--orange);background:transparent;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:var(--orange);transition:all .25s;flex-shrink:0}
.circle.correct{background:var(--green);border-color:var(--green);color:#052e16}
.circle.wrong{background:var(--red);border-color:var(--red);color:#4c0519}
.content{flex:1;padding:24px;max-width:1000px;width:100%;margin:0 auto}
.quiz-card,.study-panel{background:rgba(24,33,54,.97);border:1px solid rgba(148,163,184,.2);border-radius:24px;box-shadow:0 20px 80px rgba(0,0,0,.3)}
.quiz-head{padding:18px 22px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px}
.quiz-title{font-size:20px;font-weight:950}.quiz-sub{font-size:13px;color:var(--muted);margin-left:auto}
.quiz-body{padding:20px 22px}
.aptm-row{display:flex;gap:10px;margin-bottom:18px}.pos-btn{flex:1;background:#0f172a;border:2px solid #334155;border-radius:14px;padding:14px 10px;text-align:center;transition:all .25s}.pos-btn.active{border-color:var(--pri);background:rgba(138,180,255,.12)}.pos-btn.played{border-color:#4a5568}.pos-letter{font-size:26px;font-weight:950;color:#475569}.pos-btn.active .pos-letter{color:var(--pri)}.pos-btn.played .pos-letter{color:#94a3b8}.pos-name{font-size:11px;color:var(--muted);margin-top:4px}
.audio-controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.btn{border:0;border-radius:12px;padding:11px 16px;font-weight:850;cursor:pointer;font-size:14px;transition:all .15s}.btn:disabled{opacity:.4;cursor:default}.btn-primary{background:var(--pri);color:#0f172a}.btn-secondary{background:#334155;color:#e2e8f0}.btn-keyword{background:#fbbf2422;color:#fbbf24;border:1px solid #fbbf2444}.btn-new{background:#374151;color:#d1d5db}
.kw-reveal{background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.25);border-radius:14px;padding:14px 16px;margin-bottom:16px;display:none}.kw-reveal.show{display:block}.kw-pos{font-size:12px;color:#fbbf24;font-weight:800;margin-bottom:6px}.kw-text{font-size:15px;line-height:1.6;color:#fde68a}
.choices{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:14px}.choice{border:1px solid #3d4d70;background:#1e2d46;color:#e5e7eb;border-radius:12px;padding:11px 6px;font-weight:850;cursor:pointer;font-size:13px;text-align:center;transition:all .2s}.choice:hover{background:#2d3f5e;border-color:#5a7ab5}.choice.correct{background:#bbf7d0;color:#14532d;border-color:#22c55e}.choice.wrong{background:#fecdd3;color:#881337;border-color:#fb7185}.choice:disabled{cursor:default}
.answer-box{background:#ecfdf5;color:#14532d;border-radius:16px;padding:16px;margin-top:4px;display:none}.answer-box.show{display:block}.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.chip{font-size:12px;border-radius:999px;padding:4px 10px;background:#dbeafe;color:#1e3a8a;font-weight:800}.tip-box{background:#fef3c7;color:#78350f;border-radius:12px;padding:12px;margin-top:10px;line-height:1.6}.next-btn{margin-top:12px;width:100%}
.result-screen{display:none;padding:40px 20px;text-align:center}.result-screen.show{display:block}.result-big{font-size:56px;font-weight:950;margin-bottom:8px}.result-sub{font-size:18px;color:var(--muted);margin-bottom:28px}
.study-wrap{display:grid;grid-template-columns:1fr 1fr;gap:18px}.study-panel{padding:16px}.study-panel h3{margin:0 0 12px;font-size:15px;color:#bfdbfe;font-weight:800}.study-panel img{width:100%;border-radius:12px;display:block}.algo-row{background:#0f172a;border:1px solid #334155;border-radius:10px;padding:10px 14px;margin-bottom:8px;font-size:14px;line-height:1.5;color:#dbeafe}
.disease-tabs{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 14px}.dtab{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:8px;padding:5px 12px;font-size:12px;font-weight:800;cursor:pointer}.dtab.active{background:var(--pri);color:#0f172a;border-color:var(--pri)}
.study-aptm{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.study-slot{background:#0f172a;border:1px solid #334155;border-radius:14px;padding:12px}.study-slot .pos{font-size:24px;font-weight:950;color:var(--pri);margin-bottom:6px}.study-slot .kw{font-size:13px;line-height:1.55;color:#cbd5e1}
.study-summary{font-size:13px;color:#cbd5e1;line-height:1.7;padding:0 2px}
@media(max-width:700px){.choices{grid-template-columns:repeat(2,1fr)}.aptm-row{gap:6px}.study-wrap{grid-template-columns:1fr}.circles{gap:5px}.circle{width:22px;height:22px;font-size:10px}}
'''

    js = f'''
const DISEASES = {json.dumps(diseases, ensure_ascii=False)};
const ORDER_TIPS = {json.dumps(order_tips, ensure_ascii=False)};
const AUDIO = {json.dumps(audio, ensure_ascii=False)};
const TS = {json.dumps(timestamps, ensure_ascii=False)};
const POSITIONS = {json.dumps(POSITIONS, ensure_ascii=False)};
const POS_NAMES = {json.dumps(POS_NAMES, ensure_ascii=False)};
const QUESTION_COUNT = 10;
let mode = 'quiz';
let quizQueue = [];
let quizIdx = 0;
let results = [];
let current = null;
let curPos = 0;
let answered = false;
let kwVisible = false;
let audioLoop = null;
let studyDis = DISEASES[0].id;

function shuffle(arr){{return [...arr].sort(()=>Math.random()-.5);}}
function esc(s){{return String(s??'').replace(/[&<>]/g,m=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[m]));}}
function currentAudioKey(disease){{return disease.audioKey || disease.id;}}
function clearAudioLoop(){{if(audioLoop){{clearInterval(audioLoop); audioLoop = null;}}}}
function stopAudio(){{clearAudioLoop(); const player = document.getElementById('player'); player.pause(); player.currentTime = 0;}}

function setMode(m){{
  mode = m;
  document.getElementById('tab-quiz').className = 'modetab' + (m==='quiz'?' active':'');
  document.getElementById('tab-study').className = 'modetab' + (m==='study'?' active':'');
  document.getElementById('quiz-mode').style.display = m==='quiz'?'':'none';
  document.getElementById('study-mode').style.display = m==='study'?'':'none';
  document.getElementById('circles').style.display = m==='quiz'?'flex':'none';
  if(m==='study'){{ stopAudio(); renderStudy(); }}
  if(m==='quiz' && current) updatePosUI();
}}

function startQuiz(){{
  quizQueue = shuffle(DISEASES).slice(0, QUESTION_COUNT);
  quizIdx = 0;
  results = [];
  renderCircles();
  document.getElementById('result-screen').className = 'result-screen';
  document.getElementById('choices').style.display = '';
  document.getElementById('audio-controls').style.display = '';
  document.getElementById('aptm-row').style.display = '';
  renderQuestion();
}}

function renderCircles(){{
  const el = document.getElementById('circles');
  el.innerHTML = results.map((r,i)=>`<div class="circle ${{r===true?'correct':'wrong'}}">${{i+1}}</div>`).join('') +
    Array.from({{length:QUESTION_COUNT-results.length}},(_,i)=>`<div class="circle">${{results.length+i+1}}</div>`).join('');
}}

function renderQuestion(){{
  if(quizIdx >= QUESTION_COUNT){{ showResult(); return; }}
  current = quizQueue[quizIdx];
  curPos = 0;
  answered = false;
  kwVisible = false;
  document.getElementById('kw-reveal').className = 'kw-reveal';
  document.getElementById('answer-box').className = 'answer-box';
  document.getElementById('q-qnum').textContent = `문제 ${{quizIdx+1}} / ${{QUESTION_COUNT}}`;
  updatePosUI();
  renderChoices();
  playPos();
}}

function updatePosUI(){{
  POSITIONS.forEach((p,i)=>{{
    const el = document.getElementById('pos-'+p);
    const cls = i === curPos ? 'pos-btn active' : i < curPos ? 'pos-btn played' : 'pos-btn';
    el.className = cls;
  }});
  document.getElementById('q-position-label').textContent = `${{POSITIONS[curPos]}} 위치 청진 중`;
  const nextBtn = document.getElementById('btn-next-pos');
  nextBtn.disabled = curPos >= POSITIONS.length - 1 || answered;
  document.getElementById('btn-kw').disabled = answered;
}}

function playPos(){{
  const player = document.getElementById('player');
  clearAudioLoop();
  const key = currentAudioKey(current);
  const src = AUDIO[key];
  const ts = TS[key];
  if(!src || !ts) return;
  const pos = POSITIONS[curPos];
  const range = ts[pos];
  if(!range) return;
  const start = range[0];
  const end = range[1];
  player.src = src;
  player.currentTime = start;
  player.play().catch(()=>{{}});
  if(end !== null){{
    audioLoop = setInterval(()=>{{
      if(player.currentTime >= end){{
        player.currentTime = start;
        player.play().catch(()=>{{}});
      }}
    }}, 180);
  }}
}}

function replayPos(){{ if(!answered) playPos(); }}
function nextPos(){{
  if(curPos < POSITIONS.length - 1 && !answered){{
    curPos++;
    kwVisible = false;
    document.getElementById('kw-reveal').className = 'kw-reveal';
    updatePosUI();
    playPos();
  }}
}}

function toggleKw(){{
  if(answered) return;
  kwVisible = !kwVisible;
  const el = document.getElementById('kw-reveal');
  el.className = 'kw-reveal' + (kwVisible ? ' show' : '');
  if(kwVisible){{
    const pos = POSITIONS[curPos];
    document.getElementById('kw-pos-label').textContent = pos + ' 위치 (' + POS_NAMES[pos] + ')';
    document.getElementById('kw-text').textContent = current.pattern[pos];
  }}
}}

function renderChoices(){{
  const choices = shuffle(DISEASES.map(d=>d.id));
  document.getElementById('choices').innerHTML = choices.map(id=>`<button class="choice" data-id="${{id}}" onclick="guess('${{id}}')">${{esc(id)}}</button>`).join('');
}}

function guess(id){{
  if(answered) return;
  answered = true;
  stopAudio();
  const correct = id === current.id;
  results.push(correct);
  renderCircles();
  document.querySelectorAll('.choice').forEach(b=>{{
    if(b.dataset.id === current.id) b.classList.add('correct');
    else if(b.dataset.id === id) b.classList.add('wrong');
    b.disabled = true;
  }});
  POSITIONS.forEach((p)=>{{ document.getElementById('pos-'+p).className = 'pos-btn played'; }});
  document.getElementById('btn-next-pos').disabled = true;
  document.getElementById('btn-kw').disabled = true;
  const ab = document.getElementById('answer-box');
  ab.className = 'answer-box show';
  document.getElementById('answer-inner').innerHTML =
    `<b>${{correct?'✅':'❌'}} 정답: ${{esc(current.id)}} · ${{esc(current.full)}}</b>` +
    `<div class="chips">${{current.keywords.map(k=>`<span class="chip">${{esc(k)}}</span>`).join('')}}</div>` +
    `<div class="tip-box">${{esc(current.tip)}}</div>`;
  quizIdx++;
  document.getElementById('next-question-btn').textContent = quizIdx >= QUESTION_COUNT ? '결과 보기 ▶' : '다음 문제 ▶';
}}

function nextQuestion(){{
  if(!answered) return;
  if(quizIdx >= QUESTION_COUNT){{ showResult(); return; }}
  renderQuestion();
}}

function showResult(){{
  stopAudio();
  document.getElementById('choices').style.display = 'none';
  document.getElementById('audio-controls').style.display = 'none';
  document.getElementById('aptm-row').style.display = 'none';
  document.getElementById('answer-box').className = 'answer-box';
  document.getElementById('kw-reveal').className = 'kw-reveal';
  const ok = results.filter(Boolean).length;
  const emoji = ok >= 9 ? '🏆' : ok >= 7 ? '🎉' : ok >= 5 ? '😊' : '💪';
  const sub = ok >= 9 ? '완벽합니다!' : ok >= 7 ? '거의 다 잡혔어요.' : ok >= 5 ? '절반 넘었어요.' : '한 번 더 들어보면 더 빨라집니다.';
  document.getElementById('result-emoji').textContent = emoji;
  document.getElementById('result-score-text').textContent = `${{ok}} / ${{QUESTION_COUNT}}`;
  document.getElementById('result-sub').textContent = sub;
  document.getElementById('result-circles').innerHTML = results.map((r,i)=>`<div class="circle ${{r?'correct':'wrong'}}">${{i+1}}</div>`).join('');
  document.getElementById('result-screen').className = 'result-screen show';
  document.getElementById('q-position-label').textContent = '';
  document.getElementById('q-qnum').textContent = '결과';
}}

function renderStudy(){{
  document.getElementById('algo-list').innerHTML = ORDER_TIPS.map(t=>`<div class="algo-row">${{esc(t)}}</div>`).join('');
  document.getElementById('dtabs').innerHTML = DISEASES.map(d=>`<button class="dtab${{d.id===studyDis?' active':''}}" onclick="selectStudy('${{d.id}}')">${{esc(d.id)}}</button>`).join('');
  const disease = DISEASES.find(d=>d.id===studyDis) || DISEASES[0];
  document.getElementById('study-summary').innerHTML = `<b>${{esc(disease.id)}}</b> · ${{esc(disease.full)}}<br>${{esc(disease.tip)}}`;
  document.getElementById('study-aptm').innerHTML = POSITIONS.map(p=>`<div class="study-slot"><div class="pos">${{p}}</div><div class="kw">${{esc(disease.pattern[p])}}</div></div>`).join('');
}}
function selectStudy(id){{ studyDis = id; renderStudy(); }}

window.addEventListener('keydown', e=>{{
  if(mode !== 'quiz') return;
  if(e.key === ' '){{ e.preventDefault(); nextPos(); }}
  if(e.key.toLowerCase() === 'k'){{ toggleKw(); }}
  if(e.key.toLowerCase() === 'r'){{ replayPos(); }}
}});

renderStudy();
startQuiz();
'''

    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>심음청진 APTM 랜덤퀴즈</title>
  <style>{css}</style>
</head>
<body>
<div class="app">
  <div class="topbar">
    <div class="logo">심음청진 APTM</div>
    <div class="modetabs">
      <button class="modetab active" id="tab-quiz" onclick="setMode('quiz')">퀴즈 모드</button>
      <button class="modetab" id="tab-study" onclick="setMode('study')">공부 모드</button>
    </div>
    <div class="circles" id="circles"></div>
  </div>

  <div class="content">
    <div id="quiz-mode">
      <div class="quiz-card">
        <div class="quiz-head">
          <div class="quiz-title" id="q-qnum">문제 1 / 10</div>
          <div class="quiz-sub" id="q-position-label">A 위치 청진 중</div>
        </div>
        <div class="quiz-body">
          <div class="aptm-row" id="aptm-row">
            <div class="pos-btn active" id="pos-A"><div class="pos-letter">A</div><div class="pos-name">대동맥</div></div>
            <div class="pos-btn" id="pos-P"><div class="pos-letter">P</div><div class="pos-name">폐동맥</div></div>
            <div class="pos-btn" id="pos-T"><div class="pos-letter">T</div><div class="pos-name">삼첨판</div></div>
            <div class="pos-btn" id="pos-M"><div class="pos-letter">M</div><div class="pos-name">승모판</div></div>
          </div>
          <div class="audio-controls" id="audio-controls">
            <button class="btn btn-primary" onclick="replayPos()">🔊 다시 듣기</button>
            <button class="btn btn-secondary" id="btn-next-pos" onclick="nextPos()">▶ 다음 소리 듣기</button>
            <button class="btn btn-keyword" id="btn-kw" onclick="toggleKw()">해당 키워드 보기</button>
          </div>
          <div class="kw-reveal" id="kw-reveal">
            <div class="kw-pos" id="kw-pos-label"></div>
            <div class="kw-text" id="kw-text"></div>
          </div>
          <div style="font-size:13px;color:var(--muted);margin-bottom:12px">정답을 선택하세요</div>
          <div class="choices" id="choices"></div>
          <div class="answer-box" id="answer-box">
            <div id="answer-inner"></div>
            <button class="btn btn-primary next-btn" id="next-question-btn" onclick="nextQuestion()">다음 문제 ▶</button>
          </div>
          <div class="result-screen" id="result-screen">
            <div class="result-big" id="result-emoji"></div>
            <div style="font-size:36px;font-weight:950;margin-bottom:8px" id="result-score-text"></div>
            <div class="result-sub" id="result-sub"></div>
            <div class="circles" style="justify-content:center;gap:10px;margin-bottom:24px" id="result-circles"></div>
            <button class="btn btn-primary" style="padding:14px 32px;font-size:16px" onclick="startQuiz()">다시 시작</button>
          </div>
        </div>
      </div>
      <audio id="player" preload="auto"></audio>
    </div>

    <div id="study-mode" style="display:none">
      <div class="study-wrap">
        <div class="study-panel">
          <h3>🧭 이미지 속 감별 알고리즘</h3>
          <img src="{study_img}" alt="감별 알고리즘">
          <div style="height:12px"></div>
          <div id="algo-list"></div>
        </div>
        <div class="study-panel">
          <h3>📋 원문 표 이미지</h3>
          <img src="{source_img}" alt="원문 정리표">
        </div>
      </div>
      <div class="study-panel" style="margin-top:18px;padding:16px">
        <h3>🩺 질환별 APTM 청진 키워드</h3>
        <div class="disease-tabs" id="dtabs"></div>
        <div class="study-summary" id="study-summary"></div>
        <div class="study-aptm" id="study-aptm"></div>
      </div>
    </div>
  </div>
</div>
<script>{js}</script>
</body>
</html>
'''


if __name__ == "__main__":
    OUT.write_text(build_html(), encoding="utf-8")
    print(f"✅ 생성 완료: {OUT} ({OUT.stat().st_size/1024/1024:.1f} MB)")
