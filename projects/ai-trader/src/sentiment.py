from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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
    "surge",
    "improve",
    "optimistic",
    "buy",
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
    "sell",
    "downgrade",
    "fraud",
    "delay",
}


@dataclass
class SentimentAnalyzer:
    backend: str = "auto"
    model_name: str = "ProsusAI/finbert"
    batch_size: int = 16
    fallback_backend: str = "lexicon"

    def __post_init__(self) -> None:
        self._pipeline = None
        self._resolved_backend = self.backend
        if self.backend in {"auto", "finbert"}:
            self._pipeline = self._try_load_finbert()
            if self._pipeline is not None:
                self._resolved_backend = "finbert"
            else:
                self._resolved_backend = self.fallback_backend
        LOGGER.info("Sentiment analyzer backend resolved to %s", self._resolved_backend)

    def get_sentiment(self, text: str) -> float:
        return self.get_sentiment_batch([text])[0]

    def get_sentiment_batch(self, texts: Iterable[str]) -> list[float]:
        cleaned = [str(text or "") for text in texts]
        if not cleaned:
            return []
        if self._resolved_backend == "finbert" and self._pipeline is not None:
            return self._score_with_finbert(cleaned)
        return [self._score_with_lexicon(text) for text in cleaned]

    def _try_load_finbert(self):
        os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline  # type: ignore
        except ImportError:
            LOGGER.info("transformers is unavailable, falling back to lexicon sentiment")
            return None
        try:
            local_only = _has_local_model_cache(self.model_name)
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                local_files_only=local_only,
                use_fast=True,
            )
            model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                local_files_only=local_only,
                use_safetensors=False,
            )
            return pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                truncation=True,
            )
        except Exception as exc:  # pragma: no cover - depends on local model/runtime
            LOGGER.warning("FinBERT load failed, falling back to lexicon sentiment: %s", exc)
            return None

    def _score_with_finbert(self, texts: list[str]) -> list[float]:
        scores: list[float] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            predictions = self._pipeline(batch)
            for prediction in predictions:
                label = str(prediction.get("label", "")).lower()
                confidence = float(prediction.get("score", 0.0))
                if "positive" in label:
                    scores.append(round(confidence, 4))
                elif "negative" in label:
                    scores.append(round(-confidence, 4))
                else:
                    scores.append(0.0)
        return scores

    def _score_with_lexicon(self, text: str) -> float:
        tokens = [token.strip(".,!?;:\"'()[]{}").lower() for token in text.split()]
        positive = sum(token in POSITIVE_WORDS for token in tokens)
        negative = sum(token in NEGATIVE_WORDS for token in tokens)
        total = positive + negative
        if total == 0:
            return 0.0
        score = (positive - negative) / total
        return round(max(-1.0, min(1.0, score)), 4)


def get_sentiment(text: str, analyzer: SentimentAnalyzer | None = None) -> float:
    analyzer = analyzer or SentimentAnalyzer()
    return analyzer.get_sentiment(text)


def get_sentiment_batch(
    texts: Iterable[str],
    analyzer: SentimentAnalyzer | None = None,
) -> list[float]:
    analyzer = analyzer or SentimentAnalyzer()
    return analyzer.get_sentiment_batch(texts)


def _has_local_model_cache(model_name: str) -> bool:
    cache_root = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = cache_root / f"models--{model_name.replace('/', '--')}"
    snapshots = model_dir / "snapshots"
    return snapshots.exists() and any(snapshots.iterdir())
