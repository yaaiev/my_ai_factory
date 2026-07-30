from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


def evaluate_backtest(backtest_df: pd.DataFrame) -> dict[str, float]:
    if backtest_df.empty:
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
        }

    returns = backtest_df["return"].astype(float)
    cumulative = (1 + returns).cumprod()
    total_return = float(cumulative.iloc[-1] - 1)
    std = returns.std(ddof=0)
    sharpe_ratio = float((returns.mean() / std) * np.sqrt(252)) if std > 0 else 0.0
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    max_drawdown = float(drawdown.min())
    win_rate = float((returns > 0).mean())
    metrics = {
        "total_return": round(total_return, 6),
        "sharpe_ratio": round(sharpe_ratio, 6),
        "max_drawdown": round(max_drawdown, 6),
        "win_rate": round(win_rate, 6),
    }
    return metrics


def print_report(metrics: dict[str, float]) -> None:
    LOGGER.info("Evaluation metrics: %s", metrics)
    print("Backtest Metrics")
    for key, value in metrics.items():
        print(f"- {key}: {value}")


def save_metrics(metrics: dict[str, float], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
