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
MANTRA = "홍수로비 디폴히피로히피디디폴 사맘, Tdap HPV"

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


QUESTION_CLEANUPS = {
    "actual1_004": "34주 여아, 2,000g. 태반조기박리 의심으로 응급 제왕절개 출생. 출생 직후 무호흡/축 늘어짐. 보온·건조·자극 후 생후 40초 HR 80/min. PPV 30초 후에도 HR<100이고, MRSOPA 교정 후에도 HR<100이다. 다음 처치는? 1) 자극주기 2) 기관삽관 3) 양압환기 4) 가슴압박 5) 에피네프린",
    "actual1_006": "24개월 남아가 아직 단어를 조합하여 문장을 만들지 못한다고 내원하였다. 이 환아에게서 자폐스펙트럼 장애를 감별하기 위해 '언어장애' 외에 반드시 확인해야 할 증상을 2가지 서술하시오.",
    "actual1_020": "정상 신생아는 대개 출생 후 몇 시간 이내 첫 소변을 보는가?",
    "actual1_025": "배꼽 부위가 돌출된 사진을 보고 진단명을 고르시오. 다른 선지: 배꼽탈출 / 배벽갈림증 / 선천성 횡격막 탈장 / 기타",
    "actual1_027": "생후 6개월부터 폐렴을 3차례 앓은 영아. Lateral pharyngeal X-ray에서 편도와 아데노이드가 보이지 않고, 총 혈청 면역글로불린 농도는 90 mg/dL이다. 진단과 치료는?",
    "actual1_028": "7세 여아가 경련으로 내원. 간이 늑골 밑 4횡지 만져지고, 혈당 감소와 간수치·총콜레스테롤·중성지방·젖산·요산 상승이 있다. Q1. 진단은? Q2. 유전 방식은?",
    "actual1_029": "37주, 3.7 kg으로 분만된 소아에서 경계가 불분명한 머리 부종이 관찰된다. 진단은?",
    "actual1_030": "38주 정상체중 출생아. 심박수 100회 미만, 호흡 약함, 움직임 약간, 코에 카테터를 넣었을 때 약간 반응, 몸통은 분홍색이나 손발은 청색이다. Apgar 점수는?",
    "actual1_034": "재태기간 28주, 출생 체중 750 g, 제왕절개로 태어난 아이. 출생 직후부터 청색증, 가슴벽뒤당김, 날숨 때 끙끙거림. 양쪽 호흡음 감소와 CXR total white-out 소견이 있다. 원인은?",
    "actual1_051": "35주, 2 kg으로 생후 3일 된 신생아에서 반복적인 미열, 청색증, 끙끙거림, 빈호흡이 있다. 산모는 분만 전 고열과 양막파열이 있었다. 우선적으로 해야 하는 치료는?",
    "actual1_053": "18개월 영유아검진 발달 선지 판단 문제. 복기된 선지: 혼자 걸을 수 있으나 잘 뛰지는 못한다 / 수평선은 그릴 수 있으나 원은 그리지 못한다. 원문 선지 통합이 필요하다.",
    "actual1_054": "18개월 발달 문항의 복기 조각. 복기된 선지: 단어 10개를 말할 수 있으나 간단한 문장은 말하지 못한다 / 원하는 것을 손가락으로 가리켜 달라고 할 수 있다. actual1_053과 같은 원문으로 보아야 한다.",
    "actual1_056": "5세 여아. 탈수와 저혈압이 있고 Lab 소견이 제시되었다. 진행해야 하는 치료는?",
    "actual1_057": "17세 여아가 6개월간 다이어트로 10 kg 감량한 뒤 비위관 삽입과 정맥영양을 시작하였다. 치료 3일 뒤 K 2.5, albumin 2.5 등 전해질/영양 이상이 보인다. 진단은?",
    "actual1_058": "임신 중 태내 성장이 예상되는 성장패턴보다 둔화되는 상태를 무엇이라고 하는가?",
    "actual1_059": "탈수로 온 소아가 수액 치료 중 경련을 보였다. 치료 전 Na 170, 치료 후 Na 130이었다. 경련의 원인과 치료는?",
    "actual1_060": "5세 남아가 5일 전부터 반복 구토와 하루 10회 정도의 묽은 변, 38도 이상 발열을 보인다. 주변인도 비슷한 증상을 호소한다. 가능성이 높은 병원균은?",
    "actual1_065": "11세 소아. 4년 전 급성림프구백혈병 진단 후 조혈모세포이식 없이 항암화학요법을 받고 완치. 6세까지 예방접종은 나이에 맞게 완료. 지금 적합한 예방접종은? 원문 선지 확인 필요.",
    "actual1_066": "다운증후군 남아의 핵형을 쓰시오.",
    "actual1_067": "37주, 3,000g 신생아. 황달과 간비대가 있고 광선치료 후 총빌리루빈 16. Coombs 결과가 제시되었다. 추가로 시행할 수 있는 치료는?",
    "actual1_068": "제1 성장급등기와 제2 성장급등기의 시기를 설명하시오.",
    "actual1_069": "18.8 kg 환아에게 복부초음파 검사를 위해 금식시키려 한다. 하루 필요한 수액량을 계산하여 수액 주입 속도를 구하시오.",
    "actual1_071": "Robertsonian translocation 21;21 산모에서 다음 아이가 다운증후군으로 태어날 확률은?",
    "actual1_074": "28+3주, 820 g으로 출생한 생후 4개월 남아의 손목 X-ray 사진이 제시되었다. 추정되는 진단명과 부족한 비타민은?",
    "actual1_075": "4세, 저신장, 익상경(webbed neck), 방패가슴이 있고 핵형검사에서 45,XO가 의심된다. 감별해야 하는 진단과 호발하는 심장 기형은?",
    "actual1_076": "재태연령 37주 5일, 2300 g 제왕절개 출생 남아. 출생 후 자발호흡이 없고 축 늘어져 보온, 기도 개방, 자극을 시행했다. 생후 40초 심박수 90회/분, 호흡 불규칙, 청색증이 있다. 처치는?",
    "actual1_081": "MMR 백신의 금기증을 2가지 이상 쓰시오.",
    "actual1_082": "모유 수유와 관련 있는 호르몬 2가지를 쓰시오.",
    "actual1_083": "당뇨가 있는 10세 여아가 무력감으로 내원하였다. 산증 상태이며 ABGA와 혈장 이온 수치가 제시되었다. Plasma anion gap 계산식을 쓰시오.",
    "actual1_084": "3개월간 TPN을 진행한 소아환자가 설사와 피부 증상을 보인다. 부족한 영양소는?",
    "actual1_085": "비장 절제술을 받을 예정인 소아가 수술 전에 필요한 예방접종은?",
    "actual1_088": "9세 소아가 비만으로 내원했다. 키 130 cm(25-50 백분위), 체중 45 kg(90-95 백분위), BMI 26.6(95백분위 초과)이다. 처치는?",
    "actual1_090": "소아 연령 단계를 6단계로 열거하시오.",
    "actual1_091": "소아 연령 구분 단계 문제의 복기 조각. 전체 단계를 완성하라.",
    "actual1_092": "소아 연령 구분 단계 문제의 복기 조각. 청소년기의 연령 범위를 묻는다.",
    "actual1_093": "고암모니아혈증에서 암모니아가 500을 초과하고 초기 내과처치에 반응하지 않는 경우 치료법은?",
    "actual1_095": "모유수유 금기 문항의 복기 조각이다. actual1_094와 같은 원문으로 보아야 한다.",
    "actual1_096": "8개월 여아. 6개월까지 예방접종은 모두 맞았으나 해외 생활로 BCG를 맞지 못했다. 처치는?",
    "actual1_097": "폐렴 치료 중 경련 발생, Na 120 mEq/L. 치료는? 1) 경구 NaCl 2) 3% saline 3) ...",
    "actual1_099": "신생아 소생술에서 가슴압박:환기 비율은? 1) 30:2 2) 15:2 3) 5:1 4) 3:1 5) 1:1",
    "actual1_100": "신경형 장기 설명. 두위는 몇 세에 성인의 몇 %까지 커지는가?",
    "actual1_101": "생후 6개월 이후 반복 폐렴, 편도/아데노이드 없음, 총 면역글로불린 감소가 보인다. 의심되는 질환과 치료는?",
    "actual1_102": "Prader-Willi syndrome과 Angelman syndrome에서 deletion과 uniparental disomy가 각각 부계/모계 중 어디에서 기인하는지 채워 넣으시오.",
    "actual1_103": "생후 10일 남아. 3일 전부터 양쪽 결막 충혈과 분비물이 있다. 가장 의심되는 병원균은?",
    "actual1_104": "기관삽관 후 폐포 계면활성제를 투여하고 수분에서 1시간 이후 발관한 뒤 nasal CPAP를 진행하는 방법을 무엇이라고 하는가?",
    "drill1_011": "산모가 항암치료 중이다. 모유수유 가능 여부는?",
}


