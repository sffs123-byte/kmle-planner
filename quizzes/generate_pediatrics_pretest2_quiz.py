#!/usr/bin/env python3
"""Generate 소아청소년과 2주차 Pretest Anki-style SRS quiz.

Source of truth:
- .tmp/peds_pretest2_review_20260517/소아청소년과_2주차_pretest_전체검색_핵심정리_2026-05-17.md
- Extracted recall texts under .tmp/peds_pretest2_review_20260517/text/

Policy:
- Preserve 2026 latest recall questions as highest priority cards.
- Keep repeated 2025/2023 themes as lower-tier drill cards.
- Disable self-answer box, matching the 1주차 pretest UX.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from anki_quiz_builder import QuizBuilder

ROOT = Path(__file__).resolve().parent.parent
QUIZ_DIR = ROOT / "quizzes"
DATA_DIR = QUIZ_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUT = QUIZ_DIR / "소아청소년과_2주차_pretest_quiz.html"
DATA = DATA_DIR / "pediatrics_pretest2_cards.json"
TITLE = "소아청소년과 2주차 Pretest SRS"
STORAGE_PREFIX = "peds_pretest2_20260517"

ORIGIN_LABELS = {
    "latest_2026": "✅ 2026 최신 복기",
    "recent_2026": "🟦 2026 직전 조 복기",
    "past_recall": "📚 과거 반복 복기",
    "conference": "🏥 의국회의 후보",
}

TIER_LABELS = {
    "P4": "P4 · 최신 exact 우선",
    "P3": "P3 · 직전/반복 actual",
    "P2": "P2 · 반복 야마 drill",
    "P1": "P1 · 의국회의 대비",
}

CARDS = [
    # 2026 9~12조 latest exact 10Q
    {"id":"peds2_2026_001","origin":"latest_2026","tier":"P4","mode":"객관식","source":"2026 9·10·11·12조 2차 pretest Q1","axis":"식중독-섭취 후 1-6시간 구토","q":"6세 남아. 유치원 급식으로 김밥을 먹은 뒤 약 3시간 후 구토와 설사를 시작했고, 같은 유치원 아이들도 비슷한 증상을 보였다. 가장 가능성 높은 원인균은?","a":"포도알균 식중독, Staphylococcus aureus toxin","lock":"김밥·급식 후 1-6시간, 구토 우세 집단발생이면 S. aureus toxin."},
    {"id":"peds2_2026_002","origin":"latest_2026","tier":"P4","mode":"객관식","source":"2026 9·10·11·12조 2차 pretest Q2","axis":"장중첩증-재발-target sign","q":"3세 남아. 8시간 전부터 보채고 토하며, 보챔과 안정이 반복된다. 1주 전 장중첩증으로 공기정복을 받은 병력이 있고 복부초음파에서 target sign이 보인다. 적절한 처치는?","a":"공기정복, air reduction","lock":"장중첩증 + target sign + 복막염/천공 단서 없음 → 공기정복."},
    {"id":"peds2_2026_003","origin":"latest_2026","tier":"P4","mode":"객관식","source":"2026 9·10·11·12조 2차 pretest Q3","axis":"만성기침-부비동염/상기도 원인","q":"11세 여아. 5주 전부터 밤낮으로 기침. 청진은 정상, FeNO는 낮고, CXR와 Caldwell-Water view가 제시되었다. 알맞은 치료는?","a":"항생제 쪽으로 정리. 부비동염/상기도 원인 만성기침 축","lock":"낮은 FeNO·정상 청진이면 천식 흡입치료보다 부비동염/상기도 원인을 먼저 생각한다.","note":"원본 이미지/선지 의존성이 있는 문항이라 최종 직전에는 사진과 선지를 한 번 더 확인."},
    {"id":"peds2_2026_004","origin":"latest_2026","tier":"P4","mode":"객관식","source":"2026 9·10·11·12조 2차 pretest Q4","axis":"세기관지염-supportive care","q":"8개월 남아. 2일째 기침, 잘 먹지 않음, nasal flaring, retraction, 양측 wheezing. 림프구 우세, CRP 정상. 치료는?","a":"수액 및 산소공급","lock":"bronchiolitis는 대부분 바이러스성. 치료는 산소·수액 등 supportive care."},
    {"id":"peds2_2026_005","origin":"latest_2026","tier":"P4","mode":"객관식","source":"2026 9·10·11·12조 2차 pretest Q5","axis":"TOF-hypercyanotic spell","q":"5개월 영아. 출생 직후 청색증형 심장병 진단. 울다가 청색증이 심해졌고, 비슷한 증상이 반복되며 심잡음은 잘 들리지 않는다. 부츠모양 CXR가 제시되었다. 즉시 처치는?","a":"Knee-chest position, 무릎-가슴 자세","lock":"TOF hypercyanotic spell 첫 처치는 knee-chest position."},
    {"id":"peds2_2026_006","origin":"latest_2026","tier":"P4","mode":"주관식","source":"2026 9·10·11·12조 2차 pretest 주1","axis":"항생제 stewardship","q":"불필요하거나 부적합한 항생제를 사용했을 때 발생할 수 있는 문제를 2가지 이상 쓰시오.","a":"항생제 내성 증가, 약물 이상반응, 정상균총 파괴와 C. difficile 감염, 의료비 증가 등","lock":"내성·부작용·정상균총 파괴를 기본 3축으로 외우면 안전."},
    {"id":"peds2_2026_007","origin":"latest_2026","tier":"P4","mode":"주관식","source":"2026 9·10·11·12조 2차 pretest 주2","axis":"double bubble-십이지장폐쇄","q":"신생아가 수유 후 구토를 보이고 X-ray에서 double bubble sign이 제시되었다. 진단은?","a":"선천 십이지장 폐쇄","lock":"신생아 구토 + double bubble = congenital duodenal atresia."},
    {"id":"peds2_2026_008","origin":"latest_2026","tier":"P4","mode":"주관식","source":"2026 9·10·11·12조 2차 pretest 주3","axis":"인두후부농양-검사","q":"4세 남아. 먹지 못하고 침을 흘리며 보채고, 목을 뒤로 젖힌 채 목을 잘 움직이지 못한다. 가장 의심되는 진단명과 시행할 검사는?","a":"인두후부농양, retropharyngeal abscess / lateral neck X-ray","lock":"침흘림 + 목 신전 + 목 운동 제한 = retropharyngeal abscess, lateral neck view."},
    {"id":"peds2_2026_009","origin":"latest_2026","tier":"P4","mode":"주관식","source":"2026 9·10·11·12조 2차 pretest 주4","axis":"Kawasaki-echo","q":"8개월 남아. 6일 고열, 결막충혈, 딸기혀, 손 홍조, 발진이 있고 proBNP가 상승했다. 진단 평가에 필요한 추가검사는?","a":"심초음파","lock":"Kawasaki 의심이면 coronary artery 평가를 위해 echo."},
    {"id":"peds2_2026_010","origin":"latest_2026","tier":"P4","mode":"주관식","source":"2026 9·10·11·12조 2차 pretest 주5 의국회의","axis":"감염관리-손위생","q":"감염전파를 차단하기 위한 가장 중요한 방법 1가지는?","a":"손위생","lock":"감염관리 1번 답은 손위생."},

    # 2026 5~8조 recent 10Q
    {"id":"peds2_2026_011","origin":"recent_2026","tier":"P3","mode":"객관식","source":"2026 5·6·7·8조 2주차 프테 객1","axis":"수족구병","q":"4세 남아. 미열 뒤 잘 먹지 못하고 침을 흘리며, 손·발·사타구니 발진과 구강 궤양이 보인다. 진단은?","a":"수족구병","lock":"구강 궤양 + 손·발 발진이면 HFMD."},
    {"id":"peds2_2026_012","origin":"recent_2026","tier":"P3","mode":"객관식","source":"2026 5·6·7·8조 2주차 프테 객2","axis":"선천거대결장-확진검사","q":"선천거대결장을 확진하기 위한 검사는?","a":"직장 흡인생검 또는 생검","lock":"Hirschsprung 확진은 ganglion cell 부재 확인, 즉 생검."},
    {"id":"peds2_2026_013","origin":"recent_2026","tier":"P3","mode":"객관식","source":"2026 5·6·7·8조 2주차 프테 객3","axis":"후두연화증","q":"2개월 남아. 생후 2주부터 그르렁거림이 있고, 울거나 수유할 때 심해지며 엎드리면 완화된다. 치료는?","a":"경과관찰","lock":"후두연화증은 대개 성장하며 호전되어 경과관찰."},
    {"id":"peds2_2026_014","origin":"recent_2026","tier":"P3","mode":"객관식","source":"2026 5·6·7·8조 2주차 프테 객4","axis":"이물흡인-Heimlich","q":"8세 남아가 호두를 먹다가 청색증과 호흡곤란을 보인다. 다음 처치는?","a":"하임리히법","lock":"소아/성인 이물질 기도폐쇄 + 의식 있음 → Heimlich."},
    {"id":"peds2_2026_015","origin":"recent_2026","tier":"P3","mode":"객관식","source":"2026 5·6·7·8조 2주차 프테 객5","axis":"Kawasaki-치료","q":"7개월 남아. 6일 고열, 결막충혈, 붉고 갈라진 입술, 경부림프절, 전신발진, ESR 상승이 있다. 치료는?","a":"IVIG","lock":"Kawasaki 치료 핵심은 IVIG + aspirin."},
    {"id":"peds2_2026_016","origin":"recent_2026","tier":"P3","mode":"주관식","source":"2026 5·6·7·8조 2주차 프테 주6","axis":"cellulitis-항생제","q":"5세 아이. 전날 39도 고열 이후 발등이 붓고 만지면 아프다. 진단과 치료 항생제는?","a":"Cellulitis / cefazolin, nafcillin, oxacillin, dicloxacillin 등","lock":"비화농성 cellulitis는 MSSA/Strep coverage 축."},
    {"id":"peds2_2026_017","origin":"recent_2026","tier":"P3","mode":"주관식","source":"2026 5·6·7·8조 2주차 프테 주7","axis":"만성복통-alarm symptom","q":"소아 만성복통에서 추가검사가 필요한 alarm symptom을 2가지 이상 쓰시오.","a":"체중감소, 성장부전, 혈변/흑색변, 지속 구토, 야간통, 발열, 관절통, 구강궤양, IBD 가족력 등","lock":"성장·체중·혈변·야간통·전신증상은 기능성으로 넘기면 안 된다."},
    {"id":"peds2_2026_018","origin":"recent_2026","tier":"P3","mode":"주관식","source":"2026 5·6·7·8조 2주차 프테 주8","axis":"급성중이염","q":"화농성 중이염 사진이 제시되었다. 진단 및 1차 치료는?","a":"급성 화농성 중이염 / amoxicillin","lock":"AOM 1차 항생제는 amoxicillin."},
    {"id":"peds2_2026_019","origin":"recent_2026","tier":"P3","mode":"주관식","source":"2026 5·6·7·8조 2주차 프테 주9","axis":"폐동맥판협착","q":"7세 여아. 운동 시 흉통/호흡곤란, wide split S2, P2 약화, CXR에서 좌측 pulmonary artery 확장. 진단은?","a":"Pulmonary stenosis, 폐동맥판협착","lock":"P2 약화 + PA 확장 + 운동 시 증상 → PS."},
    {"id":"peds2_2026_020","origin":"recent_2026","tier":"P3","mode":"주관식","source":"2026 5·6·7·8조 2주차 프테 주10","axis":"High take-off RCA","q":"High take-off RCA의 정의는?","a":"우관상동맥이 정상 위치보다 높은 위치에서 기시하는 것","lock":"High take-off = coronary ostium이 정상보다 위쪽."},

    # Past repeated themes
    {"id":"peds2_past_021","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 11·12·13·14조 2차 객1","axis":"Salmonella","q":"설사, 점액성 혈변, 대변 중성구 다수 소견이 보이면 원인균은?","a":"Salmonella","lock":"침습성 세균성 장염 + 점액혈변 + PMN → Salmonella/Shigella 축, 복기 답 Salmonella."},
    {"id":"peds2_past_022","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 11·12·13·14조 2차 객2","axis":"장중첩증-진단검사","q":"주기적 복통, 갑작스러운 심한 복통, 점액성 혈변이 있는 소아에서 진단을 위한 검사는?","a":"복부초음파","lock":"장중첩증 진단은 abdominal ultrasound, 치료는 air reduction."},
    {"id":"peds2_past_023","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 11·12·13·14조 2차 주6","axis":"Croup","q":"개짖는 듯한 기침과 X-ray상 상기도 협착이 보이는 질환명과 병인은?","a":"Croup / parainfluenza virus","lock":"Barking cough + steeple sign = croup, parainfluenza."},
    {"id":"peds2_past_024","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 11·12·13·14조 2차 주8","axis":"천식 감별","q":"급성기관지염과 천식에서 천식임을 의심할 중요 소견을 3가지 쓰시오.","a":"천식/알레르기 가족력, 말초혈액 호산구 증가, 3회 이상 반복 천명, 베타2 작용제에 의한 호전","lock":"반복성·아토피성·기관지확장제 반응성이 천식 쪽."},
    {"id":"peds2_past_025","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 11·12·13·14조 2차 주9","axis":"소아 혈압 cuff","q":"소아 혈압 측정 시 혈압대 폭과 공기주머니 길이는 각각 어느 정도가 적절한가?","a":"폭은 위팔 중간둘레의 40% 이상, 공기주머니 길이는 위팔둘레의 80-100%","lock":"BP cuff: width 40%, bladder length 80-100%."},
    {"id":"peds2_past_026","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 11·12·13·14조 의국회의","axis":"선천갑상샘저하증 선별","q":"정상 신생아에서 선천성 갑상샘저하증 선별검사의 권장 시기는?","a":"이상적으로 생후 72시간, 최소 생후 48시간 이후","lock":"NBS timing: ideal 72h, at least after 48h."},
    {"id":"peds2_past_027","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 15·16·17·18조 2차 객1","axis":"adenovirus","q":"눈 주위/결막염 사진과 URI/발열 맥락이 제시될 때 반복 복기된 원인 바이러스는?","a":"Adenovirus","lock":"결막염 + 호흡기/인후 증상 = adenovirus를 떠올린다."},
    {"id":"peds2_past_028","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 15·16·17·18조 2차 객2","axis":"Meckel diverticulum","q":"3세 남아가 무통성 대량 선홍색 혈변을 보인다. 진단은?","a":"Meckel diverticulum, 메켈 게실","lock":"소아 무통성 선홍색 혈변 = Meckel."},
    {"id":"peds2_past_029","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 15·16·17·18조 2차 주1","axis":"SSSS","q":"4세 남아. 피부 벗겨짐과 발적, Nikolsky sign 양성. 진단명과 원인균은?","a":"Staphylococcal scalded skin syndrome / Staphylococcus aureus","lock":"Nikolsky+피부박리 소아 = SSSS, S. aureus exfoliative toxin."},
    {"id":"peds2_past_030","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 15·16·17·18조 2차 주2","axis":"만성 비특이 설사","q":"18개월 남아가 한 달 전부터 물 같은 변과 정상 변을 번갈아 보고, 과일주스를 자주 마시며 성장/진찰은 정상이다. 진단은?","a":"만성 비특이 설사, toddler's diarrhea","lock":"정상 성장 + 과일주스 + 만성 물변 = chronic nonspecific diarrhea."},
    {"id":"peds2_past_031","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 15·16·17·18조 2차 주4","axis":"태아순환","q":"태아순환에서 병렬순환을 가능하게 하는 구조물 3가지와 산소포화도가 가장 높은 혈관은?","a":"정맥관, 동맥관, 난원공 / 제대정맥","lock":"DV-DA-FO, 최고 산소포화도는 umbilical vein."},
    {"id":"peds2_past_032","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 15·16·17·18조 의국회의","axis":"cardiomarker","q":"소아 Cardiomarker 평가 항목 2가지는?","a":"Troponin, NT-proBNP","lock":"심근손상은 troponin, 심부전/strain은 NT-proBNP."},
    {"id":"peds2_past_033","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 19·21·22·23조 2차 객1","axis":"EBV infectious mononucleosis","q":"림프구와 비정형 림프구가 많고 전염단핵구증/성홍열/가와사키 등이 선지로 나온 경우 가장 맞는 진단은?","a":"EBV infectious mononucleosis, 전염단핵구증","lock":"Atypical lymphocyte 20% = EBV infectious mononucleosis."},
    {"id":"peds2_past_034","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 19·21·22·23조 2차 객2","axis":"탈수-정맥수액","q":"10개월 영아가 설사 후 2kg 감소하고 처져 있다. 필요한 처치는?","a":"0.9% 생리식염수 정맥주사","lock":"처짐/중증 탈수면 ORS보다 isotonic saline IV부터."},
    {"id":"peds2_past_035","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 19·21·22·23조 2차 객3","axis":"영유아 호흡기 특성","q":"영유아가 호흡기 질환에 취약한 해부·생리학적 이유로 옳은 축은?","a":"기도 지름이 좁고, 후두개가 크며, 비강호흡 의존도가 높다","lock":"작은 기도는 부종 조금에도 저항이 크게 증가한다."},
    {"id":"peds2_past_036","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 19·21·22·23조 2차 주7","axis":"Hirschsprung-DRE gas","q":"생후 5주 남아. 잘 먹지 못하고 반복 구토, 복부팽만. DRE 후 손가락을 빼자 가스가 나왔다. 진단은?","a":"선천거대결장, Hirschsprung disease","lock":"복부팽만 + DRE 후 explosive gas/stool = Hirschsprung."},
    {"id":"peds2_past_037","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 19·21·22·23조 2차 주8","axis":"AOM 합병증","q":"급성 중이염의 합병증을 3가지 이상 쓰시오.","a":"유양돌기염, 안면신경마비, 미로염, 수막염, 뇌농양, 경막외/경막하 농양 등","lock":"귀 주변 합병증 + 두개내 합병증으로 묶어 외운다."},
    {"id":"peds2_past_038","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 19·21·22·23조 2차 주9","axis":"TOF spell 응급치료","q":"TOF hypoxic spell의 내과적 응급치료를 쓰시오.","a":"Knee-chest position, 산소, morphine, phenylephrine 등 혈관수축제, 수액/탈수 교정, 베타차단제, 산증 교정 등","lock":"SVR 올리고, RVOT spasm 줄이고, 탈수/산증 교정."},
    {"id":"peds2_past_039","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 1학기 1·2조 객2","axis":"흉수-측와위","q":"발열, 기침, 흉통, 복통이 있고 CXR상 pleural effusion이 의심된다. 다음에 시행할 X-ray는?","a":"측와위 X-ray, lateral decubitus view","lock":"흉수 양/이동성 확인은 decubitus view."},
    {"id":"peds2_past_040","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 1학기 1·2조 객3","axis":"세균성 뇌수막염","q":"두통, 구토, Kernig sign 양성. CSF에서 WBC 증가, PMN 우세, 단백 증가, glucose 감소가 보인다. 진단은?","a":"세균성 뇌수막염","lock":"CSF PMN↑, protein↑, glucose↓ = bacterial meningitis."},
    {"id":"peds2_past_041","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 1학기 1·2조 객4","axis":"DiGeorge-심장기형","q":"DiGeorge/CATCH22 의심 얼굴·천명음 맥락에서 흔히 동반될 수 있는 심혈관 기형으로 복기된 답은?","a":"VSD","lock":"복기 답은 VSD. 일반적으로는 conotruncal anomaly 축도 같이 기억."},
    {"id":"peds2_past_042","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 1학기 1·2조 주1","axis":"고유량 산소공급","q":"고유량 산소 공급 방법을 3가지 이상 쓰시오.","a":"기관내삽관, Venturi mask, 산소텐트, 산소후드 등","lock":"텐트/후드/벤투리/삽관을 세트로."},
    {"id":"peds2_past_043","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 1학기 1·2조 주2","axis":"급성췌장염 진단기준","q":"소아 급성 췌장염의 진단기준을 쓰시오.","a":"상복부 급성복통/압통, amylase 또는 lipase 정상상한 3배 이상, 영상검사상 급성췌장염 소견 중 2개 이상","lock":"통증·효소 3배·영상 중 2개."},
    {"id":"peds2_past_044","origin":"past_recall","tier":"P2","mode":"야마","source":"2025/2023 반복 백일해","axis":"백일해","q":"짧고 반복적인 발작성 기침 뒤 흡기성 whoop 또는 구토가 있는 소아. 원인균과 치료 항생제는?","a":"Bordetella pertussis / macrolide, 예: azithromycin, erythromycin, clarithromycin","lock":"Pertussis = Bordetella pertussis + macrolide."},
    {"id":"peds2_past_045","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 25·28조 객2","axis":"활동결핵 접촉 영아","q":"생후 50일 영아가 활동성 결핵 환자인 할머니와 접촉했다. 처치는?","a":"TST 시행 + INH 예방치료 축","lock":"어린 영아 TB 접촉은 검사만 기다리지 말고 INH window prophylaxis를 생각."},
    {"id":"peds2_past_046","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 25·28조 객4","axis":"거짓막대장염","q":"항생제 치료 후 설사, 혈변, 복통이 생기고 대장내시경에서 막이 보인다. 진단은?","a":"거짓막 대장염, C. difficile 감염","lock":"항생제 후 pseudomembrane = C. difficile."},
    {"id":"peds2_past_047","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 25·28조 객5","axis":"감염성 심내막염 예방","q":"감염성 심내막염 예방이 필요한 고위험 심질환으로 맞는 것은?","a":"교정하지 않은 청색증형 선천심질환 등","lock":"Unrepaired cyanotic CHD는 IE prophylaxis high-risk."},
    {"id":"peds2_past_048","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 25·28조 주3","axis":"식도폐쇄","q":"34주 출생아. 출생 직후 호흡곤란, 산전 양수과다증, 비위관 삽입 시 저항감. 진단은?","a":"선천성 식도폐쇄, congenital esophageal atresia","lock":"NG tube 안 들어감 + polyhydramnios = esophageal atresia."},
    {"id":"peds2_past_049","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 25·28조 의국회의","axis":"수술 전 항생제","q":"수술 전 예방적 항생제의 가장 적절한 투여 시점은?","a":"수술 60분 전","lock":"수술 예방 항생제는 incision 전 60분 이내."},
    {"id":"peds2_past_050","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 29·32조 주1","axis":"성홍열-S.pyogenes","q":"고열, 인후통, 딸기혀, 전신 홍반성 발진. 원인균과 항생제로 예방하는 합병증은?","a":"Streptococcus pyogenes / 류마티스열 등","lock":"Scarlet fever = GAS, 치료 목적 중 하나는 rheumatic fever 예방."},
    {"id":"peds2_past_051","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 33·36조 주1","axis":"신생아 HSV","q":"13일 신생아. 수포성 발진, 경련, 축 늘어짐. 원인 병원체와 치료는?","a":"Herpes simplex virus / acyclovir","lock":"신생아 vesicle + seizure = HSV, acyclovir 즉시."},
    {"id":"peds2_past_052","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 33·36조 주2","axis":"부비동염 합병증","q":"부비동염의 합병증을 3가지 이상 쓰시오.","a":"안와/안와주위 연조직염, 안와농양, 수막염, 경막외농양, 경막하농양 등","lock":"Orbit complication + intracranial complication으로 묶는다."},
    {"id":"peds2_past_053","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 33·36조 주3","axis":"PSVT","q":"9세 소아가 감기 중 심박수가 빠르고, ECG상 규칙적인 narrow QRS tachycardia가 제시되었다. 진단과 치료는?","a":"PSVT / adenosine","lock":"소아 regular narrow QRS tachycardia = PSVT, acute drug adenosine."},
    {"id":"peds2_past_054","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 37·40조 객3","axis":"수막알균","q":"발열, 두통, 경부강직. CSF에서 PMN 증가와 당 감소, Gram negative diplococci가 보인다. 원인균은?","a":"Neisseria meningitidis, 수막알균","lock":"Gram-negative diplococci meningitis = meningococcus."},
    {"id":"peds2_past_055","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 37·40조 주1","axis":"Kawasaki 감별","q":"Kawasaki disease의 감별진단을 5가지 쓰시오.","a":"성홍열, 홍역, Stevens-Johnson syndrome, toxic shock syndrome, EBV 감염 등","lock":"Kawasaki mimic은 감염성 발진질환과 점막/쇼크 질환으로 묶는다."},
    {"id":"peds2_past_056","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 37·40조 주2","axis":"결핵 4제","q":"객혈, 피로, CXR상 cavity/infiltration으로 결핵이 의심된다. 초기 4제 약제는?","a":"INH, RMP, EMB, PZA","lock":"활동성 결핵 기본 4제 = isoniazid, rifampin, ethambutol, pyrazinamide."},
    {"id":"peds2_past_057","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 21·24조 객1","axis":"rotavirus","q":"생후 8일 환아. 묽은 변과 복부팽만, 같은 조리원에 비슷한 증상을 보이는 환아가 다수. 원인 병원체는?","a":"Rotavirus","lock":"조리원 신생아 집단 설사 복기 답은 rotavirus."},
    {"id":"peds2_past_058","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 21·24조 객2","axis":"PS","q":"7세 남아. LUSB midsystolic murmur, P2 감소, CXR pulmonary artery bulging. 진단은?","a":"Pulmonary stenosis","lock":"LUSB systolic murmur + P2 감소 + PA bulging = PS."},
    {"id":"peds2_past_059","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 21·24조 객3","axis":"epiglottitis","q":"후두경 검사에서 후두개가 붓고 붉다. 가능한 치료 3가지는?","a":"기도삽관, 비기관삽관 또는 기관절개술, 항생제","lock":"Epiglottitis는 기도확보가 먼저, 항생제는 그 다음."},
    {"id":"peds2_past_060","origin":"past_recall","tier":"P2","mode":"야마","source":"2023 21·24조 객5","axis":"식도 이물","q":"2세 아이가 뭔가를 삼킨 뒤 먹으려 하지 않는다. AP/lateral CXR에서 동전 같은 이물이 기관 뒤쪽, 즉 식도 쪽에 걸린다. 처치는?","a":"응급 위식도 내시경 또는 내시경 제거","lock":"식도 이물 + 섭취 거부 = 내시경 제거."},
    {"id":"peds2_past_061","origin":"past_recall","tier":"P2","mode":"야마","source":"2025 11·12·13·14조 객5","axis":"생리적 폐동맥분지협착음","q":"생후 18일 남아. LUSB 2/6 ejection murmur, P2, S2 splitting, ejection click 없음. 진단은?","a":"생리적 폐동맥분지협착음, physiologic peripheral pulmonary stenosis","lock":"신생아 LUSB ejection murmur + click 없음 = physiologic PPS."},

    # This week's conference candidates
    {"id":"peds2_conf_062","origin":"conference","tier":"P1","mode":"의국회의 후보","source":"강렬 실제 의국회의 메모: DSD/무월경 case","axis":"45,X/46,XY mixed gonadal dysgenesis","q":"16세 phenotypic female의 primary amenorrhea. Short stature/Turner stigmata, SRY 양성, AMH low, uterus 존재, GnRH stimulation에서 LH/FSH 상승, hCG stimulation 양성. 핵심 진단축과 처치는?","a":"45,X/46,XY mosaic mixed gonadal dysgenesis / Y material이 있는 dysgenetic gonad는 gonadoblastoma 위험 때문에 gonadectomy","lock":"Y material + dysgenetic/streak gonad = gonadoblastoma risk → gonadectomy."},
    {"id":"peds2_conf_063","origin":"conference","tier":"P1","mode":"의국회의 후보","source":"2026-05-14 의국회의: NGS/rWGS","axis":"NGS-rWGS-Trio WGS","q":"NGS, panel, WES, WGS, rWGS, Trio WGS를 각각 어떻게 구분하는가?","a":"NGS는 sequencing 기술/platform. Panel/WES/WGS는 검사 범위. WES는 exon, WGS는 whole genome. rWGS는 급성 중증 신생아·소아 희귀질환에서 빠른 진단/치료결정 목적. Trio WGS는 환아+부모 분석으로 de novo/compound heterozygous/VUS 해석에 유리","lock":"기술은 NGS, 범위는 panel-WES-WGS, 임상 속도는 rWGS, 해석력은 trio."},
    {"id":"peds2_conf_064","origin":"conference","tier":"P1","mode":"의국회의 후보","source":"2026-05-14 의국회의: NGS/rWGS","axis":"유전검사 해석","q":"rWGS/NGS 의국회의에서 sequencing 자체보다 더 중요하다고 강조된 해석 축은?","a":"Phenotype과 variant database 기반 해석, 국내 데이터 확보","lock":"유전검사는 읽는 것보다 phenotype에 맞게 해석하는 것이 핵심."},
]


def e(value: object) -> str:
    return html.escape(str(value), quote=False)


def pill(text: str, cls: str = "") -> str:
    return f'<span class="pill {cls}">{e(text)}</span>'


def answer_html(card: dict) -> str:
    note = card.get("note", "")
    note_html = f"""
  <div style="border-left:4px solid #f97316;background:#fff7ed;padding:10px 12px;border-radius:10px;color:#7c2d12;">
    <strong>주의:</strong> {e(note)}
  </div>
