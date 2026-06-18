from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    OPENAI_API_KEY: str
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    CHROMA_DB_PATH: str = "data/chromadb"
    COLLECTION_NAME: str = "news_articles"

settings = Settings()