ANSWER_DISPLAY_OVERRIDES = {
    "actual1_022": "생백신 접종 연기",
    "actual1_067": "복기상 교환수혈로 되어 있으나, 현재 제시 조건만으로는 IVIG가 우선. 교환수혈은 광선치료/IVIG 실패 또는 핵황달 위험/교환수혈 기준 이상일 때.",
    "actual1_069": "개념상 60 mL/hr. 복기상 57.6 mL/hr로 되어 있으나 100-50-20 rule로는 18.8 kg = 1000 + 440 = 1440 mL/day, 즉 60 mL/hr.",
    "actual1_042": "Fabry disease, Pompe disease",
    "actual1_043": "수액 중단/추가 crystalloid 중지로 추정 — 원문 선지 확인 필요",
    "actual1_053": "원문 통합 필요 — 18개월 발달 선지 전체를 보고 비정상 축을 골라야 함",
    "actual1_054": "파싱 조각 — actual1_053과 통합해서 판단",
    "actual1_065": "원문 선지 확인 필요 — 알렌 기준으로는 치료 종료/면역 회복 후 catch-up 접종을 검토, 11~12세 정기접종(Tdap/HPV 등)은 선지 의존",
    "actual1_077": "원문 수치 확인 필요 — 성장곡선에서 이탈한 항목, 특히 체중/성장부전 가능성을 우선 의심",
    "actual1_081": "MMR/생백신 금기: 임신, 백혈병/심한 면역억제(고용량 전신 스테로이드 포함), 최근 면역글로불린 또는 수혈 등",
    "actual1_095": "산모 항암치료 중 — 모유수유 금기(actual1_094와 같은 문항 조각)",
}


UNCERTAIN_IDS = {"actual1_043", "actual1_053", "actual1_054", "actual1_065", "actual1_067", "actual1_069", "actual1_077", "actual1_095"}


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def clean_question_text(card: dict) -> str:
    q = QUESTION_CLEANUPS.get(card.get("id"), card.get("question", ""))
    q = q.replace("(재시 문항)", "")
    q = q.replace("NaCL", "NaCl")
    q = q.replace("Digeorge", "DiGeorge")
    q = q.replace("ekg", "EKG")
    # Remove answer leakage from a few raw recall fragments.
    q = re.sub(r"\s*답\s*[:：]?\s*3%\s*saline\s*$", "", q, flags=re.I)
    q = re.sub(r"\s*답\s*4\s*$", "", q)
    return normalize_space(q)


def clean_answer_text(card: dict) -> str:
    answer = ANSWER_DISPLAY_OVERRIDES.get(card.get("id"), card.get("answer", ""))
    return normalize_space(answer)


