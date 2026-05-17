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

HI_STUDY_CSS = r"""
body.peds-pretest2-full-bg .hi-study-panel { margin:0 auto 18px; max-width:1100px; padding:20px 18px; border-radius:22px; background:rgba(2,6,23,.78); border:1px solid rgba(167,139,250,.34); box-shadow:0 18px 44px rgba(2,6,23,.24); }
body.peds-pretest2-full-bg .hi-study-head { display:flex; justify-content:space-between; align-items:flex-start; gap:14px; flex-wrap:wrap; }
body.peds-pretest2-full-bg .hi-study-kicker { display:inline-flex; padding:4px 10px; border-radius:999px; background:rgba(127,29,29,.38); border:1px solid rgba(252,165,165,.42); color:#fecaca; font-size:12px; font-weight:950; letter-spacing:.04em; }
body.peds-pretest2-full-bg .hi-study-panel h2 { margin:10px 0 6px; color:#f8fafc; font-size:24px; line-height:1.22; }
body.peds-pretest2-full-bg .hi-study-panel p { color:#cbd5e1; line-height:1.58; }
body.peds-pretest2-full-bg .hi-study-stats { color:#bfdbfe; font-size:12px; font-weight:850; }
body.peds-pretest2-full-bg .hi-study-toolbar { display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin:14px 0; }
body.peds-pretest2-full-bg .hi-study-search { flex:1; min-width:220px; border-radius:12px; border:1px solid rgba(191,219,254,.28); background:rgba(15,23,42,.88); color:#e5e7eb; padding:10px 12px; font-weight:800; }
body.peds-pretest2-full-bg .hi-study-chip { border:1px solid rgba(219,234,254,.28); background:rgba(30,41,59,.9); color:#e2e8f0; border-radius:999px; padding:7px 11px; font-size:12px; font-weight:900; cursor:pointer; }
body.peds-pretest2-full-bg .hi-study-chip.active { background:#7c3aed; color:#fff; border-color:#ddd6fe; }
body.peds-pretest2-full-bg .hi-study-layout { display:grid; grid-template-columns:minmax(220px,320px) minmax(0,1fr); gap:14px; align-items:start; }
body.peds-pretest2-full-bg .hi-study-list { display:flex; flex-direction:column; gap:7px; max-height:620px; overflow:auto; padding-right:4px; }
body.peds-pretest2-full-bg .hi-study-part { border:1px solid rgba(148,163,184,.28); background:rgba(15,23,42,.76); color:#e5e7eb; border-radius:14px; padding:10px 11px; text-align:left; cursor:pointer; }
body.peds-pretest2-full-bg .hi-study-part.active { border-color:#c4b5fd; background:rgba(88,28,135,.62); }
body.peds-pretest2-full-bg .hi-study-part-title { font-weight:950; line-height:1.35; }
body.peds-pretest2-full-bg .hi-study-part-meta { margin-top:5px; color:#bfdbfe; font-size:11px; font-weight:850; }
body.peds-pretest2-full-bg .hi-study-detail { min-height:360px; border-radius:18px; background:rgba(248,250,252,.98); color:#0f172a; padding:18px; box-shadow:0 14px 34px rgba(2,6,23,.22); }
body.peds-pretest2-full-bg .hi-study-detail h3 { margin:0 0 6px; font-size:24px; color:#111827; }
body.peds-pretest2-full-bg .hi-study-detail h4 { margin:16px 0 8px; color:#581c87; font-size:15px; }
body.peds-pretest2-full-bg .hi-study-detail ul, body.peds-pretest2-full-bg .hi-study-detail ol { margin:6px 0 12px; padding-left:20px; }
body.peds-pretest2-full-bg .hi-study-detail li { margin:6px 0; line-height:1.6; }
body.peds-pretest2-full-bg .hi-study-detail .hi-lock { border-left:4px solid #16a34a; background:#f0fdf4; border-radius:10px; padding:10px 12px; margin:8px 0; font-weight:900; color:#14532d; }
body.peds-pretest2-full-bg .hi-study-actions { display:flex; flex-wrap:wrap; gap:8px; margin:14px 0 4px; }
body.peds-pretest2-full-bg .hi-study-actions button { border:none; border-radius:12px; padding:10px 12px; font-weight:950; cursor:pointer; }
body.peds-pretest2-full-bg .hi-study-primary { background:#7c3aed; color:#fff; }
body.peds-pretest2-full-bg .hi-study-secondary { background:#e0f2fe; color:#075985; }
body.peds-pretest2-full-bg .hi-card-mini { border:1px solid #e2e8f0; background:#f8fafc; border-radius:12px; padding:10px 12px; margin:8px 0; }
body.peds-pretest2-full-bg .hi-card-mini code { color:#7c2d12; font-weight:900; }
@media (max-width:768px) { body.peds-pretest2-full-bg .hi-study-layout { grid-template-columns:1fr; } body.peds-pretest2-full-bg .hi-study-list { max-height:260px; } body.peds-pretest2-full-bg .hi-study-detail { padding:14px; } }
"""

# Manual QC fixes for cases where recall/source-variant metadata was being
# exposed as the question stem, or low-confidence neighboring images were
# attached to the wrong card. Keep these local and explicit: the FULL deck is
# source-faithful, but the learner-facing front must still be an actual quiz
# prompt, not a harvest note such as "거의 동일한 지문...".
CURATED_NON_HI_IMAGE_EXCLUDES = {
    ("PEDS2-2025-11to14-Q7", "non_hi_qimg_041"),  # steeple sign image belongs to Q6 croup, not double-bubble Q7
    ("PEDS2-2023-25to28-Q4", "non_hi_qimg_012"),  # constipation/hematochezia colonoscopy image, not C. difficile colitis
    ("PEDS2-2026-5to8-Q8", "non_hi_qimg_043"),    # cellulitis image, not acute otitis media
    ("PEDS2-2023-33to36-SA3", "non_hi_qimg_011"), # anaphylaxis/cellulitis notes, not PSVT ECG
    ("PEDS2-2023-33to36-SA3", "non_hi_qimg_016"),
}

# These are front-safe original problem images, not answer-only source crops.
# They should appear before answer reveal because the visual finding is part
# of the question stem.
CURATED_FRONT_IMAGE_EXACT = {
    ("PEDS2-2025-19to23-Q1", "non_hi_qimg_037"),  # infectious mononucleosis/PBS source image
    ("PEDS2-2025-11to14-Q6", "non_hi_qimg_041"),  # croup steeple sign
}

CURATED_ANSWER_ONLY_IMAGES = {
    ("PEDS2-2025-15to18-Q1", "non_hi_qimg_038"),  # original capture has checked/circled answer
}

# Embedded HI images are front-visible by default only when they are clean
# diagnostic material (CXR/ECG/US/lesion photo). These embedded pages contain
# diagnosis/treatment tables, labeled murmur diagrams, or annotated teaching
# ECG images, so they must stay behind answer reveal.
EMBEDDED_ANSWER_ONLY_FILENAMES = {
    "hi2_pdfimg_10_p05L.jpg",  # pediatric TB comparison/treatment table
    "hi2_pdfimg_16_p10R.jpg",  # URI/otitis teaching table, not an otoscopy photo
    "hi2_pdfimg_20_p13R.jpg",  # labeled cardiac lesion/murmur diagram
    "hi2_pdfimg_21_p13R.jpg",  # labeled innocent murmur diagram
    "hi2_pdfimg_22_p14L.jpg",  # annotated pediatric ECG teaching chart
    "hi2_pdfimg_23_p14L.jpg",  # annotated ECG crop; clean rhythm strip is pdfimg_24
}

CURATED_HI_DUPLICATES = {
    # Same original question as HI2-021. Keep the original image on the front,
    # but do not duplicate the whole answer/explanation on reveal.
    "PEDS2-2025-15to18-Q1": "PEDS2-HI2-021",
}

