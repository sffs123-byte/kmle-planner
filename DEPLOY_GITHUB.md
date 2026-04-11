# GitHub 배포 체크리스트

이 폴더는 이미 GitHub Pages + PWA 배포 준비가 끝난 상태입니다.

## 현재 준비된 것
- `manifest.webmanifest`
- `service-worker.js`
- 홈 화면 설치용 아이콘 (`assets/icons/`)
- GitHub Pages 워크플로우 (`.github/workflows/deploy-pages.yml`)
- 별도 git repo 초기화 완료 (`main` 브랜치)

## GitHub에 올리는 순서
### 1) 새 GitHub repo 만들기
예시 이름:
- `kmle-planner`
- `kuksi-planner`
- `study-codex-planner`

### 2) 로컬 repo에 remote 연결
```bash
cd ~/.openclaw/workspace/kmle-planner
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

### 3) GitHub Pages 켜기
GitHub repo에서:
- **Settings → Pages**
- Source: **GitHub Actions**

### 4) 배포 완료 후 태블릿에 설치
#### iPad / iPhone
- Safari로 배포 주소 열기
- 공유 버튼
- **홈 화면에 추가**

#### Android
- Chrome으로 배포 주소 열기
- **앱 설치** 또는 **홈 화면에 추가**

## 자동 동기화까지 같이 쓰려면
이제 `sync.js` + `supabase/` 설정이 추가되어 있어서,
GitHub Pages 배포 후 **Supabase + sync code 방식**으로 맥 ↔ 태블릿 자동 동기화가 가능합니다.

설정 문서:
- `supabase/SETUP.md`
- `supabase/schema.sql`

앱에서:
- 맥: 상단 **자동 동기화** → **새 동기화 코드 생성** → **지금 밀어넣기**
- iPad: 같은 코드 입력 → **설정 저장** → **지금 다시 받기**

## 중요한 점
- 동기화 백엔드는 GitHub Pages가 아니라 **Supabase**입니다.
- GitHub Pages는 앱 배포만 담당합니다.
- 현재 충돌 해결은 **last-write-wins** 방식입니다.
- 초기에는 **맥을 정본(primary writer)** 으로 두는 것이 안전합니다.
- 동기화가 켜져도 주기적인 **데이터 내보내기** 백업은 권장합니다.

## 추천 운영
- 1차: GitHub Pages로 배포해서 태블릿에 앱처럼 설치
- 2차: Supabase 연결 후 sync code 생성/연결
- 3차: 실제 사용하면서 UX 수정
