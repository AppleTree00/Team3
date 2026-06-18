import datetime
import os.path
import json
import os
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow # Changed from InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# dev.md '4-C' 요구사항에 따라 db_manager에서 토큰 관리 함수를 가져옵니다.
from core.exceptions import AuthTokenExpiredError, ApiQuotaExceededError, CalendarAPIError, CalendarEventNotFoundError, CalendarEventConflictError, AuthRequiredError
from database.db_manager import get_auth_token, save_auth_token

# Google Calendar API의 권한 범위(Scope)를 정의합니다.
# 여기서는 읽기/쓰기 권한을 모두 요청합니다.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# 스크립트가 실행되는 위치에 관계없이 프로젝트 루트를 기준으로 파일을 찾도록 경로를 설정합니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
# TOKEN_PATH는 더 이상 사용되지 않으며, DB로 대체됩니다.
# TOKEN_PATH = os.path.join(PROJECT_ROOT, "token.json")
CREDS_PATH = os.path.join(PROJECT_ROOT, "credentials.json")


def get_calendar_service(user_id: str):
    """Google Calendar API 서비스 객체를 생성하고 반환합니다.

    OAuth 2.0 인증 흐름을 처리합니다.
    - DB에서 'user_id'에 해당하는 인증 정보를 로드합니다.
    - 유효하지 않거나 만료된 경우, 리프레시합니다.
    - 새로운 인증 정보는 DB에 저장합니다.
    - 인증 정보가 없거나 갱신할 수 없는 경우 AuthRequiredError를 발생시킵니다.
    """
    creds = None
    token_info = get_auth_token(user_id)
    if token_info:
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                token_dict = json.loads(creds.to_json())
                save_auth_token(user_id, token_dict)
            except Exception as e:
                # Refresh token might also fail, require full re-authentication
                raise AuthRequiredError("Google Calendar 인증 토큰 갱신에 실패했습니다. 다시 인증해주세요.", original_error=e)
        else:
            # No valid credentials and no refresh token, so authentication is required
            raise AuthRequiredError("Google Calendar 인증이 필요합니다. 로그인해주세요.")
    
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        raise CalendarAPIError(f"Google Calendar 서비스 빌드 중 오류 발생: {error}", original_error=error)
    except Exception as e:
        raise CalendarAPIError(f"Google Calendar 서비스 빌드 중 알 수 없는 오류 발생: {e}", original_error=e)

def get_auth_flow(user_id: str, redirect_uri: str) -> Flow:
    """
    웹 기반 OAuth 흐름을 위한 Flow 객체를 생성합니다.
    user_id를 state 파라미터로 사용하여 콜백 후 사용자 식별에 활용합니다.
    """
    try:
        # Load client secrets from credentials.json
        with open(CREDS_PATH, 'r') as secret_file:
            client_config = json.load(secret_file)
        
        # Ensure 'web' key exists and contains client_id, client_secret
        if 'web' not in client_config or \
           not all(k in client_config['web'] for k in ['client_id', 'client_secret']):
            raise ValueError("Invalid credentials.json format for web application. Missing 'web' client_id/secret.")

        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=user_id, # Preserve user_id through the OAuth flow
            redirect_uri=redirect_uri
        )
        return flow
    except FileNotFoundError:
        raise CalendarAPIError(f"Google Calendar 인증 파일을 찾을 수 없습니다: {CREDS_PATH}. Google Cloud Console에서 다운로드한 'credentials.json' 파일을 프로젝트 루트에 넣어주세요.")
    except Exception as e:
        raise CalendarAPIError(f"OAuth Flow 생성 중 오류 발생: {e}", original_error=e)

def get_authorization_url(user_id: str, redirect_uri: str) -> str:
    """
    Google Calendar API 인증을 위한 Authorization URL을 생성하여 반환합니다.
    이 URL로 사용자를 리다이렉트하여 Google 계정 로그인 및 권한 부여를 요청합니다.
    """
    flow = get_auth_flow(user_id, redirect_uri)
    authorization_url, state = flow.authorization_url(
        access_type='offline', # Refresh token을 얻기 위해 필요
        include_granted_scopes='true'
    )
    # state는 flow 객체 내부에 이미 저장되어 있으며, 콜백 시 검증됩니다.
    return authorization_url

