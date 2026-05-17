#!/usr/bin/env python3
"""Generate 소아청소년과 2주차 Pretest full-source Anki-style SRS quiz.

Full mode policy (2026-05-17):
- Preserve existing 79-card v2 source-faithful deck with enhanced tutor explanations.
- Add all 2025 usable source-variant missing cards.
- Add all 2023 PDF actual/source-variant cards.
- Include ALL HI 2차 bank raw questions, not only high-priority candidates.
- Keep generated output separate from the existing v2 quiz to avoid breaking the current live deck.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

from anki_quiz_builder import QuizBuilder

ROOT = Path(__file__).resolve().parent.parent
QUIZ_DIR = ROOT / "quizzes"
DATA_DIR = QUIZ_DIR / "data"
ASSET_DIR = QUIZ_DIR / "assets" / "peds_pretest2_full"
DATA_FULL = DATA_DIR / "pediatrics_pretest2_full_cards.json"
OUT = QUIZ_DIR / "소아청소년과_2주차_pretest_full_quiz.html"
TITLE = "소아청소년과 2주차 Pretest FULL SRS"
STORAGE_PREFIX = "peds_pretest2_full_20260517_allhi"
LOCK_LINE = "2주차 FULL: 2026·2025·2023 actual + HI 156 전부"

WS = ROOT.parent
TMP = WS / ".tmp"
CORE79 = DATA_DIR / "pediatrics_pretest2_cards.json"
V3_2025 = TMP / "peds_pretest2_fullhunt_20260517" / "worker_2025_missing_v3_cards.json"
V3_2023 = TMP / "peds_pretest2_fullhunt_20260517" / "worker_2023_v3_cards.json"
HI_ALL = TMP / "peds_pretest2_review_20260517" / "hi_extract" / "HI_2차_기출문제_원문+이미지_2026-05-17.json"
NON_HI_IMG_MAP = TMP / "peds_pretest2_image_extract_20260517" / "NON_HI_current_deck_image_card_link_candidates_2026-05-17.json"

LAYER_LABELS = {
    "core79": "✅ Core 79",
    "source2025": "🧩 2025 source-variant",
    "source2023pdf": "🧾 2023 PDF raw",
    "hi156": "🛡️ HI 156 bank",
    "candidate": "🧠 추가 후보",
}

LAYER_STYLE = {
    "core79": "background:#1d4ed8;color:#eff6ff;border:1px solid #93c5fd;",
    "source2025": "background:#78350f;color:#ffedd5;border:1px solid #fdba74;",
    "source2023pdf": "background:#581c87;color:#f3e8ff;border:1px solid #d8b4fe;",
    "hi156": "background:#7f1d1d;color:#fee2e2;border:1px solid #fca5a5;",
    "candidate": "background:#166534;color:#dcfce7;border:1px solid #86efac;",
}

PRIORITY_STYLE = {
    "P4 최신2026": "background:#dc2626;color:#fff;border:1px solid #fecaca;",
    "P3 누적복기": "background:#1d4ed8;color:#fff;border:1px solid #bfdbfe;",
    "P3 2023PDF source-variant": "background:#6d28d9;color:#fff;border:1px solid #ddd6fe;",
    "P2 near-variant": "background:#7c2d12;color:#fff;border:1px solid #fed7aa;",
    "P2 covered-variant": "background:#334155;color:#e2e8f0;border:1px solid #94a3b8;",
    "P1 HI full bank": "background:#991b1b;color:#fff;border:1px solid #fecaca;",
}

ORIGIN_LABELS = {
    "actual_recall": "✅ 실제 복기",
    "uncertain_recall": "⚠️ 불완전 복기",
    "actual_recall_source_variant": "🧬 원문 variant",
    "hi_bank_raw": "🛡️ HI 원문 bank",
}

# Official 2-week pretest scope from 교수님 공지 PDF:
# 2주차 = 12~15장: 감염, 소화기, 호흡기, 심혈관.
# Some all-HI-bank cards are retained even when they look mixed/out-of-scope;
# those are marked separately instead of being forced into a wrong unit.
OFFICIAL_UNIT_ORDER = ["감염", "소화기", "호흡기", "심혈관", "범위외/확인"]

OFFICIAL_UNIT_CHAPTER = {
    "감염": "12장 감염",
    "소화기": "13장 소화기",
    "호흡기": "14장 호흡기",
    "심혈관": "15장 심혈관",
    "범위외/확인": "범위외/혼입 확인",
}

OFFICIAL_UNIT_STYLE = {
    "감염": "background:#9f1239;color:#fff1f2;border:1px solid #fecdd3;",
    "소화기": "background:#92400e;color:#fffbeb;border:1px solid #fde68a;",
    "호흡기": "background:#075985;color:#e0f2fe;border:1px solid #7dd3fc;",
    "심혈관": "background:#991b1b;color:#fee2e2;border:1px solid #fca5a5;",
    "범위외/확인": "background:#374151;color:#f9fafb;border:1px solid #d1d5db;",
}

OFFICIAL_UNIT_RANK = {unit: i for i, unit in enumerate(OFFICIAL_UNIT_ORDER)}

HEART_PATTERN = r"심장|심혈|심질환|심잡음|VSD|ASD|TOF|TGA|AVSD|TAPVR|CoA|PSVT|SVT|ECG|EKG|심전도|심부전|심내막염|가와사키|관상동맥|동맥관|태아순환|태아 순환|폐동맥|대혈관|심도자|murmur|Knee-chest|Tetralogy|혈압"
RESP_PATTERN = r"호흡기|호흡|폐렴|기관지|세기관지|천식|부비동|중이염|크루프|후두|기도|천명|기침|흉부|CXR|ABGA|PaCO2|산소|SpO2|결핵|TB|객혈|객담|무호흡|bronchio|pneumo|asthma|croup|sinus|otitis|wheezing|흉수|인두후부|상기도|하기도|폐|이물흡인|하임리히|Heimlich"
GI_PATTERN = r"소화기|위장|장중첩|설사|구토|복통|혈변|변비|식도|장염|식중독|간염|황달|췌장|담도|수유|탈수|수액|전해질|Hirschsprung|선천거대결장|항문|복부|대변|NGT|PEG|아연|경구|위식도|GERD|intussusception|diarrhea|constipation|jaundice|hepatitis|pancrea|esoph|ORS|로타|살모넬라"
INFECTION_PATTERN = r"감염|발열|불명열|무병소|패혈|균혈|홍역|수두|성홍열|백일해|파상풍|EBV|전염 단핵|전염단핵|포도알균|수막|뇌염|골수염|화농|봉와직염|연조직|농가진|림프절|MRSA|Acyclovir|예방접종|면역글로불린|AIDS|HIV|농양|UTI|요로감염|세균|바이러스|항생제|Koplik|measles|varicella|scarlet|pertussis|tetanus|mening|sepsis|FUO|fever|cellulitis|impetigo|mononucleosis|쯔쯔가무시|HSV|수족구|손위생|수술 60분"
ALLERGY_OUT_OF_SCOPE_PATTERN = r"아나필락|알레르|두드러기|피부단자|RAST|food allergy|식품\s*(?:제거|유발)|allergic"


def e(value: object) -> str:
    return html.escape(str(value or ""), quote=False)


def normalize_space(value: object) -> str:
    return re.sub(r"[ \t]+", " ", str(value or "")).strip()


def normalize_multiline(value: object) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fmt(text: object) -> str:
    raw = normalize_multiline(text)
    if not raw:
        return ""
    safe = e(raw)
    safe = re.sub(r"\s+(?=[①②③④⑤])", "<br>", safe)
    safe = re.sub(r"\s+(?=[1-5][\)\.]\s*)", "<br>", safe)
    safe = re.sub(r"\s+(Q[12]\.)", r"<br>\1", safe)
    safe = safe.replace("\n", "<br>")
    return safe


def pill(text: str, style: str = "") -> str:
    base = "display:inline-block;border-radius:999px;padding:2px 8px;margin:2px 4px 2px 0;font-size:11px;font-weight:900;line-height:1.35;"
    return f'<span style="{base}{style}">{e(text)}</span>'


def official_unit_signal_text(card: dict) -> str:
    """High-signal classification text.

    Do not use enhanced_explanation here: tutor explanations mention many
    differentials and can leak unrelated systems into the unit classifier.
    """
    fields = ["section", "question", "display_question", "answer", "raw_problem"]
    tags = " ".join(str(t) for t in card.get("tags", []) or [])
    return unicodedata.normalize("NFC", " ".join([tags] + [str(card.get(k, "") or "") for k in fields]))


def infer_official_unit(card: dict) -> str:
    """Map a card into the official 2-week pretest units from the notice PDF."""
    tags = [unicodedata.normalize("NFC", str(t)) for t in card.get("tags", []) or []]
    text = official_unit_signal_text(card)
    section = unicodedata.normalize("NFC", str(card.get("section") or ""))

    # Official 2주차 is only 12~15장. Allergy/immunology-looking HI cards are
    # kept because HI full-bank policy says keep all 156, but they should not be
    # silently mixed into 호흡기/감염.
    if re.search(ALLERGY_OUT_OF_SCOPE_PATTERN, text, re.I) and not re.search(r"천식|기관지|호흡|하기도|상기도|쌕쌕|천명", text, re.I):
        return "범위외/확인"

    # Prefer explicit curator tags/HI section names before noisy stem fallback.
    if any(t in {"심장", "심혈관", "ECG", "EKG", "가와사키병"} for t in tags) or re.search(HEART_PATTERN, section, re.I):
        return "심혈관"
    if any(t in {"호흡기", "상기도", "하기도", "이비인후", "흉수", "천식"} for t in tags) or re.search(RESP_PATTERN, section, re.I):
        return "호흡기"
    if any(t in {"소화기", "영양", "탈수"} for t in tags) or re.search(GI_PATTERN, section, re.I):
        return "소화기"
    if any(t in {"감염", "감염관리", "피부", "신장"} for t in tags) or re.search(INFECTION_PATTERN, section, re.I):
        return "감염"

    # Fallback: system-specific patterns before generic infection terms.
    if re.search(HEART_PATTERN, text, re.I):
        return "심혈관"
    if re.search(RESP_PATTERN, text, re.I):
        return "호흡기"
    if re.search(GI_PATTERN, text, re.I):
        return "소화기"
    if re.search(INFECTION_PATTERN, text, re.I):
        return "감염"
    return "범위외/확인"


def apply_official_unit(card: dict) -> None:
    unit = infer_official_unit(card)
    card["official_unit"] = unit
    card["official_chapter"] = OFFICIAL_UNIT_CHAPTER[unit]
    card["tags"] = list(dict.fromkeys(card.get("tags", []) + [card["official_chapter"], unit]))


def sanitize_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")[:160] or "asset"


def copy_asset(src: object, card_id: str, kind: str) -> dict | None:
    if not src:
        return None
    p = Path(str(src))
    if not p.exists():
        return None
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    dest = ASSET_DIR / f"{sanitize_name(card_id)}__{kind}__{sanitize_name(p.name)}"
    if not dest.exists():
        shutil.copy2(p, dest)
    rel = dest.relative_to(QUIZ_DIR).as_posix()
    return {"src": rel, "kind": kind, "source_path": str(p)}


def load_non_hi_image_map() -> dict[str, list[dict]]:
    if not NON_HI_IMG_MAP.exists():
        return {}
    rows = json.loads(NON_HI_IMG_MAP.read_text(encoding="utf-8"))
    out: dict[str, list[dict]] = {}
    for row in rows:
        cands = row.get("candidates") or []
        usable = []
        for cand in cands[:2]:
            # Conservative: keep only candidates that were at least contextually linked.
            if int(cand.get("score", 0)) >= 4 and cand.get("path"):
                item = copy_asset(cand["path"], row.get("card_id", "nonhi"), cand.get("curated_id", "nonhi"))
                if item:
                    item["caption"] = f"non-HI candidate · score {cand.get('score')} · {cand.get('curated_id', '')}"
                    usable.append(item)
        if usable:
            out[row.get("card_id", "")] = usable
    return out


def mask_hi_front(raw: str) -> str:
    front = normalize_multiline(raw)
    # Hide explicit answer tails.
    front = re.sub(r"A\)\s*[^\n]+", "A) [답 숨김]", front)
    front = re.sub(r"(답\s*[:：])\s*[^\n]+", r"\1 [답 숨김]", front)
    front = re.sub(r"(정답\s*[:：])\s*[^\n]+", r"\1 [답 숨김]", front)
    # Hide direct answer after a question mark on the same line, common in HI source.
    front = re.sub(r"([?？])\s{1,}([^\n①②③④⑤]{1,80})(?=\n|$)", r"\1 [답 숨김]", front)
    # Hide answer-only dash lines after stems.
    front = re.sub(r"(?m)^\s*[-·]\s*([^\n]{2,100})$", r"- [답 숨김]", front)
    return front


def extract_hi_answer(raw: str) -> str:
    text = normalize_multiline(raw)
    answers: list[str] = []
    for m in re.finditer(r"A\)\s*([^\n]+)", text):
        answers.append(m.group(1).strip())
    for m in re.finditer(r"답\s*[:：]\s*([^\n]+)", text):
        answers.append(m.group(1).strip())
    for m in re.finditer(r"정답\s*[:：]\s*([^\n]+)", text):
        answers.append(m.group(1).strip())
    for m in re.finditer(r"[?？]\s{2,}([^\n①②③④⑤]{1,90})(?=\n|$)", text):
        val = m.group(1).strip(" -·")
        if val and not val.startswith(("①", "②", "③", "④", "⑤")):
            answers.append(val)
    # Last resort: dash answer lines in short-answer cards.
    dash = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("- ", "· ")) and len(s) > 3:
            dash.append(s[2:].strip())
    if dash and not answers:
        answers.extend(dash[-3:])
    cleaned = []
    for a in answers:
        a = re.sub(r"\s+", " ", a).strip(" .;")
        if a and a not in cleaned:
            cleaned.append(a)
    if cleaned:
        return " / ".join(cleaned[:5])
    return "원문 확인 필요"


def card_pills(card: dict) -> str:
    parts = []
    unit = card.get("official_unit", "")
    chapter = card.get("official_chapter", OFFICIAL_UNIT_CHAPTER.get(unit, unit))
    if unit:
        parts.append(pill(chapter, OFFICIAL_UNIT_STYLE.get(unit, "background:#374151;color:#f9fafb;border:1px solid #d1d5db;")))
    layer = card.get("layer", "")
    parts.append(pill(LAYER_LABELS.get(layer, layer), LAYER_STYLE.get(layer, "background:#334155;color:#e2e8f0;border:1px solid #94a3b8;")))
    pri = card.get("priority", "")
    if pri:
        parts.append(pill(pri, PRIORITY_STYLE.get(pri, "background:#334155;color:#e2e8f0;border:1px solid #94a3b8;")))
    origin = card.get("origin", "")
    if origin:
        parts.append(pill(ORIGIN_LABELS.get(origin, origin), "background:#111827;color:#e5e7eb;border:1px solid #64748b;"))
    if card.get("uncertain"):
        parts.append(pill("원문 확인", "background:#7f1d1d;color:#fee2e2;border:1px solid #fca5a5;"))
    if card.get("has_image"):
        parts.append(pill("이미지", "background:#14532d;color:#dcfce7;border:1px solid #86efac;"))
    return "".join(parts)


def tags_html(tags: list[str]) -> str:
    return "".join(f'<span class="mini-tag">#{e(t)}</span>' for t in tags)


def images_html(card: dict, where: str) -> str:
    imgs = card.get("images", []) or []
    if not imgs:
        return ""
    figs = []
    for img in imgs:
        # Avoid text-answer crops on the front. Embedded images are safer; source crops stay answer/guide only.
        if where == "front" and img.get("kind") not in {"embedded", "linked", "nonhi_exact"}:
            continue
        caption = img.get("caption") or img.get("kind") or "image"
        figs.append(f"""