def format_problem_html(text: str) -> str:
    out = e(text)
    # Put choices / Q1 / Q2 on separate lines for readability.
    out = re.sub(r"\s+(?=(?:[1-5]|①|②|③|④|⑤)[\)\.]\s*)", "<br>", out)
    out = re.sub(r"\s+(Q[12]\.)", r"<br>\1", out)
    out = out.replace(" 다른 선지)", "<br>다른 선지)")
    out = out.replace(" 선지:", "<br>선지:")
    return out


def answer_confidence(card: dict) -> tuple[str, str]:
    if card.get("id") in UNCERTAIN_IDS or card.get("origin") == "actual_incomplete" or dedup_key(card) in {"needs_source", "fragment_of"}:
        return "⚠️ 알렌 기준 추정", "복기 원문/선지가 불완전해서 확정 답처럼 외우면 위험합니다. 알렌 개념으로 가장 그럴듯한 방향을 표시했습니다."
    if str(card.get("qc_flag", "")).startswith("added_from_HI_all_Q_marker_sweep"):
        return "✅ HI Q marker 보존", "HI 1차 원문에서 객Q/주Q로 표시된 문항을 빠뜨리지 않도록 exact-source 카드로 보존했습니다."
    if card.get("qc_flag") == "added_from_2023_HI_full_audit":
        return "✅ 2023/HI source 추가", "2023 기출/HI raw 전수대조에서 빠진 exact stem을 추가했습니다."
    if card.get("origin") == "generated_drill":
        return "🧠 제작 drill", "actual 복기에서 뽑은 trigger를 변형한 drill입니다."
    return "✅ actual 기준", "복기 답을 알렌 개념틀로 재정렬했습니다."


