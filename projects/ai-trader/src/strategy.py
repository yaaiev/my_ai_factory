from __future__ import annotations

from itertools import product

import pandas as pd


def generate_signals(
    features_df: pd.DataFrame,
    min_sentiment_threshold: float = 0.6,
    min_mention_growth: float = 1.5,
) -> pd.DataFrame:
    if features_df.empty:
        return pd.DataFrame(columns=["date", "entity", "signal"])
    frame = features_df.reset_index().copy()
    frame["signal"] = (
        (frame["sentiment_mean_3d"] > min_sentiment_threshold)
        & (frame["mention_growth"] > min_mention_growth)
    ).astype(int)
    return frame[["date", "entity", "signal"]]


def calibrate_thresholds(
    features_df: pd.DataFrame,
    target_min_signals: int = 4,
    default_sentiment_threshold: float = 0.08,
    default_mention_growth: float = 1.2,
) -> tuple[float, float]:
    if features_df.empty:
        return default_sentiment_threshold, default_mention_growth

    frame = features_df.reset_index().copy()
    candidates_sentiment = sorted(
        {
            round(float(value), 4)
            for value in [
                default_sentiment_threshold,
                frame["sentiment_mean_3d"].quantile(0.50),
                frame["sentiment_mean_3d"].quantile(0.60),
                frame["sentiment_mean_3d"].quantile(0.70),
                frame["sentiment_mean_3d"].quantile(0.80),
            ]
        },
        reverse=True,
    )
    candidates_growth = sorted(
        {
            round(float(value), 4)
            for value in [
                default_mention_growth,
                frame["mention_growth"].quantile(0.50),
                frame["mention_growth"].quantile(0.60),
                frame["mention_growth"].quantile(0.70),
                frame["mention_growth"].quantile(0.80),
            ]
        },
        reverse=True,
    )

    best = (default_sentiment_threshold, default_mention_growth)
    best_score = -1
    for sentiment_threshold, growth_threshold in product(candidates_sentiment, candidates_growth):
        signal_count = int(
            (
                (frame["sentiment_mean_3d"] > sentiment_threshold)
                & (frame["mention_growth"] > growth_threshold)
            ).sum()
        )
        if signal_count >= target_min_signals:
            return sentiment_threshold, growth_threshold
        if signal_count > best_score:
            best = (sentiment_threshold, growth_threshold)
            best_score = signal_count
    return best
