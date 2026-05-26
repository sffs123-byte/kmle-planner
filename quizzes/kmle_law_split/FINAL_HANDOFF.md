# 의료법규 Split Quiz + Concept App — Final Handoff

## 결과물

- `outputs/kmle/medical_law_split_app_20260526/index.html`
- `outputs/kmle/medical_law_split_app_20260526/medical_law_split_quiz_concept.html`
- `outputs/kmle/medical_law_split_app_20260526/medical_law_split_app_data.json`
- `outputs/kmle/medical_law_split_app_20260526/medical_law_split_quiz_concept_20260526.zip`
- 빌더 스크립트: `outputs/kmle/medical_law_sourcepack_20260526/build_medical_law_split_app.py`

## 포함 데이터

- sourcepack topics: 66
- sourcepack-generated quiz candidates: 247
- existing pretest seed cards: 86
- total quiz cards: 333

## 앱 구조

- 위 패널: 퀴즈
- 아래 패널: sourcepack 개념
- deck 전환:
  - Sourcepack 후보 247
  - 기존 Pretest seed 86
  - 전체 333
- 기능:
  - 법령 필터
  - 검색
  - 순서대로 / 랜덤
  - 정답 보기 / 숨기기
  - 현재 카드와 연결된 switch map, stem trigger, 오답 제거, 문제 토글 후보, 원문 excerpt 표시

## 검증

### Sourcepack parent QC
- sourcepack_files: 66
- batch_result_count: 16
- missing_batch_results: []
- todo_files: 0
- contract_fail_files: 0
- noise_files: 0

### App data QC
- title_ok: True
- topic_count_ok: True
- card_count_ok: True
- todo_in_data: False
- noise_in_data: False
- topic_minima_bad_count: 0

### Runtime/parse checks
- JS syntax: `node --check` PASS
- local HTTP 200 check: PASS
- browser smoke: Playwright Chromium binary 미설치 + localhost browser policy 제약으로 미실행

## 메모

- 기존 86카드 seed는 full 495 bank가 아니라 고빈도/함정 seed layer다.
- 이 앱은 현재 **standalone local artifact**다. 외부 배포/링크 반영은 별도 승인 후 진행.
- 495 full problem bank를 받으면 sourcepack topic id에 더 정밀한 매핑을 추가할 수 있다.
