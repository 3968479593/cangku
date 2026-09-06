from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI电商选品助手"
    DEBUG: bool = True

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "ecommerce_rag"
    DATABASE_URL: str = ""

    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    CHROMA_DENSE_COLLECTION: str = "products_dense"
    CHROMA_SPARSE_COLLECTION: str = "products_sparse"

    MODEL_CACHE_DIR: str = "./models"

    HF_ENDPOINT: str = ""

    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"

    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RRF_K: int = 60

    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    LLM_REASONER_MODEL: str = "deepseek-reasoner"

    RETRIEVAL_TOP_K: int = 10  # 候选数 20→10，重排序耗时减半（CPU 环境实测 4.6s→2.0s）
    RERANK_TOP_K: int = 5

    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # 认证
    SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