def allen_rule(card: dict) -> str:
    gid = card.get("group_id", "") or ""
    axis = card.get("content_axis", "") or ""
    q = clean_question_text(card)
    a = clean_answer_text(card)
    hay = f"{gid} {axis} {q} {a}"

    if gid == "G-NUT-B12-ILEAL-RESECTION":
        return "비타민 B12는 terminal ileum에서 흡수된다. NEC 후 회장절제술 + MCV 112 같은 대구성 빈혈이면 채식 산모 문제가 아니어도 B12/cobalamin 결핍으로 잠근다."
    if gid == "G-VAX-VARICELLA-IVIG-CONTRAST" or ("수두" in hay and "IVIG" in hay):
        return "수두만이 아니라 MMR·수두 같은 생백신 전체는 최근 면역글로불린·혈액제제를 맞았으면 접종을 미룬다. 반대로 IVIG가 명시되지 않고 ITP가 회복되어 혈소판이 정상이라면 ITP 병력 자체만으로 생백신 금기는 아니다."
    if "G-NUT-FE" in gid or ("철" in a and ("MCV" in q or "이유식" in q)):
        return "생후 6개월 이후 저장철이 떨어지는데 모유 위주·이유식 부족·MCV 감소가 같이 보이면 철결핍을 먼저 본다."
    if "B12" in gid or "코발라민" in a or "cobalamin" in a:
        return "채식 산모 + 완전 모유수유 + 빈혈이면 모유 자체가 아니라 산모 저장량 부족에 의한 비타민 B12 결핍을 의심한다."
    if "ZINC" in gid or "아연" in a:
        return "TPN, 항암, 만성 설사 뒤 피부홍반·모발 변화가 나오면 아연 결핍이 시험장 trigger다."
    if "VITD" in gid or "구루병" in hay or "비타민 D" in a:
        return "구루병은 모유 위주 식이, 낮은 25-OH vitamin D, ALP/PTH 상승, 손목·다리 X-ray 변화가 같이 묶인다. 치료 축은 비타민 D 보충이다."
    if "Vit K" in a or "비타민 K" in a:
        return "신생아/태아 출혈과 응고인자 II, VII, IX, X를 떠올리면 비타민 K로 연결된다."
    if gid == "G-POST-VACCINE-FEVER-OBSERVE":
        return "예방접종 후 1~2일 발열이어도 잘 먹고 전신상태가 좋으며 피부색이 괜찮으면 우선 경과관찰이다. 항생제/면역글로불린/스테로이드는 중증 감염이나 특수 상황 단서가 있어야 간다."
    if "VAX" in gid or "예방접종" in axis or "MMR" in hay or "BCG" in hay:
        return "예방접종 문제는 ‘오늘 맞아도 되는가’를 생백신 간격, 임신, 면역저하, 최근 IVIG/수혈, 나이별 정기접종표 순서로 판정한다. 면역저하에는 백혈병/항암뿐 아니라 고용량 전신 스테로이드도 포함해서 본다."
    if "FLUID-NS" in gid or "중증탈수" in axis or "bolus" in a:
        return "중증 탈수 또는 순환부전의 첫 처치는 0.9% 생리식염수 20 mL/kg bolus다. 10 kg이면 200 mL, 12 kg이면 240 mL로 계산한다."
    if "HYPONA" in gid or "3% saline" in a:
        return "경련이 동반된 증상성 저나트륨혈증은 CT가 정상이어도 3% saline으로 뇌부종 위험을 먼저 끊는다."
    if "PSEUDOHYPERK" in gid:
        return "K 수치만 높고 EKG가 정상이며 채혈/수술 맥락이 있으면 가성 고칼륨혈증을 먼저 의심한다. 즉시 calcium을 주기보다 재확인/경과관찰이 답이 된다."
    if "FLUID-OVERLOAD" in gid:
        return "소변이 안 나온다고 계속 수액을 밀어 넣는 문제가 아니다. 수액 후 부종·음낭수종이 생기면 체액과다 또는 신장 handling 문제를 의심해 추가 crystalloid를 멈추는 쪽이 알렌식 추론이다."
    if card.get("id") == "actual1_069":
        return "유지수액은 100-50-20 rule로 계산한다. 18.8 kg이면 첫 10 kg은 1000 mL/day, 남은 8.8 kg은 8.8×50=440 mL/day라 총 1440 mL/day이고, 24시간으로 나누면 60 mL/hr다. 복기상 57.6 mL/hr는 계산과 맞지 않아 복기 답 의심으로 표시한다."
    if "MAINTENANCE" in gid:
        return "유지수액은 100-50-20 rule로 계산하고, 하루 총량을 24시간으로 나누어 mL/hr를 구한다."
    if "TPN-DAILY-WEIGHT" in gid:
        return "TPN 모니터링에서 매일 변화를 가장 직접적으로 보는 지표는 체중이다. 키·머리둘레는 매일 변하지 않고, 중성지방/암모니아는 상황별 검사이지 매일 기본 답으로 잠그는 항목은 아니다."
    if gid == "G-WILSON-TRIENTINE":
        return "간기능 저하에 ceruloplasmin과 serum copper가 낮게 제시되면 Wilson disease 축이다. 치료 선지에서는 구리 킬레이터인 trientine을 고른다."
    if "GSD" in gid or "당원병" in a:
        return "저혈당 + 젖산 + 요산 + 중성지방 상승에 간비대가 붙으면 당원병, 특히 glycogen storage disease bundle로 본다."
    if gid == "G-AD-INHERITANCE":
        return "상염색체 우성은 세대마다 나타나는 vertical transmission과 남녀 모두 가능하다는 점을 본다. 문제에서 AD 가계도라고 주면 답은 상염색체 우성이다."
    if gid == "G-HEMOPHILIA-XLINK":
        return "혈우병 A는 X-linked recessive다. 보인자 산모가 다시 남아를 임신하면 그 남아가 혈우병일 확률은 1/2로 잠근다."
    if "IMPRINTING" in gid or "imprinting" in hay:
        return "염색체 수보다 부모 어느 쪽에서 온 유전자인지가 표현형을 바꾸면 genetic imprinting이다. Prader-Willi/Angelman, Beckwith-Wiedemann 계열이 대표 trigger다."
    if "DOWN" in gid or "Turner" in hay or "ANEUPLOIDY" in gid:
        return "염색체 문제는 수적 이상인지, 전위인지, imprinting인지부터 가른다. Down 기본 핵형은 47,XY,+21이고 Robertsonian 21;21이면 재발 위험이 극단적으로 높다."
    if "HYPERAMMONEMIA" in gid or "암모니아" in hay:
        return "신생아 고암모니아혈증은 빠르게 산염기 상태를 확인하고, 암모니아가 매우 높거나 초기 내과치료에 반응하지 않으면 혈액투석으로 제거한다."
    if "ERT" in gid:
        return "효소보충요법은 lysosomal storage disease에서 묻는다. Fabry, Pompe, Gaucher는 가능하고 PKU/MSUD는 식이치료 축이다."
    if "MSUD" in gid:
        return "MSUD는 branched-chain amino acid 대사 문제라 전구물질 제한, 즉 식이치료가 핵심이다."
    if gid == "G-NRP-INITIAL-QUESTIONS":
        return "분만 직후 소생술 필요 여부는 세 질문으로 문을 연다. 만삭인가, 근긴장도가 좋은가, 울거나 숨을 잘 쉬는가. 셋 다 예면 routine care, 아니면 초기 처치/소생술로 간다."
    if gid == "G-NEONATAL-ASPHYXIA-DEF":
        return "신생아 가사는 산소 공급과 이산화탄소 제거가 안 되어 저산소혈증, 산혈증, 고탄산혈증이 생긴 상태다. 정의 문제에서는 이 세 단어를 같이 잠근다."
    if "NRP" in gid or "PPV" in a or "기관삽관" in a or "3:1" in a:
        return "신생아 소생술은 HR 100과 60 두 문으로 푼다. HR<100 또는 무호흡이면 PPV, PPV가 안 먹히면 MRSOPA, 그래도 HR<100이면 기관삽관, HR<60이면 가슴압박+환기다."
    if gid == "G-MECONIUM-OBSERVE":
        return "태변착색이 있어도 HR 140이고 호흡/근긴장/전신상태가 괜찮으면 삽관이나 NO가 아니라 경과관찰이다. 태변 자체보다 아이 상태가 스위치다."
    if "APGAR" in gid or "Apgar" in hay:
        return "Apgar는 심박수, 호흡, 근긴장도, 자극반응, 피부색 5항목을 각각 0~2점으로 더한다."
    if "IDM" in gid:
        return "당뇨 산모 아이는 고인슐린 상태로 태어나 저혈당, 저칼슘혈증, 다혈구증 등을 보일 수 있다. 선지에 저칼슘혈증이 있으면 강한 후보가 된다."
    if "BALLARD" in gid:
        return "최종월경일이 불확실하면 출생 후 신체/신경학적 성숙도를 묶어 New Ballard score로 재태연령을 추정한다."
    if "CAPUT" in gid:
        return "경계가 불분명하고 봉합선을 넘는 두피 부종은 산류다. 두혈종은 골막하 출혈이라 봉합선을 넘지 않는다."
    if "FIRST-URINE" in gid or "첫 소변" in hay:
        return "정상 신생아는 대부분 출생 후 24시간 이내 첫 소변을 본다."
    if gid == "G-BRONZE-BABY":
        return "광선치료 후 피부가 회갈색/청동색으로 변하면 bronze baby syndrome이다. 직접빌리루빈 증가나 담즙정체/폐쇄간질환과 연결되는 황달 합병증으로 묻는다."
    if card.get("id") == "actual1_067":
        return "Q67은 Q9/Q24와 같은 면역성 용혈 황달 축으로 보이지만, 지문에 광선치료/IVIG 실패, 핵황달 증상, 교환수혈 기준 초과가 충분히 제시되지 않았다. 현재 조건만 보면 Coombs 양성/면역성 용혈 + 광선치료 후 상승이므로 IVIG를 먼저 고려하고, 교환수혈은 더 강한 다음 단계로 둔다."
    if "JAUNDICE-IVIG" in gid:
        return "생후 초반 황달에서 Coombs 양성, 광선치료에도 빌리루빈 상승이면 면역성 용혈이다. 광선치료와 함께 IVIG를 고려한다."
    if "JAUNDICE-EXCHANGE" in gid:
        return "용혈 황달이 심하거나 광선치료/IVIG로 조절되지 않으면 핵황달 예방을 위해 교환수혈로 넘어간다."
    if "JAUNDICE-OBSERVE" in gid:
        return "생후 10일, 총빌리루빈이 높지 않고 직접빌리루빈/간수치가 괜찮으며 아이가 활발하면 저위험 모유황달 쪽이라 경과관찰과 수유 지속이 중심이다."
    if "JAUNDICE" in gid or "황달" in axis:
        return "신생아 황달은 생후 시점, 직접빌리루빈, Coombs, 상승 속도, 아이 상태로 병적 황달인지 먼저 가른다."
    if "EOS" in gid or "ampicillin" in a:
        return "산모 융모양막염 cue와 신생아 호흡곤란/발열이 같이 나오면 조기 신생아 패혈증으로 보고 ampicillin + gentamicin을 경험적으로 시작한다."
    if gid == "G-PNEUMOTHORAX-CHESTTUBE":
        return "인공호흡 중 갑작스런 호흡곤란, 한쪽 공기음영 증가, 가로막 하강, mediastinal shift는 기흉이다. 긴장성/증상성 기흉이면 가슴관 삽입으로 간다."
    if gid == "G-IVH-PRETERM":
        return "미숙아, RDS, 혈압 변동, 저산소 허혈, 기흉 뒤 갑작스런 무호흡·창백·근긴장 저하·경련·Hct 감소가 나오면 IVH, 즉 뇌실주위-뇌실내 출혈을 의심한다."
    if "RDS" in gid or "INSURE" in a or "폐표면활성제" in a:
        return "미숙아의 grunting, retraction, diffuse/white lung은 폐표면활성제 부족 RDS다. 삽관-계면활성제-조기발관-CPAP 흐름은 INSURE다."
    if "NEC" in gid or "금식" in a:
        return "미숙아가 수유 중 혈변, 복부팽만, 무호흡을 보이면 NEC를 의심하고 금식, 위장관 감압, 항생제로 시작한다."
    if gid == "G-CHLAMYDIA-EYE-PROPHYLAXIS":
        return "신생아 눈관리에서 erythromycin/tetracycline 점안은 Chlamydia 감염 예방 목적이다. 생후 10일 결막염 원인 문제와 예방 목적 문제를 분리해 외운다."
    if "CHLAMYDIA" in gid or "Chlamydia" in a:
        return "생후 5~14일 무렵 양측 결막염/분비물은 Chlamydia trachomatis를 우선 떠올린다."
    if gid == "G-IMMUNE-TESTS":
        return "세포성 면역은 T cell/subset, 지연 피부반응, 림프구 증식반응, thymus X-ray 쪽이고, 체액성 면역은 Ig 정량, isohemagglutinin, 특정 항체 생성능, B cell 측정 쪽이다."
    if "IMM-DIGEORGE" in gid:
        return "DiGeorge는 흉선 저형성/무형성 문제라 T cell, 즉 세포면역 이상이 핵심이다."
    if "XLA" in gid or "범저감마" in a:
        return "생후 6개월 이후 반복 세균감염, 편도/아데노이드 없음, Ig 감소는 B cell/항체 문제인 범저감마글로불린혈증으로 보고 IVIG를 반복 투여한다."
    if "IGM" in gid or a == "IgM":
        return "IgG는 태반을 통과하지만 IgM은 통과하지 못한다. 따라서 신생아 혈중 IgM 증가는 태아가 직접 만든 항체, 즉 선천감염 clue다."
    if "IMM" in gid or "면역결핍" in axis:
        return "면역결핍은 반복·중증·기회감염, 드문 균, 항생제 반응 불량, 성장부전을 red flag로 본다."
    if gid == "G-LANGUAGE-DELAY-DEF-CAUSE":
        return "언어발달지연은 언어가 나이에 맞는 수준에 도달하지 못한 상태다. 만 2세에도 말을 못 하면 강한 경고이고, 원인은 지적장애, 자폐증, 청력장애 등을 같이 적는다."
    if gid == "G-NEURO-BREATH-HOLDING":
        return "울거나 화난 뒤 청색증이 오고 짧은 강직 뒤 회복되는 toddler spell은 호흡중지발작이다. 발작수면이나 야경증이 아니라 감정 trigger와 빠른 회복이 문을 연다."
    if "DEV" in gid or "발달" in axis:
        return "발달 문제는 대근육, 소근육, 언어, 사회성 중 어느 축이 연령 기대치보다 가장 뒤처졌는지 고르는 방식으로 푼다."
    if "GROWTH" in gid or "성장" in axis:
        return "소아 성장 문제는 나이 단계, 성장곡선, 장기별 발육패턴을 좌표축으로 잡는다. 숫자만 외우지 말고 어떤 축이 벗어났는지 본다."
    if "BREAST" in gid or "모유" in axis:
        return "모유수유 문제는 금기인지, 산모 식이/약물 문제인지, 아이 증상 때문인지 나눈다. 산모 항암치료는 금기이고, 혈변만 있으면 우선 수유모 항원 제한을 생각한다."
    if "BSA" in gid:
        return "소아 약물 용량은 문제에서 체표면적 기준을 주면 BSA 기준을 우선 적용한다. BSA 1 m²이면 1500 mg/m²/day는 1500 mg/day다."
    if "PUBERTY" in gid:
        return "Tanner staging은 남아는 고환 용적, 여아는 유방 발달이 축이고, 남녀 공통으로 음모를 함께 본다."
    if "OBESITY" in gid:
        return "BMI가 95백분위 이상이면 소아 비만으로 보고 생활습관 교정과 체중감량 방향을 잡는다."
    if "UMBILICAL" in gid:
        return "배꼽 부위로 장이 튀어나오되 피부로 덮이고 제대륜 결손이면 배꼽탈장이다. 배벽갈림증/제대탈출과 사진 위치가 다르다."
    return f"알렌 기준으로는 '{axis or card.get('section', '해당 주제')}'의 trigger를 먼저 잡고, 선지보다 병태생리/나이/검사 패턴으로 답을 고른다."


