"""
백테스터 서비스
전략 시그널을 기반으로 매수/매도를 시뮬레이션하고
수익률, MDD, 샤프지수 등 성과 지표를 계산
"""
import json
import logging
from datetime import date
from typing import Dict, Any, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# 연간 거래일 수 (샤프지수 연환산에 사용)
TRADING_DAYS_PER_YEAR = 252

# 무위험 수익률 (샤프지수 계산 기준, 한국 국채 기준 약 3.5%)
RISK_FREE_RATE_ANNUAL = 0.035


def _calculate_mdd(equity_curve: pd.Series) -> float:
    """
    최대 낙폭 (Maximum Drawdown) 계산
    - 고점 대비 최대 하락률 (음수 %로 표현)
    """
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max * 100
    return float(drawdown.min())


def _calculate_sharpe(daily_returns: pd.Series) -> float:
    """
    샤프지수 계산 (연환산)
    - (평균 일간 수익률 - 무위험 수익률) / 일간 수익률 표준편차 * sqrt(252)
    """
    if daily_returns.std() == 0:
        return 0.0

    daily_rf = RISK_FREE_RATE_ANNUAL / TRADING_DAYS_PER_YEAR
    excess_return = daily_returns.mean() - daily_rf
    sharpe = (excess_return / daily_returns.std()) * np.sqrt(TRADING_DAYS_PER_YEAR)
    return float(sharpe)


def _calculate_cagr(total_return_pct: float, days: int) -> float:
    """
    연환산 수익률 (CAGR) 계산
    - total_return_pct: 총 수익률 (%)
    - days: 백테스트 기간 (일)
    """
    if days <= 0:
        return 0.0
    years = days / 365.0
    total_return_decimal = total_return_pct / 100
    if total_return_decimal <= -1:
        return -100.0
    cagr = ((1 + total_return_decimal) ** (1 / years) - 1) * 100
    return float(cagr)


def run_backtest(
    df_signals: pd.DataFrame,
    initial_capital: float = 10_000_000,  # 초기 자본 1천만원
) -> Dict[str, Any]:
    """
    시그널 DataFrame으로 매매 시뮬레이션 실행
    - df_signals: generate_signals() 반환값 (signal, position 컬럼 포함)
    - initial_capital: 시뮬레이션 초기 자본 (원)

    반환:
    {
        "total_return": 총 수익률(%),
        "annual_return": 연환산 수익률(%),
        "mdd": 최대낙폭(%),
        "sharpe": 샤프지수,
        "total_trades": 총 거래 횟수,
        "win_rate": 승률(%),
        "trades": [거래 내역 리스트],
        "equity_curve": [자산가치 시계열]
    }
    """
    capital = initial_capital
    position = 0          # 현재 보유 주식 수
    entry_price = 0.0     # 매수 진입 가격
    trades: List[Dict] = []
    equity_values: List[float] = []

    for idx, row in df_signals.iterrows():
        close = float(row["Close"])
        signal = int(row.get("signal", 0))
        position_change = float(row.get("position", 0))

        # 매수 시그널: 포지션 없을 때만 매수
        if position_change > 0 and position == 0 and signal == 1:
            # 전액 투자 (단순화)
            shares = int(capital / close)
            if shares > 0:
                position = shares
                entry_price = close
                capital -= shares * close
                trades.append({
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                    "type": "BUY",
                    "price": close,
                    "shares": shares,
                    "capital_left": round(capital, 2),
                })

        # 매도 시그널: 포지션 있을 때만 매도
        elif (position_change < 0 or signal == -1) and position > 0:
            sell_value = position * close
            pnl_pct = (close - entry_price) / entry_price * 100
            capital += sell_value
            trades.append({
                "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                "type": "SELL",
                "price": close,
                "shares": position,
                "pnl_pct": round(pnl_pct, 2),
                "capital": round(capital, 2),
            })
            position = 0
            entry_price = 0.0

        # 현재 포트폴리오 가치 (현금 + 주식 시가)
        portfolio_value = capital + position * close
        equity_values.append(portfolio_value)

    # 마지막에 포지션이 남아있으면 마지막 가격으로 청산
    if position > 0:
        last_close = float(df_signals["Close"].iloc[-1])
        capital += position * last_close
        position = 0

    # 성과 지표 계산
    final_capital = capital
    total_return = (final_capital - initial_capital) / initial_capital * 100

    equity_series = pd.Series(equity_values)
    daily_returns = equity_series.pct_change().dropna()

    # 백테스트 기간 계산
    start_dt = df_signals.index[0]
    end_dt = df_signals.index[-1]
    days = (end_dt - start_dt).days if hasattr(start_dt, "days") else 365

    # 승률 계산
    sell_trades = [t for t in trades if t["type"] == "SELL"]
    win_trades = [t for t in sell_trades if t.get("pnl_pct", 0) > 0]
    win_rate = (len(win_trades) / len(sell_trades) * 100) if sell_trades else 0.0

    result = {
        "total_return": round(total_return, 2),
        "annual_return": round(_calculate_cagr(total_return, days), 2),
        "mdd": round(_calculate_mdd(equity_series), 2) if len(equity_series) > 1 else 0.0,
        "sharpe": round(_calculate_sharpe(daily_returns), 3) if len(daily_returns) > 1 else 0.0,
        "total_trades": len(sell_trades),
        "win_rate": round(win_rate, 2),
        "trades": trades,
        "final_capital": round(final_capital, 2),
    }

    logger.info(
        f"백테스트 완료: 수익률={result['total_return']}%, "
        f"MDD={result['mdd']}%, 샤프={result['sharpe']}, "
        f"거래={result['total_trades']}회"
    )
    return result
