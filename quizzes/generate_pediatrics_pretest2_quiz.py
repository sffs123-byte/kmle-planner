#!/usr/bin/env python3
"""Generate 소아청소년과 2주차 Pretest Anki-style SRS quiz.

v3 max policy:
- Do not collapse source variants just because they share the same answer axis.
- Preserve current 79 + 2023 PDF 45 source variants + 총괄/의국회의 extra candidates.
- Mark uncertain/incomplete/image-dependent recall explicitly.
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
TITLE = "소아청소년과 2주차 Pretest SRS v3 MAX"
STORAGE_PREFIX = "peds_pretest2_20260517_v3_max_126"
LOCK_LINE = "최대수집 126문항 · 2026/2025 + 2023 PDF 45 variants · 불확실 문항도 버리지 않고 원문확인 표시"

ORIGIN_LABELS = {
    "actual_recall": "✅ 실제 복기",
    "uncertain_recall": "⚠️ 불완전 복기",
    "actual_recall_source_variant": "🧩 2023 원문 variant",
    "source_drill": "🧠 보강 개념",
    "conference_candidate": "🏥 의국회의 후보",
}

PRIORITY_STYLE = {
    "P4 최신2026": "background:#dc2626;color:#fff;border:1px solid #fecaca;",
    "P3 누적복기": "background:#1d4ed8;color:#fff;border:1px solid #bfdbfe;",
    "P3 2023PDF source-variant": "background:#7c2d12;color:#fff7ed;border:1px solid #fed7aa;",
    "P2 covered-variant": "background:#78350f;color:#ffedd5;border:1px solid #fdba74;",
    "P2 near-variant": "background:#854d0e;color:#fef9c3;border:1px solid #fde68a;",
    "P2 보강개념": "background:#166534;color:#fff;border:1px solid #bbf7d0;",
    "P2 의국회의 후보": "background:#4c1d95;color:#f5f3ff;border:1px solid #ddd6fe;",
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


def format_tutor_html(text: object) -> str:
    """Render enhanced tutor explanations with safe lightweight markdown."""
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    blocks = []
    for block in raw.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        first = lines[0].strip()
        if re.match(r"^[🧭🔎👣🧠📊✅🎯]", first):
            title = e(first)
            body = "\n".join(lines[1:]).strip()
            body_html = format_tutor_inline(body) if body else ""
            blocks.append(f"<section class='tutor-section'><h4>{title}</h4>{body_html}</section>")
        else:
            blocks.append(format_tutor_inline(block))
    return "".join(blocks)


def format_tutor_inline(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    safe = e(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    lines = safe.split("\n")
    if len(lines) >= 2 and sum(1 for line in lines if line.lstrip().startswith(("- ", "• "))) >= 2:
        items=[]
        for line in lines:
            stripped=line.strip()
            if stripped.startswith(("- ", "• ")):
                items.append(f"<li>{stripped[2:].strip()}</li>")
            else:
                items.append(f"<li><strong>{stripped}</strong></li>")
        return "<ul class='tutor-list'>" + "".join(items) + "</ul>"
    return "<p>" + "<br>".join(lines) + "</p>"


def pill(text: str, style: str = "") -> str:
    base = "display:inline-block;border-radius:999px;padding:2px 8px;margin:2px 4px 2px 0;font-size:11px;font-weight:900;line-height:1.35;"
    return f'<span style="{base}{style}">{e(text)}</span>'




def image_block_html(card: dict, placement: str) -> str:
    """Render question/reference images attached to a card.

    placement='front' shows only image candidates safe for the question side.
    placement='answer' shows both front images and answer/reference-only images.
    """
    imgs = []
    for img in card.get("images", []) or []:
        img_place = img.get("placement", "front")
        if placement == "front" and img_place != "front":
            continue
        if placement == "answer" and img_place not in {"front", "answer"}:
            continue
        src = img.get("src") or img.get("path")
        if not src:
            continue
        caption = img.get("caption") or img.get("note") or "원문 이미지"
        quality = img.get("quality") or img.get("confidence") or ""
        badge = f"<span style='font-size:11px;color:#64748b;margin-left:6px;'>{e(quality)}</span>" if quality else ""
        imgs.append(f"""
