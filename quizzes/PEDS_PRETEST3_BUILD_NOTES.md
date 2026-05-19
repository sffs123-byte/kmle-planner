# 소아청소년과 3주차 Pretest 퀴즈 작업 틀

## 목적

3주차 pretest 문제 원본을 받으면 바로 SRS 퀴즈로 흡수할 수 있게 해 두는 scaffold.

## 공식 범위

근거: `Desktop/의학과 공부 파일/본3/소아청소년과/인계/소아청소년과 공지.pdf`

- 1주차: 1~11장
- 2주차: 12~15장 = 감염, 소화기, 호흡기, 심혈관
- 3주차: 16~28장 = 혈액-종양, 신요로, 내분비, 신경-근육, 골격, 알레르기, 결체조직, 피부, 안과, 손상, 통일/기타
- 전 주 아침 집담회 내용이 반영된 문제가 출제될 수 있음.
- 구성: 주관식 5문항 + 객관식 5문항.

## 생성 파일

- 데이터 원본: `quizzes/data/pediatrics_pretest3_cards.json`
- 생성기: `quizzes/generate_pediatrics_pretest3_quiz.py`
- 출력 HTML: `quizzes/소아청소년과_3주차_pretest_quiz.html`

## 카드 스키마

```json
{
  "id": "PEDS3-2026-001",
  "source": "사용자 제공 3주차 문제 모음 / 2026",
  "origin": "actual_recall",
  "priority": "P4 최신2026",
  "official_unit": "혈액-종양",
  "question": "문제 원문. 객관식이면 ①~⑤ 포함.",
  "answer": "정답",
  "explanation": "짧은 해설",
  "enhanced_explanation": "🧭 Big picture\n...\n\n🔎 핵심 단서\n...\n\n👣 시험장 사고 흐름\n...\n\n📊 감별/오답 제거\n...\n\n✅ 3초 Lock line\n...",
  "tags": ["혈액-종양", "빈혈", "actual"],
  "uncertain": false,
  "raw_anchor": "원문에서 확인한 근거 문구",
  "images": [
    {
      "src": "assets/peds_pretest3_question_images/example.png",
      "placement": "front",
      "caption": "원문 이미지",
      "quality": "front-safe"
    }
  ]
}
```

## 원본 들어오면 처리 순서

1. 사용자 제공 문제 모음을 최우선 source of truth로 보존한다.
2. 문항 수를 먼저 센다. 객관식/주관식/이미지 의존 문항을 분리한다.
3. `pediatrics_pretest3_cards.json`에 source-faithful 카드로 넣는다.
4. 같은 답이라도 stem/선지/이미지가 다르면 variant로 보존한다.
5. 불완전 복기는 삭제하지 말고 `uncertain: true`, `원문 확인 필요` badge로 남긴다.
6. 문제 앞면 answer leakage를 검사한다. 특히 단답/서술형은 문제면에 답이 남으면 fail.
7. 공식 3주차 단원 badge와 단원 필터가 맞는지 확인한다.
8. 생성 후 QC: card count, QUIZ_DATA count, title, storage prefix, self-answer box 0, 주요 답/선지 표시.
9. 강렬 확인 후 main/share/deploy 반영 여부를 결정한다.

## 예상 source layer

- `P4 최신2026`: 강렬이 줄 문제 모음 / 최신 복기
- `P3 누적복기`: 2025 3차 docx, 2023 3주차 PDF
- `P2 HI`: `소아과 pre-test 3차_HI.pdf`
- `P2 집담회`: 전 주 아침 집담회/의국회의 문제 후보
- `P1 보강개념`: 실제 문제와 연결되는 필수 개념 보강 카드

