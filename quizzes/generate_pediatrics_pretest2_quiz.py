#!/usr/bin/env python3
"""Generate 소아청소년과 2주차 Pretest Anki-style SRS quiz.

v2 policy:
- Use the 79-card source-faithful extraction as source of truth.
- Preserve repeated/variant actual recall cards instead of over-compressing.
- Mark uncertain/incomplete recall explicitly.
- Disable self-answer box, matching the 1주차 pretest UX.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from anki_quiz_builder import QuizBuilder

ROOT = Path(__file__).resolve().parent.parent
QUIZ_DIR = ROOT / "quizzes"
DATA_DIR = QUIZ_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUT = QUIZ_DIR / "소아청소년과_2주차_pretest_quiz.html"
DATA = DATA_DIR / "pediatrics_pretest2_cards.json"
TITLE = "소아청소년과 2주차 Pretest SRS v2"
STORAGE_PREFIX = "peds_pretest2_20260517_v2_79"
LOCK_LINE = "김밥 3시간 포도알균 · target sign 공기정복 · wheezing 세기관지염 · Tet spell knee-chest · 의국회의 손위생"

ORIGIN_LABELS = {
    "actual_recall": "✅ 실제 복기",
    "uncertain_recall": "⚠️ 불완전 복기",
    "source_drill": "🧠 보강 개념",
}

PRIORITY_STYLE = {
    "P4 최신2026": "background:#dc2626;color:#fff;border:1px solid #fecaca;",
    "P3 누적복기": "background:#1d4ed8;color:#fff;border:1px solid #bfdbfe;",
    "P2 보강개념": "background:#166534;color:#fff;border:1px solid #bbf7d0;",
}


def e(value: object) -> str:
    return html.escape(str(value), quote=False)


def normalize_space(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def format_problem_html(text: object) -> str:
    out = e(normalize_space(text))
    out = re.sub(r"\s+(?=[①②③④⑤])", "<br>", out)
    out = re.sub(r"\s+(?=[1-5][\)\.]\s*)", "<br>", out)
    out = re.sub(r"\s+(Q[12]\.)", r"<br>\1", out)
    out = out.replace(" 보기:", "<br>보기:")
    out = out.replace(" 선지:", "<br>선지:")
    return out


def pill(text: str, style: str = "") -> str:
    base = "display:inline-block;border-radius:999px;padding:2px 8px;margin:2px 4px 2px 0;font-size:11px;font-weight:900;line-height:1.35;"
    return f'<span style="{base}{style}">{e(text)}</span>'


def card_pills(card: dict) -> str:
    priority = card.get("priority", "")
    origin = card.get("origin", "")
    style = PRIORITY_STYLE.get(priority, "background:#334155;color:#e2e8f0;border:1px solid #94a3b8;")
    parts = [pill(priority or "P?", style), pill(ORIGIN_LABELS.get(origin, origin or "source"), "background:#111827;color:#e5e7eb;border:1px solid #64748b;")]
    if card.get("uncertain"):
        parts.append(pill("원문 확인", "background:#7f1d1d;color:#fee2e2;border:1px solid #fca5a5;"))
    if "repeat" in card.get("tags", []):
        parts.append(pill("반복", "background:#581c87;color:#f3e8ff;border:1px solid #d8b4fe;"))
    if "variant" in card.get("tags", []):
        parts.append(pill("변형", "background:#78350f;color:#ffedd5;border:1px solid #fdba74;"))
    return "".join(parts)


def answer_html(card: dict) -> str:
    tags = "".join(f'<span class="mini-tag">#{e(t)}</span>' for t in card.get("tags", []))
    return f"""
<section class="kmle-answer" style="display:flex;flex-direction:column;gap:12px;">
  <div style="border-left:4px solid #2563eb;background:#eff6ff;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#1d4ed8;margin-bottom:6px;letter-spacing:.04em;">문제</div>
    <div style="font-size:15px;line-height:1.72;color:#111827;">{format_problem_html(card.get('question', ''))}</div>
  </div>
  <div style="border-left:4px solid #16a34a;background:#f0fdf4;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#15803d;margin-bottom:6px;letter-spacing:.04em;">답</div>
    <div style="font-size:20px;line-height:1.55;color:#052e16;"><strong>{e(card.get('answer', ''))}</strong></div>
  </div>
  <div style="border-left:4px solid #f59e0b;background:#fffbeb;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#b45309;margin-bottom:6px;letter-spacing:.04em;">3초 lock / 해설</div>
    <div style="font-size:15px;line-height:1.75;color:#451a03;">{format_problem_html(card.get('explanation', ''))}</div>
  </div>
  <details style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px 12px;color:#334155;">
    <summary style="cursor:pointer;font-weight:800;">출처 / 태그</summary>
    <div style="margin-top:10px;">{card_pills(card)}</div>
    <h4>출처</h4>
    <p><code>{e(card.get('source', '-'))}</code></p>
    <div class="tag-row">{tags}</div>
  </details>
