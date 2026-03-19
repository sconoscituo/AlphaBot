"""
AI 전략 생성기
Gemini가 종목 특성과 시장 상황을 분석하여 최적 전략 파라미터를 추천
"""
import asyncio
import json
import logging
from typing import Dict, Any

import google.generativeai as genai
import pandas as pd

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_ai_strategy_prompt(
    ticker: str,
    price_stats: Dict[str, float],
    date_range: str,
) -> str:
    """Gemini에게 전략 추천을 요청하는 프롬프트 생성"""
    return f"""
당신은 퀀트 투자 전문가입니다.
다음 종목의 주가 통계를 보고 최적의 백테스팅 전략과 파라미터를 추천해주세요.

종목: {ticker}
분석 기간: {date_range}
주가 통계:
- 평균 종가: {price_stats.get('mean_close', 0):.2f}
- 변동성 (일간 수익률 표준편차): {price_stats.get('volatility', 0):.4f}
- 최대가 / 최소가 비율: {price_stats.get('max_min_ratio', 0):.2f}
- 평균 거래량: {price_stats.get('mean_volume', 0):.0f}

다음 JSON 형식으로 정확히 응답하세요 (마크다운 코드블록 없이):
{{
  "strategy_type": "ma_cross 또는 rsi 중 하나",
  "params": {{
    "추천 파라미터 (전략에 맞게)"
  }},
  "reason": "이 전략과 파라미터를 추천하는 이유 (2~3문장)",
  "expected_trades_per_year": 예상 연간 거래 횟수 (숫자),
  "risk_level": "낮음/중간/높음"
}}
"""


async def generate_ai_strategy(
    ticker: str,
    df: pd.DataFrame,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """
    Gemini AI가 주가 데이터 분석 후 전략 파라미터 추천
    반환: {"strategy_type": ..., "params": {...}, "reason": ..., ...}
    """
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY 미설정 — 기본 전략(MA Cross 20/60) 반환")
        return {
            "strategy_type": "ma_cross",
            "params": {"short_window": 20, "long_window": 60},
            "reason": "API 키 미설정으로 기본 전략을 사용합니다.",
            "expected_trades_per_year": 6,
            "risk_level": "중간",
        }

    # 주가 통계 계산
    daily_returns = df["Close"].pct_change().dropna()
    price_stats = {
        "mean_close": float(df["Close"].mean()),
        "volatility": float(daily_returns.std()),
        "max_min_ratio": float(df["Close"].max() / df["Close"].min()),
        "mean_volume": float(df["Volume"].mean()),
    }

    prompt = _build_ai_strategy_prompt(
        ticker=ticker,
        price_stats=price_stats,
        date_range=f"{start_date} ~ {end_date}",
    )

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt),
        )

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        result = json.loads(raw_text)
        logger.info(f"AI 전략 생성 완료: {ticker} → {result.get('strategy_type')}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"AI 전략 파싱 실패: {e}")
        # 파싱 실패 시 안전한 기본값 반환
        return {
            "strategy_type": "ma_cross",
            "params": {"short_window": 20, "long_window": 60},
            "reason": "AI 응답 파싱 오류로 기본 전략을 사용합니다.",
            "expected_trades_per_year": 6,
            "risk_level": "중간",
        }
    except Exception as e:
        logger.error(f"AI 전략 생성 오류: {e}")
        raise
