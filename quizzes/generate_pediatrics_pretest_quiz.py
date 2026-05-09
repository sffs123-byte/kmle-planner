#!/usr/bin/env python3
"""Generate 소아청소년과 1주차 Pretest Anki-style SRS quiz.

v2 policy:
- 실제 복기 문항은 조별/시기별 1차 pretest 누적 복기를 모두 별도 카드로 넣는다.
- 제작 응용 문항은 자비스 교수님 Answer Bank/구두퀴즈 기반 drill로 따로 붙인다.
- 모든 카드는 `실제 복기` 또는 `제작 응용` origin badge를 표시한다.

Source of truth:
- Actual recall data: quizzes/data/pediatrics_pretest1_actual_cards.json
- Generated drill source: Obsidian 000_소아과 실습 강의/03_구두퀴즈/01_1주차_Pretest_구두퀴즈_50문항.md
- Answer Bank: Obsidian 000_소아과 실습 강의/02_암기표/01_1주차_Pretest_Answer_Bank.md
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

OBSIDIAN = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/의학과공부/000_소아과 실습 강의"
ORAL_MD = OBSIDIAN / "03_구두퀴즈/01_1주차_Pretest_구두퀴즈_50문항.md"
ANSWER_MD = OBSIDIAN / "02_암기표/01_1주차_Pretest_Answer_Bank.md"

ACTUAL_DATA = DATA_DIR / "pediatrics_pretest1_actual_cards.json"
COMBINED_DATA = DATA_DIR / "pediatrics_pretest1_cards.json"
OUT = QUIZ_DIR / "소아청소년과_1주차_pretest_quiz.html"
TITLE = "소아청소년과 1주차 Pretest SRS"
STORAGE_PREFIX = "peds_pretest1_20260510"

ORIGIN_LABELS = {
    "actual_recall": "✅ 실제 복기",
    "actual_incomplete": "⚠️ 실제 복기 · 답 미복기",
    "generated_drill": "🛠️ 제작 응용 · 기출 기반 drill",
}

TIER_LABELS = {
    "P4": "P4 · 최신 2026 exact",
    "P3": "P3 · 실제 누적 복기",
    "P2": "P2 · 제작 응용 drill",
}

TYPE_LABELS = {
    "actual_pretest": "🧾 Actual",
    "generated_trigger": "🧠 Drill",
}

DEDUP_LABELS = {
    "duplicate": "🔁 exact repeat",
    "near_duplicate": "🔁 near-repeat",
    "answer_conflict": "🚨 답 충돌",
    "contrast_pair": "⚖️ IVIG 갈림길",
    "fragment_group": "🧩 조각 대표",
    "fragment_of": "🧩 파싱 조각",
    "same_topic_sibling": "↔️ sibling",
    "variant_keep": "🧬 variant",
    "needs_source": "🔎 원문 확인",
    "keep_separate": "분리 보존",
    "keep_unique": "단독 actual",
}

DEDUP_FRONT_KEYS = {
    "duplicate",
    "near_duplicate",
    "answer_conflict",
    "contrast_pair",
    "fragment_group",
    "fragment_of",
    "same_topic_sibling",
    "variant_keep",
    "needs_source",
}

DEDUP_PILL_STYLE = {
    "duplicate": "background:#1e3a8a;color:#dbeafe;border:1px solid #60a5fa;",
    "near_duplicate": "background:#1e3a8a;color:#dbeafe;border:1px solid #60a5fa;",
    "answer_conflict": "background:#7f1d1d;color:#fee2e2;border:1px solid #fca5a5;",
    "contrast_pair": "background:#581c87;color:#f3e8ff;border:1px solid #d8b4fe;",
    "fragment_group": "background:#78350f;color:#ffedd5;border:1px solid #fdba74;",
    "fragment_of": "background:#78350f;color:#ffedd5;border:1px solid #fdba74;",
    "same_topic_sibling": "background:#374151;color:#f3f4f6;border:1px solid #9ca3af;",
    "variant_keep": "background:#312e81;color:#e0e7ff;border:1px solid #a5b4fc;",
    "needs_source": "background:#854d0e;color:#fef3c7;border:1px solid #fbbf24;",
    "keep_separate": "background:#334155;color:#e2e8f0;border:1px solid #94a3b8;",
    "keep_unique": "background:#14532d;color:#dcfce7;border:1px solid #86efac;",
}

EXACT_EXPRESSIONS = {
    1: "철 결핍",
    2: "수두백신을 접종한다",
    3: "0.9% NS 20 mL/kg bolus",
    4: "기관삽관",
    5: "저칼슘혈증",
    6: "대인관계 형성장애, 제한되고 반복적인 행동/관심",
    7: "IgM",
    8: "당원병",
    9: "IVIG / 정맥 면역글로불린",
    10: "ampicillin + gentamicin",
}


def e(s: object) -> str:
    return html.escape(str(s), quote=False)


def dedup_key(card: dict) -> str:
    return str(card.get("dedup_decision", "")).split(":", 1)[0]


def dedup_label(card: dict) -> str:
    key = dedup_key(card)
    return DEDUP_LABELS.get(key, key)


def dedup_pills_html(card: dict, *, front: bool = False) -> str:
    key = dedup_key(card)
    if not key:
        return ""
    if front and key not in DEDUP_FRONT_KEYS:
        return ""
    style = DEDUP_PILL_STYLE.get(key, "background:#334155;color:#e2e8f0;border:1px solid #94a3b8;")
    base = "display:inline-block;border-radius:999px;padding:2px 7px;margin:1px 3px 1px 0;font-size:11px;font-weight:800;line-height:1.35;"
    title = card.get("dedup_why", "")
    return f'<span class="dedup-pill" title="{e(title)}" style="{base}{style}">{e(dedup_label(card))}</span>'


def is_missing_answer(answer: str) -> bool:
    incomplete_markers = [
        "미복기",
        "원문 확인 필요",
        "원문 선지 확인 필요",
        "원문 통합 확인 필요",
        "복기 불완전",
        "파싱 조각",
    ]
    return any(marker in answer for marker in incomplete_markers)


def parse_generated_drill() -> list[dict]:
    text = ORAL_MD.read_text(encoding="utf-8")
    cards: list[dict] = []
    current_section = ""
    current_subsection = ""
    current_q: tuple[int, str] | None = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            current_subsection = ""
            continue
        if line.startswith("### "):
            current_subsection = line.removeprefix("### ").strip()
            continue
        m = re.match(r"^(\d+)\.\s+(.+)$", line.strip())
        if m:
            current_q = (int(m.group(1)), m.group(2).strip())
            continue
        if current_q and line.strip().startswith("- 답:"):
            num, question = current_q
            answer = line.strip().removeprefix("- 답:").strip()
            cards.append({
                "id": f"drill1_{num:03d}",
                "source": "자비스 교수님 구두퀴즈 50문항",
                "mode": "구두퀴즈",
                "num_in_source": num,
                "question": question,
                "answer": answer,
                "exact_expression": EXACT_EXPRESSIONS.get(num, ""),
                "section": current_section,
                "subsection": current_subsection,
                "origin": "generated_drill",
                "priority_tier": "P2",
                "type": "generated_trigger",
            })
            current_q = None
    if len(cards) != 50:
        raise RuntimeError(f"Expected 50 generated drill cards, got {len(cards)}")
    return cards


def load_actual_cards() -> list[dict]:
    cards = json.loads(ACTUAL_DATA.read_text(encoding="utf-8"))
    for c in cards:
        c.setdefault("section", "실제 1차 Pretest 누적 복기")
        c.setdefault("subsection", c.get("source", ""))
        c.setdefault("exact_expression", "")
        c.setdefault("priority_tier", "P3")
        c.setdefault("type", "actual_pretest")
        if c.get("origin") == "actual_incomplete" or is_missing_answer(c.get("answer", "")):
            c["origin"] = "actual_incomplete"
        else:
            c["origin"] = "actual_recall"
    return cards


def tags_html(tags: list[str]) -> str:
    return "".join(f'<span class="mini-tag">#{e(t)}</span>' for t in tags)


def build_answer_html(card: dict) -> str:
    origin = card["origin"]
    tier = card.get("priority_tier", "")
    typ = card.get("type", "")
    answer = card.get("answer", "")
    warning = ""
    if origin == "actual_incomplete":
        warning = '<p style="color:#b45309;font-weight:800;">이 카드는 실제 복기 문항이지만 원문에 명시 답이 부족합니다. 원본 확인 또는 강의/Answer Bank로 보강이 필요합니다.</p>'
    exact = card.get("exact_expression") or ""
    dedup = dedup_pills_html(card)
    audit_block = ""
    if card.get("group_id"):
        audit_block = f"""
  <h4>Strict dedup audit v2</h4>
  <table>
    <tr><th>Episode</th><td>{e(card.get('episode', '-'))}</td></tr>
    <tr><th>Content axis</th><td>{e(card.get('content_axis', '-'))}</td></tr>
    <tr><th>Normalized answer</th><td>{e(card.get('answer_key_normalized', '-'))}</td></tr>
    <tr><th>Group</th><td><code>{e(card.get('group_id', '-'))}</code></td></tr>
    <tr><th>Decision</th><td>{dedup} <code>{e(card.get('dedup_decision', '-'))}</code></td></tr>
    <tr><th>Why</th><td>{e(card.get('dedup_why', '-'))}</td></tr>
  </table>
