"""
이동평균 교차 (MA Cross) 전략
단기 이동평균이 장기 이동평균을 상향 돌파할 때 매수,
하향 돌파할 때 매도하는 추세 추종 전략
"""
import logging
from typing import Dict, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MACrossStrategy:
    """
    이동평균 교차 전략
    파라미터:
    - short_window (int): 단기 이동평균 기간 (기본 20일)
    - long_window  (int): 장기 이동평균 기간 (기본 60일)
    """

    def __init__(self, params: Dict[str, Any] | None = None):
        p = params or {}
        self.short_window: int = int(p.get("short_window", 20))
        self.long_window: int = int(p.get("long_window", 60))

        if self.short_window >= self.long_window:
            raise ValueError("단기 이동평균 기간은 장기보다 짧아야 합니다.")

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        이동평균 교차 시그널 생성
        반환: signal 컬럼 추가된 DataFrame (1=매수, -1=매도, 0=홀드)
        """
        result = df.copy()

        # 이동평균 계산
        result["ma_short"] = result["Close"].rolling(window=self.short_window).mean()
        result["ma_long"] = result["Close"].rolling(window=self.long_window).mean()

        # 이동평균 계산이 완료된 행부터 시그널 생성
        result["signal"] = 0

        # 단기 MA가 장기 MA 위에 있으면 매수 포지션 (1)
        result.loc[result["ma_short"] > result["ma_long"], "signal"] = 1

        # 교차 발생 지점만 거래 시그널로 표시
        # 이전 포지션과 달라진 지점 = 실제 매수/매도 시점
        result["position"] = result["signal"].diff()

        # NaN 제거 (이동평균 계산 전 구간)
        result.dropna(inplace=True)

        logger.debug(
            f"MA Cross 시그널 생성 완료: "
            f"MA{self.short_window}/{self.long_window}, {len(result)}행"
        )
        return result

    def get_params(self) -> Dict[str, Any]:
        """현재 전략 파라미터 반환"""
        return {
            "short_window": self.short_window,
            "long_window": self.long_window,
        }
