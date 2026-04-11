# Clerkship JSON Import System

호흡기내과처럼 **실습 인계/일정/과제/교수님 정보가 정리된 JSON**을 반복적으로 받을 때,
매번 HTML을 직접 수정하지 않고도 플래너에 반영하기 위한 ingest 시스템이다.

---

## 왜 이 시스템이 필요한가
실습 JSON에는 단순 시간표만 있는 게 아니라 아래가 같이 들어온다.
- 트랙(A/B)
- 과제 목록과 마감
- 요일별 세션
- raw note / curated 요약
- 사용자 override
- 교수님 정보

이걸 수동으로 앱에 붙이면
- 누락
- 중복
- override 충돌
- 과거 버전 덮어쓰기
가 반복된다.

그래서 구조를 다음 5단계로 나눈다.

---

## 5단계 ingest 구조
### 1. raw intake
원본 JSON 그대로 보존.
- 경로: `data/clerkships/raw/<과목>/...json`

### 2. normalize
플래너 공통 스키마로 변환.
- 일정 → session
- 과제 → assignment
- override → planner-friendly field

### 3. enrich
플래너가 실제로 써먹을 필드 계산.
- `start_at`
- `soft_deadline`
- `hard_deadline`
- `difficulty_content`
- `difficulty_operational`
- 교수님 기반 difficulty
- daily windows

### 4. audit
자동 점검.
- 제외된 세션
- 미설정 과제
- 일정/마감 충돌

### 5. promote
검증 통과한 번들을 플래너 import용 state로 승격.
- `data/clerkships/bundles/...bundle.json`
- `data/planner_state_..._import.json`

---

## 현재 호흡기내과 B트랙 적용 파일
### raw archive 경로
- `data/clerkships/raw/respiratory/2026-04-11_v15.json`

### primary content source (설명층 기준)
- `data/clerkships/packets/respiratory/2026-04-11_content_handoff_v2.json`
- `data/clerkships/packets/respiratory/2026-04-11_content_handoff_v2.md`

### execution packet 경로 (보조 필드용)
- `data/clerkships/packets/respiratory/2026-04-11_planner_packet_v1.json`
- 구형 과도기 packet: `data/clerkships/packets/respiratory/2026-04-11_handoff_v1.json`

### config
- `data/clerkships/config/respiratory_2026-04-13_B.json`

### rubric
- `data/clerkships/rubrics/respiratory_professors.json`

### outputs
- raw 기반 bundle: `data/clerkships/bundles/respiratory_2026-04-13_B.bundle.json`
- content 기반 bundle(권장): `data/clerkships/bundles/respiratory_content_handoff_v2.bundle.json`
- content 기반 briefing: `data/clerkships/briefings/respiratory_content_handoff_v2.daily_briefing.json`
- content 기반 reminders: `data/clerkships/reminders/respiratory_content_handoff_v2.day_reminders.json`
- content 기반 planner import: `data/planner_state_respiratory_content_handoff_v2_import.json`
- audit: `data/clerkships/audit/respiratory_content_handoff_v2.audit.json`

---

## 교수님 난이도 원칙
교수님 점수는 1~10점으로 두고,
단순 호감도나 외래 추천도가 아니라 **플래너 운영 중요도/난이도** 기준으로 평가한다.

### 5개 축
- `stakes`: 점수/통과 영향
- `questioning`: 질문/브리핑/방어 강도
- `volatility`: 일정 변동/확인 필요
- `case_fit_risk`: 환자/케이스 선택 리스크
- `prep_load`: 사전 준비/후처리 부담

사용자 override는 최우선으로 반영한다.
예:
- 정성수 10
- 이정은 8
- 정재욱 7
- 김소윤 7

---

## import 실행 방법
### raw archive 기반
```bash
python3 scripts/build_clerkship_bundle.py \
  --raw data/clerkships/raw/respiratory/2026-04-11_v15.json \
  --config data/clerkships/config/respiratory_2026-04-13_B.json \
  --rubric data/clerkships/rubrics/respiratory_professors.json \
  --base-state data/canary_import_seed.json \
  --bundle-out data/clerkships/bundles/respiratory_2026-04-13_B.bundle.json \
  --planner-out data/planner_state_respiratory_B_import.json \
  --audit-out data/clerkships/audit/respiratory_2026-04-13_B.audit.json
```

### content + execution packet 기반 (권장)
```bash
python3 scripts/build_clerkship_content_bundle.py \
  --content data/clerkships/packets/respiratory/2026-04-11_content_handoff_v2.json \
  --packet data/clerkships/packets/respiratory/2026-04-11_planner_packet_v1.json \
  --config data/clerkships/config/respiratory_2026-04-13_B.json \
  --rubric data/clerkships/rubrics/respiratory_professors.json \
  --base-state data/canary_import_seed.json \
  --bundle-out data/clerkships/bundles/respiratory_content_handoff_v2.bundle.json \
  --briefing-out data/clerkships/briefings/respiratory_content_handoff_v2.daily_briefing.json \
  --reminders-out data/clerkships/reminders/respiratory_content_handoff_v2.day_reminders.json \
  --planner-out data/planner_state_respiratory_content_handoff_v2_import.json \
  --audit-out data/clerkships/audit/respiratory_content_handoff_v2.audit.json
```

---

## 앞으로 다른 과/새 버전이 올 때
### 새 JSON이 오면
1. raw 폴더에 원본 저장
2. 과목별 config 복사해서 날짜/트랙/과제 override 수정
3. 교수님 rubric 작성/보강
4. script 실행
5. audit 확인
6. planner import json 생성

### 원칙
- 원본 JSON은 건드리지 않는다.
- 사용자 직접 정리본은 최대한 보존한다.
- override는 config/rubric에 누적한다.
- UI를 먼저 고치지 말고, data layer를 먼저 잠근다.

---

## 현재 판단
이 시스템은 강의 제작 하네스처럼 큰 구조가 아니라,
**실습 운영 데이터를 플래너에 넣기 위한 ingest/promotion 하네스**라고 보면 된다.

즉:
- raw = reference
- bundle = normalized source of truth
- planner import = 실행판

현재 앱은 `state backup JSON`뿐 아니라 `planner bundle JSON`도 직접 import/merge할 수 있다. 즉 장기적으로는 `planner import state`보다 `bundle`이 1차 산출물이 된다.