def pitfall_line(card: dict) -> str:
    key = dedup_key(card)
    gid = card.get("group_id", "") or ""
    if card.get("id") == "actual1_069":
        return "복기상 57.6 mL/hr로 들어왔지만 18.8 kg 유지수액 계산식과 맞지 않는다. 100-50-20 rule 기준 개념상 우선답은 60 mL/hr로 보고 review-needed로 표시한다."
    if card.get("id") == "actual1_067":
        return "복기상 답은 교환수혈로 들어왔지만 Q9/Q24의 IVIG 카드와 concept conflict가 있다. 이 카드는 복기의심/review-needed로 보고 IVIG 우선, 교환수혈은 실패·핵황달·threshold 조건이 있을 때로 잠근다."
    if gid == "G-VAX-VARICELLA-IVIG-CONTRAST":
        return "수두만의 문제가 아니라 생백신 전체의 효과 문제다. ITP라는 단어보다 IVIG/혈액제제 투여 여부가 갈림길이다. actual1_002는 IVIG 명시가 없어 접종, actual1_022는 IVIG 명시가 있어 생백신 연기다."
    if key in {"duplicate", "near_duplicate"}:
        return "반복 출제 신호가 있는 카드다. 같은 답을 여는 trigger를 통째로 묶어 외운다."
    if key in {"same_topic_sibling", "variant_keep"}:
        return "비슷한 주제지만 trigger나 답의 축이 달라질 수 있으므로 무리하게 병합하지 않는다."
    if card.get("id") in UNCERTAIN_IDS:
        return "복기 정보가 불완전하므로 최종 시험장 암기는 원문 선지 확인 전까지 '추정'으로 둔다."
    return "선지 하나를 외우기보다, 문제에서 답을 여는 단서를 먼저 찾는다."