"""
    return f"""
<section class="kmle-answer">
  <div class="answer-meta">
    <span class="pill">{e(ORIGIN_LABELS.get(origin, origin))}</span>
    <span class="pill tier-{e(tier)}">{e(TIER_LABELS.get(tier, tier))}</span>
    <span class="pill">{e(TYPE_LABELS.get(typ, typ))}</span>
    {dedup}
  </div>
  <h3>정답</h3>
  <p class="answer-main"><strong>{e(answer)}</strong></p>
  {warning}
  {f'<h4>정확 표현</h4><p><strong>{e(exact)}</strong></p>' if exact else ''}
  <h4>문항 원문/트리거</h4>
  <p>{e(card['question'])}</p>
  <h4>출처</h4>
  <p><code>{e(card.get('source', '-'))}</code></p>
  {audit_block}
  <div class="tag-row">{tags_html(card.get('tags', []))}</div>
</section>
""".strip()


def build_guide_html(card: dict) -> str:
    origin = card["origin"]
    dedup_rows = ""
    if card.get("group_id"):
        dedup_rows = f"""
    <tr><th>Episode</th><td>{e(card.get('episode', '-'))}</td></tr>
    <tr><th>Content axis</th><td>{e(card.get('content_axis', '-'))}</td></tr>
    <tr><th>Answer normalized</th><td>{e(card.get('answer_key_normalized', '-'))}</td></tr>
    <tr><th>Dedup group</th><td><code>{e(card.get('group_id', '-'))}</code></td></tr>
    <tr><th>Dedup decision</th><td>{dedup_pills_html(card)} <code>{e(card.get('dedup_decision', '-'))}</code></td></tr>
    <tr><th>Why</th><td>{e(card.get('dedup_why', '-'))}</td></tr>
