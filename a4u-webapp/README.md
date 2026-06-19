# **프로젝트 README.md: 이력서 AI 코칭 시스템 (MVP 시연용)**

## **1\. 프로젝트 개요**

본 프로젝트는 3일 내 구현 가능한 이력서 AI 코칭 및 지원 관리 시스템의 MVP(Minimum Viable Product)입니다. 시연을 위해 2\~3종의 이력서 샘플과 2종의 템플릿에 집중하며, 범위 외 기능은 안내 메시지로 대체합니다.

## **2\. 핵심 기능 정의**

* **로그인:** 구글 인증.  
* **이력서 관리:** 직접 작성 및 파일 업로드(PDF, WORD). 형식 오류 시 "업데이트 예정" 메시지 출력.  
* **AI 코칭:** 샘플 2\~3종 기반의 프롬프트 코칭 및 에디트.  
* **지원 관리:** 제출처 템플릿(2종) 기반 미리보기 및 출력.

## **3\. 시연 제약사항 및 예외 처리**

3일 내 구현 불가 항목은 **"현재 이 기능은 고도화 단계에 있습니다. 업데이트 이후 사용 가능하니 잠시만 기다려주세요."**라는 메시지를 호출하여 대응합니다.

## **4\. 기술 스택**

* **Frontend:** HTML/CSS/JS (Tailwind CSS, 샘플 기반 고정 레이아웃)  
* **Backend:** Flask (API 라우팅, DB 제어)  
* **Database:** SQLite (샘플 기반 고정 스키마 및 JSONB 활용)

## **5\. 협업 규칙**

모든 팀원은 PROJECT\_MASTER.md를 기준으로 단위 업무를 업데이트하며, 변경적용 시 PM의 컨펌을 받습니다.

## **6. 로컬 개발 환경 설정 및 실행**

### **6.1. 사전 준비**
*   Python 3.8 이상
*   pip (Python 패키지 관리자)

### **6.2. 설치 및 실행**

1.  **가상 환경 생성 및 활성화:**
    프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 가상 환경을 설정합니다.
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **의존성 패키지 설치:**
    ```bash
    pip install Flask Flask-SQLAlchemy Flask-Cors
    ```

3.  **애플리케이션 실행:**
    다음 명령어를 실행하면 `a4u.db` 데이터베이스가 초기화되고 웹 서버가 시작됩니다.
    ```bash
    python run.py
    ```

4.  **접속 정보:**
    *   **메인 페이지:** `http://localhost:5000`
    *   **관리자 페이지:** `http://localhost:5000/admin`
    *   **관리자 초기 비밀번호:** `admin1234` (`ADMIN_PASSWORD` 환경 변수로 변경 가능)