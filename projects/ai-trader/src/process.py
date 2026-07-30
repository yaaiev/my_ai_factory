from __future__ import annotations

import logging
import math

import pandas as pd

from src.sentiment import SentimentAnalyzer

LOGGER = logging.getLogger(__name__)

POSITIVE_WORDS = {
    "love",
    "launch",
    "growth",
    "bullish",
    "great",
    "good",
    "win",
    "record",
    "strong",
    "breakthrough",
    "beat",
    "demand",
    "up",
}
NEGATIVE_WORDS = {
    "bad",
    "down",
    "weak",
    "lawsuit",
    "investigation",
    "risk",
    "bearish",
    "decline",
    "miss",
    "drop",
    "problem",
    "warning",
    "ban",
}
NOISE_PATTERNS = (
    "follow @",
    "expert stock recommendations",
    "daily alerts",
    "earn $",
    "join my",
    "subscribe now",
    "free discord",
    "whatsapp",
    "telegram",
    "pump",
)


def process_twitter_data(
    raw_df: pd.DataFrame,
    analyzer: SentimentAnalyzer | None = None,
) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame(columns=["timestamp", "entity", "sentiment", "mention"])
    frame = raw_df.copy()
    frame = frame.dropna(subset=["timestamp", "entity", "content", "author"])
    frame = frame[~frame["content"].astype(str).str.lower().map(_is_noise_text)]
    analyzer = analyzer or SentimentAnalyzer()
    frame["sentiment"] = analyzer.get_sentiment_batch(frame["content"].astype(str).tolist())
    frame["mention"] = 1
    frame["mention_weight"] = frame.apply(_mention_weight, axis=1)
    processed = frame[["timestamp", "entity", "sentiment", "mention", "mention_weight"]].dropna()
    LOGGER.info("Processed %s twitter rows into sentiment rows", len(processed))
    return processed


def simple_sentiment(text: str) -> float:
    tokens = [token.strip(".,!?;:\"'()[]{}").lower() for token in text.split()]
    positive = sum(token in POSITIVE_WORDS for token in tokens)
    negative = sum(token in NEGATIVE_WORDS for token in tokens)
    total = positive + negative
    if total == 0:
        return 0.5
    score = (positive - negative) / total
    normalized = (score + 1.0) / 2.0
    return round(max(0.0, min(1.0, normalized)), 4)


def _is_noise_text(text: str) -> bool:
    return any(pattern in text for pattern in NOISE_PATTERNS)


def _mention_weight(row: pd.Series) -> float:
    likes = max(float(row.get("likes", 0) or 0), 0.0)
    views = max(float(row.get("views", 0) or 0), 0.0)
    return round(1.0 + math.log1p(likes) + 0.1 * math.log1p(views), 4)
