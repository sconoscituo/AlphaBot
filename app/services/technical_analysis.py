"""Technical analysis indicators: RSI, MACD, Bollinger Bands using numpy."""
import numpy as np
from typing import Dict


def compute_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Compute Relative Strength Index."""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.zeros(len(prices))
    avg_loss = np.zeros(len(prices))

    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])

    for i in range(period + 1, len(prices)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period

    rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
    rsi = 100 - (100 / (1 + rs))
    rsi[:period] = np.nan
    return rsi


def compute_ema(prices: np.ndarray, period: int) -> np.ndarray:
    """Compute Exponential Moving Average."""
    ema = np.zeros(len(prices))
    k = 2 / (period + 1)
    ema[period - 1] = np.mean(prices[:period])
    for i in range(period, len(prices)):
        ema[i] = prices[i] * k + ema[i - 1] * (1 - k)
    ema[:period - 1] = np.nan
    return ema


def compute_macd(
    prices: np.ndarray,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Dict[str, np.ndarray]:
    """Compute MACD line, signal line, and histogram."""
    ema_fast = compute_ema(prices, fast)
    ema_slow = compute_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = compute_ema(np.nan_to_num(macd_line), signal)
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def compute_bollinger_bands(
    prices: np.ndarray, period: int = 20, num_std: float = 2.0
) -> Dict[str, np.ndarray]:
    """Compute Bollinger Bands (upper, middle, lower)."""
    middle = np.full(len(prices), np.nan)
    upper = np.full(len(prices), np.nan)
    lower = np.full(len(prices), np.nan)

    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1 : i + 1]
        mean = np.mean(window)
        std = np.std(window, ddof=1)
        middle[i] = mean
        upper[i] = mean + num_std * std
        lower[i] = mean - num_std * std

    return {"upper": upper, "middle": middle, "lower": lower}


def compute_all_indicators(prices: np.ndarray) -> Dict[str, np.ndarray]:
    """Return all indicators for a price series."""
    return {
        "rsi": compute_rsi(prices),
        **{f"macd_{k}": v for k, v in compute_macd(prices).items()},
        **{f"bb_{k}": v for k, v in compute_bollinger_bands(prices).items()},
    }
