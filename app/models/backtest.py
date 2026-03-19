"""
백테스팅 결과 ORM 모델
전략 실행 결과 (수익률, MDD, 샤프지수 등) 저장
"""
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Float, Integer, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BacktestResult(Base):
    """백테스팅 결과 테이블"""
    __tablename__ = "backtest_results"

    # 기본 키
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 소유자 FK
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 전략 FK (선택적 — 저장된 전략 없이 일회성 백테스트도 가능)
    strategy_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("strategies.id"), nullable=True
    )

    # 종목 티커 (예: 005930.KS, AAPL)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # 전략 유형
    strategy_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 백테스트 기간
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- 성과 지표 ---
    # 총 수익률 (%, 예: 45.3)
    total_return: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # 연환산 수익률 (CAGR, %)
    annual_return: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # 최대 낙폭 MDD (%, 음수 표현, 예: -25.4)
    mdd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # 샤프지수 (위험 대비 수익 효율)
    sharpe: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # 총 거래 횟수
    total_trades: Mapped[int] = mapped_column(Integer, default=0)

    # 승률 (%)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # 거래 내역 JSON (매수/매도 날짜·가격·수량)
    trades_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 전략 파라미터 JSON (결과와 함께 보관)
    params_json: Mapped[str] = mapped_column(Text, default="{}")

    # 백테스트 실행 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<BacktestResult id={self.id} ticker={self.ticker} "
            f"return={self.total_return:.1f}% mdd={self.mdd:.1f}%>"
        )
