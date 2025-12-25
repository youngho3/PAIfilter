import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "pai"
    PINECONE_ENV: str = "us-east-1"
    PINECONE_HOST: str = ""
    
    # .env 파일이 backend 디렉토리에 있다고 가정
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
