import logging
import chromadb
from chromadb.utils import embedding_functions
from typing import List

from src.core.config import settings
from src.schemas.article import AnalyzedArticle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.OPENAI_API_KEY,
    model_name="text-embedding-ada-002"
)

collection = client.get_or_create_collection(
    name=settings.COLLECTION_NAME,
    embedding_function=openai_ef
)

def embed_and_store_articles(articles: List[AnalyzedArticle]):
    """
분석된 기사에 대한 임베딩을 생성하고 ChromaDB에 저장합니다.
    """
    if not articles:
        logger.info("임베딩 및 저장할 기사가 없습니다.")
        return

    try:
        ids = [article.url for article in articles]
        documents = [article.content for article in articles]
        metadatas = [article.model_dump(exclude={'content'}) for article in articles]

        # ChromaDB 호환성을 위해 데이터 타입을 변환합니다.
        for meta in metadatas:
            meta['published_at'] = meta['published_at'].isoformat()
            if isinstance(meta.get('keywords'), list):
                meta['keywords'] = ", ".join(meta['keywords'])
        existing_ids = set(collection.get(ids=ids)['ids'])
        new_ids, new_documents, new_metadatas = [], [], []

        for i, article_id in enumerate(ids):
            if article_id not in existing_ids:
                new_ids.append(article_id)
                new_documents.append(documents[i])
                new_metadatas.append(metadatas[i])
        
        if new_ids:
            collection.add(ids=new_ids, documents=new_documents, metadatas=new_metadatas)
            logger.info(f"{len(new_ids)}개의 새 기사를 성공적으로 임베딩하고 저장했습니다.")

    except Exception as e:
        logger.error(f"기사 임베딩 및 저장 중 오류 발생: {e}")
        raise