def explanation_lines(card: dict) -> list[tuple[str, str]]:
    if card.get("id") == "actual1_069":
        return [
            ("핵심 단서", "18.8 kg, 금식 중 유지수액 하루 필요량과 시간당 주입속도 계산"),
            ("계산", "100-50-20 rule: 첫 10 kg 1000 mL/day + 남은 8.8 kg×50 = 440 mL/day → 총 1440 mL/day"),
            ("판단", "1440 ÷ 24 = 60 mL/hr. 복기상 57.6 mL/hr는 계산식과 맞지 않아 복기 답 의심으로 표시한다."),
            ("주의", "체중이 18.8 kg 그대로라면 60 mL/hr가 개념상 우선답이다. 57.6은 체중/복기 오기 가능성이 있어 단독 정답으로 외우지 말 것."),
        ]
    if card.get("id") == "actual1_067":
        return [
            ("핵심 단서", "37주 신생아 황달+간비대, 광선치료 후 T-bil 16, Coombs 결과 제시"),
            ("Q9/Q24 비교", "Q9/Q24처럼 Coombs 양성/면역성 용혈 + 광선치료 후 상승 축이면 우선 IVIG를 고려한다."),
            ("알렌 기준", "교환수혈은 광선치료와 IVIG로 조절되지 않거나, 핵황달 증상/교환수혈 기준 이상처럼 더 강한 조건이 있을 때의 다음 단계다."),
            ("판단", "복기상 교환수혈로 되어 있으나 현재 제시 조건만으로는 IVIG가 우선이다. 이 카드는 복기의심/concept-conflict/review-needed로 표시한다."),
            ("주의", "교환수혈 단독 정답으로 외우지 말 것. IVIG 우선, 교환수혈은 실패·핵황달·threshold 조건이 있을 때."),
        ]
    confidence, note = answer_confidence(card)
    return [
        ("핵심 단서", card.get("content_axis") or clean_question_text(card)[:80]),
        ("알렌 기준", allen_rule(card)),
        ("판단", f"따라서 이 카드의 답은 {clean_answer_text(card)}입니다."),
        ("주의", f"{pitfall_line(card)} {note}"),
    ]


