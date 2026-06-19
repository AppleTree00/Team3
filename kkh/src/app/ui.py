import streamlit as st
import os
from datetime import datetime

from ..core.agent import Agent
from ..core.calendar_api import create_calendar_event, exchange_code_for_token, get_authorization_url
from ..core.exceptions import AuthRequiredError, CalendarAPIError
from ..database.db_manager import create_tables, update_event_history

# --- 1. 초기 설정 및 세션 상태 관리 ---

st.set_page_config(page_title="개인 일정 관리 AI 에이전트", page_icon="📅")

# dev.md '4-C'에 따라 DB 테이블을 초기화합니다.
create_tables()

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    # dev.md 'ISSUE-03' 해결을 위해 하드코딩된 ID 대신 세션 기반 ID 사용
    st.session_state.user_id = f"streamlit_user_{os.urandom(8).hex()}"
if "agent" not in st.session_state:
    st.session_state.agent = Agent(user_id=st.session_state.user_id)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "pending_creation" not in st.session_state:
    st.session_state.pending_creation = None
# IMPROVEMENT-01: 과거 일정 확인을 위한 세션 상태 추가
if "pending_past_creation" not in st.session_state:
    st.session_state.pending_past_creation = None


# --- 2. UI 렌더링 ---

st.title("📅 개인 일정 관리 AI 에이전트")
st.caption("자연어 대화로 당신의 구글 캘린더를 관리하세요.")

# ui.md '6.1 사이드바' 디자인 초안
with st.sidebar:
    st.header("사용자 정보")
    st.write(f"👤 사용자 ID: `{st.session_state.user_id}`")
    
    st.header("캘린더 연동 상태")
    if st.session_state.authenticated:
        st.success("✅ 구글 캘린더가 연동되었습니다.")
    else:
        st.warning("🚨 구글 캘린더 연동이 필요합니다.")

# 이전 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 3. 핵심 인터랙션 로직 ---

def handle_agent_response(response):
    """Agent의 응답을 파싱하고 적절한 UI를 렌더링합니다."""
    if isinstance(response, str):
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    elif isinstance(response, dict):
        action = response.get("action")
        
        if action == "request_auth":
            auth_url = response.get("auth_url")
            message = response.get("message", "인증이 필요합니다.")
            st.error(f"{message}\n여기를 클릭하여 구글 계정으로 로그인하세요")
            st.session_state.messages.append({"role": "assistant", "content": f"{message} 인증 링크를 생성했습니다."})

        elif action == "confirm_creation":
            st.session_state.pending_creation = response.get("details")
            st.rerun()

        # IMPROVEMENT-01: 과거 날짜 일정 등록 확인 플로우
        elif action == "confirm_past_creation":
            st.session_state.pending_past_creation = response.get("details")
            st.rerun()

def execute_event_creation(details):
    """세션 상태에 저장된 정보를 바탕으로 실제 캘린더 이벤트를 생성합니다."""
    try:
        result = create_calendar_event(user_id=st.session_state.user_id, **details)
        message = result.get("message", "일정이 등록되었습니다.")
        event_id = result.get("event_id")
        
        if event_id:
            update_event_history(st.session_state.user_id, event_id)

        st.success(message)
        st.session_state.messages.append({"role": "assistant", "content": message})
    except CalendarAPIError as e:
        st.error(f"일정 등록 중 오류가 발생했습니다: {e}")
        st.session_state.messages.append({"role": "assistant", "content": f"오류: {e}"})

# --- 4. UI 컴포넌트 및 이벤트 핸들러 ---

# ui.md 'A. 일정 등록 및 확인 플로우' - 확인 카드 UI
if st.session_state.pending_creation:
    details = st.session_state.pending_creation
    with st.chat_message("assistant"):
        start_dt = datetime.fromisoformat(details['start_datetime'])
        date_str = start_dt.strftime("%Y년 %m월 %d일 (%a)")
        time_str = start_dt.strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")

        st.info("📝 새로운 일정을 등록할까요?")
        st.markdown(f"**제목:** {details['title']}\n\n**날짜:** {date_str}\n\n**시간:** {time_str}")
        
        col1, col2 = st.columns(2)
        if col1.button("확인", key="confirm_create", use_container_width=True):
            execute_event_creation(details)
            st.session_state.pending_creation = None
            st.rerun()
        if col2.button("취소", key="cancel_create", use_container_width=True):
            msg = "알겠습니다. 등록을 취소했습니다."
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.session_state.pending_creation = None
            st.rerun()

# ui.md 'D. 과거 날짜 일정 등록 시 경고' - 확인 카드 UI (IMPROVEMENT-01)
if st.session_state.pending_past_creation:
    details = st.session_state.pending_past_creation
    with st.chat_message("assistant"):
        start_dt = datetime.fromisoformat(details['start_datetime'])
        date_str = start_dt.strftime("%Y년 %m월 %d일 (%a)")

        st.warning("⚠️ 과거 시점의 일정입니다.")
        st.markdown(f"선택하신 날짜는 과거입니다. 기록을 위해 등록하시겠습니까?\n\n"
                    f"**제목:** {details['title']}\n\n"
                    f"**날짜:** {date_str}")
        
        col1, col2 = st.columns(2)
        if col1.button("네, 등록합니다", key="confirm_past_create", use_container_width=True):
            execute_event_creation(details)
            st.session_state.pending_past_creation = None
            st.rerun()
        if col2.button("아니요, 취소합니다", key="cancel_past_create", use_container_width=True):
            msg = "알겠습니다. 등록을 취소했습니다."
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.session_state.pending_past_creation = None
            st.rerun()

# --- 5. 메인 로직 실행 ---

# Google OAuth 콜백 처리
if "code" in st.query_params and not st.session_state.authenticated:
    if st.query_params.get("state") == st.session_state.user_id:
        try:
            redirect_uri = "http://localhost:8501"
            exchange_code_for_token(st.session_state.user_id, st.query_params["code"], redirect_uri)
            st.session_state.authenticated = True
            st.success("🎉 구글 캘린더 연동에 성공했습니다!")
            st.query_params.clear()
            st.rerun()
        except CalendarAPIError as e:
            st.error(f"인증 토큰 교환 중 오류가 발생했습니다: {e}")

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not st.session_state.pending_creation and not st.session_state.pending_past_creation:
        with st.spinner("AI가 생각 중입니다..."):
            try:
                agent_response = st.session_state.agent.invoke(prompt)
                handle_agent_response(agent_response)
            except AuthRequiredError as e:
                auth_url = get_authorization_url(st.session_state.user_id, "http://localhost:8501")
                response = {"action": "request_auth", "auth_url": auth_url, "message": str(e)}
                handle_agent_response(response)
            except CalendarAPIError as e:
                st.error(f"오류가 발생했습니다: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"오류: {e}"})