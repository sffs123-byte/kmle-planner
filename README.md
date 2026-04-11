# 국시 준비 일정 관리 플래너

로컬에서 바로 열어서 쓰는 정적 웹앱입니다.

## 파일
- `index.html` — 메인 앱

## 핵심 기능
- 과목별 5단계 진행도 관리
  - 강의 듣기
  - 개념 틀 짜기
  - 문제 풀기
  - 오답노트/개념틀 수정
  - 복습하기
- 과목별 학습량(`완료량 / 목표량`) 입력
- 오늘 일정 / 이번 주 일정 / 밀린 일정 확인
- 복습 단계 우선 추적
- 취약 파트 / 다음 액션 / 과목 메모 저장
- localStorage 저장
- JSON 백업 내보내기 / 가져오기

## 실행 방법
### 가장 간단한 방법
브라우저에서 `index.html`을 직접 열기

### 권장 방법 (로컬 서버)
```bash
cd ~/.openclaw/workspace/kmle-planner
python3 -m http.server 8765
```
그다음 브라우저에서:
- `http://127.0.0.1:8765`

## 데이터 저장 방식
- 기본 저장 위치: 브라우저 localStorage
- 백업이 필요하면 앱 상단의 **데이터 내보내기** 사용
- 다른 브라우저/다른 기기로 옮길 때는 **데이터 가져오기** 사용

## 실사용 팁
- 처음엔 **4월 canary 초기 상태**로 시작한다. 진행률은 전부 0으로 초기화되어 있고, 호흡기/순환기 파트 기준으로 관리한다.
- 자기 일정으로 바꾸려면:
  1. 과목 진행도 수정
  2. 일정 추가
  3. 필요하면 canary 일정을 수정 또는 삭제
- 실제 운용 중에는 주 1회 정도 JSON 백업 권장

## 🐥 4월 Canary 운영 가이드 (호흡기/심장)
4월은 시스템이 실제로 워킹하는지 확인하는 **Canary 기간**입니다.

### 1. 전용 파일 활용
- 앱 상단 **`4월 Canary 세팅` 버튼**: 호흡기/순환기 canary 상태와 주말 일정 샘플을 앱에 바로 불러오고, 곧바로 **오늘 플래너(호흡기 / today / pending)** 로 이동합니다.
- `CANARY_TRACKER_APRIL.md`: 파트별 루프(배국자 전송 여부)를 수동 체크하는 관측판입니다.
- `CARDIOLOGY_CHIEF_PREP.md`: 일요일 심장내과 조장 준비 전용 체크리스트입니다.
- `TODAY_START_GUIDE.md`: 오늘(토) 시작 순서와 배국자 전송 예시를 모아둔 빠른 시작 가이드입니다.
- `data/canary_import_seed.json`: 호흡기/순환기 기본 데이터가 세팅된 시드 파일입니다. (수동 import용 백업)

### 2. 핵심 운영 규칙
- **2단계 완료** = 배국자에게 **개념틀** 전송 완료 시
- **4단계 완료** = 배국자에게 **함정/출제개념** 전송 완료 시
- **문제풀이 total**은 강렬이 준 알렌 문항 수 데이터(y)를 기준으로 자동 반영한다.
- 강의/개념틀/오답정리/복습은 **파트 수 기준**, 문풀은 **실제 문항 수 기준**으로 계산한다.
- 앱의 과목 상세에서 **배국자 개념 전송 / 함정 전송 체크박스**와 **막힘 이유**를 직접 기록할 수 있습니다.
- **`오늘 학습 시작` 버튼**은 canary 세팅이 아직 아니면 먼저 canary 세팅을 제안한 뒤, 오늘 플래너로 바로 이동합니다.
- 루프가 막히면 트래커나 앱에 **막힘 이유**를 반드시 남깁니다.

### 3. 이번 주말 기본 흐름
- **오늘(토)**: 호흡기 강의 몰입 + 밤에 배국자 1차 전송
- **내일(일)**: 심장내과 인계 분석 + 조장 준비

## GitHub Pages로 배포해서 태블릿 앱처럼 쓰기
이 폴더는 **정적 사이트 + PWA** 형태로 배포 가능하게 준비되어 있습니다.

## 자동 동기화 (맥 ↔ 태블릿)
이제 플래너는 **Supabase 기반 자동 동기화**도 지원합니다.

### 구성 파일
- `sync.js`
- `supabase/schema.sql`
- `supabase/SETUP.md`

### 핵심 방식
- 플래너 데이터는 기본적으로 localStorage에 저장
- 같은 이메일로 맥과 태블릿에서 로그인하면
- Supabase에 planner state를 저장하고 서로 받아와 자동 동기화

### 빠른 시작
1. GitHub Pages로 배포
2. `supabase/SETUP.md` 보고 Supabase 프로젝트 생성
3. 앱 상단 **자동 동기화** 버튼에서
   - Supabase URL
   - anon key
   - 동기화용 이메일
   입력
4. 맥/태블릿 둘 다 같은 이메일로 로그인

### 동기화 방식
- 현재는 **last-write-wins**
- 즉 마지막으로 저장한 기기의 상태가 최신본이 됨

### 포함된 배포 파일
- `manifest.webmanifest`
- `service-worker.js`
- `assets/icons/`
- `.github/workflows/deploy-pages.yml`
- `.nojekyll`

### 추천 배포 방식
이 `kmle-planner/` 폴더를 **별도 GitHub repo** 로 올리고, GitHub Pages를 켭니다.

### 가장 쉬운 순서
```bash
cd ~/.openclaw/workspace/kmle-planner
git init
git add .
git commit -m "Initial KMLE planner"
# GitHub repo 만든 뒤
# git branch -M main
# git remote add origin <repo-url>
# git push -u origin main
```

그다음 GitHub에서:
- **Settings → Pages**
- Source: **GitHub Actions**

푸시가 되면 자동으로 배포됩니다.

### 태블릿에서 앱처럼 설치
#### iPad / iPhone (Safari)
1. 배포된 URL 열기
2. 공유 버튼
3. **홈 화면에 추가**

#### Android (Chrome)
1. 배포된 URL 열기
2. 메뉴
3. **앱 설치** 또는 **홈 화면에 추가**

### 주의
- localStorage 기반이라 브라우저/기기별 데이터는 따로 저장됩니다.
- 주기적으로 **데이터 내보내기** 해서 백업하는 것을 권장합니다.
- 앱처럼 설치해도 내부 데이터는 GitHub에 자동 저장되지 않습니다.

## 다음 확장 아이디어
- 반복 복습 자동 생성
- 오늘 완료량 기준 자동 추천
- 과목별 시험일/우선순위 반영
- Obsidian 일정/노트와 동기화
- GitHub 연동 외에 Supabase/파일 동기화 추가
