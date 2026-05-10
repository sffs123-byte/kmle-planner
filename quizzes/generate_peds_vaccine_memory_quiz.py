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
SOURCE_SCHEDULE_IN = Path("/Users/sffs123gmail.com/.openclaw/media/inbound/file_147---292231db-2c85-4287-a66f-27486b82853b.jpg")
SOURCE_SCHEDULE = ASSET_DIR / "source_vaccine_schedule_20260511.jpg"

if SOURCE_IMAGE_IN.exists():
    shutil.copyfile(SOURCE_IMAGE_IN, SOURCE_IMAGE)
if SOURCE_SCHEDULE_IN.exists():
    shutil.copyfile(SOURCE_SCHEDULE_IN, SOURCE_SCHEDULE)


def e(s: object) -> str:
    return html.escape(str(s), quote=False)


CARDS = [
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
    ("schedule_all_core", "이미지 표 기준 소아 예방접종 일정 핵심 10개를 순서대로 말하기", "BCG 1개월 / HAV 12·24개월 / HBV 0·1·6개월 / Rotavirus 2·4·6개월 / Hib·PCV 2·4·6·12개월 / Tdap 2·4·6·18개월·6세·12세 / IPV 2·4·6개월·6세 / VAR 12개월 / MMR 12개월·6세 / Influenza 6개월부터 매년", "표 전체를 한 번에 떠올리는 final boss 카드."),
    ("schedule_bcg", "BCG 접종 시기", "1개월", "BCG는 가장 앞쪽 단독 월령으로 기억."),
    ("schedule_hav", "A형간염 HAV 접종 시기", "12개월, 24개월", "HAV는 12와 24, 1년 간격 느낌."),
    ("schedule_hbv", "B형간염 HBV 접종 시기", "0개월, 1개월, 6개월", "출생 직후 0개월을 놓치면 안 된다."),
    ("schedule_rota", "Rotavirus 접종 시기", "2개월, 4개월, 6개월", "영아 초반 2-4-6 세트."),
    ("schedule_hib_pcv", "Hib와 PCV 접종 시기", "2개월, 4개월, 6개월, 12개월", "둘이 같은 리듬: 2-4-6 후 12개월 booster."),
    ("schedule_tdap", "Tdap/DTaP 계열 접종 시기", "2개월, 4개월, 6개월, 18개월, 6세, 12세", "2-4-6 기본접종 뒤 18개월, 6세, 12세로 이어진다."),
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
    ("year_12", "12세 접종으로 표에 있는 것은?", "Tdap/Tdap 계열", "이미지 요약표 기준 12세 booster."),
    ("schedule_246_set", "2·4·6개월 공통 리듬으로 외울 백신은?", "Rotavirus, Hib, PCV, Tdap/DTaP, IPV", "2-4-6 리듬을 먼저 묶으면 표가 단순해진다."),
    ("schedule_12_pair_live", "12개월 생백신으로 같이 떠올릴 것", "수두(VAR), MMR", "12개월에 생백신 VAR/MMR을 같이 잠근다."),
    ("schedule_12_boosters", "12개월 booster/추가 접종으로 같이 떠올릴 것", "HAV 시작, Hib·PCV booster, VAR, MMR", "12개월은 실제 문제에서 많이 물리는 갈림길."),
    ("schedule_hepatitis_compare", "A형간염과 B형간염 일정 비교", "HAV: 12·24개월 / HBV: 0·1·6개월", "간염끼리 헷갈릴 때 0개월이 있으면 B형간염."),
    ("schedule_live_12_6", "12개월과 6세에 반복되는 생백신은?", "MMR", "수두는 12개월, MMR은 12개월과 6세."),
    ("schedule_one_line", "소아 예방접종 일정 한 줄 lock line", "0-1-6 HBV, 1 BCG, 2-4-6 로타/Hib/PCV/DTaP/IPV, 12 HAV/Hib/PCV/VAR/MMR, 6세 DTaP/IPV/MMR, 독감 6개월부터 매년", "시험 직전 전체 표를 한 문장으로 압축."),
]


def card_html_q(q: str, tag: str) -> str:
    return f"""
<div style="display:flex;flex-direction:column;gap:8px;width:100%;">
  <div style="font-size:11px;font-weight:900;color:#93c5fd;letter-spacing:.06em;">예방접종 암기</div>
  <div style="font-size:17px;line-height:1.65;color:#e5e7eb;font-weight:800;">{e(q)}</div>
  <div><span style="background:#1e3a8a;color:#dbeafe;border:1px solid #60a5fa;border-radius:999px;padding:2px 8px;font-size:11px;font-weight:800;">#{e(tag)}</span></div>
</div>
""".strip()


def card_html_a(q: str, a: str, note: str, tag: str) -> str:
    src_img = "./assets/peds_vaccine_memory/source_vaccine_note_20260511.jpg"
    schedule_img = "./assets/peds_vaccine_memory/source_vaccine_schedule_20260511.jpg"
    return f"""
<section style="display:flex;flex-direction:column;gap:12px;line-height:1.7;">
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


def main() -> None:
    cards=build_cards()
    builder=QuizBuilder(cards=cards, title=TITLE, storage_prefix=STORAGE_PREFIX, enable_self_answer=False)
    builder.write(str(OUT))
    print(f"cards: {len(cards)}")
    print(f"data: {DATA_OUT}")
    print(f"out: {OUT}")
    print(f"source_image: {SOURCE_IMAGE} exists={SOURCE_IMAGE.exists()}")
    print(f"source_schedule: {SOURCE_SCHEDULE} exists={SOURCE_SCHEDULE.exists()}")
    print(f"storage_prefix: {STORAGE_PREFIX}_")


if __name__ == "__main__":
    main()
