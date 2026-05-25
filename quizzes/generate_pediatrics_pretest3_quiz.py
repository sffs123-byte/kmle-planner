#!/usr/bin/env python3
"""Generate 소아청소년과 3주차 Pretest Anki-style SRS quiz.

Scaffold policy (2026-05-19):
- Keep the shell ready before the real 3주차 problem collection arrives.
- Official scope is 16~28장: 혈액-종양, 신요로, 내분비, 신경-근육, 골격,
  알레르기, 결체조직, 피부, 안과, 손상, 통일/기타.
- Preserve source variants; do not collapse different stems just because they share
  the same answer.
- Mark incomplete recalls explicitly instead of deleting them.
- Disable self-answer box, matching the 1주차/2주차 pretest UX.
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

OUT = QUIZ_DIR / "소아청소년과_3주차_pretest_quiz.html"
DATA = DATA_DIR / "pediatrics_pretest3_cards.json"
TITLE = "소아청소년과 3주차 Pretest SRS"
STORAGE_PREFIX = "peds_pretest3_20260525_full_v5_hybrid"
LOCK_LINE = "3주차 Pretest Anki v5 · 309문항 · 기존 튜터식 보강 해설 + Allen PDF 근거 동시 제공 · 불완전 복기는 원문확인 표시"

OFFICIAL_RANGE_LABEL = "공식 3주차 16~28장"
OFFICIAL_UNIT_ORDER = [
    "혈액-종양",
    "신요로",
    "내분비",
    "신경-근육",
    "골격",
    "알레르기",
    "결체조직",
    "피부",
    "안과",
    "손상",
    "통일/기타",
    "범위외/집담회",
]

OFFICIAL_UNIT_CHAPTER = {
    "혈액-종양": "혈액-종양",
    "신요로": "신요로",
    "내분비": "내분비",
    "신경-근육": "신경-근육",
    "골격": "골격",
    "알레르기": "알레르기",
    "결체조직": "결체조직",
    "피부": "피부",
    "안과": "안과",
    "손상": "손상",
    "통일/기타": "통일/기타",
    "범위외/집담회": "범위외/집담회 확인",
}

OFFICIAL_UNIT_STYLE = {
    "혈액-종양": "background:#7f1d1d;color:#fee2e2;border:1px solid #fca5a5;",
    "신요로": "background:#075985;color:#e0f2fe;border:1px solid #7dd3fc;",
    "내분비": "background:#166534;color:#dcfce7;border:1px solid #86efac;",
    "신경-근육": "background:#4c1d95;color:#f5f3ff;border:1px solid #ddd6fe;",
    "골격": "background:#78350f;color:#ffedd5;border:1px solid #fdba74;",
    "알레르기": "background:#9f1239;color:#fff1f2;border:1px solid #fecdd3;",
    "결체조직": "background:#1e3a8a;color:#dbeafe;border:1px solid #93c5fd;",
    "피부": "background:#854d0e;color:#fef3c7;border:1px solid #fcd34d;",
    "안과": "background:#0f766e;color:#ccfbf1;border:1px solid #5eead4;",
    "손상": "background:#991b1b;color:#fee2e2;border:1px solid #fca5a5;",
    "통일/기타": "background:#334155;color:#e2e8f0;border:1px solid #94a3b8;",
    "범위외/집담회": "background:#374151;color:#f9fafb;border:1px solid #d1d5db;",
}

HOME_GROUPS = [
    {
        "key": "all",
        "label": "전체",
        "units": OFFICIAL_UNIT_ORDER,
        "description": "전체 카드를 한 번에 봅니다.",
        "accent": "linear-gradient(135deg, #1d4ed8, #7c3aed)",
    },
    {
        "key": "heme",
        "label": "혈종",
        "units": ["혈액-종양"],
        "description": "빈혈, 혈소판, 백혈병/종양 축.",
        "accent": "linear-gradient(135deg, #991b1b, #dc2626)",
    },
    {
        "key": "renal",
        "label": "신요로",
        "units": ["신요로"],
        "description": "단백뇨, 혈뇨, 신증후군, UTI 축.",
        "accent": "linear-gradient(135deg, #075985, #0284c7)",
    },
    {
        "key": "endo",
        "label": "내분비",
        "units": ["내분비"],
        "description": "갑상선, 당뇨, 성조숙, 부신 축.",
        "accent": "linear-gradient(135deg, #166534, #16a34a)",
    },
    {
        "key": "neuro",
        "label": "신경근육",
        "units": ["신경-근육"],
        "description": "발작, 근육병, 뇌/신경 문제 축.",
        "accent": "linear-gradient(135deg, #5b21b6, #7c3aed)",
    },
    {
        "key": "other",
        "label": "나머지",
        "units": ["골격", "알레르기", "결체조직", "피부", "안과", "손상", "통일/기타", "범위외/집담회"],
        "description": "골격·알레르기·류마·피부·안과·손상·기타 묶음.",
        "accent": "linear-gradient(135deg, #475569, #0f172a)",
    },
]

ORIGIN_LABELS = {
    "actual_recall": "✅ 실제 복기",
    "uncertain_recall": "⚠️ 불완전 복기",
    "actual_recall_source_variant": "🧩 원문 variant",
    "source_drill": "🧠 보강 개념",
    "conference_candidate": "🏥 집담회 후보",
    "hi_bank": "🛡️ HI bank",
    "scaffold": "🧱 scaffold",
}

PRIORITY_STYLE = {
    "P4 최신2026": "background:#dc2626;color:#fff;border:1px solid #fecaca;",
    "P3 누적복기": "background:#1d4ed8;color:#fff;border:1px solid #bfdbfe;",
    "P3 2023PDF source-variant": "background:#7c2d12;color:#fff7ed;border:1px solid #fed7aa;",
    "P2 HI": "background:#581c87;color:#f3e8ff;border:1px solid #d8b4fe;",
    "P2 집담회": "background:#4c1d95;color:#f5f3ff;border:1px solid #ddd6fe;",
    "P1 보강개념": "background:#166534;color:#fff;border:1px solid #bbf7d0;",
    "SCAFFOLD": "background:#0f172a;color:#e2e8f0;border:1px solid #94a3b8;",
}

UNIT_PATTERNS = [
    ("혈액-종양", r"혈액|빈혈|용혈|철결핍|지중해|혈소판|ITP|혈우|백혈병|림프종|종양|암|neuroblastoma|Wilms|leukemia|lymphoma|oncology"),
    ("신요로", r"신장|요로|소변|단백뇨|혈뇨|부종|신증후군|사구체|신염|방광|요도|무뇨|핍뇨|BUN|Cr|creatinine|renal|nephro|UTI|VUR"),
    ("내분비", r"내분비|당뇨|인슐린|저혈당|갑상선|부갑상선|부신|성조숙|사춘기|성장호르몬|비만|대사|DM|DKA|thyroid|adrenal"),
    ("신경-근육", r"신경|근육|경련|발작|열성경련|뇌전증|두통|의식|마비|뇌성마비|근이영양|Duchenne|seizure|epilepsy|neuromuscular"),
    ("골격", r"골격|골절|뼈|관절|고관절|척추|측만|보행|절뚝|SCFE|Legg|Perthes|osteomyelitis|arthritis"),
    ("알레르기", r"알레르|아나필락|두드러기|아토피|비염|식품.*알레르|RAST|IgE|urticaria|anaphylaxis|allergy|atopy"),
    ("결체조직", r"결체|류마|면역질환|JIA|SLE|루푸스|혈관염|Henoch|IgA vasculitis|가와사키|Kawasaki|rheuma|connective"),
    ("피부", r"피부|발진|습진|홍반|수포|농가진|피부염|모반|멜라닌|dermat|rash|eczema"),
    ("안과", r"안과|눈|시력|사시|백내장|녹내장|망막|결막|동공|ophthal|eye|strabismus"),
    ("손상", r"손상|외상|중독|화상|익수|교통사고|아동학대|학대|abuse|trauma|poison|burn|injury"),
]

UNIT_RANK = {unit: i for i, unit in enumerate(OFFICIAL_UNIT_ORDER)}


def e(value: object) -> str:
    return html.escape(str(value or ""), quote=False)


def normalize_multiline(value: object) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_space(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def format_problem_html(text: object) -> str:
    raw = normalize_multiline(text)
    safe = e(raw)
    safe = re.sub(r"\s+(?=[①②③④⑤])", "<br>", safe)
    safe = re.sub(r"\s+(?=[1-5][\)\.]\s*)", "<br>", safe)
    safe = re.sub(r"\s+(Q[0-9]+\.)", r"<br>\1", safe)
    safe = safe.replace(" 보기:", "<br>보기:")
    safe = safe.replace(" 선지:", "<br>선지:")
    return safe.replace("\n", "<br>")


def format_tutor_html(text: object) -> str:
    raw = normalize_multiline(text)
    if not raw:
        return ""
    blocks = []
    for block in raw.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        first = lines[0].strip()
        if re.match(r"^[🧭🔎👣🧠📊✅🎯⚠️]", first):
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
        items = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("- ", "• ")):
                items.append(f"<li>{stripped[2:].strip()}</li>")
            elif stripped:
                items.append(f"<li><strong>{stripped}</strong></li>")
        return "<ul class='tutor-list'>" + "".join(items) + "</ul>"
    if "|" in safe and "\n" in safe:
        return "<pre class='tutor-pre'>" + safe + "</pre>"
    return "<p>" + "<br>".join(lines) + "</p>"


def pill(text: str, style: str = "") -> str:
    base = "display:inline-block;border-radius:999px;padding:2px 8px;margin:2px 4px 2px 0;font-size:11px;font-weight:900;line-height:1.35;"
    return f'<span style="{base}{style}">{e(text)}</span>'


def infer_official_unit(card: dict) -> str:
    explicit = normalize_space(card.get("official_unit"))
    if explicit:
        return explicit if explicit in OFFICIAL_UNIT_CHAPTER else "범위외/집담회"
    haystack = " ".join(
        normalize_space(card.get(k))
        for k in ("section", "question", "answer", "explanation", "enhanced_explanation", "source", "raw_anchor")
    )
    haystack += " " + " ".join(map(str, card.get("tags", []) or []))
    for unit, pattern in UNIT_PATTERNS:
        if re.search(pattern, haystack, flags=re.I):
            return unit
    if re.search(r"집담회|의국회의|컨퍼런스|conference", haystack, flags=re.I):
        return "범위외/집담회"
    return "통일/기타"


def image_block_html(card: dict, placement: str) -> str:
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
    unit = card.get("official_unit", "통일/기타")
    parts = [
        pill(priority or "P?", PRIORITY_STYLE.get(priority, "background:#334155;color:#e2e8f0;border:1px solid #94a3b8;")),
        pill(ORIGIN_LABELS.get(origin, origin or "source"), "background:#111827;color:#e5e7eb;border:1px solid #64748b;"),
        pill(OFFICIAL_UNIT_CHAPTER.get(unit, unit), OFFICIAL_UNIT_STYLE.get(unit, "background:#374151;color:#f9fafb;border:1px solid #d1d5db;")),
    ]
    if card.get("uncertain"):
        parts.append(pill("원문 확인", "background:#7f1d1d;color:#fee2e2;border:1px solid #fca5a5;"))
    if card.get("scaffold"):
        parts.append(pill("문제 원본 대기", "background:#0f172a;color:#e2e8f0;border:1px dashed #cbd5e1;"))
    return "".join(parts)


def question_html(card: dict) -> str:
    return f"""
