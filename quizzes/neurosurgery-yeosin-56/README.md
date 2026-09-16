# 신경외과 여신 완성본 · 56문제 Anki

기존 `anki` / `anki-quiz-builder` 스킬의 공용 `QuizBuilder`를 사용하는 덱입니다.
별도 카드 앱 대신 다른 과목과 동일한 Anki SRS·필기·편집 방식을 사용합니다.

## 사용

- 순서대로 / 랜덤 시작 → 정답 보기 → 색상 버튼으로 복습 시점 선택.
- 다시 1분 / 어려움 5분 / 보통 10분(연속 2회면 숙달) / 내일 1일.
- 랜덤 초기 큐는 중복 없이 구성되며, 복습 시각이 된 카드는 다시 출제됩니다.
- 새로고침하면 현재 카드·순서·정답 공개·Study Guide 상태가 복원됩니다.
- 전체 다시 풀기: 확인 후 이 덱의 SRS·평가·진도만 초기화하며, 수정 답안·개인 메모·필기는 남습니다.
- 기존 🍎 필기(펜·형광펜·지우개·올가미) / ✏️ 정답 편집 / 📋 복사 / Study Guide 지원.
- 수정본 내보내기·불러오기로 SRS·필기·수정 내용을 백업합니다.
- 이전 별도 앱의 브라우저 저장 키는 삭제하지 않고 개인 메모를 수정 답안에 옮깁니다. 이전의 단순 평가는 SRS 숙달로 바꾸지 않습니다.

## 재생성

저장소 루트에서:

```sh
python3 quizzes/neurosurgery-yeosin-56/build_deck.py
```

- 내용 원본: `deck.json` (중복통합 56개, 이전 버전과 동일)
- 생성기: `generate_skill_deck.py`
- 공용 UI·학습 엔진: `../anki_quiz_builder.py` (기존 skill 빌더)
- 공용 백업: `../anki_backup_restore.py`
- 이 덱 한정 보완: `deck-layout.css`, `storage-adapter.js`, `skill-adapter.js`
- 결과: `index.html`, `build-qc.json`

기존 `app.js`, `style.css`, `deck.js`는 이전 버전 기록으로 보존되며 현재 HTML에서 불러오지 않습니다.
운영 노트·하단 해설·댓글·원본 PDF는 수정하지 않습니다. 환자 식별정보나 비공개 PDF는 포함하지 않습니다.
