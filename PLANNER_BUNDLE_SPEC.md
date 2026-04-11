# Planner Bundle Spec

`planner_bundle`은 실습 JSON/packet을 앱이 직접 소비할 수 있도록 만든 **execution-layer 표준**이다.

핵심 원칙:
- `raw archive`는 보존/추적용
- `planner packet`은 전공의/비서가 보는 실행용 입력
- `planner bundle`은 앱이 직접 import/merge하는 최종 데이터

---

## 최상위 구조
```json
{
  "meta": {},
  "global_rules": {},
  "fixed_info": {},
  "submission_rules": [],
  "sessions": [],
  "assignments": [],
  "daily_briefing_seed": [],
  "day_reminders": [],
  "outpatient_professors": [],
  "analysis_appendix": {},
  "audit": {}
}
```

---

## 1. meta
번들의 정체성과 생성 정보를 담는다.

필수 필드:
- `clerkship_id`
- `subject`
- `track`
- `generated_at`

권장 필드:
- `packet_source`
- `config_source`
- `rubric_source`

---

## 2. sessions[]
실습 세션/수업/평가/운영 이벤트의 기본 단위.
앱 캘린더의 주요 이벤트 소스가 된다.

### 필수 필드
- `id`
- `date`
- `time_label`
- `title`
- `event_type`
- `difficulty`

### 권장 필드
- `week`
- `day`
- `start_time`
- `end_time`
- `professor`
- `professor_score`
- `summary`
- `focus_points`
- `prepare_points`
- `research_notes`
- `status`
- `kind`
- `start_when`
- `follow_up`
- `needs_confirmation`
- `note`

---

## 3. assignments[]
과제/발표/서류 제출/준비물을 실행 큐로 변환한 단위.
앱에서는 calendar event + task seed로 파생한다.

### 필수 필드
- `id`
- `name`
- `difficulty_total`

### 권장 필드
- `priority_label`
- `priority_score`
- `format`
- `raw_deadline`
- `start_at`
- `soft_deadline`
- `hard_deadline`
- `followup_deadline`
- `needs_confirmation`
- `difficulty_content`
- `difficulty_operational`
- `linked_session_ids`
- `linked_professors`
- `milestones`
- `notes`

---

## 4. daily_briefing_seed[]
아침 브리핑용으로 하루를 얇게 뽑은 구조.

필드 예시:
- `date`
- `headline`
- `day_digest`
- `sessions[]`
- `assignment_start_today[]`
- `assignment_due_today[]`
- `max_professor_score`
- `max_session_difficulty`

---

## 5. day_reminders[]
실습일 당일 준비물/주의점 리마인드용 구조.

필드 예시:
- `date`
- `sessions[]`
- `prepare[]`
- `watchouts[]`

---

## 6. audit
import 과정에서 제거/보류/경고된 항목을 남긴다.

필드 예시:
- `excluded_sessions`
- `unconfigured_assignments`
- `warnings`

---

## 앱 적용 원칙
앱은 bundle을 직접 import하면 다음을 수행한다.
1. `clerkshipBundles[clerkship_id]`에 bundle 저장
2. `sessions`를 캘린더 이벤트로 변환
3. `assignments.start_at / hard_deadline / milestones`를 이벤트/태스크로 변환
4. subject note/recentHistory에 bundle 적용 이력 남김

즉 앱은 `state` JSON뿐 아니라 `planner_bundle`도 직접 먹을 수 있어야 한다.

---

## 현재 기준 예시 파일
- `data/clerkships/bundles/respiratory_content_handoff_v2.bundle.json`

이 파일을 1차 레퍼런스 bundle로 본다.
