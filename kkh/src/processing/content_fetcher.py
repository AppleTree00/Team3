import logging
import requests
from bs4 import BeautifulSoup

from newspaper import Article as NewspaperArticle
logger = logging.getLogger(__name__)

def fetch_article_content(url: str) -> str | None:
    """
    주어진 URL에서 기사 본문을 스크래핑합니다.
    간단한 구현으로, 여러 언론사 구조에 완벽하게 대응하지 못할 수 있습니다.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding # 인코딩 자동 감지

        soup = BeautifulSoup(response.text, "html.parser")

        # 일반적인 기사 본문 컨테이너 선택자들 (언론사마다 다를 수 있음)
        selectors = [
            "article", "#articleBodyContents", "#dic_area", ".article_body", "#newsct_article", "#articeBody",
        ]
        
        content_element = None
        for selector in selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
        
        if content_element:
            # 불필요한 태그(광고, 관련기사 링크 등) 제거
            for ad_selector in [".ad_wrap", ".ad-template", ".ad_box", "script", "style"]:
                for tag in content_element.select(ad_selector):
                    tag.decompose()
            return content_element.get_text(separator="\n", strip=True)
        else:
            # 기본 선택자로 본문을 찾지 못한 경우, newspaper3k를 fallback으로 사용
            logger.warning(f"기본 선택자로 본문을 찾지 못했습니다. Fallback(newspaper3k) 시도: {url}")
            try:
                article = NewspaperArticle(url)
                # 이미 response.text가 있으므로 다시 다운로드하지 않고 html을 직접 전달
                article.download(input_html=response.text)
                article.parse()
                return article.text
            except Exception as e:
                logger.error(f"Newspaper3k fallback 처리 중 오류 발생: {url}, 오류: {e}")
                return None

    except requests.exceptions.RequestException as e:
        logger.warning(f"기사 본문 스크래핑 중 오류 발생: {url}, 오류: {e}")
        return None
    except Exception as e:
        logger.error(f"스크래핑 중 예상치 못한 오류 발생: {url}, 오류: {e}")
        return None