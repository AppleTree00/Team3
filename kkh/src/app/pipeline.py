import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from src.processing.ingestion import fetch_news
from src.processing.analysis import analyze_news_content
from src.processing.embedding import embed_and_store_articles
from src.schemas.article import AnalyzedArticle, Article

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_and_store_articles(articles: List[Article]) -> List[AnalyzedArticle]:
    """
    기사 목록을 분석하고, 데이터베이스에 저장한 후, 분석된 기사 목록을 반환합니다.
    """
    if not articles:
        logger.info("분석 및 저장할 기사가 없습니다.")
        return []

    unique_articles = list({article.url: article for article in articles}.values())
    logger.info(f"처리할 고유 기사 수: {len(unique_articles)}")

    analyzed_articles = []
    # ThreadPoolExecutor를 사용하여 기사 분석을 병렬로 실행합니다.
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_article = {executor.submit(analyze_news_content, article): article for article in unique_articles}
        for future in as_completed(future_to_article):
            article = future_to_article[future]
            try:
                analyzed_articles.append(future.result())
            except Exception as e:
                logger.warning(f"분석 오류로 인해 '{article.title}' 기사를 건너뜁니다: {e}")
    
    if analyzed_articles:
        embed_and_store_articles(analyzed_articles)
    
    return analyzed_articles


def run_pipeline(keywords: list[str], page_size: int = 20):
    """
키워드 목록에 대한 전체 데이터 처리 파이프라인을 실행합니다.
1. 각 키워드에 대한 뉴스를 가져옵니다.
2. 각 새 기사를 분석합니다.
3. 분석된 기사를 임베딩하고 저장합니다.
    """
    logger.info(f"파이프라인 실행 시작 (키워드: {keywords})...")
    start_time = time.time()

    all_new_articles = []
    for keyword in keywords:
        logger.info(f"키워드 처리 중: {keyword}")
        new_articles = fetch_news(query=keyword, page_size=page_size)
        all_new_articles.extend(new_articles)
    
    process_and_store_articles(all_new_articles)

    end_time = time.time()
    logger.info(f"파이프라인 실행 완료. 소요 시간: {end_time - start_time:.2f}초")

if __name__ == "__main__":
    AI_KEYWORDS = [
        "Artificial Intelligence",
        "Machine Learning",
        "OpenAI",
        "Deep Learning",
        "https://www.zdnet.co.kr/rss/all.xml",  # ZDNet Korea 전체기사 RSS
    ]
    run_pipeline(keywords=AI_KEYWORDS)