def exchange_code_for_token(user_id: str, auth_code: str, redirect_uri: str):
    """
    콜백으로 받은 authorization code를 사용하여 액세스 토큰 및 리프레시 토큰을 교환하고 저장합니다.
    """
    flow = get_auth_flow(user_id, redirect_uri)
    try:
        # 인증 코드를 사용하여 토큰 교환
        flow.fetch_token(code=auth_code)
        creds = flow.credentials

        # 사용자 ID가 state 파라미터와 일치하는지 확인 (보안 강화)
        if flow.state != user_id:
            raise CalendarAPIError("OAuth state mismatch. Potential CSRF attack or invalid callback.")

        # 다음 실행을 위해 인증 정보를 DB에 저장합니다.
        token_dict = json.loads(creds.to_json())
        save_auth_token(user_id, token_dict)
        return True
    except Exception as e:
        raise CalendarAPIError(f"인증 코드 토큰 교환 중 오류 발생: {e}", original_error=e)

def create_calendar_event(user_id: str, title: str, start_datetime: str, end_datetime: str):
    """
    dev.md '4-B'에서 정의된 함수 명세에 따라 새로운 구글 캘린더 일정을 생성합니다.

    Args:
        title (str): 일정 제목
        start_datetime (str): 시작 시간 (ISO 8601 형식)
        end_datetime (str): 종료 시간 (ISO 8601 형식)

    Returns:
        str: 성공 또는 실패 메시지
    """
    service = get_calendar_service(user_id) # This will now raise an exception if it fails

    # Google Calendar API가 요구하는 이벤트 객체 형식으로 변환합니다.
    # LLM이 'Asia/Seoul' 시간대를 기준으로 ISO 8601 문자열을 생성하므로,
    # API 요청 시에도 해당 시간대를 명시해주는 것이 정확합니다.
    event = {
        'summary': title,
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'Asia/Seoul',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'Asia/Seoul',
        },
    }

    try:
        # dev.md '4-D'의 예외 처리 요구사항을 고려하여 API를 호출합니다.
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        event_id = created_event.get('id')
        print(f"DEBUG: Event created: {created_event.get('htmlLink')}, ID: {event_id}")
        # ui.md '6.2-A'의 피드백 요구사항에 맞춰 성공 메시지를 반환합니다.
        # dev.md '4-E' 컨텍스트 유지를 위해 event_id를 함께 반환합니다.
        return {
            "message": f"✅ 일정이 등록되었습니다: '{title}' ({start_datetime} ~ {end_datetime})",
            "event_id": event_id
        }
    except HttpError as error:
        if error.resp.status == 401:
            raise AuthTokenExpiredError("Google Calendar 인증이 만료되었습니다. 다시 인증해주세요.", original_error=error)
        elif error.resp.status == 403: # Often indicates quota issues
            raise ApiQuotaExceededError("Google Calendar API 할당량을 초과했습니다. 잠시 후 다시 시도해주세요.", original_error=error)
        else:
            raise CalendarAPIError(f"일정 생성 중 Google Calendar API 오류 발생: {error}", original_error=error)
    except Exception as e:
        raise CalendarAPIError(f"일정 생성 중 알 수 없는 오류 발생: {e}", original_error=e)


