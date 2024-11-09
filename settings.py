from pydantic_settings import BaseSettings
from typing import Any, Optional

class Settings(BaseSettings):
    POSTGRES_USER: str | Any=None
    POSTGRES_PASSWORD: str | Any=None
    POSTGRES_DB: str | Any=None
    POSTGRES_HOST: str | Any=None
    POSTGRES_PORT: int=34748
    SECRET_KEY: str | Any=None
    ACCESS_TOKEN_EXPIRE_MINUTES: int=120
    ALGORITHM: str | Any=None
    ADMIN_USERNAME: str="1"
    ADMIN_PASSWORD: str="1"
    ADMIN_EMAIL: str="amirsazegar16@gmail.com"
    AUTH_TOKEN: Optional[str] = None
    HMAC_SECRET_KEY: Optional[str] = None
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None
    MINIO_USE_SSL: bool=True
    MINIO_BUCKET_NAME: str
    CLIENT_KEY_PATH: str
    CLIENT_CERT_PATH: str
    CA_CERT_PATH: str


    class Config:
        env_file = ".env"


settings = Settings()