</section>
""".strip()


def guide_html(card: dict) -> str:
    return f"""
<section class="kmle-guide" style="line-height:1.7;">
  <h4>문제</h4>
  <p>{format_problem_html(card.get('question', ''))}</p>
  <h4>답</h4>
  <p><strong>{e(card.get('answer', ''))}</strong></p>
  <h4>해설</h4>
  <p>{format_problem_html(card.get('explanation', ''))}</p>
  <h4>출처</h4>
  <p><code>{e(card.get('source', '-'))}</code></p>
  <p>{card_pills(card)}</p>
</section>
""".strip()


def question_html(card: dict) -> str:
    return f"""
<div style="display:flex;flex-direction:column;gap:8px;width:100%;">
  <div style="font-size:11px;font-weight:900;color:#93c5fd;letter-spacing:.06em;">문제</div>
  <div style="font-size:14px;line-height:1.62;color:#e5e7eb;">{format_problem_html(card.get('question', ''))}</div>
  <div style="display:flex;gap:5px;flex-wrap:wrap;align-items:center;">{card_pills(card)}</div>
</div>
""".strip()


def sort_key(card: dict) -> tuple:
    priority_order = {"P4 최신2026": 0, "P3 누적복기": 1, "P2 보강개념": 2}
    return (priority_order.get(card.get("priority"), 9), int(card.get("source_rank", 999)), card.get("id", ""))


def load_cards() -> list[dict]:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    cards = []
    for i, src in enumerate(raw, 1):
        c = dict(src)
        c.setdefault("id", f"pretest2_{i:03d}")
        c.setdefault("source_rank", i)
        c.setdefault("origin", "actual_recall")
        c.setdefault("priority", "P3 누적복기")
        c["question"] = normalize_space(c.get("question") or c.get("q") or "")
        c["answer"] = normalize_space(c.get("answer") or c.get("a") or "원문 확인 필요")
        c["explanation"] = normalize_space(c.get("explanation") or c.get("lock") or c.get("note") or "")
        c["tags"] = list(dict.fromkeys(c.get("tags", [])))
        c["uncertain"] = bool(c.get("uncertain") or c.get("origin") == "uncertain_recall" or "원문 확인 필요" in c["answer"])
        if c["uncertain"]:
            c["origin"] = "uncertain_recall"
        cards.append(c)
    return sorted(cards, key=sort_key)


def add_background() -> None:
    text = OUT.read_text(encoding="utf-8")
    lock = e(LOCK_LINE)
    css = f"""

/* Pediatric 2-week pretest v2 cue wall */
body.peds-pretest2-bg {{
  background: radial-gradient(circle at 12% 8%, rgba(14,165,233,.24), transparent 32%),
              radial-gradient(circle at 86% 14%, rgba(249,115,22,.18), transparent 30%),
              linear-gradient(135deg, #0f172a 0%, #1e293b 48%, #111827 100%) !important;
}}
body.peds-pretest2-bg::before {{
  content: '{lock}'; position: fixed; left: 0; right: 0; bottom: 0; z-index: 9999;
  padding: 7px 10px; background: rgba(15,23,42,.88); color:#bfdbfe;
  border-top: 1px solid rgba(147,197,253,.35); font-size:12px; font-weight:950;
  letter-spacing:.04em; text-align:center; pointer-events:none;
}}
body.peds-pretest2-bg .main, body.peds-pretest2-bg .quiz-header {{ position: relative; z-index: 1; }}
body.peds-pretest2-bg .card, body.peds-pretest2-bg .quiz-card {{ box-shadow: 0 18px 44px rgba(2,6,23,.24); }}
"""
    text = text.replace("</style>", css + "\n</style>", 1)
    text = text.replace("<body>", '<body class="peds-pretest2-bg">', 1)
    OUT.write_text(text, encoding="utf-8")


def main() -> None:
    records = load_cards()
    DATA.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = [{"id": c["id"], "num": i, "q": question_html(c), "a": answer_html(c), "g": guide_html(c)} for i, c in enumerate(records, 1)]
    builder = QuizBuilder(
        cards=cards,
        title=TITLE,
        subtitle="원문형 79문항 · 최신 2026 exact 20 + 누적 actual/variant 59",
        storage_prefix=STORAGE_PREFIX,
        enable_self_answer=False,
        randomize_review=True,
    )
    builder.write(str(OUT))
    add_background()
    print(f"cards: {len(cards)}")
    print(f"data: {DATA}")
    print(f"out: {OUT}")
    print(f"storage_prefix: {STORAGE_PREFIX}_")


if __name__ == "__main__":
    main()
