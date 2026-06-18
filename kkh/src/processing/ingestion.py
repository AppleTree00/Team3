import logging
import re
from typing import List
from urllib.parse import urlparse
import feedparser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from src.schemas.article import Article
from src.processing.content_fetcher import fetch_article_content

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_news(query: str, page_size: int = 20) -> List[Article]:
    """
    Google News RSS 피드 또는 직접 제공된 RSS URL을 사용하여 뉴스 기사를 가져옵니다.
    - query가 http/https로 시작하면 직접 RSS URL로 간주합니다.
    - 그렇지 않으면 Google News 검색 쿼리로 간주합니다.
    """
    try:
        # query가 URL 형식인지 확인하여 직접 RSS 피드로 처리할지, Google News 검색으로 처리할지 결정
        if query.startswith("http://") or query.startswith("https"):
            url = query
            logger.info(f"지정된 RSS 피드에서 뉴스 수집을 시작합니다: {url}")
        else:
            # Google News RSS URL. hl(언어), gl(국가), ceid는 한국 설정입니다.
            url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
            logger.info(f"Google News RSS 피드에서 '{query}' 쿼리로 뉴스 수집을 시작합니다.")

        feed = feedparser.parse(url)

        if feed.bozo:
            logger.warning(f"RSS 피드 파싱에 문제가 발생했습니다: {url}. 원인: {feed.bozo_exception}")
        
        items = feed.entries[:page_size]

        # 병렬 스크래핑을 위해 스크래핑할 아이템과 링크를 미리 준비합니다.
        items_to_scrape = [item for item in items if item.link]
        links_to_scrape = [item.link for item in items_to_scrape]
        
        # ThreadPoolExecutor를 사용하여 기사 본문을 병렬로 가져옵니다.
        scraped_content_map = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_link = {executor.submit(fetch_article_content, link): link for link in links_to_scrape}
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    scraped_content_map[link] = future.result()
                except Exception as exc:
                    logger.error(f"'{link}' 콘텐츠 스크래핑 중 오류 발생: {exc}")
                    scraped_content_map[link] = None

        articles = []
        for item in items_to_scrape:
            # HTML 태그와 &quot;를 제거합니다.
            title = re.sub(r"<[^>]+>|&quot;", "", item.title)
            description = re.sub(r"<[^>]+>|&quot;", "", item.get("summary", ""))

            # published_parsed는 time.struct_time 객체입니다. datetime 객체로 변환합니다.
            try:
                published_dt = datetime.fromtimestamp(time.mktime(item.published_parsed))
            except AttributeError:
                logger.warning(f"'{title}' 기사에 발행일 정보가 없어 현재 시간으로 대체합니다.")
                published_dt = datetime.now()

            # 병렬로 스크래핑된 본문 내용을 가져옵니다.
            full_content = scraped_content_map.get(item.link)
            # 스크래핑 실패 시 설명으로 대체합니다.
            content_to_use = full_content if full_content else description

            if not content_to_use:
                logger.warning(f"'{title}' 기사의 본문 내용을 수집하지 못해 건너뜁니다.")
                continue

            article_data = {
                "title": title,
                "url": item.link,
                "description": description,
                "content": content_to_use,
                "published_at": published_dt,
                "source": urlparse(item.link).netloc,
            }
            articles.append(Article(**article_data))

        logger.info(f"'{query}'로부터 {len(articles)}개의 새 기사를 가져왔습니다.")
        return articles
    except Exception as e:
        logger.error(f"뉴스 수집 중 오류 발생: {e}")
        return []