def explanation_html(card: dict) -> str:
    items = "".join(
        f'<li style="margin:7px 0;"><strong>{e(label)}:</strong> {e(text)}</li>'
        for label, text in explanation_lines(card)
    )
    return f'<ul style="padding-left:20px;margin:8px 0 0;line-height:1.72;">{items}</ul>'


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
    answer = clean_answer_text(card)
    question = clean_question_text(card)
    confidence, confidence_note = answer_confidence(card)
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
<section class="kmle-answer" style="display:flex;flex-direction:column;gap:12px;">
  <div style="border-left:4px solid #2563eb;background:#eff6ff;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#1d4ed8;margin-bottom:6px;letter-spacing:.04em;">문제</div>
    <div style="font-size:15px;line-height:1.72;color:#111827;">{format_problem_html(question)}</div>
  </div>

  <div style="border-left:4px solid #16a34a;background:#f0fdf4;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#15803d;margin-bottom:6px;letter-spacing:.04em;">답</div>
    <div class="answer-main" style="font-size:19px;line-height:1.55;color:#052e16;"><strong>{e(answer)}</strong></div>
    {f'<div style="margin-top:6px;color:#166534;font-size:13px;"><strong>정확 표현:</strong> {e(exact)}</div>' if exact and exact != answer else ''}
    <div style="margin-top:8px;font-size:12px;color:#475569;"><strong>{e(confidence)}</strong> · {e(confidence_note)}</div>
  </div>

  <div style="border-left:4px solid #f59e0b;background:#fffbeb;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#b45309;margin-bottom:6px;letter-spacing:.04em;">해설</div>
    {explanation_html(card)}
  </div>

  <details style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px 12px;color:#334155;">
    <summary style="cursor:pointer;font-weight:800;">출처 / 중복 정보</summary>
    <div class="answer-meta" style="margin-top:10px;">
      <span class="pill">{e(ORIGIN_LABELS.get(origin, origin))}</span>
      <span class="pill tier-{e(tier)}">{e(TIER_LABELS.get(tier, tier))}</span>
      <span class="pill">{e(TYPE_LABELS.get(typ, typ))}</span>
      {dedup}
    </div>
    <h4>출처</h4>
    <p><code>{e(card.get('source', '-'))}</code></p>
    {audit_block}
    <div class="tag-row">{tags_html(card.get('tags', []))}</div>
  </details>
</section>
""".strip()


def build_guide_html(card: dict) -> str:
    origin = card["origin"]
    answer = clean_answer_text(card)
    question = clean_question_text(card)
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
<section class="kmle-guide" style="line-height:1.7;">
  <h4>문제</h4>
  <p>{format_problem_html(question)}</p>
  <h4>답</h4>
  <p><strong>{e(answer)}</strong></p>
  <h4>해설</h4>
  {explanation_html(card)}
  <h4 style="margin-top:14px;">📌 문항 성격</h4>
  <table>
    <tr><th>Origin</th><td>{e(ORIGIN_LABELS.get(origin, origin))}</td></tr>
    <tr><th>Source</th><td>{e(card.get('source', '-'))}</td></tr>
    <tr><th>Mode</th><td>{e(card.get('mode', '-'))}</td></tr>
    <tr><th>Source No.</th><td>{e(card.get('num_in_source', '-'))}</td></tr>
    <tr><th>Section</th><td>{e(card.get('section', '-'))}</td></tr>
    <tr><th>Subsection</th><td>{e(card.get('subsection', '-') or '-')}</td></tr>
    {dedup_rows}
  </table>
  <p class="guide-note">실제 복기 문항과 HI 원문 Q marker 보강 카드를 함께 보존합니다. 제작 drill은 제거했고, HI 보강 카드는 중복 정도를 overlap badge로 표시합니다.</p>
</section>
""".strip()


def card_question_html(card: dict) -> str:
    origin = card["origin"]
    tier = card.get("priority_tier", "")
    typ = card.get("type", "")
    badge_html = (
        f'<span class="q-tier">{e(tier)}</span> '
        f'<span class="q-type">{e(ORIGIN_LABELS.get(origin, origin))}</span> '
        f'<span class="q-type">{e(TYPE_LABELS.get(typ, typ))}</span> '
        f'{dedup_pills_html(card, front=True)}'
    )
    return f"""
<div style="display:flex;flex-direction:column;gap:8px;width:100%;">
  <div style="font-size:11px;font-weight:900;color:#93c5fd;letter-spacing:.06em;">문제</div>
  <div style="font-size:14px;line-height:1.62;color:#e5e7eb;">{format_problem_html(clean_question_text(card))}</div>
  <div style="display:flex;gap:5px;flex-wrap:wrap;align-items:center;">{badge_html}</div>
</div>
""".strip()


def enrich_card_record(card: dict) -> dict:
    enriched = dict(card)
    enriched["display_question"] = clean_question_text(card)
    enriched["display_answer"] = clean_answer_text(card)
    enriched["explanation_lines"] = [{"label": label, "text": text} for label, text in explanation_lines(card)]
    enriched["answer_confidence"] = answer_confidence(card)[0]
    return enriched


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



def pretest_mantra_wall_html(class_name: str) -> str:
    pieces = [
        "홍수로비 디폴히피로히피디디폴 사맘, Tdap HPV",
        "홍수로비", "디폴히피로히피디디폴", "사맘", "Tdap HPV",
        "디폴히피로", "히피디디폴", "SAMAM", "12개월 히피+SAM", "4~6세 디폴+MMR", "11세 Tdap HPV",
    ]
    layouts = [
        (10,12,-16,1.05,.38,27),(36,9,9,.80,.28,18),(64,12,-7,.92,.30,22),(88,10,15,.78,.28,18),
        (12,28,11,.82,.28,18),(46,26,-12,1.08,.38,25),(78,28,18,.84,.30,18),
        (20,45,-25,.90,.30,19),(42,44,12,.78,.28,17),(67,46,-9,1.06,.38,24),(90,45,23,.78,.28,17),
        (9,64,18,.74,.24,16),(32,66,-8,1.04,.34,23),(58,64,6,.78,.26,17),(82,67,-18,1.08,.38,24),
        (15,84,-6,1.14,.40,24),(45,84,16,.82,.30,18),(72,86,-14,.88,.30,18),
    ]
    spans = []
    for i, (x, y, r, sc, op, fs) in enumerate(layouts):
        label = pieces[i % len(pieces)]
        spans.append(f'<span style="--x:{x}%;--y:{y}%;--r:{r}deg;--s:{sc};--o:{op};--fs:{fs}px">{e(label)}</span>')
    strings = []
    for x, y, r, w in [(20,35,-18,42),(56,37,13,35),(38,69,19,48),(74,72,-14,38),(51,52,-35,72)]:
        strings.append(f'<i style="--x:{x}%;--y:{y}%;--r:{r}deg;--w:{w}vw"></i>')
    return f'<div class="{class_name}" aria-hidden="true">' + ''.join(spans + strings) + '</div>'