<figure style="margin:10px 0;padding:8px;border:1px solid #cbd5e1;border-radius:10px;background:#fff;">
  <img src="{e(img.get('src'))}" alt="{e(caption)}" style="max-width:100%;height:auto;border-radius:8px;display:block;margin:auto;" />
  <figcaption style="font-size:11px;color:#64748b;margin-top:6px;text-align:center;">{e(caption)}</figcaption>
</figure>
""".strip())
    if not figs:
        return ""
    return "<div class='source-images'>" + "".join(figs) + "</div>"


def format_tutor_html(text: object) -> str:
    raw = normalize_multiline(text)
    if not raw:
        return ""
    blocks = []
    for block in re.split(r"\n\s*\n", raw):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        first = lines[0].strip()
        if re.match(r"^[🧭🔎👣🧠📊✅🎯]", first):
            body = "\n".join(lines[1:]).strip()
            blocks.append(f"<section class='tutor-section'><h4>{e(first)}</h4><p>{fmt(body)}</p></section>")
        else:
            blocks.append(f"<p>{fmt(block)}</p>")
    return "".join(blocks)


def answer_html(card: dict) -> str:
    explanation = card.get("enhanced_explanation") or card.get("explanation") or ""
    raw_block = ""
    if card.get("raw_problem"):
        raw_block = f"""
  <details style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:10px;padding:10px 12px;color:#334155;">
    <summary style="cursor:pointer;font-weight:900;">원문 raw 보기</summary>
    <p style="line-height:1.7;">{fmt(card.get('raw_problem'))}</p>
  </details>