""" if note else ""
    return f"""
<section class="kmle-answer" style="display:flex;flex-direction:column;gap:12px;">
  <div style="border-left:4px solid #2563eb;background:#eff6ff;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#1d4ed8;margin-bottom:6px;letter-spacing:.04em;">문제</div>
    <div style="font-size:15px;line-height:1.72;color:#111827;">{e(card['q'])}</div>
  </div>
  <div style="border-left:4px solid #16a34a;background:#f0fdf4;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#15803d;margin-bottom:6px;letter-spacing:.04em;">답</div>
    <div class="answer-main" style="font-size:20px;line-height:1.55;color:#052e16;"><strong>{e(card['a'])}</strong></div>
  </div>
  <div style="border-left:4px solid #f59e0b;background:#fffbeb;padding:12px 14px;border-radius:10px;">
    <div style="font-size:12px;font-weight:900;color:#b45309;margin-bottom:6px;letter-spacing:.04em;">3초 lock line</div>
    <div style="font-size:15px;line-height:1.7;color:#422006;">{e(card['lock'])}</div>
  </div>
  {note_html}
  <details style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px 12px;color:#334155;">
    <summary style="cursor:pointer;font-weight:800;">출처 / 분류</summary>
    <div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap;">
      {pill(ORIGIN_LABELS.get(card['origin'], card['origin']))}
      {pill(TIER_LABELS.get(card['tier'], card['tier']))}
      {pill(card['mode'])}
      {pill(card['axis'])}
    </div>
    <p style="margin-top:10px;"><code>{e(card['source'])}</code></p>
  </details>