"""
    return f"""
<section class="kmle-guide">
  <h4>📌 문항 성격</h4>
  <table>
    <tr><th>Origin</th><td>{e(ORIGIN_LABELS.get(origin, origin))}</td></tr>
    <tr><th>Source</th><td>{e(card.get('source', '-'))}</td></tr>
    <tr><th>Mode</th><td>{e(card.get('mode', '-'))}</td></tr>
    <tr><th>Source No.</th><td>{e(card.get('num_in_source', '-'))}</td></tr>
    <tr><th>Section</th><td>{e(card.get('section', '-'))}</td></tr>
    <tr><th>Subsection</th><td>{e(card.get('subsection', '-') or '-')}</td></tr>
    {dedup_rows}
  </table>
  <p class="guide-note">실제 복기 문항과 제작 응용 drill을 섞되, origin badge로 분리했습니다. actual 문항은 v2 strict audit 기준으로 duplicate/variant/conflict/fragment를 표시하며, 문항 삭제 없이 원문 evidence를 보존합니다.</p>
</section>
""".strip()


def card_question_html(card: dict) -> str:
    origin = card["origin"]
    tier = card.get("priority_tier", "")
    typ = card.get("type", "")
    return (
        f'<span class="q-tier">{e(tier)}</span> '
        f'<span class="q-type">{e(ORIGIN_LABELS.get(origin, origin))}</span> '
        f'<span class="q-type">{e(TYPE_LABELS.get(typ, typ))}</span> '
        f'{dedup_pills_html(card, front=True)} '
        f'{e(card["question"])}'
    )


def build_cards(raw_cards: list[dict]) -> list[dict]:
    cards = []
    for i, c in enumerate(raw_cards, 1):
        c.setdefault("tags", [])
        dedup_tags = c.get("dedup_badges", []) if c.get("type") == "actual_pretest" else []
        group_tag = [c["group_id"]] if c.get("group_id") else []
        c["tags"] = list(dict.fromkeys(c.get("tags", []) + ["소아과", "pretest", "1주차", c["origin"]] + dedup_tags + group_tag))
        cards.append({
            "id": c["id"],
            "num": i,
            "q": card_question_html(c),
            "a": build_answer_html(c),
            "g": build_guide_html(c),
        })
    return cards


def main() -> None:
    actual = load_actual_cards()
    generated = parse_generated_drill()
    combined = actual + generated
    COMBINED_DATA.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = build_cards(combined)
    builder = QuizBuilder(cards=cards, title=TITLE, storage_prefix=STORAGE_PREFIX)
    builder.write(str(OUT))
    print(f"actual_cards: {len(actual)}")
    print(f"generated_drill_cards: {len(generated)}")
    print(f"total_cards: {len(cards)}")
    print(f"combined_data: {COMBINED_DATA}")
    print(f"out: {OUT}")
    print(f"storage_prefix: {STORAGE_PREFIX}_")


if __name__ == "__main__":
    main()
