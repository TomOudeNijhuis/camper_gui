from pydantic_settings import BaseSettings
import platform


class Settings(BaseSettings):
    # api_base: str = "http://localhost:8000"
    # api_base: str = "http://192.168.1.175:8000"
    api_base: str = "http://192.168.28.84:8000"


settings = Settings()
