#!/usr/bin/env python3
"""
심장내과 Pre-test 퀴즈 HTML 생성기
- Q1~Q10, 총 10문항
- PDF 페이지 이미지 포함
"""

import os, sys, io, base64
from pdf2image import convert_from_path
from anki_quiz_builder import QuizBuilder

PDF_CANDIDATES = [
    os.environ.get("CARDIO_PRETEST_PDF"),
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "심장내과_Pre_test_수정본.pdf"
    ),
]


def resolve_pdf_path():
    for candidate in PDF_CANDIDATES:
        if candidate and os.path.exists(os.path.abspath(candidate)):
            return os.path.abspath(candidate)
    raise FileNotFoundError(
        "심장내과 Pre-test PDF를 찾지 못했습니다. "
        "CARDIO_PRETEST_PDF=/path/to/pdf 로 지정한 뒤 다시 실행하세요."
    )

# ── 카드 데이터 ──────────────────────────
CARDS = [
    {
        "id": "c1", "num": 1,
        "q": "Normal EKG를 그리고, wave, interval, segment에 대해 설명하시오.",
        "a": """<h4>Wave, Segment, Interval 정의</h4>
<p>- <b>wave</b>: 각각의 파장<br>
- <b>segment</b>: wave 사이 평평한 부분<br>
- <b>interval</b>: wave와 segment를 포함하여 통칭</p>

<h4>1) Wave</h4>
<p>(1) <b>P wave</b>: atrial depolarization<br>
(2) <b>QRS complex</b>: ventricular depolarization<br>
&nbsp;&nbsp;- Q wave: septal depolarization<br>
&nbsp;&nbsp;- R wave: ventricular depolarization<br>
&nbsp;&nbsp;- S wave: LV posterior wall depolarization<br>
(3) <b>T wave</b>: ventricular repolarization</p>

<h4>2) Segment</h4>
<p>(1) <b>PR segment</b>: AV node → ventricle로의 depolarization 지연<br>
(2) <b>ST segment</b>: ventricular depolarization 이후 ventricular repolarization 이전까지</p>

<h4>3) Interval</h4>
<p>(1) <b>PR interval</b> (P wave + PR segment): atrial depolarization 시작부터 AV node에서의 지연까지<br>
(2) <b>QT interval</b> (QRS complex + ST segment + T wave): ventricular depolarization 시작부터 ventricular repolarization 끝까지</p>""",
        "pages": [1],
    },
    {
        "id": "c2", "num": 2,
        "q": "Syncope 원인에 대한 감별진단을 3가지 이상 나열하고, 진단 과정에 대해 설명하시오.",
        "a": """<h4>1) Vasovagal syncope</h4>
<p>신체적 또는 정신적 긴장으로 인해 교감신경이 활성화되고, 이를 억제하기 위한 부교감신경의 일시적 과활성화가 원인</p>
<p>- <b>Tilt table test</b>: 기립성 저혈압과 감별진단<br>
- <b>자율신경계 관련 검사</b>: 기타 neural syncope와의 감별 진단</p>

<h4>2) Orthostatic hypotension</h4>
<p>기립 시 venous return 감소 및 중력에 의해 일시적으로 뇌혈류가 감소하는데, 이를 보상하기 위한 자율신경계 활성이 충분치 않음</p>
<p>- <b>Tilt table test</b>: 5분 이상 누운 상태에서 측정한 혈압과 비교하여, 기립 후 3분 안에 SBP/DBP가 20/10mmHg 이상 감소하는 경우</p>

<h4>3) Cardiac syncope</h4>
<p>부정맥이나 판막 질환 등에 의해 stroke volume 유지가 힘들어져 cardiac output 유지가 되지 않아 발생</p>
<p>- <b>ECG, Holter, 심초음파</b>: 가장 위험하므로 우선 배제 위한 검사 진행</p>""",
        "pages": [1],
    },
    {
        "id": "c3", "num": 3,
        "q": "측정 방법에 따른 고혈압 진단 기준을 정의하고 대표적인 고혈압 약제의 적응증 및 흔한 부작용에 대해 설명하시오.",
        "a": """<h4>혈압 분류</h4>
<table>
<tr><th></th><th>SBP</th><th></th><th>DBP</th></tr>
<tr><td>정상</td><td>&lt;120</td><td>and</td><td>&lt;80</td></tr>
<tr><td>주의 혈압</td><td>120-129</td><td>and</td><td>&lt;80</td></tr>
<tr><td>고혈압 전단계</td><td>130-139</td><td>or</td><td>80-89</td></tr>
<tr><td>고혈압 1기</td><td>140-159</td><td>or</td><td>90-99</td></tr>
<tr><td>고혈압 2기</td><td>≥160</td><td>or</td><td>≥100</td></tr>
<tr><td>수축기 단독 고혈압</td><td>≥140</td><td>and</td><td>&lt;90</td></tr>
</table>

<h4>측정 방법에 따른 고혈압 진단 기준</h4>
<p>1) 진료실 혈압 ≥140/90<br>
2) 가정 혈압 ≥135/85<br>
3) 24시간 활동 혈압: 주간 ≥135/85, 야간 ≥120/70, 일일 ≥130/80<br>
4) 진료실 자동 혈압 ≥135/85</p>

<h4>고혈압 약제</h4>
<table>
<tr><th>약제</th><th>적극적 적응</th><th>금기</th><th>부작용</th></tr>
<tr><td><b>ACEi/ARB</b></td><td>심부전, DM with albuminuria, CKD</td><td>Hyperkalemia, Renal failure, bilateral RAS, 임신</td><td>Hyperkalemia, 마른기침(ACEi), 혈관부종(ACEi)</td></tr>
<tr><td><b>BB</b></td><td>심부전, 협심증, 심근경색, 빈맥성 부정맥</td><td>천식, COPD, 심한 서맥, 말초혈관질환</td><td>천식 악화, 서맥, diabetogenic potential</td></tr>
<tr><td><b>CCB</b></td><td>협심증, 수축기 단독 고혈압, 빈맥</td><td>서맥(non-DHP)</td><td>DHP: 홍조, 두통, 부종 / NDHP: AV block, 심근 수축력 저하</td></tr>
<tr><td><b>Thiazide</b></td><td>심부전, 수축기 단독 고혈압</td><td>통풍, 저칼륨혈증</td><td>Hypo NA, metabolic alkalosis, dyslipidemia, 인슐린 저항성 증가</td></tr>
</table>""",
        "pages": [2],
    },
    {
        "id": "c4", "num": 4,
        "q": "심방세동의 항응고치료에서 CHA₂DS₂-VASc score 각 항목과 치료 기준에 대해 나열하시오.",
        "a": """<h4>CHA₂DS₂-VASc score</h4>
<table>
<tr><th>항목</th><th>위험인자</th><th>점수</th></tr>
<tr><td><b>C</b></td><td>CHF, LV dysfunction</td><td>1</td></tr>
<tr><td><b>H</b></td><td>Hypertension</td><td>1</td></tr>
<tr><td><b>A₂</b></td><td>Age ≥75세</td><td>2</td></tr>
<tr><td><b>D</b></td><td>Diabetes mellitus</td><td>1</td></tr>
<tr><td><b>S₂</b></td><td>Stroke, TIA, thromboembolism 병력</td><td>2</td></tr>
<tr><td><b>V</b></td><td>Vascular disease (MI, PAD, aortic plaque) 병력</td><td>1</td></tr>
<tr><td><b>A</b></td><td>Age 65-74세</td><td>1</td></tr>
<tr><td><b>Sc</b></td><td>Sex-category: female</td><td>1</td></tr>
</table>

<h4>심방세동 항응고치료 기준</h4>
<p>항응고제: DOAC(NOAC), warfarin</p>
<p><b>CHA₂DS₂-VA score</b><br>
- <b>2점 이상</b>: 항응고치료 시행<br>
- <b>1점</b>: 항응고치료 고려<br>
- <b>0점</b>: 시행하지 않음</p>""",
        "pages": [2],
    },
    {
        "id": "c5", "num": 5,
        "q": "운동부하검사 treadmill stress test의 양성 소견에 대해 설명하시오.",
        "a": """<h4>운동부하검사 양성 소견</h4>
<p>이미지 기준으로 양성 소견은 세 축으로 정리한다.</p>

<h4>1. EKG 변화</h4>
<p>- <b>Horizontal/Down-sloping ST depression</b>이 <b>1mm 이상</b>이며 <b>0.08초 이상 지속</b><br>
- <b>pathologic Q wave가 없는 lead</b>에서 <b>1mm 이상 ST elevation</b><br>
&nbsp;&nbsp;단, <b>aVR, V1은 제외</b></p>

<h4>2. 임상 증상</h4>
<p>- <b>Chest pain, tightness</b> 등의 <b>typical angina</b> 증상이 유발되는 경우</p>

<h4>3. Hemodynamic change, BP response</h4>
<p>- workload가 증가하는데도 <b>SBP가 기저치보다 10mmHg 이상 감소</b>하는 경우</p>""",
        "pages": [3],
    },
    {
        "id": "c6", "num": 6,
        "q": "Unstable angina/NSTEMI의 정의와 병인에 대해 설명하시오.",
        "a": """<h4>(1) 정의</h4>
<p><b>Unstable angina</b>: 급성 허혈 증상(안정 시 흉통, 최근 새롭게 나타난 흉통, 악화되는 흉통)은 있으나 cardiac enzyme 상승이 나타나지 않아 심근 손상의 증거가 없는 상태</p>
<p><b>NSTEMI</b>: 급성 허혈 증상과 함께 cardiac enzyme 상승 소견이 있으나, ECG 상 지속적 ST elevation이 없는 급성 심근경색</p>

<h4>(2) 병인</h4>
<p>- Plaque의 rupture 또는 endothelium erosion으로 인한 <b>partially occlusive thrombus</b><br>
- Coronary obstruction이 있는 상태에서 myocardial demand의 증가: 운동, 발열, 빈맥, 갑상선 항진증</p>""",
        "pages": [3],
    },
    {
        "id": "c7", "num": 7,
        "q": "Heart failure stage를 정의하고 각 단계의 치료 및 acute heart failure 치료에 대해 설명하시오.",
        "a": """<h4>심부전의 Stage &amp; Management</h4>
<table>
<tr><th>Stage</th><th>정의</th><th>치료</th></tr>
<tr><td><b>A</b></td><td>HF를 일으킬 수 있는 선행질환(HTN, DM, CVD 등)은 있으나, 구조적 변화나 HF 증상 없음</td><td>위험인자 조절</td></tr>
<tr><td><b>B</b></td><td>구조적 변화(LV 비대, 섬유화, 확장, 기능저하)는 있으나 HF 증상 없음</td><td>Stage A + ACEi/ARB + BB {+ statin(MI), SGLT2-i(LVEF&lt;40%)}</td></tr>
<tr><td><b>C</b></td><td>구조적 변화 + HF의 증상이 한번이라도 있었음</td><td>Stage B + <b>4-pillars</b> (ARNI or ACEi/ARB / BB / MRA / SGLT2-i) + 이뇨제</td></tr>
<tr><td><b>D</b></td><td>약물에도 증상 심해 일상생활 제한, 특별 치료 필요</td><td>Stage C + LVAD, 심장이식, IV inotrope, ECMO, hospice</td></tr>
</table>

<h4>Acute Heart Failure 치료</h4>
<table>
<tr><th></th><th>Dry</th><th>Wet</th></tr>
<tr><td><b>Warm</b></td><td>기존 약물 유지, 원인 파악</td><td>IV diuretics + vasodilator(sBP&gt;90)</td></tr>
<tr><td><b>Cold</b></td><td>수액치료</td><td>수축촉진제/승압제, vasodilator(sBP&gt;90), mechanical support</td></tr>
</table>""",
        "pages": [4],
    },
    {
        "id": "c8", "num": 8,
        "q": "Valvular heart disease 심잡음의 청진 부위 및 특징에 대해 서술하고, 시술/수술의 적응증에 대해 설명하시오.",
        "a": """<h4>VHD 심잡음의 청진 부위 및 특징</h4>
<table>
<tr><th>VHD</th><th>청진 부위</th><th>특징</th></tr>
<tr><td><b>AS</b></td><td>Aortic valve area (RUSB, Rt. 2nd ICS)</td><td>Mid-systolic ejection murmur, 목으로 방사, S2 단일/paradoxical splitting</td></tr>
<tr><td><b>AR</b></td><td>Erb's area (Lt. sternal border, Lt. 3rd ICS)</td><td>Early-diastolic murmur</td></tr>
<tr><td><b>MS</b></td><td>Mitral valve area (MCL, Lt. 5th ICS)</td><td>Mid-diastolic rumbling murmur with opening snap</td></tr>
<tr><td><b>MR</b></td><td>Mitral valve area</td><td>Pansystolic murmur, Axilla로 방사, S2 wide splitting</td></tr>
</table>

<h4>VHD 시술/수술의 적응증</h4>
<table>
<tr><th>VHD</th><th>적응증</th></tr>
<tr><td><b>AS</b></td><td>(1) symptomatic severe AS<br>(2) asymptomatic severe AS + LV dysfunction (LVEF&lt;50%)<br>(3) 다른 심장 수술을 받을 때</td></tr>
<tr><td><b>AR</b></td><td>(1) Acute AR<br>(2) symptomatic severe AR<br>(3) asymptomatic severe AR + (LVEF&lt;55% 또는 LVESD&gt;50mm)<br>(4) 다른 심장 수술을 받을 때</td></tr>
<tr><td><b>MS</b></td><td>(1) symptomatic severe MS (MVA &lt; 1.5cm²)<br>(2) asymptomatic severe MS + (New AF or Pulmonary HTN)</td></tr>
<tr><td><b>MR</b></td><td>(1) Acute MR<br>(2) symptomatic severe MR<br>(3) asymptomatic severe MR + (LVEF&lt;60% 또는 LVESD&gt;40mm)</td></tr>
</table>""",
        "pages": [4],
    },
    {
        "id": "c9", "num": 9,
        "q": "Critical limb ischemia의 임상적 특징과 chronic limb ischemia의 Rutherford classification과 치료에 대해 설명하시오.",
        "a": """<h4>Critical Limb Ischemia의 임상적 특징</h4>
<p>1) 2주 이상 지속되는 허혈 증상<br>
2) 자세에 따른 통증 변화: 누우면 악화, 앉거나 다리를 내리면 완화(중력에 의해 동맥 관류 증가)<br>
3) 피부 및 조직 변화: 궤양, 괴사, 창백/청색/자색 변화<br>
4) 객관적 허혈 지표: ABI ≤0.4, ankle SBP &lt;50mmHg, toe SBP &lt;30mmHg</p>

<h4>Rutherford Classification</h4>
<table>
<tr><th>Grade</th><th>C</th><th>Clinical</th></tr>
<tr><td>0</td><td>0</td><td>Asymptomatic: 증상 없음</td></tr>
<tr><td rowspan="3">I</td><td>1</td><td>Mild claudication: 짧은 거리 보행 시 간헐적 파행</td></tr>
<tr><td>2</td><td>Moderate claudication: 중등도 보행 장애</td></tr>
<tr><td>3</td><td>Severe claudication: 매우 짧은 거리에서도 통증</td></tr>
<tr><td>II</td><td>4</td><td>Ischemia rest pain: 휴식 시 통증, 밤에 악화, 다리 내리면 호전</td></tr>
<tr><td rowspan="2">III</td><td>5</td><td>Minor tissue loss: 비치유성 궤양, 제한된 발가락 부위 궤양</td></tr>
<tr><td>6</td><td>Major tissue loss: 발가락 여러개 또는 발, 다리의 심부 조직 괴사</td></tr>
</table>

<h4>Chronic Limb Ischemia 치료</h4>
<p><b>PAD (Rutherford 1-3)</b>: 금연, 운동치료, 기저질환 조절. 약물: Cilostazol(TOC, HFrEF 금기). 재관류: 약물/운동으로도 삶의 질 제한 시</p>
<p><b>CLI (Rutherford 4-6)</b>:</p>
<p>1) 재관류 치료<br>
- PTA: 수술 위험 높을 때, 병변 짧고 개수 적을 때, 근위부 병변<br>
- Bypass surgery: 수술 위험 낮을 때, 병변 길고 광범위할 때, 관절 부위나 동맥 분지 부위</p>
<p>2) 상처 관리: Debriment, 항생제, Off-loading<br>
3) 약물 치료: 항혈전제 및 statin<br>
4) 적극적인 통증 조절</p>""",
        "pages": [5],
    },
    {
        "id": "c10", "num": 10,
        "q": "Pulmonary thromboembolism의 치료에 대해 설명하시오.",
        "a": """<h4>PTE 치료: Risk Stratification</h4>
<table>
<tr><th>Risk</th><th>기준</th><th>치료 방향</th></tr>
<tr><td><b>Low risk</b></td><td>Normotension + normal RV</td><td>Secondary prevention</td></tr>
<tr><td><b>Moderate risk</b></td><td>Normotension + RV hypokinesis</td><td>Anticoagulant + individualized therapy</td></tr>
<tr><td><b>High risk</b></td><td>Hypotension</td><td>Primary therapy</td></tr>
</table>

<h4>1) Low risk PTE</h4>
<p><b>Normotension + normal RV</b> → secondary prevention</p>
<p>- <b>Anticoagulant</b>: Heparin, DOAC, warfarin<br>
- <b>IVC filter</b>: 항응고제 금기 시 또는 항응고제에 반응하지 않는 경우 삽입</p>
<p><b>항응고제 금기</b>: 치명적인 현성 출혈, 심하게 높은 PT/aPTT, 심하게 낮은 Plt</p>

<h4>2) Moderate risk PTE</h4>
<p><b>Normotension + RV hypokinesis</b> → anticoagulant + individualized therapy</p>

<h4>3) High risk PTE</h4>
<p><b>Hypotension</b> → primary therapy</p>
<p>- <b>Anticoagulant + thrombolysis</b> (TOC)<br>
- <b>Anticoagulant + embolectomy</b> (catheter, surgical): thrombolysis 금기 시</p>
<p><b>Thrombolysis 금기</b>: 뇌출혈 과거력, 6개월-1년 이내 뇌경색 과거력, CNS tumor, 현성 출혈, 대동맥 박리</p>""",
        "pages": [6],
    },
]


def generate_page_images(pdf_path):
    """PDF에서 페이지 이미지 base64 생성"""
    images = convert_from_path(pdf_path, dpi=200)
    page_images = {}
    for i, img in enumerate(images, 1):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        page_images[i] = base64.b64encode(buf.getvalue()).decode()
    return page_images


if __name__ == "__main__":
    pdf = resolve_pdf_path()

    print(f"PDF: {pdf}")
    print("Generating page images...")
    page_images = generate_page_images(pdf)
    print(f"Loaded {len(page_images)} page images")

    print("Building HTML...")
    builder = QuizBuilder(
        cards=CARDS,
        title="심장내과 Pre-test",
        storage_prefix="cardio_pretest",
        page_images=page_images,
    )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "심장내과_pretest_quiz.html")
    builder.write(out_path)