<div class="peds3-card-head">
  <div>{card_pills(card)}</div>
  <div style="margin-top:6px;color:#64748b;font-size:12px;font-weight:800;">{e(OFFICIAL_RANGE_LABEL)} · {e(card.get('source', 'source pending'))}</div>
</div>
<div class="question-text" style="margin-top:10px;">{format_problem_html(card.get('question'))}</div>
{image_block_html(card, 'front')}
""".strip()


def allen_pdf_section_html(card: dict) -> str:
    allen_explanation = normalize_multiline(card.get("allen_explanation"))
    allen_answer = normalize_multiline(card.get("allen_answer"))
    refs = card.get("allen_refs") or []
    confidence = normalize_space(card.get("allen_confidence") or "")
    notes = normalize_multiline(card.get("allen_notes"))
    needs_original = bool(card.get("allen_needs_original_source"))
    if not (allen_explanation or allen_answer or refs or notes):
        return ""

    chunks: list[str] = ["<section class='answer-section allen-pdf'>"]
    badge = f" <span class='allen-confidence'>{e(confidence)}</span>" if confidence else ""
    chunks.append(f"<h4>Allen PDF 기준 해설{badge}</h4>")
    if allen_answer:
        chunks.append(f"<p><strong>Allen 기준 답:</strong> {e(allen_answer).replace(chr(10), '<br>')}</p>")
    if allen_explanation:
        chunks.append(f"<p>{e(allen_explanation).replace(chr(10), '<br>')}</p>")
    if refs:
        chunks.append("<div class='allen-refs'><strong>Allen 근거</strong><ul>")
        for ref in refs:
            page = ref.get("page_code") or ref.get("page_file") or "Allen"
            topic = ref.get("topic") or ""
            quote = ref.get("quote") or ""
            label = " · ".join(x for x in [str(page), str(topic)] if x)
            chunks.append(f"<li><span>{e(label)}</span>{': ' if quote else ''}{e(str(quote))}</li>")
        chunks.append("</ul></div>")
    if needs_original or notes:
        note_text = notes or "Allen 직접근거가 약하거나 복기 원문 확인이 필요합니다."
        if needs_original:
            note_text = "원문확인 필요 — " + note_text
        chunks.append(f"<p class='allen-note'>{e(note_text).replace(chr(10), '<br>')}</p>")
    chunks.append("</section>")
    return "".join(chunks)


def answer_html(card: dict) -> str:
    explanation = normalize_multiline(card.get("explanation"))
    enhanced = normalize_multiline(card.get("enhanced_explanation"))
    allen_block = allen_pdf_section_html(card)
    parts = [
        f"<div class='answer-final'><h3>정답</h3><p>{e(card.get('answer', '원문 확인 필요'))}</p></div>"
    ]
    if explanation:
        parts.append(f"<section class='answer-section'><h4>기존 방식 보강 해설</h4><p>{e(explanation).replace(chr(10), '<br>')}</p></section>")
    if enhanced:
        parts.append(f"<section class='answer-section enhanced'><h4>튜터식 상세 해설</h4>{format_tutor_html(enhanced)}</section>")
    if allen_block:
        parts.append(allen_block)
    parts.append(image_block_html(card, "answer"))
    if card.get("uncertain"):
        parts.append("<section class='answer-section warning'><h4>원문 확인 필요</h4><p>이 문항은 복기가 불완전하거나 이미지/선지 확인이 필요합니다. 원본이 들어오면 stem과 정답을 source-faithful하게 교체합니다.</p></section>")
    return "".join(parts)


def guide_html(card: dict) -> str:
    tags = ", ".join(map(str, card.get("tags", []) or [])) or "-"
    raw_anchor = normalize_multiline(card.get("raw_anchor")) or "원문 수령 후 입력"
    checklist = """
