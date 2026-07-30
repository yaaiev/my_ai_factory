from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

LOGGER = logging.getLogger(__name__)


def get_price(
    ticker: str,
    start: str | date,
    end: str | date,
    cache_dir: str | Path | None = None,
    use_cache: bool = True,
    max_retries: int = 3,
    retry_sleep_seconds: int = 5,
) -> pd.DataFrame:
    cache_path = Path(cache_dir) if cache_dir else None
    if cache_path:
        cache_path.mkdir(parents=True, exist_ok=True)
        target = cache_path / f"{ticker}.csv"
        if use_cache and target.exists():
            frame = pd.read_csv(target)
            if not frame.empty:
                return frame[["date", "open", "close"]]

    history = pd.DataFrame()
    for attempt in range(1, max_retries + 1):
        try:
            history = yf.download(
                tickers=ticker,
                start=_to_date_string(start),
                end=_to_date_string(end),
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False,
            )
        except Exception as exc:
            LOGGER.warning("Price download attempt %s failed for %s: %s", attempt, ticker, exc)
            history = pd.DataFrame()
        if not history.empty:
            break
        if attempt < max_retries:
            time.sleep(retry_sleep_seconds)
    if history.empty:
        LOGGER.warning("No price history returned for %s", ticker)
        return pd.DataFrame(columns=["date", "open", "close"])

    if isinstance(history.columns, pd.MultiIndex):
        history = history.droplevel(1, axis=1)
    frame = history.reset_index()[["Date", "Open", "Close"]].copy()
    frame.columns = ["date", "open", "close"]
    frame["date"] = pd.to_datetime(frame["date"]).dt.date.astype(str)
    if cache_path:
        frame.to_csv(cache_path / f"{ticker}.csv", index=False)
    return frame


def get_prices(
    tickers: list[str],
    start: str | date,
    end: str | date,
    cache_dir: str | Path | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    cache_path = Path(cache_dir) if cache_dir else None
    cached_frames: list[pd.DataFrame] = []
    missing_tickers: list[str] = []

    for ticker in tickers:
        cached = pd.DataFrame()
        if cache_path:
            cache_path.mkdir(parents=True, exist_ok=True)
            target = cache_path / f"{ticker}.csv"
            if use_cache and target.exists():
                cached = pd.read_csv(target)
        if cached.empty:
            missing_tickers.append(ticker)
            continue
        cached["entity"] = ticker
        cached_frames.append(cached[["date", "entity", "open", "close"]])

    downloaded_frames: list[pd.DataFrame] = []
    for ticker in missing_tickers:
        frame = get_price(
            ticker=ticker,
            start=start,
            end=end,
            cache_dir=cache_dir,
            use_cache=use_cache,
        )
        if frame.empty:
            continue
        frame["entity"] = ticker
        downloaded_frames.append(frame[["date", "entity", "open", "close"]])
        time.sleep(2)

    frames = cached_frames + downloaded_frames
    if not frames:
        return pd.DataFrame(columns=["date", "entity", "open", "close"])
    merged = pd.concat(frames, ignore_index=True)
    merged["date"] = pd.to_datetime(merged["date"]).dt.normalize()
    return merged.sort_values(["entity", "date"]).reset_index(drop=True)


def build_price_window(period_days: int) -> tuple[str, str]:
    end = date.today() + timedelta(days=1)
    start = end - timedelta(days=period_days)
    return start.isoformat(), end.isoformat()


def _to_date_string(value: str | date) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value)
