"""
주가 데이터 로더 서비스
yfinance를 이용해 과거 주가 데이터를 DataFrame으로 반환
"""
import asyncio
import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _fetch_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    yfinance로 OHLCV 데이터 동기 로드
    - ticker: 종목 코드 (예: 005930.KS, AAPL)
    - start/end: YYYY-MM-DD 형식
    반환: 날짜 인덱스를 가진 DataFrame (Open, High, Low, Close, Volume)
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(start=start, end=end, auto_adjust=True)

        if df.empty:
            raise ValueError(f"'{ticker}'에 대한 데이터가 없습니다. 티커를 확인하세요.")

        # 인덱스를 timezone-naive로 변환 (비교 연산 편의)
        df.index = df.index.tz_localize(None)

        # 필요한 컬럼만 유지
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)

        logger.info(f"데이터 로드 완료: {ticker} ({len(df)}행, {start} ~ {end})")
        return df

    except Exception as e:
        logger.error(f"데이터 로드 실패 ({ticker}): {e}")
        raise


async def load_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    비동기 래퍼 — yfinance(동기)를 스레드 풀에서 실행
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_ohlcv, ticker, start, end)


def validate_date_range(
    start_date: str,
    end_date: str,
    is_premium: bool,
) -> tuple[str, str]:
    """
    날짜 범위 유효성 검사 및 조정
    - 무료 사용자: 최근 3년까지만 허용
    - 프리미엄 사용자: 최근 10년까지 허용
    반환: (검증된 start_date, end_date) 튜플
    """
    max_years = settings.premium_backtest_years if is_premium else settings.free_backtest_years
    earliest_allowed = datetime.now() - timedelta(days=365 * max_years)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # 무료 사용자 기간 초과 시 자동 조정
    if start_dt < earliest_allowed:
        start_dt = earliest_allowed
        logger.info(f"무료 플랜 기간 제한으로 시작일 조정: {start_dt.date()}")

    if end_dt <= start_dt:
        raise ValueError("종료일은 시작일 이후여야 합니다.")

    return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")