<ul>
  <li>문제 앞면에 정답 누수 없음</li>
  <li>객관식 선지 ①~⑤ 보존</li>
  <li>주관식은 단답/짧은 서술형 답안 분리</li>
  <li>이미지 의존 문항은 front-safe/answer-only 구분</li>
  <li>동일 정답이라도 stem이 다르면 variant 보존</li>
</ul>
""".strip()
    return f"""
<section class="study-guide-block">
  <h3>{e(OFFICIAL_RANGE_LABEL)}</h3>
  <p><strong>단원:</strong> {e(OFFICIAL_UNIT_CHAPTER.get(card.get('official_unit'), card.get('official_unit', '통일/기타')))}</p>
  <p><strong>출처:</strong> {e(card.get('source', 'source pending'))}</p>
  <p><strong>태그:</strong> {e(tags)}</p>
  <p><strong>원문 anchor:</strong><br>{e(raw_anchor).replace(chr(10), '<br>')}</p>
  <h4>3주차 카드화 체크리스트</h4>
  {checklist}
</section>
""".strip()


def normalize_record(src: dict, i: int) -> dict:
    c = dict(src)
    c.setdefault("id", f"PEDS3-{i:03d}")
    c.setdefault("source_rank", i)
    c.setdefault("origin", "actual_recall")
    c.setdefault("priority", "P3 누적복기")
    c["question"] = normalize_multiline(c.get("question") or c.get("q") or "")
    c["answer"] = normalize_multiline(c.get("answer") or c.get("a") or "원문 확인 필요")
    c["explanation"] = normalize_multiline(c.get("explanation") or c.get("lock") or c.get("note") or "")
    if c.get("enhanced_explanation"):
        c["enhanced_explanation"] = normalize_multiline(c.get("enhanced_explanation"))
    c["tags"] = list(dict.fromkeys(c.get("tags", []) or []))
    c["official_unit"] = infer_official_unit(c)
    c["official_chapter"] = OFFICIAL_UNIT_CHAPTER.get(c["official_unit"], c["official_unit"])
    c["uncertain"] = bool(c.get("uncertain") or c.get("origin") == "uncertain_recall" or "원문 확인 필요" in c["answer"])
    if c["uncertain"] and c.get("origin") == "actual_recall":
        c["origin"] = "uncertain_recall"
    return c


def sort_key(card: dict) -> tuple[int, int, str]:
    return (UNIT_RANK.get(card.get("official_unit"), 99), int(card.get("source_rank", 999999)), str(card.get("id", "")))


def load_source_cards() -> list[dict]:
    if not DATA.exists():
        DATA.write_text("[]\n", encoding="utf-8")
        return []
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise TypeError(f"{DATA} must be a JSON list")
    records = [normalize_record(src, i) for i, src in enumerate(raw, 1)]
    return sorted(records, key=sort_key)


def scaffold_records() -> list[dict]:
    return [
        normalize_record(
            {
                "id": "PEDS3-SCAFFOLD-001",
                "source": "scaffold only / 문제 원본 대기",
                "origin": "scaffold",
                "priority": "SCAFFOLD",
                "official_unit": "통일/기타",
                "question": "3주차 pretest 문제 원본을 기다리는 준비 카드입니다. 강렬이 문제 모음을 주면 이 자리에 실제 문항이 들어갑니다.",
                "answer": "원본 수령 후 카드화. 우선 공식 범위 16~28장과 1·2주차 UX/검증 규칙만 고정했습니다.",
                "explanation": "실제 배포 전에는 이 scaffold 카드를 제거하고 source question count와 card count를 맞춥니다.",
                "enhanced_explanation": "🧭 Big picture\n3주차는 범위가 넓어서 문제 모음의 원문 보존이 우선입니다.\n\n🔎 핵심 단서\n공식 범위는 16~28장이고, 전 주 아침 집담회 내용도 나올 수 있습니다.\n\n👣 작업 흐름\n문제 수 세기 → 객관식/주관식/이미지 의존 분리 → JSON 카드화 → 해설 보강 → answer leakage/QC → 필요 시 share 배포.\n\n✅ 3초 Lock line\n3주차는 넓은 범위라 '삭제하지 말고 보존·표시·분류'가 핵심입니다.",
                "tags": ["scaffold", "3주차", "16-28장"],
                "scaffold": True,
                "raw_anchor": "소아청소년과 공지.pdf: 3주차 16~28장 + 전 주 아침 집담회 반영 가능",
            },
            1,
        )
    ]


def add_background_and_unit_filter(records: list[dict], source_count: int) -> None:
    text = OUT.read_text(encoding="utf-8")
    lock = e(LOCK_LINE)
    group_payload = []
    for g in HOME_GROUPS:
        ids = [c["id"] for c in records] if g["key"] == "all" else [c["id"] for c in records if c.get("official_unit") in g["units"]]
        group_payload.append(
            {
                "key": g["key"],
                "label": g["label"],
                "units": g["units"],
                "description": g["description"],
                "accent": g["accent"],
                "ids": ids,
                "count": len(ids),
            }
        )
    group_json = json.dumps(group_payload, ensure_ascii=False)
    css = f"""

