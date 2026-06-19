import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Database Path Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "agent_data.db")

def get_weekly_report_data():
    """지난 7일간의 데이터를 DB에서 조회하여 리포트용으로 가공합니다."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)

    with sqlite3.connect(DB_PATH) as conn:
        # ai_interaction_log 테이블이 UTC 시간으로 저장되므로, 그대로 사용
        query = f"SELECT * FROM ai_interaction_log WHERE timestamp >= '{start_date}' AND timestamp < '{end_date}'"
        df = pd.read_sql_query(query, conn, parse_dates=['timestamp'])

    if df.empty:
        return None

    # 지표 계산
    total_interactions = len(df)
    slot_filling_count = len(df[df['interaction_type'] == 'slot_filling'])
    
    func_calls = df[df['interaction_type'].isin(['function_call_success', 'function_call_fail'])]
    total_func_calls = len(func_calls)
    success_calls = len(func_calls[func_calls['interaction_type'] == 'function_call_success'])
    success_rate = (success_calls / total_func_calls * 100) if total_func_calls > 0 else 0

    # 가장 많이 사용된 함수
    success_calls_df = func_calls[func_calls['interaction_type'] == 'function_call_success'].copy()
    if not success_calls_df.empty:
        success_calls_df['function_name'] = success_calls_df['details'].apply(lambda x: pd.read_json(x, typ='series').get('function_name'))
        top_functions = success_calls_df['function_name'].value_counts().head(3)
    else:
        top_functions = pd.Series()

    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "total_interactions": total_interactions,
        "slot_filling_count": slot_filling_count,
        "total_func_calls": total_func_calls,
        "success_rate": f"{success_rate:.2f}%",
        "top_functions": top_functions.to_dict()
    }

def generate_html_report(data: dict) -> str:
    """리포트 데이터를 바탕으로 HTML 이메일 본문을 생성합니다."""
    if not data:
        return "<h1>주간 리포트</h1><p>지난 주 데이터가 없습니다.</p>"

    top_functions_html = "<ul>"
    if data['top_functions']:
        for func, count in data['top_functions'].items():
            top_functions_html += f"<li><b>{func}</b>: {count}회</li>"
    else:
        top_functions_html = "<li>사용된 기능 없음</li>"
    top_functions_html += "</ul>"

    html = f"""
    <html><head><style>
        body {{ font-family: sans-serif; }} .container {{ max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; }}
        h1 {{ color: #333; }} .metric {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 10px; border-radius: 5px; }}
        .metric h3 {{ margin-top: 0; }} .metric p {{ font-size: 24px; font-weight: bold; margin-bottom: 0; }}
    </style></head><body><div class="container">
        <h1>📊 개인 일정 관리 AI 에이전트 주간 리포트</h1>
        <p><b>리포트 기간:</b> {data['start_date']} ~ {data['end_date']}</p>
        <div class="metric"><h3>총 상호작용 수</h3><p>{data['total_interactions']}</p></div>
        <div class="metric"><h3>Function Calling 성공률</h3><p>{data['success_rate']}</p><small>총 호출: {data['total_func_calls']}회</small></div>
        <div class="metric"><h3>정보 보완(Slot-filling) 요청 수</h3><p>{data['slot_filling_count']} 회</p></div>
        <div class="metric"><h3>Top 3 사용 기능</h3>{top_functions_html}</div>
    </div></body></html>
    """
    return html

def send_email(subject: str, html_content: str, recipient_email: str):
    """설정된 SMTP 서버를 통해 이메일을 발송합니다."""
    smtp_server, smtp_port, smtp_username, smtp_password = os.getenv("SMTP_SERVER"), os.getenv("SMTP_PORT"), os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD")
    if not all([smtp_server, smtp_port, smtp_username, smtp_password, recipient_email]):
        raise ValueError("SMTP 관련 환경 변수와 수신자 이메일을 .env 파일에 모두 설정해야 합니다.")

    msg = MIMEMultipart('alternative')
    msg['Subject'], msg['From'], msg['To'] = subject, smtp_username, recipient_email
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
    print(f"✅ 리포트 이메일이 성공적으로 발송되었습니다. (수신자: {recipient_email})")