</section>
""".strip()


def guide_html(card: dict) -> str:
    return f"""
<section class="kmle-guide" style="line-height:1.7;">
  <h4>문제</h4><p>{e(card['q'])}</p>
  <h4>답</h4><p><strong>{e(card['a'])}</strong></p>
  <h4>3초 lock</h4><p>{e(card['lock'])}</p>
  <table>
    <tr><th>출처</th><td>{e(card['source'])}</td></tr>
    <tr><th>우선순위</th><td>{e(TIER_LABELS.get(card['tier'], card['tier']))}</td></tr>
    <tr><th>축</th><td>{e(card['axis'])}</td></tr>
    <tr><th>성격</th><td>{e(ORIGIN_LABELS.get(card['origin'], card['origin']))}</td></tr>
  </table>
</section>
""".strip()


def question_html(card: dict) -> str:
    return f"""
<div style="display:flex;flex-direction:column;gap:8px;width:100%;">
  <div style="font-size:11px;font-weight:900;color:#93c5fd;letter-spacing:.06em;">문제</div>
  <div style="font-size:14px;line-height:1.62;color:#e5e7eb;">{e(card['q'])}</div>
  <div style="display:flex;gap:5px;flex-wrap:wrap;align-items:center;">
    <span class="q-tier">{e(card['tier'])}</span>
    <span class="q-type">{e(ORIGIN_LABELS.get(card['origin'], card['origin']))}</span>
    <span class="q-type">{e(card['mode'])}</span>
  </div>
</div>
""".strip()


def build_cards() -> list[dict]:
    cards = []
    for i, card in enumerate(CARDS, 1):
        cards.append({
            "id": card["id"],
            "num": i,
            "q": question_html(card),
            "a": answer_html(card),
            "g": guide_html(card),
        })
    return cards


def main() -> None:
    DATA.write_text(json.dumps(CARDS, ensure_ascii=False, indent=2), encoding="utf-8")
    builder = QuizBuilder(
        cards=build_cards(),
        title=TITLE,
        subtitle="최신 2026 2차 복기 20문항 + 과거 반복 야마 + 이번 주 의국회의 후보",
        storage_prefix=STORAGE_PREFIX,
        enable_self_answer=False,
        randomize_review=True,
    )
    builder.write(str(OUT))
    print(f"cards: {len(CARDS)}")
    print(f"data: {DATA}")
    print(f"out: {OUT}")
    print(f"storage_prefix: {STORAGE_PREFIX}_")


if __name__ == "__main__":
    main()