""".strip()
    return f"""
<section class="kmle-answer" style="display:flex;flex-direction:column;gap:12px;">
  <div style="border-left:4px solid #2563eb;background:#eff6ff;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#1d4ed8;margin-bottom:6px;letter-spacing:.04em;">문제</div>
    <div style="font-size:15px;line-height:1.72;color:#111827;">{fmt(card.get('display_question') or card.get('question'))}</div>
    {images_html(card, 'answer')}
  </div>
  <div style="border-left:4px solid #16a34a;background:#f0fdf4;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#15803d;margin-bottom:6px;letter-spacing:.04em;">답</div>
    <div style="font-size:20px;line-height:1.55;color:#052e16;"><strong>{e(card.get('answer'))}</strong></div>
    <div style="margin-top:8px;font-size:12px;color:#475569;">{card_pills(card)}</div>
  </div>
  <div style="border-left:4px solid #f59e0b;background:#fffbeb;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#b45309;margin-bottom:6px;letter-spacing:.04em;">해설 / 판단</div>
    <div style="font-size:15px;line-height:1.75;color:#451a03;">{format_tutor_html(explanation) or fmt(explanation)}</div>
  </div>
  {raw_block}
  <details style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px 12px;color:#334155;">
    <summary style="cursor:pointer;font-weight:800;">출처 / 태그</summary>
    <h4>출처</h4>
    <p><code>{e(card.get('source', '-'))}</code></p>
    <p>Official unit: <code>{e(card.get('official_chapter', '-'))}</code> · Section: <code>{e(card.get('section', '-'))}</code> · Mode: <code>{e(card.get('mode', '-'))}</code></p>
    <div class="tag-row">{tags_html(card.get('tags', []))}</div>
  </details>
