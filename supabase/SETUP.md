# Supabase 자동 동기화 설정 (sync code 방식)

국시 플래너는 GitHub Pages 같은 정적 호스팅에서도 동작하도록 만들었기 때문에,
**기기 간 자동 동기화는 Supabase + 개인용 sync code 방식**으로 설계했습니다.

## 핵심 개념
- GitHub Pages = 앱 배포
- Supabase = state 저장소
- 로그인/이메일 인증 없음
- 대신 **맥과 iPad가 같은 sync code를 공유**해서 같은 planner state를 읽고 씁니다.

## 1. Supabase 프로젝트 생성
1. https://supabase.com 로그인
2. **New project**
3. 원하는 프로젝트 이름 생성
4. 비밀번호/리전 선택

## 2. SQL 실행
Supabase 대시보드에서:
- **SQL Editor** 열기
- `supabase/schema.sql` 내용 전체 붙여넣기
- 실행

이 SQL은 `planner_sync_slots` 테이블과
- `planner_sync_pull`
- `planner_sync_push`
RPC 함수를 만듭니다.

## 3. URL / API key 확인
Supabase에서:
- **Project Settings → API Keys**
- `Project URL`
- `public / publishable key`
확인

> 현재 기본 배포본에는 이 프로젝트 값이 이미 들어가 있으므로,
> 보통은 사용자가 직접 다시 입력할 필요가 없습니다.

## 4. 플래너 앱에서 연결
### 맥에서
1. 상단 **자동 동기화** 버튼
2. **새 동기화 코드 생성**
3. **지금 밀어넣기**
4. 코드를 복사

### iPad에서
1. 같은 앱 열기
2. **자동 동기화** 버튼
3. 맥에서 생성한 **같은 동기화 코드 입력**
4. **설정 저장**
5. **지금 다시 받기**

## 5. 동작 방식
- 플래너는 기본적으로 localStorage에 저장됨
- sync code가 연결되면 상태를 Supabase에 저장/불러옴
- 현재 충돌 해결은 **last-write-wins**

## 추천 운영
- **맥 = primary writer(정본)**
- **iPad = 보기 + 간단 수정**
- 처음 1주일은 두 기기에서 동시에 많이 수정하지 않기

## 주의
- sync code를 아는 기기는 같은 상태에 접근할 수 있음
- 따라서 code는 개인용으로만 관리
- sync는 편의 기능이지 백업 대체가 아님
- 주기적으로 **데이터 내보내기** 백업 권장

---

## DB-first 전환 준비 (2026-04-11 추가)

현재 운영 원칙은 다음과 같습니다.
- **앱 셸(HTML / sync / service worker)은 freeze**
- **공용 콘텐츠는 live bundle JSON 교체로 운영**
- **개인 상태만 Supabase DB로 이동**

이번 단계에서 schema.sql에는 아래 RPC가 추가되었습니다.
- `planner_user_state_pull(p_user_id text)`
- `planner_user_state_push(p_user_id text, p_state_json jsonb, ...)`

의도:
- `planner_sync_slots` = 기존 전체 state sync 실험용 / 레거시 호환
- `planner_user_state` = 앞으로의 **single-user, multi-device 정본 상태 저장소**

권장 user_id:
- 당분간은 단순하게 하나의 고정 값 사용
- 예: `gangryeol-main`

권장 운영 구조:
1. **공용 구조/일정/설명** → GitHub Pages의 live bundle JSON
2. **개인 진행도/체크/메모** → Supabase `planner_user_state`

즉 앞으로 맥/핸드폰 동기화의 핵심은
- bundle은 서버 정적 파일에서 공통으로 읽고
- 네가 체크한 값은 `planner_user_state`에서 읽고 쓰는 방향입니다.
