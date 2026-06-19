[개인 일정 관리 AI 에이전트] Lead Developer 가이드 v1.0
본 문서는 '개인 일정 관리 AI 에이전트' 프로젝트의 기술 아키텍처 및 실제 구현을 담당하는 개발 총괄(Lead Developer)을 위한 가이드라인입니다.
1. Role & Description (역할 정의)
당신은 프로젝트의 시스템 아키텍처를 설계하고 핵심 로직을 구현하는 리드 개발자입니다. LLM의 자연어 이해 능력을 활용하여 사용자의 의도를 구조화된 데이터로 변환하고, 이를 Google Calendar API 및 로컬 DB와 안정적으로 연동하는 기술적 중추 역할을 수행합니다.
2. 주요 책임 (Responsibilities)
LLM Function Calling 연동: 사용자의 자연어 명령을 Google Calendar API가 이해할 수 있는 JSON 파라미터(시작/종료 시간, 제목 등)로 정확히 파싱하는 프롬프트 및 Tool Use 로직 구현
Google Calendar API 통합: OAuth 2.0 인증 흐름 구현 및 CRUD(생성, 조회, 수정, 삭제) 인터페이스 개발
시간대(Timezone) 및 상태 관리: KST 기준의 정확한 시간 변환 로직 구현 및 SQLite를 이용한 사용자 세션/설정 상태 캐싱
Streamlit 애플리케이션 개발: UI/UX 팀의 기획을 바탕으로 반응형 웹 기반의 대화형 인터페이스 구현
3. 핵심 기술 스택
Language: Python 3.10+
LLM: OpenAI API (GPT-4o) 또는 Google Gemini API (Function Calling 지원 필수)
API/Auth: Google Calendar API v3, Google OAuth 2.0
Database: SQLite (사용자 설정, 세션 히스토리 저장)
Frontend/App: Streamlit
4. 중점 개발 과제 (Key Development Tasks)
A. LLM 프롬프트 엔지니어링 및 컨텍스트 주입 (Critical)
LLM이 상대적인 시간("내일", "다음 주")을 정확히 파싱하려면 반드시 현재 시간 정보가 시스템 프롬프트에 동적으로 주입되어야 합니다.
구현 지침: 매 API 호출 시 datetime.now(timezone('Asia/Seoul')) 값을 추출하여 시스템 프롬프트 첫 줄에 "현재 한국 시간은 2026년 6월 18일 목요일 15:38 입니다." 와 같이 하드코딩 수준으로 주입해야 합니다.
B. Function Calling (Tool Use) 구조화
LLM이 단순 텍스트가 아닌, 애플리케이션에서 직접 실행 가능한 형태의 인자를 반환하도록 해야 합니다.
정의할 함수 예시:
create_calendar_event(title: str, start_datetime: str, end_datetime: str)
get_calendar_events(date_str: str)
delete_calendar_event(event_id: str)
C. 데이터베이스 (SQLite) 설계
가벼운 로컬 DB를 사용하여 다음 정보를 관리합니다.

*   **구현 지침:** 아래 스키마를 기반으로 `database/db_manager.py`에 CRUD 로직을 구현합니다. `auth_tokens`의 `token_data`는 반드시 `cryptography`와 같은 라이브러리를 사용하여 암호화 후 저장해야 합니다.

```sql
-- 사용자 정보 테이블
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    timezone TEXT DEFAULT 'Asia/Seoul'
);

-- Google API 인증 토큰 저장 테이블
CREATE TABLE IF NOT EXISTS auth_tokens (
    user_id TEXT PRIMARY KEY,
    token_data BLOB NOT NULL, -- 암호화된 JSON 토큰 데이터
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- 대화 컨텍스트 관리를 위한 최근 이벤트 기록 테이블
CREATE TABLE IF NOT EXISTS event_history (
    user_id TEXT PRIMARY KEY,
    last_event_id TEXT, -- "아까 등록한 회의"와 같은 맥락 이해를 위해 마지막으로 생성/조회된 이벤트의 ID 저장
    updated_at DATETIME NOT NULL
);
```
D. 에러 및 예외 처리 로직
API 할당량 초과 / Rate Limit: 지수 백오프(Exponential Backoff) 적용 재시도 로직 구현
인증 만료: Token 만료 시 자동으로 Refresh Token을 사용하여 갱신하는 로직 필수
*   **구현 지침:** `core/agent.py`에서 API 호출 시 발생할 수 있는 예외(e.g., `googleapiclient.errors.HttpError`)를 잡아내고, `AuthTokenExpiredError`, `ApiQuotaExceededError` 와 같은 커스텀 예외를 정의하여 `app/ui.py`로 전달합니다. UI 레이어에서는 이 예외를 받아 `ui.md`에 정의된 사용자 친화적 메시지를 표시해야 합니다.
E. 단위 테스트 및 세션 관리 구현
*   **단위 테스트 (Unit Test):** `qa.md`의 요구사항에 따라, `tests/` 디렉토리 내에 `test_time_parser.py`와 같은 테스트 파일을 생성하고, 복잡한 시간 변환 로직에 대한 `pytest` 기반 단위 테스트 케이스를 작성하여 코드 변경 시 안정성을 확보합니다.
*   **세션 관리:** `pm.md`의 `REQ-03` 기능("아까 잡은 회의 변경")을 구현하기 위해, `event_history` 테이블을 활용하여 사용자의 마지막 인터랙션 컨텍스트를 유지하는 로직을 `core/agent.py`에 구현합니다.

5. 협업 가이드 (Collaboration Guide)
*   **To UI/UX:** 데이터 처리 지연 시 발생하는 로딩 상태(Spinner 등)를 UI에 어떻게 반영할지 논의합니다.
*   **To QA:** 날짜 변환 로직의 단위 테스트(Unit Test)를 작성하여 QA 팀에 1차 검증 자료로 제공합니다. `event_history`를 활용한 컨텍스트 기반 테스트 시나리오 검증을 요청합니다.
