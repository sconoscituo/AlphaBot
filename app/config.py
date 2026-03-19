"""
AlphaBot 애플리케이션 설정 관리
환경변수를 읽어 전역 설정으로 제공
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Gemini AI API 키
    gemini_api_key: str = ""

    # 데이터베이스 연결 URL
    database_url: str = "sqlite+aiosqlite:///./alphabot.db"

    # JWT 시크릿 키
    secret_key: str = "change-this-secret-key-in-production"

    # JWT 알고리즘
    algorithm: str = "HS256"

    # 액세스 토큰 만료 시간 (분)
    access_token_expire_minutes: int = 60 * 24  # 24시간

    # 디버그 모드
    debug: bool = True

    # 앱 이름
    app_name: str = "AlphaBot"

    # 무료 사용자 백테스팅 최대 기간 (년)
    free_backtest_years: int = 3

    # 프리미엄 사용자 백테스팅 최대 기간 (년)
    premium_backtest_years: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환 (캐시됨)"""
    return Settings()
