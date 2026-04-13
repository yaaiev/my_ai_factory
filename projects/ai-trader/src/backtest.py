from __future__ import annotations

import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)


def run_backtest(signals_df: pd.DataFrame, prices_df: pd.DataFrame) -> pd.DataFrame:
    if signals_df.empty or prices_df.empty:
        return pd.DataFrame(columns=["date", "entity", "return", "cumulative_return"])

    signals = signals_df.copy()
    signals["date"] = pd.to_datetime(signals["date"]).dt.normalize()
    prices = prices_df.copy().sort_values(["entity", "date"])
    prices["next_open"] = prices.groupby("entity")["open"].shift(-1)
    prices["next_close"] = prices.groupby("entity")["close"].shift(-1)

    merged = signals.merge(prices[["date", "entity", "next_open", "next_close"]], on=["date", "entity"], how="left")
    merged = merged[(merged["signal"] == 1) & merged["next_open"].notna() & merged["next_close"].notna()].copy()
    if merged.empty:
        return pd.DataFrame(columns=["date", "entity", "return", "cumulative_return"])

    merged["return"] = (merged["next_close"] - merged["next_open"]) / merged["next_open"]
    merged = merged.sort_values(["date", "entity"])
    merged["cumulative_return"] = (1 + merged["return"]).cumprod() - 1
    result = merged[["date", "entity", "return", "cumulative_return"]]
    LOGGER.info("Backtest generated %s trades", len(result))
    return result