def get_calendar_events(user_id: str, date_str: str):
    """
    dev.md '4-B'에서 정의된 함수 명세에 따라 특정 날짜의 구글 캘린더 일정을 조회합니다.

    Args:
        date_str (str): 조회할 날짜 (YYYY-MM-DD 형식)

    Returns:
        str: 해당 날짜의 일정 목록 또는 결과 메시지
    """
    service = get_calendar_service(user_id) # This will now raise an exception if it fails

    try:
        # YYYY-MM-DD 형식의 문자열을 datetime 객체로 파싱합니다.
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

        # dev.md '2. 주요 책임'에 따라 KST 기준 시간으로 처리합니다.
        kst = pytz.timezone('Asia/Seoul')

        # 조회 시작 시간을 해당 날짜의 시작(00:00:00)으로 설정
        time_min = kst.localize(datetime.datetime.combine(target_date, datetime.time.min)).isoformat()

        # 조회 종료 시간을 해당 날짜의 끝(23:59:59)으로 설정
        time_max = kst.localize(datetime.datetime.combine(target_date, datetime.time.max)).isoformat()

        print(f"DEBUG: Searching events for {date_str} between {time_min} and {time_max}")

        events_result = (
            service.events()
            .list(
                calendarId="primary", timeMin=time_min, timeMax=time_max, singleEvents=True, orderBy="startTime"
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            return f"✅ {date_str}에는 예정된 일정이 없습니다."

        # ui.md '6.1 사이드바' 및 'B. 결과 요약 카드' 디자인을 고려하여 결과 포맷팅
        event_list = [f"🗓️ {date_str} 일정 목록입니다."]
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))

            if 'T' in start:  # 시간 정보가 있는 경우
                start_dt = datetime.datetime.fromisoformat(start)
                start_formatted = start_dt.strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
            else:  # 종일 일정인 경우
                start_formatted = "하루 종일"

            event_list.append(f"- {start_formatted}: {event['summary']}")

        return "\n".join(event_list)
    except (ValueError, TypeError):
        raise CalendarAPIError(f"날짜 형식이 올바르지 않습니다. 'YYYY-MM-DD' 형식으로 전달되어야 합니다. (입력값: {date_str})")
    except HttpError as error:
        print(f"An error occurred during event retrieval: {error}")
        if error.resp.status == 401:
            raise AuthTokenExpiredError("Google Calendar 인증이 만료되었습니다. 다시 인증해주세요.", original_error=error)
        elif error.resp.status == 403:
            raise ApiQuotaExceededError("Google Calendar API 할당량을 초과했습니다. 잠시 후 다시 시도해주세요.", original_error=error)
        else:
            raise CalendarAPIError(f"일정 조회 중 Google Calendar API 오류 발생: {error}", original_error=error)
    except Exception as e:
        raise CalendarAPIError(f"일정 조회 중 알 수 없는 오류 발생: {e}", original_error=e)


def delete_calendar_event(user_id: str, title: str, date_str: str):
    """
    특정 날짜의 일정을 제목으로 찾아 삭제합니다. REQ-03 요구사항을 구현합니다.
    정확히 일치하는 제목의 일정이 하나일 경우에만 삭제를 수행합니다.

    Args:
        title (str): 삭제할 일정의 제목
        date_str (str): 일정이 있는 날짜 (YYYY-MM-DD 형식)

    Returns:
        str: 성공, 실패 또는 확인 요청 메시지
    """
    service = get_calendar_service(user_id) # This will now raise an exception if it fails

    try:
        # get_calendar_events와 동일한 로직으로 날짜 범위 설정
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        kst = pytz.timezone('Asia/Seoul')
        time_min = kst.localize(datetime.datetime.combine(target_date, datetime.time.min)).isoformat()
        time_max = kst.localize(datetime.datetime.combine(target_date, datetime.time.max)).isoformat()

        events_result = (
            service.events()
            .list(calendarId="primary", timeMin=time_min, timeMax=time_max, singleEvents=True)
            .execute()
        )
        events = events_result.get("items", [])

        # 제목(summary)이 대소문자 구분 없이 정확히 일치하는 이벤트를 찾습니다.
        matching_events = [event for event in events if event.get("summary", "").lower() == title.lower()]

        if len(matching_events) == 0:
            raise CalendarEventNotFoundError(f"'{date_str}'에 '{title}' 제목의 일정을 찾을 수 없습니다.")

        if len(matching_events) > 1:
            raise CalendarEventConflictError(f"'{title}' 제목으로 여러 개의 일정이 검색되었습니다. 더 구체적으로 알려주세요.")

        event_to_delete = matching_events[0]
        event_id = event_to_delete["id"]

        service.events().delete(calendarId='primary', eventId=event_id).execute()

        return f"✅ {date_str}의 '{title}' 일정을 삭제했습니다."
    except (ValueError, TypeError):
        raise CalendarAPIError(f"날짜 형식이 올바르지 않습니다. 'YYYY-MM-DD' 형식으로 전달되어야 합니다. (입력값: {date_str})")
    except HttpError as error: # Catch HttpError during list or delete
        if error.resp.status == 401:
            raise AuthTokenExpiredError("Google Calendar 인증이 만료되었습니다. 다시 인증해주세요.", original_error=error)
        elif error.resp.status == 403:
            raise ApiQuotaExceededError("Google Calendar API 할당량을 초과했습니다. 잠시 후 다시 시도해주세요.", original_error=error)
        elif error.resp.status == 404: # Event might have been deleted by another process
            raise CalendarEventNotFoundError(f"삭제하려는 일정을 찾을 수 없습니다. (ID: {event_id})", original_error=error)
        else:
            raise CalendarAPIError(f"일정 삭제 중 Google Calendar API 오류 발생: {error}", original_error=error)
    except Exception as e:
        raise CalendarAPIError(f"일정 삭제 중 알 수 없는 오류 발생: {e}", original_error=e)


