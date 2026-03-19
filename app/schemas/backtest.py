"""
백테스팅 관련 Pydantic 스키마
API 요청/응답 직렬화 및 유효성 검사
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ─── 전략 스키마 ───────────────────────────────────────────

class StrategyCreate(BaseModel):
    """전략 저장 요청 스키마"""
    name: str = Field(..., min_length=1, max_length=200, description="전략 이름")
    strategy_type: str = Field(..., description="전략 유형 (ma_cross/rsi/ai_generated)")
    params_json: str = Field(default="{}", description="전략 파라미터 JSON 문자열")
    description: Optional[str] = Field(None, description="전략 설명")


class StrategyResponse(BaseModel):
    """전략 응답 스키마"""
    id: int
    user_id: int
    name: str
    strategy_type: str
    params_json: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── 백테스트 요청 스키마 ──────────────────────────────────

class BacktestRequest(BaseModel):
    """백테스팅 실행 요청 스키마"""
    ticker: str = Field(
        ...,
        description="종목 티커 (예: 005930.KS, AAPL)",
        example="005930.KS",
    )
    strategy: str = Field(
        ...,
        description="전략 유형 (ma_cross / rsi / ai_generated)",
        example="ma_cross",
    )
    start_date: str = Field(
        ...,
        description="백테스트 시작일 (YYYY-MM-DD)",
        example="2021-01-01",
    )
    end_date: str = Field(
        ...,
        description="백테스트 종료일 (YYYY-MM-DD)",
        example="2023-12-31",
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="전략 파라미터 (전략마다 다름)",
        example={"short_window": 20, "long_window": 60},
    )
    save_strategy: bool = Field(
        default=False,
        description="전략을 저장할지 여부",
    )
    strategy_name: Optional[str] = Field(
        default=None,
        description="저장할 전략 이름 (save_strategy=True일 때 필요)",
    )


# ─── 백테스트 결과 스키마 ──────────────────────────────────

class BacktestResultResponse(BaseModel):
    """백테스팅 결과 응답 스키마"""
    id: int
    ticker: str
    strategy_type: str
    start_date: date
    end_date: date

    # 성과 지표
    total_return: float = Field(..., description="총 수익률 (%)")
    annual_return: float = Field(..., description="연환산 수익률 CAGR (%)")
    mdd: float = Field(..., description="최대낙폭 MDD (%, 음수)")
    sharpe: float = Field(..., description="샤프지수")
    total_trades: int = Field(..., description="총 거래 횟수")
    win_rate: float = Field(..., description="승률 (%)")

    params_json: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BacktestListResponse(BaseModel):
    """백테스팅 결과 목록 응답"""
    total: int
    items: List[BacktestResultResponse]


# ─── 사용자 스키마 ─────────────────────────────────────────

class UserCreate(BaseModel):
    """사용자 등록 요청 스키마"""
    email: str = Field(..., description="이메일 주소")
    username: str = Field(..., min_length=2, max_length=50, description="사용자 이름")
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    email: str
    username: str
    is_active: bool
    is_premium: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """토큰 페이로드 스키마"""
    email: Optional[str] = None