</section>
""".strip()


def guide_html(card: dict) -> str:
    return f"""
<section class="kmle-guide" style="line-height:1.7;">
  <h4>문제</h4>
  <p>{fmt(card.get('display_question') or card.get('question'))}</p>
  {images_html(card, 'guide')}
  <h4>답</h4>
  <p><strong>{e(card.get('answer'))}</strong></p>
  <h4>해설</h4>
  <div>{format_tutor_html(card.get('enhanced_explanation') or card.get('explanation', '')) or fmt(card.get('explanation', ''))}</div>
  <h4>분류</h4>
  <p>{card_pills(card)}</p>
  <table>
    <tr><th>Layer</th><td>{e(card.get('layer'))}</td></tr>
    <tr><th>Origin</th><td>{e(card.get('origin'))}</td></tr>
    <tr><th>Official unit</th><td>{e(card.get('official_chapter'))}</td></tr>
    <tr><th>Source</th><td>{e(card.get('source'))}</td></tr>
    <tr><th>Section</th><td>{e(card.get('section'))}</td></tr>
    <tr><th>Mode</th><td>{e(card.get('mode'))}</td></tr>
  </table>
</section>
""".strip()


def question_html(card: dict) -> str:
    return f"""
<div style="display:flex;flex-direction:column;gap:8px;width:100%;">
  <div style="font-size:11px;font-weight:900;color:#93c5fd;letter-spacing:.06em;">문제</div>
  <div style="font-size:14px;line-height:1.62;color:#e5e7eb;">{fmt(card.get('display_question') or card.get('question'))}</div>
  {images_html(card, 'front')}
  <div style="display:flex;gap:5px;flex-wrap:wrap;align-items:center;">{card_pills(card)}</div>