<figure class="question-image" style="margin:10px 0 0;padding:10px;border:1px solid #dbeafe;background:#f8fbff;border-radius:12px;">
  <img src="{e(src)}" alt="{e(caption)}" loading="lazy" style="max-width:100%;height:auto;display:block;margin:0 auto;border-radius:8px;box-shadow:0 8px 24px rgba(15,23,42,.12);" />
  <figcaption style="margin-top:6px;font-size:12px;line-height:1.45;color:#334155;font-weight:800;">{e(caption)}{badge}</figcaption>
</figure>
""".strip())
    if not imgs:
        return ""
    title = "원문 이미지" if placement == "front" else "원문/참고 이미지"
    return f"<div class='image-block image-block-{placement}' style='margin-top:10px;'><div style='font-size:12px;font-weight:950;color:#1d4ed8;margin:4px 0 6px;'>{title}</div>" + "".join(imgs) + "</div>"


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
  {image_block_html(card, "answer")}
  <div style="border-left:4px solid #16a34a;background:#f0fdf4;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#15803d;margin-bottom:6px;letter-spacing:.04em;">답</div>
    <div style="font-size:20px;line-height:1.55;color:#052e16;"><strong>{e(card.get('answer', ''))}</strong></div>
  </div>
  <div style="border-left:4px solid #f59e0b;background:#fffbeb;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#b45309;margin-bottom:6px;letter-spacing:.04em;">기존 3초 lock / 원문 해설</div>
    <div style="font-size:15px;line-height:1.75;color:#451a03;">{format_problem_html(card.get('explanation', ''))}</div>
  </div>
  <div class="tutor-explain" style="border-left:4px solid #7c3aed;background:#faf5ff;padding:14px 16px;border-radius:12px;">
    <div style="font-size:12px;font-weight:950;color:#6d28d9;margin-bottom:8px;letter-spacing:.04em;">튜터식 상세 해설</div>
    <div style="font-size:15px;line-height:1.78;color:#2e1065;">{format_tutor_html(card.get('enhanced_explanation') or card.get('explanation', ''))}</div>
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
  {image_block_html(card, "answer")}
  <h4>답</h4>
  <p><strong>{e(card.get('answer', ''))}</strong></p>
  <h4>기존 해설</h4>
  <p>{format_problem_html(card.get('explanation', ''))}</p>
  <h4>튜터식 상세 해설</h4>
  <div class="tutor-explain">{format_tutor_html(card.get('enhanced_explanation') or card.get('explanation', ''))}</div>
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
  {image_block_html(card, "front")}
  <div style="display:flex;gap:5px;flex-wrap:wrap;align-items:center;">{card_pills(card)}</div>
</div>
""".strip()


def sort_key(card: dict) -> tuple:
    priority_order = {
        "P4 최신2026": 0,
        "P3 누적복기": 1,
        "P3 2023PDF source-variant": 2,
        "P2 covered-variant": 3,
        "P2 near-variant": 4,
        "P2 보강개념": 5,
        "P2 의국회의 후보": 6,
    }
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
        if c.get("enhanced_explanation"):
            c["enhanced_explanation"] = str(c.get("enhanced_explanation", "")).strip()
        c["tags"] = list(dict.fromkeys(c.get("tags", [])))
        c["uncertain"] = bool(c.get("uncertain") or c.get("origin") == "uncertain_recall" or "원문 확인 필요" in c["answer"])
        if c["uncertain"] and c.get("origin") == "actual_recall":
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
body.peds-pretest2-bg .tutor-section {{ margin: 12px 0; padding: 10px 12px; background: rgba(255,255,255,.62); border: 1px solid rgba(124,58,237,.14); border-radius: 10px; }}
body.peds-pretest2-bg .tutor-section h4 {{ margin: 0 0 7px; font-size: 15px; color: #581c87; }}
body.peds-pretest2-bg .tutor-section p {{ margin: 0; }}
body.peds-pretest2-bg .tutor-list {{ margin: 0; padding-left: 1.2em; }}
body.peds-pretest2-bg .tutor-list li {{ margin: 4px 0; }}

body.peds-pretest2-bg .image-block-front .question-image {{ background: rgba(15,23,42,.72) !important; border-color: rgba(147,197,253,.36) !important; }}
body.peds-pretest2-bg .image-block-front figcaption {{ color:#dbeafe !important; }}

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
        subtitle="최대수집 126문항 · 현재 79 + 2023 PDF 원문 variant 45 + 총괄 후보 2",
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
