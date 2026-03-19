"""
AlphaBot 기본 동작 테스트
FastAPI TestClient로 주요 엔드포인트 및 백테스팅 로직 검증
"""
import json
from datetime import date, timedelta

import pandas as pd
import numpy as np
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import get_db, Base
from app.services.strategies.ma_cross import MACrossStrategy
from app.services.strategies.rsi import RSIStrategy
from app.services.backtester import run_backtest

# 테스트용 인메모리 SQLite DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """테스트용 DB 세션 오버라이드"""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(autouse=True)
async def setup_db():
    """각 테스트 전 테이블 생성, 후 삭제"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


def _make_dummy_ohlcv(n: int = 200) -> pd.DataFrame:
    """테스트용 더미 OHLCV DataFrame 생성"""
    dates = pd.date_range(start="2022-01-01", periods=n, freq="B")
    np.random.seed(42)
    close = 50000 + np.cumsum(np.random.randn(n) * 500)
    close = np.maximum(close, 10000)
    df = pd.DataFrame({
        "Open": close * 0.99,
        "High": close * 1.01,
        "Low": close * 0.98,
        "Close": close,
        "Volume": np.random.randint(100000, 1000000, n),
    }, index=dates)
    return df


# ─── API 테스트 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check():
    """헬스체크 엔드포인트 정상 응답 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root():
    """루트 엔드포인트 서비스명 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "AlphaBot"


@pytest.mark.asyncio
async def test_register_and_login():
    """회원가입 후 로그인 토큰 발급 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg = await client.post(
            "/api/users/register",
            json={"email": "test@ab.com", "username": "테스터", "password": "pass1234"},
        )
        assert reg.status_code == 201

        login = await client.post(
            "/api/users/login",
            data={"username": "test@ab.com", "password": "pass1234"},
        )
        assert login.status_code == 200
        assert "access_token" in login.json()


@pytest.mark.asyncio
async def test_backtest_requires_auth():
    """인증 없이 백테스트 실행 시 401 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/backtest/run",
            json={
                "ticker": "AAPL",
                "strategy": "ma_cross",
                "start_date": "2022-01-01",
                "end_date": "2023-01-01",
            },
        )
    assert response.status_code == 401


# ─── 전략 유닛 테스트 ──────────────────────────────────────

def test_ma_cross_signals():
    """이동평균 교차 전략 시그널 생성 확인"""
    df = _make_dummy_ohlcv(200)
    strategy = MACrossStrategy({"short_window": 20, "long_window": 60})
    result = strategy.generate_signals(df)

    assert "signal" in result.columns
    assert "position" in result.columns
    assert "ma_short" in result.columns
    assert "ma_long" in result.columns
    # 시그널은 0, 1 값만 가져야 함
    assert set(result["signal"].unique()).issubset({0, 1})


def test_ma_cross_invalid_params():
    """단기 MA >= 장기 MA 시 ValueError 발생 확인"""
    with pytest.raises(ValueError):
        MACrossStrategy({"short_window": 60, "long_window": 20})


def test_rsi_signals():
    """RSI 전략 시그널 생성 확인"""
    df = _make_dummy_ohlcv(200)
    strategy = RSIStrategy({"period": 14, "oversold": 30, "overbought": 70})
    result = strategy.generate_signals(df)

    assert "rsi" in result.columns
    assert "signal" in result.columns
    # RSI 값은 0~100 범위여야 함
    assert result["rsi"].between(0, 100).all()


def test_rsi_invalid_params():
    """과매도 >= 과매수 시 ValueError 발생 확인"""
    with pytest.raises(ValueError):
        RSIStrategy({"oversold": 70, "overbought": 30})


def test_backtester_returns_metrics():
    """백테스터 성과 지표 계산 확인"""
    df = _make_dummy_ohlcv(200)
    strategy = MACrossStrategy({"short_window": 10, "long_window": 30})
    df_signals = strategy.generate_signals(df)
    result = run_backtest(df_signals, initial_capital=10_000_000)

    # 모든 필수 지표가 존재해야 함
    assert "total_return" in result
    assert "annual_return" in result
    assert "mdd" in result
    assert "sharpe" in result
    assert "total_trades" in result
    assert "win_rate" in result
    assert isinstance(result["total_return"], float)
    assert result["mdd"] <= 0  # MDD는 항상 0 이하
    assert 0 <= result["win_rate"] <= 100
