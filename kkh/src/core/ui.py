import streamlit as st
import os
import sys
from datetime import datetime
import pytz

# 프로젝트 루트 경로를 sys.path에 추가하여 다른 모듈(core, database)을 임포트할 수 있도록 합니다.
# Streamlit 실행 환경과 정적 분석 도구(Pylance)에서 모두 안정적으로 모듈을 찾을 수 있도록
# 프로젝트의 'src' 디렉토리를 sys.path에 추가합니다.
# 이렇게 하면 'src'를 최상위 패키지로 하는 절대 경로 임포트가 가능해집니다.
SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SRC_ROOT not in sys.path:
    sys.path.append(SRC_ROOT)

from core.agent import Agent
from core.exceptions import CalendarAPIError, AuthTokenExpiredError, ApiQuotaExceededError, CalendarEventNotFoundError, CalendarEventConflictError, AuthRequiredError
from core.calendar_api import get_calendar_events, create_calendar_event, exchange_code_for_token
from database.db_manager import update_event_history, get_auth_token

# --- Streamlit 페이지 설정 ---
st.set_page_config(
    page_title="개인 일정 관리 AI 에이전트",
    page_icon="🗓️",
    layout="centered",
    initial_sidebar_state="auto",
)

# UI 전체에서 사용할 사용자 ID. 세션 상태에서 관리.
if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user" # 초기값 설정

# OAuth2 Redirect URI (Streamlit 앱의 기본 실행 주소)
# 로컬 환경에서는 일반적으로 http://localhost:8501 입니다.
REDIRECT_URI = "http://localhost:8501"

# --- OAuth 콜백 처리 ---
# Google로부터 리다이렉트된 경우 URL 파라미터에 'code'가 포함됩니다.
query_params = st.query_params
if "code" in query_params and "state" in query_params:
    auth_code = query_params["code"]
    state_user_id = query_params["state"]

    if state_user_id == st.session_state.user_id: # 간단한 state 검증
        try:
            exchange_code_for_token(st.session_state.user_id, auth_code, REDIRECT_URI)
            st.success("✅ Google Calendar 인증에 성공했습니다!")
            # 쿼리 파라미터를 제거하여 새로고침 시 재인증 방지
            st.experimental_set_query_params(code=None, state=None)
            st.experimental_rerun()
        except Exception as e:
            st.error(f"❌ Google Calendar 인증 중 오류 발생: {e}")
            st.experimental_set_query_params(code=None, state=None)
            st.experimental_rerun()
    else:
        st.error("❌ OAuth 상태 불일치 오류. 인증 요청이 올바르지 않습니다.")
        st.experimental_set_query_params(code=None, state=None)
        st.experimental_rerun()
# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 어떤 일정을 도와드릴까요?"}]
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

# --- 메인 채팅 UI ---
st.title("개인 일정 관리 AI 에이전트")
st.caption("자연어 대화로 당신의 구글 캘린더를 관리하세요.")

# 이전 채팅 기록을 화면에 표시합니다.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 사이드바 UI (ui.md 6.1) ---
with st.sidebar:
    st.header("사용자 설정")
    st.session_state.user_id = st.text_input(
        "사용자 ID 입력",
        value=st.session_state.user_id,
        key="user_id_input",
        help="Google Calendar 인증에 사용될 사용자 ID를 입력하세요. (예: test_user_01)"
    )
    if not st.session_state.user_id or st.session_state.user_id == "default_user":
        st.warning("유효한 사용자 ID를 입력해주세요.")
        st.stop() # 사용자 ID가 없으면 앱 실행 중지

    st.header("🔐 캘린더 연동 상태")
    # db_manager와 연동하여 실제 인증 상태(토큰 존재 여부)를 표시합니다.
    is_authenticated = get_auth_token(user_id=st.session_state.user_id) is not None
    
    if is_authenticated:
        st.success(f"'{st.session_state.user_id}' 계정과 연결됨")
        if st.button("연결 해제"):
            st.warning("연결 해제 기능은 아직 구현되지 않았습니다.")
    else:
        st.error(f"'{st.session_state.user_id}' 계정이 연결되지 않았습니다.")
        st.info("캘린더 기능을 사용하려면 인증이 필요합니다. 채팅을 시작하면 인증 절차가 진행됩니다.")

    st.divider()

    st.header("🗓️ 오늘의 일정")
    # REQ-02 (일정 조회) 기능과 연동하여 오늘 일정을 표시합니다.
    if is_authenticated: # 인증된 경우에만 일정 표시
        try:
            kst = pytz.timezone('Asia/Seoul')
            today_str = datetime.now(kst).strftime("%Y-%m-%d")
            todays_events = get_calendar_events(user_id=st.session_state.user_id, date_str=today_str)
            st.markdown(todays_events)
        except AuthTokenExpiredError:
            # 사이드바 로딩 시 인증 에러는 채팅 시작으로 유도
            st.warning("인증이 만료되었습니다. 채팅을 시작하여 재인증해주세요.")
        except ApiQuotaExceededError:
            st.warning("API 할당량을 초과했습니다.")
        except Exception as e:
            st.error(f"일정 로딩 실패: {e}")

