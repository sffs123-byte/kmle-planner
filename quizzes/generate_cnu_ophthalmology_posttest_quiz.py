#!/usr/bin/env python3
"""Build the CNU ophthalmology post-test Anki deck.

Source inventory
----------------
- 2021 original 25-axis exam
- 2025 HI / yama / recall variants
- 2026 group 1 (04-17), group 2 (04-24), group 3 (05-01) recalls

The recalls are not an official question paper or answer key. Cards carrying
uncertain=true keep that uncertainty visible on the answer side.
This generator and the JSON data file are the source of truth for the
published standalone HTML.
"""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path

from anki_quiz_builder import QuizBuilder, run_rails
from anki_backup_restore import inject_backup_restore


ROOT = Path(__file__).resolve().parent.parent
QUIZ_DIR = ROOT / "quizzes"
DATA_PATH = QUIZ_DIR / "data" / "cnu_ophthalmology_posttest_anki_cards.json"
EXPLANATIONS_PATH = QUIZ_DIR / "data" / "cnu_ophthalmology_posttest_anki_explanations.json"
OUT_PATH = QUIZ_DIR / "충남대_안과_포테_기출_Anki.html"
QC_PATH = QUIZ_DIR / "qc_cnu_ophthalmology_posttest_anki.json"

TITLE = "충남대 안과 포테 기출 Anki · 2021–2026 · 49카드"
STORAGE_PREFIX = "cnu_ophthalmology_posttest_anki_20260818_v1"
EXPECTED_CARD_COUNT = 49
EXPECTED_TREND_COUNT = 0
EXPECTED_UNCERTAIN_COUNT = 7
EXPECTED_AXES = list(range(1, 26))
EXPECTED_LIMITED_IDS = {"q05b", "q10c", "q15c", "q18c", "q19b", "q25d", "qx01"}
IMAGE_STATUSES = {"exact", "teaching-reference", "missing"}


