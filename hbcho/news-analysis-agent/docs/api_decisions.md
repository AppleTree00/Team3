# API 선택 기준

## 기본값: 자동 안정 모드

정적 GitHub Pages에서 실제 데이터를 보여주는 것이 목적이므로, 한 API에 실패하면 다른 공개 API를 순차적으로 시도합니다.

1. **GDELT DOC API**
   - 글로벌 뉴스 기사 목록 검색
   - API Key 불필요
   - JSON/JSONP 사용 가능
   - 일부 로컬 환경에서 네트워크/CORS/보안 프로그램 영향 가능

2. **Hacker News Algolia API**
   - API Key 불필요
   - 기술/AI 관련 최신 링크 확인에 적합
   - 언론사 API는 아니지만 프론트엔드 정적 페이지에서 실제 데이터 확인용 fallback으로 안정적

3. **Spaceflight News API**
   - API Key 불필요
   - 공개 CORS 테스트와 실제 기사 카드 표시용 fallback
   - 주제 범위가 우주/항공 분야로 제한됨

4. **The Guardian Open Platform**
   - 언론사 제공 API
   - API Key 필요
   - Key는 코드에 저장하지 않고 브라우저 화면에서 직접 입력

## 제외한 API

| API | 처리 | 이유 |
|---|---|---|
| NewsAPI | GitHub Pages 기본 화면에서 제외 | 공개 정적 웹 배포와 브라우저 CORS 제약 가능성이 큼 |
| NYTimes API | 제외 | API Key 필요, 공개 저장소에 키를 포함할 수 없음 |
| RSS 직접 호출 | 제외 | 대부분 CORS 제한으로 브라우저 직접 호출이 불안정 |
