#!/usr/bin/env python3
"""Generate a hypertension CPX study + roleplay quiz app."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "quizzes" / "고혈압_CPX_공부_환자역할_퀴즈.html"
PDF_ENV = "HYPERTENSION_CPX_PDF"

DISEASES = [
    {
        "id": "essential",
        "emoji": "🧂",
        "title": "본태성(일차성) 고혈압",
        "summary": "특별한 범인을 못 잡았는데 혈압이 꾸준히 높은 타입. 현실에서는 이 친구가 제일 흔해요.",
        "metaphor": "집 전체 배선은 멀쩡한데, 수도 압력이 늘 조금 과한 집이라고 생각하면 돼요. 범인은 한 명이 아니라 생활습관+체질이 단체로 장난치는 느낌 😅",
        "clues": [
            "반복 측정해도 혈압이 높음",
            "비만, 복부비만, 짠 음식, 운동 부족, 스트레스가 같이 보이기 쉬움",
            "다른 이차성 원인을 물어봐도 결정적 단서가 약함",
        ],
        "ask": [
            "집에서도 높았는지",
            "짜게 먹는지, 운동은 하는지",
            "당뇨/이상지질혈증/흡연 같은 심혈관 위험인자",
        ],
        "tests": ["반복 혈압 측정", "안저 확인", "기본 혈액·소변검사"],
        "treatment": ["생활습관 교정", "항고혈압제", "목표 혈압 설명"],
        "joke": "고혈압계가 괜히 예민한 게 아니라, 몸이 매일 '짠맛 파티 그만!'이라고 공지 올리는 중입니다 📢",
    },
    {
        "id": "whitecoat",
        "emoji": "🥼",
        "title": "백의고혈압",
        "summary": "병원만 오면 혈압이 올라가는 타입. 혈압계 앞에서 심장이 면접 보는 느낌이에요.",
        "metaphor": "평소엔 멀쩡한데 교무실만 들어가면 괜히 심박수 올라가는 학생 같은 패턴 😵‍💫",
        "clues": [
            "병원에서는 150/90, 160/95처럼 높음",
            "집에서는 120/80 정도로 정상",
            "병원 올 때 유독 긴장, 얼굴 홍조, 손땀을 호소하기도 함",
        ],
        "ask": ["집에서 잰 혈압", "24시간 활동혈압(ABPM) 여부", "측정 전 안정했는지"],
        "tests": ["가정혈압", "24시간 활동혈압", "반복 측정"],
        "treatment": ["지금 당장 약은 아닐 수 있음", "자가혈압 교육", "6~12개월 추적"],
        "joke": "의사 가운만 보면 혈압이 '출석 체크!' 하고 튀어 오르는 케이스 👔📈",
    },
    {
        "id": "masked",
        "emoji": "🎭",
        "title": "가면 고혈압",
        "summary": "병원에서는 얌전한데 집에서는 높아요. 이름 그대로 혈압이 마스크 쓰고 다니는 타입.",
        "metaphor": "학교에서는 조용한데 집에서 게임 켜면 텐션 폭발하는 친구 같은 반전형 🎮",
        "clues": [
            "진료실에서는 정상처럼 보임",
            "집·직장·일상에서는 높게 나옴",
            "스트레스 많은 생활에서 놓치기 쉬움",
        ],
        "ask": ["집이나 약국에서 재본 적 있는지", "아침/저녁 기록이 있는지"],
        "tests": ["가정혈압", "24시간 활동혈압"],
        "treatment": ["진짜 고혈압처럼 관리", "위험인자 동시 교정"],
        "joke": "병원에서는 모범생, 집에서는 문제아. 혈압에도 이중생활이 있습니다 🎭",
    },
    {
        "id": "drug",
        "emoji": "💊",
        "title": "약물 유발 고혈압",
        "summary": "스테로이드, NSAIDs, 에스트로겐, 감기약/각성제 등이 혈압을 끌어올리는 경우예요.",
        "metaphor": "원래 조용한 동네에 외부 응원단이 와서 확성기 틀어버린 느낌 📣",
        "clues": [
            "최근 진통제(ibuprofen), 스테로이드, 피임약, 한약, ADHD 약 등 복용력",
            "복용 시작 후 혈압 상승",
            "중단 시 회복 가능",
        ],
        "ask": ["복용약 전체", "언제부터 먹었는지", "임의로 산 약/건강식품도 포함"],
        "tests": ["약물력 확인", "필요시 기본 혈액검사"],
        "treatment": ["원인 약 조정·중단", "필요하면 혈압약 추가"],
        "joke": "환자가 '약은 별로 안 먹어요'라고 해도, 가방 속 진통제가 반전 주인공일 수 있어요 👜",
    },
    {
        "id": "hyperthyroid",
        "emoji": "🔥",
        "title": "갑상샘항진증 관련 고혈압",
        "summary": "몸의 엔진이 과열된 상태라 심박수와 혈압이 같이 올라갑니다.",
        "metaphor": "자동차 엑셀이 계속 밟힌 상태. 몸이 '공회전'을 못 멈추는 거예요 🚗💨",
        "clues": [
            "두근거림, 발한, 더위불내성",
            "체중 감소, 손 떨림, 안구 돌출 가능",
            "혈압과 맥박이 같이 들썩임",
        ],
        "ask": ["더위 참기 힘든지", "땀이 많은지", "체중이 빠졌는지"],
        "tests": ["TSH↓, Free T4↑", "심전도", "필요시 갑상샘 초음파"],
        "treatment": ["Methimazole", "β차단제", "카페인·스트레스 피하기"],
        "joke": "몸속 보일러가 고장 나서 4계절 내내 한여름 모드인 셈이에요 🌞",
    },
    {
        "id": "renovascular",
        "emoji": "🚰",
        "title": "신혈관성 고혈압(신동맥 협착)",
        "summary": "신장으로 가는 혈류가 줄어 신장이 '어? 피가 부족한데?' 하고 RAAS를 과하게 켭니다.",
        "metaphor": "집 수압은 충분한데 수도계량기가 고장 나서 계속 '물 부족!' 경보 울리는 상황 🚨",
        "clues": [
            "젊은 나이의 고혈압",
            "복부 bruit",
            "ACEi/ARB 후 신기능 악화 가능",
            "조절 안 되는 혈압",
        ],
        "ask": ["언제부터인지", "복부 잡음 들은 적 있는지", "기존 혈압약 후 악화했는지"],
        "tests": ["신장 도플러", "신초음파", "혈관 조영술(확진)"],
        "treatment": ["혈압약 조정", "필요시 혈관 성형술"],
        "joke": "신장이 착각이 심한 날엔, 정상 혈압도 '낮다!'고 오해하고 호르몬을 팍팍 뿌립니다 😵",
    },
    {
        "id": "aldo",
        "emoji": "🧂⚡",
        "title": "원발성 알도스테론증",
        "summary": "알도스테론이 너무 많이 나와서 소금과 물을 붙잡고, 칼륨은 버리는 질환입니다.",
        "metaphor": "몸이 '물과 소금 저금통'이 돼서 저축은 과하게 하고, 칼륨은 월급처럼 줄줄 새는 상태 💸",
        "clues": [
            "고혈압 + 저칼륨",
            "근력저하, 손발저림, 경련, 피로",
            "젊고 약으로 잘 안 잡히는 고혈압",
        ],
        "ask": ["칼륨 낮다는 말 들은 적 있는지", "근력저하/경련 있는지"],
        "tests": ["renin/aldosterone ratio", "전해질", "생리식염수 부하", "복부 CT"],
        "treatment": ["Spironolactone/Eplerenone", "Amiloride", "일측성은 수술"],
        "joke": "나트륨은 붙들고 칼륨은 해고하는, 편애가 심한 호르몬 매니저입니다 🙃",
    },
    {
        "id": "pheo",
        "emoji": "🎢",
        "title": "갈색세포종",
        "summary": "카테콜아민이 폭주해서 혈압이 롤러코스터처럼 오르내립니다.",
        "metaphor": "몸속에 비상벨 덕후가 있어서 아무도 안 불렀는데 계속 '긴급상황!' 외치는 상태 🚨🎢",
        "clues": [
            "두통 + 발한 + 두근거림",
            "발작성 혈압 상승",
            "기립성 저혈압, 오심/복통이 같이 오기도 함",
        ],
        "ask": ["발작처럼 오는지", "땀과 두근거림이 같이 오는지"],
        "tests": ["혈중 유리 메타네프린", "24시간 소변 메타네프린", "복부 CT/MRI"],
        "treatment": ["α차단제 먼저(Phenoxybenzamine/Doxazosin)", "그 다음 필요 시 β차단제", "부신절제술"],
        "joke": "이 병에서 β차단제부터 먼저 쓰면 큰일나요. 줄 안 서고 새치기하면 놀이기구 멈춥니다 🎢❌",
    },
    {
        "id": "cushing",
        "emoji": "🌙",
        "title": "쿠싱증후군",
        "summary": "코르티솔이 오래 과해서 중심성 비만, 자색선조, 고혈압이 같이 보일 수 있어요.",
        "metaphor": "몸이 스테로이드 모드로 오래 굴러가서 지방 배치도 이상해지고 압력도 올라간 상태예요 🍩",
        "clues": [
            "최근 체중 증가, 특히 배쪽",
            "둥근 얼굴, 보라색 선조",
            "여드름, 다모증, 허벅지 힘 빠짐",
            "스테로이드 복용력",
        ],
        "ask": ["스테로이드 먹는지", "몸통 살만 찌는지", "자색선조 있는지"],
        "tests": ["24시간 소변 cortisol", "덱사메타손 억제 검사"],
        "treatment": ["원인 교정", "스테로이드 감량", "필요시 혈압약"],
        "joke": "살이 찐 게 게으름 때문이 아니라, 호르몬이 인테리어를 이상하게 해놓은 겁니다 🛋️",
    },
    {
        "id": "ckd",
        "emoji": "🫘",
        "title": "만성신질환/치료저항성 고혈압",
        "summary": "신장이 오래 아프면 혈압 조절이 잘 안 되고, 약을 여러 개 써도 잘 안 잡힐 수 있어요.",
        "metaphor": "정수 필터가 망가지면 수압과 물 상태가 같이 꼬이는 것과 비슷합니다 🚿",
        "clues": [
            "거품뇨, 부종, 소변량 감소",
            "Cr 상승, 신질환 병력",
            "이뇨제 포함 3제 이상 써도 조절 안 되는 resistant HTN",
        ],
        "ask": ["신장병 진단받았는지", "거품뇨/부종 있는지", "약 몇 개 먹는지"],
        "tests": ["BUN/Cr", "소변검사", "신장초음파"],
        "treatment": ["생활관리", "ACEi/ARB", "필요시 신대체요법"],
        "joke": "혈압이 말을 안 듣는다고 환자 탓만 하면 안 돼요. 뒤에서 신장이 '나 지금 바빠!' 하는 중일 수 있습니다 😮‍💨",
    },
    {
        "id": "gestational",
        "emoji": "🤰",
        "title": "임신성 고혈압",
        "summary": "임신 20주 이후 새로 생긴 고혈압인데, 전신 증상이 뚜렷하지 않은 경우예요.",
        "metaphor": "임신이라는 큰 프로젝트 중에 혈압 팀이 과로해서 살짝 오버하는 느낌 🤰📈",
        "clues": [
            "20주 이후 새 고혈압",
            "두통/시야장애/경련/심한 단백뇨가 없으면 임신성 HTN 쪽",
            "임신 전에는 고혈압 병력 없음",
        ],
        "ask": ["임신 몇 주차인지", "임신 전 혈압은 어땠는지", "단백뇨/두통/시야장애 있는지"],
        "tests": ["혈압 추적", "소변단백", "산과 평가"],
        "treatment": ["Labetalol/Hydralazine/Nifedipine(상황 따라)", "산과 추적"],
        "joke": "임신은 공동과제인데, 혈압이 갑자기 혼자 분량 늘려버린 상황입니다 📚",
    },
    {
        "id": "preeclampsia",
        "emoji": "⚠️🤰",
        "title": "전자간증",
        "summary": "임신 20주 이후 고혈압 + 단백뇨 또는 전신 장기 증상이 붙으면 전자간증을 강하게 생각해요.",
        "metaphor": "임신성 고혈압이 '업그레이드'돼서 Brain·Eye·Kidney까지 건드리기 시작한 상태예요 🚨",
        "clues": [
            "두통, 시야장애, 부종, 단백뇨",
            "심하면 경련까지 → eclampsia",
            "산모·태아 모두 위험",
        ],
        "ask": ["두통 있는지", "눈이 침침한지", "거품뇨/부종/경련 있었는지"],
        "tests": ["소변단백", "간기능/신장기능/혈소판", "혈압 재측정"],
        "treatment": ["심한 경우 MgSO4", "Labetalol/Hydralazine/Nifedipine", "분만 시점 판단"],
        "joke": "이건 '조금 높네요~' 하고 넘길 병이 아니라, 산모 몸이 비상 깜빡이 켠 상황입니다 🚨",
    },
]

CASES = [
    {
        "id": "essential_50m",
        "diagnosis": "본태성 고혈압",
        "study_id": "essential",
        "difficulty": "기본형",
        "intro": "50세 남성입니다.",
        "answers": {
            "greeting": "네, 안녕하세요. 저는 50살 남자예요.",
            "chief": "건강검진에서 혈압이 높다고 해서 왔어요.",
            "onset": "1년 전 건강검진에서도 150/90 정도였고, 이번에도 비슷하게 높다고 들었어요.",
            "where": "병원하고 건강검진에서 재봤고, 오늘도 높다고 하네요. 집에서는 잘 안 재봤어요.",
            "home": "집에서는 거의 안 재봤어요.",
            "measurement": "오늘은 커피나 담배는 안 하고 왔고, 조금 쉬고 재긴 했어요.",
            "symptoms": "특별히 아픈 곳은 없어요. 두통이나 시야장애, 가슴통증, 소변 이상도 없어요.",
            "endocrine": "살이 좀 쪘고 운동은 잘 안 해요. 땀이 특별히 많거나 두근거리는 건 없어요.",
            "sleep": "코골이는 좀 있는 것 같아요.",
            "meds": "혈압약은 아직 안 먹고 있어요. 다른 약도 특별히 없어요.",
            "past": "당뇨나 큰 병은 없어요.",
            "surgery": "수술한 적은 없어요.",
            "family": "아버지가 고혈압, 당뇨 있으셨어요.",
            "social": "운동은 거의 안 하고, 배달음식이랑 짠 안주를 좋아해요. 복부비만도 있는 편이에요.",
            "female": "해당 없어요.",
            "unknown": "그건 잘 모르겠고, 제가 느끼기엔 그냥 혈압이 높다고만 들었어요.",
        },
        "hint": ["반복 혈압 상승", "비만/복부비만", "뚜렷한 이차성 단서 없음"],
        "reveal": {
            "diagnosis": "본태성 고혈압",
            "why": ["반복 측정에서 지속적 상승", "위험인자(비만, 짠 식이, 운동 부족)", "이차성 고혈압 단서가 약함"],
            "tests": ["반복 혈압 측정", "안저", "기본 혈액·소변검사"],
            "treatment": ["생활습관 교정", "필요 시 항고혈압제", "목표 혈압 교육"],
        },
    },
    {
        "id": "whitecoat_35f",
        "diagnosis": "백의고혈압",
        "study_id": "whitecoat",
        "difficulty": "함정형",
        "intro": "35세 여성입니다.",
        "answers": {
            "greeting": "안녕하세요, 35살 여자예요.",
            "chief": "병원만 오면 혈압이 높다고 해서 걱정돼서 왔어요.",
            "onset": "예전부터 병원 갈 때마다 높다는 말을 종종 들었어요.",
            "where": "병원에서는 150/90, 오늘은 160/95까지 나왔대요. 근데 집에서는 120/80 정도예요.",
            "home": "네, 집에서 재면 정상 범위예요.",
            "measurement": "병원 오면 좀 긴장돼요. 얼굴도 좀 달아오르고 손에 땀도 나는 편이에요.",
            "symptoms": "특별히 두통이나 시야장애는 없어요.",
            "endocrine": "체중 변화나 땀 폭발 같은 건 없어요. 그냥 긴장되는 느낌이에요.",
            "sleep": "수면은 괜찮아요.",
            "meds": "혈압약은 안 먹어요.",
            "past": "큰 병 없어요.",
            "surgery": "수술력 없어요.",
            "family": "가족 중 고혈압은 있긴 한데, 저는 집에선 괜찮아요.",
            "social": "직장 스트레스가 좀 있고, 병원 오면 더 불안해져요.",
            "female": "임신은 아니고 생리도 규칙적이에요.",
            "unknown": "병원에서만 그러는 것 같아서 저도 좀 헷갈려요.",
        },
        "hint": ["병원에서만 상승", "집에서는 정상", "긴장/홍조/손땀"],
        "reveal": {
            "diagnosis": "백의고혈압",
            "why": ["진료실 혈압만 높음", "가정혈압 정상", "긴장으로 일시적 상승"],
            "tests": ["가정혈압", "24시간 활동혈압"],
            "treatment": ["약보다 추적관찰", "자가혈압 교육", "6~12개월 follow-up"],
        },
    },
    {
        "id": "drug_nsaid_60f",
        "diagnosis": "약물 유발 고혈압",
        "study_id": "drug",
        "difficulty": "약물형",
        "intro": "60세 여성입니다.",
        "answers": {
            "greeting": "네, 60살 여자예요.",
            "chief": "며칠 전부터 혈압이 높게 나왔어요.",
            "onset": "3일 전 병원에서 150/90이라고 들었고, 집에서도 비슷하게 나왔어요.",
            "where": "병원, 집 둘 다 비슷하게 높았어요.",
            "home": "네, 집에서도 비슷했어요.",
            "measurement": "운동이나 커피는 안 하고 쟀어요.",
            "symptoms": "2일 전부터 속쓰림, 소화불량, 오심, 두통이 있어요.",
            "endocrine": "체중 변화나 더위불내성은 없어요.",
            "sleep": "수면은 괜찮아요.",
            "meds": "몸살감기처럼 아파서 약국에서 ibuprofen을 하루 3번 먹었어요.",
            "past": "고혈압 진단받은 적은 없어요.",
            "surgery": "수술력 없어요.",
            "family": "가족 중 고혈압은 특별히 잘 모르겠어요.",
            "social": "평소엔 큰 문제 없어요.",
            "female": "폐경은 됐어요.",
            "unknown": "약 때문일 수도 있는 건가요? 그런 생각은 못 했어요.",
        },
        "hint": ["최근 NSAID 복용", "병원·집 모두 상승", "이전 고혈압 병력 없음"],
        "reveal": {
            "diagnosis": "약물 유발 고혈압",
            "why": ["최근 NSAID 복용력", "새로 생긴 혈압 상승", "다른 단서보다 약물력이 핵심"],
            "tests": ["약물력 재확인", "필요시 기본 검사"],
            "treatment": ["원인 약 중단/조정", "증상 따라 혈압약"],
        },
    },
    {
        "id": "hyperthyroid_30f",
        "diagnosis": "갑상샘항진증 관련 고혈압",
        "study_id": "hyperthyroid",
        "difficulty": "내분비형",
        "intro": "30세 여성입니다.",
        "answers": {
            "greeting": "안녕하세요, 30살 여자예요.",
            "chief": "혈압이 높다고 해서 왔는데, 두근거림도 있어요.",
            "onset": "한 달 전 건강검진에서 혈압 높다고 들었고, 요즘 더 신경 쓰여요.",
            "where": "병원에서 160/110 정도였어요.",
            "home": "집에서는 잘 안 재봤어요.",
            "measurement": "오늘은 커피나 담배는 안 했어요.",
            "symptoms": "두근거리고, 체중이 좀 빠졌고, 땀이 많고 더위를 잘 못 참겠어요.",
            "endocrine": "눈이 약간 튀어나온다고 들은 적도 있어요.",
            "sleep": "더워서 잠이 좀 불편할 때가 있어요.",
            "meds": "혈압약은 안 먹어요.",
            "past": "큰 병은 없어요.",
            "surgery": "수술은 없어요.",
            "family": "엄마가 갑상샘항진증이 있었어요.",
            "social": "운동은 잘 안 하고, 평소 덥다고 에어컨을 자주 틀어요.",
            "female": "생리 주기가 조금 짧아졌고 양도 줄었어요.",
            "unknown": "제가 좀 열이 많은 체질인 줄만 알았어요.",
        },
        "hint": ["두근거림", "체중감소", "발한/더위불내성"],
        "reveal": {
            "diagnosis": "갑상샘항진증 관련 고혈압",
            "why": ["전형적 갑상샘항진 증상", "맥박/혈압 상승", "가족력도 힌트"],
            "tests": ["TSH, Free T4", "심전도"],
            "treatment": ["Methimazole", "β차단제"],
        },
    },
    {
        "id": "ckd_resistant_60m",
        "diagnosis": "만성신질환 + 치료저항성 고혈압",
        "study_id": "ckd",
        "difficulty": "저항성형",
        "intro": "60세 남성입니다.",
        "answers": {
            "greeting": "네, 60살 남자예요.",
            "chief": "혈압약을 먹는데도 잘 안 잡혀서 왔어요.",
            "onset": "5년 전에 신부전 때문에 고혈압 진단받았어요.",
            "where": "오늘도 병원에서 160/110이라고 했어요.",
            "home": "집에서도 왔다 갔다 하는데 높을 때가 많아요.",
            "measurement": "오늘은 쉬고 재긴 했어요.",
            "symptoms": "거품뇨, 부종, 소변량이 좀 줄고 피로감이 있어요.",
            "endocrine": "땀 폭발이나 체중 감소는 없어요.",
            "sleep": "코골이는 좀 있어요.",
            "meds": "amlodipine, telmisartan, thiazide 먹고 있어요. 꾸준히 먹는데도 잘 안 돼요.",
            "past": "당뇨도 10년 됐어요.",
            "surgery": "수술은 없어요.",
            "family": "아버지가 고혈압 있었어요.",
            "social": "운동은 잘 안 하고, 짠 안주에 술을 자주 먹었어요.",
            "female": "해당 없어요.",
            "unknown": "약을 먹는데도 이러니까 좀 겁나요.",
        },
        "hint": ["3제 복용", "신부전 병력", "거품뇨·부종"],
        "reveal": {
            "diagnosis": "만성신질환/치료저항성 고혈압",
            "why": ["CKD 병력", "이뇨제 포함 3제", "표적장기·신장 증상 동반"],
            "tests": ["BUN/Cr", "소변검사", "신장초음파"],
            "treatment": ["복약 순응도 확인", "생활관리", "약 조정"],
        },
    },
    {
        "id": "ras_30f",
        "diagnosis": "신혈관성 고혈압",
        "study_id": "renovascular",
        "difficulty": "복부 bruit형",
        "intro": "30세 여성입니다.",
        "answers": {
            "greeting": "안녕하세요, 30살 여자예요.",
            "chief": "혈압이 잘 조절이 안 된다고 해서 왔어요.",
            "onset": "젊을 때부터 높다는 말은 없었는데, 최근 확 높아졌어요.",
            "where": "병원에서는 160/110까지 나왔어요.",
            "home": "집에서도 꽤 높게 나와요.",
            "measurement": "오늘은 안정하고 쟀어요.",
            "symptoms": "거품뇨랑 하지부종이 있고 피곤해요.",
            "endocrine": "두근거림이나 열감은 없어요.",
            "sleep": "수면은 보통이에요.",
            "meds": "혈압약은 먹고 있는데 반응이 별로예요.",
            "past": "특별한 내분비 질환은 없어요.",
            "surgery": "없어요.",
            "family": "가족력은 뚜렷하지 않아요.",
            "social": "운동은 안 하고 식사는 불규칙해요.",
            "female": "생리는 규칙적이고 임신은 아니에요.",
            "unknown": "예전에 복부 잡음 얘길 들은 적은 있어요.",
        },
        "hint": ["젊은 여성", "복부 bruit 힌트", "조절 불량"],
        "reveal": {
            "diagnosis": "신혈관성 고혈압",
            "why": ["젊은 나이의 심한 혈압", "복부 bruit", "약 반응 불량"],
            "tests": ["신장 도플러", "신초음파", "혈관 조영술"],
            "treatment": ["약 조정", "필요시 혈관 성형술"],
        },
    },
    {
        "id": "aldo_50f",
        "diagnosis": "원발성 알도스테론증",
        "study_id": "aldo",
        "difficulty": "저칼륨형",
        "intro": "50세 여성입니다.",
        "answers": {
            "greeting": "네, 50살 여자예요.",
            "chief": "혈압이 오르내리고 두통도 있어요.",
            "onset": "3년 전쯤 고혈압 진단받았는데 요즘 더 신경 쓰여요.",
            "where": "병원에서 160/110이라고 들었어요.",
            "home": "집에서도 들쭉날쭉한데 높을 때가 있어요.",
            "measurement": "오늘은 안정하고 쟀어요.",
            "symptoms": "두통도 있고, 피곤하고, 근력이 좀 떨어지고 손발 저릴 때도 있어요.",
            "endocrine": "땀이 갑자기 폭발하거나 체중이 빠지는 건 없어요.",
            "sleep": "코골이는 없어요.",
            "meds": "혈압약은 먹는데 잘 안 잡히는 느낌이에요.",
            "past": "건강검진에서 전해질이 이상하다고 들은 적이 있어요. 칼륨이 낮다고 했던 것 같아요.",
            "surgery": "수술은 없어요.",
            "family": "고혈압 가족력은 좀 있어요.",
            "social": "운동은 거의 안 하고 식사는 불규칙해요.",
            "female": "생리는 끝났어요.",
            "unknown": "그때 검진에서 뭐가 낮다고 했는데 자세히는 기억 안 나요.",
        },
        "hint": ["고혈압 + 저칼륨 힌트", "근력저하", "약 반응 불량"],
        "reveal": {
            "diagnosis": "원발성 알도스테론증",
            "why": ["저칼륨 힌트", "근력저하/저림", "조절 안 되는 혈압"],
            "tests": ["ARR", "전해질", "생리식염수 부하", "복부 CT"],
            "treatment": ["Spironolactone/Eplerenone", "수술 가능성"],
        },
    },
    {
        "id": "pheo_30f",
        "diagnosis": "갈색세포종",
        "study_id": "pheo",
        "difficulty": "발작성형",
        "intro": "30세 여성입니다.",
        "answers": {
            "greeting": "안녕하세요, 30살 여자예요.",
            "chief": "혈압이 확 오를 때가 있고 두통이 심해요.",
            "onset": "최근 들어 발작처럼 반복돼요.",
            "where": "병원에서는 160/110이라고 했어요.",
            "home": "집에서도 오를 때가 있고, 괜찮을 때도 있어요.",
            "measurement": "잴 때마다 들쭉날쭉해요.",
            "symptoms": "두통이 오면서 두근거리고, 식은땀이 나고, 가끔 메스꺼워요.",
            "endocrine": "체중은 큰 변화 없어요. 대신 발작처럼 증상이 와요.",
            "sleep": "가끔 불안해서 잠이 깨요.",
            "meds": "혈압약은 아직 본격적으로 안 먹었어요.",
            "past": "특별한 병은 없어요.",
            "surgery": "수술력은 없어요.",
            "family": "아버지가 내분비 종양 수술 받았다는 얘기는 있어요.",
            "social": "커피, 에너지음료는 거의 안 해요.",
            "female": "생리는 규칙적이에요.",
            "unknown": "한 번 시작되면 롤러코스터 타는 것처럼 심장이 벌렁거려요.",
        },
        "hint": ["두통", "발한", "두근거림", "혈압 변동"],
        "reveal": {
            "diagnosis": "갈색세포종",
            "why": ["3대 증상", "발작성", "가족력 힌트"],
            "tests": ["혈중 유리 메타네프린", "24시간 소변 메타네프린", "복부 CT/MRI"],
            "treatment": ["α차단제 먼저", "필요시 β차단제", "부신절제술"],
        },
    },
    {
        "id": "cushing_steroid",
        "diagnosis": "쿠싱증후군/스테로이드 관련 고혈압",
        "study_id": "cushing",
        "difficulty": "외형형",
        "intro": "30세 여성입니다.",
        "answers": {
            "greeting": "안녕하세요, 30살 여자예요.",
            "chief": "혈압이 높다고 하고, 살도 좀 이상하게 쪘어요.",
            "onset": "최근 몇 달 사이에 더 심해졌어요.",
            "where": "병원에서 160/110이라고 들었어요.",
            "home": "집에서는 잘 안 재봤어요.",
            "measurement": "오늘은 안정하고 쟀어요.",
            "symptoms": "배쪽 살이 많이 찌고, 얼굴이 둥글어지고, 배에 보라색 줄도 생겼어요. 허벅지에 힘도 빠져요.",
            "endocrine": "여드름이랑 털도 좀 늘었어요.",
            "sleep": "수면은 그냥 그래요.",
            "meds": "prednisolone 10~15mg을 10개월 정도 먹고 있어요.",
            "past": "SLE 진단받았어요.",
            "surgery": "수술은 없어요.",
            "family": "가족력은 특별한 건 없어요.",
            "social": "운동은 거의 안 해요.",
            "female": "생리도 좀 불규칙해졌어요.",
            "unknown": "그냥 살찐 줄 알았는데 배쪽만 너무 심해요.",
        },
        "hint": ["중심성 비만", "자색선조", "스테로이드 복용"],
        "reveal": {
            "diagnosis": "쿠싱증후군/스테로이드 관련 고혈압",
            "why": ["전형적 외형", "근위부 근력저하", "장기 스테로이드"],
            "tests": ["cortisol 검사", "DST"],
            "treatment": ["원인 교정", "스테로이드 감량", "필요시 혈압약"],
        },
    },
    {
        "id": "gestational_25w",
        "diagnosis": "임신성 고혈압",
        "study_id": "gestational",
        "difficulty": "산과 기본형",
        "intro": "30세 여성, 임신 25주차입니다.",
        "answers": {
            "greeting": "안녕하세요, 30살이고 지금 임신 25주예요.",
            "chief": "임신하고 나서 혈압이 높다고 해서 왔어요.",
            "onset": "24주쯤부터 높다고 들었어요.",
            "where": "병원에서 높다고 했어요.",
            "home": "집에서는 자주 안 재봤어요.",
            "measurement": "오늘은 쉬고 재긴 했어요.",
            "symptoms": "두통이나 시야장애는 없고, 거품뇨도 잘 모르겠어요.",
            "endocrine": "특별한 내분비 증상은 없어요.",
            "sleep": "임신해서 좀 피곤하긴 해요.",
            "meds": "혈압약은 아직 없어요.",
            "past": "임신 전엔 고혈압 없었어요.",
            "surgery": "없어요.",
            "family": "가족 중 고혈압은 있어요.",
            "social": "음주, 흡연 없어요.",
            "female": "첫 임신이고, 임신 전보다 체중은 좀 늘었어요.",
            "unknown": "아기가 걱정돼서 왔어요.",
        },
        "hint": ["임신 20주 이후", "새 고혈압", "중증 증상 없음"],
        "reveal": {
            "diagnosis": "임신성 고혈압",
            "why": ["20주 이후 시작", "임신 전 고혈압 병력 없음", "전신 증상 부족"],
            "tests": ["혈압 추적", "소변단백", "산과 평가"],
            "treatment": ["상황 따라 Labetalol/Hydralazine/Nifedipine", "추적관찰"],
        },
    },
    {
        "id": "preeclampsia_25w",
        "diagnosis": "전자간증",
        "study_id": "preeclampsia",
        "difficulty": "산과 심화형",
        "intro": "30세 여성, 임신 25주차입니다.",
        "answers": {
            "greeting": "안녕하세요, 30살이고 지금 임신 25주예요.",
            "chief": "혈압이 높다고 했고 머리도 아프고 몸이 붓는 것 같아요.",
            "onset": "24주쯤부터 혈압 높다고 들었어요.",
            "where": "병원에서 높다고 했어요.",
            "home": "집에서는 잘 안 재봤어요.",
            "measurement": "오늘은 쉬고 재긴 했어요.",
            "symptoms": "두통이 있고, 눈이 좀 침침할 때가 있어요. 거품뇨도 있어요.",
            "endocrine": "체중이 갑자기 확 빠지거나 그런 건 없어요.",
            "sleep": "임신 때문에 잠이 좀 불편해요.",
            "meds": "혈압약은 아직 없어요.",
            "past": "임신 전에는 고혈압 없었어요.",
            "surgery": "없어요.",
            "family": "특별한 산과 가족력은 몰라요.",
            "social": "음주, 흡연 없어요.",
            "female": "첫 임신이고, 경련은 아직 없었어요.",
            "unknown": "아기랑 저 둘 다 괜찮은지 제일 걱정돼요.",
        },
        "hint": ["임신 20주 이후", "두통/시야장애", "단백뇨 힌트"],
        "reveal": {
            "diagnosis": "전자간증",
            "why": ["임신 20주 이후 고혈압", "두통/시야증상", "단백뇨 시사"],
            "tests": ["소변단백", "간기능·Cr·혈소판", "산과 평가"],
            "treatment": ["심하면 MgSO4", "혈압 조절", "분만 시점 판단"],
        },
    },
]

COMMON_QUESTIONS = [
    "안녕하세요. 성함과 나이가 어떻게 되세요?",
    "오늘 어디가 불편해서 오셨어요?",
    "혈압이 높다는 건 언제부터 아셨어요?",
    "어디에서 재셨고, 집에서도 높았나요?",
    "혈압 재기 전에 커피, 담배, 운동은 안 하셨어요?",
    "두통, 시야장애, 가슴통증, 두근거림은 있으세요?",
    "거품뇨나 부종, 소변량 변화는 있나요?",
    "평소 드시는 약이나 건강식품 있으세요?",
    "가족 중에 고혈압이나 신장질환 있으세요?",
    "임신 중이거나 생리 변화는 있으세요?",
]

SOURCE_KEYPOINTS = [
    "진료실 혈압 ≥140/90, 가정혈압은 보통 135/85 기준으로 본다 📏",
    "이차성 고혈압 red flag: ≤35세 또는 ≥55세 새 발생, 180/110 이상, 저칼륨, 복부 bruit, 갑자기 조절 악화 🚨",
    "White coat HTN은 병원에서만 높고, masked HTN은 집에서만 높을 수 있다 🎭",
    "치료저항성 고혈압은 이뇨제 포함 3제 이상에도 안 잡히는 경우를 떠올린다 💪",
    "갈색세포종은 α차단제 먼저, β차단제는 그 다음! 줄 서기 엄수 🎢",
    "전자간증은 임신 20주 이후 고혈압 + 단백뇨/전신 증상. 심하면 MgSO4와 분만 판단까지 간다 ⚠️🤰",
]


def render_pdf_image() -> str:
    pdf_path = os.environ.get(PDF_ENV)
    if not pdf_path or not Path(pdf_path).exists():
        return ""
    with tempfile.TemporaryDirectory() as tmpdir:
        outbase = Path(tmpdir) / "page"
        subprocess.run(
            ["pdftoppm", "-jpeg", "-f", "1", "-singlefile", pdf_path, str(outbase)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        jpg_path = outbase.with_suffix(".jpg")
        return base64.b64encode(jpg_path.read_bytes()).decode()


def build_html(source_image: str) -> str:
    diseases_json = json.dumps(DISEASES, ensure_ascii=False)
    cases_json = json.dumps(CASES, ensure_ascii=False)
    questions_json = json.dumps(COMMON_QUESTIONS, ensure_ascii=False)
    keypoints_json = json.dumps(SOURCE_KEYPOINTS, ensure_ascii=False)
    img_url = f"data:image/jpeg;base64,{source_image}" if source_image else ""
    return f"""<!doctype html>
