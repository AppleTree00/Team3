import os
import json
import inspect
from datetime import datetime
from openai import OpenAI
import pytz
from dotenv import load_dotenv

# dev.md 가이드에 따라 calendar_api 모듈을 연동합니다.
from core.calendar_api import create_calendar_event, get_calendar_events, delete_calendar_event, delete_calendar_event_by_id, update_calendar_event, get_authorization_url
from core.exceptions import CalendarAPIError, AuthTokenExpiredError, ApiQuotaExceededError, CalendarEventNotFoundError, CalendarEventConflictError, AuthRequiredError
# dev.md '4-C', '4-E'에 따라 데이터베이스 모듈을 연동합니다.
from database.db_manager import add_or_get_user, update_event_history, get_last_event_id

# .env 파일에서 환경 변수 로드
load_dotenv()

class Agent:
    """
    LLM 오케스트레이터 및 프롬프트 로직을 담당하는 에이전트 클래스.
    dev.md 가이드라인에 따라 구현되었습니다.
    """
    def __init__(self, user_id: str):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        self.user_id = user_id
        # dev.md '4-C'에 따라 사용자 정보를 DB에 등록/조회합니다.
        self.user_info = add_or_get_user(self.user_id)

        # ui.md '6.2-B' Slot-filling을 위한 시스템 명령어 정의
        self.system_instruction = (
            "당신은 구글 캘린더 일정을 관리하는 유능한 비서입니다. "
            "사용자와의 대화를 통해 일정을 관리하는 것이 당신의 주요 목표입니다. "
            "사용자가 일정 생성이나 수정을 요청할 때 필요한 정보(예: 제목, 특정 시간, 소요 시간 등)가 누락된 경우, 함수를 호출하지 마세요. "
            "대신, 빠진 정보를 친절하고 명확하게 사용자에게 다시 질문하세요. 이것을 '정보 채우기(slot-filling)' 과업이라고 합니다.")

        # dev.md '4-B' 항목에 따라, LLM이 호출할 수 있는 함수(Tool) 목록을 정의합니다.
        # 실제 실행될 파이썬 함수와 매핑합니다.
        self.available_functions = {
            "create_calendar_event": create_calendar_event,
            "get_calendar_events": get_calendar_events,
            "delete_calendar_event": delete_calendar_event,
            "delete_calendar_event_by_id": delete_calendar_event_by_id,
            "update_calendar_event": update_calendar_event,
        }

    def _get_current_kst_time_prompt(self) -> str:
        """
        dev.md '4-A' 항목에 따라 현재 KST 시간을 포맷에 맞게 생성합니다.
        LLM이 상대적인 시간을 절대 시간으로 변환하는 데 핵심적인 컨텍스트를 제공합니다.
        """
        kst_timezone = pytz.timezone('Asia/Seoul')
        now_kst = datetime.now(kst_timezone)
        # 요일을 한국어로 변환
        weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][now_kst.weekday()]
        
        # "현재 한국 시간은 2026년 6월 18일 목요일 15:38 입니다." 형식으로 반환
        return now_kst.strftime(f"현재 한국 시간은 %Y년 %m월 %d일 {weekday_kr}요일 %H:%M 입니다.")

    def invoke(self, user_query: str):
        """
        사용자 쿼리를 받아 LLM을 호출하고, Function Calling을 처리합니다.
        """
        current_time_prompt = self._get_current_kst_time_prompt()
        system_prompt = f"{self.system_instruction}\n\n{current_time_prompt}"

        # dev.md '4-E' 컨텍스트 유지 기능 구현
        # 사용자의 발화에 컨텍스트 키워드가 있는지 확인합니다.
        contextual_keywords = ["방금", "아까", "그 일정", "그 회의", "그 약속"]
        if any(keyword in user_query for keyword in contextual_keywords):
            last_event_id = get_last_event_id(self.user_id)
            if last_event_id:
                # LLM이 컨텍스트를 더 잘 이해하도록 쿼리를 보강합니다.
                user_query += f" (컨텍스트: 방금 처리한 이벤트 ID는 '{last_event_id}' 입니다.)"
                print(f"DEBUG: 컨텍스트 정보를 추가하여 쿼리 보강: {user_query}")

        print(f"DEBUG: System Prompt: {system_prompt}")
 
        # dev.md '4-B' 항목에 따라 Function Calling(Tool Use)을 정의합니다.
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_calendar_event",
                    "description": "사용자의 요청에 따라 새로운 구글 캘린더 일정을 생성합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "일정의 제목"},
                            "start_datetime": {"type": "string", "description": "일정 시작 시간 (ISO 8601 형식, 예: 2026-06-19T15:00:00)"},
                            "end_datetime": {"type": "string", "description": "일정 종료 시간 (ISO 8601 형식, 예: 2026-06-19T16:00:00)"},
                        },
                        "required": ["title", "start_datetime", "end_datetime"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_calendar_events",
                    "description": "특정 날짜의 구글 캘린더 일정을 조회합니다. 사용자가 '오늘', '내일', '모레' 등의 상대적인 날짜나 특정 날짜를 언급하며 일정을 물어볼 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_str": {"type": "string", "description": "조회할 날짜 (YYYY-MM-DD 형식)"},
                        },
                        "required": ["date_str"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_calendar_event",
                    "description": "특정 날짜의 구글 캘린더 일정을 제목으로 찾아 삭제합니다. 사용자가 '취소', '삭제' 등의 키워드와 함께 일정 제목과 날짜를 언급할 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "삭제할 일정의 제목"},
                            "date_str": {"type": "string", "description": "일정이 있는 날짜 (YYYY-MM-DD 형식)"},
                        },
                        "required": ["title", "date_str"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_calendar_event_by_id",
                    "description": "이벤트의 고유 ID를 사용하여 구글 캘린더 일정을 삭제합니다. 사용자가 '방금 만든 일정', '아까 등록한 회의' 등 이전에 상호작용한 일정을 명시적으로 가리키며 삭제를 요청할 때 사용합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string", "description": "삭제할 이벤트의 고유 ID"},
                        },
                        "required": ["event_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_calendar_event",
                    "description": "기존 구글 캘린더 일정의 시간 또는 제목을 변경합니다. 사용자가 '변경', '수정', '옮겨줘' 등의 키워드를 사용할 때 호출합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "original_title": {"type": "string", "description": "변경하고자 하는 기존 일정의 제목"},
                            "date_str": {"type": "string", "description": "기존 일정이 위치한 날짜 (YYYY-MM-DD 형식)"},
                            "new_title": {"type": "string", "description": "새로운 일정 제목"},
                            "new_start_datetime": {"type": "string", "description": "새로운 시작 시간 (ISO 8601 형식)"},
                            "new_end_datetime": {"type": "string", "description": "새로운 종료 시간 (ISO 8601 형식)"},
                        },
                        "required": ["original_title", "date_str"],
                    },
                },
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # LLM이 함수 호출을 요청했는지 확인합니다.
        if tool_calls:
            # ui.md '6.2-A'에 따라, 'create_calendar_event'는 즉시 실행하지 않고 확인을 위해 UI에 정보를 반환합니다.
            # 여러 tool_call이 있더라도, 생성 확인이 필요한 경우 우선적으로 처리하고 반환합니다.
            for tool_call in tool_calls:
                if tool_call.function.name == "create_calendar_event":
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        print(f"DEBUG: '{tool_call.function.name}'에 대한 확인 요청을 UI로 보냅니다.")
                        return {
                            "action": "confirm_creation",
                            "details": function_args
                        }
                    except json.JSONDecodeError:
                        return f"오류: 함수 인자 파싱에 실패했습니다. (인자: {tool_call.function.arguments})"

            # 생성 확인이 필요 없는 다른 tool_call들을 처리합니다.
            # 여러 함수를 동시에 호출하는 경우(parallel function calling)도 처리합니다.
            results = []
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = self.available_functions.get(function_name)

                if function_to_call:
                    try:
                        function_args = json.loads(tool_call.function.arguments)

                        # dev.md '4-C' DB 연동에 따라, calendar_api 함수에 user_id를 주입합니다.
                        sig = inspect.signature(function_to_call)
                        if 'user_id' in sig.parameters:
                            function_args['user_id'] = self.user_id

                        print(f"DEBUG: LLM이 '{function_name}' 함수 호출을 요청했습니다.")
                        print(f"DEBUG: 전달된 인자: {function_args}")
                        
                        # 실제 함수를 실행합니다.
                        function_response = function_to_call(**function_args)

                        results.append(function_response)
                    except json.JSONDecodeError:
                        results.append(f"오류: 함수 인자 파싱에 실패했습니다. (인자: {tool_call.function.arguments})")
                    except (AuthTokenExpiredError, ApiQuotaExceededError, CalendarEventNotFoundError, CalendarEventConflictError) as e:
                        # Re-raise custom exceptions to be handled by the UI layer
                        raise e
                    except AuthRequiredError as e:
                        # If authentication is required, generate an authorization URL and return it to the UI.
                        # The redirect_uri here must match the one registered in Google Cloud Console
                        # and the one Streamlit will use.
                        # For local development with Streamlit, it's typically http://localhost:8501
                        # For the purpose of this task, we will assume a fixed redirect_uri.
                        redirect_uri = "http://localhost:8501" # Placeholder, will be passed from UI later
                        auth_url = get_authorization_url(self.user_id, redirect_uri)
                        print(f"DEBUG: AuthRequiredError caught. Returning authorization URL: {auth_url}")
                        return {
                            "action": "request_auth",
                            "auth_url": auth_url,
                            "message": "Google Calendar 인증이 필요합니다. 아래 링크를 클릭하여 로그인해주세요."
                        }
                    except CalendarAPIError as e: # Catch our own generic custom error
                        # Re-raise to be handled by the UI layer
                        raise e
                    except Exception as e: # Catch any other truly unexpected errors
                        # Wrap unexpected errors in a generic CalendarAPIError
                        raise CalendarAPIError(f"'{function_name}' 함수 실행 중 예상치 못한 오류 발생: {e}", original_error=e)
                else:
                    results.append(f"오류: '{function_name}'에 해당하는 함수를 찾을 수 없습니다.")
            
            # 모든 함수 실행 결과를 합쳐서 반환합니다.
            return "\n".join(results)
        else:
            # 함수 호출 없이 일반 텍스트로 응답한 경우
            return response_message.content

