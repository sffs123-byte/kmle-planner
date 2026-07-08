#!/usr/bin/env python3
"""Generate the orthopedics PK100 quiz with the reusable Anki builder.

Source inventory:
- PK_시험문제_100.docx
- PK_시험문제_100_정답해설_일부수정.pdf

The extracted card/image JSON is stored in quizzes/data/ortho_pk100_questions.json.
Keep this generator as the source of truth for the published HTML.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from anki_quiz_builder import QuizBuilder, run_rails


ROOT = Path(__file__).resolve().parent.parent
QUIZ_DIR = ROOT / "quizzes"
DATA = QUIZ_DIR / "data" / "ortho_pk100_questions.json"
OUT = QUIZ_DIR / "정형외과_PK100_Anki.html"

TITLE = "정형외과 PK 시험문제 100 (81문항)"
STORAGE_PREFIX = "ortho_pk100_anki_skill_20260708"
LOCK_LINE = (
    "Anki Quiz Builder rail · 원문 파일상 25-30번 누락 · "
    "81문항 · 이미지 103개 · 정답 매핑 81/81"
)

MANUAL_NOTES = {
    22: "정답은 수정 PDF 시각 하이라이트 기준으로 수동 보정함.",
    23: "정답은 원본 PDF 시각 하이라이트 기준으로 수동 보정함.",
    31: "정답은 수정 PDF 시각 하이라이트 기준으로 수동 보정함.",
    72: "정답은 수정 PDF 시각 하이라이트 기준으로 수동 보정함.",
    82: "두 해설 PDF 모두 정답 하이라이트가 없어 Thomas test 문항으로 보고 1번으로 보정함.",
}

CATEGORY_LABELS = {
    "foot_ankle": "Foot & ankle",
    "hand_wrist": "Hand & wrist",
    "hip_pelvis": "Hip & pelvis",
    "knee": "Knee",
    "ortho_general": "General orthopedics",
    "shoulder": "Shoulder",
    "spine": "Spine",
    "trauma": "Trauma",
    "tumor_infection": "Tumor/Infection",
}


def e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def normalize_text(value: object) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def paragraph_html(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    blocks = []
    for block in text.split("\n\n"):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        safe = "<br>".join(e(line) for line in lines)
        blocks.append(f"<p style='margin:8px 0;line-height:1.62;'>{safe}</p>")
    return "\n".join(blocks)


def render_images(images: list[dict], label: str) -> str:
    if not images:
        return ""
    parts = [
        "<div style='display:flex;flex-wrap:wrap;gap:10px;margin:14px 0;'>"
    ]
    for idx, image in enumerate(images, 1):
        src = image.get("src") or image.get("data_uri", "")
        filename = image.get("filename", f"image-{idx}")
        parts.append(
            "<figure style='margin:0;flex:1 1 220px;max-width:100%;'>"
            f"<img src='{e(src)}' alt='원문 이미지' "
            "loading='lazy' decoding='async' "
            "style='max-width:100%;height:auto;border-radius:8px;"
            "border:1px solid rgba(148,163,184,.35);background:#fff;' />"
            f"<figcaption style='font-size:11px;color:#94a3b8;margin-top:4px;'>{e(label)} {idx} · {e(filename)}</figcaption>"
            "</figure>"
        )
    parts.append("</div>")
    return "\n".join(parts)


def render_choices(q: dict) -> str:
    choices = q.get("choices") or []
    choice_images = q.get("choice_images") or []
    if not choices:
        return "<p style='color:#f97316;font-weight:700;'>선지 확인 필요</p>"

    parts = [
        "<ol style='margin:14px 0 0 1.25rem;padding:0;line-height:1.62;'>"
    ]
    for idx, choice in enumerate(choices, 1):
        parts.append("<li style='margin:7px 0;padding-left:4px;'>")
        parts.append(e(choice))
        if idx - 1 < len(choice_images) and choice_images[idx - 1]:
            parts.append(render_images(choice_images[idx - 1], f"선지 {idx} 이미지"))
        parts.append("</li>")
    parts.append("</ol>")
    return "\n".join(parts)


def make_front(q: dict) -> str:
    no = q.get("original_no")
    category = CATEGORY_LABELS.get(q.get("category"), q.get("category", ""))
    return "\n".join(
        [
            "<div style='display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;'>",
            f"<span style='font-size:12px;font-weight:800;color:#bfdbfe;'>원문 {e(no)}</span>",
            f"<span style='font-size:12px;color:#cbd5e1;'>seq {e(q.get('seq'))}</span>",
            f"<span style='font-size:12px;color:#cbd5e1;'>{e(category)}</span>",
            "</div>",
            f"<div style='font-size:1rem;line-height:1.68;font-weight:700;color:#f8fafc;'>{paragraph_html(q.get('stem'))}</div>",
            render_images(q.get("images") or [], "문항 이미지"),
            render_choices(q),
        ]
    )


def make_answer(q: dict) -> str:
    no = int(q.get("original_no") or 0)
    answer_index = q.get("answer_index")
    answer_text = q.get("answer_text") or "정답 매핑 확인 필요"
    note = MANUAL_NOTES.get(no)

    parts = [
        "<div style='display:grid;gap:12px;'>",
        "<section style='background:#ecfdf5;border:1px solid #86efac;border-radius:10px;padding:12px 14px;color:#064e3b;'>",
        f"<div style='font-weight:900;margin-bottom:4px;'>정답: {e(answer_index)}. {e(answer_text)}</div>",
        f"<div style='font-size:12px;'>원문 번호 {e(no)} · PDF page {e(q.get('pdf_page'))}</div>",
        "</section>",
    ]

    if note:
        parts.extend(
            [
                "<section style='background:#fff7ed;border:1px solid #fdba74;border-radius:10px;padding:10px 12px;color:#7c2d12;'>",
                f"<strong>수동 보정 note</strong><br>{e(note)}",
                "</section>",
            ]
        )

    parts.extend(
        [
            "<section style='background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;color:#111827;'>",
            "<h4 style='margin:0 0 8px;font-size:0.98rem;'>원해설</h4>",
            paragraph_html(q.get("explanation_raw")),
            "</section>",
            "</div>",
        ]
    )
    return "\n".join(parts)


def make_guide(q: dict) -> str:
    no = int(q.get("original_no") or 0)
    note = MANUAL_NOTES.get(no, "자동 추출 정답 매핑.")
    tags = ", ".join(q.get("tags") or [])
    return "\n".join(
        [
            "<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:12px;color:#0f172a;'>",
            "<h4 style='margin:0 0 8px;'>Source / QC</h4>",
            f"<p style='margin:6px 0;'><strong>builder:</strong> anki_quiz_builder.py + rail mode</p>",
            f"<p style='margin:6px 0;'><strong>source:</strong> PK_시험문제_100.docx / PK_시험문제_100_정답해설_일부수정.pdf</p>",
            f"<p style='margin:6px 0;'><strong>status:</strong> {e(note)}</p>",
            f"<p style='margin:6px 0;'><strong>tags:</strong> {e(tags)}</p>",
            "</div>",
        ]
    )


def load_questions() -> list[dict]:
    questions = json.loads(DATA.read_text(encoding="utf-8"))
    questions.sort(key=lambda item: (int(item.get("seq") or 0), int(item.get("original_no") or 0)))
    return questions


def build_cards(questions: list[dict]) -> list[dict]:
    cards = []
    for q in questions:
        no = int(q.get("original_no") or q.get("seq") or 0)
        cards.append(
            {
                "id": q["id"],
                "num": no,
                "q": make_front(q),
                "a": make_answer(q),
                "g": make_guide(q),
            }
        )
    return cards


def validate_source(questions: list[dict]) -> None:
    nums = [int(q["original_no"]) for q in questions]
    missing = [n for n in range(min(nums), max(nums) + 1) if n not in nums]
    image_count = sum(len(q.get("images") or []) for q in questions)
    choice_image_count = sum(
        sum(len(group or []) for group in (q.get("choice_images") or []))
        for q in questions
    )

    checks = {
        "question_count": len(questions) == 81,
        "number_range": (min(nums), max(nums)) == (1, 87),
        "missing_numbers": missing == [25, 26, 27, 28, 29, 30],
        "answer_mapping": all(q.get("answer_index") and q.get("answer_text") for q in questions),
        "image_count": image_count + choice_image_count == 103,
        "unique_ids": len({q["id"] for q in questions}) == len(questions),
    }
    for q in questions:
        for image in q.get("images") or []:
            if not (image.get("src") or image.get("data_uri")):
                checks[f"image_src_q{q.get('original_no')}"] = False
        for group in q.get("choice_images") or []:
            for image in group or []:
                if not (image.get("src") or image.get("data_uri")):
                    checks[f"choice_image_src_q{q.get('original_no')}"] = False
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"Source validation failed: {failed}")


def main() -> None:
    questions = load_questions()
    validate_source(questions)
    cards = build_cards(questions)

    rail_report = run_rails(cards, mode="pretest", strict=False)
    rail_report.print_report()
    if rail_report.has_errors:
        raise SystemExit("Rail errors present; aborting build.")

    builder = QuizBuilder(
        cards=cards,
        title=TITLE,
        storage_prefix=STORAGE_PREFIX,
        subtitle=LOCK_LINE,
        enable_self_answer=False,
        randomize_review=False,
        enable_rail=True,
        rail_mode="pretest",
        rail_strict=False,
    )
    builder.write(str(OUT))
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Cards: {len(cards)}")


if __name__ == "__main__":
    main()