/* Pediatric 3-week pretest scaffold */
body.peds-pretest3-bg {{
  background: radial-gradient(circle at 12% 8%, rgba(168,85,247,.22), transparent 32%),
              radial-gradient(circle at 86% 14%, rgba(20,184,166,.18), transparent 30%),
              linear-gradient(135deg, #0f172a 0%, #1e293b 48%, #111827 100%) !important;
}}
body.peds-pretest3-bg::before {{
  content: '{lock}'; position: fixed; left: 0; right: 0; bottom: 0; z-index: 9999;
  padding: 7px 10px; background: rgba(15,23,42,.88); color:#ddd6fe;
  border-top: 1px solid rgba(221,214,254,.35); font-size:12px; font-weight:950;
  letter-spacing:.04em; text-align:center; pointer-events:none;
}}
body.peds-pretest3-bg .main, body.peds-pretest3-bg .quiz-header {{ position: relative; z-index: 1; }}
body.peds-pretest3-bg .card, body.peds-pretest3-bg .quiz-card {{ box-shadow: 0 18px 44px rgba(2,6,23,.24); }}
body.peds-pretest3-bg .tutor-section {{ margin: 12px 0; padding: 10px 12px; background: rgba(255,255,255,.68); border: 1px solid rgba(124,58,237,.14); border-radius: 10px; }}
body.peds-pretest3-bg .tutor-section h4 {{ margin: 0 0 7px; font-size: 15px; color: #581c87; }}
body.peds-pretest3-bg .tutor-section p {{ margin: 0; }}
body.peds-pretest3-bg .tutor-list {{ margin: 0; padding-left: 1.2em; }}
body.peds-pretest3-bg .tutor-list li {{ margin: 4px 0; }}
body.peds-pretest3-bg .answer-final {{ padding: 12px 14px; border: 1px solid #bfdbfe; background: #eff6ff; border-radius: 12px; margin-bottom: 12px; }}
body.peds-pretest3-bg .answer-final h3 {{ margin: 0 0 6px; color: #1d4ed8; }}
body.peds-pretest3-bg .answer-final p {{ margin: 0; font-size: 18px; font-weight: 900; }}
body.peds-pretest3-bg .answer-section {{ margin: 12px 0; padding: 10px 12px; border: 1px solid #e2e8f0; background: rgba(255,255,255,.72); border-radius: 10px; }}
body.peds-pretest3-bg .answer-section h4 {{ margin: 0 0 7px; color: #334155; }}
body.peds-pretest3-bg .answer-section.allen-pdf {{ border-color:#bbf7d0; background:#f0fdf4; }}
body.peds-pretest3-bg .allen-confidence {{ display:inline-block; margin-left:6px; padding:2px 7px; border-radius:999px; background:#dcfce7; color:#166534; font-size:11px; font-weight:900; text-transform:uppercase; }}
body.peds-pretest3-bg .allen-refs ul {{ margin:6px 0 0 18px; padding:0; }}
body.peds-pretest3-bg .allen-refs li {{ margin:4px 0; color:#334155; }}
body.peds-pretest3-bg .allen-refs span {{ font-weight:900; color:#166534; }}
body.peds-pretest3-bg .allen-note {{ margin-top:8px; padding:8px 10px; border-radius:9px; background:#fff7ed; color:#9a3412; font-weight:800; }}
body.peds-pretest3-bg .answer-section.warning {{ border-color: #fecaca; background:#fff1f2; }}
body.peds-pretest3-bg .study-guide-block ul {{ margin-top: 4px; padding-left: 1.2em; }}
body.peds-pretest3-bg .tutor-pre {{ white-space: pre-wrap; font-family: inherit; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:8px; }}
body.peds-pretest3-bg .peds3-source-count::after {{ content: 'source cards: {source_count}'; }}
body.peds-pretest3-bg .peds3-home-wrap {{ margin: 0 0 16px; padding: 16px; border: 1px solid rgba(191,219,254,.32); background: rgba(15,23,42,.45); border-radius: 18px; box-shadow: 0 18px 40px rgba(2,6,23,.18); }}
body.peds-pretest3-bg .peds3-home-head {{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:12px; flex-wrap:wrap; }}
body.peds-pretest3-bg .peds3-home-title {{ font-size: 18px; font-weight: 950; color: #eff6ff; }}
body.peds-pretest3-bg .peds3-home-sub {{ font-size: 13px; line-height: 1.6; color: #cbd5e1; max-width: 780px; }}
body.peds-pretest3-bg .peds3-home-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }}
body.peds-pretest3-bg .peds3-home-card {{ border-radius: 16px; padding: 14px; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.05); color: #f8fafc; box-shadow: 0 10px 24px rgba(15,23,42,.15); }}
body.peds-pretest3-bg .peds3-home-card.active {{ outline: 2px solid rgba(255,255,255,.9); outline-offset: 1px; }}
body.peds-pretest3-bg .peds3-home-label {{ font-size: 16px; font-weight: 950; margin-bottom: 4px; }}
body.peds-pretest3-bg .peds3-home-desc {{ font-size: 12px; line-height: 1.55; color: rgba(255,255,255,.88); min-height: 38px; }}
body.peds-pretest3-bg .peds3-home-count {{ margin-top: 8px; font-size: 13px; font-weight: 900; color: #e2e8f0; }}
body.peds-pretest3-bg .peds3-home-actions {{ display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }}
body.peds-pretest3-bg .peds3-home-btn {{ border:none; border-radius: 999px; padding: 10px 13px; font-size: 12px; font-weight: 900; cursor: pointer; }}
body.peds-pretest3-bg .peds3-home-btn.view {{ background: rgba(255,255,255,.92); color: #0f172a; }}
body.peds-pretest3-bg .peds3-home-btn.seq {{ background: rgba(15,23,42,.88); color: #e0f2fe; border: 1px solid rgba(191,219,254,.55); }}
body.peds-pretest3-bg .peds3-active-filter {{ margin-top: 12px; display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; padding: 10px 12px; border-radius: 14px; background: rgba(15,23,42,.42); border:1px solid rgba(191,219,254,.2); }}
body.peds-pretest3-bg .peds3-active-filter .meta {{ font-size: 13px; color: #dbeafe; line-height:1.5; }}
body.peds-pretest3-bg .peds3-clear-filter {{ border:none; border-radius:999px; padding: 9px 12px; background:#e2e8f0; color:#0f172a; font-size:12px; font-weight:900; cursor:pointer; }}
html.peds3-quiz-isolated, body.peds3-quiz-isolated {{ min-height: 100%; overflow: hidden !important; background: var(--bg) !important; }}
body.peds3-quiz-isolated::before {{ display: none !important; content: none !important; }}
body.peds3-quiz-isolated .sidebar,
body.peds3-quiz-isolated .main,
body.peds3-quiz-isolated .sb-mobile-toggle,
body.peds3-quiz-isolated .mobile-review-start,
body.peds3-quiz-isolated .sb-overlay {{ display: none !important; visibility: hidden !important; }}
body.peds3-quiz-isolated #quizOverlay.quiz-overlay.active {{
  display: flex !important;
  position: fixed !important;
  top: 0 !important; right: 0 !important; bottom: 0 !important; left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  height: 100dvh !important;
  min-height: 100svh !important;
  max-height: 100dvh !important;
  z-index: 100000 !important;
  background: var(--bg) !important;
  overflow-y: auto !important;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}}
body.peds3-quiz-isolated #quizBody {{ flex: 1 0 auto; width: 100%; background: var(--bg); }}
body.peds3-quiz-isolated .quiz-card {{ min-height: calc(100dvh - 64px); box-sizing: border-box; margin: 0 auto !important; padding-bottom: max(92px, env(safe-area-inset-bottom) + 72px) !important; background: var(--bg); }}

@media (max-width: 768px) {{
  body.peds-pretest3-bg .peds3-home-grid {{ grid-template-columns: 1fr; }}
}}

"""
    text = text.replace("</style>", css + "\n</style>", 1)
    text = text.replace("<body>", '<body class="peds-pretest3-bg">', 1)
    unit_counts = {u: sum(1 for c in records if c.get("official_unit") == u) for u in OFFICIAL_UNIT_ORDER}
    summary = "".join(
        f"<span style='{OFFICIAL_UNIT_STYLE[u]}display:inline-block;border-radius:999px;padding:3px 9px;margin:3px;font-size:12px;font-weight:900;'>{e(OFFICIAL_UNIT_CHAPTER[u])} {unit_counts[u]}</span>"
        for u in OFFICIAL_UNIT_ORDER
        if unit_counts[u] or source_count == 0
    )
    scaffold_note = f"""
<div class="peds3-scaffold-note" style="margin:12px 0 18px;padding:14px 16px;border:1px solid rgba(221,214,254,.55);background:rgba(248,250,252,.92);border-radius:16px;box-shadow:0 12px 30px rgba(15,23,42,.16);">
  <div style="font-size:13px;font-weight:950;color:#4c1d95;margin-bottom:6px;">소아청소년과 3주차 Pretest Anki v5 Hybrid</div>
  <div style="font-size:13px;line-height:1.6;color:#334155;">공식 범위는 <strong>16~28장</strong>입니다. 현재 카드 <strong>{source_count}</strong>개를 최신 2026 복기, 25-21 야마/source layout, 2023 PDF audit 기준으로 묶었습니다. 각 카드에는 <strong>기존 튜터식 보강 해설 + Allen PDF 기준 해설/근거</strong>를 함께 붙였습니다. <strong>추정답/원문 확인</strong> 표시는 복기가 불완전하거나 직접 근거가 약해 재확인이 필요한 카드입니다.</div>
  <div style="margin-top:8px;">{summary}</div>
</div>
""".strip()
    home_cards = []
    for group in group_payload:
        home_cards.append(
            f"""
<div class="peds3-home-card" id="peds3-home-card-{e(group['key'])}" style="background:{e(group['accent'])};">
  <div class="peds3-home-label">{e(group['label'])}</div>
  <div class="peds3-home-desc">{e(group['description'])}</div>
  <div class="peds3-home-count">{group['count']} cards</div>
  <div class="peds3-home-actions">
    <button class="peds3-home-btn view" onclick="peds3SelectHomeGroup('{e(group['key'])}')">카드 보기</button>
    <button class="peds3-home-btn seq" onclick="peds3StartGroupSequential('{e(group['key'])}')">순서대로 시작</button>
  </div>
</div>
""".strip()
        )
    home_html = f"""
<div class="peds3-home-wrap" id="peds3HomeWrap">
  <div class="peds3-home-head">
    <div>
      <div class="peds3-home-title">계통별 Anki 시작</div>
      <div class="peds3-home-sub">2주차처럼 계통별로 묶어서 볼 수 있게 홈에서 바로 선택합니다. 각 묶음은 <strong>카드 보기</strong>로 필터링하거나, <strong>순서대로 시작</strong>으로 그 계통만 번호 순서대로 바로 풀 수 있습니다.</div>
    </div>
  </div>
  <div class="peds3-home-grid">
    {''.join(home_cards)}
  </div>
  <div class="peds3-active-filter" id="peds3ActiveFilter">
    <div class="meta" id="peds3FilterMeta">현재: 전체 카드 표시 중</div>
    <button class="peds3-clear-filter" onclick="peds3ClearGroupFilter()">전체로 복귀</button>
  </div>
</div>
""".strip()
    if '<div class="main" id="mainContent">' in text:
        text = text.replace('<div class="main" id="mainContent">', '<div class="main" id="mainContent">\n' + scaffold_note, 1)
    elif '<div class="card-grid">' in text:
        text = text.replace('<div class="card-grid">', scaffold_note + '\n<div class="card-grid">', 1)
    elif '<main' in text:
        text = text.replace('<main', scaffold_note + '\n<main', 1)
    text = text.replace('<div class="review-hero" id="reviewHero">', home_html + '\n<div class="review-hero" id="reviewHero">', 1)
    injected_script = f"""
<script>
(function() {{
  const HOME_GROUPS = {group_json};
  const GROUP_MAP = Object.fromEntries(HOME_GROUPS.map(g => [g.key, g]));
  let currentGroup = 'all';

  function assignSidebarIds() {{
    const items = Array.from(document.querySelectorAll('.sb-item'));
    items.forEach((el, idx) => {{
      el.dataset.cardId = ALL_IDS[idx] || '';
    }});
  }}

  function updateActiveCards() {{
    document.querySelectorAll('.peds3-home-card').forEach(el => el.classList.toggle('active', el.id === 'peds3-home-card-' + currentGroup));
  }}

  function applyGroupFilter(key) {{
    currentGroup = GROUP_MAP[key] ? key : 'all';
    const group = GROUP_MAP[currentGroup] || GROUP_MAP.all;
    const allowed = new Set(group.ids || []);
    ALL_IDS.forEach(id => {{
      const card = document.getElementById('card-' + id);
      if (card) card.style.display = (currentGroup === 'all' || allowed.has(id)) ? '' : 'none';
    }});
    document.querySelectorAll('.sb-item').forEach(el => {{
      const id = el.dataset.cardId;
      if (!id) return;
      el.style.display = (currentGroup === 'all' || allowed.has(id)) ? '' : 'none';
    }});
    const meta = document.getElementById('peds3FilterMeta');
    if (meta) meta.innerHTML = '현재: <strong>' + group.label + '</strong> · ' + group.count + ' cards · ' + group.description;
    updateActiveCards();
  }}

  window.peds3SelectHomeGroup = function(key) {{
    applyGroupFilter(key);
    const main = document.getElementById('mainContent');
    if (main) main.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }};

  window.peds3StartGroupSequential = function(key) {{
    applyGroupFilter(key);
    const group = GROUP_MAP[key] || GROUP_MAP.all;
    if (!group.ids || !group.ids.length) return;
    startQuizWith([...(group.ids || [])]);
  }};

  window.peds3ClearGroupFilter = function() {{
    applyGroupFilter('all');
  }};

  function enterIsolatedQuizPage() {{
    document.documentElement.classList.add('peds3-quiz-isolated');
    document.body.classList.add('peds3-quiz-isolated');
    if (!document.body.dataset.peds3ScrollY) document.body.dataset.peds3ScrollY = String(window.scrollY || 0);
    try {{
      if (location.hash !== '#quiz') history.pushState({{ peds3Quiz: true }}, '', '#quiz');
    }} catch (err) {{}}
    setTimeout(() => {{
      const overlay = document.getElementById('quizOverlay');
      if (overlay) overlay.scrollTop = 0;
      window.scrollTo(0, 0);
    }}, 0);
  }}

  function leaveIsolatedQuizPage() {{
    document.documentElement.classList.remove('peds3-quiz-isolated');
    document.body.classList.remove('peds3-quiz-isolated');
    const y = parseInt(document.body.dataset.peds3ScrollY || '0', 10);
    delete document.body.dataset.peds3ScrollY;
    try {{
      if (location.hash === '#quiz') history.replaceState(null, '', location.pathname + location.search);
    }} catch (err) {{}}
    setTimeout(() => window.scrollTo(0, Number.isFinite(y) ? y : 0), 0);
  }}

  const baseStartQuizWith = window.startQuizWith;
  if (typeof baseStartQuizWith === 'function') {{
    window.startQuizWith = function(...args) {{
      enterIsolatedQuizPage();
      return baseStartQuizWith.apply(this, args);
    }};
  }}

  const baseExitQuiz = window.exitQuiz;
  if (typeof baseExitQuiz === 'function') {{
    window.exitQuiz = function(...args) {{
      const result = baseExitQuiz.apply(this, args);
      leaveIsolatedQuizPage();
      return result;
    }};
  }}

  window.addEventListener('popstate', () => {{
    const overlay = document.getElementById('quizOverlay');
    if (overlay && overlay.classList.contains('active') && location.hash !== '#quiz' && typeof window.exitQuiz === 'function') {{
      window.exitQuiz();
    }}
  }});

  assignSidebarIds();
  applyGroupFilter('all');
}})();
</script>
""".strip()
    text = text.replace('</body>', injected_script + '\n</body>', 1)
    OUT.write_text(text, encoding="utf-8")


def main() -> None:
    source_records = load_source_cards()
    records = source_records if source_records else scaffold_records()
    if source_records:
        DATA.write_text(json.dumps(source_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cards = [{"id": c["id"], "num": i, "q": question_html(c), "a": answer_html(c), "g": guide_html(c)} for i, c in enumerate(records, 1)]
    builder = QuizBuilder(
        cards=cards,
        title=TITLE,
        subtitle="공식 3주차 16~28장 · 혈액-종양/신요로/내분비/신경-근육/골격/알레르기/결체조직/피부/안과/손상/통일 + 집담회 후보",
        storage_prefix=STORAGE_PREFIX,
        enable_self_answer=False,
        randomize_review=True,
    )
    builder.write(str(OUT))
    add_background_and_unit_filter(records, source_count=len(source_records))
    print(f"source_cards: {len(source_records)}")
    print(f"rendered_cards: {len(cards)}")
    print(f"data: {DATA}")
    print(f"out: {OUT}")
    print(f"storage_prefix: {STORAGE_PREFIX}_")


if __name__ == "__main__":
    main()