if __name__ == '__main__':
    # 테스트를 위한 임시 사용자 ID
    test_user_id = "test_user_01"
    agent = Agent(user_id=test_user_id)

    # REQ-01 & REQ-03 (Contextual) 테스트 시나리오
    print("--- 시나리오 1: 일정 생성 후 컨텍스트 기반 삭제 ---")

    # 1. 일정 생성
    print("\n[USER] 내일 오후 4시에 '컨텍스트 테스트 회의' 잡아줘")
    result_create = agent.invoke("내일 오후 4시에 '컨텍스트 테스트 회의' 잡아줘")
    print("[AGENT]", result_create)

    # 2. 컨텍스트 기반 삭제
    # 사용자가 '방금'이라는 키워드를 사용
    print("\n[USER] 방금 등록한 회의 취소해줘")
    result_delete_context = agent.invoke("방금 등록한 회의 취소해줘")
    print("[AGENT]", result_delete_context)

    # REQ-03 (Update) 테스트 시나리오
    print("\n--- 시나리오 2: 일정 변경 ---")
    # 1. 변경할 일정 생성
    print("\n[USER] 내일 오후 3시에 '업무 보고' 회의 잡아줘")
    result_create_for_update = agent.invoke("내일 오후 3시에 '업무 보고' 회의 잡아줘")
    print("[AGENT]", result_create_for_update)
    # 2. 생성된 일정 변경
    print("\n[USER] 내일 '업무 보고' 회의를 오후 5시로 변경해줘")
    result_update = agent.invoke("내일 '업무 보고' 회의를 오후 5시로 변경해줘")
    print("[AGENT]", result_update)

    # ui.md '6.2-B' (Slot-filling) 테스트 시나리오
    print("\n--- 시나리오 4: 정보 부족 시 되묻기 (Slot-filling) ---")
    print("\n[USER] 다음 주 월요일에 약속 잡아줘")
    result_slot_filling = agent.invoke("다음 주 월요일에 약속 잡아줘")
    print("[AGENT]", result_slot_filling)