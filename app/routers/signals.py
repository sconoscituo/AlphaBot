"""API router for trading signal generation and retrieval."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import numpy as np
import yfinance as yf

from app.services.signal_generator import signal_generator
from app.utils.auth import get_current_user

router = APIRouter(prefix="/signals", tags=["signals"])


class SignalRequest(BaseModel):
    symbol: str
    period: str = "3mo"
    interval: str = "1d"


class SignalResponse(BaseModel):
    symbol: str
    signal: str
    confidence: float
    reasoning: str
    current_price: Optional[float] = None


@router.post("/generate", response_model=SignalResponse)
async def generate_signal(
    req: SignalRequest,
    current_user=Depends(get_current_user),
):
    """Generate an AI trading signal for the given symbol."""
    try:
        ticker = yf.Ticker(req.symbol)
        hist = ticker.history(period=req.period, interval=req.interval)
        if hist.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for symbol: {req.symbol}",
            )
        prices = hist["Close"].values.astype(np.float64)
        result = await signal_generator.generate_signal(req.symbol, prices)
        return SignalResponse(
            symbol=req.symbol,
            signal=result.get("signal", "HOLD"),
            confidence=result.get("confidence", 0.0),
            reasoning=result.get("reasoning", ""),
            current_price=float(prices[-1]),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/history/{symbol}", response_model=list[SignalResponse])
async def get_signal_history(
    symbol: str,
    current_user=Depends(get_current_user),
):
    """Return cached signal history (stub – extend with DB persistence)."""
    return []
