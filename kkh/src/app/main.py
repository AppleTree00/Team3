import logging
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks

from src.app.pipeline import process_and_store_articles, run_pipeline
from src.app.search import find_similar_articles, search_articles_by_query
from src.core.db import get_news_collection
from src.processing.ingestion import fetch_news
from src.schemas.article import AnalyzedArticle

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI News Analysis Pipeline API",
    description="AI 뉴스를 수집, 분석하고 유사한 뉴스를 추천하는 API입니다.",
    version="1.0.0",
)


@app.post("/pipeline/run", status_code=202)
async def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    백그라운드에서 뉴스 처리 파이프라인을 실행합니다.
    """
    logger.info("파이프라인 실행 요청을 수신했습니다.")
    AI_KEYWORDS = [
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "LLM",
        "NPU",
        "OpenAI",
        "https://www.zdnet.co.kr/rss/all.xml",  # ZDNet Korea 전체기사 RSS
    ]
    background_tasks.add_task(run_pipeline, keywords=AI_KEYWORDS, page_size=20)
    return {"message": "뉴스 처리 파이프라인이 백그라운드에서 시작되었습니다."}


@app.post("/pipeline/run-sync", response_model=List[AnalyzedArticle])
async def trigger_pipeline_sync(background_tasks: BackgroundTasks):
    """
    대화형으로 파이프라인을 실행합니다.
    - 타임아웃을 방지하기 위해, 초기 키워드의 뉴스 중 일부(3개)만 즉시 처리하여 반환합니다.
    - 나머지 초기 뉴스와 다른 모든 키워드에 대한 처리는 백그라운드에서 계속합니다.
    """
    logger.info("대화형 파이프라인 실행 요청을 수신했습니다.")
    try:
        AI_KEYWORDS = [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "LLM",
            "NPU",
            "OpenAI",
            "https://www.zdnet.co.kr/rss/all.xml",  # ZDNet Korea 전체기사 RSS
        ]
        initial_keyword = AI_KEYWORDS[0]
        remaining_keywords = AI_KEYWORDS[1:]
        INITIAL_FETCH_SIZE = 10  # 초기 키워드에서 가져올 전체 기사 수
        SYNC_BATCH_SIZE = 3  # 동기적으로 처리할 기사 수

        logger.info(f"초기 키워드 '{initial_keyword}'에 대한 뉴스 수집 시작...")
        all_initial_articles = fetch_news(query=initial_keyword, page_size=INITIAL_FETCH_SIZE)

        if not all_initial_articles:
            logger.warning(f"초기 키워드 '{initial_keyword}'에 대한 뉴스를 찾지 못했습니다.")
            if remaining_keywords:
                background_tasks.add_task(run_pipeline, keywords=remaining_keywords, page_size=20)
            return []

        # 즉시 반환할 동기 처리 배치와 백그라운드 처리 배치를 분리
        sync_batch = all_initial_articles[:SYNC_BATCH_SIZE]
        background_batch = all_initial_articles[SYNC_BATCH_SIZE:]

        logger.info(f"즉시 반환을 위해 {len(sync_batch)}개 기사를 동기적으로 처리합니다.")
        analyzed_articles = process_and_store_articles(sync_batch)
        logger.info(f"초기 동기 배치 처리 완료. {len(analyzed_articles)}개 기사 반환.")

        # 나머지 작업들을 백그라운드로 넘깁니다.
        # 1. 초기 키워드에서 남은 기사들 처리
        # 2. 다른 모든 키워드들에 대한 파이프라인 실행
        logger.info("나머지 기사 및 키워드에 대한 처리를 백그라운드에서 시작합니다.")
        background_tasks.add_task(process_and_store_articles, articles=background_batch)
        if remaining_keywords:
            background_tasks.add_task(run_pipeline, keywords=remaining_keywords, page_size=20)
        return analyzed_articles
    except Exception as e:
        logger.error(f"파이프라인 대화형 실행 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"파이프라인 실행 중 오류가 발생했습니다: {str(e)}")

@app.get("/news", response_model=List[Dict[str, Any]])
async def get_latest_news(limit: int = 10):
    """
    DB에 저장된 최신 뉴스 기사 목록을 반환합니다.
    """
    try:
        collection = get_news_collection()
        # 개선: 메모리 내 정렬을 위해 고정된 수의 최근 문서를 가져옵니다.
        # ChromaDB는 메타데이터 정렬을 직접 지원하지 않으므로 이는 차선책입니다.
        results = collection.get(limit=200, include=["metadatas"])

        if not results or not results["ids"]:
            return []

        # published_at 기준으로 내림차순 정렬
        sorted_metadatas = sorted(
            results["metadatas"], key=lambda x: x.get("published_at", ""), reverse=True
        )

        return sorted_metadatas[:limit]

    except Exception as e:
        logger.error(f"최신 뉴스 조회 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")


@app.get("/news/search", response_model=List[Dict[str, Any]])
async def search_news(q: str, limit: int = 10):
    """
    주어진 쿼리(키워드)와 의미적으로 유사한 뉴스 기사를 검색합니다.
    """
    if not q:
        raise HTTPException(status_code=400, detail="쿼리 파라미터 'q'가 필요합니다.")

    try:
        return search_articles_by_query(query=q, top_k=limit)
    except Exception as e:
        logger.error(f"뉴스 검색 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")


@app.get("/news/similar", response_model=List[Dict[str, Any]])
async def get_similar_news(url: str, top_k: int = 5):
    """
    주어진 URL의 기사와 유사한 뉴스 기사 목록을 반환합니다.
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL 파라미터가 필요합니다.")

    try:
        return find_similar_articles(article_url=url, top_k=top_k)
    except Exception as e:
        logger.error(f"유사 뉴스 검색 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")