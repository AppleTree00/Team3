import logging

import chromadb
from chromadb.types import Collection

from src.core.config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

# ChromaDB 클라이언트 초기화 (데이터를 디스크에 영구 저장)
# PersistentClient를 사용하여 지정된 경로에 데이터베이스 파일을 저장합니다.
# 이렇게 하면 애플리케이션을 재시작해도 데이터가 유지됩니다.
try:
    client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    logger.info(f"ChromaDB PersistentClient가 '{settings.CHROMA_DB_PATH}' 경로에서 성공적으로 초기화되었습니다.")
except Exception as e:
    logger.critical(f"ChromaDB 클라이언트 초기화 중 심각한 오류 발생: {e}", exc_info=True)
    client = None


def get_news_collection() -> Collection:
    """
    설정에 정의된 이름의 ChromaDB 컬렉션을 가져오거나 생성합니다.

    Returns:
        Collection: ChromaDB 컬렉션 객체.
    """
    if not client:
        raise Exception("ChromaDB client is not initialized.")

    collection = client.get_or_create_collection(name=settings.COLLECTION_NAME)
    return collection