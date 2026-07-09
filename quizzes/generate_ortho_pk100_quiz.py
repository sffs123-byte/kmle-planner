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
    19: "수정 PDF의 빨간 표시/메모 기준으로 5번 흉추 전만으로 보정함.",
    22: "정답은 수정 PDF 시각 하이라이트 기준으로 수동 보정함.",
    23: "정답은 원본 PDF 시각 하이라이트 기준으로 수동 보정함.",
    31: "정답은 수정 PDF 시각 하이라이트 기준으로 수동 보정함.",
    72: "정답은 수정 PDF 시각 하이라이트 기준으로 수동 보정함.",
    82: "두 해설 PDF 모두 정답 하이라이트가 없어 Thomas test 문항으로 보고 1번으로 보정함.",
}

IMAGE_RECHECK_NOTES = {
    1: "A에서는 새끼손가락 끝마디가 잘 굽지 않는다. B의 CT에서는 손목 새끼손가락 쪽 작은 갈고리뼈 조각이 떨어져 있어, 그 옆을 지나던 굽힘힘줄이 오래 쓸려 끊어진 상황으로 읽는다.",
    2: "A는 손목은 들 수 있는데 손가락만 축 처진 모습이다. B에서는 팔꿈치 바깥쪽 신경길 중 supinator 근육을 통과하는 좁은 터널, 즉 빨간 선 '다' 부위에서 끼인 것으로 보면 된다.",
    3: "MRI에서 손목 새끼손가락 쪽 받침판인 TFCC가 붙어 있어야 할 깊은 자리에서 들떠 보인다. 관절경에서는 탐침으로 누르면 탄탄한 막이 아니라 축 늘어진 막처럼 밀려 올라가므로 fovea 봉합이 필요하다고 읽는다.",
    4: "A에서는 주상골이 오래 붙지 않은 골절처럼 보이고, B에서는 몸쪽 조각이 어둡고 죽은 뼈처럼 보인다. 뼈를 붙이는 것만으로는 부족해서 피가 통하는 뼈 조각을 붙여야 한다.",
    5: "정복 전에는 손목뼈 배열이 한 번 크게 흐트러져 있다. 정복 후에는 튀어나온 뼈가 어느 정도 들어갔지만, 엄지쪽 주상골과 가운데 월상골 사이 틈이 계속 벌어져 있어 둘을 묶는 인대까지 찢어진 것으로 읽는다.",
    6: "사진은 약지 손가락이 펴지지 않고 굽은 상태다. 손바닥 안쪽의 끈 같은 조직이 짧아진 Dupuytren 변형이며, PIP 관절까지 굽히는 데 가장 크게 관여하는 끈은 spiral cord다.",
    7: "엄지 밑 두툼한 살이 꺼져 있고 엄지를 맞은편 손가락으로 가져가는 동작이 안 된다. 눌린 신경을 풀어주는 것만으로는 이미 약해진 엄지 기능이 돌아오기 어려워 힘줄을 옮겨 보강한다.",
    8: "손목 가운데의 월상골이 주변 뼈보다 하얗고 납작하게 찌그러져 있다. 다만 손목 전체 관절이 다 망가진 단계는 아니므로 전유합까지 가지 않고 부분 유합을 선택한다.",
    9: "MRI는 손가락 힘줄을 싸는 통로가 길게 두꺼워진 모습이고, 수술사진에는 밥알처럼 작은 흰 덩어리들이 많이 보인다. 만성 경과와 이 rice body 조합은 결핵성 건활액막염 쪽으로 읽는다.",
    10: "초음파에서는 손끝의 아주 작은 덩어리에 혈류가 많이 보이고, 수술사진에서도 손톱 아래/손끝의 작은 종물이 확인된다. '한 점을 누르면 찌르는 듯 아픔'과 혈관성 종물이라 사구종이다.",
    11: "MRI에는 회전근개가 크게 찢어진 소견이 있지만, C 사진에서 환자가 팔을 머리 위로 직접 올릴 수 있다. 즉 그림이 심해 보여도 기능이 남아 있어 바로 큰 수술로 가지 않는다.",
    12: "상완골 머리 주변이 여러 조각으로 부서진 사분골절 탈구다. 치환술 뒤에는 인공관절 자체보다 회전근개가 붙는 대결절/소결절 조각이 잘 붙느냐가 팔 올리는 기능을 좌우한다.",
    13: "CT/MRI에서 어깨 소켓의 앞쪽 뼈가 깎여 있고, 상완골 머리에도 반복 탈구로 생긴 움푹 팬 자국이 보인다. 격투기 선수의 반복 탈구라 단순 봉합보다 뼈 블록을 보태는 Latarjet가 맞다.",
    14: "탐촉자를 어깨 위쪽에서 힘줄 진행 방향과 나란히 댄 장축 영상이다. 정상이라면 매끈한 회색 힘줄띠가 보여야 하는데 중간이 검게 끊겨 있어 극상건 파열로 읽는다.",
    15: "팔꿈치 바깥쪽에서 상완골 소두와 요골두가 맞닿는 부위에 골연골 결손이 보인다. 투구 동작 때 바깥쪽이 반복 압박되고 팔꿈치가 굽는 힘이 겹쳐 생긴 손상으로 본다.",
    16: "L1 척추뼈 앞부분이 쐐기처럼 눌려 있지만 뒤쪽 벽과 신경길은 크게 무너지지 않았다. 다리 마비 같은 신경증상이 없으므로 수술보다 보조기로 버티며 붙이는 상황이다.",
    17: "검은 점은 L4-5 디스크가 뒤가쪽으로 나온 위치다. 이 위치에서는 지나가는 L4가 아니라 아래로 내려가던 L5 신경뿌리를 누르므로, L5가 맡는 중둔근 약화가 나온다.",
    18: "수술 전후 사진에서 목뼈 압박은 풀렸는데, 수술 며칠 뒤 어깨 벌림 힘만 떨어졌다. 어깨 벌림은 주로 C5 신경근이 담당하므로 경추 수술 후 C5 palsy로 읽는다.",
    19: "앞사진의 35도 휘어짐은 보통 수술 기준으로 보기에는 크기가 애매하다. 옆사진에서는 등뼈가 정상처럼 뒤로 둥글지 않고 앞쪽으로 꺾인 흉추 전만 표시가 있어, 수정 PDF 기준 정답은 이 변형 소견이다.",
    20: "영상은 목뼈가 다치며 척수 앞쪽이 눌린 상황이다. 운동, 통증, 온도는 앞쪽 척수길이 담당하고 진동/위치감각은 뒤쪽 길이 담당하므로, 앞쪽 손상만 설명하는 전방 척수 증후군이다.",
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
    image_recheck = IMAGE_RECHECK_NOTES.get(no)

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

    if image_recheck:
        parts.extend(
            [
                "<section style='background:#eff6ff;border:1px solid #93c5fd;border-radius:10px;padding:10px 12px;color:#1e3a8a;'>",
                "<strong>이미지 읽는 법</strong><br>",
                f"{e(image_recheck)}",
                "</section>",
            ]
        )

    parts.extend(
        [
            "<section style='background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;color:#111827;'>",
            "<h4 style='margin:0 0 8px;font-size:0.98rem;'>해설</h4>",
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
