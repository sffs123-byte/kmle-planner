#!/usr/bin/env python3
"""Generate 소아 예방접종 암기 SRS quiz from uploaded lecture note image."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from anki_quiz_builder import QuizBuilder

ROOT = Path(__file__).resolve().parent.parent
QUIZ_DIR = ROOT / "quizzes"
DATA_DIR = QUIZ_DIR / "data"
ASSET_DIR = QUIZ_DIR / "assets" / "peds_vaccine_memory"
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSET_DIR.mkdir(parents=True, exist_ok=True)

TITLE = "소아 예방접종 암기 SRS"
STORAGE_PREFIX = "peds_vaccine_memory_20260511"
OUT = QUIZ_DIR / "소아_예방접종_암기퀴즈.html"
DATA_OUT = DATA_DIR / "peds_vaccine_memory_cards.json"
SOURCE_IMAGE_IN = Path("/Users/sffs123gmail.com/.openclaw/media/inbound/file_146---2b868f2a-112a-4a1f-aae5-ffac82352f8b.jpg")
SOURCE_IMAGE = ASSET_DIR / "source_vaccine_note_20260511.jpg"
SOURCE_SCHEDULE_IN = Path("/Users/sffs123gmail.com/.openclaw/media/inbound/file_148---55496679-f7da-4af4-8f36-a728419ba4ee.jpg")
SOURCE_SCHEDULE = ASSET_DIR / "source_vaccine_schedule_20260511.jpg"
MANTRA = "홍수로비 디폴히피로히피디디폴 사맘, Tdap HPV"

if SOURCE_IMAGE_IN.exists():
    shutil.copyfile(SOURCE_IMAGE_IN, SOURCE_IMAGE)
if SOURCE_SCHEDULE_IN.exists():
    shutil.copyfile(SOURCE_SCHEDULE_IN, SOURCE_SCHEDULE)


def e(s: object) -> str:
    return html.escape(str(s), quote=False)


def mantra_strip() -> str:
    return f'<div class="vaccine-mantra-inline">{e(MANTRA)}</div>'


CARDS = [
    ("diphihiro_full", "12개월 전후 핵심 추가접종 구호 전체는?", "디폴히피로히피디디폴", "강렬 고정 암기문장. 디폴히피로 → 히피 → 디 → 디폴 순서로 밀고 간다."),
    ("diphihiro_parse", "디폴히피로히피디디폴을 4블록으로 끊으면?", "디폴히피로 / 히피 / 디 / 디폴", "붙여 외우되, 문제 풀 때는 월령별 4블록으로 자른다."),
    ("diphihiro_block1", "디폴히피로 = 어떤 백신들?", "DTaP, IPV, Hib, PCV, Rotavirus", "디=DTaP, 폴=폴리오 IPV, 히=Hib, 피=PCV, 로=Rotavirus."),
    ("diphihiro_block2", "히피 = 어떤 백신들?", "Hib, PCV", "돌 무렵 booster 핵심: Hib 4차, PCV 4차."),
    ("diphihiro_block3", "디 = 어떤 백신?", "DTaP", "15~18개월 DTaP 4차로 연결."),
    ("diphihiro_block4", "디폴 = 어떤 백신들?", "DTaP, IPV", "4~6세 booster: DTaP 5차, IPV 4차."),
    ("diphihiro_timeline", "디폴히피로 / 히피 / 디 / 디폴은 각각 언제?", "2·4·6개월 / 12개월 / 15~18개월 / 4~6세", "이 카드가 구호와 표를 연결하는 핵심."),
    ("diphihiro_246", "2·4·6개월 기본 세트를 구호로 말하면?", "디폴히피로", "12개월 전 핵심 반복 세트. Rota는 RV1이면 2·4개월, RV5면 2·4·6개월."),
    ("diphihiro_12m", "12개월 booster 핵심을 구호로 말하면?", "히피", "Hib 4차 + PCV 4차."),
    ("diphihiro_18m", "15~18개월 추가접종 핵심을 구호로 말하면?", "디", "DTaP 4차."),
    ("diphihiro_4y", "4~6세 추가접종 핵심을 구호로 말하면?", "디폴", "DTaP 5차 + IPV 4차."),
    ("diphihiro_reverse_d", "구호에서 ‘디’는 백신명과 주요 차수가 어떻게 이어지나?", "DTaP: 2·4·6개월 1~3차, 15~18개월 4차, 4~6세 5차", "디가 두 번 더 나오는 이유: 4차와 5차 booster."),
    ("diphihiro_reverse_pol", "구호에서 ‘폴’은 백신명과 주요 차수가 어떻게 이어지나?", "IPV: 2·4·6개월 1~3차, 4~6세 4차", "폴은 초반 디폴히피로에 들어가고, 4~6세 디폴에서 다시 나온다."),
    ("diphihiro_reverse_hipi", "구호에서 ‘히피’는 백신명과 차수가 어떻게 이어지나?", "Hib·PCV: 2·4·6개월 1~3차, 12개월 4차", "히피가 12개월에 따로 나오는 이유: 둘 다 4차 booster."),
    ("samam_full", "히피 제외, 12개월 시작/후속 구호는?", "SAMAM", "S-A-M-A-M으로 붙여 외운다. 수두 1차, A형간염 1차, MMR 1차, A형간염 2차, MMR 2차."),
    ("samam_parse", "SAMAM을 백신명과 차수로 풀면?", "수두 1차 / A형간염 1차 / MMR 1차 / A형간염 2차 / MMR 2차", "뒤 AM은 일본뇌염이 아니라 A형간염이 한 번 더, MMR이 4세 이후 한 번 더 맞는다는 뜻."),
    ("samam_12_start", "12개월에 새로 시작하는 SAMAM 앞 3개는?", "S 수두 1차, A A형간염 1차, M MMR 1차", "히피는 booster, SAM은 새로 시작하는 느낌."),
    ("samam_later_am", "SAMAM 뒤 AM은 왜 붙나?", "A형간염 2차, MMR 2차가 뒤에 남기 때문", "강렬 정정: 일본뇌염 사/생 구분이 아니라 A와 M의 후속 차수."),
    ("samam_s", "SAMAM의 S는?", "수두(VAR) 1차", "12개월에 시작."),
    ("samam_a", "SAMAM의 A는?", "A형간염: 12개월 1차, 이후 2차", "A가 두 번 나오는 이유."),
    ("samam_m", "SAMAM의 M은?", "MMR: 12개월 1차, 4~6세 2차", "M이 두 번 나오는 이유."),
    ("twelve_lock_hipi_samam", "12개월 핵심 구호 전체는?", "히피 + SAM", "히피는 Hib/PCV 4차, SAM은 수두 1차·A형간염 1차·MMR 1차. 뒤 AM은 후속 차수로 기억."),
    ("eleven_tdap_hpv", "11세 추가접종 핵심은?", "Tdap + HPV", "11세 축은 Tdap과 HPV를 같이 잠근다."),
    ("eleven_tdap_hpv_detail", "11세 Tdap+HPV를 차수로 말하면?", "Tdap 1회, HPV 1차 시작 후 일정에 따라 추가 접종", "문제에서 11세를 주면 Tdap과 HPV를 먼저 떠올린다."),
    ("live_mnemonic", "생백신 암기 구호는?", "사일 홍수 로비", "생백신 리스트를 여는 암기문장. 사일=Sabin·일본뇌염, 홍수=홍역-볼거리-풍진(MMR)·수두, 로비=로타바이러스·BCG."),
    ("live_list", "이미지 기준 생백신 6가지를 모두 쓰기", "Sabin, 일본뇌염, MMR, 수두, 로타바이러스, BCG", "구호 ‘사일 홍수 로비’를 실제 백신명으로 풀어쓴다."),
    ("live_sail", "‘사일’이 뜻하는 생백신은?", "Sabin, 일본뇌염", "Sabin은 경구 폴리오 생백신을 가리키는 암기 포인트."),
    ("live_hongsu", "‘홍수’가 뜻하는 생백신은?", "홍역-볼거리-풍진(MMR), 수두", "홍역·볼거리·풍진은 MMR 한 묶음으로 기억."),
    ("live_robi", "‘로비’가 뜻하는 생백신은?", "로타바이러스, BCG", "로타 + 비씨지."),
    ("same_day_principle", "2가지 백신을 동시에 투여할 때 원칙은?", "다른 주사기로 다른 부위에 투여", "같은 날 맞출 수 있어도 한 주사기에 섞는 게 아니다."),
    ("live_live_interval", "생백신끼리 따로 맞을 때 필요한 간격은?", "4주 이상", "같은 날이 아니면 4주 이상 간격이 필요하다."),
    ("live_live_same_day", "생백신-생백신은 같은 날 접종 가능한가?", "가능. 단 같은 날이 아니면 4주 이상 간격", "동시접종은 가능하고, 따로 맞으면 4주 rule."),
    ("live_inactivated_interval", "생백신-사백신 사이 간격 제한은?", "상관없음. 동시접종 가능", "4주 rule은 생백신끼리 따로 맞을 때가 핵심."),
    ("inactivated_inactivated_interval", "사백신-사백신 사이 간격 제한은?", "상관없음. 동시접종 가능", "사백신끼리는 간격에 크게 묶이지 않는다."),
    ("minimum_interval", "예방접종 간격의 최소기준은 어떻게 해야 하나?", "최소기준은 지켜야 함", "너무 짧으면 면역 형성이 부족할 수 있다."),
    ("longer_interval", "접종 간격이 권장보다 길어지면 어떻게 되나?", "백신 효과에 지장 없음. 횟수도 동일", "밀렸다고 처음부터 다시 시작하지 않는다는 감각."),
    ("permanent_contra_anaphylaxis", "예방접종 영구 금기 1: 이전 접종 후 무엇?", "아나필락시스 과거력", "같은 백신/성분에 대한 중증 알레르기 반응은 영구 금기."),
    ("permanent_contra_pertussis", "예방접종 영구 금기 2: 백일해 접종 후 언제 뇌증?", "백일해 접종 7일 이내 뇌증 발생", "pertussis-containing vaccine의 핵심 금기."),
    ("temporary_contra_pregnancy", "일시적 금기: 임신에서 특히 피해야 하는 백신군은?", "생백신", "MMR·수두 같은 생백신은 임신 중 금기."),
    ("temporary_contra_immuno", "일시적 금기: 면역저하에는 무엇이 포함될 수 있나?", "면역저하, 스테로이드 치료 등", "생백신은 면역저하에서 안전성과 효과가 문제된다."),
    ("steroid_live", "고용량 전신 스테로이드 사용 중 생백신 판단은?", "생백신 연기/금기", "Pretest lock: 면역저하 단서가 있으면 생백신을 바로 맞히지 않는다."),
    ("recent_ig_blood", "최근 감마글로불린/혈청 주사/수혈은 어떤 접종에서 주의?", "생백신 접종 연기 고려", "이미지 기준 ‘최근 11개월 이내’가 주의사항. 실제 간격은 제제/용량별로 달라질 수 있다."),
    ("caution_acute_fever", "접종 주의사항 예시: 급성 열성 질환이면?", "상태 평가 후 접종 연기 가능", "가벼운 증상인지, 전신상태가 나쁜지 구분."),
    ("caution_chronic_disease", "접종 주의사항 예시로 나온 장기 질환은?", "심혈관·신장·간 질환", "생명 위험 가능성이나 면역 형성 저하 가능성을 평가한다."),
    ("risk_benefit", "주의사항에서 최종 판단 원칙은?", "예방효과와 이상반응 위험성 평가", "접종 이득과 위험을 비교한다."),
    ("case_mmr_varicella", "Case: MMR을 오늘 맞고 수두를 다른 날 맞으려면 최소 간격은?", "4주 이상", "MMR과 수두는 둘 다 생백신."),
    ("case_mmr_dtap", "Case: MMR과 DTaP를 같은 날 맞을 수 있나?", "가능", "생백신-사백신 간격은 상관없고 동시접종 가능."),
    ("case_dtap_ipv", "Case: DTaP와 IPV 사이 간격 제한은?", "상관없음", "사백신-사백신 조합."),
    ("case_anaphylaxis", "Case: 이전 백신 접종 후 아나필락시스가 있었다. 다음 같은 백신은?", "금기", "영구 금기 카드."),
    ("case_encephalopathy", "Case: 백일해 포함 백신 7일 이내 뇌증 발생. 이후 pertussis 백신은?", "금기", "DTaP/Tdap 판단에서 중요한 문구."),
    ("case_pregnant_mmr", "Case: 임신 중 MMR 접종 가능한가?", "불가. 생백신 금기", "임신은 생백신 일시적 금기."),
    ("case_ivig_mmr", "Case: 최근 IVIG/수혈 후 MMR·수두 접종은?", "연기 고려", "외부 항체가 생백신 효과를 떨어뜨릴 수 있다."),
    ("case_delayed_schedule", "Case: 접종 간격이 너무 길어졌다. 처음부터 다시 시작?", "아니오. 이어서 접종", "간격이 길어진 것은 효과에 지장 없고 횟수 동일."),
    ("one_line_lock", "예방접종 간격 한 줄 lock line", "생백신끼리 따로면 4주, 나머지는 대체로 상관없음", "시험장에서 가장 빨리 쓰는 문장."),
    ("schedule_all_core", "이미지 표 기준 소아 예방접종 일정 핵심을 순서대로 말하기", "BCG 1개월 / HAV 12개월 1차·이후 2차 / HBV 0·1·6개월 / Rotavirus 2·4·6개월 / Hib·PCV 2·4·6·12개월 / DTaP 2·4·6·18개월·4~6세 / IPV 2·4·6개월·4~6세 / VAR 12개월 / MMR 12개월·4~6세 / Influenza 6개월부터 매년 / 11세 Tdap+HPV", "표 전체를 한 번에 떠올리는 final boss 카드."),
    ("schedule_bcg", "BCG 접종 시기", "1개월", "BCG는 가장 앞쪽 단독 월령으로 기억."),
    ("schedule_hav", "A형간염 HAV 접종 시기", "12개월, 24개월", "HAV는 12와 24, 1년 간격 느낌."),
    ("schedule_hbv", "B형간염 HBV 접종 시기", "0개월, 1개월, 6개월", "출생 직후 0개월을 놓치면 안 된다."),
    ("schedule_rota", "Rotavirus 접종 시기", "2개월, 4개월, 6개월", "영아 초반 2-4-6 세트."),
    ("schedule_hib_pcv", "Hib와 PCV 접종 시기", "2개월, 4개월, 6개월, 12개월", "둘이 같은 리듬: 2-4-6 후 12개월 booster."),
    ("schedule_tdap", "DTaP/Tdap 계열 접종 시기", "DTaP: 2·4·6개월, 15~18개월, 4~6세 / Tdap: 11세", "영아·유아기는 DTaP, 11세 추가는 Tdap."),
    ("schedule_ipv", "폴리오 IPV 접종 시기", "2개월, 4개월, 6개월, 6세", "2-4-6 후 6세 booster."),
    ("schedule_var", "수두 VAR 접종 시기", "12개월", "수두는 12개월 단독으로 먼저 잠근다."),
    ("schedule_mmr", "MMR 접종 시기", "12개월, 6세", "MMR은 12개월과 6세."),
    ("schedule_influenza", "Influenza 접종 시기", "6개월부터 매년", "매년접종이라는 단어가 핵심."),
    ("month_0", "0개월 접종으로 표에 있는 것은?", "HBV", "출생 직후 B형간염."),
    ("month_1", "1개월 접종으로 표에 있는 것은?", "BCG, HBV", "BCG 1개월, HBV 1개월."),
    ("month_2", "2개월에 시작/접종되는 백신 묶음", "Rotavirus, Hib, PCV, Tdap/DTaP, IPV", "2개월은 2-4-6 세트가 한꺼번에 시작되는 달."),
    ("month_4", "4개월 접종 백신 묶음", "Rotavirus, Hib, PCV, Tdap/DTaP, IPV", "2개월 묶음과 같은 2-4-6 리듬."),
    ("month_6", "6개월 접종 백신 묶음", "HBV, Rotavirus, Hib, PCV, Tdap/DTaP, IPV, Influenza 시작", "6개월은 HBV 마무리 + 2-4-6 세트 + 독감 시작."),
    ("month_12", "12개월 접종 백신 묶음", "HAV, Hib, PCV, 수두(VAR), MMR", "12개월은 HAV 시작, Hib/PCV booster, 생백신 VAR/MMR."),
    ("month_18", "18개월 접종으로 표에 있는 것은?", "Tdap/DTaP", "18개월 booster."),
    ("month_24", "24개월 접종으로 표에 있는 것은?", "HAV", "A형간염 두 번째."),
    ("year_6", "6세 접종 백신 묶음", "Tdap/DTaP, IPV, MMR", "6세는 DTaP/IPV/MMR booster."),
    ("year_11", "11세 추가접종으로 표에 있는 것은?", "Tdap, HPV", "강렬 암기축: 11세는 Tdap + HPV."),
    ("schedule_246_set", "2·4·6개월 공통 리듬으로 외울 백신은?", "Rotavirus, Hib, PCV, Tdap/DTaP, IPV", "2-4-6 리듬을 먼저 묶으면 표가 단순해진다."),
    ("schedule_12_pair_live", "12개월 생백신으로 같이 떠올릴 것", "수두(VAR), MMR", "12개월에 생백신 VAR/MMR을 같이 잠근다."),
    ("schedule_12_boosters", "12개월 booster/추가 접종으로 같이 떠올릴 것", "HAV 시작, Hib·PCV booster, VAR, MMR", "12개월은 실제 문제에서 많이 물리는 갈림길."),
    ("schedule_hepatitis_compare", "A형간염과 B형간염 일정 비교", "HAV: 12·24개월 / HBV: 0·1·6개월", "간염끼리 헷갈릴 때 0개월이 있으면 B형간염."),
    ("schedule_live_12_6", "12개월과 6세에 반복되는 생백신은?", "MMR", "수두는 12개월, MMR은 12개월과 6세."),
    ("schedule_one_line", "소아 예방접종 일정 한 줄 lock line", "0-1-6 HBV, 1 BCG, 2-4-6 디폴히피로, 12 히피+SAM, 뒤 AM, 4~6세 디폴+MMR, 11세 Tdap+HPV, 독감 6개월부터 매년", "시험 직전 전체 표를 한 문장으로 압축."),
]


def card_html_q(q: str, tag: str) -> str:
    return f"""