# ui.md '6.2-A'에 따른 일정 등록 확인 UI
if st.session_state.pending_action:
    action_details = st.session_state.pending_action['details']
    with st.chat_message("assistant"):
        try:
            start_dt = datetime.fromisoformat(action_details['start_datetime'])
            # 한국어 요일 변환
            weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][start_dt.weekday()]
            date_str = start_dt.strftime(f"%Y년 %m월 %d일 ({weekday_kr})")
            time_str = start_dt.strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
        except (ValueError, KeyError):
            date_str = "알 수 없는 날짜"
            time_str = "알 수 없는 시간"

        st.markdown(
            f"""
            **✨ 새로운 일정을 등록할까요?**
            - **제목:** {action_details.get('title', '제목 없음')}
            - **날짜:** {date_str}
            - **시간:** {time_str}
            """
        )
        
        col1, col2, _ = st.columns([1, 1, 3])
        with col1:
            if st.button("✅ 확인", use_container_width=True):
                with st.spinner("일정을 등록하는 중..."):
                    response_dict = create_calendar_event(user_id=st.session_state.user_id, **action_details)
                    final_response = response_dict.get("message", "오류가 발생했습니다.")
                    event_id = response_dict.get("event_id")
                    
                    if event_id:
                        update_event_history(st.session_state.user_id, event_id)
                    
                    st.session_state.messages.append({"role": "assistant", "content": final_response})
                    st.session_state.pending_action = None
                    st.rerun()

        with col2:
            if st.button("❌ 취소", use_container_width=True):
                final_response = "알겠습니다. 등록을 취소했습니다."
                st.session_state.messages.append({"role": "assistant", "content": final_response})
                st.session_state.pending_action = None
                st.rerun()

# 사용자 입력을 받습니다.
if prompt := st.chat_input("내일 오후 3시에 개발팀 주간 회의 잡아줘"):
    if st.session_state.pending_action:
        st.toast("먼저 제안된 일정을 확인 또는 취소해주세요.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("생각 중..."):
            agent = Agent(user_id=st.session_state.user_id)
            try:
                response = agent.invoke(prompt)
            except AuthTokenExpiredError:
                st.error("🚨 Google Calendar 인증이 만료되었거나 유효하지 않습니다. 다시 인증해주세요.")
                response = "인증이 필요합니다. 잠시 후 페이지를 새로고침하여 다시 시도해주세요."
            except ApiQuotaExceededError:
                st.error("🚨 Google Calendar API 할당량을 초과했습니다. 잠시 후 다시 시도해주세요.")
                response = "API 할당량을 초과하여 요청을 처리할 수 없습니다."
            except CalendarEventNotFoundError as e:
                st.warning(f"🤔 일정을 찾을 수 없습니다: {e}")
                response = str(e)
            except CalendarEventConflictError as e:
                st.warning(f"🤔 여러 일정이 해당됩니다: {e}")
                response = str(e)
            except CalendarAPIError as e:
                st.error(f"🚨 캘린더 API 오류: {e}")
                response = "캘린더 기능 사용 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            except Exception as e:
                st.error(f"처리 중 예상치 못한 오류가 발생했습니다: {e}")
                response = f"죄송합니다, 요청을 처리하는 중에 예상치 못한 오류가 발생했습니다."

    if isinstance(response, dict):
        if response.get("action") == "confirm_creation":
            st.session_state.pending_action = response
            st.rerun()
        elif response.get("action") == "request_auth":
            st.session_state.messages.append({"role": "assistant", "content": f"{response.get('message', '인증이 필요합니다.')} [여기]({response.get('auth_url')})를 클릭해주세요."})
            st.rerun()
    else:
        st.session_state.messages.append({"role": "assistant", "content": str(response)})
        st.rerun()