CURATED_CARD_FIXES = {
    "PEDS2-2023-25to28-Q2": {
        "answer": "활동성/선천결핵 확인 후, 활동성 결핵이 없으면 isoniazid 3개월 예방투여 후 TST 판정",
        "uncertain": False,
        "enhanced_explanation": "🧭 Big picture\n이 문제는 단순히 TST + INH가 아니라, 생후 50일이라는 나이 때문에 <3개월 활동성 결핵 접촉자 알고리즘으로 풀어야 한다. 알렌 기준으로 먼저 병력청취, 신체진찰, CXR 등으로 활동성 결핵을 배제하고, 신생아/어린 영아에서는 선천결핵 가능성도 확인한다. 활동성 결핵이 없으면 <3개월 영아는 TST/IGRA를 먼저 시행하기보다 isoniazid를 3개월 예방적으로 투여한 뒤 TST로 판정하는 흐름이 핵심이다.\n\n🔎 핵심 단서\n- 생후 50일: 3개월 미만 영아\n- 할머니 활동결핵: 활동성 결핵 접촉자\n- 3개월 미만: TST/IGRA를 먼저 던지는 나이가 아니라 INH 3개월 예방투여 축\n- 활동성 결핵 배제: 병력, 신체진찰, CXR 등 먼저 확인\n- 신생아/어린 영아에서는 선천결핵 가능성도 함께 확인\n- 이전 답 TST + INH는 방향은 비슷하지만, 알렌 알고리즘의 순서와 나이별 차이를 충분히 반영하지 못함\n\n👣 시험장 사고 흐름\n1단계: 활동성 결핵 접촉자인지 확인한다.\n2단계: 증상, 진찰, CXR로 활동성 결핵을 먼저 배제한다.\n3단계: 생후 50일은 <3개월이므로 TST/IGRA를 먼저 믿고 판단하지 않는다.\n4단계: 활동성 결핵이 없으면 INH 3개월 예방투여를 먼저 시작한다.\n5단계: 이후 TST를 시행하여 음성이면 INH 중단, 양성이면 잠복결핵 치료 축으로 넘어간다.\n\n🧠 쉽게 이해하기\n3개월 미만 영아는 결핵에 노출된 뒤 검사 반응을 기다리기엔 위험도가 높다. 그래서 검사를 먼저 해석하고 움직이는 큰아이와 달리, 활동성 결핵만 배제되면 창기간 동안 INH로 먼저 막아주는 느낌이다. 이후 TST로 진짜 감염 여부를 다시 확인한다.\n\n📊 감별/오답 제거\n<3개월 활동성 결핵 접촉자: 활동성/선천결핵 확인 후 INH 3개월 예방투여 → 이후 TST 판정.\n3개월~2세 접촉자: 활동성 결핵 배제 후 TST 시행. TST 음성이면 INH 3개월 예방투여 후 8주 뒤 재검, TST 양성이면 잠복결핵 치료.\n2~5세 접촉자: 활동성 결핵 배제 후 TST, 음성이면 마지막 접촉 8주 후 재검.\n5세 이상 접촉자: 활동성 결핵 배제 후 IGRA, 음성이면 8주 후 재검.\nCXR 이상/증상 있음: 예방치료가 아니라 활동성 결핵 평가/치료 축.\n\n✅ 3초 Lock line\n생후 50일 활동결핵 접촉자 = 활동성/선천결핵 확인 후, 활동성 아니면 INH 3개월 먼저.\n\n🎯 암기 확인 퀴즈\nQ1. 생후 50일은 결핵 접촉자 알고리즘에서 어느 연령군인가?\nA1. 3개월 미만.\nQ2. 이 연령군에서 활동성 결핵이 없으면 먼저 하는 예방 처치는?\nA2. Isoniazid 3개월 예방투여.\nQ3. 3개월~2세 접촉자에서 TST 음성이면?\nA3. INH 3개월 예방투여 후 8주 뒤 재검."
    },
    "PEDS2-2025-19to23-Q1": {
        "question": "객Q. 10세 여아가 7일간 지속되는 발열과 인후통으로 내원하였다. 편도 비대와 회색 삼출, 입천장 점상출혈이 보이고 양쪽 경부 림프절이 2 cm 정도로 만져지며 압통이 있다. 지라는 갈비뼈 아래 3횡지 만져진다. 몸통과 사타구니에 홍반구진성 발진/점상출혈이 있고, 혈액검사에서 림프구 증가와 비정형 림프구 20%가 보인다. 가장 가능성이 큰 진단은?",
        "answer": "전염단핵구증(EBV infectious mononucleosis)",
        "uncertain": False,
        "enhanced_explanation": "🧭 Big picture\n발열, 인후통, 편도 삼출, 경부림프절비대, 비장비대에 비정형 림프구 20%가 붙으면 전염단핵구증을 고른다. 대표 원인은 EBV다.\n\n🔎 핵심 단서\n- 7일 발열과 인후통\n- 편도 비대와 회색 삼출\n- 경부 림프절비대\n- 비장비대\n- 림프구 증가와 비정형 림프구 20%\n\n👣 시험장 사고 흐름\n1단계: 삼출성 인두염에서 GAS와 EBV를 같이 떠올린다.\n2단계: 림프절비대, 비장비대, 비정형 림프구가 있으면 EBV 쪽으로 잠근다.\n3단계: 성홍열은 딸기혀/사포양 발진, 가와사키병은 5일 이상 발열+점막/손발/관상동맥 축으로 감별한다.\n\n🧠 쉽게 이해하기\n전염단핵구증은 목감기처럼 보이지만 실제로는 림프조직 전체가 반응하는 바이러스 감염이다. 그래서 편도도 붓고, 림프절도 커지고, 비장도 만져질 수 있다. 비정형 림프구는 EBV에 반응한 T세포가 커져 보이는 단서다.\n\n📊 감별/오답 제거\n전염단핵구증: 삼출성 인두염 + 경부림프절 + 비장비대 + 비정형 림프구.\n성홍열: GAS 인두염 + 딸기혀 + 사포양 발진.\n가와사키병: 5일 이상 발열 + 결막/입술/손발 + 관상동맥 위험.\n\n✅ 3초 Lock line\n삼출성 인두염 + 비장비대 + 비정형 림프구 = EBV 전염단핵구증.\n\n🎯 암기 확인 퀴즈\nQ. 전염단핵구증에서 증가하는 특징적 혈액세포는?\nA. 비정형 림프구."
    },
    "PEDS2-2023PDF-022": {
        "question": "객Q. 발열, 기침, 콧물, 결막염 후 구강 점막의 Koplik spot과 얼굴에서 시작해 몸통/사지로 퍼지는 발진이 보인다. 진단은?",
        "answer": "홍역, measles",
    },
    "PEDS2-2023PDF-029": {
        "question": "객Q. 발열과 보챔, 섭취 저하가 있는 소아에서 잇몸과 구강 점막의 다발성 수포/궤양성 병변이 보인다. 가장 가능성이 큰 진단은?",
        "answer": "헤르페스 잇몸구내염, herpetic gingivostomatitis",
    },
    "PEDS2-2026-5to8-Q8": {
        "question": "객Q. 소아에서 발열/귀 통증과 함께 고막 팽윤·화농성 중이염 소견이 제시되었다. 진단과 1차 치료는?",
        "answer": "화농성 중이염, 아목시실린",
    },
    "PEDS2-2023PDF-001": {
        "question": "객Q. 생후 초기부터 흡기 시 그르렁거림/협착음이 있고, 울거나 보채거나 수유할 때 심해지며 엎드리면 완화된다. 가장 가능성이 큰 진단은?",
        "answer": "후두연화증 또는 선천성 후두 협착음",
    },
    "PEDS2-2025-15to18-Q5": {
        "question": "객Q. 상지 혈압은 높고 하지 혈압은 낮거나 femoral pulse가 약하게 만져지는 소아 선천심질환을 의심한다. 가장 가능성이 큰 진단은?",
        "answer": "CoA",
        "enhanced_explanation": "🧭 Big picture\n상지 고혈압, 하지 저혈압, femoral pulse 약화/지연이 보이면 대동맥축착(CoA)을 의심한다. 대동맥이 좁아져 협착부 위쪽은 압력이 높고 아래쪽은 관류가 떨어지는 구조다.\n\n🔎 핵심 단서\n- 상지 혈압이 상대적으로 높음\n- 하지 혈압이 낮거나 femoral pulse가 약함\n- 영아에서는 ductus가 닫히며 shock/심부전 가능\n- 큰 아이에서는 두통, 코피, 운동 시 다리 피로 가능\n\n👣 시험장 사고 흐름\n1단계: 선천심질환 문제에서 산소포화도와 murmur만 보지 말고 pulse/BP를 확인한다.\n2단계: 팔과 다리 차이가 있으면 CoA를 올린다.\n3단계: Turner syndrome, rib notching, collateral circulation 단서를 연결한다.\n\n🧠 쉽게 이해하기\nCoA는 대동맥 중간이 조인 호스라고 생각하면 된다. 조인 곳 위쪽인 머리와 팔 쪽은 압력이 높아지고, 아래쪽인 다리는 피가 덜 가서 맥박이 약하다. 그래서 “팔은 높고 다리는 낮다”가 핵심 그림이다.\n\n📊 감별/오답 제거\nCoA: 상하지 혈압 차이, femoral pulse 약화/지연.\nPDA: continuous machinery murmur, bounding pulse, wide pulse pressure.\nTOF: 청색증, boot-shaped heart, cyanotic spell.\nASD: fixed wide splitting S2.\nVSD: holosystolic murmur at LLSB.\n\n✅ 3초 Lock line\n상지 고혈압 + 하지 맥박 약함 = 대동맥축착.\n\n🎯 암기 확인 퀴즈\nQ. CoA에서 반드시 비교해야 하는 진찰 소견은?\nA. 상지/하지 혈압과 femoral pulse."
    },
}

