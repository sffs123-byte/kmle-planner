# 의료법규 Allen Split Quiz + Concept App

## 산출물

- `medical_law_split_quiz_concept.html` — 위 퀴즈 / 아래 개념 split standalone HTML
- `medical_law_split_app_data.json` — 66 sourcepack + 247 sourcepack 후보 + 기존 pretest seed 86 통합 데이터

## 포함 범위

- Sourcepack topics: 66
- Sourcepack-generated quiz candidates: 247
- Existing pretest seed cards: 86
- Total quiz cards: 333

## UX

- 기본 모드: sourcepack 후보를 순서대로 학습
- deck 전환: sourcepack 후보 / 기존 pretest seed / 전체
- 법령 필터, 검색, 순서/랜덤, 정답공개, 하단 개념 패널
- 하단 개념 패널은 현재 카드의 sourcepack switch map, stem trigger, 오답 제거, 문제 후보, 원문 excerpt 표시

## 주의

- 기존 86카드는 full bank가 아니라 고빈도/함정 seed layer다.
- 495문항 full bank가 들어오면 sourcepack topic id에 추가 매핑해 확장한다.
