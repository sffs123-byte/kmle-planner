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
YAMA_MIXED_20260518 = DATA_DIR / "pediatrics_pretest2_yama_mixed_20260518.json"

# 2026-05-18 full source audit: 2025 cumulative/raw leftovers that were
# not represented as exact cards in the FULL deck.  These are intentionally
# kept separate from CORE79/V3_2025 so the generator remains the source of truth.
RAW_2025_LEFTOVER_CARDS = [
    {
        "id": "PEDS2-2025RAW-2528-Q1-RFCA",
        "source": "2025 cumulative 2차 raw source / 25~28조 객관식 1번",
        "origin": "actual_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 심혈관",
        "question": "14세 남아가 컴퓨터 게임을 하다가 심박수가 빠르다고 내원했다. 치료는?\n① 경과관찰 ② ICD ③ flecainide로 추정되는 항부정맥제 ④ cardiac resynchronization therapy ⑤ RFCA",
        "answer": "RFCA",
        "explanation": "2025 raw source에 보기와 정답축이 남아 있으나 기존 FULL deck에는 RFCA exact card가 없었다. 증상성/반복성 SVT 계열에서 근치적 치료 선택지는 전극도자절제술(RFCA)이다.",
        "enhanced_explanation": """🧭 Big picture\n소아·청소년이 갑자기 심박수가 빨라져 내원하고 선택지에 RFCA가 있으면, 단순 빈맥보다 재발성 SVT/PSVT의 근치 치료 축을 생각한다. 약물로 급성 발작을 끊는 문제와, 반복 발작의 definitive treatment를 묻는 문제를 구분해야 한다.\n\n🔎 핵심 단서\n⭕ 14세 청소년\n⭕ 게임 중 갑작스러운 빠른 심박수\n⭕ 보기 중 RFCA 존재\n⭕ ICD/CRT는 구조적 심질환·심부전/치명성 부정맥 축이라 이 stem과 다름\n\n👣 시험장 사고 흐름\n1단계: 단순 sinus tachycardia인지 발작성 빈맥인지 본다.\n2단계: 치료 보기 중 급성 종료인지 근치 치료인지 구분한다.\n3단계: 반복/증상성 SVT 맥락이면 RFCA를 고른다.\n\n📊 감별/오답 제거\n| 보기 | 왜 아님/맞음 |\n| 경과관찰 | 증상성 빠른 심박으로 치료 질문이면 약함 |\n| ICD | 심정지/악성 심실성 부정맥 예방 장치 |\n| CRT | 심부전 동기화 치료 |\n| RFCA | ✅ SVT/PSVT 계열의 definitive treatment |\n\n✅ 3초 Lock line\n청소년 발작성 빈맥 + definitive treatment 보기 = RFCA.""",
        "tags": ["심혈관", "부정맥", "SVT", "PSVT", "RFCA", "2025-leftover"],
        "uncertain": False,
        "raw_anchor": "14세 남아가 컴퓨터 게임을 하다가 심박수가 빠르다고 내원함. 치료는? ... 5. RFCA",
    },
    {
        "id": "PEDS2-2025RAW-2932-Q2-AVF",
        "source": "2025 cumulative 2차 raw source / 29~32조 객관식 2번",
        "origin": "uncertain_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 심혈관",
        "question": "29~32조 객관식 2번은 원문에 지문이 거의 남지 않고 '답은 동정맥루'라고만 복기되어 있다. 이 문항의 복기 정답은?",
        "answer": "동정맥루",
        "explanation": "raw source가 지문을 보존하지 못하고 답만 남긴 문항이다. 기존 deck에는 동정맥루 exact card가 없어서, 원문 누락 방지용 답보존 카드로 추가했다.",
        "enhanced_explanation": """🧭 Big picture\n이 카드는 완전한 문제 풀이용이라기보다 raw source에 남아 있던 답을 잃지 않기 위한 보존 카드다. 원문에는 '답은 동정맥루'만 남아 있어 stem 재구성은 과장하지 않는다.\n\n🔎 핵심 단서\n⭕ 2025 cumulative raw source\n⭕ 29~32조 객관식 2번\n⭕ 지문 미복기\n⭕ 답만 동정맥루로 기록\n\n⚠️ 함정\nstem이 없으므로 다른 동정맥 질환으로 확대 해석하지 않는다. 실제 문제 이미지/원문을 찾으면 이 카드는 정확한 stem으로 교체한다.\n\n✅ 3초 Lock line\nraw에 답만 남은 29~32조 객2 = 동정맥루.""",
        "tags": ["심혈관", "동정맥루", "raw-answer-only", "2025-leftover"],
        "uncertain": True,
        "raw_anchor": ", 답은 동정맥루",
    },
    {
        "id": "PEDS2-2025RAW-2932-Q3-HPS-FLUID",
        "source": "2025 cumulative 2차 raw source / 29~32조 객관식 3번",
        "origin": "actual_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 소화기",
        "question": "HPS, 즉 비대날문협착증에서 수술 전 탈수·대사성 알칼리증·전해질 이상을 교정하기 위한 수액치료 조합은?",
        "answer": "0.45~0.5% 식염수 + 5~10% dextrose + KCl 30~50 mEq/L",
        "explanation": "raw source와 HI 소화기 정리 모두 HPS 수술 전 교정 수액으로 0.45~0.5% 식염수 + 5~10% dextrose + KCl 30~50 mEq/L를 제시한다.",
        "enhanced_explanation": """🧭 Big picture\n비대날문협착증은 바로 수술방으로 밀어 넣는 병이 아니다. 반복적인 비담즙성 구토 때문에 탈수, 저염소성 대사성 알칼리증, 저칼륨혈증이 생길 수 있어서 먼저 수액과 전해질을 교정한 뒤 날문근육절개술로 간다.\n\n🔎 핵심 단서\n⭕ HPS, projectile vomiting, olive mass 축\n⭕ 수술 전 교정\n⭕ 탈수·산염기·전해질 이상\n⭕ raw 정답: 0.45~0.5% 식염수 + 5~10% dextrose + KCl 30~50 mEq/L\n\n👣 시험장 사고 흐름\n1단계: HPS는 구토로 탈수와 알칼리증이 먼저 문제다.\n2단계: 수술은 definitive지만, 먼저 교정한다.\n3단계: dextrose, saline, KCl 조합을 고른다.\n\n📊 감별/오답 제거\n| 상황 | 처치 |\n| HPS 진단 직후 탈수/알칼리증 | ✅ 수액·전해질 교정 |\n| 교정 후 definitive treatment | 날문근육절개술 |\n| 즉시 수술만 선택 | 수술 전 교정 생략이라 위험 |\n\n✅ 3초 Lock line\nHPS는 수술 전 0.45~0.5% 식염수 + 5~10% dextrose + KCl로 교정.""",
        "tags": ["소화기", "HPS", "비대날문협착증", "수액", "전해질", "2025-leftover"],
        "uncertain": False,
        "raw_anchor": "HPS 수액치료 문제 / 0.45-0.5% 식염수 + 5-10% dextrose +KCl 30-50mEq/L",
    },
    {
        "id": "PEDS2-2025RAW-2932-SA2-EISENMENGER-NOT",
        "source": "2025 cumulative 2차 raw source / 29~32조 주관식 2번",
        "origin": "actual_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 심혈관",
        "question": "Eisenmenger syndrome으로 빠르게 진행하는 경우가 아닌 것은?\n① 방실중격결손 ② 완전대혈관전위 + 심실중격결손 ③ 대동맥폐동맥개창 ④ 다운증후군 ⑤ CATCH22/DiGeorge syndrome",
        "answer": "⑤ CATCH22/DiGeorge syndrome",
        "explanation": "기존 deck에는 '빠르게 진행하는 경우 5가지' 카드만 있었고, raw source의 polarity인 '아닌 것' 문제는 exact로 없었다. 빠른 Eisenmenger 진행은 큰 post-tricuspid shunt/대혈관 수준 shunt와 Down syndrome에서 중요하며, CATCH22는 TOF 등 원추동맥간 심기형 연관은 있지만 이 목록의 빠른 진행 항목은 아니다.",
        "enhanced_explanation": """🧭 Big picture\nEisenmenger로 빨리 가는 건 폐혈관이 어릴 때부터 큰 압력·큰 혈류에 오래 맞는 상황이다. 그래서 큰 좌우단락, 대혈관 수준 단락, Down syndrome이 고위험으로 묶인다. 문제는 '아닌 것'을 물었으므로, 빠르게 진행하는 목록에 들어가지 않는 CATCH22를 골라야 한다.\n\n🔎 핵심 단서\n⭕ '빠르게 진행하는 경우가 아닌 것'\n⭕ AVSD, TGA+VSD, aortopulmonary window, Down syndrome은 빠른 진행 축\n⭕ CATCH22/DiGeorge는 conotruncal anomaly 연관이지 빠른 Eisenmenger 진행 목록 자체는 아님\n\n👣 시험장 사고 흐름\n1단계: 문제 polarity를 먼저 확인한다: 아닌 것.\n2단계: 큰 단락/폐혈류 과다 항목을 제거한다.\n3단계: 남는 syndrome association인 CATCH22를 답으로 잡는다.\n\n📊 감별/오답 제거\n| 보기 | 판정 |\n| 방실중격결손 | 빠른 진행 가능 |\n| TGA + VSD | 빠른 진행 가능 |\n| 대동맥폐동맥개창 | 빠른 진행 가능 |\n| Down syndrome | 빠른 진행 위험 증가 |\n| CATCH22/DiGeorge | ✅ 아닌 것 |\n\n✅ 3초 Lock line\nEisenmenger 빠른 진행 '아닌 것' = CATCH22.""",
        "tags": ["심혈관", "Eisenmenger", "선천심질환", "CATCH22", "polarity", "2025-leftover"],
        "uncertain": False,
        "raw_anchor": "Eisenmenger syndrome으로 빠르게 진행하는 경우가 아닌 것은? ... 5. catch 22",
    },
    {
        "id": "PEDS2-2025RAW-2932-SA5-CRE-RISK",
        "source": "2025 cumulative 2차 raw source / 29~32조 주관식 5번 컨퍼런스",
        "origin": "actual_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 감염관리",
        "question": "CRE 감염 위험인자 3가지는?",
        "answer": "중환자실 입원, 장기간/반복적 광범위 항생제 사용, 중심정맥관·도뇨관·기관내관 등 침습적 의료기구 사용",
        "explanation": "raw source에는 문제만 있고 답은 없었으나, 사용자 제공 정리 이미지의 답과 감염관리 일반 원칙을 반영해 3개 축으로 정리했다.",
        "enhanced_explanation": """🧭 Big picture\nCRE는 carbapenem-resistant Enterobacteriaceae다. 위험인자는 '병원 안에서 오래, 항생제를 많이, 관을 많이'로 잡으면 된다. 즉 중환자실/장기입원, 광범위 항생제 노출, 침습적 의료기구가 핵심 3축이다.\n\n🔎 핵심 단서\n⭕ CRE 감염 위험 3가지\n⭕ 중환자실 입원 또는 장기 입원\n⭕ 장기간/반복적 광범위 항생제 사용\n⭕ 중심정맥관, 도뇨관, 기관내관 등 침습적 기구\n\n👣 시험장 사고 흐름\n1단계: CRE는 병원획득/의료관련감염 축으로 본다.\n2단계: colonization selection pressure는 항생제 사용.\n3단계: 침입 경로와 biofilm은 의료기구.\n4단계: 고위험 환경은 ICU/장기입원.\n\n📊 감별/오답 제거\n| 축 | 예시 |\n| 환경 | ICU, 장기입원, 요양병원/의료기관 노출 |\n| 선택압 | carbapenem 포함 광범위 항생제 장기 사용 |\n| 침입 경로 | CVC, Foley, E-tube, ventilator 등 |\n\n✅ 3초 Lock line\nCRE 위험 = ICU/장기입원 + 장기 항생제 + 침습적 기구.""",
        "tags": ["감염", "감염관리", "CRE", "의료관련감염", "컨퍼런스", "2025-leftover"],
        "uncertain": False,
        "raw_anchor": "5번(컨퍼런스 문제) CRE 감염 위험 3가지",
    },
    {
        "id": "PEDS2-2025RAW-3336-Q3-WHEEZE-SABA",
        "source": "2025 cumulative 2차 raw source / 33~36조 객관식 3번",
        "origin": "actual_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 호흡기",
        "question": "발열, 기침, 콧물이 있고 알레르기 가족력은 없으며 양측 폐야 천명음이 들린다. 다음 처치/약제로 가장 적절한 것은?\n① 진정제 ② 수액 ③ 스테로이드 ④ 항생제 ⑤ SABA",
        "answer": "⑤ SABA",
        "explanation": "기존 FULL deck에는 SABA 개념카드는 있었지만, raw source의 exact stem은 빠져 있었다. wheezing이 두드러진 하기도 폐쇄/천명 상황에서 보기 중 우선 고르는 약제는 흡입 속효성 β2 agonist(SABA)다.",
        "enhanced_explanation": """🧭 Big picture\n소아 wheezing 문제는 먼저 '공기가 좁아진 기도를 지나며 나는 소리'로 이해한다. 원인이 바이러스성이든 천식성이든 보기에서 기관지를 빨리 열어주는 약제를 묻는다면 SABA가 가장 직접적인 선택지다.\n\n🔎 핵심 단서\n⭕ 양측 폐야 천명음\n⭕ 호흡기 증상: 발열, 기침, 콧물\n⭕ 보기 중 기관지확장제는 SABA\n⭕ 진정제/항생제/수액/스테로이드는 이 stem의 즉답축이 아님\n\n👣 시험장 사고 흐름\n1단계: wheezing을 확인한다.\n2단계: 현재 막힌 기도를 열어야 하는지 본다.\n3단계: 보기에서 SABA가 있으면 우선 선택한다.\n\n📊 감별/오답 제거\n| 보기 | 판단 |\n| 진정제 | 호흡 억제 위험, 천명 치료 아님 |\n| 수액 | 탈수/세기관지염 보조치료 축 |\n| 스테로이드 | 천식 악화 보조 가능하지만 즉각 기관지확장은 SABA |\n| 항생제 | 세균성 감염 근거 부족 |\n| SABA | ✅ wheezing 즉시 완화 |\n\n✅ 3초 Lock line\n소아 wheezing + 보기 중 SABA = 기도 먼저 열어라.""",
        "tags": ["호흡기", "천명", "wheezing", "SABA", "기관지확장제", "2025-leftover"],
        "uncertain": False,
        "raw_anchor": "발열, 기침, 콧물, 알레르기 가족력은 없음, 양측 폐야 천명음 ... 5. SABA",
    },
    {
        "id": "PEDS2-2025RAW-3336-SA5-CRRT-INDICATION",
        "source": "2025 cumulative 2차 raw source / 33~36조 주관식 5번 의국회의",
        "origin": "actual_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 신장/응급",
        "question": "CRRT indication 3가지는?",
        "answer": "이뇨제에 반응하지 않는 체액과다/폐부종, 조절되지 않는 고칼륨혈증 등 중증 전해질 이상, 중증 대사성 산증 또는 요독증/AKI. 혈역학적으로 불안정해 간헐적 혈액투석이 어려운 경우 CRRT를 선택한다.",
        "explanation": "raw source에는 'crrt indication 3개'만 있고 답은 없었다. 카드화에서는 시험에서 쓰기 좋은 3축: fluid overload, refractory electrolyte problem, severe acidosis/uremia/AKI로 정리했다.",
        "enhanced_explanation": """🧭 Big picture\nCRRT는 continuous renal replacement therapy다. 핵심은 '신장이 못 해서 몸 안에 물·전해질·산이 쌓이는데, 환자가 불안정해서 천천히 지속적으로 빼야 하는 상황'이다. 그래서 indication은 일반 투석 적응증을 CRRT 방식으로 바꾼다고 생각하면 쉽다.\n\n🔎 핵심 단서\n⭕ 이뇨제 불응 체액과다, 폐부종\n⭕ 조절되지 않는 고칼륨혈증 등 중증 전해질 이상\n⭕ 중증 대사성 산증\n⭕ 요독증/AKI, 필요 시 독소 제거\n⭕ 혈역학 불안정하면 intermittent HD보다 CRRT 선호\n\n👣 시험장 사고 흐름\n1단계: 물이 너무 많나? fluid overload.\n2단계: 전해질이 위험한가? 특히 hyperkalemia.\n3단계: 산이 쌓였나? severe metabolic acidosis.\n4단계: uremia/AKI가 있고 환자가 불안정하면 CRRT로 간다.\n\n📊 감별/오답 제거\n| 축 | 예시 |\n| Volume | 폐부종, fluid overload, diuretic failure |\n| Electrolyte | refractory hyperkalemia |\n| Acid-base/uremia | severe acidosis, uremic complication, severe AKI |\n\n✅ 3초 Lock line\nCRRT 적응증 = 물 과다, K/전해질, 산증/요독증을 불안정 환자에서 천천히 빼야 할 때.""",
        "tags": ["범위외/확인", "신장", "CRRT", "AKI", "전해질", "컨퍼런스", "2025-leftover"],
        "uncertain": True,
        "raw_anchor": "주5) (의국회의) crrt indication 3개",
    },
    {
        "id": "PEDS2-2025RAW-3740-Q1-LEFT-BRONCHUS-OBSTRUCTION",
        "source": "2025 cumulative 2차 raw source / 37~40조 객관식 1번",
        "origin": "actual_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 호흡기",
        "question": "CXR에서 왼쪽 폐 음영이 저하되어 있는 사진이 제시되었다. 문제가 되는 위치는?",
        "answer": "왼쪽 기관지 폐쇄",
        "explanation": "raw source에 '왼쪽 폐 음영 저하 CXR → 왼쪽 기관지 폐쇄'로 복기되어 있었으나 existing FULL deck에는 exact card가 없었다.",
        "enhanced_explanation": """🧭 Big picture\n한쪽 폐가 더 검게, 즉 과투과성으로 보이면 공기가 그쪽에 갇힌 ball-valve obstruction을 떠올린다. 소아에서는 이물흡인이나 기관지 폐쇄가 대표적이다. raw source는 왼쪽 폐 음영 저하 CXR의 정답을 왼쪽 기관지 폐쇄로 기록했다.\n\n🔎 핵심 단서\n⭕ CXR 한쪽 폐 음영 저하/과투과성\n⭕ 왼쪽 폐가 더 검게 보임\n⭕ 위치를 묻는 문제\n⭕ raw 정답: 왼쪽 기관지 폐쇄\n\n👣 시험장 사고 흐름\n1단계: 한쪽 폐가 더 검은지 본다.\n2단계: 공기 trapping을 생각한다.\n3단계: 해당 쪽 기관지 폐쇄를 답한다.\n\n📊 감별/오답 제거\n| CXR 패턴 | 해석 |\n| 한쪽 과투과성 | 기관지 폐쇄/이물흡인에 의한 air trapping |\n| 한쪽 완전 백색화 | 무기폐, 폐렴, 흉수 등 감별 |\n| 양측 과팽창 | 천식/세기관지염 등 전반적 하기도 폐쇄 |\n\n✅ 3초 Lock line\n왼쪽 폐가 과투과성으로 검다 = 왼쪽 기관지 폐쇄.""",
        "tags": ["호흡기", "CXR", "기관지폐쇄", "이물흡인", "air_trapping", "2025-leftover"],
        "uncertain": False,
        "raw_anchor": "왼쪽 폐 음영 저하되어있는 CXR ... 왼쪽 기관지 폐쇄",
    },
    {
        "id": "PEDS2-2025RAW-3740-Q2-PULMONIC-CONUS-BULGING",
        "source": "2025 cumulative 2차 raw source / 37~40조 객관식 2번",
        "origin": "actual_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 심혈관",
        "question": "CXR가 제시되었다. 다음 흉부 X선 소견은?",
        "answer": "Pulmonic conus bulging",
        "explanation": "existing deck에는 PS 진단 카드가 있지만, raw source의 exact CXR 소견명 'Pulmonic conus bulging'을 묻는 카드는 없어서 추가했다.",
        "enhanced_explanation": """🧭 Big picture\n심장 CXR에서는 진단명뿐 아니라 실루엣 소견명을 묻는 문제가 나온다. Pulmonic conus bulging은 좌상부 심장 윤곽, 즉 주폐동맥 부위가 돌출되어 보이는 소견이다. 폐동맥판협착 등 우심실 유출로/폐동맥 축 문제와 연결된다.\n\n🔎 핵심 단서\n⭕ CXR 소견명을 묻는 문제\n⭕ raw 답: Pulmonic conus bulging\n⭕ 유사 카드의 진단축은 PS이지만, 이 카드는 소견명 자체를 묻는다\n\n👣 시험장 사고 흐름\n1단계: 사진 문제에서 진단명인지 소견명인지 확인한다.\n2단계: 좌상부 심장 윤곽/주폐동맥 부위 돌출이면 pulmonic conus bulging.\n3단계: 진단 연결은 PS 등으로 회수한다.\n\n✅ 3초 Lock line\nCXR 주폐동맥 부위 돌출 소견명 = pulmonic conus bulging.""",
        "tags": ["심혈관", "CXR", "Pulmonic_conus", "PS", "폐동맥", "2025-leftover"],
        "uncertain": False,
        "raw_anchor": "다음 CXR의 소견은? Pulmonic conus bulging",
    },
    {
        "id": "PEDS2-2025RAW-3740-SA5-ANOREXIA-BIOCHEM",
        "source": "2025 cumulative 2차 raw source / 37~40조 주관식 5번 컨퍼런스",
        "origin": "actual_recall",
        "priority": "P3 누적복기",
        "section": "2025 raw leftovers · 영양/정신",
        "question": "Anorexia nervosa에서 나타나는 생화학적 변화 4가지 이상은?",
        "answer": "저칼륨혈증, 저염소혈증/대사성 알칼리증, 저혈당, 저인산혈증 또는 저마그네슘혈증, 탈수에 따른 BUN 상승, 저T3/euthyroid sick pattern, 고콜레스테롤혈증 등이 가능하다.",
        "explanation": "raw source에는 질문만 있고 답은 없었다. 소아청소년 식이장애/재급식 위험에서 자주 쓰는 전해질·대사 이상을 4개 이상 쓸 수 있게 정리했다.",
        "enhanced_explanation": """🧭 Big picture\nAnorexia nervosa의 lab은 '굶음 + 구토/하제 + 탈수 + 재급식 위험'으로 이해하면 된다. 굶으면 저혈당, 저T3 패턴이 오고, 구토/하제는 전해질 이상을 만든다. 재급식이 시작되면 특히 저인산혈증을 조심해야 한다.\n\n🔎 핵심 단서\n⭕ 신경성 식욕부진\n⭕ 생화학적 변화 4가지 이상\n⭕ 전해질: 저K, 저Cl, 저Mg, 저P\n⭕ 산염기: 구토 시 대사성 알칼리증\n⭕ 대사/내분비: 저혈당, 저T3, 고콜레스테롤\n⭕ 탈수: BUN 상승 가능\n\n👣 시험장 사고 흐름\n1단계: 구토/하제 사용 여부를 떠올린다 → 저K, 저Cl, 알칼리증.\n2단계: 굶음 자체를 떠올린다 → 저혈당, 저T3.\n3단계: 재급식 위험을 떠올린다 → 저인산혈증.\n4단계: 탈수와 영양불량을 붙인다 → BUN 상승, Mg 이상.\n\n📊 감별/오답 제거\n| 기전 | 변화 |\n| 구토 | 저염소혈증, 대사성 알칼리증, 저칼륨혈증 |\n| 굶음 | 저혈당, 저T3/euthyroid sick |\n| 재급식 | 저인산혈증, 저마그네슘혈증, 저칼륨혈증 |\n| 탈수 | BUN 상승 |\n\n✅ 3초 Lock line\nAnorexia lab = 저K·저Cl/알칼리증·저혈당·저P를 먼저 써라.""",
        "tags": ["소화기", "영양", "anorexia_nervosa", "전해질", "refeeding", "컨퍼런스", "2025-leftover"],
        "uncertain": True,
        "raw_anchor": "anorexia nervosa에서 나타나는 생화학적 변화 4가지 이상 (컨퍼런스)",
    },

    {
        "id": "PEDS2-2026RAW-SA2-HIB-MENINGITIS-CELLULITIS",
        "source": "강렬 Telegram 첨부 문제 모음 / 2026-05-18 user-provided exact stem / 주관식 2번",
        "origin": "actual_recall",
        "priority": "P2 user-confirmed-missing",
        "section": "2026 첨부문제 누락 · 감염",
        "question": "주Q. 10개월 여아가 1일 전부터 시작된 발열과 왼쪽 눈 주위가 부어오르는 증상으로 내원했다. 발열은 40.1도까지 올랐다. 내원 당일 왼쪽 눈 주변이 빨갛게 부어오르고 볼까지 부었다. 아기가 처져 있어 시행한 뇌척수액 검사에서 압력 20, gram-negative coccobacilli가 관찰되었다.\n(1) 진단은?\n(2) 항생제는?",
        "answer": "Haemophilus influenzae type b(Hib) 수막염을 동반한 안와주위/안면 연조직염; cefotaxime 또는 ceftriaxone",
        "explanation": "기존 FULL 298문항에서 10개월, 눈 주위/볼 부종, gram-negative coccobacilli 조합이 exact match되지 않아 user-confirmed missing card로 추가했다. CSF gram-negative coccobacilli는 H. influenzae를 강하게 시사하고, 영아의 periorbital/facial cellulitis와 invasive Hib infection/meningitis가 연결된다. 치료는 3세대 cephalosporin인 cefotaxime 또는 ceftriaxone이 중심이다.",
        "enhanced_explanation": """🧭 Big picture\n영아에서 얼굴, 특히 눈 주위와 볼까지 붓는 cellulitis가 있고 CSF에서 gram-negative coccobacilli가 보이면 Haemophilus influenzae type b, 즉 Hib invasive infection을 먼저 잡는다. 이 문제는 단순 안와주위연조직염만 묻는 게 아니라 뇌척수액 소견으로 Hib 수막염까지 연결하는 카드다.\n\n🔎 핵심 단서\n⭕ 10개월 영아\n⭕ 고열 40.1도와 처짐\n⭕ 왼쪽 눈 주위 발적·부종, 볼까지 부음\n⭕ CSF에서 gram-negative coccobacilli\n⭕ 진단축: Hib meningitis with periorbital/facial cellulitis\n⭕ 치료축: cefotaxime 또는 ceftriaxone\n\n👣 시험장 사고 흐름\n1단계: 눈 주위/볼 cellulitis만 보고 피부감염으로 끝내지 않는다.\n2단계: 처짐과 CSF 검사가 나온 순간 invasive infection/meningitis로 격상한다.\n3단계: gram-negative coccobacilli를 보면 Hib를 떠올린다.\n4단계: Hib 수막염 치료는 3세대 cephalosporin, cefotaxime 또는 ceftriaxone을 쓴다.\n\n📊 감별/오답 제거\n| 후보 | 판단 |\n| Hib meningitis | ✅ CSF gram-negative coccobacilli와 영아 facial cellulitis |\n| Pneumococcus | 그람양성 쌍알균 축 |\n| Meningococcus | 그람음성 쌍알균 축, coccobacilli 표현과 다름 |\n| Staphylococcus/Streptococcus cellulitis | 피부감염 원인 가능하나 CSF coccobacilli 설명 부족 |\n\n✅ 3초 Lock line\n영아 facial/periorbital cellulitis + CSF gram-negative coccobacilli = Hib meningitis, 치료는 cefotaxime/ceftriaxone.\n\n🎯 암기 확인 퀴즈\nQ1. CSF gram-negative coccobacilli에서 떠올릴 균은?\nQ2. 이 문제의 진단축은?\nQ3. 항생제 답은?\n\nA1. Haemophilus influenzae type b, Hib\nA2. Hib 수막염 동반 안와주위/안면 연조직염\nA3. Cefotaxime 또는 ceftriaxone""",
        "tags": ["감염", "수막뇌염", "Hib", "Haemophilus_influenzae", "cellulitis", "user-confirmed-missing", "2026-attachment"],
        "uncertain": False,
        "raw_anchor": "10개월 여아, 왼쪽 눈 주위/볼 부종, CSF 압력 20, gram-negative coccobacilli, 진단과 항생제",
        "append_to_end": True,
    },
]

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