<div style="display:flex;flex-direction:column;gap:8px;width:100%;">
  <div style="font-size:11px;font-weight:900;color:#93c5fd;letter-spacing:.06em;">예방접종 암기</div>
  <div style="font-size:17px;line-height:1.65;color:#e5e7eb;font-weight:800;">{e(q)}</div>
  <div><span style="background:#1e3a8a;color:#dbeafe;border:1px solid #60a5fa;border-radius:999px;padding:2px 8px;font-size:11px;font-weight:800;">#{e(tag)}</span></div>
  {mantra_strip()}
</div>
""".strip()


def card_html_a(q: str, a: str, note: str, tag: str) -> str:
    src_img = "./assets/peds_vaccine_memory/source_vaccine_note_20260511.jpg"
    schedule_img = "./assets/peds_vaccine_memory/source_vaccine_schedule_20260511.jpg"
    return f"""
<section style="display:flex;flex-direction:column;gap:12px;line-height:1.7;">
  {mantra_strip()}
  <div style="border-left:4px solid #2563eb;background:#eff6ff;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#1d4ed8;margin-bottom:6px;">문제</div>
    <div>{e(q)}</div>
  </div>
  <div style="border-left:4px solid #16a34a;background:#f0fdf4;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#15803d;margin-bottom:6px;">답</div>
    <div style="font-size:20px;color:#052e16;"><strong>{e(a)}</strong></div>
  </div>
  <div style="border-left:4px solid #f59e0b;background:#fffbeb;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#b45309;margin-bottom:6px;">암기 포인트</div>
    <div>{e(note)}</div>
  </div>
  <details style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px 12px;color:#334155;">
    <summary style="cursor:pointer;font-weight:800;">원본 이미지 보기</summary>
    <img src="{src_img}" alt="예방접종 원본 필기" style="max-width:100%;border-radius:12px;margin-top:10px;border:1px solid #e5e7eb;" />
    <img src="{schedule_img}" alt="소아 예방접종 일정 원본" style="max-width:100%;border-radius:12px;margin-top:10px;border:1px solid #e5e7eb;" />
    <div style="margin-top:8px;font-size:12px;color:#64748b;">#{e(tag)} · 업로드 이미지 기반</div>
  </details>
  {mantra_strip()}
