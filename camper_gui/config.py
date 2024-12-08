from pydantic_settings import BaseSettings
import platform


class Settings(BaseSettings):
    api_base: str = "http://localhost:8000"


class DebugSettings(Settings):
    api_base: str = "http://192.168.68.167:8000"


class ProductionSettings(Settings):
    pass


if platform.machine() == "x86_64":
    settings = DebugSettings()
else:
    settings = ProductionSettings()