def apply_pretest_background() -> None:
    """Add a text-only evidence-board mantra wall behind the 193-card pretest."""
    text = OUT.read_text(encoding="utf-8")
    mantra = e(MANTRA)
    css = f"""

/* Pediatric pretest text-only evidence-board cue */
body.peds-pretest-bg-body {{
    background:
        radial-gradient(circle at 12% 8%, rgba(37, 99, 235, .22), transparent 32%),
        radial-gradient(circle at 86% 14%, rgba(220, 38, 38, .18), transparent 30%),
        linear-gradient(135deg, #111827 0%, #1f2937 48%, #0f172a 100%) !important;
}}
body.peds-pretest-bg-body::before {{
    content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image:
        linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.028) 1px, transparent 1px);
    background-size: 44px 44px, 44px 44px; opacity: .55;
}}
.peds-pretest-mantra-wall {{ position: fixed; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }}
.peds-pretest-mantra-wall span {{
    position: absolute; left: var(--x); top: var(--y);
    transform: translate(-50%, -50%) rotate(var(--r)) scale(var(--s));
    opacity: var(--o); color: #dbeafe; background: rgba(15, 23, 42, .56);
    border: 1px solid rgba(191, 219, 254, .30); border-radius: 6px; padding: 4px 10px;
    font-size: var(--fs); font-weight: 1000; letter-spacing: .06em; white-space: nowrap;
    text-transform: uppercase; font-family: Impact, Haettenschweiler, 'Arial Black', system-ui, sans-serif;
    text-shadow: 0 2px 10px rgba(0,0,0,.58); box-shadow: 0 8px 22px rgba(0,0,0,.20);
}}
.peds-pretest-mantra-wall span:nth-child(3n) {{ color: #fecaca; border-color: rgba(248, 113, 113, .34); background: rgba(127, 29, 29, .20); }}
.peds-pretest-mantra-wall span:nth-child(4n) {{ color: #bbf7d0; border-color: rgba(74, 222, 128, .32); background: rgba(20, 83, 45, .20); }}
.peds-pretest-mantra-wall i {{
    position: absolute; left: var(--x); top: var(--y); width: var(--w); height: 2px;
    transform: translate(-50%, -50%) rotate(var(--r)); background: rgba(239, 68, 68, .42);
    box-shadow: 0 0 8px rgba(248, 113, 113, .34);
}}
body.peds-pretest-bg-body .sidebar {{ position: fixed; }}
body.peds-pretest-bg-body .main, body.peds-pretest-bg-body .quiz-header {{ position: relative; z-index: 1; }}
body.peds-pretest-bg-body .quiz-overlay {{ position: fixed; z-index: 200; }}
body.peds-pretest-bg-body .card, body.peds-pretest-bg-body .quiz-card {{ position: relative; overflow: hidden; box-shadow: 0 18px 44px rgba(2, 6, 23, .24); }}
body.peds-pretest-bg-body .card::before, body.peds-pretest-bg-body .quiz-card::before {{
    content: '{mantra}'; position: absolute; left: 0; right: 0; top: 0; padding: 5px 12px;
    background: linear-gradient(90deg, rgba(30, 64, 175, .92), rgba(16, 185, 129, .82));
    color: #eff6ff; font-size: 11px; font-weight: 900; letter-spacing: .04em; text-align: center; z-index: 2;
}}
body.peds-pretest-bg-body .card .card-header, body.peds-pretest-bg-body .quiz-card {{ padding-top: 34px !important; }}
.peds-pretest-mantra-ribbon {{
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 9999; padding: 7px 10px;
    background: rgba(15, 23, 42, .86); color: #bfdbfe; border-top: 1px solid rgba(147, 197, 253, .35);
    font-size: 12px; font-weight: 950; letter-spacing: .08em; white-space: nowrap; overflow: hidden; text-align: center;
}}
body.peds-pretest-bg-body .quiz-answer::after {{
    content: '{mantra}'; display: block; margin-top: 14px; padding: 8px 10px; border-radius: 10px;
    background: #dbeafe; color: #1e3a8a; font-weight: 950; text-align: center;
}}
"""
    ribbon = f'<div class="peds-pretest-mantra-ribbon">{mantra} · {mantra} · {mantra}</div>'
    wall = pretest_mantra_wall_html("peds-pretest-mantra-wall")
    text = text.replace("</style>", css + "\n</style>", 1)
    text = text.replace("<body>", '<body class="peds-pretest-bg-body">\n' + wall + "\n" + ribbon, 1)
    OUT.write_text(text, encoding="utf-8")


def main() -> None:
    actual = load_actual_cards()
    generated = []  # 강렬 지시: 제작 drill 문제는 제거하고 actual/HI source card만 유지한다.
    combined = [enrich_card_record(c) for c in actual + generated]
    COMBINED_DATA.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = build_cards(combined)
    builder = QuizBuilder(
        cards=cards,
        title=TITLE,
        storage_prefix=STORAGE_PREFIX,
        enable_self_answer=False,
        randomize_review=True,
    )
    builder.write(str(OUT))
    apply_pretest_background()
    print(f"actual_cards: {len(actual)}")
    print(f"generated_drill_cards: {len(generated)}")
    print(f"total_cards: {len(cards)}")
    print(f"combined_data: {COMBINED_DATA}")
    print(f"out: {OUT}")
    print(f"storage_prefix: {STORAGE_PREFIX}_")


if __name__ == "__main__":
    main()