</div>
""".strip()


def normalize_base_card(src: dict, idx: int, layer: str, default_priority: str, default_origin: str) -> dict:
    c = dict(src)
    c.setdefault("id", f"{layer}_{idx:03d}")
    c["layer"] = layer
    c.setdefault("origin", default_origin)
    c.setdefault("priority", default_priority)
    c.setdefault("mode", c.get("kind") or ("객관식" if re.search(r"[①②③④⑤]", str(c.get("question", ""))) else "주관식"))
    c.setdefault("source_rank", idx)
    c["question"] = normalize_multiline(c.get("question") or c.get("q") or "")
    c["display_question"] = normalize_multiline(c.get("display_question") or c["question"])
    c["answer"] = normalize_space(c.get("answer") or c.get("a") or "원문 확인 필요")
    c["explanation"] = normalize_multiline(c.get("explanation") or c.get("lock") or c.get("note") or "")
    c["enhanced_explanation"] = normalize_multiline(c.get("enhanced_explanation") or "")
    c["source"] = normalize_space(c.get("source") or "")
    c["section"] = normalize_space(c.get("section") or c.get("priority") or "")
    c["tags"] = list(dict.fromkeys([str(t) for t in c.get("tags", [])] + ["소아과", "pretest", "2주차", layer, c["origin"]]))
    c["uncertain"] = bool(c.get("uncertain") or "원문 확인 필요" in c["answer"] or c["origin"] == "uncertain_recall")
    c.setdefault("images", [])
    c["has_image"] = bool(c.get("images"))
    return c


def build_hi_card(src: dict, idx: int) -> dict:
    raw = normalize_multiline(src.get("raw_problem", ""))
    card_id = f"PEDS2-HI2-{idx:03d}"
    images = []
    for p in src.get("linked_images") or []:
        item = copy_asset(p, card_id, "embedded")
        if item:
            item["caption"] = f"HI embedded image · {Path(p).name}"
            images.append(item)
    if src.get("question_crop"):
        item = copy_asset(src.get("question_crop"), card_id, "source_crop")
        if item:
            item["caption"] = "HI source crop · 원문 위치 확인용"
            images.append(item)
    answer = extract_hi_answer(raw)
    section = normalize_space(src.get("section") or "HI")
    kind = normalize_space(src.get("kind") or src.get("marker") or "HI")
    front = mask_hi_front(raw)
    explanation = f"HI 2차 bank 원문보존 카드입니다. 섹션은 {section}, 문항 유형은 {kind}입니다. 답은 원문에서 추출한 값이며, '원문 확인 필요' 표시는 정답이 명시되지 않았거나 선지/이미지 의존성이 큰 경우입니다."
    if src.get("linked_image_ids") or src.get("question_crop"):
        explanation += " 이미지 의존 가능성이 있어 answer/guide의 이미지와 source crop을 함께 확인하세요."
    return {
        "id": card_id,
        "layer": "hi156",
        "origin": "hi_bank_raw",
        "priority": "P1 HI full bank",
        "mode": kind,
        "source_rank": 1000 + idx,
        "source": "소아과 pre-test 2차_HI.pdf",
        "section": section,
        "question": raw,
        "display_question": front,
        "raw_problem": raw,
        "answer": answer,
        "explanation": explanation,
        "enhanced_explanation": "",
        "tags": list(dict.fromkeys(["소아과", "pretest", "2주차", "HI", "HI-2차", kind, section, "hi_bank_raw"])),
        "uncertain": answer == "원문 확인 필요",
        "images": images,
        "has_image": bool(images),
        "hi_id": src.get("id"),
        "page": src.get("page"),
        "column": src.get("column"),
    }


def load_existing_full_explanations() -> dict[str, str]:
    if not DATA_FULL.exists():
        return {}
    try:
        rows = json.loads(DATA_FULL.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {str(c.get("id")): str(c.get("enhanced_explanation") or "").strip() for c in rows if c.get("id") and c.get("enhanced_explanation")}


def load_all_records() -> list[dict]:
    existing_enhanced = load_existing_full_explanations()
    non_hi_images = load_non_hi_image_map()
    records: list[dict] = []

    core = json.loads(CORE79.read_text(encoding="utf-8"))
    existing_ids: set[str] = set()
    for i, c in enumerate(core, 1):
        cid = str(c.get("id", ""))
        if cid.startswith("PEDS2-2023PDF-"):
            layer = "source2023pdf"
        elif cid.startswith("PEDS2-EXTRA-") or cid.startswith("PEDS2-CONF-"):
            layer = "candidate"
        else:
            layer = "core79"
        rec = normalize_base_card(c, i, layer, c.get("priority") or "P3 누적복기", c.get("origin") or "actual_recall")
        rec["source_rank"] = i
        rec["images"] = non_hi_images.get(rec["id"], [])
        rec["has_image"] = bool(rec["images"])
        records.append(rec)
        existing_ids.add(rec["id"])

    extra2025 = json.loads(V3_2025.read_text(encoding="utf-8")) if V3_2025.exists() else []
    for i, c in enumerate(extra2025, 1):
        if c.get("id") in existing_ids:
            continue
        rec = normalize_base_card(c, i, "source2025", c.get("priority") or "P3 누적복기", c.get("origin") or "actual_recall")
        rec["source_rank"] = 2000 + i
        rec["tags"].extend(["2025-source-variant"])
        records.append(rec)
        existing_ids.add(rec["id"])

    extra2023 = json.loads(V3_2023.read_text(encoding="utf-8")) if V3_2023.exists() else []
    for i, c in enumerate(extra2023, 1):
        if c.get("id") in existing_ids:
            continue
        rec = normalize_base_card(c, i, "source2023pdf", c.get("priority") or "P3 2023PDF source-variant", c.get("origin") or "actual_recall_source_variant")
        rec["source_rank"] = 3000 + i
        rec["tags"].extend(["2023-PDF", str(c.get("source_variant_status_vs_current79", "variant"))])
        records.append(rec)
        existing_ids.add(rec["id"])

    hi = json.loads(HI_ALL.read_text(encoding="utf-8"))
    for i, src in enumerate(hi, 1):
        records.append(build_hi_card(src, i))

    # Stable output order: official 2주차 units first, source order inside each unit.
    for n, rec in enumerate(records, 1):
        rec["tags"] = list(dict.fromkeys(rec.get("tags", [])))
        if rec.get("id") in existing_enhanced:
            rec["enhanced_explanation"] = existing_enhanced[rec["id"]]
        apply_official_unit(rec)

    records.sort(key=lambda r: (OFFICIAL_UNIT_RANK.get(r.get("official_unit"), 99), int(r.get("source_rank", 999999)), str(r.get("id", ""))))

    for n, rec in enumerate(records, 1):
        rec["num"] = n
    return records


def add_background_and_stats() -> None:
    text = OUT.read_text(encoding="utf-8")
    data = json.loads(DATA_FULL.read_text(encoding="utf-8"))
    counts = {k: sum(1 for c in data if c.get("layer") == k) for k in ["core79", "source2025", "source2023pdf", "candidate", "hi156"]}
    unit_counts = {u: sum(1 for c in data if c.get("official_unit") == u) for u in OFFICIAL_UNIT_ORDER}
    stats = f"공식 2주차: 감염 {unit_counts['감염']} · 소화기 {unit_counts['소화기']} · 호흡기 {unit_counts['호흡기']} · 심혈관 {unit_counts['심혈관']} · 범위외/확인 {unit_counts['범위외/확인']} · Total {len(data)}"
    source_stats = f"Core {counts['core79']} · 2025+{counts['source2025']} · 2023PDF {counts['source2023pdf']} · 후보 {counts['candidate']} · HI {counts['hi156']}"
    css = f"""

