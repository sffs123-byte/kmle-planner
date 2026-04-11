# Canary v1 Verification — 2026-04-11 03:10 KST

> 2026-04-11 오전 추가 반영:
> - 기본 진행률을 전부 **0으로 초기화**하도록 storage key를 갱신하고 기본 로드 상태를 canary 초기 상태로 전환.
> - 호흡기/순환기 과목을 **파트 기반 관리**로 올림.
> - 문풀 total은 강렬이 준 **알렌 문제 수 데이터(y)** 를 파트별로 반영.
> - 강의/개념틀/오답정리/복습은 파트 수 기준, 문풀은 문항 수 기준으로 자동 계산되도록 수정.

## 1) 확인한 항목

| 항목 | 결과 | 메모 |
|---|---|---|
| `index.html` 로컬 서버 실행 | 통과 | `python3 -m http.server 8765`로 확인. 검증 중 서버 1회 종료되어 재기동 후 재검증 완료. |
| `4월 Canary 세팅` 버튼 | 통과 | canary 상태를 적용하고, 바로 `오늘 플래너 / 호흡기 / today / pending`으로 이동하도록 개선 및 실동작 확인. |
| `오늘 학습 시작` 버튼 | 통과 | canary 세팅이 아니면 먼저 canary 적용을 제안한 뒤 오늘 플래너로 이동하도록 개선 및 확인. |
| 과목 상세 `배국자 개념 전송` | 통과 | 체크 후 localStorage 반영 확인. |
| 과목 상세 `배국자 함정 전송` | 통과 | UI 존재 및 상태 저장 경로 확인. |
| 과목 상세 `막힘 이유` | 통과 | 텍스트 저장 후 localStorage 반영 및 새로고침 유지 확인. |
| 진행도 수치 수정 | 통과 | 호흡기 `강의 done=12` 수정 후 새로고침 persistence 확인. |
| localStorage persistence | 통과 | 체크박스/텍스트/수치 수정 후 새로고침 유지 확인. |
| export sanity check | 통과 | export 버튼이 JSON 백업 파일명을 생성하고 현재 상태를 그대로 직렬화하는 것 확인. |
| import roundtrip sanity check | 통과 | export된 JSON으로 동일 normalize/import 경로를 통해 상태 복원 확인. |
| `README.md` / `TODAY_START_GUIDE.md` / 앱 동선 일치 | 통과 | 아침 시작 동선 기준으로 문서 수정 완료. |
| `CANARY_TRACKER_APRIL.md` / `CARDIOLOGY_CHIEF_PREP.md`와 앱 목적 일치 | 통과 | 보조 문서 역할과 앱 내 흐름이 충돌하지 않음 확인. |

## 2) 수정한 내용

### 앱 (`index.html`)
- `buildCanaryState()`를 실제 4월 canary 운영 문맥에 맞게 정리
  - 호흡기/순환기 2과목 중심 유지
  - 주말 task 블록을 `data/canary_import_seed.json`과 같은 방향으로 정렬
  - 과목 설명/다음 액션/메모를 실사용 문구로 교체
- `오늘 학습 시작` 버튼 polish
  - canary 상태가 아니면 먼저 canary 세팅을 제안
  - 이후 곧바로 오늘 플래너(`today / pending / 호흡기`)로 이동
- `4월 Canary 세팅` 버튼 polish
  - 세팅 후 대시보드에 머무르지 않고 바로 오늘 플래너로 이동
- footer에 아침 시작 권장 순서(`4월 Canary 세팅 → 오늘 학습 시작`) 명시

### 문서
- `README.md`
  - `4월 Canary 세팅` 버튼이 곧바로 오늘 플래너로 이동한다는 점 반영
  - `오늘 학습 시작` 버튼의 auto-canary 제안 동선 반영
- `TODAY_START_GUIDE.md`
  - 버튼 동선 기준으로 시작 순서 재정렬
  - `4월 Canary 세팅` 이후 바로 오늘 플래너로 들어간다는 점 반영
  - `오늘 학습 시작` 버튼 설명 추가

## 3) 검증 중 실제 확인한 상태 예시
- canary 적용 후 과목 목록이 `호흡기`, `순환기` 2개로 정리됨
- `오늘 학습 시작` 후 활성 탭이 `주간 플래너`로 전환됨
- 필터가 `today / pending / 호흡기`로 맞춰짐
- 호흡기 과목에서 아래 state 저장 확인
  - `lecture.done = 12`
  - `conceptSent = true`
  - `blockedReason = "PFT 해석이 막힘"`
- 새로고침 후 동일 state 유지 확인
- export JSON 안에도 위 값이 그대로 들어가는 것 확인
- export JSON을 다시 import 경로에 태웠을 때 값이 복원되는 것 확인

## 4) 아직 남은 리스크
- 저장은 **현재 브라우저 localStorage 단일 저장소** 기준이다. 브라우저를 바꾸거나 캐시/사이트 데이터 삭제 시 사라질 수 있으므로, 아침 사용 전후로 export 1회 권장.
- import는 파일 선택 UI를 타는 구조라 브라우저 환경별 UX 차이가 있을 수 있다. 다만 JSON import 로직 자체는 roundtrip sanity check 통과.
- canary v1은 의도적으로 작은 범위(호흡기/순환기)만 안정화한 상태다. 다른 과목까지 확장하면 다시 검증이 필요하다.

## 5) 사용자가 아침에 할 시작 순서
1. `kmle-planner/index.html` 열기
2. 혹시 기존 데이터가 중요하면 먼저 `데이터 내보내기`
3. `4월 Canary 세팅` 누르기
4. 바로 열린 오늘 플래너에서 호흡기 블록부터 시작
5. `CANARY_TRACKER_APRIL.md`를 같이 열고, 배국자 전송/막힘 이유를 앱과 트래커 둘 다 갱신

## 6) 수정한 파일 목록
- `kmle-planner/index.html`
- `kmle-planner/README.md`
- `kmle-planner/TODAY_START_GUIDE.md`
- `kmle-planner/CANARY_V1_VERIFICATION.md`

## 7) 짧은 전달용 요약
- canary v1 아침 스타트 동선은 이제 `4월 Canary 세팅 → 오늘 플래너 진입`으로 바로 이어진다.
- `오늘 학습 시작`도 canary 미세팅 상태면 먼저 세팅을 제안하도록 바꿨다.
- 배국자 전송 체크, 막힘 이유, 진행도 수정, localStorage persistence, export/import sanity는 실제로 검증했다.
- 서버가 한 번 죽는 상황도 재현됐고, 재기동 후 다시 끝까지 검증했다.