def e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def paragraphs(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return "".join(
        f"<p style='margin:7px 0;line-height:1.72;'>{e(block).replace(chr(10), '<br>')}</p>"
        for block in re.split(r"\n\s*\n", text)
        if block.strip()
    )


def badge(label: str, color: str, background: str) -> str:
    return (
        "<span style='display:inline-flex;align-items:center;border-radius:999px;"
        f"padding:3px 9px;font-size:11px;font-weight:850;color:{color};"
        f"background:{background};'>{e(label)}</span>"
    )


def status_badge(card: dict) -> str:
    if card.get("uncertain"):
        return badge(card["status"], "#9a3412", "#ffedd5")
    if card["kind"] == "trend":
        return badge("출제 흐름", "#5b21b6", "#ede9fe")
    if card["kind"] in {"variant", "correction"}:
        return badge(card["status"], "#1d4ed8", "#dbeafe")
    return badge(card["status"], "#166534", "#dcfce7")


def axis_badge(card: dict) -> str:
    axes = card.get("axes") or []
    if not axes:
        return badge("전체 경향", "#334155", "#e2e8f0")
    label = "축 " + "·".join(str(axis) for axis in axes)
    return badge(label, "#0f766e", "#ccfbf1")


def render_choices(card: dict) -> str:
    choices = card.get("choices") or []
    if not choices:
        return ""
    items = "".join(
        f"<li style='margin:8px 0;padding-left:4px;line-height:1.62;'>{e(choice)}</li>"
        for choice in choices
    )
    return (
        "<ol style='margin:14px 0 0 1.3rem;padding:0;color:#e2e8f0;'>"
        f"{items}</ol>"
    )


def render_images(images: list[dict], *, surface: str) -> str:
    if not images:
        return ""
    cards = []
    for item in images:
        image_status = item["status"]
        if image_status == "missing":
            cards.append(
                "<figure style='margin:0;padding:14px;border-radius:12px;"
                "border:1px dashed #fb923c;background:rgba(124,45,18,.18);color:#fed7aa;'>"
                f"{badge('원문 미확보', '#9a3412', '#ffedd5')}"
                "<div style='margin-top:9px;font-size:13px;font-weight:760;line-height:1.6;'>"
                f"{e(item['caption'])}</div></figure>"
            )
            continue
        if image_status == "exact":
            status = badge("충남대 출제자료", "#166534", "#dcfce7")
        else:
            status = badge("시험 원본 아님", "#9a3412", "#ffedd5")
        cards.append(
            "<figure style='margin:0;padding:9px;border-radius:12px;border:1px solid "
            + ("rgba(147,197,253,.42);background:rgba(15,23,42,.42);" if surface == "front" else "#dbeafe;background:#f8fafc;")
            + "'>"
            f"<img src='{e(item['src'])}' alt='{e(item['alt'])}' loading='lazy' decoding='async' "
            "style='display:block;width:100%;max-height:430px;object-fit:contain;border-radius:8px;background:#020617;'>"
            "<figcaption style='display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:8px;"
            + ("color:#cbd5e1;" if surface == "front" else "color:#334155;")
            + "font-size:11px;line-height:1.5;'>"
            f"{status}<span>{e(item['caption'])}</span></figcaption></figure>"
        )
    return (
        "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));"
        f"gap:10px;margin-top:14px;'>{''.join(cards)}</div>"
    )


def make_front(card: dict) -> str:
    alert = ""
    if card.get("uncertain"):
        alert = (
            "<div style='margin:10px 0 0;padding:8px 10px;border-radius:8px;"
            "background:rgba(251,146,60,.13);border:1px solid rgba(251,146,60,.45);"
            "color:#fed7aa;font-size:12px;font-weight:750;'>"
            "⚠️ 불완전 학생 복기 — 정답을 추측하지 말고 답면의 한계를 확인하세요."
            "</div>"
        )
    return "".join(
        [
            "<div style='display:flex;gap:6px;flex-wrap:wrap;margin-bottom:11px;'>",
            status_badge(card),
            axis_badge(card),
            "</div>",
            f"<div style='font-size:1rem;line-height:1.72;font-weight:780;color:#f8fafc;'>{e(card['q'])}</div>",
            render_choices(card),
            render_images(card.get("front_images") or [], surface="front"),
            alert,
        ]
    )


def text_section(title: str, body: object, *, background: str, border: str, color: str) -> str:
    if isinstance(body, list):
        content = "<ul style='margin:0;padding-left:1.15rem;'>" + "".join(
            f"<li style='margin:6px 0;line-height:1.68;'>{e(item)}</li>" for item in body
        ) + "</ul>"
    else:
        content = paragraphs(body)
    return (
        f"<section style='background:{background};border:1px solid {border};border-radius:10px;"
        f"padding:11px 13px;color:{color};'>"
        f"<h4 style='margin:0 0 6px;'>{e(title)}</h4>{content}</section>"
    )


def make_answer(card: dict) -> str:
    warning_style = (
        "background:#fff7ed;border:1px solid #fdba74;color:#7c2d12;"
        if card.get("uncertain")
        else "background:#ecfdf5;border:1px solid #86efac;color:#064e3b;"
    )
    return "".join(
        [
            "<div style='display:grid;gap:11px;'>",
            f"<section style='{warning_style}border-radius:10px;padding:12px 14px;'>",
            "<div style='font-size:12px;font-weight:850;margin-bottom:5px;'>",
            "정답·판정" if not card.get("uncertain") else "불확실성 포함 판정",
            "</div>",
            f"<div style='font-size:15px;font-weight:900;line-height:1.7;'>{e(card['a'])}</div>",
            "</section>",
            text_section("왜 맞나", card["why_correct"], background="#ffffff", border="#e5e7eb", color="#111827"),
            text_section("오답 함정", card["distractors"], background="#fff7ed", border="#fdba74", color="#7c2d12"),
            text_section("출제 변형", card["variants"], background="#eff6ff", border="#93c5fd", color="#1e3a8a"),
            text_section("교과서 근거", card["evidence"], background="#f8fafc", border="#cbd5e1", color="#334155"),
            text_section("3초 암기문장", card["lock"], background="#f0fdf4", border="#86efac", color="#14532d"),
            (
                text_section("원문 한계", card["limitation"], background="#fff7ed", border="#fb923c", color="#9a3412")
                if card.get("limitation") else ""
            ),
            render_images(card.get("answer_images") or [], surface="answer"),
            "</div>",
        ]
    )


def make_guide(card: dict) -> str:
    sources = " · ".join(card.get("sources") or ["출처 표기 없음"])
    axes = ", ".join(str(axis) for axis in card.get("axes") or []) or "전체 경향"
    return "".join(
        [
            "<div style='line-height:1.72;color:#0f172a;'>",
            "<h4 style='margin:0 0 8px;'>Source / QC</h4>",
            f"<p style='margin:6px 0;'><b>출처:</b> {e(sources)}</p>",
            f"<p style='margin:6px 0;'><b>반복축:</b> {e(axes)}</p>",
            f"<p style='margin:6px 0;'><b>신뢰표시:</b> {e(card['status'])}</p>",
            "<p style='margin:8px 0 0;color:#475569;font-size:12px;'>"
            "학생 복기 기반이며 실습 주 최신 PPT·공식 안내가 최종 우선입니다.</p>",
            "</div>",
        ]
    )


def load_source() -> tuple[dict, list[dict], dict[str, dict]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    explanations = json.loads(EXPLANATIONS_PATH.read_text(encoding="utf-8"))
    return payload["meta"], payload["cards"], explanations


def validate_source(meta: dict, cards: list[dict], explanations: dict[str, dict]) -> dict:
    ids = [card["id"] for card in cards]
    axes = sorted({axis for card in cards for axis in card.get("axes", [])})
    kind_counts = Counter(card["kind"] for card in cards)
    status_counts = Counter(card["status"] for card in cards)
    uncertain_cards = [card for card in cards if card.get("uncertain")]
    explanation_fields = ("why_correct", "distractors", "variants", "evidence", "lock")
    image_items = [
        item
        for explanation in explanations.values()
        for field in ("front_images", "answer_images")
        for item in explanation.get(field, [])
    ]
    asset_items = [item for item in image_items if item.get("status") != "missing"]
    missing_items = [item for item in image_items if item.get("status") == "missing"]
    private_path_pattern = re.compile(r"(?:/Users/|\.openclaw|Dropbox|sffs123gmail)")

    checks = {
        "card_count": len(cards) == EXPECTED_CARD_COUNT,
        "unique_ids": len(ids) == len(set(ids)),
        "trend_count": kind_counts["trend"] == EXPECTED_TREND_COUNT,
        "uncertain_count": len(uncertain_cards) == EXPECTED_UNCERTAIN_COUNT,
        "uncertain_marker": all("원문 확인 필요" in card["a"] for card in uncertain_cards),
        "axes_1_to_25": axes == EXPECTED_AXES,
        "official_key_flag": meta.get("official_answer_key") is False,
        "required_fields": all(
            all(str(card.get(field, "")).strip() for field in ("id", "num", "kind", "status", "q", "a", "why", "trend"))
            for card in cards
        ),
        "explanation_id_match": set(explanations) == set(ids),
        "six_section_fields": all(
            all(explanations.get(card_id, {}).get(field) for field in explanation_fields)
            for card_id in ids
        ),
        "distractors_are_lists": all(isinstance(explanations[card_id]["distractors"], list) for card_id in ids),
        "evidence_are_lists": all(isinstance(explanations[card_id]["evidence"], list) for card_id in ids),
        "limited_ids_exact": {card_id for card_id, value in explanations.items() if value.get("limitation")} == EXPECTED_LIMITED_IDS,
        "image_statuses_valid": all(item.get("status") in IMAGE_STATUSES for item in image_items),
        "image_metadata_complete": all(
            item.get("caption") and (
                item.get("status") == "missing" or (item.get("src") and item.get("alt"))
            ) for item in image_items
        ),
        "image_assets_exist": all((QUIZ_DIR / item["src"]).is_file() for item in asset_items),
        "missing_original_panels": len(missing_items) == 4,
        "no_private_paths": not private_path_pattern.search(json.dumps(cards, ensure_ascii=False)),
        "no_private_paths_in_explanations": not private_path_pattern.search(json.dumps(explanations, ensure_ascii=False)),
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"Source validation failed: {failed}")

    return {
        "checks": checks,
        "card_count": len(cards),
        "question_variant_correction_count": len(cards) - kind_counts["trend"],
        "kind_counts": dict(kind_counts),
        "status_counts": dict(status_counts),
        "uncertain_count": len(uncertain_cards),
        "axes": axes,
        "explanations": {
            "complete": len(explanations),
            "limited": len(EXPECTED_LIMITED_IDS),
            "image_assets": len({item["src"] for item in asset_items}),
            "exact_image_placements": sum(item["status"] == "exact" for item in asset_items),
            "teaching_reference_placements": sum(item["status"] == "teaching-reference" for item in asset_items),
            "missing_original_panels": len(missing_items),
        },
    }


def build_cards(source_cards: list[dict], explanations: dict[str, dict]) -> list[dict]:
    merged_cards = []
    for source_card in source_cards:
        card = {**source_card, **explanations[source_card["id"]]}
        merged_cards.append(card)
    return [
        {
            "id": card["id"],
            "num": card["num"],
            "q": make_front(card),
            "a": make_answer(card),
            "g": make_guide(card),
            "uncertain": bool(card.get("uncertain")),
        }
        for card in merged_cards
    ]


def decorate_html(html_text: str) -> str:
    title_marker = "</title>"
    if html_text.count(title_marker) != 1:
        raise SystemExit("Favicon injection marker mismatch")
    html_text = html_text.replace(
        title_marker,
        '</title>\n<link rel="icon" href="../assets/icons/favicon.svg">',
        1,
    )

    quiz_num_marker = '<span class="card-num">Q${data.num}</span>'
    if html_text.count(quiz_num_marker) != 1:
        raise SystemExit("Quiz number injection marker mismatch")
    html_text = html_text.replace(
        quiz_num_marker,
        '<span class="card-num">${data.num}</span>',
        1,
    )

    grid_marker = '<div class="card-grid">'
    banner = """<div style="margin:0 0 14px;padding:14px 16px;border-radius:12px;
background:linear-gradient(135deg,rgba(30,64,175,.24),rgba(124,58,237,.18));
border:1px solid rgba(147,197,253,.35);color:#dbeafe;line-height:1.65;">
<b>49카드</b> · 전 카드 6단계 해설 · 이미지 자산 22개 · 불확실 복기 7<br>
<span style="font-size:12px;color:#bfdbfe;">순서대로 첫 공부 · due 카드 우선 랜덤 실전 · 원문 미확보/시험 원본 아님 표시 · 최신 실습 주 사진/PPT 우선</span>
</div>
<div class="card-grid">"""
    if html_text.count(grid_marker) != 1:
        raise SystemExit("Banner injection marker mismatch")
    html_text = html_text.replace(grid_marker, banner, 1)
    return inject_backup_restore(
        html_text,
        site_id="cnu-ophthalmology-posttest-anki",
        download_prefix="충남대_안과_Anki_수정본",
    )


def validate_generated(html_text: str, cards: list[dict], qc: dict) -> dict:
    checks = {
        "quiz_data_present": "const QUIZ_DATA" in html_text,
        "all_ids_present": "const ALL_IDS" in html_text,
        "storage_prefix_present": STORAGE_PREFIX in html_text,
        "ordered_mode_present": "순서대로 시작" in html_text,
        "random_mode_present": "랜덤 시작" in html_text,
        "order_mode_enabled": "const ENABLE_ORDER_MODES = true" in html_text,
        "mode_and_remaining_badges": all(token in html_text for token in ("quizOrderModeBadge", "quizRemainingBadge")),
        "due_priority_random": "shuffledCopy(plan.dueIds)" in html_text,
        "session_order_restore": "orderMode: saved.orderMode || 'ordered'" in html_text,
        "backup_restore_present": all(token in html_text for token in ("BACKUP_RESTORE_V1", "btnExportBackup", "btnImportBackup")),
        "trend_cards_removed": all(f'trend0{number}' not in html_text for number in range(1, 9)),
        "updated_card_count_visible": "<b>49카드</b>" in html_text,
        "favicon_present": '../assets/icons/favicon.svg' in html_text,
        "quiz_number_not_double_prefixed": '<span class="card-num">Q${data.num}</span>' not in html_text,
        "card_id_count": sum(f'"{card["id"]}"' in html_text for card in cards) == len(cards),
        "uncertainty_visible": html_text.count("원문 확인 필요") >= EXPECTED_UNCERTAIN_COUNT,
        "six_sections_visible": all(
            html_text.count(title) >= len(cards)
            for title in ("왜 맞나", "오답 함정", "출제 변형", "교과서 근거", "3초 암기문장")
        ),
        "image_asset_references": html_text.count("assets/cnu_ophthalmology_posttest/") >= 22,
        "missing_original_visible": html_text.count("원문 미확보") >= 4,
        "teaching_reference_visible": "시험 원본 아님" in html_text,
        "medical_correction_visible": "정립·가상상" in html_text,
        "removed_wrong_claim": "상이 반대로 맺힌다. (맞음)" not in html_text,
        "no_private_paths": all(token not in html_text for token in ("/Users/", ".openclaw", "sffs123gmail")),
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"Generated HTML validation failed: {failed}")
    qc["generated_checks"] = checks
    return qc


def main() -> None:
    meta, source_cards, explanations = load_source()
    qc = validate_source(meta, source_cards, explanations)
    cards = build_cards(source_cards, explanations)

    rail_report = run_rails(cards, mode="pretest", strict=False)
    rail_report.print_report()
    if rail_report.has_errors:
        raise SystemExit("Rail errors present; aborting build")

    builder = QuizBuilder(
        cards=cards,
        title=TITLE,
        storage_prefix=STORAGE_PREFIX,
        subtitle="25축 전수 · 2026 1·2·3조 실제 문제와 변형",
        enable_self_answer=True,
        randomize_review=False,
        enable_order_modes=True,
        enable_rail=True,
        rail_mode="pretest",
        rail_strict=False,
    )
    html_text = decorate_html(builder.build())
    html_text = "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"
    qc = validate_generated(html_text, cards, qc)
    OUT_PATH.write_text(html_text, encoding="utf-8")

    qc["rail"] = {
        "cards_checked": rail_report.cards_checked,
        "errors": len(rail_report.errors),
        "warnings": len(rail_report.warnings),
        "auto_fixes": rail_report.auto_fixes,
    }
    qc["output"] = {
        "path": str(OUT_PATH.relative_to(ROOT)),
        "bytes": OUT_PATH.stat().st_size,
        "storage_prefix": STORAGE_PREFIX,
    }
    QC_PATH.write_text(json.dumps(qc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(qc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
