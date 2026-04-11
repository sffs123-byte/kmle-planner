# Supabase 자동 동기화 설정

국시 플래너는 GitHub Pages 같은 정적 호스팅에서도 동작하도록 만들었기 때문에,
**기기 간 자동 동기화는 Supabase를 백엔드로 붙이는 방식**으로 설계했습니다.

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

이 테이블은 로그인한 사용자 자신의 planner state만 읽고/쓰게 되어 있습니다.

## 3. Email 로그인 켜기
Supabase에서:
- **Authentication → Providers → Email**
- Email provider 활성화

기본 magic link 로그인만 써도 충분합니다.

## 4. URL / Redirect 설정
Supabase에서:
- **Authentication → URL Configuration**

여기에 다음을 추가합니다.

### Site URL
GitHub Pages 배포 주소
예:
- `https://<github-username>.github.io/<repo-name>/`

### Redirect URLs
적어도 아래 둘 중 쓰는 주소를 추가:
- `https://<github-username>.github.io/<repo-name>/`
- `http://127.0.0.1:8766/`
- `http://127.0.0.1:8765/`

## 5. anon key 복사
Supabase에서:
- **Project Settings → API**
- `Project URL`
- `anon public key`
를 복사

## 6. 플래너 앱에서 연결
앱 상단의 **자동 동기화** 버튼 클릭 후:
- Supabase URL 입력
- anon key 입력
- 같은 이메일 입력
- **설정 저장**
- **이메일 로그인 링크 보내기**

맥과 태블릿 둘 다 **같은 이메일로 로그인**하면 자동 동기화됩니다.

## 7. 동작 방식
- 플래너는 기본적으로 localStorage에 저장됨
- 자동 동기화가 켜지면 변경 시 원격 업로드
- 다른 기기에서 로그인하면 원격 상태를 받아옴
- 현재는 **last-write-wins** 방식

## 주의
- 동기화는 같은 이메일 계정 기준
- GitHub Pages 자체에는 데이터가 저장되지 않음
- 민감한 비밀번호는 앱에 넣지 않음
- anon key는 공개 키라 클라이언트에 넣어도 됨

## 권장 사용 순서
1. GitHub Pages 배포
2. Supabase 설정
3. 맥에서 로그인
4. 태블릿에서 같은 이메일로 로그인
5. 실제로 일정 하나 수정해서 반영 확인