# BEGIN INFECTION_ANSWER_AUDIT_FIXES_20260517
CURATED_CARD_FIXES.update({'PEDS2-2025-15to18-Q1': {'question': '객Q. 2세 여아가 발열과 눈 충혈로 병원에 왔다. 결막이 충혈되어 있고, 눈 주위에\n황색 분비물과 인두 부위의 발적이 있었다. 목 림프절이 만져진다. 원인은?\n① 리노바이러스 ② 노로바이러스 ③ 파르보바이러스\n④ 아데노바이러스 ⑤ RSV', 'display_question': '객Q. 2세 여아가 발열과 눈 충혈로 병원에 왔다. 결막이 충혈되어 있고, 눈 주위에\n황색 분비물과 인두 부위의 발적이 있었다. 목 림프절이 만져진다. 원인은?\n① 리노바이러스 ② 노로바이러스 ③ 파르보바이러스\n④ 아데노바이러스 ⑤ RSV', 'answer': '아데노바이러스', 'uncertain': False}, 'PEDS2-2023PDF-029': {'answer': '헤르페스 잇몸구내염, herpetic gingivostomatitis', 'uncertain': False}, 'PEDS2-2023PDF-038': {'answer': '급성 중이염 1차 치료: Amoxicillin', 'uncertain': False}, 'PEDS2-HI2-001': {'answer': '직장 체온 38℃ 이상', 'uncertain': False}, 'PEDS2-HI2-002': {'answer': '감염, 류마티즘/자가염증성질환, 종양', 'uncertain': False}, 'PEDS2-HI2-003': {'answer': '1~3개월: E. coli, enterovirus, parechovirus / 3~36개월: S. pneumoniae, N. meningitidis, Salmonella', 'uncertain': False}, 'PEDS2-HI2-004': {'answer': '항생제 내성 증가, 정상균총 파괴, 부작용/불필요한 경제적 부담 증가', 'uncertain': False}, 'PEDS2-HI2-005': {'answer': '홍역; 생후 4개월 남동생은 노출 6일 이내 면역글로불린', 'uncertain': False}, 'PEDS2-HI2-008': {'answer': 'Mumps virus; 대증치료/acetaminophen', 'uncertain': False}, 'PEDS2-HI2-009': {'answer': '수족구병; Coxsackievirus A16', 'uncertain': False}, 'PEDS2-HI2-010': {'answer': '돌발진(장미진); HHV-6', 'uncertain': False}, 'PEDS2-HI2-014': {'answer': '엡스타인바 바이러스(EBV)', 'uncertain': False}, 'PEDS2-HI2-015': {'answer': 'Acetaminophen 등 대증치료', 'uncertain': False}, 'PEDS2-HI2-016': {'answer': 'A군 사슬알균(Streptococcus pyogenes); 류마티스열 예방', 'uncertain': False}, 'PEDS2-HI2-017': {'answer': '고름 사슬알균(Streptococcus pyogenes)', 'uncertain': False}, 'PEDS2-HI2-018': {'answer': '아목시실린', 'uncertain': False}, 'PEDS2-HI2-021': {'answer': '아데노바이러스', 'uncertain': False}, 'PEDS2-HI2-022': {'answer': 'Bordetella pertussis; erythromycin 또는 macrolide', 'uncertain': False}, 'PEDS2-HI2-023': {'answer': '클라리트로마이신', 'uncertain': False}, 'PEDS2-HI2-024': {'question': '주Q. 12세 환자가 2일 전부터 시작된 발열과 무릎 통증을 주소로 내원하였다. 신체검사상 압통은 있었고, 발적과 열감은 없었다.\n(1) 진단은? 급성 골수염\n(2) 원인균? S. aureus', 'display_question': '주Q. 12세 환자가 2일 전부터 시작된 발열과 무릎 통증을 주소로 내원하였다. 신체검사상 압통은 있었고, 발적과 열감은 없었다.\n(1) 진단은? [답 숨김]\n(2) 원인균? [답 숨김]', 'answer': '급성 골수염; Staphylococcus aureus', 'uncertain': False}, 'PEDS2-HI2-025': {'answer': '나프실린', 'uncertain': False}, 'PEDS2-HI2-026': {'answer': '농가진; S. aureus 및 Group A Streptococcus', 'uncertain': False}, 'PEDS2-HI2-028': {'answer': '파상풍 백신 X, 파상풍 면역글로불린 X; 상처 소독', 'uncertain': False}, 'PEDS2-HI2-039': {'answer': '바이러스 수막염; Enterovirus', 'uncertain': False}, 'PEDS2-HI2-041': {'answer': '엔테로바이러스', 'uncertain': False}, 'PEDS2-HI2-042': {'answer': 'B군 사슬알균(Group B Streptococcus)', 'uncertain': False}, 'PEDS2-HI2-082': {'answer': '인두 후부 농양 - Neck lateral view', 'uncertain': False}, 'PEDS2-2023-37to40-Q3': {'answer': '수막알균(Neisseria meningitidis)', 'uncertain': False}, 'PEDS2-HI2-030': {'answer': '반응성/세균성 림프절염, EBV 전염단핵구증, 결핵/비정형 마이코박테리아, Kawasaki disease, 악성질환 등에서 3가지 이상', 'uncertain': False}, 'PEDS2-HI2-038': {'answer': 'S. pneumoniae, H. influenzae type b, N. meningitidis', 'uncertain': False}})
# END INFECTION_ANSWER_AUDIT_FIXES_20260517

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
    if any(t in {"감염", "감염관리", "피부"} for t in tags) or re.search(INFECTION_PATTERN, section, re.I):
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
        card_id = row.get("card_id", "")
        cands = row.get("candidates") or []
        usable = []
        for cand in cands[:2]:
            # Conservative: keep only candidates that were at least contextually linked.
            curated_id = cand.get("curated_id", "")
            if (card_id, curated_id) in CURATED_NON_HI_IMAGE_EXCLUDES:
                continue
            if int(cand.get("score", 0)) >= 4 and cand.get("path"):
                is_front_exact = (card_id, curated_id) in CURATED_FRONT_IMAGE_EXACT
                is_answer_only = (card_id, curated_id) in CURATED_ANSWER_ONLY_IMAGES
                item_kind = "nonhi_exact" if is_front_exact else ("answer_only_source" if is_answer_only else (curated_id or "nonhi"))
                item = copy_asset(cand["path"], card_id or "nonhi", item_kind)
                if item:
                    item["caption"] = "원문 문제 이미지" if is_front_exact else ("답 체크 원문 이미지" if is_answer_only else f"non-HI candidate · score {cand.get('score')} · {cand.get('curated_id', '')}")
                    if is_front_exact:
                        item["front_visible"] = True
                        item["curated_id"] = curated_id
                    if is_answer_only:
                        item["answer_only"] = True
                        item["curated_id"] = curated_id
                    usable.append(item)
        if usable:
            out[card_id] = usable
    return out


