# 개인 일정 관리 AI 에이전트 Demo

GitHub Pages에서 바로 열 수 있는 HTML 기반 개인 일정 관리 AI 에이전트입니다.

## 실행 방법

### 1) GitHub Pages 배포

1. 압축을 해제합니다.
2. `index.html`, `assets/`, `backend/`, `README.md`를 GitHub 저장소 루트에 업로드합니다.
3. GitHub 저장소의 **Settings → Pages**에서 배포 브랜치를 선택합니다.
4. 배포 URL에서 `index.html` 화면을 확인합니다.

GitHub Pages에서는 브라우저 `LocalStorage`에 일정이 저장됩니다.

### 2) 로컬에서 바로 실행

압축 해제 후 `index.html`을 브라우저로 열면 됩니다.

### 3) Python + SQLite 선택 실행

Python/SQLite 실습용 로컬 서버를 포함했습니다. 이 방식은 GitHub Pages가 아니라 로컬 개발용입니다.

```bash
cd personal_assistant_agent
python backend/server.py
```

브라우저에서 아래 주소를 엽니다.

```text
http://localhost:8000
```

SQLite DB는 프로젝트 루트의 `assistant.db`로 생성됩니다.

## 구현 기능

| 항목 | 처리 | 설명 |
|---|---|---|
| 일정 등록 | 구현 | 자연어 명령 및 직접 입력 |
| 일정 조회 | 구현 | 전체/오늘/내일/7일/높은 우선순위/검색 필터 |
| 일정 변경 | 구현 | 목록 편집 버튼 및 간단한 자연어 변경 명령 |
| 중요한 일정 알림 | 부분 구현 | 페이지가 열려 있을 때 브라우저 알림 |
| 우선순위 추천 | 구현 | 중요도, 긴급도, 키워드, 충돌 기반 점수화 |
| Python | 선택 포함 | `backend/server.py` |
| SQLite | 선택 포함 | 로컬 서버 실행 시 `assistant.db` 사용 |
| Google Calendar API | 제외 | OAuth, 권한, 배포 도메인 설정 필요로 오류 위험 큼 |
| Gemini/OpenAI API | 제외 | API Key, 과금, 브라우저 노출, CORS 보안 이슈 방지 |

## 예시 명령

- `다음 주 화요일 오후 2시에 회의 등록해줘`
- `내일 오전 10시에 병원 예약 등록해줘`
- `오늘 일정 조회해줘`
- `회의 시간을 오후 3시로 변경해줘`
- `중요한 일정 추천해줘`

## 설계 의도

- API Key 없이 GitHub Pages에서 즉시 실행되도록 외부 API 의존성을 제거했습니다.
- 사용자가 실습 과제 발표나 데모에서 바로 보여줄 수 있도록 단일 화면 SPA 형태로 구성했습니다.
- 실제 Google Calendar/Gemini/OpenAI 연동은 서버와 OAuth 인증이 필요하므로 안정적인 데모 범위에서 제외했습니다.

## 파일 구조

```text
personal_assistant_agent/
├── index.html
├── assets/
│   ├── app.js
│   └── style.css
├── backend/
│   └── server.py
└── README.md
```
