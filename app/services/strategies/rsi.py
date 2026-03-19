"""
RSI (Relative Strength Index) 전략
RSI가 과매도 구간 아래로 내려갈 때 매수,
과매수 구간 위로 올라갈 때 매도하는 역추세 전략
"""
import logging
from typing import Dict, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class RSIStrategy:
    """
    RSI 과매수/과매도 전략
    파라미터:
    - period     (int): RSI 계산 기간 (기본 14일)
    - oversold   (int): 과매도 기준선 (기본 30) → 이 아래에서 매수
    - overbought (int): 과매수 기준선 (기본 70) → 이 위에서 매도
    """

    def __init__(self, params: Dict[str, Any] | None = None):
        p = params or {}
        self.period: int = int(p.get("period", 14))
        self.oversold: int = int(p.get("oversold", 30))
        self.overbought: int = int(p.get("overbought", 70))

        if self.oversold >= self.overbought:
            raise ValueError("과매도 기준선은 과매수 기준선보다 낮아야 합니다.")

    @staticmethod
    def _compute_rsi(close: pd.Series, period: int) -> pd.Series:
        """
        Wilder's RSI 계산
        - 상승폭/하락폭 평균을 이용한 상대강도 지수
        """
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        # Wilder's smoothing (EMA with alpha=1/period)
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        RSI 시그널 생성
        반환: signal 컬럼 추가된 DataFrame (1=매수, -1=매도, 0=홀드)
        """
        result = df.copy()
        result["rsi"] = self._compute_rsi(result["Close"], self.period)

        result["signal"] = 0

        # 과매도 구간 (RSI < oversold): 매수 시그널
        result.loc[result["rsi"] < self.oversold, "signal"] = 1

        # 과매수 구간 (RSI > overbought): 매도 시그널
        result.loc[result["rsi"] > self.overbought, "signal"] = -1

        # 실제 포지션 변화 지점 계산
        result["position"] = result["signal"].diff()

        result.dropna(inplace=True)

        logger.debug(
            f"RSI 시그널 생성 완료: period={self.period}, "
            f"oversold={self.oversold}, overbought={self.overbought}"
        )
        return result

    def get_params(self) -> Dict[str, Any]:
        """현재 전략 파라미터 반환"""
        return {
            "period": self.period,
            "oversold": self.oversold,
            "overbought": self.overbought,
        }