def delete_calendar_event_by_id(user_id: str, event_id: str):
    """
    dev.md '4-B' 명세에 따라 event_id로 구글 캘린더 일정을 삭제합니다.
    "방금 만든 일정 취소해줘"와 같은 컨텍스트 기반 요청을 처리하는 데 사용됩니다.

    Args:
        event_id (str): 삭제할 이벤트의 고유 ID

    Returns:
        str: 성공 또는 실패 메시지
    """
    service = get_calendar_service(user_id) # This will now raise an exception if it fails

    try:
        # 삭제 전 이벤트 정보를 가져와 사용자에게 더 나은 피드백을 제공합니다.
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        summary = event.get('summary', '제목 없는 일정')

        service.events().delete(calendarId='primary', eventId=event_id).execute()

        return f"✅ '{summary}' 일정을 삭제했습니다."
    except HttpError as error:
        if error.resp.status == 404:
            raise CalendarEventNotFoundError(f"ID '{event_id}'에 해당하는 일정을 찾을 수 없거나 이미 삭제되었습니다.", original_error=error)
        elif error.resp.status == 401:
            raise AuthTokenExpiredError("Google Calendar 인증이 만료되었습니다. 다시 인증해주세요.", original_error=error)
        elif error.resp.status == 403:
            raise ApiQuotaExceededError("Google Calendar API 할당량을 초과했습니다. 잠시 후 다시 시도해주세요.", original_error=error)
        else:
            raise CalendarAPIError(f"일정 삭제 중 Google Calendar API 오류 발생: {error}", original_error=error)
    except Exception as e:
        raise CalendarAPIError(f"일정 삭제 중 알 수 없는 오류 발생: {e}", original_error=e)