<html lang=\"ko\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>고혈압 CPX 공부 · 환자 역할 퀴즈</title>
<style>
:root{{--bg:#fffaf4;--paper:#fffefb;--ink:#2a2621;--muted:#6d655e;--line:#eadfce;--accent:#ff7a59;--accent2:#7c5cff;--green:#0f9d58;--yellow:#f59e0b;--blue:#2563eb;--pink:#ec4899;--danger:#dc2626;--shadow:0 18px 50px rgba(86,63,39,.12);}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(180deg,#fff8ee 0%,#fffdf8 100%);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
.app{{max-width:1280px;margin:0 auto;padding:18px}}
.hero{{background:linear-gradient(135deg,#fff0e0,#fff7f0 42%,#f7f3ff);border:1px solid #f3ddc9;border-radius:28px;padding:22px;box-shadow:var(--shadow);display:grid;grid-template-columns:1.15fr .85fr;gap:18px;align-items:center}}
.hero h1{{margin:0 0 10px;font-size:30px;line-height:1.2}} .hero p{{margin:0;color:var(--muted);line-height:1.7;font-size:15px}}
.badges{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}} .badge{{padding:6px 12px;border-radius:999px;font-size:12px;font-weight:800}}
.b1{{background:#ffe7e1;color:#c2410c}} .b2{{background:#efe8ff;color:#6d28d9}} .b3{{background:#e8f7ef;color:#0f9d58}} .b4{{background:#fff3d6;color:#b45309}}
.sourceBox{{background:rgba(255,255,255,.7);border:1px solid #efdfd4;border-radius:22px;padding:14px}}
.sourceBox img{{width:100%;border-radius:16px;display:block;background:#fff}} .sourceNote{{font-size:12px;color:var(--muted);margin-top:8px;line-height:1.5}}
.tabs{{display:flex;gap:10px;margin:16px 0 18px}} .tab{{border:0;padding:12px 18px;border-radius:16px;background:#f4ede5;color:#6b5f52;font-weight:900;cursor:pointer}} .tab.active{{background:var(--ink);color:white}}
.screen{{display:none}} .screen.active{{display:block}}
.studyLayout{{display:grid;grid-template-columns:280px 1fr;gap:18px}}
.sidebar{{background:var(--paper);border:1px solid var(--line);border-radius:24px;padding:14px;box-shadow:var(--shadow)}}
.sideTitle{{font-size:15px;font-weight:900;margin-bottom:10px}} .diseaseBtn{{width:100%;border:1px solid var(--line);background:#fff;padding:11px 12px;border-radius:14px;text-align:left;cursor:pointer;margin-bottom:8px;font-weight:800;color:#4b453f}}
.diseaseBtn.active{{border-color:#ffb499;background:#fff3ed;color:#b93815}}
.card{{background:var(--paper);border:1px solid var(--line);border-radius:26px;padding:20px;box-shadow:var(--shadow)}}
.card h2{{margin:0 0 8px;font-size:28px}} .sublead{{font-size:16px;line-height:1.7;color:#554d46}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:16px}} .box{{border:1px solid var(--line);background:#fff;border-radius:20px;padding:16px}}
.box h3{{margin:0 0 10px;font-size:15px}} .box ul{{margin:0;padding-left:18px;line-height:1.7}} .box li{{margin:4px 0}}
.metaphor{{background:linear-gradient(135deg,#fff3ec,#fff9f4);border:1px dashed #f6b48d;border-radius:18px;padding:14px;margin-top:12px;line-height:1.8}}
.joke{{background:linear-gradient(135deg,#fff0fb,#fff8ff);border:1px dashed #f0b6df;border-radius:18px;padding:14px;margin-top:12px;line-height:1.8}}
.quickList{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:16px}} .pill{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:10px 12px;font-weight:700;color:#5b5148}}
.quizLayout{{display:grid;grid-template-columns:320px 1fr;gap:18px}}
.panel{{background:var(--paper);border:1px solid var(--line);border-radius:24px;padding:16px;box-shadow:var(--shadow)}}
.panel h3{{margin:0 0 10px}} .mini{{font-size:13px;color:var(--muted);line-height:1.6}}
.caseMeta{{display:grid;gap:8px;margin-top:10px}} .metaChip{{padding:10px 12px;border-radius:14px;background:#fff;border:1px solid var(--line);font-size:13px;font-weight:800;color:#5a5148}}
.actions{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}} .btn{{border:0;border-radius:14px;padding:11px 14px;font-weight:900;cursor:pointer}} .primary{{background:var(--accent);color:#fff}} .secondary{{background:#f4ede5;color:#51473f}} .ghost{{background:#efe8ff;color:#5f3dc4}}
.chat{{height:520px;overflow:auto;background:#fff;border:1px solid var(--line);border-radius:20px;padding:14px;display:flex;flex-direction:column;gap:10px}}
.msg{{max-width:82%;padding:12px 14px;border-radius:18px;line-height:1.65;white-space:pre-wrap}} .doctor{{align-self:flex-end;background:#f3f0ff;color:#4c1d95}} .patient{{align-self:flex-start;background:#fff5e9;color:#7c2d12;border:1px solid #ffd8bd}} .system{{align-self:center;background:#f4f4f5;color:#52525b;font-size:12px}}
.inputRow{{display:flex;gap:8px;margin-top:10px}} .inputRow input{{flex:1;border:1px solid var(--line);border-radius:14px;padding:14px;font-size:15px}}
.questionGrid{{display:grid;grid-template-columns:1fr;gap:8px;margin-top:12px}} .qbtn{{border:1px solid var(--line);background:#fff;border-radius:14px;padding:10px 12px;text-align:left;cursor:pointer;font-weight:800;color:#5b5148}}
.reveal{{margin-top:14px;border:1px solid #ffd8bd;background:#fff8f2;border-radius:20px;padding:14px;display:none}} .reveal.show{{display:block}} .reveal ul{{margin:8px 0 0;padding-left:18px;line-height:1.7}}
.scoreNote{{margin-top:10px;font-size:12px;color:var(--muted)}}
@media (max-width:980px){{.hero,.studyLayout,.quizLayout{{grid-template-columns:1fr}} .chat{{height:420px}} .grid,.quickList{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class=\"app\">
  <section class=\"hero\">
    <div>
      <h1>🩺 고혈압 CPX 공부 · 환자 역할 퀴즈</h1>
      <p>이 앱은 <b>교수님이 질환명 4개 던져놓고 “알아서 연기해보세요”</b> 할 때 버티라고 만든 실전형 도구예요. 공부 모드에서는 질환별 핵심을 <b>고등학생도 이해될 말투</b>로 줄여주고, 퀴즈 모드에서는 랜덤 환자가 배정돼서 <b>강렬이 대본대로 질문하면 환자처럼 대답</b>합니다. 말하자면, <b>필기 + 과외 + 롤플레잉</b>을 한 판에 넣은 거예요 😎</p>
      <div class=\"badges\">
        <span class=\"badge b1\">📚 {len(DISEASES)}질환 공부 카드</span>
        <span class=\"badge b2\">🎭 랜덤 환자 역할 퀴즈</span>
        <span class=\"badge b3\">💊 치료/약물 포인트 포함</span>
        <span class=\"badge b4\">🧠 PDF 핵심 압축</span>
      </div>
      <div class=\"metaphor\"><b>오늘의 큰 그림</b> 👉 고혈압은 그냥 숫자 암기가 아니라, <b>“왜 올라가는지”를 캐릭터처럼 외우는 게임</b>이에요. 본태성은 생활습관 팀플형, 갈색세포종은 비상벨 난사형, 전자간증은 임신 중 비상등 켜진 형으로 잡으면 오래 갑니다.</div>
    </div>
    <div class=\"sourceBox\">{f'<img src="{img_url}" alt="고혈압 CPX 원문 PDF">' if img_url else '<div style="padding:34px 20px;border-radius:16px;background:#fff;font-weight:800;color:#6d655e;text-align:center">PDF 이미지가 있으면 여기에 원문이 같이 들어옵니다 📄</div>'}
      <div class=\"sourceNote\">원문 PDF의 포인트를 공부 카드와 환자 설정에 녹였습니다. 너무 길게 베끼지 않고, <b>실전에서 입으로 꺼내기 쉬운 정보</b> 위주로 압축했어요.</div>
    </div>
  </section>

  <div class=\"tabs\">
    <button class=\"tab active\" id=\"studyTab\" onclick=\"setScreen('study')\">📚 공부 모드</button>
    <button class=\"tab\" id=\"quizTab\" onclick=\"setScreen('quiz')\">🎭 환자 역할 퀴즈</button>
  </div>

  <section class=\"screen active\" id=\"studyScreen\">
    <div class=\"studyLayout\">
      <aside class=\"sidebar\">
        <div class=\"sideTitle\">질환별 강의록 카드</div>
        <div id=\"diseaseList\"></div>
        <div class=\"box\" style=\"margin-top:10px\">
          <h3>📌 PDF 전체 핵심 압축</h3>
          <div id=\"keypointList\"></div>
        </div>
      </aside>
      <main class=\"card\" id=\"studyCard\"></main>
    </div>
  </section>

  <section class=\"screen\" id=\"quizScreen\">
    <div class=\"quizLayout\">
      <aside class=\"panel\">
        <h3>🎲 랜덤 환자 배정</h3>
        <div class=\"mini\">버튼을 누르면 환자 하나가 랜덤으로 정해져요. <b>진단명은 숨겨둔 채</b> 강렬이 대본대로 질문하면, 환자가 그 질환답게 대답합니다.</div>
        <div class=\"actions\">
          <button class=\"btn primary\" onclick=\"newCase()\">새 환자 뽑기</button>
          <button class=\"btn secondary\" onclick=\"showHint()\">힌트 보기</button>
          <button class=\"btn ghost\" onclick=\"revealCase()\">정답 공개</button>
        </div>
        <div class=\"caseMeta\" id=\"caseMeta\"></div>
        <div class=\"scoreNote\">💡 팁: 모를 때는 환자가 의학 강의하듯 말하지 않아요. 애매하면 “잘 모르겠어요”, “병원에서 그렇게 들었어요”처럼 답하게 설계했어요.</div>
        <div class=\"questionGrid\" id=\"questionGrid\"></div>
      </aside>
      <main class=\"panel\">
        <h3>💬 문진 롤플레잉</h3>
        <div class=\"mini\">예: <b>“혈압이 높다는 건 언제부터 아셨어요?”</b>, <b>“집에서도 높았나요?”</b>, <b>“두통이나 시야장애는요?”</b></div>
        <div class=\"chat\" id=\"chat\"></div>
        <div class=\"inputRow\">
          <input id=\"questionInput\" placeholder=\"대본대로 질문해보세요. 예: 요즘 두통이나 두근거림은 있으세요?\" />
          <button class=\"btn primary\" onclick=\"sendQuestion()\">질문하기</button>
        </div>
        <div class=\"reveal\" id=\"revealBox\"></div>
      </main>
    </div>
  </section>
</div>

<script>
const DISEASES = {diseases_json};
const CASES = {cases_json};
const COMMON_QUESTIONS = {questions_json};
const SOURCE_KEYPOINTS = {keypoints_json};
let currentDisease = DISEASES[0].id;
let currentCase = null;

function esc(s){{return String(s ?? '').replace(/[&<>]/g, m => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[m]));}}
function setScreen(mode){{
  document.getElementById('studyScreen').classList.toggle('active', mode==='study');
  document.getElementById('quizScreen').classList.toggle('active', mode==='quiz');
  document.getElementById('studyTab').classList.toggle('active', mode==='study');
  document.getElementById('quizTab').classList.toggle('active', mode==='quiz');
}}
function renderDiseaseList(){{
  document.getElementById('diseaseList').innerHTML = DISEASES.map(d => `<button class="diseaseBtn ${{d.id===currentDisease?'active':''}}" onclick="pickDisease('${{d.id}}')">${{d.emoji}} ${{esc(d.title)}}</button>`).join('');
  document.getElementById('keypointList').innerHTML = SOURCE_KEYPOINTS.map(t => `<div class="pill" style="margin-bottom:8px">${{esc(t)}}</div>`).join('');
}}
function pickDisease(id){{ currentDisease = id; renderDiseaseList(); renderStudyCard(); }}
function renderStudyCard(){{
  const d = DISEASES.find(x => x.id === currentDisease);
  document.getElementById('studyCard').innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
      <div style="font-size:32px">${{d.emoji}}</div>
      <div>
        <h2>${{esc(d.title)}}</h2>
        <div class="sublead">${{esc(d.summary)}}</div>
      </div>
    </div>
    <div class="metaphor"><b>🧠 비유로 잡기</b><br>${{esc(d.metaphor)}}</div>
    <div class="grid">
      <div class="box"><h3>🔍 이 질환이 의심되는 이유</h3><ul>${{d.clues.map(x => `<li>${{esc(x)}}</li>`).join('')}}</ul></div>
      <div class="box"><h3>🗣️ 꼭 물어볼 질문</h3><ul>${{d.ask.map(x => `<li>${{esc(x)}}</li>`).join('')}}</ul></div>
      <div class="box"><h3>🧪 검사 포인트</h3><ul>${{d.tests.map(x => `<li>${{esc(x)}}</li>`).join('')}}</ul></div>
      <div class="box"><h3>💊 치료/약물 포인트</h3><ul>${{d.treatment.map(x => `<li>${{esc(x)}}</li>`).join('')}}</ul></div>
    </div>
    <div class="joke"><b>😏 과외쌤 한마디</b><br>${{esc(d.joke)}}</div>
    <div class="quickList">
      <div class="pill">핵심 한 줄: <b>${{esc(d.summary)}}</b></div>
      <div class="pill">시험에서의 역할: <b>증상 조합을 캐릭터처럼 구별하기</b></div>
    </div>`;
}}
function pushMessage(kind, text){{
  const el = document.createElement('div');
  el.className = `msg ${{kind}}`;
  el.textContent = text;
  const chat = document.getElementById('chat');
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
}}
function renderQuestions(){{
  document.getElementById('questionGrid').innerHTML = COMMON_QUESTIONS.map(q => `<button class="qbtn" onclick='askPreset(${{JSON.stringify(q)}})'>${{esc(q)}}</button>`).join('');
}}
function newCase(){{
  currentCase = CASES[Math.floor(Math.random()*CASES.length)];
  document.getElementById('chat').innerHTML = '';
  document.getElementById('revealBox').className = 'reveal';
  document.getElementById('revealBox').innerHTML = '';
  document.getElementById('caseMeta').innerHTML = `
    <div class="metaChip">🙋 환자 정보: ${{esc(currentCase.intro)}}</div>
    <div class="metaChip">🎚️ 난도: ${{esc(currentCase.difficulty)}}</div>
    <div class="metaChip">🤫 진단명: 아직 비밀</div>`;
  pushMessage('system', '랜덤 환자가 배정됐어요. 이제 대본대로 문진해보세요 🎭');
  pushMessage('patient', currentCase.answers.greeting + '\\n' + currentCase.answers.chief);
}}
function showHint(){{
  if(!currentCase) newCase();
  pushMessage('system', '힌트 👉 ' + currentCase.hint.join(' · '));
}}
function revealCase(){{
  if(!currentCase) newCase();
  const r = currentCase.reveal;
  const box = document.getElementById('revealBox');
  box.className = 'reveal show';
  box.innerHTML = `
    <div style="font-weight:900;font-size:18px;margin-bottom:8px">🧾 정답: ${{esc(r.diagnosis)}}</div>
    <div><b>왜 이 진단?</b></div>
    <ul>${{r.why.map(x=>`<li>${{esc(x)}}</li>`).join('')}}</ul>
    <div style="margin-top:8px"><b>검사</b></div>
    <ul>${{r.tests.map(x=>`<li>${{esc(x)}}</li>`).join('')}}</ul>
    <div style="margin-top:8px"><b>치료/약물</b></div>
    <ul>${{r.treatment.map(x=>`<li>${{esc(x)}}</li>`).join('')}}</ul>`;
}}
function detectCategory(q){{
  const s = q.toLowerCase();
  if(/안녕|성함|나이|연세|본인 확인/.test(q)) return 'greeting';
  if(/어디가 불편|왜 오셨|무엇 때문에|주호소|혈압이 높다고 해서/.test(q)) return 'chief';
  if(/언제부터|처음|고혈압.*언제/.test(q)) return 'onset';
  if(/어디에서|병원에서|집에서|몇.*나왔|얼마로/.test(q)) return 'where';
  if(/집에서도|가정혈압|반복해서|다른 곳에서도/.test(q)) return 'home';
  if(/커피|담배|운동|쉬고|안정|30분|10분/.test(q)) return 'measurement';
  if(/두통|시야|침침|가슴|흉통|두근|호흡곤란|부종|소변|거품뇨|어지러/.test(q)) return 'symptoms';
  if(/더위|땀|체중|자색선조|근력|털|여드름|안구돌출|칼륨/.test(q)) return 'endocrine';
  if(/코골|수면|낮졸림/.test(q)) return 'sleep';
  if(/약|복용|진통제|스테로이드|감기약|피임약|한약/.test(q)) return 'meds';
  if(/과거력|기저질환|당뇨|고지혈증|신부전|갑상선|sle/.test(q)) return 'past';
  if(/수술|다친 적|입원/.test(q)) return 'surgery';
  if(/가족|아버지|어머니|유전/.test(q)) return 'family';
  if(/술|담배|커피|운동|스트레스|식사|짜게|직업/.test(q)) return 'social';
  if(/임신|생리|폐경|출산/.test(q)) return 'female';
  return 'unknown';
}}
function answerFor(question){{
  if(!currentCase) newCase();
  const cat = detectCategory(question);
  return currentCase.answers[cat] || currentCase.answers.unknown;
}}
function askPreset(q){{ document.getElementById('questionInput').value = q; sendQuestion(); }}
function sendQuestion(){{
  if(!currentCase) newCase();
  const input = document.getElementById('questionInput');
  const q = input.value.trim();
  if(!q) return;
  pushMessage('doctor', q);
  pushMessage('patient', answerFor(q));
  input.value = '';
}}

document.getElementById('questionInput').addEventListener('keydown', e => {{ if(e.key === 'Enter') sendQuestion(); }});
renderDiseaseList(); renderStudyCard(); renderQuestions(); newCase();
</script>
</body>
</html>
"""


def main() -> None:
    OUT.write_text(build_html(render_pdf_image()), encoding="utf-8")
    print(f"✅ generated {{OUT}}")


if __name__ == "__main__":
    main()
