from __future__ import annotations

import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)


def run_backtest(signal_df: pd.DataFrame, price_df: pd.DataFrame) -> pd.DataFrame:
    if signal_df.empty or price_df.empty:
        return pd.DataFrame(columns=["date", "entity", "return", "cumulative_return"])

    signals = signal_df.copy()
    signals["date"] = pd.to_datetime(signals["date"], utc=True).dt.tz_localize(None).dt.normalize()
    prices = price_df.copy().sort_values(["entity", "date"])
    prices["date"] = pd.to_datetime(prices["date"]).dt.tz_localize(None).dt.normalize()
    prices["next_open"] = prices.groupby("entity")["open"].shift(-1)
    prices["next_close"] = prices.groupby("entity")["close"].shift(-1)

    merged = signals.merge(
        prices[["date", "entity", "next_open", "next_close"]],
        on=["date", "entity"],
        how="left",
    )
    merged = merged[(merged["signal"] == 1) & merged["next_open"].notna() & merged["next_close"].notna()].copy()
    if merged.empty:
        return pd.DataFrame(columns=["date", "entity", "return", "cumulative_return"])

    merged["return"] = (merged["next_close"] - merged["next_open"]) / merged["next_open"]
    merged = merged.sort_values(["date", "entity"])
    merged["cumulative_return"] = (1 + merged["return"]).cumprod() - 1
    result = merged[["date", "entity", "return", "cumulative_return"]]
    LOGGER.info("Backtest generated %s trades", len(result))
    return result
