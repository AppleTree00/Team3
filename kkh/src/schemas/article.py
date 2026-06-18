from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Article(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    url: str
    published_at: datetime
    source: str

class AnalyzedArticle(Article):
    summary: str
    keywords: List[str]
    sentiment: str