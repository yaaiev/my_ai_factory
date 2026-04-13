from __future__ import annotations

import logging

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


def build_features(processed_df: pd.DataFrame, rolling_window_days: int = 3) -> pd.DataFrame:
    if processed_df.empty:
        return pd.DataFrame(
            columns=["date", "entity", "sentiment_mean_3d", "mention_count_3d", "mention_growth"]
        ).set_index(["date", "entity"])

    frame = processed_df.copy()
    frame["date"] = pd.to_datetime(frame["timestamp"]).dt.normalize()
    daily = (
        frame.groupby(["date", "entity"], as_index=False)
        .agg(
            sentiment_mean=("sentiment", "mean"),
            mention_count=("mention_weight", "sum") if "mention_weight" in frame.columns else ("mention", "sum"),
        )
        .sort_values(["entity", "date"])
    )

    pieces: list[pd.DataFrame] = []
    for entity, group in daily.groupby("entity", sort=False):
        entity_frame = group.copy().sort_values("date")
        full_range = pd.date_range(entity_frame["date"].min(), entity_frame["date"].max(), freq="D")
        entity_frame = (
            entity_frame.set_index("date")
            .reindex(full_range)
            .rename_axis("date")
            .reset_index()
        )
        entity_frame["entity"] = entity
        entity_frame["sentiment_mean"] = entity_frame["sentiment_mean"].fillna(0.0)
        entity_frame["mention_count"] = entity_frame["mention_count"].fillna(0)
        entity_frame["sentiment_mean_3d"] = entity_frame["sentiment_mean"].rolling(
            window=rolling_window_days,
            min_periods=rolling_window_days,
        ).mean()
        entity_frame["mention_count_3d"] = entity_frame["mention_count"].rolling(
            window=rolling_window_days,
            min_periods=rolling_window_days,
        ).sum()
        previous_mentions = entity_frame["mention_count_3d"].shift(rolling_window_days)
        entity_frame["mention_growth"] = np.where(
            previous_mentions.fillna(0) > 0,
            entity_frame["mention_count_3d"] / previous_mentions,
            np.nan,
        )
        pieces.append(entity_frame)

    features = pd.concat(pieces, ignore_index=True)
    features = features.dropna(subset=["sentiment_mean_3d", "mention_count_3d", "mention_growth"])
    features = features[["date", "entity", "sentiment_mean_3d", "mention_count_3d", "mention_growth"]]
    features = features.set_index(["date", "entity"]).sort_index()
    LOGGER.info("Built %s feature rows", len(features))
    return features