def apply_curated_card_fixes(card: dict) -> None:
    fix = CURATED_CARD_FIXES.get(str(card.get("id", "")))
    if not fix:
        return
    if "question" in fix:
        fixed_question = normalize_multiline(fix["question"])
        card["question"] = fixed_question
        # normalize_base_card may already have copied a stale source-variant
        # note into display_question. If we curate the learner-facing question,
        # keep front display in sync unless an explicit display_question is set.
        card["display_question"] = normalize_multiline(fix.get("display_question", fixed_question))
    if "display_question" in fix:
        card["display_question"] = normalize_multiline(fix["display_question"])
        card["display_question"] = normalize_multiline(fix.get("display_question") or fix["question"])
    elif "display_question" in fix:
        card["display_question"] = normalize_multiline(fix["display_question"])
    if "answer" in fix:
        card["answer"] = normalize_space(fix["answer"])
    if "enhanced_explanation" in fix:
        card["enhanced_explanation"] = normalize_multiline(fix["enhanced_explanation"])
    if "explanation" in fix:
        card["explanation"] = normalize_multiline(fix["explanation"])
    if "uncertain" in fix:
        card["uncertain"] = bool(fix["uncertain"])
    if "same_as_hi" in fix:
        card["same_as_hi"] = normalize_space(fix["same_as_hi"])
    if card.get("id") in CURATED_HI_DUPLICATES:
        card["same_as_hi"] = CURATED_HI_DUPLICATES[str(card.get("id"))]
    extra_tags = ["curated-front-fix"]
    if card.get("same_as_hi"):
        extra_tags.append("HI-duplicate")
    card["tags"] = list(dict.fromkeys(card.get("tags", []) + extra_tags))


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
        if where == "front" and img.get("answer_only"):
            continue
        # Avoid text-answer crops on the front. Embedded images are safer; source crops stay answer/guide only.
        if where == "front" and not (img.get("front_visible") or img.get("kind") in {"embedded", "linked", "nonhi_exact"}):
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


def duplicate_answer_html(card: dict) -> str:
    same = normalize_space(card.get("same_as_hi"))
    answer = normalize_space(card.get("answer"))
    answer_line = ""
    if answer and "동일 문항" not in answer and not answer.startswith("HI2-"):
        answer_line = f"""
    <div style="margin-top:8px;font-size:13px;font-weight:900;color:#166534;">정답</div>
    <div style="font-size:20px;line-height:1.55;color:#052e16;"><strong>{e(answer)}</strong></div>
""".rstrip()
    return f"""
<section class="kmle-answer" style="display:flex;flex-direction:column;gap:12px;">
  <div style="border-left:4px solid #2563eb;background:#eff6ff;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#1d4ed8;margin-bottom:6px;letter-spacing:.04em;">답</div>
    <div style="font-size:20px;line-height:1.55;color:#052e16;"><strong>HI와 동일 문항입니다.</strong></div>
    {answer_line}
    <div style="margin-top:8px;font-size:13px;line-height:1.65;color:#334155;">{e(same)} 카드와 같은 원문이라, 여기서는 중복 해설을 반복하지 않습니다.</div>
    {images_html(card, 'answer')}
  </div>
</section>
""".strip()


def answer_html(card: dict) -> str:
    if card.get("same_as_hi"):
        return duplicate_answer_html(card)
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
    if card.get("same_as_hi"):
        return f"""
<section class="kmle-guide" style="line-height:1.7;">
  <h4>문제</h4>
  <p>{fmt(card.get('display_question') or card.get('question'))}</p>
  {images_html(card, 'front')}
  <h4>답</h4>
  <p><strong>HI와 동일 문항입니다.</strong></p>
  <p>{e(card.get('same_as_hi'))} 카드와 같은 원문이라 중복 해설을 반복하지 않습니다.</p>
  {images_html(card, 'answer')}
</section>
""".strip()
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


