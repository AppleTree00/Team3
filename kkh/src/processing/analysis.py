import logging
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field

from src.core.config import settings
from src.schemas.article import Article, AnalyzedArticle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-3.5-turbo")

class AnalysisResult(BaseModel):
    summary: str = Field(description="뉴스 기사의 핵심 내용을 3-4 문장으로 요약")
    keywords: List[str] = Field(description="기사와 가장 관련성 높은 키워드 5개 목록", max_items=5)
    sentiment: str = Field(description="기사의 전반적인 감성 (예: Positive, Negative, Neutral)")

output_parser = PydanticOutputParser(pydantic_object=AnalysisResult)

ANALYSIS_TEMPLATE = """
다음 뉴스 기사 내용을 분석하여 다음을 제공해 주세요:
1. 기사의 핵심 내용을 3-4 문장으로 요약.
2. 가장 관련성 높은 키워드 5개.
3. 기사의 전반적인 감성 (예: Positive, Negative, Neutral).

{format_instructions}

기사:
{content}
"""

def analyze_news_content(article: Article) -> AnalyzedArticle:
    """
단일 뉴스 기사를 분석하여 요약, 키워드, 감성을 생성합니다.
    """
    try:
        logger.info(f"기사 분석 중: {article.title}")

        analysis_prompt = ChatPromptTemplate.from_template(
            template=ANALYSIS_TEMPLATE,
            partial_variables={"format_instructions": output_parser.get_format_instructions()}
        )
        analysis_chain = analysis_prompt | llm | output_parser
        analysis_result: AnalysisResult = analysis_chain.invoke({"content": article.content})

        return AnalyzedArticle(
            **article.model_dump(),
            summary=analysis_result.summary,
            keywords=analysis_result.keywords,
            sentiment=analysis_result.sentiment
        )
    except Exception as e:
        logger.error(f"'{article.title}' 기사 분석 중 오류 발생: {e}")
        raise