/* Pediatric pretest2 FULL source wall */
body.peds-pretest2-full-bg {{
  background: radial-gradient(circle at 12% 8%, rgba(14,165,233,.22), transparent 32%),
              radial-gradient(circle at 84% 10%, rgba(220,38,38,.20), transparent 34%),
              linear-gradient(135deg, #0f172a 0%, #1e293b 48%, #111827 100%) !important;
}}
body.peds-pretest2-full-bg::before {{
  content: '{e(stats)}'; position: fixed; left: 0; right: 0; bottom: 0; z-index: 9999;
  padding: 7px 10px; background: rgba(15,23,42,.90); color:#bfdbfe;
  border-top: 1px solid rgba(147,197,253,.35); font-size:12px; font-weight:950;
  letter-spacing:.04em; text-align:center; pointer-events:none;
}}
body.peds-pretest2-full-bg::after {{
  content: '{e(source_stats)}'; position: fixed; left: 8px; top: 8px; z-index: 9999;
  padding: 5px 8px; border-radius: 999px; background: rgba(15,23,42,.82); color:#dbeafe;
  border: 1px solid rgba(147,197,253,.30); font-size:11px; font-weight:900;
  pointer-events:none;
}}
body.peds-pretest2-full-bg .main, body.peds-pretest2-full-bg .quiz-header {{ position: relative; z-index: 1; }}
body.peds-pretest2-full-bg .card, body.peds-pretest2-full-bg .quiz-card {{ box-shadow: 0 18px 44px rgba(2,6,23,.24); }}
body.peds-pretest2-full-bg .tutor-section {{ margin: 12px 0; padding: 10px 12px; background: rgba(255,255,255,.62); border: 1px solid rgba(124,58,237,.14); border-radius: 10px; }}
body.peds-pretest2-full-bg .tutor-section h4 {{ margin: 0 0 7px; font-size: 15px; color: #581c87; }}
body.peds-pretest2-full-bg .source-images img {{ max-height: 520px; object-fit: contain; }}
"""
    text = text.replace("</style>", css + "\n</style>", 1)
    text = text.replace("<body>", '<body class="peds-pretest2-full-bg">', 1)
    OUT.write_text(text, encoding="utf-8")


def main() -> None:
    records = load_all_records()
    DATA_FULL.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = [{"id": c["id"], "num": i, "q": question_html(c), "a": answer_html(c), "g": guide_html(c)} for i, c in enumerate(records, 1)]
    builder = QuizBuilder(
        cards=cards,
        title=TITLE,
        subtitle="교수님 공지 기준 2주차 12~15장: 감염 → 소화기 → 호흡기 → 심혈관 정렬 · Core 79 + 2025 variants + 2023 PDF + HI 156 전체",
        storage_prefix=STORAGE_PREFIX,
        enable_self_answer=False,
        randomize_review=True,
    )
    builder.write(str(OUT))
    add_background_and_stats()
    print(f"core79: {sum(1 for c in records if c['layer']=='core79')}")
    print(f"source2025: {sum(1 for c in records if c['layer']=='source2025')}")
    print(f"source2023pdf: {sum(1 for c in records if c['layer']=='source2023pdf')}")
    print(f"candidate: {sum(1 for c in records if c['layer']=='candidate')}")
    print(f"hi156: {sum(1 for c in records if c['layer']=='hi156')}")
    for unit in OFFICIAL_UNIT_ORDER:
        print(f"unit_{unit}: {sum(1 for c in records if c.get('official_unit') == unit)}")
    print(f"total_cards: {len(cards)}")
    print(f"data: {DATA_FULL}")
    print(f"out: {OUT}")
    print(f"assets: {ASSET_DIR}")
    print(f"storage_prefix: {STORAGE_PREFIX}_")


if __name__ == "__main__":
    main()
