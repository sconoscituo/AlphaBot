"""
헥사고날 아키텍처 - AlphaBot Trading Service Port
트레이딩/투자 전략 도메인 서비스 추상 인터페이스
"""
from abc import abstractmethod
from typing import Any, Dict, List

from .base_service import AbstractService


class AbstractTradingService(AbstractService):
    """트레이딩 서비스 포트 - 구현체는 이 인터페이스를 따라야 함"""

    @abstractmethod
    async def get_signals(
        self,
        symbol: str,
        strategy: str,
        params: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        주어진 전략으로 매매 시그널 생성
        :param symbol: 종목 코드 (예: AAPL, 005930.KS)
        :param strategy: 전략명 (ma_cross, rsi, ai 등)
        :param params: 전략 파라미터
        :return: 매수/매도/홀드 시그널 및 신뢰도
        """
        ...

    @abstractmethod
    async def backtest_strategy(
        self,
        symbol: str,
        strategy: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        params: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        전략 백테스팅 실행
        :param symbol: 종목 코드
        :param strategy: 전략명
        :param start_date: 백테스트 시작일 (YYYY-MM-DD)
        :param end_date: 백테스트 종료일 (YYYY-MM-DD)
        :param initial_capital: 초기 투자 자본
        :param params: 전략 파라미터
        :return: 수익률, MDD, 샤프지수, 거래 내역 등
        """
        ...

    @abstractmethod
    async def analyze_stock(
        self,
        symbol: str,
        indicators: List[str] | None = None,
    ) -> Dict[str, Any]:
        """
        종목 기술적 분석
        :param symbol: 종목 코드
        :param indicators: 분석할 지표 목록 (RSI, MACD, BB 등)
        :return: 각 지표 값 및 해석
        """
        ...