</section>
""".strip()


def guide_html(q: str, a: str, note: str, tag: str) -> str:
    return f"""
<section style="line-height:1.7;">
  <h4>문제</h4>
  <p>{e(q)}</p>
  <h4>답</h4>
  <p><strong>{e(a)}</strong></p>
  <h4>암기 포인트</h4>
  <p>{e(note)}</p>
  <h4>출처</h4>
  <p>업로드 이미지: 생백신/동시접종/금기 메모 + 소아 예방접종 일정표</p>
  <p><strong>{e(MANTRA)}</strong></p>
  <p><code>{e(tag)}</code></p>
</section>
""".strip()


def build_cards() -> list[dict]:
    built=[]
    data=[]
    for i,(cid,q,a,note) in enumerate(CARDS,1):
        tag=cid.replace('_','-')
        built.append({
            "id": f"vaccine_{i:03d}_{cid}",
            "num": i,
            "q": card_html_q(q, tag),
            "a": card_html_a(q, a, note, tag),
            "g": guide_html(q, a, note, tag),
        })
        data.append({"id": f"vaccine_{i:03d}_{cid}", "num": i, "question": q, "answer": a, "note": note, "source": "uploaded vaccine note/schedule images 2026-05-11"})
    DATA_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return built



def mantra_wall_html(class_name: str) -> str:
    pieces = [
        "홍수로비 디폴히피로히피디디폴 사맘, Tdap HPV",
        "홍수로비", "디폴히피로히피디디폴", "사맘", "Tdap HPV",
        "디폴히피로", "히피디디폴", "SAMAM", "12개월 히피+SAM", "4~6세 디폴+MMR", "11세 Tdap HPV",
    ]
    layouts = [
        (8,10,-14,1.05,.42,28),(30,8,7,.86,.32,18),(62,9,-5,.90,.30,22),(86,8,13,.86,.34,20),
        (12,24,8,.82,.30,18),(44,23,-11,1.08,.42,26),(75,24,16,.84,.34,18),(93,24,-20,.78,.28,16),
        (18,40,-25,.88,.30,19),(38,39,11,.82,.30,17),(64,42,-8,1.12,.42,25),(88,40,22,.86,.32,18),
        (7,58,18,.74,.26,16),(28,60,-9,1.04,.36,23),(52,58,5,.78,.26,17),(77,61,-18,1.10,.42,24),
        (14,76,-6,1.18,.44,25),(43,78,17,.84,.32,18),(67,76,-13,.90,.34,19),(91,80,9,.80,.30,17),
        (24,92,12,.82,.28,17),(54,91,-4,1.08,.40,24),(82,93,-16,.86,.32,18),
    ]
    spans = []
    for i, (x, y, r, sc, op, fs) in enumerate(layouts):
        label = pieces[i % len(pieces)]
        spans.append(f'<span style="--x:{x}%;--y:{y}%;--r:{r}deg;--s:{sc};--o:{op};--fs:{fs}px">{e(label)}</span>')
    strings = []
    for x, y, r, w in [(18,31,-18,42),(55,33,11,35),(35,67,19,48),(72,69,-14,38),(50,50,-35,70)]:
        strings.append(f'<i style="--x:{x}%;--y:{y}%;--r:{r}deg;--w:{w}vw"></i>')
    return f'<div class="{class_name}" aria-hidden="true">' + ''.join(spans + strings) + '</div>'


def apply_spell_background() -> None:
    """Make the vaccine mantra unavoidable without using image wallpaper."""
    text = OUT.read_text(encoding="utf-8")
    css = f"""

