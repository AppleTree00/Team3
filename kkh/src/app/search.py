import logging
from typing import List, Dict, Any

from src.core.db import get_news_collection
from src.processing.embedding import openai_ef

logger = logging.getLogger(__name__)


def _format_search_results(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Helper function to format ChromaDB query results."""
    articles = []
    # 'ids'가 존재하고, 그 첫 번째 리스트가 비어있지 않은지 확인합니다.
    if not results or not results.get("ids") or not results["ids"][0]:
        return []

    # 쿼리 결과는 2차원 리스트이므로 첫 번째 요소를 사용합니다.
    result_ids = results["ids"][0]
    result_metadatas = results["metadatas"][0]
    result_distances = results["distances"][0]

    for i, doc_id in enumerate(result_ids):
        metadata = result_metadatas[i]
        distance = result_distances[i]

        # DB에 문자열로 저장된 키워드를 다시 리스트로 변환합니다.
        keywords_val = metadata.get("keywords", "")
        if isinstance(keywords_val, str) and keywords_val:
            metadata["keywords"] = [k.strip() for k in keywords_val.split(",")]
        else:
            metadata["keywords"] = []

        articles.append(
            {**metadata, "distance": distance}
        )
    return articles


def find_similar_articles(article_url: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    주어진 기사 URL과 유사한 기사를 ChromaDB에서 검색합니다.

    Args:
        article_url (str): 유사도 검색의 기준이 될 기사의 URL.
        top_k (int): 반환할 유사 기사의 수.

    Returns:
        List[Dict[str, Any]]: 검색된 유사 기사 정보 딕셔너리 리스트.
    """
    try:
        collection = get_news_collection()
    except Exception as e:
        logger.error(f"ChromaDB 컬렉션을 가져오는 중 오류 발생: {e}", exc_info=True)
        return []

    try:
        # 1. 기준 기사의 임베딩을 DB에서 가져옵니다.
        target_article = collection.get(ids=[article_url], include=["embeddings"])

        if not target_article.get("ids"):
            logger.warning(f"기준 기사 '{article_url}'를 DB에서 찾을 수 없습니다.")
            return []

        target_embedding = target_article["embeddings"][0]

        # 2. 가져온 임베딩을 사용하여 유사한 기사를 쿼리합니다.
        results = collection.query(query_embeddings=[target_embedding], n_results=top_k + 1)

        if not results or not results["ids"][0]:
            logger.info(f"'{article_url}'에 대한 유사 기사를 찾을 수 없습니다.")
            return []

        # 3. 결과에서 자기 자신을 제외하고 반환할 형태로 가공합니다.
        all_articles = _format_search_results(results)
        similar_articles = [
            article for article in all_articles if article["url"] != article_url
        ]

        logger.info(f"'{article_url}'에 대해 {len(similar_articles)}개의 유사 기사를 찾았습니다.")
        return similar_articles

    except Exception as e:
        logger.error(f"유사 기사 검색 중 오류 발생: {e}", exc_info=True)
        return []


def search_articles_by_query(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    주어진 텍스트 쿼리를 임베딩하여 의미적으로 유사한 기사를 ChromaDB에서 검색합니다.
    """
    try:
        collection = get_news_collection()
    except Exception as e:
        logger.error(f"ChromaDB 컬렉션을 가져오는 중 오류 발생: {e}", exc_info=True)
        return []

    try:
        # 1. 쿼리 텍스트를 임베딩으로 변환합니다.
        query_embedding = openai_ef([query])

        # 2. 생성된 임베딩을 사용하여 유사한 기사를 쿼리합니다.
        # openai_ef가 이미 리스트 형태의 임베딩(List[List[float]])을 반환하므로 추가로 리스트로 감싸지 않습니다.
        results = collection.query(query_embeddings=query_embedding, n_results=top_k)

        # ChromaDB는 결과가 없을 때 'ids': [[]]를 반환하므로, 내부 리스트가 비었는지 확인해야 합니다.
        if not results or not results["ids"][0]:
            logger.info(f"'{query}'에 대한 검색 결과가 없습니다.")
            return []

        # 3. 결과를 반환할 형태로 가공합니다.
        searched_articles = _format_search_results(results)

        logger.info(f"'{query}' 쿼리로 {len(searched_articles)}개의 기사를 찾았습니다.")
        return searched_articles

    except Exception as e:
        logger.error(f"쿼리 기반 기사 검색 중 오류 발생: {e}", exc_info=True)
        return []