body.peds-pretest2-full-bg .hi-flow-start-row { display:grid; grid-template-columns:minmax(0,1.2fr) minmax(0,1fr); gap:10px; margin:14px 0 10px; }
body.peds-pretest2-full-bg .hi-flow-start-row button { border:none; border-radius:16px; min-height:52px; padding:12px 14px; font-size:14px; font-weight:950; cursor:pointer; }
body.peds-pretest2-full-bg .hi-flow-start-primary { background:linear-gradient(135deg,#c4b5fd,#93c5fd); color:#111827; }
body.peds-pretest2-full-bg .hi-flow-start-secondary { background:rgba(15,23,42,.88); color:#e0f2fe; border:1px solid rgba(196,181,253,.36) !important; }
body.peds-pretest2-full-bg .hi-study-resume { margin:10px 0 12px; padding:12px 13px; border-radius:16px; background:rgba(88,28,135,.34); border:1px solid rgba(196,181,253,.38); color:#ede9fe; }
body.peds-pretest2-full-bg .hi-study-resume-title { font-weight:950; color:#f8fafc; margin-bottom:4px; }
body.peds-pretest2-full-bg .hi-study-resume-detail { font-size:12px; color:#ddd6fe; line-height:1.45; }
body.peds-pretest2-full-bg .hi-study-progress { margin-top:10px; height:8px; border-radius:999px; background:rgba(15,23,42,.72); overflow:hidden; border:1px solid rgba(196,181,253,.22); }
body.peds-pretest2-full-bg .hi-study-progress-fill { width:0%; height:100%; background:linear-gradient(90deg,#a78bfa,#5eead4); transition:width .18s ease; }
body.peds-pretest2-full-bg .hi-flow-status { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:8px; margin:0 0 12px; padding:10px 12px; border-radius:14px; background:#eef2ff; border:1px solid #c7d2fe; color:#312e81; font-size:13px; font-weight:900; }
body.peds-pretest2-full-bg .hi-flow-nav { position:sticky; bottom:8px; z-index:5; display:grid; grid-template-columns:1fr 1.15fr 1fr; gap:8px; margin:14px 0; padding:8px; border-radius:16px; background:rgba(15,23,42,.92); border:1px solid rgba(196,181,253,.34); box-shadow:0 14px 36px rgba(2,6,23,.24); }
body.peds-pretest2-full-bg .hi-flow-nav button { border:none; border-radius:12px; padding:10px 9px; font-size:13px; font-weight:950; cursor:pointer; }
body.peds-pretest2-full-bg .hi-flow-prev, body.peds-pretest2-full-bg .hi-flow-next { background:#e0f2fe; color:#075985; }
body.peds-pretest2-full-bg .hi-flow-done { background:#86efac; color:#14532d; }
body.peds-pretest2-full-bg .hi-study-part.done .hi-study-part-title::before { content:'✓ '; color:#86efac; }
body.peds-pretest2-full-bg .hi-card-mini { border:1px solid #e2e8f0; background:#f8fafc; border-radius:12px; padding:0; margin:8px 0; overflow:hidden; }
body.peds-pretest2-full-bg .hi-card-mini summary { list-style:none; cursor:pointer; padding:11px 12px; font-weight:850; line-height:1.48; display:flex; justify-content:space-between; gap:10px; align-items:flex-start; }
body.peds-pretest2-full-bg .hi-card-mini summary::-webkit-details-marker { display:none; }
body.peds-pretest2-full-bg .hi-card-mini summary::after { content:'펼침'; flex:0 0 auto; font-size:11px; color:#6d28d9; background:#ede9fe; border-radius:999px; padding:3px 7px; font-weight:950; }
body.peds-pretest2-full-bg .hi-card-mini[open] summary::after { content:'접기'; }
body.peds-pretest2-full-bg .hi-card-mini code { color:#7c2d12; font-weight:900; }
body.peds-pretest2-full-bg .hi-card-body { border-top:1px solid #e2e8f0; padding:11px 12px 12px; background:#fff; }
body.peds-pretest2-full-bg .hi-answer-line { border-left:4px solid #16a34a; background:#f0fdf4; border-radius:10px; padding:9px 10px; color:#14532d; line-height:1.58; }
body.peds-pretest2-full-bg .hi-mini-lock { margin-top:9px; color:#312e81; background:#eef2ff; border-radius:10px; padding:8px 10px; line-height:1.55; font-weight:850; }
body.peds-pretest2-full-bg .hi-inline-actions { display:flex; flex-wrap:wrap; gap:7px; margin-top:10px; }
body.peds-pretest2-full-bg .hi-inline-actions button { border:none; border-radius:10px; padding:8px 10px; background:#7c3aed; color:#fff; font-weight:900; cursor:pointer; }
body.peds-pretest2-full-bg .hi-part-bottom-note { color:#64748b; font-size:12px; line-height:1.5; margin-top:10px; }
@media (max-width:768px) { body.peds-pretest2-full-bg .hi-flow-start-row { grid-template-columns:1fr; } body.peds-pretest2-full-bg .hi-flow-nav { bottom:4px; grid-template-columns:1fr 1.1fr 1fr; gap:6px; padding:6px; } body.peds-pretest2-full-bg .hi-flow-nav button { padding:9px 5px; font-size:12px; } }

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

# Manual source-image recoveries for source-variant cards that are not covered
# by the automatic non-HI candidate linker. The HSV source crop contains the
# written answer, so the committed asset is a tight front-safe clinical-photo
# crop made from that source image.
CURATED_MANUAL_CARD_IMAGES = {
    "PEDS2-2023PDF-029": [
        {
            "src": "assets/peds_pretest2_full/PEDS2-2023PDF-029__front_crop__hsv_gingivostomatitis_perioral.png",
            "caption": "원문 병변 사진 crop",
            "kind": "manual_front_crop",
            "front_visible": True,
            "curated_id": "manual_hsv_gingivostomatitis_crop_20260517",
        }
    ],
    # The original HI PDF source crop for this card contains the answer text and
    # the only embedded neighboring image is an EBV smear. Use a neutral,
    # answer-safe trunk rash photo as the learner-facing image.
    "PEDS2-HI2-013": [
        {
            "src": "assets/peds_pretest2_full/PEDS2-HI2-013__front_rash_trunk_20260517.jpg",
            "caption": "몸통 발진 사진 · Jonnymccullagh / CC BY-SA 3.0",
            "kind": "manual_front_image",
            "front_visible": True,
            "curated_id": "manual_trunk_rash_photo_20260517",
        }
    ],
    # 소화기/구토 축: 원문 clean X-ray만 front-visible로 수동 복구.
    # target sign/대장내시경/achalasia/coin CXR는 현재 원본에서 정답 노출 없는 clean visual을 못 찾아 보류.
    "PEDS2-2026-9to12-SA2": [
        {
            "src": "assets/peds_pretest2_full/peds2_manual_double_bubble_xray_hi2_pdfimg_14_p08R.jpg",
            "caption": "원문 double bubble X-ray",
            "kind": "manual_front_xray",
            "front_visible": True,
            "curated_id": "manual_double_bubble_xray_20260517",
        }
    ],
    "PEDS2-2025-11to14-Q7": [
        {
            "src": "assets/peds_pretest2_full/peds2_manual_double_bubble_xray_hi2_pdfimg_14_p08R.jpg",
            "caption": "원문 double bubble X-ray",
            "kind": "manual_front_xray",
            "front_visible": True,
            "curated_id": "manual_double_bubble_xray_20260517",
        }
    ],
    "PEDS2-2025-1to2-Q1": [
        {
            "src": "assets/peds_pretest2_full/peds2_manual_double_bubble_xray_hi2_pdfimg_14_p08R.jpg",
            "caption": "원문 double bubble X-ray",
            "kind": "manual_front_xray",
            "front_visible": True,
            "curated_id": "manual_double_bubble_xray_20260517",
        }
    ],
    "PEDS2-HI2-068": [
        {
            "src": "assets/peds_pretest2_full/peds2_manual_double_bubble_xray_hi2_pdfimg_14_p08R.jpg",
            "caption": "원문 double bubble X-ray",
            "kind": "manual_front_xray",
            "front_visible": True,
            "curated_id": "manual_double_bubble_xray_20260517",
        }
    ],
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
    "hi2_pdfimg_26_p15R.jpg",  # TAPVR teaching snowman/Olaf image; answer cue, keep behind reveal
}

CURATED_HI_DUPLICATES = {
    # Same original question as HI2-021. Keep the original image on the front,
    # but do not duplicate the whole answer/explanation on reveal.
    "PEDS2-2025-15to18-Q1": "PEDS2-HI2-021",
}

# Some images are answer-only globally because they are annotated teaching crops,
# but one card may still need a clean-enough crop as the actual question image.
CURATED_HI_IMAGE_FRONT_OVERRIDES = {
    ("PEDS2-HI2-122", "hi2_pdfimg_23_p14L.jpg"),  # neonatal ECG question image
}

# HI PDF image extraction is proximity-based, so images from the same page/column
# can be pulled into a neighboring question. These explicit card+filename blocks
# are the infection-unit audit fixes. Prefer no image over a misleading image.
CURATED_HI_IMAGE_EXCLUDES = {
    # Q43 수두: extracted image is an EBV atypical lymphocyte smear from the next section.
    ("PEDS2-HI2-013", "hi2_pdfimg_03_p03L.jpg"),
    ("PEDS2-HI2-013", "hi2_013_p03L.png"),
    # Q55 septic arthritis asks for joint-fluid Gram stain; CXR belongs to pertussis Q53.
    ("PEDS2-HI2-025", "hi2_pdfimg_08_p04L.jpg"),
    # Q56 impetigo infant face/perioral lesion: keep face image, drop adjacent leg lesion.
    ("PEDS2-HI2-026", "hi2_pdfimg_06_p04R.jpg"),
    # Q57 impetigo scratched lesion: keep leg lesion, drop tetanus table and infant face.
    ("PEDS2-HI2-027", "hi2_pdfimg_04_p04R.jpg"),
    ("PEDS2-HI2-027", "hi2_pdfimg_05_p04R.jpg"),
    # GI p08R proximity cleanup: pyloric US and double-bubble X-ray sit in the same page column.
    # Keep only the image that belongs to each stem; do not leak neighboring GI visuals.
    ("PEDS2-HI2-066", "hi2_pdfimg_14_p08R.jpg"),  # pyloric stenosis card: drop double-bubble X-ray
    ("PEDS2-HI2-069", "hi2_pdfimg_13_p08R.jpg"),  # double-bubble treatment card: drop pyloric US
    ("PEDS2-HI2-071", "hi2_pdfimg_13_p08R.jpg"),  # pancreatitis/MRCP card: no clean MRCP asset in source
    ("PEDS2-HI2-071", "hi2_pdfimg_14_p08R.jpg"),
    # 2026-05-18 HI embedded-image full audit: proximity extraction leaked
    # diagnostic images into neighboring cards. Prefer no image over a misleading front image.
    # p07L image is an anorectal malformation/imperforate-anus invertogram, not Hirschsprung.
    ("PEDS2-HI2-050", "hi2_pdfimg_11_p07L.jpg"),
    ("PEDS2-HI2-051", "hi2_pdfimg_11_p07L.jpg"),
    ("PEDS2-HI2-052", "hi2_pdfimg_11_p07L.jpg"),
    ("PEDS2-HI2-053", "hi2_pdfimg_11_p07L.jpg"),
    ("PEDS2-HI2-054", "hi2_pdfimg_11_p07L.jpg"),
    # ECG p14L: pdfimg_24 is PSVT strip, so keep it only on PSVT/adenosine cards.
    ("PEDS2-HI2-122", "hi2_pdfimg_24_p14L.jpg"),
    ("PEDS2-HI2-123", "hi2_pdfimg_22_p14L.jpg"),
    ("PEDS2-HI2-123", "hi2_pdfimg_23_p14L.jpg"),
    ("PEDS2-HI2-123", "hi2_pdfimg_24_p14L.jpg"),
    ("PEDS2-HI2-124", "hi2_pdfimg_22_p14L.jpg"),
    ("PEDS2-HI2-124", "hi2_pdfimg_23_p14L.jpg"),
    ("PEDS2-HI2-125", "hi2_pdfimg_22_p14L.jpg"),
    ("PEDS2-HI2-125", "hi2_pdfimg_23_p14L.jpg"),
    ("PEDS2-HI2-126", "hi2_pdfimg_22_p14L.jpg"),
    ("PEDS2-HI2-126", "hi2_pdfimg_23_p14L.jpg"),
    ("PEDS2-HI2-127", "hi2_pdfimg_22_p14L.jpg"),
    ("PEDS2-HI2-127", "hi2_pdfimg_23_p14L.jpg"),
    ("PEDS2-HI2-127", "hi2_pdfimg_24_p14L.jpg"),
    # p15R cardiac CXR images: 25=PS PA bulging, 26=TAPVR teaching/answer cue, 27=TAPVR question CXR.
    ("PEDS2-HI2-142", "hi2_pdfimg_25_p15R.jpg"),
    ("PEDS2-HI2-145", "hi2_pdfimg_25_p15R.jpg"),
    ("PEDS2-HI2-145", "hi2_pdfimg_26_p15R.jpg"),
    ("PEDS2-HI2-145", "hi2_pdfimg_27_p15R.jpg"),
    ("PEDS2-HI2-146", "hi2_pdfimg_25_p15R.jpg"),

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


# 2026-05-17 user check: PEDS2-HI2-003 answer is source-faithful,
# but the stem wording says "serious bacterial infection" while the HI source
# table is actually fever-without-focus causes by age and includes viruses.
CURATED_CARD_FIXES.update({
    "PEDS2-HI2-003": {
        "answer": "1~3개월: E. coli, Enterovirus, Parechovirus / 3~36개월: S. pneumoniae, N. meningitidis, Salmonella",
        "uncertain": False,
        "enhanced_explanation": """🧭 Big picture
이 카드는 현재 답이 맞다. 다만 문제 표현이 헷갈린다. HI 원문에서는 이 문항 바로 위 제목이 ‘국소 증상 없는 발열 원인’이고, 나이별 원인을 표처럼 제시한다. 그래서 Enterovirus와 Parechovirus가 들어간다. 둘은 세균이 아니라 바이러스이므로, 이 문제를 ‘순수 세균 균주만’으로 해석하면 오히려 틀린다. 시험장에서는 HI 원문 나이별 리스트를 그대로 쓰는 카드로 보면 된다.

🔎 핵심 단서
⭕ 원문 제목: 국소 증상 없는 발열 원인
⭕ 1~3개월: E. coli, Enterovirus, Parechovirus
⭕ 3~36개월: S. pneumoniae, N. meningitidis, Salmonella
⭕ Enterovirus/Parechovirus는 세균이 아니라 바이러스
❌ GBS, Listeria, Hib, UTI 원인균을 이 카드 답에 추가로 쓰는 것은 원문 답안과 어긋날 수 있음

👣 시험장 사고 흐름
1단계: ‘발열 + 국소 증상 없음’이면 fever without focus 표를 떠올린다.
2단계: 나이를 먼저 자른다.
3단계: 1~3개월은 E. coli + Enterovirus + Parechovirus를 쓴다.
4단계: 3~36개월은 S. pneumoniae + N. meningitidis + Salmonella를 쓴다.
5단계: 문제 문구가 ‘세균성 감염’이라고 되어 있어도, HI 원문 답은 바이러스까지 포함한 나이별 원인 리스트라는 점을 기억한다.

🧠 쉽게 이해하기
이 카드의 함정은 이름이다. 제목만 보면 ‘세균만 적어야 하나?’ 싶은데, 실제 원문 표는 ‘국소 증상 없는 발열의 원인’을 나이별로 묶는다. 1~3개월 영아는 장바이러스와 parechovirus가 발열 원인으로 중요하고, 그중 일부에서 E. coli 같은 세균감염을 조심한다. 3~36개월에서는 바이러스가 많지만, 시험 답으로는 폐렴알균, 수막알균, 살모넬라를 묶어 둔 구조다.

📊 감별/오답 제거
| 연령 | HI 원문 답 | 주의점 |
| 신생아~1개월 | GBS, E. coli, L. monocytogenes, HSV, Enterovirus | 이 문항이 직접 묻는 구간은 아님 |
| 1~3개월 | E. coli, Enterovirus, Parechovirus | Entero/Parecho는 바이러스지만 원문 답에 포함 |
| 3~36개월 | S. pneumoniae, N. meningitidis, Salmonella | Hib/UTI를 추가하면 일반론은 가능해도 이 카드 답은 흐려짐 |
| 세균수막염 원인균 문제 | S. pneumoniae, Hib, N. meningitidis 등 | 이 카드와 다른 주제 |

✅ 3초 Lock line
HI 무병소 발열 원인: 1~3개월은 E. coli·Enterovirus·Parechovirus, 3~36개월은 pneumococcus·meningococcus·Salmonella.

🎯 암기 확인 퀴즈
Q1. 이 카드에서 Enterovirus/Parechovirus가 들어가는 이유는?
Q2. 1~3개월 국소 증상 없는 발열 원문 답은?
Q3. 3~36개월 국소 증상 없는 발열 원문 답은?

A1. 이 카드는 순수 세균 균주가 아니라 HI 원문의 국소 증상 없는 발열 원인 표를 묻기 때문
A2. E. coli, Enterovirus, Parechovirus
A3. S. pneumoniae, N. meningitidis, Salmonella""",
    },
})


# 2026-05-17 user report: Q44 front display masked the vital sign and lab
# result lines as [답 숨김]. The source question is an MCQ, so the lab values
# and answer choices should remain visible on the learner-facing front.
CURATED_CARD_FIXES.setdefault("PEDS2-HI2-014", {}).update({
    "display_question": """객Q. 17세 남자가 1주 전부터 열이 나고 목이 아파서 병원에 왔다. 110/70 - 95 - 18 - 38.5.
편도가 부어있고 삼출물이 관찰되었다. 양측 목에서 압통이 없는 최대 1cm 크기의 림프절이 만져졌다.
혈액검사 결과는 다음과 같다. 원인 바이러스는?
· 혈색소 11.5 / 백혈구 19,000 (중성구 32%, 림프구 60%, 단핵구 7%, 호산구 1%)
· 혈소판 110,000 / AST 186 / ALT 236
① 단순 헤르페스 바이러스 ② 뎅기 바이러스
③ 엔테로 바이러스 ④ 엡스타인바 바이러스 ⑤ A형 간염 바이러스""",
})


# 2026-05-17 user report: Q57/PEDS2-HI2-027 had adjacent lecture notes
# (erysipelas/cellulitis/S. aureus syndromes) appended into the problem stem.
# Keep only the actual impetigo question; the following notes are not part of
# this item.
CURATED_CARD_FIXES.setdefault("PEDS2-HI2-027", {}).update({
    "question": """객Q. 7세 남아가 5일 전부터 피부가 가렵다며 병원에 왔다.
2일 전부터 긁은 자리에 사진과 같은 병터가 생겼다. (예상 Pic)
아파 보이지는 않고 체온 36.5도이다. 진단은?""",
    "display_question": """객Q. 7세 남아가 5일 전부터 피부가 가렵다며 병원에 왔다.
2일 전부터 긁은 자리에 사진과 같은 병터가 생겼다. (예상 Pic)
아파 보이지는 않고 체온 36.5도이다. 진단은?""",
    "answer": "고름딱지증 (=농가진)",
    "uncertain": False,
})


# 2026-05-17 user request: add normal CSF glucose/protein values to Q62 and
# restore the CSF result line on the front. These lab values are not answers;
# they are required to classify viral vs bacterial meningitis.
CURATED_CARD_FIXES.setdefault("PEDS2-HI2-039", {}).update({
    "display_question": """주Q. 7세 여아 두통을 주소로 내원. 이틀 전 상기도감염 증세. 하루 전 심한 두통과
구토. 신체검진 상 경부강직. Kernig sign & Brudzinski sign 양성.
· 뇌척수액 검사 결과 압력 100, WBC 350 (단핵구 90%), 단백 55, 당 75
(1) 진단명? [답 숨김]
(2) 가장 흔한 원인? [답 숨김]""",
    "enhanced_explanation": """🧭 Big picture
두통, 구토, 경부강직, Kernig/Brudzinski 양성이면 수막염을 생각한다. 여기서 CSF가 압력 100, WBC 350 중 단핵구 90%, 단백 55, 당 75이면 세균보다 바이러스수막염 패턴이다. 정상 CSF glucose는 대략 45~80 mg/dL 또는 혈당의 약 2/3 이상이고, 정상 CSF protein은 대략 15~45 mg/dL로 본다. 이 문제의 당 75는 정상 범위이고, 단백 55는 살짝 상승한 정도라 바이러스수막염 쪽에 더 맞다. 바이러스수막염의 소아 흔한 원인은 Enterovirus다.

🔎 핵심 단서
⭕ 상기도감염 후 두통/구토: 바이러스 감염 선행 가능
⭕ 경부강직, Kernig/Brudzinski: meningeal irritation
⭕ WBC 350, 단핵구 90%: 림프구/단핵구 우세 → 바이러스 쪽
⭕ CSF glucose 75: 정상 범위, 세균수막염의 저당 소견과 다름
⭕ CSF protein 55: 정상 15~45보다 약간 상승, 세균수막염처럼 크게 상승한 패턴은 아님

👣 시험장 사고 흐름
1단계: 수막자극 징후 확인 → 수막염.
2단계: CSF 세포 종류 확인 → 단핵구/림프구 우세면 바이러스 쪽.
3단계: CSF glucose 확인 → 정상치 45~80 mg/dL 정도, 또는 혈당의 2/3 이상이면 보존.
4단계: CSF protein 확인 → 정상 15~45 mg/dL 정도, 55는 경도 상승.
5단계: 바이러스수막염이면 가장 흔한 원인 Enterovirus로 정리.

🧠 쉽게 이해하기
세균수막염은 뇌척수액 안에서 세균과 중성구가 거칠게 싸우는 상황이라 PMN이 우세하고, 단백이 크게 오르고, glucose가 떨어진다. 반대로 바이러스수막염은 림프구/단핵구 중심 반응이고 glucose가 대체로 보존된다. 이 문제는 당 75가 정상이고 단백 55도 약간 오른 정도라 “세균의 저당·고단백 폭발”이 아니다.

📊 감별/오답 제거
| 항목 | 정상 CSF 기준 | 이 문제 | 바이러스 수막염 | 세균 수막염 |
| WBC/세포 | 거의 없음, 림프구 소수 | WBC 350, 단핵구 90% | 림프구/단핵구 우세 | PMN 우세 |
| Glucose | 약 45~80 mg/dL 또는 혈당의 약 2/3 이상 | 75 | 대개 정상 | 감소 |
| Protein | 약 15~45 mg/dL | 55 | 정상~경도 증가 | 크게 증가 |
| 흔한 원인 | - | - | Enterovirus | 폐렴알균/수막알균 등 |

✅ 3초 Lock line
수막염 증상 + CSF 단핵구 우세 + glucose 정상(45~80) + protein 경도 상승 = 바이러스수막염, 원인 m/c는 Enterovirus.

🎯 암기 확인 퀴즈
Q1. 정상 CSF glucose는 대략 어느 범위인가?
Q2. 정상 CSF protein은 대략 어느 범위인가?
Q3. 바이러스수막염의 대표 원인은?

A1. 약 45~80 mg/dL 또는 혈당의 약 2/3 이상
A2. 약 15~45 mg/dL
A3. Enterovirus""",
})

# 2026-05-18 user report: Q117/PEDS2-HI2-071 front masked the lab
# result lines as [답 숨김]. These lab values are required to diagnose
# gallstone pancreatitis and must stay visible on the learner-facing front.
CURATED_CARD_FIXES.setdefault("PEDS2-HI2-071", {}).update({
    "display_question": """주Q. 5세 여아 황달. 공막황달을 제외한 다른 이상소견 없음 (발열 X), 혈액검사 및
MR cholangiography 줌. 진단명은?
· 혈액검사 WBC 8000, Hb 12.5, 총빌리루빈/간접 5/5
· amylase 200, lipase 350
A) [답 숨김]""",
})

# BEGIN DIGESTIVE_ANSWER_AUDIT_FIXES_20260517
CURATED_CARD_FIXES.update({'PEDS2-2026-5to8-Q7': {'answer': '만성복통 alarm symptom: 야간 각성 복통, 지속적 우상복부/우하복부 통증 또는 국소 압통, 연하곤란, 혈변/위장관 실혈, 의미 있는 담즙성·주기적·지속적 구토, 만성 중증/야간 설사, 발열, 체중감소/성장속도 감소, 사춘기 지연, IBD/소화성궤양 가족력 등에서 2개 이상', 'uncertain': False}, 'PEDS2-2025-19to23-Q2': {'answer': '중증 탈수로 보이면 등장성 IV 수액(0.9% 생리식염수 등)을 우선 투여한다. 중등도 이하 탈수는 ORS 50–100 mL/kg를 3–4시간에 투여한다.', 'uncertain': False}, 'PEDS2-2023PDF-035': {'answer': '중간창자 꼬임(midgut volvulus)', 'uncertain': False}, 'PEDS2-HI2-043': {'answer': '로타바이러스 백신', 'uncertain': False}, 'PEDS2-HI2-044': {'answer': '바이러스 위장관염; 가장 흔한 바이러스는 로타바이러스', 'uncertain': False}, 'PEDS2-HI2-045': {'answer': '로타바이러스', 'uncertain': False}, 'PEDS2-HI2-046': {'answer': 'Salmonella typhi; ceftriaxone 또는 3세대 cephalosporin', 'uncertain': False}, 'PEDS2-HI2-047': {'answer': '수유모의 항원 제한 식사', 'uncertain': False}, 'PEDS2-HI2-048': {'answer': '젖당 제한 식이', 'uncertain': False}, 'PEDS2-HI2-056': {'answer': '만성복통 red flag: 야간 각성 복통, 지속적 RUQ/RLQ 통증 또는 국소 압통, 연하곤란, 혈변/위장관 실혈, 의미 있는 구토, 야간/중증 설사, 발열, 체중감소/성장속도 감소, 사춘기 지연, IBD/소화성궤양 가족력 등에서 4개 이상', 'uncertain': False}, 'PEDS2-HI2-057': {'answer': '복부초음파', 'uncertain': False}, 'PEDS2-HI2-059': {'answer': '장중첩증; 복부초음파', 'uncertain': False}, 'PEDS2-HI2-060': {'answer': '연소 용종 의심; 대장내시경', 'uncertain': False}, 'PEDS2-HI2-062': {'answer': '메켈 게실; 99mTc-pertechnetate scan(메켈 스캔)', 'uncertain': False}, 'PEDS2-HI2-069': {'answer': '전해질 및 수분 공급 후 수술적 치료', 'uncertain': False}, 'PEDS2-HI2-073': {'answer': '비타민 D', 'uncertain': False}, 'PEDS2-HI2-076': {'answer': '아연', 'uncertain': False}, 'PEDS2-HI2-077': {'answer': '아연', 'uncertain': False}})
# END DIGESTIVE_ANSWER_AUDIT_FIXES_20260517

CURATED_CARD_FIXES.setdefault("PEDS2-2023PDF-029", {}).update({
    "question": "객Q. 다음 구강/입주위 병변 사진을 보고 가장 가능성이 큰 진단은?",
    "display_question": "객Q. 다음 구강/입주위 병변 사진을 보고 가장 가능성이 큰 진단은?",
    "answer": "헤르페스 잇몸구내염, herpetic gingivostomatitis",
    "explanation": "2023PDF 원문에는 HSV 잇몸구내염 사진/증례가 있었고, FULL 병합 과정에서 이미지가 누락되었다. 답이 적힌 원문 캡처에서 글자 없는 병변 사진만 crop해 front에 복원했다.",
    "enhanced_explanation": "🧭 Big picture\n소아가 발열, 보챔, 섭취 저하와 함께 입술 주변 또는 구강 점막의 다발성 수포·궤양 병변을 보이면 단순포진바이러스에 의한 헤르페스 잇몸구내염을 생각한다.\n\n🔎 핵심 단서\n- 입주위/구강 수포와 궤양성 병변\n- 통증 때문에 잘 먹지 못함, 침 흘림 가능\n- 원인: HSV, 흔히 HSV-1\n- 치료: 증상 완화와 수분 보충, 필요한 경우 acyclovir\n\n👣 시험장 사고 흐름\n1단계: 병변 위치가 입안/입주위인지 본다.\n2단계: 손발 병변이 같이 있으면 수족구병을 먼저 생각한다.\n3단계: 손발보다 입주위·잇몸·구강 궤양이 중심이고 통증/섭취 저하가 강하면 HSV 잇몸구내염으로 간다.\n\n✅ 3초 Lock line\n소아 + 입주위/구강 다발 수포·궤양 + 못 먹음 = 헤르페스 잇몸구내염.",
    "uncertain": False,
})

# BEGIN RESPIRATORY_ANSWER_AUDIT_FIXES_20260517
CURATED_CARD_FIXES.update({'PEDS2-HI2-031': {'answer': '소아: 폐 하부 병변·초감염 결핵·치유 시 석회화 / 성인: 폐첨 또는 쇄골상부 병변·재감염/재활성화 결핵·치유 시 섬유화', 'uncertain': False}, 'PEDS2-HI2-032': {'answer': 'Chest X-ray와 TST; 정상/활동성 결핵 배제 시 isoniazid 예방치료', 'uncertain': False}, 'PEDS2-HI2-034': {'answer': '이소니아지드 9개월 복용', 'uncertain': False}, 'PEDS2-HI2-037': {'answer': 'Isoniazid + Rifampicin + Pyrazinamide + Ethambutol 2개월 후 Isoniazid + Rifampicin 4개월', 'uncertain': False}, 'PEDS2-HI2-065': {'answer': '기관루 동반 식도폐쇄', 'uncertain': False}, 'PEDS2-HI2-078': {'answer': '니스타틴', 'uncertain': False}, 'PEDS2-HI2-081': {'answer': '경과관찰', 'uncertain': False}, 'PEDS2-HI2-087': {'answer': '부비동염; Streptococcus pneumoniae', 'uncertain': False}, 'PEDS2-HI2-088': {'answer': '크룹; Parainfluenza virus', 'uncertain': False}, 'PEDS2-HI2-090': {'answer': '에피네프린', 'uncertain': False}, 'PEDS2-HI2-091': {'answer': '수액치료', 'uncertain': False}, 'PEDS2-HI2-093': {'answer': '바이러스성 폐렴', 'uncertain': False}, 'PEDS2-HI2-094': {'answer': '암피실린-설박탐', 'uncertain': False}, 'PEDS2-HI2-095': {'answer': '마이코플라즈마 폐렴', 'uncertain': False}, 'PEDS2-HI2-101': {'answer': 'ICS + LABA', 'uncertain': False}, 'PEDS2-HI2-102': {'answer': '흡입형 속효성 β2 항진제(SABA)', 'uncertain': False}, 'PEDS2-HI2-104': {'answer': 'A: Formoterol / B: Budesonide-Formoterol 복합제', 'uncertain': False}, 'PEDS2-2025-19to23-Q3-SOURCEVAR': {'answer': '4번', 'uncertain': False}})
# END RESPIRATORY_ANSWER_AUDIT_FIXES_20260517

# BEGIN CARDIOVASCULAR_ANSWER_AUDIT_FIXES_20260517
CURATED_CARD_FIXES.update({'PEDS2-HI2-108': {'answer': '태아 순환: 태반 산소공급, 정맥관·난원공·동맥관을 통한 병렬 순환 / 출생 후: 폐혈관저항 감소·체혈관저항 증가, 동맥관·난원공·정맥관 폐쇄', 'uncertain': False}, 'PEDS2-HI2-113': {'answer': '도약맥박: PDA, 대동맥판 역류, 동정맥 샛길 / 맥박 약화: 심장눌림증, 좌심실 유출로 협착, 심근병증', 'uncertain': False}, 'PEDS2-HI2-114': {'answer': 'VSD > ASD > PDA > TOF > PS', 'uncertain': False}, 'PEDS2-HI2-116': {'answer': '생리적 폐동맥 분지 협착 잡음, 스틸 심잡음, 정맥 잡음; 무해성 아님: 이완기 잡음, 강도 3도 이상 잡음', 'uncertain': False}, 'PEDS2-HI2-118': {'answer': '정맥 잡음(venous hum)', 'uncertain': False}, 'PEDS2-HI2-119': {'answer': '생리적 폐동맥 분지 협착 잡음', 'uncertain': False}, 'PEDS2-HI2-124': {'answer': 'Adenosine 정주', 'uncertain': False}, 'PEDS2-HI2-132': {'answer': '작은 결손은 생후 1~2년 또는 2년간 30~50% 자연폐쇄; 큰 결손은 심부전·폐동맥고혈압, 잦은 호흡기 감염, Eisenmenger syndrome·감염성 심내막염·대동맥판 역류가 생길 수 있음', 'uncertain': False}, 'PEDS2-HI2-135': {'answer': '좌상흉골연 수축기 박출성 잡음, 고정성 넓은 S2 분열, 좌하흉골연 rumbling mid-diastolic murmur', 'uncertain': False}, 'PEDS2-HI2-141': {'answer': 'CXR: 폐동맥 팽대/확장; 진단: 폐동맥판 협착', 'uncertain': False}, 'PEDS2-HI2-142': {'answer': '경과관찰', 'uncertain': False}, 'PEDS2-HI2-143': {'answer': '대동맥판 협착(AS)', 'uncertain': False}, 'PEDS2-HI2-146': {'answer': 'CXR snowman sign; 총폐정맥환류이상(TAPVR)', 'uncertain': False}, 'PEDS2-HI2-147': {'answer': '무릎-가슴 자세, morphine, 산소/안정, 필요 시 propranolol·ketamine·phenylephrine, 탈수/산증 교정', 'uncertain': False}, 'PEDS2-HI2-151': {'answer': '5일 이상 발열 + 비화농성 양측 결막충혈, 입술/구강 변화, 다양한 발진, 비화농성 경부림프절 비대, 손발 변화 중 4개 이상', 'uncertain': False}, 'PEDS2-HI2-153': {'answer': '인두결막열, 성홍열, 홍역, EBV 감염, 스티븐스-존슨 증후군, 독성 쇼크 증후군, 특발 소아 관절염 등', 'uncertain': False}})
# END CARDIOVASCULAR_ANSWER_AUDIT_FIXES_20260517
# BEGIN REMAINING_ANSWER_AUDIT_FIXES_20260517
CURATED_CARD_FIXES.update({'PEDS2-2023PDF-017': {'answer': '직장수지검사(DRE). 직장에 딱딱한 변 덩어리가 만져지면 기능성 변비를 지지하고, 직장이 비어 있으면 선천성 거대결장 등을 의심한다.', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 직장수지검사(DRE). 직장에 딱딱한 변 덩어리가 만져지면 기능성 변비를 지지하고, 직장이 비어 있으면 선천성 거대결장 등을 의심한다..\n\n🔎 핵심 단서\n⭕ 문항: 6세가 3년째 변비, 주 1회 배변, 소량 혈변, 성장 정상이다. 해야 할 검사는?\n⭕ 확정 근거: Allen A04 기능성 변비: DRE에서 큰 변 덩어리 확인이 핵심 감별점\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n직장수지검사(DRE). 직장에 딱딱한 변 덩어리가 만져지면 기능성 변비를 지지하고, 직장이 비어 있으면 선천성 거대결장 등을 의심한다.'}, 'PEDS2-2023PDF-045': {'answer': 'Pediatric-onset IBD, early-onset IBD, very-early-onset IBD, infantile-onset IBD, neonatal-onset IBD', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 Pediatric-onset IBD, early-onset IBD, very-early-onset IBD, infantile-onset IBD, neonatal-onset IBD.\n\n🔎 핵심 단서\n⭕ 문항: Pediatric IBD를 발병 연령별 5가지로 분류하라.\n⭕ 확정 근거: 문항 자체가 발병 연령별 pediatric IBD 5분류를 요구\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nPediatric-onset IBD, early-onset IBD, very-early-onset IBD, infantile-onset IBD, neonatal-onset IBD'}, 'PEDS2-2023PDF-001': {'answer': '후두연화증(laryngomalacia)', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 후두연화증(laryngomalacia).\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 생후 초기부터 흡기 시 그르렁거림/협착음이 있고, 울거나 보채거나 수유할 때 심해지며 엎드리면 완화된다. 가장 가능성이 큰 진단은?\n⭕ 확정 근거: 생후 초기 흡기성 협착음, 울거나 수유 시 악화, 엎드리면 완화\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n후두연화증(laryngomalacia)'}, 'PEDS2-2023PDF-021': {'answer': '기관지/기도 이물 흡인', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 기관지/기도 이물 흡인.\n\n🔎 핵심 단서\n⭕ 문항: 4세가 2개월 전부터 발열이 반복되고 항생제 후 호전, 오른쪽만 천명음이 들린다. 가장 의심되는 진단은?\n⭕ 확정 근거: 반복 발열·항생제 후 호전 반복 + 한쪽 천명음은 국소 기도폐쇄/이물 흡인을 우선 의심\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n기관지/기도 이물 흡인'}, 'PEDS2-2023PDF-037': {'answer': 'Turner syndrome', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 Turner syndrome.\n\n🔎 핵심 단서\n⭕ 문항: 신생아/영아 얼굴과 손·발등 부종, CXR가 제시된 증례. 진단은?\n⭕ 확정 근거: 신생아/영아의 손발등 부종과 Turner phenotype 축\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nTurner syndrome'}, 'PEDS2-HI2-036': {'answer': '항결핵제 치료', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 항결핵제 치료.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 발열과 기침있는데 X-ray 줌. 다음 치료는? ① 항결핵제 ② 심장초음파 ③ 측와위 X-ray\n⭕ 확정 근거: HI 원문 crop에서 ① 항결핵제 정답 표시 확인\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n항결핵제 치료'}, 'PEDS2-HI2-079': {'answer': '체위 배담(두드림·진동), 호흡운동과 기침, 기구 사용', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 체위 배담(두드림·진동), 호흡운동과 기침, 기구 사용.\n\n🔎 핵심 단서\n⭕ 문항: 주Q. 물리적 객담 배출법 3가지 적기\n⭕ 확정 근거: HI XML p.10 물리적 객담 배출법 항목\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n체위 배담(두드림·진동), 호흡운동과 기침, 기구 사용'}, 'PEDS2-HI2-080': {'answer': '저유량: 코캐뉼라, 코카테터, 산소마스크, 산소저장기 부착 마스크 / 고유량: 산소텐트, 산소후드, 기관내삽관, Venturi mask', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 저유량: 코캐뉼라, 코카테터, 산소마스크, 산소저장기 부착 마스크 / 고유량: 산소텐트, 산소후드, 기관내삽관, Venturi mask.\n\n🔎 핵심 단서\n⭕ 문항: 주Q. 저유량, 고유량 산소공급법 각각 3가지 이상\n⭕ 확정 근거: HI XML p.10 산소 공급 방법 항목\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n저유량: 코캐뉼라, 코카테터, 산소마스크, 산소저장기 부착 마스크 / 고유량: 산소텐트, 산소후드, 기관내삽관, Venturi mask'}, 'PEDS2-HI2-086': {'answer': 'Amoxicillin 40–45 mg/kg/일', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 Amoxicillin 40–45 mg/kg/일.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 39도 이상 3일 지속, 과거력 상 중이염 2회. (중이염 사진), 처치는? ① 자연호전되니까 경과관찰 ② Amoxicillin 40~45mg/kg/일 ③ Amoxicillin 80~90mg/kg/일 ④ 청력감소 있을 수 있어 청력검사 한다. ⑤ Mastoiditis 있을 수 있어 CT 검사한다.\n⭕ 확정 근거: HI 원문 crop에서 ② Amoxicillin 40–45 mg/kg/일 정답 표시 확인\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nAmoxicillin 40–45 mg/kg/일'}, 'PEDS2-HI2-096': {'answer': '② 오른쪽 기관지가 막혔다', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 ② 오른쪽 기관지가 막혔다.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 2세 남아 땅콩 먹고 발작적인 기침과 입술 주변이 파래져서 왔다. 틀린 설명은? ① 기관지내 이물이 가장 흔하다. ② 오른쪽 기관지가 막혔다. ③ 경직성 기관지경 사용해서 뺀다. ④ Stop valve, Bypass valve, Check valve 모두 나타날 수 있다. ⑤ 기도 이물에 의한 질식 소견 보이면 복\n⭕ 확정 근거: HI 원문 crop에서 틀린 설명으로 ② 표시 확인\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n② 오른쪽 기관지가 막혔다'}, 'PEDS2-2023PDF-040': {'answer': 'DiGeorge syndrome, 22q11.2 deletion', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 DiGeorge syndrome, 22q11.2 deletion.\n\n🔎 핵심 단서\n⭕ 문항: 청색증으로 추적 중인 30세 여성이 돌 전 경련, 8세 변형 Blalock-Taussig 단락수술, cleft palate, odd looking face, clubbing, Hb 18.5를 보인다. 가장 가능성 높은 underlying disease는?\n⭕ 확정 근거: cleft palate, odd looking face, 청색증 선천심질환, 경련 병력의 전형적 축\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nDiGeorge syndrome, 22q11.2 deletion'}, 'PEDS2-HI2-111': {'answer': '측정: 안정 상태에서 적절한 커프 사용, 혈압대 폭은 위팔 중간 둘레의 40%, 공기주머니 길이는 위팔 둘레의 80–100%, 하지 혈압은 상지보다 약 10 mmHg 높음, 영아는 진동식 자동혈압계 사용 가능. 분류: 정상 <90백분위수, 상승혈압 90–95백분위수 미만 또는 120/80 이상, 1단계 고혈압 95백분위수 이상~95백분위수+12 또는 130/80–139/89, 2단계 고혈압 95백분위수+12 이상 또는 140/90 이상.', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 측정: 안정 상태에서 적절한 커프 사용, 혈압대 폭은 위팔 중간 둘레의 40%, 공기주머니 길이는 위팔 둘레의 80–100%, 하지 혈압은 상지보다 약 10 mmHg 높음, 영아는 진동식 자동혈압계 사용 가능. 분류: 정상 <90백분위수, 상승혈압 90–95백분위수 미만 또는 120/80 이상, 1단계 고혈압 95백분위수 이상~95백분위수+12 또는 130/80–139/89, 2단계 고혈압 95백분위수+12 이상 또는 140/90 이상..\n\n🔎 핵심 단서\n⭕ 문항: 주Q. 소아혈압 측정 방법과 소아 청소년기 혈압의 분류 기술\n⭕ 확정 근거: HI XML p.13 소아혈압 측정 항목 + 기존 P2 covered 혈압 분류 카드\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n측정: 안정 상태에서 적절한 커프 사용, 혈압대 폭은 위팔 중간 둘레의 40%, 공기주머니 길이는 위팔 둘레의 80–100%, 하지 혈압은 상지보다 약 10 mmHg 높음, 영아는 진동식 자동혈압계 사용 가능. 분류: 정상 <90백분위수, 상승혈압 90–95백분위수 미만 또는 120/80 이상, 1단계 고혈압 95백분위수 이상~95백분위수+12 또는 130/80–139/89, 2단계 고혈압 95백분위수+12 이상 또는 140/90 이상.'}, 'PEDS2-HI2-115': {'answer': '심실중격결손(VSD), 대동맥판막 폐쇄부전(AR), 폐동맥판막 협착(PS), 심방중격결손(ASD), 동맥관개존(PDA), 승모판협착(MS)', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 심실중격결손(VSD), 대동맥판막 폐쇄부전(AR), 폐동맥판막 협착(PS), 심방중격결손(ASD), 동맥관개존(PDA), 승모판협착(MS).\n\n🔎 핵심 단서\n⭕ 문항: 주Q. 심잡음 그림에서 해당 질환명의 빈칸을 채우기 (5개, 위 그림에서 네모)\n⭕ 확정 근거: HI 원문 이미지 네모 빈칸 OCR 확인\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n심실중격결손(VSD), 대동맥판막 폐쇄부전(AR), 폐동맥판막 협착(PS), 심방중격결손(ASD), 동맥관개존(PDA), 승모판협착(MS)'}, 'PEDS2-HI2-121': {'answer': 'ASD, 폐동맥판 협착(PS), 우각차단(RBBB), 엡스타인 기형, 총폐정맥환류이상(TAPVR)', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 ASD, 폐동맥판 협착(PS), 우각차단(RBBB), 엡스타인 기형, 총폐정맥환류이상(TAPVR).\n\n🔎 핵심 단서\n⭕ 문항: 주Q. Wide S2 splitting 을 보이는 선천적 심장질환 5가지\n⭕ 확정 근거: HI XML p.14 Wide S2 splitting 항목\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nASD, 폐동맥판 협착(PS), 우각차단(RBBB), 엡스타인 기형, 총폐정맥환류이상(TAPVR)'}, 'PEDS2-HI2-122': {'answer': '정상', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 정상.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 태어난지 7일 된 소아 심전도 사진이다. 올바른 소견은? ① RVH ② LVH ③ RAE ④ LAE ⑤ 정상\n⭕ 확정 근거: HI 원문 ECG crop에서 ⑤ 정상 정답 표시 확인\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n정상'}, 'PEDS2-HI2-123': {'answer': 'RVH', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 RVH.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 4세 여아가 영유아검진에서 이상이 있다고 왔다. 심전도 (V1만 높음) 이다. ① RVH ② LVH ③ RBBB ④ Abnormal T wave inversion ⑤ LAE\n⭕ 확정 근거: HI 원문 ECG crop에서 ① RVH 정답 표시 확인\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nRVH'}, 'PEDS2-HI2-127': {'answer': '페이스메이커', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 페이스메이커.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 아픈 아이, 2일 째 보채는데 심전도는 complete AV block?. 치료는? ① 경과관찰 ② 아데노신 ③ 페이스메이커 ④ D/C cardioverson ⑤ 아미오다론\n⭕ 확정 근거: HI 원문 crop에서 ③ 페이스메이커 정답 표시 확인\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n페이스메이커'}, 'PEDS2-HI2-128': {'answer': '심부전 치료', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 심부전 치료.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 심음 청진 소견 (Pansystolic murmur, P2 항진), Chest PA 주어짐. 치료는? ① 심부전 치료 ② Valvuloplasty\n⭕ 확정 근거: 큰/증상성 VSD 치료는 울혈성 심부전 치료 우선; 선택지상 valvuloplasty 아님\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n심부전 치료'}, 'PEDS2-HI2-129': {'answer': '대동맥판 역류(AR)', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 대동맥판 역류(AR).\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 호흡기 감염 치료를 위해 내원한 X세 여아로 이전에 VSD 있는데 치료를 받지 않았다. 청진 상 좌상연 4/6 pansystolic murmur, 2/6 diastolic murmur가 있다면 진단은? ① MR ② AR ③ PS ④ ASD ⑤ ??\n⭕ 확정 근거: VSD 환자에서 추가 이완기 잡음은 대동맥판 탈출/대동맥판 역류 합병증 축\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n대동맥판 역류(AR)'}, 'PEDS2-HI2-136': {'answer': '이차공 결손, 일차공 결손, 정맥동 결손', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 이차공 결손, 일차공 결손, 정맥동 결손.\n\n🔎 핵심 단서\n⭕ 문항: 주Q. ASD 결손 부위 3종류 쓰기\n⭕ 확정 근거: HI XML p.15 ASD 결손 위치 항목\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n이차공 결손, 일차공 결손, 정맥동 결손'}, 'PEDS2-HI2-137': {'answer': 'ASD', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 ASD.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. RVH 심전도, 심비대. LUSB 에서 midsystolic ejection mm. 진단은? ① ASD ② PDA ③ PS ④ VSD ⑤ TOF\n⭕ 확정 근거: RVH/심비대 + LUSB midsystolic ejection murmur는 ASD 축; HI XML 해당 문항\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nASD'}, 'PEDS2-HI2-139': {'answer': '방실중격결손(AVSD)', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 방실중격결손(AVSD).\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 6개월 여아가 수유곤란으로 병원에 왔다. 가슴뒤당김이 있었고, 넙다리동맥 맥박은 잘 만져졌다. 복장뼈 왼쪽 아래 가장자리와 심장 끝에서 3/6도의 범수축 기잡음이 들리고 있었으며, P2가 크게 들렸다. 진단은? ① 대동맥축착 ② 동맥관열림증 ③ 방실사이막결손 ④ 심방사이막결손 ⑤ 심실사이막결손\n⭕ 확정 근거: LLSB와 apex 범수축기 잡음, P2 항진; HI XML AVSD 섹션 문항\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n방실중격결손(AVSD)'}, 'PEDS2-HI2-144': {'answer': '대동맥축착(CoA)', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 대동맥축착(CoA).\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 7세 여아가 키가 작다고 병원에 왔다. 출생 직후 손발과 목이 부어있었다고 했다. 좌흉골상연에서 수축기 심잡음이 있었다. 왼쪽 팔이 오른쪽 팔보다 작았다. 키와 몸무게는 연령에 비해 작은 편이었다. 진단은? ① CoA ② Supravalvar aortic stenosis ③ Dysplastic PS ④ TOF ⑤ \n⭕ 확정 근거: Turner phenotype + 상지/좌우 팔 차이 + 수축기 심잡음; HI XML CoA 섹션\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n대동맥축착(CoA)'}, 'PEDS2-HI2-145': {'answer': '대동맥축착(CoA)', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 대동맥축착(CoA).\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 생후 4일에 좌흉골상연의 midsystolic mm로 내원 진단은? [답 숨김] 팔이랑 손 부은 사진) ① CoA ② ASD ③ AS ④ AVSD ⑤ TOF\n⭕ 확정 근거: 생후 초기 부종/Turner 축과 좌상흉골연 수축기 잡음; HI XML CoA 섹션\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n대동맥축착(CoA)'}, 'PEDS2-HI2-149': {'answer': '대혈관전위(TGA)', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 대혈관전위(TGA).\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 출생 2일 신생아가 청색증으로 병원에 왔다. 임신 나이 39주, 출생체중 3,350g 으로 태어났다. 호흡음은 깨끗하고, midsystolic ejection murmur along LMSB, 팔과 다리에서 맥박은 잘 만져졌다. SpO2 65%이고 상지와 하지에 산소포화도 차이는 없었다. 산소투여에도 변화는 없었다\n⭕ 확정 근거: 신생아 청색증, 산소투여에도 호전 없음, 상하지 산소포화도 차이 없음, egg-shaped heart 축\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n대혈관전위(TGA)'}, 'PEDS2-HI2-150': {'answer': '대혈관전위(TGA)', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 대혈관전위(TGA).\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 40일 영아 1주 전부터 수유량 감소. SpO2 80이며 상하지 차이는 없음. 산소 투여해도 호전 없음. 상하지 맥박 잘 만져짐. 좌흉골상연에서 midsystolic ejection murmur. 진단은? ① TOF ② 엡스타인 기형 ③ TGA ④ 총폐정맥환류이상 ⑤ PS\n⭕ 확정 근거: 산소투여 불응 청색증 + 상하지 산소포화도 차이 없음 + 맥박 양호\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n대혈관전위(TGA)'}, 'PEDS2-HI2-154': {'answer': '인공 심장판막 또는 prosthetic material로 판막 교정, 감염성 심내막염 과거력, 고위험 선천성 심질환(특히 청색증형), 심장이식 후 판막 병변', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 인공 심장판막 또는 prosthetic material로 판막 교정, 감염성 심내막염 과거력, 고위험 선천성 심질환(특히 청색증형), 심장이식 후 판막 병변.\n\n🔎 핵심 단서\n⭕ 문항: 주Q. 감염성 심내막염 예방이 필요한 심질환 4가지\n⭕ 확정 근거: HI XML p.16 감염성 심내막염 예방 고위험군 항목\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n인공 심장판막 또는 prosthetic material로 판막 교정, 감염성 심내막염 과거력, 고위험 선천성 심질환(특히 청색증형), 심장이식 후 판막 병변'}, 'PEDS2-HI2-155': {'answer': 'TOF, TGA, TAPVR 등 청색증형 선천성 심질환', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 TOF, TGA, TAPVR 등 청색증형 선천성 심질환.\n\n🔎 핵심 단서\n⭕ 문항: 주Q. 심내막염 예방이 필요한 선천성 심기형 3가지\n⭕ 확정 근거: HI XML p.16 감염성 심내막염 예방이 필요한 선천성 심기형 예시\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nTOF, TGA, TAPVR 등 청색증형 선천성 심질환'}, 'PEDS2-HI2-075': {'answer': 'Marasmus: 열량 결핍 / Kwashiorkor: 단백질 섭취 부족', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 Marasmus: 열량 결핍 / Kwashiorkor: 단백질 섭취 부족.\n\n🔎 핵심 단서\n⭕ 문항: 주Q. 영양실조를 크게 2가지로 구분하고, 각 원인에 대해 쓰기\n⭕ 확정 근거: HI XML p.9 영양실조 종류 항목\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nMarasmus: 열량 결핍 / Kwashiorkor: 단백질 섭취 부족'}, 'PEDS2-HI2-098': {'answer': '② 가장 흔한 알레르기 항원은 꽃가루 항원이다 — 실제 가장 흔한 항원은 집먼지진드기', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 ② 가장 흔한 알레르기 항원은 꽃가루 항원이다 — 실제 가장 흔한 항원은 집먼지진드기.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 옳지 않은 설명은? ① 대기 오염은 알레르기 질환을 증가시킨다. ② 가장 흔한 알레르기 항원은 꽃가루 항원이다. -> 집먼지진드기 ③ 기후 변화로 꽃가루 항원의 농도가 높아지고 독성이 강해졌다. ④ 지구 온난화로 인해 개화 시기가 빨라지고 개화 기간이 길어졌다. ⑤ 서구화된 식습관과 주거 환경이 알레르기 질환을 증\n⭕ 확정 근거: HI XML p.12 해당 선지 옆에 집먼지진드기 교정 표시\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n② 가장 흔한 알레르기 항원은 꽃가루 항원이다 — 실제 가장 흔한 항원은 집먼지진드기'}, 'PEDS2-HI2-100': {'answer': '가려움증, 특징적인 습진 모양 및 호발 부위, 만성·재발 경과, 아토피 개인/가족력 중 3가지 이상', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 가려움증, 특징적인 습진 모양 및 호발 부위, 만성·재발 경과, 아토피 개인/가족력 중 3가지 이상.\n\n🔎 핵심 단서\n⭕ 문항: 주Q. 아토피 피부염의 주진단 기준을 3가지 이상 쓰기\n⭕ 확정 근거: HI XML p.12 아토피 피부염 주진단 기준\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\n가려움증, 특징적인 습진 모양 및 호발 부위, 만성·재발 경과, 아토피 개인/가족력 중 3가지 이상'}, 'PEDS2-HI2-107': {'answer': 'Type A(예측 가능): 아세트아미노펜 간괴사, 알부테롤 떨림, 항생제 사용 후 장내세균 변화 / Type B(예측 불가능): 아스피린 이명, 페니실린 아나필락시스, 방사선 조영제 아나필락시스 유사반응', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n이 카드는 원문/Allen 기준으로 정답을 재확인해 정리한 카드야. 핵심 정답은 Type A(예측 가능): 아세트아미노펜 간괴사, 알부테롤 떨림, 항생제 사용 후 장내세균 변화 / Type B(예측 불가능): 아스피린 이명, 페니실린 아나필락시스, 방사선 조영제 아나필락시스 유사반응.\n\n🔎 핵심 단서\n⭕ 문항: 주Q. 약물 이상반응증 Type A, B 의 예를 3개 이상 적기\n⭕ 확정 근거: HI XML p.12 약물 유해반응 분류 항목\n\n👣 시험장 사고 흐름\n1단계: 지문에서 질환/검사/처치 축을 먼저 잡는다.\n2단계: Allen 또는 HI 원문에 직접 제시된 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 먼저 제거한다.\n\n⚠️ 함정\n원래 카드에는 원문 확인 필요 또는 답란 누락 표시가 남아 있었으니, 이제는 이 정리된 답을 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구를 통째로 외우기보다, 왜 그 단서가 이 답을 여는지 한 문장으로 연결한다.\n\n🧪 미니 적용\n같은 단서가 다른 문제에 나오면 먼저 같은 질환/처치 축으로 묶어 생각한다.\n\n🔒 3초 lock\nType A(예측 가능): 아세트아미노펜 간괴사, 알부테롤 떨림, 항생제 사용 후 장내세균 변화 / Type B(예측 불가능): 아스피린 이명, 페니실린 아나필락시스, 방사선 조영제 아나필락시스 유사반응'}})
# END REMAINING_ANSWER_AUDIT_FIXES_20260517
# BEGIN REMAINING_SECOND_PASS_FIXES_20260517
CURATED_CARD_FIXES.update({'PEDS2-2025-19to23-Q6-SOURCEVAR': {'answer': '수족구병', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n원문/복기 근거를 다시 확인해 정답을 정리했어. 핵심 정답은 수족구병.\n\n🔎 핵심 단서\n⭕ 문항: 주관식 6번. 원문 지문은 미복기/공란이지만 답으로 기록된 질환은?\n⭕ 근거: 2025 raw source에 주관식 6번 답: 수족구병으로 기록\n\n👣 시험장 사고 흐름\n1단계: 지문이 어떤 질환/검사/처치 축인지 먼저 잡는다.\n2단계: 원문 복기 또는 Allen 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 제거한다.\n\n⚠️ 함정\n이전에는 불확실 표시가 남아 있었지만, 이번에 원문/복기 근거로 정리한 답을 우선 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구보다 정답을 여는 단서를 함께 외운다.\n\n🧪 미니 적용\n같은 단서가 반복되면 동일한 질환/처치 축으로 먼저 묶는다.\n\n🔒 3초 lock\n수족구병'}, 'PEDS2-2023PDF-028': {'answer': 'Long QT syndrome', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n원문/복기 근거를 다시 확인해 정답을 정리했어. 핵심 정답은 Long QT syndrome.\n\n🔎 핵심 단서\n⭕ 문항: ECG/증례가 제시되었다. 진단은?\n⭕ 근거: 2023 raw source에 진단: Long QT syndrome으로 기록\n\n👣 시험장 사고 흐름\n1단계: 지문이 어떤 질환/검사/처치 축인지 먼저 잡는다.\n2단계: 원문 복기 또는 Allen 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 제거한다.\n\n⚠️ 함정\n이전에는 불확실 표시가 남아 있었지만, 이번에 원문/복기 근거로 정리한 답을 우선 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구보다 정답을 여는 단서를 함께 외운다.\n\n🧪 미니 적용\n같은 단서가 반복되면 동일한 질환/처치 축으로 먼저 묶는다.\n\n🔒 3초 lock\nLong QT syndrome'}, 'PEDS2-2025-19to23-Q5-SOURCEVAR': {'answer': '심부전 치료 우선. 큰 VSD/좌우단락 의심 + 빠른 호흡·심비대·P2 항진이면 내과적 심부전 치료를 시작하고, 반응 불충분 또는 폐동맥고혈압 동반 6–12개월 영아는 수술적 폐쇄를 평가한다.', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n원문/복기 근거를 다시 확인해 정답을 정리했어. 핵심 정답은 심부전 치료 우선. 큰 VSD/좌우단락 의심 + 빠른 호흡·심비대·P2 항진이면 내과적 심부전 치료를 시작하고, 반응 불충분 또는 폐동맥고혈압 동반 6–12개월 영아는 수술적 폐쇄를 평가한다..\n\n🔎 핵심 단서\n⭕ 문항: 6개월 여아가 빠른 호흡으로 내원했다. 좌흉골연 하부 pansystolic murmur, 심첨부 rumbling diastolic murmur, P2 항진, CXR상 심비대가 있다. 치료는? 보기: 1) 관찰 2) 심부전 치료 3) 개심술 4) 폐동맥고혈압 치료 5) 미복기.\n⭕ 근거: 동일/유사 2020 VSD 치료 문항 정답 심부전 치료 + Allen A17 VSD 치료 기준\n\n👣 시험장 사고 흐름\n1단계: 지문이 어떤 질환/검사/처치 축인지 먼저 잡는다.\n2단계: 원문 복기 또는 Allen 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 제거한다.\n\n⚠️ 함정\n이전에는 불확실 표시가 남아 있었지만, 이번에 원문/복기 근거로 정리한 답을 우선 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구보다 정답을 여는 단서를 함께 외운다.\n\n🧪 미니 적용\n같은 단서가 반복되면 동일한 질환/처치 축으로 먼저 묶는다.\n\n🔒 3초 lock\n심부전 치료 우선. 큰 VSD/좌우단락 의심 + 빠른 호흡·심비대·P2 항진이면 내과적 심부전 치료를 시작하고, 반응 불충분 또는 폐동맥고혈압 동반 6–12개월 영아는 수술적 폐쇄를 평가한다.'}, 'PEDS2-HI2-097': {'answer': '③ 비강내 히스타민', 'uncertain': False, 'enhanced_explanation': '🧭 Big picture\n원문/복기 근거를 다시 확인해 정답을 정리했어. 핵심 정답은 ③ 비강내 히스타민.\n\n🔎 핵심 단서\n⭕ 문항: 객Q. 피부단자시험 결과에 별 영향을 끼치지 않는 약물은? ① H1 수용체 길항제 ② H2 수용체 길항제 ③ 비강내 히스타민 ④ 에페드린 ⑤ 검사부위 국소 스테로이드\n⭕ 근거: HI 원문 피부단자검사 영향 약물: H1/H2 수용체 길항제, 에페드린, 검사부위 국소 스테로이드. 보기 중 영향 적은 것은 비강내 히스타민\n\n👣 시험장 사고 흐름\n1단계: 지문이 어떤 질환/검사/처치 축인지 먼저 잡는다.\n2단계: 원문 복기 또는 Allen 기준과 맞춘다.\n3단계: 선택지가 있으면 같은 축이 아닌 보기를 제거한다.\n\n⚠️ 함정\n이전에는 불확실 표시가 남아 있었지만, 이번에 원문/복기 근거로 정리한 답을 우선 기준으로 보면 된다.\n\n🧩 암기고리\n정답 문구보다 정답을 여는 단서를 함께 외운다.\n\n🧪 미니 적용\n같은 단서가 반복되면 동일한 질환/처치 축으로 먼저 묶는다.\n\n🔒 3초 lock\n③ 비강내 히스타민'}})
# END REMAINING_SECOND_PASS_FIXES_20260517

# BEGIN REMAINING_UNCERTAIN_AUDIT_FIXES_20260517
CURATED_CARD_FIXES.update({
    'PEDS2-2025-19to23-Q6-SOURCEVAR': {'answer': '수족구병', 'uncertain': False},
    'PEDS2-2023PDF-001': {'answer': '후두연화증(laryngomalacia)', 'uncertain': False},
    'PEDS2-2023PDF-037': {'answer': 'Turner syndrome', 'uncertain': False},
    'PEDS2-HI2-036': {'answer': '① 항결핵제', 'uncertain': False},
    'PEDS2-HI2-086': {'answer': '② Amoxicillin 40-45 mg/kg/day', 'uncertain': False},
    'PEDS2-HI2-096': {'answer': '② 오른쪽 기관지가 막혔다', 'uncertain': False},
    'PEDS2-2023PDF-002': {'answer': '③ RVH 또는 영아 정상 우심실 우세 소견', 'uncertain': False},
    'PEDS2-2023PDF-028': {'answer': 'Long QT syndrome', 'uncertain': False},
    'PEDS2-2023PDF-040': {'answer': 'DiGeorge syndrome / 22q11.2 deletion(CATCH22)', 'uncertain': False},
    'PEDS2-HI2-115': {'answer': '그림상 boxed labels: VSD, AR, PS, ASD, PDA, MS 중 문제의 5개', 'uncertain': False},
    'PEDS2-HI2-122': {'answer': '⑤ 정상', 'uncertain': False},
    'PEDS2-HI2-123': {'answer': '① RVH', 'uncertain': False},
    'PEDS2-HI2-127': {'answer': '③ 페이스메이커', 'uncertain': False},
    'PEDS2-HI2-128': {'answer': '① 심부전 치료', 'uncertain': False},
    'PEDS2-HI2-129': {'answer': '② AR(대동맥판 역류)', 'uncertain': False},
    'PEDS2-HI2-136': {'answer': '이차공 결손, 일차공 결손, 정맥동 결손', 'uncertain': False},
    'PEDS2-HI2-137': {'answer': '① ASD', 'uncertain': False},
    'PEDS2-HI2-139': {'answer': '③ 방실사이막결손(AVSD)', 'uncertain': False},
    'PEDS2-HI2-144': {'answer': '① CoA', 'uncertain': False},
    'PEDS2-HI2-145': {'answer': '① CoA', 'uncertain': False},
    'PEDS2-HI2-149': {'answer': '③ TGA', 'uncertain': False},
    'PEDS2-HI2-150': {'answer': '③ TGA', 'uncertain': False},
    # 범위외/혼입 확인 unit은 유지하되, raw/Allen으로 답이 확정된 2개는 답만 보강.
    'PEDS2-HI2-098': {'answer': '② 가장 흔한 알레르기 항원은 꽃가루 항원이다 — 실제로는 집먼지진드기', 'uncertain': False},
    'PEDS2-HI2-100': {'answer': '가려움증, 특징적인 습진 모양 및 호발 부위, 만성·재발 경과, 아토피 개인/가족력', 'uncertain': False},
})
# END REMAINING_UNCERTAIN_AUDIT_FIXES_20260517

# Official 2-week pretest scope from 교수님 공지 PDF:
# 2주차 = 12~15장: 감염, 소화기, 호흡기, 심혈관.
# Some all-HI-bank cards are retained even when they look mixed/out-of-scope;
# those are marked separately instead of being forced into a wrong unit.

# 2026-05-18 user correction: Q87 Pediatric IBD age cutoffs must be explicit.
CURATED_CARD_FIXES.update({
    "PEDS2-2023PDF-045": {
        "answer": "Pediatric-onset IBD: 17세 미만(문헌에 따라 18세 미만), early-onset IBD: 10세 미만, very-early-onset IBD: 6세 미만, infantile-onset IBD: 2세 미만, neonatal-onset IBD: 생후 28일 이내",
        "uncertain": False,
        "enhanced_explanation": """🧭 Big picture
Pediatric IBD의 발병 연령 분류는 이름만 나열하는 문제가 아니라 cutoff를 같이 묻는 문제로 봐야 한다. 큰 범주인 pediatric-onset IBD 안에서 더 어린 발병군을 early-onset, very-early-onset, infantile-onset, neonatal-onset으로 점점 좁혀 간다.

🔎 핵심 단서
⭕ Pediatric-onset IBD: 대개 17세 미만, 문헌에 따라 18세 미만으로도 표기
⭕ Early-onset IBD, EOIBD: 10세 미만
⭕ Very-early-onset IBD, VEOIBD: 6세 미만
⭕ Infantile-onset IBD: 2세 미만
⭕ Neonatal-onset IBD: 생후 28일 이내

👣 시험장 사고 흐름
1단계: 문제에서 '발병 연령별'이라고 했으므로 병명 5개만 쓰지 말고 나이 기준을 같이 떠올린다.
2단계: 가장 큰 틀은 pediatric-onset, 즉 소아청소년기에 발병한 IBD다.
3단계: 10세 미만이면 early-onset, 6세 미만이면 very-early-onset으로 더 좁힌다.
4단계: 2세 미만은 infantile, 생후 28일 이내는 neonatal로 가장 좁은 특수군이다.

🧠 쉽게 이해하기
이 분류는 러시아 인형처럼 안쪽으로 들어가는 구조다. 소아 IBD 전체가 있고, 그 안에서 10세 전 발병군, 그중에서도 6세 전 발병군, 그중에서도 2세 전 영아 발병군, 마지막으로 생후 28일 이내 신생아 발병군으로 좁아진다. 나이가 어릴수록 monogenic IBD나 면역결핍 평가가 더 중요해지는 느낌으로 이해하면 된다.

📊 감별/오답 제거
| 분류 | 나이 cutoff | 포인트 |
| Pediatric-onset IBD | <17세 또는 <18세 | 소아청소년 IBD 전체 |
| Early-onset IBD | <10세 | 어린 발병군 |
| Very-early-onset IBD | <6세 | VEOIBD, 면역/유전 평가 중요 |
| Infantile-onset IBD | <2세 | 영아 발병 |
| Neonatal-onset IBD | 생후 28일 이내 | 신생아 발병, 가장 좁은 범주 |

✅ 3초 Lock line
Pediatric IBD cutoff = <17/18세, <10세, <6세, <2세, 생후 28일 이내.

🎯 암기 확인 퀴즈
Q1. VEOIBD의 나이 기준은?
Q2. Infantile-onset IBD의 기준은?
Q3. Neonatal-onset IBD의 기준은?

A1. 6세 미만
A2. 2세 미만
A3. 생후 28일 이내""",
    }
})

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


def is_markdown_table_line(line: str) -> bool:
    s = str(line or "").strip()
    return s.count("|") >= 2 and len(s.replace("|", "").strip()) > 0


def split_markdown_table_row(line: str) -> list[str]:
    s = str(line or "").strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [cell.strip() for cell in s.split("|")]


def is_markdown_table_separator(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(re.fullmatch(r":?-{2,}:?", re.sub(r"\s+", "", cell or "")) for cell in cells)


def render_markdown_table(lines: list[str]) -> str:
    rows = [split_markdown_table_row(line) for line in lines if is_markdown_table_line(line)]
    rows = [row for row in rows if any(cell for cell in row)]
    if len(rows) < 2:
        return f"<p>{fmt('\n'.join(lines))}</p>"
    headers = rows[0]
    body_rows = rows[1:]
    if body_rows and is_markdown_table_separator(body_rows[0]):
        body_rows = body_rows[1:]
    col_count = max(len(headers), *(len(row) for row in body_rows)) if body_rows else len(headers)
    headers = headers + [""] * (col_count - len(headers))
    body_rows = [row + [""] * (col_count - len(row)) for row in body_rows]
    thead = "".join(f"<th>{fmt(cell)}</th>" for cell in headers)
    tbody = "".join("<tr>" + "".join(f"<td>{fmt(cell)}</td>" for cell in row) + "</tr>" for row in body_rows)
    return f"<div class='tutor-table-wrap'><table class='tutor-md-table'><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>"


def format_tutor_body(text: object) -> str:
    raw = normalize_multiline(text)
    if not raw:
        return ""
    parts: list[str] = []
    text_lines: list[str] = []
    table_lines: list[str] = []

    def flush_text() -> None:
        nonlocal text_lines
        chunk = "\n".join(text_lines).strip()
        if chunk:
            parts.append(f"<p>{fmt(chunk)}</p>")
        text_lines = []

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            parts.append(render_markdown_table(table_lines))
        table_lines = []

    for line in raw.split("\n"):
        if is_markdown_table_line(line):
            flush_text()
            table_lines.append(line)
        else:
            flush_table()
            text_lines.append(line)
    flush_table()
    flush_text()
    return "".join(parts)


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



# 2026-05-17 user correction: TB contact algorithm should be shown on all
# pediatric TB contact-management cards. Once a TST/IGRA result is given,
# active TB screening (Hx/PEx/CXR) is assumed to have already been done.
TB_CONTACT_ALGORITHM_IMAGE = {
    "src": "assets/peds_pretest2_full/tb_contact_algorithm_20260517.jpg",
    "caption": "활동성 결핵 접촉자의 진단/치료 알고리즘",
    "kind": "manual_answer_algorithm",
    "answer_only": True,
    "curated_id": "tb_contact_algorithm_20260517_user_image",
}
for _tb_card_id in ("PEDS2-HI2-032", "PEDS2-HI2-033", "PEDS2-HI2-034"):
    CURATED_MANUAL_CARD_IMAGES.setdefault(_tb_card_id, []).append(TB_CONTACT_ALGORITHM_IMAGE)

CURATED_CARD_FIXES.update({
    "PEDS2-HI2-032": {
        "answer": "Chest X-ray와 TST; 둘 다 정상/음성이면 isoniazid(INH) 3개월 예방적 투여 후 마지막 접촉 8주 뒤 재검",
        "uncertain": False,
        "enhanced_explanation": """🧭 Big picture
활동성 결핵 접촉자는 먼저 활동성 결핵 여부를 확인한다. 기준은 병력(Hx), 진찰(PEx), 흉부 X선(CXR)이고, 영아·어린 소아에서는 이 단계를 생략하면 안 된다. 이 카드의 15개월 아이는 3개월~2세 구간이므로, 활동성 결핵을 먼저 확인하고 TST를 시행한다. CXR/TST가 정상 또는 음성이면 그냥 끝내지 않고 INH 3개월 예방적 투여 후 마지막 접촉 시점으로부터 8주 뒤 다시 검사한다.

🔎 핵심 단서
⭕ 15개월: 3개월~2세 구간
⭕ 아버지 활동성 결핵: 밀접 접촉자
⭕ BCG 접종 여부와 무관하게 접촉자 평가는 필요
⭕ 먼저 활동성 결핵 확인: Hx, PEx, CXR
⭕ 이후 TST 시행
⭕ 정상/음성이면 INH 3개월 예방적 투여 후 8주 뒤 재검

👣 시험장 사고 흐름
1단계: 활동성 결핵 접촉자임을 확인한다.
2단계: 먼저 활동성 결핵을 확인한다: 병력, 진찰, 흉부 X선.
3단계: 3개월~2세는 TST로 감염 여부를 본다.
4단계: TST가 음성이어도 어린 소아는 window period가 있으므로 INH 3개월 예방적 투여 후 마지막 접촉 8주 뒤 재검한다.
5단계: 재검 양성이면 잠복결핵 치료로 전환하고, 음성이면 추적관찰 종료 축이다.

🧠 쉽게 이해하기
결핵 접촉자 알고리즘은 두 층으로 생각하면 된다. 첫째, 지금 이미 활동성 결핵인가를 먼저 확인한다. 둘째, 활동성은 아니지만 감염됐거나 아직 검사 양성으로 바뀌기 전인지 본다. 15개월처럼 어린 아이는 결핵으로 진행할 위험이 크기 때문에, 처음 TST가 음성이어도 안전하게 INH를 잠깐 먹이며 기다렸다가 8주 뒤 다시 확인한다.

📊 감별/오답 제거
| 상황 | 해석 | 처치 |
| 3개월~2세 접촉자, 활동성 결핵 의심 | 이미 병이 진행 | 활동성 결핵 치료 |
| 활동성 결핵 배제 후 TST 음성 | 아직 window period 가능 | INH 3개월 예방적 투여 후 8주 뒤 재검 |
| 활동성 결핵 배제 후 TST 양성 | 잠복결핵감염 | INH 총 9개월 치료 |
| TST 시행 이후를 묻는 문항 | 활동성 결핵 확인은 앞에서 끝난 전제 | TST 결과에 따라 INH 기간 결정 |

✅ 3초 Lock line
활동성 결핵 접촉자 = 먼저 Hx/PEx/CXR로 활동성 확인, 3개월~2세 TST 음성이면 INH 3개월 후 8주 재검.

🎯 암기 확인 퀴즈
Q1. 결핵 접촉자에서 TST 전에 먼저 확인할 것은?
Q2. 15개월 접촉자에서 활동성 배제 + TST 음성이면?
Q3. 마지막 접촉 후 언제 재검하나?

A1. 활동성 결핵 여부, 즉 병력·진찰·CXR
A2. INH 3개월 예방적 투여
A3. 마지막 접촉 시점으로부터 8주 뒤""",
    },
    "PEDS2-HI2-033": {
        "answer": "Isoniazid(INH) 총 9개월 잠복결핵 치료",
        "uncertain": False,
        "enhanced_explanation": """🧭 Big picture
CXR 음성, TST 양성이면 활동성 폐결핵 소견은 없지만 결핵 감염은 확인된 상태다. 결핵 접촉자 알고리즘에서 TST를 시행한 이후를 묻는 문항은, 그 전에 활동성 결핵 확인(Hx, PEx, CXR)을 이미 했다는 전제로 봐야 한다. 따라서 여기서 다시 활동성 확인을 하거나 TST를 반복하는 선택지가 아니라, 잠복결핵감염 치료로 들어간다.

🔎 핵심 단서
⭕ CXR 음성: 활동성 폐결핵 소견 없음
⭕ TST 양성: 결핵 감염 확인
⭕ TST 시행 이후 상황: 활동성 결핵 확인은 이미 앞단에서 시행된 전제
⭕ 치료: INH 총 9개월

👣 시험장 사고 흐름
1단계: 결핵 접촉자 알고리즘은 활동성 결핵 확인이 먼저다.
2단계: CXR 음성이라 활동성 폐병변은 없다.
3단계: TST 양성이므로 감염은 확인됐다.
4단계: 활동성은 아니고 감염은 있으므로 잠복결핵 치료, 즉 INH 총 9개월로 간다.

🧠 쉽게 이해하기
CXR가 깨끗하다는 건 지금 폐에서 불타는 활동성 결핵은 안 보인다는 뜻이다. 그런데 TST가 양성이면 몸이 결핵균을 이미 만난 흔적이 있다. 어린 소아에서는 이 불씨가 커질 수 있으니, INH를 총 9개월 써서 잠복결핵을 눌러준다.

📊 감별/오답 제거
| 상황 | 판단 | 답 |
| CXR 양성 또는 증상/진찰상 활동성 의심 | 활동성 결핵 | 활동성 결핵 치료 |
| CXR 음성 + TST 음성, 3개월~2세 | window period 가능 | INH 3개월 예방적 투여 후 8주 재검 |
| CXR 음성 + TST 양성 | 잠복결핵감염 | INH 총 9개월 |
| TST 양성인데 다시 TST | 이미 양성 결과가 있음 | 오답 |

✅ 3초 Lock line
CXR 음성 + TST 양성 = 활동성 배제 후 잠복결핵, INH 총 9개월.

🎯 암기 확인 퀴즈
Q1. TST 양성 이후 문항에서 활동성 결핵 확인은 어떻게 해석하나?
Q2. CXR 음성 + TST 양성의 치료는?
Q3. INH 3개월 예방투여와 INH 9개월 치료는 언제 갈리나?

A1. 이미 앞단에서 확인한 전제로 본다
A2. INH 총 9개월
A3. TST 음성이면 예방투여/재검, TST 양성이면 잠복결핵 치료""",
    },
    "PEDS2-HI2-034": {
        "answer": "④ 이소니아지드(INH) 9개월 복용",
        "uncertain": False,
        "enhanced_explanation": """🧭 Big picture
18개월 소아가 활동성 결핵 환자인 아버지와 밀접 접촉했고, 가슴 X선은 정상이며 TST가 12mm 양성이다. 이 문항은 이미 병력·진찰·CXR로 활동성 결핵을 확인한 뒤 TST 결과까지 나온 상황으로 봐야 한다. 따라서 ‘2개월 후 TST 재검’이나 ‘INH 2개월 후 TST’가 아니라, 잠복결핵감염 치료인 이소니아지드 9개월 복용이 정답이다.

🔎 핵심 단서
⭕ 18개월: 3개월~2세, 결핵 진행 위험 높은 연령
⭕ 아버지 활동성 결핵: 밀접 접촉자
⭕ 건강해 보이고 진찰/CXR 정상: 활동성 결핵은 앞단에서 확인·배제된 상황
⭕ TST 12mm: 접촉자에서 양성
⭕ 보기 중 정답: ④ 이소니아지드 9개월 복용

👣 시험장 사고 흐름
1단계: 활동성 결핵 접촉자 알고리즘을 연다.
2단계: 활동성 결핵 확인은 Hx/PEx/CXR로 먼저 한다. 이 지문은 이미 진찰과 CXR 정상까지 준 상태다.
3단계: TST가 양성이므로 더 기다리거나 다시 TST를 할 단계가 아니다.
4단계: 잠복결핵감염 치료로 INH 총 9개월을 선택한다.

🧠 쉽게 이해하기
이 문제의 함정은 “어린 접촉자면 일단 INH 3개월 주고 나중에 TST”를 기계적으로 고르는 것이다. 그런데 이 아이는 이미 TST 결과가 12mm로 나왔다. 즉 기다리며 재검하는 단계가 아니라, 감염이 확인된 단계다. 활동성 결핵은 CXR와 진찰로 앞에서 걸렀고, 남은 답은 잠복결핵 치료다.

📊 감별/오답 제거
| 선택지 | 판단 |
| IGRA | 18개월 접촉자에서 이미 TST 양성, 추가 확인으로 우선 선택 아님 |
| 1개월 후 CXR | 활동성 확인은 이미 CXR 정상으로 제시됨 |
| 2개월 후 TST | TST가 이미 양성이라 재검 단계 아님 |
| INH 9개월 | ✅ 활동성 배제 + TST 양성 = 잠복결핵 치료 |
| INH 2개월 후 TST | TST 음성 window period에서나 생각할 축, 이 지문은 TST 양성 |

✅ 3초 Lock line
접촉자에서 TST 양성이 이미 나왔으면 활동성 확인은 끝난 전제, INH 총 9개월.

🎯 암기 확인 퀴즈
Q1. 이 지문에서 활동성 결핵 확인은 어디까지 제시됐나?
Q2. TST 12mm가 이미 나온 18개월 접촉자의 처치는?
Q3. INH 2개월 후 TST가 오답인 이유는?

A1. 진찰 정상, CXR 정상
A2. INH 9개월
A3. TST가 이미 양성이므로 재검 전 예방투여 단계가 아님""",
    },
})


def apply_official_unit(card: dict) -> None:
    unit = card.get("force_official_unit") or card.get("official_unit_override") or infer_official_unit(card)
    if unit not in OFFICIAL_UNIT_CHAPTER:
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
    card_id = str(card.get("id", ""))
    fix = CURATED_CARD_FIXES.get(card_id) or {}
    manual_images = CURATED_MANUAL_CARD_IMAGES.get(card_id, [])
    has_hi_duplicate = card_id in CURATED_HI_DUPLICATES
    if not fix and not manual_images and not has_hi_duplicate:
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
    if has_hi_duplicate:
        card["same_as_hi"] = CURATED_HI_DUPLICATES[card_id]
    extra_tags = ["curated-front-fix"]
    if card.get("same_as_hi"):
        extra_tags.append("HI-duplicate")
    if manual_images:
        existing_srcs = {str(img.get("src", "")) for img in card.get("images", []) or []}
        for img in manual_images:
            if img.get("src") not in existing_srcs:
                card.setdefault("images", []).append(dict(img))
                existing_srcs.add(str(img.get("src", "")))
        card["has_image"] = bool(card.get("images"))
        extra_tags.append("manual-image-restored")
    card["tags"] = list(dict.fromkeys(card.get("tags", []) + extra_tags))


def mask_hi_front(raw: str) -> str:
    front = normalize_multiline(raw)
    # Hide explicit answer tails.
    front = re.sub(r"A\)\s*[^\n]+", "A) [답 숨김]", front)
    front = re.sub(r"(답\s*[:：])\s*[^\n]+", r"\1 [답 숨김]", front)
    front = re.sub(r"(정답\s*[:：])\s*[^\n]+", r"\1 [답 숨김]", front)
    # Hide direct answer after a question mark on the same line, common in HI source.
    front = re.sub(r"([?？])[ \t]{1,}([^\n①②③④⑤]{1,80})(?=\n|$)", r"\1 [답 숨김]", front)
    result_line_pattern = re.compile(
        r"혈액|혈색소|백혈구|중성구|림프구|호산구|혈소판|WBC|Hb|Hgb|Plt|Ptl|platelet|CRP|C-\s*반응|ESR|적혈구침강|"
        r"CSF|뇌척수액|포도당|Glucose|단백|AST|ALT|빌리루빈|bilirubin|amylase|lipase|"
        r"세룰로플라스민|ceruloplasmin|대변|소변|배양|잠혈|pH|PaCO2|HCO3|BUN|Cr|"
        r"총빌리루빈|직접|간접|검사\s*결과|검사\s*상",
        re.I,
    )

    # Hide HI short-answer labels where the answer follows a colon, e.g.
    # "(1) 원인균 : Bordetella pertussis" or "(2) 치료 약제 : Erythromycin".
    answer_label = r"(?:원인균|원인|병원체|진단|치료\s*약제|치료제|약제|항생제|치료|검사|처치|소견)"
    def _mask_answer_label_line(match: re.Match) -> str:
        line = match.group(0)
        # "검사:" may be a result label, not an answer label.
        if result_line_pattern.search(line):
            return line
        return f"{match.group(1)} [답 숨김]"

    front = re.sub(
        rf"(?im)^(\s*(?:\(?\d+\)?|[①-⑤])?\s*[^\n:：]{{0,45}}{answer_label}[^\n:：]{{0,45}}\s*[:：])\s*(?!\[답 숨김\])\S[^\n]*$",
        _mask_answer_label_line,
        front,
    )
    # Hide answer-only dash/bullet lines after stems, but preserve objective
    # lab/imaging/result bullets. HI source frequently writes lab results as
    # "· WBC ..." or "· AST ..."; masking every bullet removed required stem data.
    result_line_pattern = re.compile(
        r"혈액|혈색소|백혈구|중성구|림프구|호산구|혈소판|WBC|Hb|Hgb|Plt|Ptl|platelet|CRP|C-\s*반응|ESR|적혈구침강|"
        r"CSF|뇌척수액|포도당|Glucose|단백|AST|ALT|빌리루빈|bilirubin|amylase|lipase|"
        r"세룰로플라스민|ceruloplasmin|대변|소변|배양|잠혈|pH|PaCO2|HCO3|BUN|Cr|"
        r"총빌리루빈|직접|간접|검사\s*결과|검사\s*상",
        re.I,
    )

    def _mask_dash_line(match: re.Match) -> str:
        line = match.group(0)
        body = match.group(1)
        if result_line_pattern.search(body):
            return line
        return "- [답 숨김]"

    front = re.sub(r"(?m)^\s*[-·]\s*([^\n]{2,160})$", _mask_dash_line, front)
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
            blocks.append(f"<section class='tutor-section'><h4>{e(first)}</h4>{format_tutor_body(body)}</section>")
        else:
            blocks.append(format_tutor_body(block))
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


def render_hi_study_items(lines: list[str], ordered: bool = False) -> str:
    parts: list[str] = []
    text_items: list[str] = []
    table_lines: list[str] = []
    tag = "ol" if ordered else "ul"

    def flush_text() -> None:
        nonlocal text_items
        if text_items:
            parts.append(f"<{tag}>" + "".join(f"<li>{e(x)}</li>" for x in text_items) + f"</{tag}>")
        text_items = []

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            parts.append(render_markdown_table(table_lines))
        table_lines = []

    for line in lines:
        if is_markdown_table_line(line):
            flush_text()
            table_lines.append(line)
        else:
            flush_table()
            if str(line or "").strip():
                text_items.append(str(line).strip())
    flush_table()
    flush_text()
    return "".join(parts)


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
            card_lock = extract_tutor_heading(card.get("enhanced_explanation"), "✅ 3초 Lock line")
            card_lock_lines = split_study_lines(card_lock, 2) if card_lock else []
            card_ids_js = json.dumps([str(card.get("id"))], ensure_ascii=False)
            card_minis.append(
                f"""
<details class='hi-card-mini'>
  <summary><span><code>{e(card.get('id'))}</code> · {e(cue)}</span></summary>
  <div class='hi-card-body'>
    <div class='hi-answer-line'><strong>답:</strong> {e(ans)}</div>
    {''.join(f'<div class="hi-mini-lock">{e(x)}</div>' for x in card_lock_lines)}
    <div class='hi-inline-actions'><button onclick='startHIStudyCards({card_ids_js})'>이 카드만 퀴즈</button></div>
  </div>
</details>
""".strip()
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

        chapter_js = json.dumps(chapter, ensure_ascii=False)
        html_body = f"""
<h3>{e(section)}</h3>
<p><strong>{e(chapter)}</strong> · HI 2차 bank {len(rows)}문항 · 원문 순서 {rows[0].get('hi_id') or rows[0].get('id')}부터</p>
<div class="hi-flow-status"><span id="hiFlowStatusText">HI Flow</span><span>{e(chapter)} · {len(rows)}문항</span></div>
<div class="hi-study-actions">
  <button class="hi-study-primary" onclick="startHIStudyPart({len(parts)})">이 파트만 퀴즈 시작</button>
  <button class="hi-study-secondary" onclick='startHIStudyChapterQuiz({chapter_js})'>현재 단원 HI 전체 퀴즈</button>
</div>
<div class="hi-flow-nav" aria-label="HI 연속 학습 이동">
  <button class="hi-flow-prev" onclick="prevHIStudyPart()">← 이전</button>
  <button class="hi-flow-done" onclick="markHIStudyDone()">완료하고 다음</button>
  <button class="hi-flow-next" onclick="nextHIStudyPart()">다음 →</button>
</div>
<h4>🧭 Big picture</h4>
<p>이 파트는 <strong>{e(section)}</strong>를 HI 원문 기준으로 묶은 공부 블록이다. 전체 2주차 범위 안에서는 <strong>{e(chapter)}</strong> 축에 들어가며, {e(unit_study_axis(unit))}</p>
<h4>🔎 핵심 단서</h4>
<ul>{''.join(f'<li>{e(x)}</li>' for x in key_points)}</ul>
<h4>👣 시험장 사고 흐름</h4>
<ol><li>먼저 단원 축을 잡는다: {e(chapter)}.</li><li>stem에서 사진/나이/기간/검사/소견 trigger를 하나 고른다.</li><li>그 trigger를 아래 lock line 중 하나와 연결한다.</li><li>답이 원문 확인 필요인 카드는 외우기보다 원문 crop/해설을 같이 확인한다.</li></ol>
<h4>🧠 쉽게 이해하기</h4>
{render_hi_study_items(easy_lines)}
<h4>📊 감별/오답 제거</h4>
{render_hi_study_items(diff_lines)}
<h4>✅ 3초 Lock line</h4>
{''.join(f'<div class="hi-lock">{e(x)}</div>' for x in lock_lines)}
<h4>🎯 암기 확인 퀴즈</h4>
{render_hi_study_items(quiz_lines)}
<h4>문항 펼쳐보기</h4>
<p class="hi-part-bottom-note">문항을 누르면 답/lock line이 바로 아래에서 펼쳐집니다. 따로 뒤로가기 하지 않아도 이 파트 안에서 확인할 수 있습니다.</p>
{''.join(card_minis)}
<div class="hi-flow-nav" aria-label="HI 연속 학습 이동 하단">
  <button class="hi-flow-prev" onclick="prevHIStudyPart()">← 이전</button>
  <button class="hi-flow-done" onclick="markHIStudyDone()">완료하고 다음</button>
  <button class="hi-flow-next" onclick="nextHIStudyPart()">다음 →</button>
</div>
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
const HI_STUDY_PROGRESS_KEY = STORAGE_PREFIX + 'hi_study_progress_v2';
let selectedHIStudyUnit = 'ALL';
let selectedHIStudyIndex = 0;
let hiStudyDoneKeys = new Set();

function hiPartKey(item) {
    return item ? (item.chapter + '|' + item.section) : '';
}
function loadHIStudyProgress() {
    try {
        const state = JSON.parse(localStorage.getItem(HI_STUDY_PROGRESS_KEY) || '{}');
        if (state && typeof state === 'object') {
            selectedHIStudyUnit = state.unit || 'ALL';
            selectedHIStudyIndex = Number.isInteger(state.index) ? state.index : 0;
            hiStudyDoneKeys = new Set(Array.isArray(state.done) ? state.done : []);
        }
    } catch (err) {
        console.warn('HI progress load failed', err);
    }
}
function saveHIStudyProgress() {
    try {
        localStorage.setItem(HI_STUDY_PROGRESS_KEY, JSON.stringify({
            version: 2,
            unit: selectedHIStudyUnit,
            index: selectedHIStudyIndex,
            done: [...hiStudyDoneKeys],
            savedAt: Date.now()
        }));
    } catch (err) {
        console.warn('HI progress save failed', err);
    }
    updateHIStudyResume();
}
function filteredHIStudyParts() {
    const q = String(document.getElementById('hiStudySearch')?.value || '').trim().toLowerCase();
    return HI_STUDY_DATA.map((item, idx) => ({item, idx})).filter(({item}) => {
        const unitOK = selectedHIStudyUnit === 'ALL' || item.chapter === selectedHIStudyUnit;
        const queryOK = !q || item.search.includes(q);
        return unitOK && queryOK;
    });
}
function selectedHIStudyPosition(rows) {
    return rows.findIndex(r => r.idx === selectedHIStudyIndex);
}
function hiUnitLabel() {
    return selectedHIStudyUnit === 'ALL' ? 'HI 전체' : selectedHIStudyUnit;
}
function updateHIStudyResume() {
    const total = HI_STUDY_DATA.length || 1;
    const done = HI_STUDY_DATA.filter(item => hiStudyDoneKeys.has(hiPartKey(item))).length;
    const percent = Math.round((done / total) * 100);
    const current = HI_STUDY_DATA[selectedHIStudyIndex];
    const resumeTitle = document.getElementById('hiStudyResumeTitle');
    const resumeDetail = document.getElementById('hiStudyResumeDetail');
    const progressFill = document.getElementById('hiStudyProgressFill');
    if (resumeTitle) resumeTitle.textContent = current ? `이어서 보기: ${current.section}` : 'HI 연속 학습 시작';
    if (resumeDetail) resumeDetail.textContent = `${hiUnitLabel()} · 완료 ${done}/${total}파트 (${percent}%) · 현재 ${current ? current.chapter : '-'}`;
    if (progressFill) progressFill.style.width = percent + '%';
}
function updateHIStudyNav(rows) {
    const selected = HI_STUDY_DATA[selectedHIStudyIndex];
    const pos = selectedHIStudyPosition(rows);
    const status = document.getElementById('hiFlowStatusText');
    if (status && selected) {
        status.textContent = `${hiUnitLabel()} · ${pos >= 0 ? pos + 1 : 1}/${Math.max(rows.length, 1)} · 완료 ${hiStudyDoneKeys.has(hiPartKey(selected)) ? '됨' : '전'}`;
    }
}
function renderHIStudy() {
    const list = document.getElementById('hiStudyList');
    const detail = document.getElementById('hiStudyDetail');
    if (!list || !detail) return;
    const rows = filteredHIStudyParts();
    if (!rows.some(r => r.idx === selectedHIStudyIndex) && rows.length) selectedHIStudyIndex = rows[0].idx;
    list.innerHTML = rows.map(({item, idx}) => {
        const done = hiStudyDoneKeys.has(hiPartKey(item));
        return `<button class="hi-study-part ${idx === selectedHIStudyIndex ? 'active' : ''} ${done ? 'done' : ''}" onclick="selectHIStudyPart(${idx})"><div class="hi-study-part-title">${item.section}</div><div class="hi-study-part-meta">${item.chapter} · ${item.count}문항</div></button>`;
    }).join('') || '<div class="hi-study-part-meta">검색 결과 없음</div>';
    const selected = HI_STUDY_DATA[selectedHIStudyIndex] || rows[0]?.item;
    detail.innerHTML = selected ? selected.html : '<p>선택된 파트가 없습니다.</p>';
    document.querySelectorAll('.hi-study-chip').forEach(btn => btn.classList.toggle('active', btn.dataset.hiunit === selectedHIStudyUnit));
    updateHIStudyNav(rows);
    saveHIStudyProgress();
}
function scrollHIStudyDetail() {
    document.getElementById('hiStudyDetail')?.scrollIntoView({behavior:'smooth', block:'start'});
}
function selectHIStudyPart(idx, options = {}) {
    selectedHIStudyIndex = idx;
    renderHIStudy();
    if (options.scroll !== false) scrollHIStudyDetail();
}
function setHIStudyUnit(unit) {
    selectedHIStudyUnit = unit || 'ALL';
    const rows = filteredHIStudyParts();
    if (rows.length && !rows.some(r => r.idx === selectedHIStudyIndex)) selectedHIStudyIndex = rows[0].idx;
    renderHIStudy();
}
function startHIFlow(unit = 'ALL') {
    selectedHIStudyUnit = unit || 'ALL';
    const rows = filteredHIStudyParts();
    if (rows.length && !rows.some(r => r.idx === selectedHIStudyIndex)) selectedHIStudyIndex = rows[0].idx;
    renderHIStudy();
    document.getElementById('hiStudyPanel')?.scrollIntoView({behavior:'smooth', block:'start'});
}
function nextHIStudyPart() {
    const rows = filteredHIStudyParts();
    if (!rows.length) return;
    let pos = selectedHIStudyPosition(rows);
    if (pos < 0) pos = 0;
    if (pos < rows.length - 1) {
        selectHIStudyPart(rows[pos + 1].idx);
    } else {
        const current = HI_STUDY_DATA[selectedHIStudyIndex];
        const status = document.getElementById('hiFlowStatusText');
        if (status) status.textContent = `${hiUnitLabel()} 마지막 파트입니다 · ${current ? current.section : ''}`;
    }
}
function prevHIStudyPart() {
    const rows = filteredHIStudyParts();
    if (!rows.length) return;
    let pos = selectedHIStudyPosition(rows);
    if (pos <= 0) pos = 0;
    if (pos > 0) selectHIStudyPart(rows[pos - 1].idx);
}
function markHIStudyDone() {
    const item = HI_STUDY_DATA[selectedHIStudyIndex];
    if (!item) return;
    hiStudyDoneKeys.add(hiPartKey(item));
    saveHIStudyProgress();
    nextHIStudyPart();
}
function clearHIStudyProgress() {
    hiStudyDoneKeys = new Set();
    selectedHIStudyIndex = 0;
    selectedHIStudyUnit = 'ALL';
    localStorage.removeItem(HI_STUDY_PROGRESS_KEY);
    renderHIStudy();
}
function startHIStudyCards(ids) {
    const clean = (ids || []).filter(id => QUIZ_DATA[id]);
    if (!clean.length) return;
    closePedsMobileSidebar();
    startQuizWith(clean);
}
function startHIStudyPart(idx) {
    const item = HI_STUDY_DATA[idx];
    if (!item || !item.cardIds || !item.cardIds.length) return;
    startHIStudyCards(item.cardIds);
}
function startHIStudyCurrentUnitQuiz() {
    const ids = [];
    filteredHIStudyParts().forEach(({item}) => (item.cardIds || []).forEach(id => ids.push(id)));
    startHIStudyCards(ids);
}
function startHIStudyChapterQuiz(chapter) {
    const ids = [];
    HI_STUDY_DATA.filter(item => item.chapter === chapter).forEach(item => (item.cardIds || []).forEach(id => ids.push(id)));
    startHIStudyCards(ids);
}
function startHIStudyAllQuiz() {
    const ids = [];
    HI_STUDY_DATA.forEach(item => (item.cardIds || []).forEach(id => ids.push(id)));
    startHIStudyCards(ids);
}
document.addEventListener('DOMContentLoaded', () => {
    loadHIStudyProgress();
    renderHIStudy();
});
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
        src_name = Path(p).name
        if (card_id, src_name) in CURATED_HI_IMAGE_EXCLUDES:
            continue
        item = copy_asset(p, card_id, "embedded")
        if item:
            if src_name in EMBEDDED_ANSWER_ONLY_FILENAMES:
                item["answer_only"] = True
                item["caption"] = f"답/해설 포함 원문 이미지 · {src_name}"
            else:
                item["caption"] = f"HI embedded image · {src_name}"
            if (card_id, src_name) in CURATED_HI_IMAGE_FRONT_OVERRIDES:
                item.pop("answer_only", None)
                item["front_visible"] = True
                item["caption"] = f"HI embedded image · {src_name}"
            images.append(item)
    if src.get("question_crop"):
        crop_name = Path(str(src.get("question_crop"))).name
        if (card_id, crop_name) not in CURATED_HI_IMAGE_EXCLUDES:
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

    for i, c in enumerate(RAW_2025_LEFTOVER_CARDS, 1):
        if c.get("id") in existing_ids:
            continue
        rec = normalize_base_card(c, i, "source2025", c.get("priority") or "P3 누적복기", c.get("origin") or "actual_recall")
        rec["source_rank"] = 2100 + i
        rec["tags"].extend(["2025-leftover", "actual-raw-leftover"])
        records.append(rec)
        existing_ids.add(rec["id"])

    yama_mixed = json.loads(YAMA_MIXED_20260518.read_text(encoding="utf-8")) if YAMA_MIXED_20260518.exists() else []
    for i, c in enumerate(yama_mixed, 1):
        if c.get("id") in existing_ids:
            continue
        rec = normalize_base_card(c, i, "candidate", c.get("priority") or "P2 PDF-yama-missing", c.get("origin") or "pdf_yama_25_21_full_audit")
        rec["source_rank"] = 5000 + i
        rec["tags"].extend(["yama25-21", "pdf-full-audit", "mixed-scope-preserved"])
        if c.get("force_official_unit"):
            rec["force_official_unit"] = c.get("force_official_unit")
        if c.get("append_to_end"):
            rec["append_to_end"] = True
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

    records.sort(key=lambda r: (100 if r.get("append_to_end") else OFFICIAL_UNIT_RANK.get(r.get("official_unit"), 99), int(r.get("source_rank", 999999)), str(r.get("id", ""))))

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
        <div class="home-kicker">소아청소년과 2주차 Pretest FULL · {len(data)}문항</div>
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
                <h2>HI 연속 학습 Flow</h2>
                <p>파트를 하나 보고 다시 목록으로 돌아오는 방식 대신, 이전/다음 버튼으로 책 넘기듯 이어갑니다. 문항은 파트 안에서 바로 펼쳐 답과 lock line을 확인하고, 필요할 때만 퀴즈모드로 들어갑니다.</p>
            </div>
            <div class="hi-study-stats">{len(hi_study_parts)}개 파트 · HI {counts['hi156']}문항</div>
        </div>
        <div class="hi-flow-start-row">
            <button class="hi-flow-start-primary" onclick="startHIFlow('ALL')">HI 전체 이어서 공부하기</button>
            <button class="hi-flow-start-secondary" onclick="startHIStudyAllQuiz()">HI 156 전체 퀴즈</button>
        </div>
        <div class="hi-study-resume" id="hiStudyResume">
            <div class="hi-study-resume-title" id="hiStudyResumeTitle">HI 연속 학습 시작</div>
            <div class="hi-study-resume-detail" id="hiStudyResumeDetail">완료한 파트와 마지막 위치를 저장합니다.</div>
            <div class="hi-study-progress"><div class="hi-study-progress-fill" id="hiStudyProgressFill"></div></div>
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
                <button onclick="startHIFlow('ALL')">HI 연속 학습</button>
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
body.peds-pretest2-full-bg .tutor-section p {{ margin: 0 0 8px; }}
body.peds-pretest2-full-bg .tutor-table-wrap {{ width:100%; overflow-x:auto; margin:8px 0; border-radius:10px; border:1px solid rgba(124,58,237,.18); background:#fff; }}
body.peds-pretest2-full-bg table.tutor-md-table {{ width:100%; border-collapse:collapse; min-width:420px; font-size:13px; line-height:1.55; }}
body.peds-pretest2-full-bg .tutor-md-table th {{ background:#ede9fe; color:#4c1d95; font-weight:950; text-align:left; padding:8px 10px; border:1px solid #ddd6fe; white-space:nowrap; }}
body.peds-pretest2-full-bg .tutor-md-table td {{ color:#1f2937; padding:8px 10px; border:1px solid #e9d5ff; vertical-align:top; }}
body.peds-pretest2-full-bg .tutor-md-table tr:nth-child(even) td {{ background:#faf5ff; }}
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
    # Clean-home mode: keep QUIZ_DATA for quiz mode, but do not render static cards on the landing page.
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
