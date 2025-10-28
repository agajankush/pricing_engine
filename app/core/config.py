from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "DynamicPricingEngine"
    WORKERS: int = 4
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENABLE_METRICS: bool = True
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
settings = Settings()

