import streamlit as st
import requests
import pandas as pd

# API 서버 주소 (로컬에서 실행 시)
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide", page_title="AI 뉴스 분석 서비스")

# --- 0. 관리자 기능 (사이드바) ---
with st.sidebar:
    st.header("⚙️ 관리자 기능")
    st.info(
        "뉴스 검색을 하기 전, 먼저 파이프라인을 실행하여 최신 뉴스를 데이터베이스에 저장해야 합니다."
    )
    if st.button("뉴스 파이프라인 실행"):
        with st.spinner("초기 뉴스를 수집/분석 중입니다... (약 10-20초 소요)"):
            try:
                # 1. 대화형 파이프라인 실행 API를 호출합니다.
                # 이 API는 초기 분석 결과를 즉시 반환하고, 나머지는 백그라운드에서 처리합니다.
                # 요청 타임아웃을 60초에서 120초로 늘려 긴 처리 시간을 기다립니다.
                response = requests.post(f"{API_BASE_URL}/pipeline/run-sync", timeout=120)
                response.raise_for_status()
                initial_news = response.json()

                if initial_news:
                    # 2. 반환된 초기 뉴스를 세션 상태에 저장하여 목록에 표시합니다.
                    st.session_state.news_list = initial_news
                    st.session_state.selected_article = None # 선택 초기화
                    st.success(f"초기 뉴스 {len(initial_news)}개를 성공적으로 불러왔습니다. 전체 파이프라인은 백그라운드에서 계속 실행됩니다.")
                else:
                    st.warning("처리할 수 있는 초기 뉴스를 찾지 못했습니다. 백엔드에서 뉴스 수집에 실패했을 수 있습니다.")
                    st.session_state.news_list = []

            except requests.exceptions.RequestException as e:
                st.error(f"파이프라인 실행 또는 뉴스 로딩에 실패했습니다: {e}")

st.title("📰 AI 뉴스 분석 서비스")
st.markdown(
    """
`ui.md` 가이드라인에 따라 구현된 Streamlit 데모입니다.  
키워드로 최신 뉴스를 검색하고, 기사를 선택하여 요약 및 분석 결과를 확인하세요.
"""
)

# --- 1. 뉴스 검색 기능 ---
st.header("🔍 뉴스 검색")
keyword = st.text_input("검색할 키워드를 입력하세요 (예: LLM, NPU, OpenAI):", "OpenAI")

if st.button("의미 기반 뉴스 검색"):
    if keyword:
        try:
            # 백엔드 API의 검색 엔드포인트 호출
            response = requests.get(f"{API_BASE_URL}/news/search", params={"q": keyword, "limit": 20})
            response.raise_for_status()
            news_list = response.json()

            if news_list:
                # 검색 결과를 세션 상태에 저장
                st.session_state.news_list = news_list
                st.session_state.selected_article = None # 선택 초기화
                st.success(f"'{keyword}'와(과) 관련된 뉴스 {len(news_list)}개를 찾았습니다.")
            else:
                st.warning("검색 결과가 없습니다.")
                st.session_state.news_list = []

        except requests.exceptions.RequestException as e:
            st.error(f"API 서버에 연결할 수 없습니다. 백엔드 서버를 실행했는지 확인하세요. (오류: {e})")
    else:
        st.warning("검색할 키워드를 입력해주세요.")

# --- 2. 화면 레이아웃 (2단) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 검색된 뉴스 목록")
    if "news_list" in st.session_state and st.session_state.news_list:

        # QA 제안 및 ui.md 가이드에 따라 뉴스 목록을 DataFrame으로 변환하여 테이블로 표시
        df = pd.DataFrame(st.session_state.news_list)
        df_display = df[["title", "source", "published_at"]].rename(
            columns={"title": "제목", "source": "출처", "published_at": "발행일"}
        )

        st.info("아래 목록에서 분석할 기사를 선택하세요.")

        # st.dataframe을 사용하여 테이블 형태로 뉴스 목록 표시 및 행 선택 기능 활성화
        event = st.dataframe(
            df_display,
            key="news_list_df",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
            use_container_width=True,
        )

        # 선택된 행이 있으면 해당 기사 정보를 세션 상태에 저장
        if event.selection.rows:
            # event.selection.rows는 선택된 행의 인덱스 리스트입니다. (e.g., [0])
            selected_row_index = event.selection.rows[0]
            # 원본 데이터 리스트(st.session_state.news_list)에서 해당 인덱스의 전체 기사 정보를 가져옵니다.
            st.session_state.selected_article = st.session_state.news_list[selected_row_index]
    else:
        st.info("먼저 뉴스를 검색해주세요.")

with col2:
    st.subheader("✨ 기사 분석 및 추천")
    if st.session_state.get("selected_article"):
        article = st.session_state.selected_article
        
        st.markdown(f"#### {article['title']}")
        st.caption(f"출처: {article['source']} | 발행일: {article['published_at']}")
        st.markdown(f"[원문 링크]({article['url']})")

        # ui.md 가이드에 따라 expander 사용
        with st.expander("AI 요약 및 분석 결과 보기", expanded=True):
            st.markdown("**요약:**")
            st.write(article.get("summary", "요약 정보가 없습니다."))
            
            st.markdown("**키워드:**")
            st.write(", ".join(article.get("keywords", [])) or "키워드 정보가 없습니다.")

            st.markdown("**감성 분석:**")
            st.write(article.get("sentiment", "감성 분석 정보가 없습니다."))

        # 유사 뉴스 추천
        st.markdown("---")
        st.markdown("#### 🔗 관련 뉴스 추천")
        try:
            similar_response = requests.get(f"{API_BASE_URL}/news/similar", params={"url": article['url'], "top_k": 4})
            similar_response.raise_for_status()
            similar_articles = similar_response.json()

            if similar_articles:
                for sim_article in similar_articles:
                    with st.container(border=True):
                        st.markdown(f"**{sim_article['title']}** ({sim_article['source']})")
                        st.caption(f"유사도 점수: {sim_article['distance']:.2f} (낮을수록 유사)")
                        st.markdown(f"[기사 보기]({sim_article['url']})")
            else:
                st.info("관련 뉴스를 찾을 수 없습니다.")

        except requests.exceptions.RequestException as e:
            st.error(f"유사 뉴스 API 호출 중 오류가 발생했습니다: {e}")
    else:
        st.info("왼쪽 목록에서 분석할 기사를 선택해주세요.")