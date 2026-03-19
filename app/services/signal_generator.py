"""Gemini AI-based trading signal generator."""
import os
import json
import logging
from typing import Optional
import numpy as np
import google.generativeai as genai

from app.services.technical_analysis import compute_all_indicators

logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

SIGNAL_PROMPT = """
You are an expert quantitative analyst. Given the following technical indicators for stock {symbol},
generate a trading signal.

Current Price: {price}
RSI (14): {rsi}
MACD: {macd}, Signal: {macd_signal}, Histogram: {macd_hist}
Bollinger Upper: {bb_upper}, Middle: {bb_middle}, Lower: {bb_lower}

Respond ONLY with a valid JSON object in this exact format:
{{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<brief explanation>"
}}
"""


class SignalGenerator:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model = genai.GenerativeModel(model_name)

    async def generate_signal(
        self, symbol: str, prices: np.ndarray
    ) -> Optional[dict]:
        """Generate BUY/SELL/HOLD signal using Gemini AI."""
        if len(prices) < 30:
            return {"signal": "HOLD", "confidence": 0.0, "reasoning": "Insufficient data"}

        indicators = compute_all_indicators(prices)
        current_price = float(prices[-1])

        def _safe(arr: np.ndarray) -> str:
            val = arr[-1]
            return "N/A" if np.isnan(val) else f"{val:.4f}"

        prompt = SIGNAL_PROMPT.format(
            symbol=symbol,
            price=f"{current_price:.2f}",
            rsi=_safe(indicators["rsi"]),
            macd=_safe(indicators["macd_macd"]),
            macd_signal=_safe(indicators["macd_signal"]),
            macd_hist=_safe(indicators["macd_histogram"]),
            bb_upper=_safe(indicators["bb_upper"]),
            bb_middle=_safe(indicators["bb_middle"]),
            bb_lower=_safe(indicators["bb_lower"]),
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # Strip markdown fences if present
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            return json.loads(text)
        except Exception as exc:
            logger.error("Gemini signal generation failed: %s", exc)
            return {"signal": "HOLD", "confidence": 0.0, "reasoning": str(exc)}


signal_generator = SignalGenerator()