def update_calendar_event(user_id: str, original_title: str, date_str: str, new_title: str = None, new_start_datetime: str = None, new_end_datetime: str = None):
    """
    특정 날짜의 일정을 제목으로 찾아 변경합니다. REQ-03의 '변경' 요구사항을 구현합니다.
    하나 이상의 변경 사항(새 제목, 새 시작/종료 시간)이 반드시 제공되어야 합니다.

    Args:
        original_title (str): 변경할 기존 일정의 제목
        date_str (str): 일정이 있는 날짜 (YYYY-MM-DD 형식)
        new_title (str, optional): 새로운 일정 제목. Defaults to None.
        new_start_datetime (str, optional): 새로운 시작 시간 (ISO 8601). Defaults to None.
        new_end_datetime (str, optional): 새로운 종료 시간 (ISO 8601). Defaults to None.

    Returns:
        str: 성공, 실패 또는 확인 요청 메시지
    """
    service = get_calendar_service(user_id) # This will now raise an exception if it fails

    if not any([new_title, new_start_datetime, new_end_datetime]):
        return "❓ 변경할 내용(새 제목, 새 시간)이 없습니다. 무엇을 변경할지 알려주세요."

    try:
        # get_calendar_events와 동일한 로직으로 날짜 범위 설정
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        kst = pytz.timezone('Asia/Seoul')
        time_min = kst.localize(datetime.datetime.combine(target_date, datetime.time.min)).isoformat()
        time_max = kst.localize(datetime.datetime.combine(target_date, datetime.time.max)).isoformat()

        events_result = service.events().list(calendarId="primary", timeMin=time_min, timeMax=time_max, singleEvents=True).execute()
        events = events_result.get("items", [])

        matching_events = [event for event in events if event.get("summary", "").lower() == original_title.lower()]

        if len(matching_events) == 0:
            raise CalendarEventNotFoundError(f"'{date_str}'에 '{original_title}' 제목의 일정을 찾을 수 없습니다.")

        if len(matching_events) > 1:
            raise CalendarEventConflictError(f"'{original_title}' 제목으로 여러 개의 일정이 검색되었습니다. 더 구체적으로 알려주세요.")

        event_to_update = matching_events[0]
        event_id = event_to_update["id"]

        if new_title:
            event_to_update['summary'] = new_title
        
        if new_start_datetime and not new_end_datetime and 'dateTime' in event_to_update['start']:
            duration = datetime.datetime.fromisoformat(event_to_update['end']['dateTime']) - datetime.datetime.fromisoformat(event_to_update['start']['dateTime'])
            new_start = datetime.datetime.fromisoformat(new_start_datetime)
            event_to_update['start']['dateTime'] = new_start.isoformat()
            event_to_update['end']['dateTime'] = (new_start + duration).isoformat()
        elif new_start_datetime:
            event_to_update['start']['dateTime'] = new_start_datetime
        
        if new_end_datetime:
            event_to_update['end']['dateTime'] = new_end_datetime

        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event_to_update).execute()
        return f"✅ '{original_title}' 일정을 성공적으로 변경했습니다: '{updated_event.get('summary')}'"
    except (ValueError, TypeError):
        raise CalendarAPIError(f"날짜 형식이 올바르지 않습니다. 'YYYY-MM-DD' 형식으로 전달되어야 합니다. (입력값: {date_str})")
    except HttpError as error: # Catch HttpError during list or update
        if error.resp.status == 401:
            raise AuthTokenExpiredError("Google Calendar 인증이 만료되었습니다. 다시 인증해주세요.", original_error=error)
        elif error.resp.status == 403:
            raise ApiQuotaExceededError("Google Calendar API 할당량을 초과했습니다. 잠시 후 다시 시도해주세요.", original_error=error)
        elif error.resp.status == 404: # Event might have been deleted by another process
            raise CalendarEventNotFoundError(f"변경하려는 일정을 찾을 수 없습니다. (ID: {event_id})", original_error=error)
        else:
            raise CalendarAPIError(f"일정 변경 중 Google Calendar API 오류 발생: {error}", original_error=error)
    except Exception as e:
        raise CalendarAPIError(f"일정 변경 중 알 수 없는 오류 발생: {e}", original_error=e)


if __name__ == "__main__":
    test_user = "test_user_for_api"
    # 이 스크립트를 직접 실행하여 API 연동을 테스트합니다.
    service = get_calendar_service(test_user)
    if service:
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z'는 UTC를 나타냅니다.
        print("앞으로 예정된 10개의 일정을 가져옵니다.")
        events_result = (
            service.events()
            .list(
                calendarId="primary", timeMin=now, maxResults=10, singleEvents=True, orderBy="startTime"
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("예정된 일정이 없습니다.")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])