/* Vaccine spell layer: text-only evidence-board / ransom-note wall */
body.vaccine-spell-body {{
    background:
        radial-gradient(circle at 12% 8%, rgba(37, 99, 235, .22), transparent 32%),
        radial-gradient(circle at 86% 14%, rgba(220, 38, 38, .20), transparent 30%),
        linear-gradient(135deg, #111827 0%, #1f2937 48%, #0f172a 100%) !important;
}}
body.vaccine-spell-body::before {{
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image:
        linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.028) 1px, transparent 1px);
    background-size: 44px 44px, 44px 44px;
    opacity: .55;
}}
.vaccine-mantra-wall {{ position: fixed; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }}
.vaccine-mantra-wall span {{
    position: absolute; left: var(--x); top: var(--y);
    transform: translate(-50%, -50%) rotate(var(--r)) scale(var(--s));
    opacity: var(--o); color: #dbeafe; background: rgba(15, 23, 42, .56);
    border: 1px solid rgba(191, 219, 254, .30); border-radius: 6px; padding: 4px 10px;
    font-size: var(--fs); font-weight: 1000; letter-spacing: .06em; white-space: nowrap;
    text-transform: uppercase; font-family: Impact, Haettenschweiler, 'Arial Black', system-ui, sans-serif;
    text-shadow: 0 2px 10px rgba(0,0,0,.58); box-shadow: 0 8px 22px rgba(0,0,0,.20);
}}
.vaccine-mantra-wall span:nth-child(3n) {{ color: #fecaca; border-color: rgba(248, 113, 113, .34); background: rgba(127, 29, 29, .20); }}
.vaccine-mantra-wall span:nth-child(4n) {{ color: #bbf7d0; border-color: rgba(74, 222, 128, .32); background: rgba(20, 83, 45, .20); }}
.vaccine-mantra-wall i {{
    position: absolute; left: var(--x); top: var(--y); width: var(--w); height: 2px;
    transform: translate(-50%, -50%) rotate(var(--r)); background: rgba(239, 68, 68, .42);
    box-shadow: 0 0 8px rgba(248, 113, 113, .34);
}}
body.vaccine-spell-body .sidebar {{ position: fixed; }}
body.vaccine-spell-body .main, body.vaccine-spell-body .quiz-overlay, body.vaccine-spell-body .quiz-header {{ position: relative; z-index: 1; }}
body.vaccine-spell-body .card, body.vaccine-spell-body .quiz-card {{ position: relative; overflow: hidden; box-shadow: 0 18px 44px rgba(2, 6, 23, .24); }}
body.vaccine-spell-body .card::before, body.vaccine-spell-body .quiz-card::before {{
    content: '{e(MANTRA)}'; position: absolute; left: 0; right: 0; top: 0; padding: 5px 12px;
    background: linear-gradient(90deg, rgba(30, 64, 175, .92), rgba(16, 185, 129, .82));
    color: #eff6ff; font-size: 11px; font-weight: 900; letter-spacing: .04em; text-align: center; z-index: 2;
}}
body.vaccine-spell-body .card .card-header, body.vaccine-spell-body .quiz-card {{ padding-top: 34px !important; }}
.vaccine-mantra-inline {{
    display: inline-flex; align-items: center; justify-content: center; width: fit-content; max-width: 100%;
    padding: 6px 10px; border-radius: 999px; background: linear-gradient(90deg, #eff6ff, #ecfdf5);
    color: #1e3a8a; border: 1px solid rgba(37, 99, 235, .24); font-size: 12px; font-weight: 950; letter-spacing: .03em;
}}
.vaccine-mantra-ribbon {{
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 9999; padding: 7px 10px;
    background: rgba(15, 23, 42, .86); color: #bfdbfe; border-top: 1px solid rgba(147, 197, 253, .35);
    font-size: 12px; font-weight: 950; letter-spacing: .08em; white-space: nowrap; overflow: hidden; text-align: center;
}}
body.vaccine-spell-body .quiz-answer::after {{
    content: '{e(MANTRA)}'; display: block; margin-top: 14px; padding: 8px 10px; border-radius: 10px;
    background: #dbeafe; color: #1e3a8a; font-weight: 950; text-align: center;
}}
"""
    ribbon = f'<div class="vaccine-mantra-ribbon">{e(MANTRA)} · {e(MANTRA)} · {e(MANTRA)} · {e(MANTRA)}</div>'
    wall = mantra_wall_html("vaccine-mantra-wall")
    text = text.replace("</style>", css + "\n</style>", 1)
    text = text.replace("<body>", '<body class="vaccine-spell-body">\n' + wall + "\n" + ribbon, 1)
    OUT.write_text(text, encoding="utf-8")


def main() -> None:
    cards=build_cards()
    builder=QuizBuilder(
        cards=cards,
        title=TITLE,
        storage_prefix=STORAGE_PREFIX,
        enable_self_answer=False,
        randomize_review=True,
    )
    builder.write(str(OUT))
    apply_spell_background()
    print(f"cards: {len(cards)}")
    print(f"data: {DATA_OUT}")
    print(f"out: {OUT}")
    print(f"source_image: {SOURCE_IMAGE} exists={SOURCE_IMAGE.exists()}")
    print(f"source_schedule: {SOURCE_SCHEDULE} exists={SOURCE_SCHEDULE.exists()}")
    print(f"storage_prefix: {STORAGE_PREFIX}_")


if __name__ == "__main__":
    main()