def short_text(value: object, limit: int = 120) -> str:
    text = normalize_space(value)
    text = re.sub(r"[①②③④⑤]\s*", "", text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def extract_tutor_heading(text: object, heading: str) -> str:
    raw = normalize_multiline(text)
    if not raw:
        return ""
    headings = ["🧭 Big picture", "🔎 핵심 단서", "👣 시험장 사고 흐름", "🧠 쉽게 이해하기", "📊 감별/오답 제거", "✅ 3초 Lock line", "🎯 암기 확인 퀴즈"]
    try:
        start = raw.index(heading) + len(heading)
    except ValueError:
        return ""
    end = len(raw)
    for h in headings:
        if h == heading:
            continue
        pos = raw.find(h, start)
        if pos != -1:
            end = min(end, pos)
    return raw[start:end].strip()


def split_study_lines(text: object, limit: int = 6) -> list[str]:
    raw = normalize_multiline(text)
    if not raw:
        return []
    lines: list[str] = []
    for line in raw.splitlines():
        line = normalize_space(re.sub(r"^[\-•⭕❌0-9.①②③④⑤\s]+", "", line))
        if line and line not in lines:
            lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def unit_study_axis(unit: str) -> str:
    return {
        "감염": "나이, 발진 순서, 노출 후 예방, 항생제 선택을 분리해서 본다.",
        "소화기": "구토·설사·혈변·탈수에서 응급도와 보충/금기 처치를 먼저 가른다.",
        "호흡기": "상기도/하기도, 산소화, 흉부영상, 치료 escalation 단서를 먼저 잡는다.",
        "심혈관": "청색증, 심잡음 위치, 맥박/혈압 차이, 심전도 리듬을 축으로 나눈다.",
        "범위외/확인": "2주차 핵심 범위 밖이 섞였을 수 있으므로 원문 확인 표시를 유지한다.",
    }.get(unit, "문제 stem의 trigger를 먼저 잡고 정답 단어로 잠근다.")


def build_hi_study_parts(cards: list[dict]) -> list[dict]:
    hi_cards = [c for c in cards if c.get("layer") == "hi156"]
    groups: dict[tuple[str, str], list[dict]] = {}
    for card in hi_cards:
        key = (str(card.get("official_unit") or "범위외/확인"), str(card.get("section") or "HI"))
        groups.setdefault(key, []).append(card)

    parts: list[dict] = []
    for (unit, section), rows in groups.items():
        rows.sort(key=lambda c: int(c.get("source_rank", 999999)))
        chapter = OFFICIAL_UNIT_CHAPTER.get(unit, unit)
        first_rank = int(rows[0].get("source_rank", 999999))
        key_points = []
        lock_lines = []
        diff_lines = []
        easy_lines = []
        quiz_lines = []
        card_minis = []

        for card in rows:
            cue = short_text(card.get("display_question") or card.get("question"), 150)
            ans = short_text(card.get("answer") or "원문 확인 필요", 90)
            key_points.append(f"{cue} → {ans}")
            lock = extract_tutor_heading(card.get("enhanced_explanation"), "✅ 3초 Lock line")
            if lock:
                lock_lines.extend(split_study_lines(lock, 2))
            diff = extract_tutor_heading(card.get("enhanced_explanation"), "📊 감별/오답 제거")
            if diff:
                diff_lines.extend(split_study_lines(diff, 3))
            easy = extract_tutor_heading(card.get("enhanced_explanation"), "🧠 쉽게 이해하기")
            if easy:
                easy_lines.extend(split_study_lines(easy, 2))
            quiz = extract_tutor_heading(card.get("enhanced_explanation"), "🎯 암기 확인 퀴즈")
            if quiz:
                quiz_lines.extend(split_study_lines(quiz, 4))
            card_minis.append(
                f"<div class='hi-card-mini'><code>{e(card.get('id'))}</code> · {e(cue)}<br><strong>답:</strong> {e(ans)}</div>"
            )

        key_points = list(dict.fromkeys(key_points))[:10]
        lock_lines = list(dict.fromkeys(lock_lines))[:8]
        diff_lines = list(dict.fromkeys(diff_lines))[:8]
        easy_lines = list(dict.fromkeys(easy_lines))[:5]
        quiz_lines = list(dict.fromkeys(quiz_lines))[:8]
        if len(rows) > len(key_points):
            key_points.append(f"이외 {len(rows) - len(key_points)}문항은 아래 카드 목록에서 이어서 확인")
        if not lock_lines:
            lock_lines = [f"{section}: stem trigger를 보고 {unit_study_axis(unit)}"]
        if not diff_lines:
            diff_lines = [unit_study_axis(unit)]
        if not easy_lines:
            easy_lines = [f"{section} 파트는 문제마다 하나의 trigger와 하나의 정답 단어를 연결하는 식으로 먼저 잠그면 된다."]
        if not quiz_lines:
            quiz_lines = [f"Q. {section} 파트에서 가장 먼저 잡을 축은?", f"A. {unit_study_axis(unit)}"]

        html_body = f"""
<h3>{e(section)}</h3>
<p><strong>{e(chapter)}</strong> · HI 2차 bank {len(rows)}문항 · 원문 순서 {rows[0].get('hi_id') or rows[0].get('id')}부터</p>
<div class="hi-study-actions">
  <button class="hi-study-primary" onclick="startHIStudyPart({len(parts)})">이 파트만 퀴즈 시작</button>
  <button class="hi-study-secondary" onclick="setOfficialUnitFilter('{e(chapter)}')">{e(chapter)} 전체 보기</button>
</div>
<h4>🧭 Big picture</h4>
<p>이 파트는 <strong>{e(section)}</strong>를 HI 원문 기준으로 묶은 공부 블록이다. 전체 2주차 범위 안에서는 <strong>{e(chapter)}</strong> 축에 들어가며, {e(unit_study_axis(unit))}</p>
<h4>🔎 핵심 단서</h4>
<ul>{''.join(f'<li>{e(x)}</li>' for x in key_points)}</ul>
<h4>👣 시험장 사고 흐름</h4>
<ol><li>먼저 단원 축을 잡는다: {e(chapter)}.</li><li>stem에서 사진/나이/기간/검사/소견 trigger를 하나 고른다.</li><li>그 trigger를 아래 lock line 중 하나와 연결한다.</li><li>답이 원문 확인 필요인 카드는 외우기보다 원문 crop/해설을 같이 확인한다.</li></ol>
<h4>🧠 쉽게 이해하기</h4>
<ul>{''.join(f'<li>{e(x)}</li>' for x in easy_lines)}</ul>
<h4>📊 감별/오답 제거</h4>
<ul>{''.join(f'<li>{e(x)}</li>' for x in diff_lines)}</ul>
<h4>✅ 3초 Lock line</h4>
{''.join(f'<div class="hi-lock">{e(x)}</div>' for x in lock_lines)}
<h4>🎯 암기 확인 퀴즈</h4>
<ul>{''.join(f'<li>{e(x)}</li>' for x in quiz_lines)}</ul>
<h4>카드 목록</h4>
{''.join(card_minis)}
""".strip()
        parts.append({
            "unit": unit,
            "chapter": chapter,
            "section": section,
            "count": len(rows),
            "firstRank": first_rank,
            "cardIds": [str(c.get("id")) for c in rows],
            "search": normalize_space(" ".join([unit, chapter, section] + [str(c.get("question", "")) + " " + str(c.get("answer", "")) for c in rows])).lower(),
            "html": html_body,
        })
    parts.sort(key=lambda p: (OFFICIAL_UNIT_RANK.get(p["unit"], 99), p["firstRank"], p["section"]))
    return parts


def hi_study_js(parts: list[dict]) -> str:
    payload = json.dumps(parts, ensure_ascii=False)
    return "\nconst HI_STUDY_DATA = " + payload + ";\n" + r"""
let selectedHIStudyUnit = 'ALL';
let selectedHIStudyIndex = 0;
function filteredHIStudyParts() {
    const q = String(document.getElementById('hiStudySearch')?.value || '').trim().toLowerCase();
    return HI_STUDY_DATA.map((item, idx) => ({item, idx})).filter(({item}) => {
        const unitOK = selectedHIStudyUnit === 'ALL' || item.chapter === selectedHIStudyUnit;
        const queryOK = !q || item.search.includes(q);
        return unitOK && queryOK;
    });
}
function renderHIStudy() {
    const list = document.getElementById('hiStudyList');
    const detail = document.getElementById('hiStudyDetail');
    if (!list || !detail) return;
    const rows = filteredHIStudyParts();
    if (!rows.some(r => r.idx === selectedHIStudyIndex) && rows.length) selectedHIStudyIndex = rows[0].idx;
    list.innerHTML = rows.map(({item, idx}) => `<button class="hi-study-part ${idx === selectedHIStudyIndex ? 'active' : ''}" onclick="selectHIStudyPart(${idx})"><div class="hi-study-part-title">${item.section}</div><div class="hi-study-part-meta">${item.chapter} · ${item.count}문항</div></button>`).join('') || '<div class="hi-study-part-meta">검색 결과 없음</div>';
    const selected = HI_STUDY_DATA[selectedHIStudyIndex] || rows[0]?.item;
    detail.innerHTML = selected ? selected.html : '<p>선택된 파트가 없습니다.</p>';
    document.querySelectorAll('.hi-study-chip').forEach(btn => btn.classList.toggle('active', btn.dataset.hiunit === selectedHIStudyUnit));
}
function selectHIStudyPart(idx) { selectedHIStudyIndex = idx; renderHIStudy(); document.getElementById('hiStudyDetail')?.scrollIntoView({behavior:'smooth', block:'start'}); }
function setHIStudyUnit(unit) { selectedHIStudyUnit = unit || 'ALL'; renderHIStudy(); }
function startHIStudyPart(idx) {
    const item = HI_STUDY_DATA[idx];
    if (!item || !item.cardIds || !item.cardIds.length) return;
    closePedsMobileSidebar();
    startQuizWith(item.cardIds);
}
document.addEventListener('DOMContentLoaded', renderHIStudy);
"""


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
            src_name = Path(p).name
            if src_name in EMBEDDED_ANSWER_ONLY_FILENAMES:
                item["answer_only"] = True
                item["caption"] = f"답/해설 포함 원문 이미지 · {src_name}"
            else:
                item["caption"] = f"HI embedded image · {src_name}"
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
        apply_curated_card_fixes(rec)
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
    unit_by_id = {str(c.get("id")): str(c.get("official_chapter")) for c in data}
    hi_study_parts = build_hi_study_parts(data)
    stats = f"공식 2주차: 감염 {unit_counts['감염']} · 소화기 {unit_counts['소화기']} · 호흡기 {unit_counts['호흡기']} · 심혈관 {unit_counts['심혈관']} · 범위외/확인 {unit_counts['범위외/확인']} · Total {len(data)}"
    source_stats = f"Core {counts['core79']} · 2025+{counts['source2025']} · 2023PDF {counts['source2023pdf']} · 후보 {counts['candidate']} · HI {counts['hi156']}"
    filter_buttons = "".join(
        f'<button class="unit-filter-chip" data-unit="{e(OFFICIAL_UNIT_CHAPTER[u])}" onclick="setOfficialUnitFilter(\'{e(OFFICIAL_UNIT_CHAPTER[u])}\')">{e(OFFICIAL_UNIT_CHAPTER[u])} <b>{unit_counts[u]}</b></button>'
        for u in OFFICIAL_UNIT_ORDER
    )
    sidebar_buttons = "".join(
        f'<button class="peds-side-unit unit-filter-chip" data-unit="{e(OFFICIAL_UNIT_CHAPTER[u])}" onclick="setOfficialUnitFilter(\'{e(OFFICIAL_UNIT_CHAPTER[u])}\')">{e(OFFICIAL_UNIT_CHAPTER[u])} <b>{unit_counts[u]}</b></button>'
        for u in OFFICIAL_UNIT_ORDER
    )
    filter_html = f"""
    <section class="official-unit-filter clean-home-shell" id="officialUnitFilter">
        <div class="home-kicker">소아청소년과 2주차 Pretest FULL · 288문항</div>
        <h1>공식 범위대로 바로 풀기</h1>
        <p class="home-lead">교수님 공지 기준 12~15장 순서로 정돈했습니다. 범위를 고른 뒤 순서대로 공부하거나 랜덤으로 점검하세요.</p>
        <div class="unit-filter-actions">
            <button class="unit-filter-chip active" data-unit="ALL" onclick="setOfficialUnitFilter('ALL')">전체 <b>{len(data)}</b></button>
            {filter_buttons}
        </div>
        <div class="home-start-row">
            <button class="home-start-primary" onclick="startOfficialUnitOrdered()">선택 범위 순서대로 시작 <b id="orderedStartCount">{len(data)}</b></button>
            <button class="home-start-secondary" onclick="startOfficialUnitRandom()">랜덤으로 점검 <b id="randomStartCount">{len(data)}</b></button>
        </div>
        <div class="resume-quiz-card" id="resumeQuizPanel" hidden>
            <div class="resume-quiz-meta">진행 중인 퀴즈가 있어요</div>
            <div class="resume-quiz-title" id="resumeQuizTitle">퀴즈 이어하기</div>
            <div class="resume-quiz-detail" id="resumeQuizDetail">방금 보던 카드로 돌아갑니다.</div>
            <div class="resume-quiz-actions">
                <button class="resume-quiz-btn" onclick="resumeQuizSession()">퀴즈 이어하기</button>
                <button class="resume-clear-btn" onclick="clearQuizResumeState()">이어하기 지우기</button>
            </div>
        </div>
        <div class="home-selected">현재 범위: <strong id="selectedUnitLabel">전체</strong> · <span id="selectedUnitCount">{len(data)}</span>문항</div>
        <div class="unit-filter-note">범위외/혼입 확인은 HI 전체 포함 정책 때문에 삭제하지 않고 보존한 카드입니다.</div>
        <div class="home-source-stats">{e(source_stats)}</div>
    </section>
""".rstrip()
    hi_unit_buttons = ''.join(
        f'<button class="hi-study-chip" data-hiunit="{e(OFFICIAL_UNIT_CHAPTER[u])}" onclick="setHIStudyUnit(\'{e(OFFICIAL_UNIT_CHAPTER[u])}\')">{e(OFFICIAL_UNIT_CHAPTER[u])}</button>'
        for u in OFFICIAL_UNIT_ORDER
    )
    hi_study_html = f"""
    <section class="hi-study-panel" id="hiStudyPanel">
        <div class="hi-study-head">
            <div>
                <div class="hi-study-kicker">HI 2차 원문 bank 공부모드</div>
                <h2>HI 공부하기</h2>
                <p>HI 156문항을 원문 section 기준으로 묶고, 각 파트를 퀴즈 해설용 7섹션 형식으로 압축했습니다. 먼저 파트 요약을 보고, 바로 그 파트만 퀴즈로 들어갈 수 있습니다.</p>
            </div>
            <div class="hi-study-stats">{len(hi_study_parts)}개 파트 · HI {counts['hi156']}문항</div>
        </div>
        <div class="hi-study-toolbar">
            <input id="hiStudySearch" class="hi-study-search" type="search" placeholder="HI 파트/키워드 검색" oninput="renderHIStudy()" />
            <button class="hi-study-chip active" data-hiunit="ALL" onclick="setHIStudyUnit('ALL')">전체</button>
            {hi_unit_buttons}
        </div>
        <div class="hi-study-layout">
            <div class="hi-study-list" id="hiStudyList"></div>
            <article class="hi-study-detail" id="hiStudyDetail"></article>
        </div>
    </section>
""".rstrip()
    sidebar_html = f"""
        <div class="peds-sidebar-launcher">
            <div class="peds-side-title">공식 단원</div>
            <button class="peds-side-unit unit-filter-chip active" data-unit="ALL" onclick="setOfficialUnitFilter('ALL')">전체 <b>{len(data)}</b></button>
            {sidebar_buttons}
            <div class="peds-side-actions">
                <button onclick="startOfficialUnitOrdered()">순서대로 시작</button>
                <button onclick="startOfficialUnitRandom()">랜덤 시작</button>
            </div>
        </div>
""".rstrip()
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
body.peds-pretest2-full-bg::before, body.peds-pretest2-full-bg::after {{ display:none !important; content:none !important; }}
body.peds-pretest2-full-bg .mobile-review-start, body.peds-pretest2-full-bg .review-hero, body.peds-pretest2-full-bg .card-grid, body.peds-pretest2-full-bg .sidebar .sb-quiz-btns, body.peds-pretest2-full-bg .sidebar .sb-item {{ display:none !important; }}
body.peds-pretest2-full-bg .main {{ padding-bottom: 42px; }}
body.peds-pretest2-full-bg .official-unit-filter {{ margin: 0 auto 18px; max-width: 980px; padding: 20px 18px; border-radius: 22px; background: rgba(15,23,42,.82); border: 1px solid rgba(191,219,254,.28); box-shadow: 0 18px 44px rgba(2,6,23,.22); }}
body.peds-pretest2-full-bg .home-kicker {{ display:inline-flex; padding:4px 10px; border-radius:999px; background:rgba(37,99,235,.20); border:1px solid rgba(147,197,253,.32); color:#bfdbfe; font-size:12px; font-weight:950; letter-spacing:.04em; }}
body.peds-pretest2-full-bg .official-unit-filter h1 {{ margin:12px 0 8px; color:#f8fafc; font-size:26px; line-height:1.22; }}
body.peds-pretest2-full-bg .home-lead {{ margin:0 0 16px; color:#cbd5e1; line-height:1.58; font-size:14px; }}
body.peds-pretest2-full-bg .unit-filter-title {{ font-weight: 950; color: #dbeafe; margin-bottom: 10px; line-height: 1.45; }}
body.peds-pretest2-full-bg .unit-filter-actions {{ display:flex; flex-wrap:wrap; gap:8px; }}
body.peds-pretest2-full-bg .unit-filter-chip {{ border:1px solid rgba(219,234,254,.34); background: rgba(30,41,59,.92); color:#e2e8f0; border-radius:999px; padding:7px 11px; font-size:12px; font-weight:900; cursor:pointer; }}
body.peds-pretest2-full-bg .unit-filter-chip b {{ color:#fef3c7; margin-left:4px; }}
body.peds-pretest2-full-bg .unit-filter-chip.active {{ background:#2563eb; color:#fff; border-color:#bfdbfe; }}
body.peds-pretest2-full-bg .unit-filter-note {{ margin-top:8px; color:#bfdbfe; font-size:12px; opacity:.88; }}
body.peds-pretest2-full-bg .home-start-row {{ display:grid; grid-template-columns: minmax(0,1.2fr) minmax(0,1fr); gap:10px; margin:18px 0 10px; }}
body.peds-pretest2-full-bg .home-start-row button {{ border:none; border-radius:16px; min-height:56px; padding:14px 16px; font-size:15px; font-weight:950; cursor:pointer; }}
body.peds-pretest2-full-bg .home-start-primary {{ background:linear-gradient(135deg,#5eead4,#93c5fd); color:#0f172a; box-shadow:0 12px 30px rgba(45,212,191,.18); }}
body.peds-pretest2-full-bg .home-start-secondary {{ background:rgba(15,23,42,.88); color:#e0f2fe; border:1px solid rgba(125,211,252,.34) !important; }}
body.peds-pretest2-full-bg .home-selected {{ color:#e2e8f0; font-size:13px; font-weight:850; }}
body.peds-pretest2-full-bg .home-source-stats {{ margin-top:10px; color:#94a3b8; font-size:12px; }}
body.peds-pretest2-full-bg .resume-quiz-card[hidden] {{ display:none !important; }}
body.peds-pretest2-full-bg .resume-quiz-card {{ margin:12px 0 10px; padding:13px 14px; border-radius:16px; background:linear-gradient(135deg, rgba(20,184,166,.22), rgba(37,99,235,.20)); border:1px solid rgba(125,211,252,.42); box-shadow:0 12px 30px rgba(14,165,233,.14); color:#e0f2fe; }}
body.peds-pretest2-full-bg .resume-quiz-meta {{ font-size:11px; font-weight:950; letter-spacing:.05em; color:#bae6fd; margin-bottom:4px; }}
body.peds-pretest2-full-bg .resume-quiz-title {{ font-size:17px; font-weight:950; color:#f8fafc; }}
body.peds-pretest2-full-bg .resume-quiz-detail {{ margin-top:3px; font-size:12px; line-height:1.45; color:#cbd5e1; }}
body.peds-pretest2-full-bg .resume-quiz-actions {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }}
body.peds-pretest2-full-bg .resume-quiz-actions button {{ border:none; border-radius:12px; padding:10px 12px; font-size:13px; font-weight:950; cursor:pointer; }}
body.peds-pretest2-full-bg .resume-quiz-btn {{ background:#5eead4; color:#0f172a; }}
body.peds-pretest2-full-bg .resume-clear-btn {{ background:rgba(15,23,42,.82); color:#bae6fd; border:1px solid rgba(186,230,253,.32) !important; }}
body.peds-pretest2-full-bg .peds-sidebar-launcher {{ margin-top:14px; display:flex; flex-direction:column; gap:8px; }}
body.peds-pretest2-full-bg .peds-side-title {{ color:#93c5fd; font-size:12px; font-weight:950; letter-spacing:.05em; }}
body.peds-pretest2-full-bg .peds-side-unit {{ width:100%; text-align:left; border-radius:10px; }}
body.peds-pretest2-full-bg .peds-side-actions {{ display:grid; grid-template-columns:1fr; gap:7px; margin-top:6px; }}
body.peds-pretest2-full-bg .peds-side-actions button {{ border:none; border-radius:10px; padding:9px 10px; color:#0f172a; background:#93c5fd; font-weight:900; cursor:pointer; }}
body.peds-pretest2-full-bg.quiz-mode-active .sb-mobile-toggle, body.peds-pretest2-full-bg.quiz-mode-active .mobile-review-start {{ display:none !important; }}
body.peds-pretest2-full-bg .quiz-overlay.active {{ z-index:10000; }}
body.peds-pretest2-full-bg .quiz-header {{ z-index:10001; background:rgba(15,23,42,.96); backdrop-filter: blur(10px); }}
body.peds-pretest2-full-bg .quiz-card {{ max-width:920px; margin:18px auto 84px; padding:18px; }}
body.peds-pretest2-full-bg .quiz-q {{ padding:14px; border:1px solid rgba(147,197,253,.18); border-radius:16px; background:rgba(15,23,42,.62); }}
body.peds-pretest2-full-bg .quiz-q-text {{ font-size:18px; }}
body.peds-pretest2-full-bg .unit-hidden {{ display:none !important; }}
@media (max-width: 768px) {{
  body.peds-pretest2-full-bg .official-unit-filter {{ margin-top:4px; padding:18px 14px; border-radius:18px; }}
  body.peds-pretest2-full-bg .official-unit-filter h1 {{ font-size:22px; }}
  body.peds-pretest2-full-bg .home-start-row {{ grid-template-columns:1fr; }}
  body.peds-pretest2-full-bg .home-start-row button {{ min-height:52px; }}
  body.peds-pretest2-full-bg .unit-filter-chip {{ padding:8px 10px; }}
  body.peds-pretest2-full-bg .quiz-card {{ width:100%; margin:8px auto 72px; padding:10px; }}
  body.peds-pretest2-full-bg .quiz-q {{ padding:10px; border-radius:14px; }}
  body.peds-pretest2-full-bg .quiz-q-text {{ font-size:15px; }}
}}
"""
    css += HI_STUDY_CSS
    text = text.replace("</style>", css + "\n</style>", 1)
    text = text.replace("<body>", '<body class="peds-pretest2-full-bg">', 1)
    text = text.replace('        <div class="sb-quiz-btns">', sidebar_html + '\n        <div class="sb-quiz-btns">', 1)
    text = text.replace('    <div class="review-hero" id="reviewHero">', filter_html + '\n' + hi_study_html + '\n    <div class="review-hero" id="reviewHero">', 1)
    # Clean-home mode: keep QUIZ_DATA for quiz mode, but do not render 288 static cards on the landing page.
    card_grid_start = text.find('    <div class="card-grid">')
    card_grid_end = text.find('\n</div>\n\n<!-- Quiz overlay -->', card_grid_start)
    if card_grid_start != -1 and card_grid_end != -1:
        text = text[:card_grid_start] + '    <div class="card-grid peds-home-card-grid" aria-hidden="true"></div>' + text[card_grid_end:]
    unit_js = hi_study_js(hi_study_parts) + f"""

const QUIZ_RESUME_KEY = STORAGE_PREFIX + 'quiz_resume_v1';
let currentQuizId = null;
let currentQuizAnswerVisible = false;

function safeQuizResumeState() {{
    try {{
        const raw = sessionStorage.getItem(QUIZ_RESUME_KEY);
        if (!raw) return null;
        const state = JSON.parse(raw);
        if (!state || state.version !== 1) return null;
        const validQueue = Array.isArray(state.queue) ? state.queue.filter(id => QUIZ_DATA[id]) : [];
        const validPending = Array.isArray(state.pending) ? state.pending.filter(item => item && QUIZ_DATA[item.id]) : [];
        const currentId = QUIZ_DATA[state.currentId] ? state.currentId : null;
        if (!currentId && validQueue.length === 0 && validPending.length === 0) return null;
        return {{...state, currentId, queue: validQueue, pending: validPending}};
    }} catch (err) {{
        console.warn('resume state parse failed', err);
        return null;
    }}
}}

function saveQuizResumeState() {{
    const hasCurrent = currentQuizId && QUIZ_DATA[currentQuizId];
    if (!hasCurrent && queue.length === 0 && pending.length === 0) {{
        clearQuizResumeState({{silent:true}});
        return;
    }}
    const state = {{
        version: 1,
        currentId: hasCurrent ? currentQuizId : null,
        answerVisible: Boolean(currentQuizAnswerVisible),
        queue: [...queue],
        pending: pending.map(item => ({{id:item.id, dueTime:Number(item.dueTime || 0)}})).filter(item => QUIZ_DATA[item.id]),
        bonusMode: Boolean(bonusMode),
        savedAt: Date.now()
    }};
    sessionStorage.setItem(QUIZ_RESUME_KEY, JSON.stringify(state));
    updateResumeQuizButton();
}}

function clearQuizResumeState(options = {{}}) {{
    sessionStorage.removeItem(QUIZ_RESUME_KEY);
    if (!options.silent) {{
        currentQuizId = null;
        currentQuizAnswerVisible = false;
        updateResumeQuizButton();
    }}
}}

function resumeQuizSession() {{
    const state = safeQuizResumeState();
    if (!state) {{ clearQuizResumeState(); return; }}
    bonusMode = Boolean(state.bonusMode);
    queue = [...state.queue];
    pending = [...state.pending].sort(sortByDueThenOrder);
    currentQuizId = state.currentId;
    currentQuizAnswerVisible = Boolean(state.answerVisible);
    closePedsMobileSidebar();
    document.body.classList.add('quiz-mode-active');
    document.getElementById('quizOverlay').classList.add('active');
    if (currentQuizId && QUIZ_DATA[currentQuizId]) {{
        const restoreAnswer = currentQuizAnswerVisible;
        renderQuizCard(currentQuizId);
        if (restoreAnswer) {{
            setTimeout(() => showQuizAnswer(currentQuizId), 40);
        }}
    }} else {{
        showNextCard();
    }}
    updateResumeQuizButton();
}}

function updateResumeQuizButton() {{
    const panel = document.getElementById('resumeQuizPanel');
    if (!panel) return;
    const state = safeQuizResumeState();
    if (!state || document.body.classList.contains('quiz-mode-active')) {{
        panel.hidden = true;
        return;
    }}
    const detail = document.getElementById('resumeQuizDetail');
    const title = document.getElementById('resumeQuizTitle');
    const currentLabel = state.currentId && QUIZ_DATA[state.currentId] ? 'Q' + QUIZ_DATA[state.currentId].num : '대기 중인 카드';
    const remain = (state.currentId ? 1 : 0) + state.queue.length + state.pending.length;
    if (title) title.textContent = currentLabel + '부터 퀴즈 이어하기';
    if (detail) detail.textContent = '남은 카드 ' + remain + '개 · ' + (state.answerVisible ? '정답 공개 상태까지 복원' : '문제 풀이 상태로 복원');
    panel.hidden = false;
}}

const OFFICIAL_UNIT_BY_ID = {json.dumps(unit_by_id, ensure_ascii=False)};
let selectedOfficialUnit = 'ALL';
function getOfficialUnitIds() {{
    return ALL_IDS.filter(id => selectedOfficialUnit === 'ALL' || OFFICIAL_UNIT_BY_ID[id] === selectedOfficialUnit);
}}
function updateOfficialUnitLauncher() {{
    const ids = getOfficialUnitIds();
    const label = selectedOfficialUnit === 'ALL' ? '전체' : selectedOfficialUnit;
    const labelEl = document.getElementById('selectedUnitLabel');
    const countEl = document.getElementById('selectedUnitCount');
    const orderedEl = document.getElementById('orderedStartCount');
    const randomEl = document.getElementById('randomStartCount');
    if (labelEl) labelEl.textContent = label;
    if (countEl) countEl.textContent = ids.length;
    if (orderedEl) orderedEl.textContent = ids.length;
    if (randomEl) randomEl.textContent = ids.length;
}}
function setOfficialUnitFilter(unit) {{
    selectedOfficialUnit = unit || 'ALL';
    document.querySelectorAll('.unit-filter-chip').forEach(btn => btn.classList.toggle('active', btn.dataset.unit === unit));
    document.querySelectorAll('.card[id^="card-"]').forEach(card => {{
        const id = card.id.replace(/^card-/, '');
        const chapter = OFFICIAL_UNIT_BY_ID[id] || '';
        card.classList.toggle('unit-hidden', unit !== 'ALL' && chapter !== unit);
    }});
    document.querySelectorAll('.sb-item').forEach(item => {{
        const m = String(item.getAttribute('onclick') || '').match(/scrollToCard[(]'([^']+)'[)]/);
        const chapter = m ? (OFFICIAL_UNIT_BY_ID[m[1]] || '') : '';
        item.classList.toggle('unit-hidden', unit !== 'ALL' && chapter !== unit);
    }});
    updateOfficialUnitLauncher();
}}
function closePedsMobileSidebar() {{
    const sb = document.getElementById('sidebar');
    const overlay = document.getElementById('sbOverlay');
    const btn = document.getElementById('sbMobileToggle');
    if (sb) sb.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('active');
    if (btn) btn.textContent = '☰';
}}
function startOfficialUnitOrdered() {{
    const ids = getOfficialUnitIds();
    if (!ids.length) return;
    closePedsMobileSidebar();
    startQuizWith(ids);
}}
function startOfficialUnitRandom() {{
    const ids = getOfficialUnitIds();
    if (!ids.length) return;
    closePedsMobileSidebar();
    startQuizWith(shuffledCopy(ids));
}}
document.addEventListener('DOMContentLoaded', () => {{
    setOfficialUnitFilter('ALL');
    updateResumeQuizButton();
}});
"""
    text = text.replace("// ── Card View Functions ──", unit_js + "\n// ── Card View Functions ──", 1)
    resume_patches = [
        ("function startQuizWith(ids, options = {}) {", "function startQuizWith(ids, options = {}) {\n    clearQuizResumeState({silent:true});\n    currentQuizId = null;\n    currentQuizAnswerVisible = false;"),
        ("    document.getElementById('quizOverlay').classList.add('active');\n    showNextCard();\n}", "    document.getElementById('quizOverlay').classList.add('active');\n    showNextCard();\n    saveQuizResumeState();\n}"),
        ("function exitQuiz() {\n    if (waitTimer) { clearInterval(waitTimer); waitTimer = null; }", "function exitQuiz() {\n    saveQuizResumeState();\n    if (waitTimer) { clearInterval(waitTimer); waitTimer = null; }"),
        ("    document.getElementById('quizOverlay').classList.remove('active');\n    updateReviewBtn();\n}", "    document.getElementById('quizOverlay').classList.remove('active');\n    updateReviewBtn();\n    updateResumeQuizButton();\n}"),
        ("function renderQuizCard(id) {\n    const data = QUIZ_DATA[id];", "function renderQuizCard(id) {\n    currentQuizId = id;\n    currentQuizAnswerVisible = false;\n    saveQuizResumeState();\n    const data = QUIZ_DATA[id];"),
        ("function showQuizAnswer(id) {\n    document.getElementById('quizAnswer').classList.add('visible');", "function showQuizAnswer(id) {\n    currentQuizId = id;\n    currentQuizAnswerVisible = true;\n    saveQuizResumeState();\n    document.getElementById('quizAnswer').classList.add('visible');"),
        ("function renderWaiting() {\n    if (waitTimer) { clearInterval(waitTimer); waitTimer = null; }", "function renderWaiting() {\n    currentQuizId = null;\n    currentQuizAnswerVisible = false;\n    saveQuizResumeState();\n    if (waitTimer) { clearInterval(waitTimer); waitTimer = null; }"),
        ("function renderComplete() {\n    const masteredIds = ALL_IDS.filter(id => srs[id] && srs[id].mastered);", "function renderComplete() {\n    currentQuizId = null;\n    currentQuizAnswerVisible = false;\n    clearQuizResumeState({silent:true});\n    const masteredIds = ALL_IDS.filter(id => srs[id] && srs[id].mastered);"),
    ]
    for old, new in resume_patches:
        if old not in text:
            raise RuntimeError(f"resume patch anchor missing: {old[:80]}")
        text = text.replace(old, new, 1)
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
