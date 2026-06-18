# 뉴스 요약 및 분석 에이전트 — GitHub Pages Live v3

브라우저에서 바로 실행되는 정적 HTML/CSS/JS 뉴스 요약 및 분석 에이전트입니다. GitHub Pages에 업로드하면 팀원들이 웹 URL로 실제 뉴스 API 연동 화면을 볼 수 있습니다.

## 핵심 변경 사항 v3

- 이전 Preview 디자인 톤 유지
- `index.html`에서 실제 뉴스 데이터 출력
- 기본 데이터 소스: **자동 안정 모드**
  1. GDELT DOC API
  2. Hacker News Algolia API
  3. Spaceflight News API
- GDELT `fetch()` 실패 시 JSONP 재시도
- 모든 공개 API가 실패해도 오류 화면으로 멈추지 않고 샘플 fallback 표시
- Guardian API Key는 선택 입력이며, 저장소에 포함하지 않음

## 실행 방법

### 로컬 검토

압축 해제 후 `index.html` 또는 `standalone-preview.html`을 더블클릭합니다.

일부 브라우저/보안 프로그램은 `file://` 환경의 외부 API 호출을 제한할 수 있습니다. 이 경우 아래 명령으로 로컬 서버를 실행하세요.

```bash
python -m http.server 8000
```

그 다음 브라우저에서 `http://localhost:8000`으로 접속합니다.

### GitHub Pages 배포

1. GitHub Desktop에서 이 폴더를 새 Repository로 추가
2. Commit
3. Publish repository
4. GitHub 웹 → Settings → Pages
5. Source: Deploy from a branch
6. Branch: main, Folder: /root
7. 발급된 URL을 팀원에게 공유

## 파일 구조

```text
.
├─ index.html
├─ preview.html
├─ standalone-preview.html
├─ assets/
│  ├─ app.js
│  └─ styles.css
├─ docs/
│  ├─ api_decisions.md
│  ├─ excluded_items.md
│  └─ github_pages_deploy.md
├─ .nojekyll
└─ README.md
```

## 주의사항

- GitHub Pages는 정적 호스팅이므로 서버 비밀키를 안전하게 숨길 수 없습니다.
- API Key가 필요한 서비스는 화면 입력 방식만 사용합니다.
- 기본 요약은 기사 전문 크롤링이 아니라 API가 제공하는 제목, 메타데이터, 요약 필드 기반 경량 요약입니다.
