import streamlit as st
import pandas as pd
import sqlite3
import os
import altair as alt
from datetime import datetime, timedelta

# --- 0. 초기 설정 ---

# 프로젝트 루트를 sys.path에 추가 (dashboard.py를 직접 실행하기 위함)
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "agent_data.db")

st.set_page_config(page_title="운영 대시보드", layout="wide")

st.title("📊 개인 일정 관리 AI 에이전트 - 운영 대시보드")
st.caption("이 대시보드는 제품의 주요 지표를 시각화하여 데이터 기반 의사결정을 지원합니다.")

# --- 1. 데이터 로딩 및 처리 ---

@st.cache_data(ttl=600) # 10분마다 데이터 캐시
def load_dashboard_data():
    """데이터베이스에서 데이터를 로드합니다."""
    if not os.path.exists(DB_PATH):
        st.error(f"데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}")
        return None, None, None, None
        
    with sqlite3.connect(DB_PATH) as conn:
        try:
            users_df = pd.read_sql_query("SELECT * FROM users", conn)
            auth_tokens_df = pd.read_sql_query("SELECT user_id FROM auth_tokens", conn)
            event_history_df = pd.read_sql_query("SELECT * FROM event_history", conn, parse_dates=['updated_at'])
            # 새로 추가된 로그 테이블 로드
            interaction_log_df = pd.read_sql_query("SELECT * FROM ai_interaction_log", conn, parse_dates=['timestamp'])
            return users_df, auth_tokens_df, event_history_df, interaction_log_df
        except pd.io.sql.DatabaseError as e:
            st.error(f"DB 테이블을 읽는 중 오류 발생: {e}. 'create_tables()'가 먼저 실행되었는지 확인하세요.")
            return None, None, None, None

# 데이터 로드
users_df, auth_tokens_df, event_history_df, interaction_log_df = load_dashboard_data()

# --- 2. 대시보드 UI 구성 ---

if users_df is None:
    st.stop()

def process_interaction_data(df):
    """인터랙션 로그 데이터를 대시보드 시각화에 맞게 가공합니다."""
    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df['date'] = df['timestamp'].dt.date

    # 기능별 사용량 데이터 (성공한 function call만 집계)
    func_df = df[df['interaction_type'] == 'function_call_success'].copy()
    func_df['function_name'] = func_df['details'].apply(lambda x: pd.read_json(x, typ='series').get('function_name'))
    function_usage = func_df.groupby(['date', 'function_name']).size().reset_index(name='count')

    # AI 성능 데이터
    daily_summary = df.groupby('date')['interaction_type'].value_counts().unstack(fill_value=0)
    daily_summary['total_calls'] = daily_summary.get('function_call_success', 0) + daily_summary.get('function_call_fail', 0)
    daily_summary['success_rate'] = (daily_summary.get('function_call_success', 0) / daily_summary['total_calls'].replace(0, 1)) * 100
    ai_performance = daily_summary[['success_rate', 'slot_filling']].reset_index()
    
    return function_usage, ai_performance

function_usage_df, ai_performance_df = process_interaction_data(interaction_log_df)

# 2.1. 최상단 핵심 지표 (KPIs)
st.subheader("🚀 핵심 지표 (KPIs)")
total_users = len(users_df)
authenticated_users = len(auth_tokens_df) if auth_tokens_df is not None else 0
auth_rate = (authenticated_users / total_users * 100) if total_users > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("총 가입 사용자 수", f"{total_users} 명")
col2.metric("캘린더 인증 완료 사용자", f"{authenticated_users} 명")
col3.metric("인증 전환율", f"{auth_rate:.1f} %")

st.divider()

# 2.2. 사용자 참여 및 활성도
st.subheader("📈 사용자 참여 및 활성도")

if not function_usage_df.empty:
    chart = alt.Chart(function_usage_df).mark_area(opacity=0.7, interpolate='monotone').encode(
        x=alt.X('date:T', title='날짜'),
        y=alt.Y('count:Q', stack='zero', title='호출 수'),
        color=alt.Color('function_name:N', title='기능', scale=alt.Scale(scheme='category10'))
    ).properties(title='일별 핵심 기능 사용량 추이 (성공 기준)').interactive()
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("아직 기능 사용 기록이 없습니다.")


# 2.3. AI 성능 및 품질
st.subheader("🤖 AI 성능 및 품질")

if event_history_df is not None and not event_history_df.empty:
    st.markdown("#### 컨텍스트 이해 기능 사용 현황")
    context_usage_df = event_history_df.copy()
    context_usage_df['date'] = context_usage_df['updated_at'].dt.date
    daily_context_usage = context_usage_df.groupby('date').size().reset_index(name='count')
    
    context_chart = alt.Chart(daily_context_usage).mark_bar().encode(
        x=alt.X('date:T', title='날짜'),
        y=alt.Y('count:Q', title='사용 횟수')
    ).properties(title='일별 컨텍스트 기반 요청 수 ("그 일정", "아까 회의" 등)').interactive()
    st.altair_chart(context_chart, use_container_width=True)
else:
    st.markdown("#### 컨텍스트 이해 기능 사용 현황")
    st.write("아직 컨텍스트 기반 요청 기록이 없습니다.")

if not ai_performance_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        success_rate_chart = alt.Chart(ai_performance_df).mark_line(point=True, color='green').encode(
            x=alt.X('date:T', title='날짜'),
            y=alt.Y('success_rate:Q', title='성공률 (%)', scale=alt.Scale(domain=[0, 100])),
        ).properties(title='Function Calling 성공률')
        st.altair_chart(success_rate_chart, use_container_width=True)

    with col2:
        slot_filling_df = ai_performance_df[['date', 'slot_filling']].copy()
        slot_filling_chart = alt.Chart(slot_filling_df).mark_bar(color='orange').encode(
            x=alt.X('date:T', title='날짜'),
            y=alt.Y('slot_filling:Q', title='요청 수'),
        ).properties(title='일별 정보 보완(Slot-filling) 요청 수')
        st.altair_chart(slot_filling_chart, use_container_width=True)
else:
    st.info("아직 AI 성능 관련 로그가 없습니다.")

st.divider()

# 2.4. 시스템 상태 및 API
st.subheader("⚙️ 시스템 상태 및 API")
st.warning("Google Calendar API 에러율 및 할당량은 **Google Cloud Console**에서 직접 모니터링하는 것이 가장 정확합니다.")