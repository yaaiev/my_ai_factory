from __future__ import annotations

import logging
from pathlib import Path

import yaml

from src.backtest_engine import run_backtest
from src.data_provider import build_price_window, get_prices
from src.evaluate import evaluate_backtest, print_report, save_metrics
from src.features import build_features
from src.ingest import bootstrap_twitter_raw_data, load_twitter_json
from src.process import process_twitter_data
from src.sentiment import SentimentAnalyzer
from src.strategy import calibrate_thresholds, generate_signals
from src.tracker import log_experiment


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def load_config() -> dict:
    config_path = Path(__file__).resolve().parent / "config" / "config.yaml"
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def main() -> None:
    config = load_config()
    setup_logging(config.get("logging", {}).get("level", "INFO"))

    if config["twitter"].get("use_opencli_bootstrap", False):
        bootstrap_twitter_raw_data(
            tickers=list(config["tickers"]),
            raw_dir=config["twitter"]["raw_dir"],
            search_terms=dict(config["twitter"].get("search_terms", {})),
            lookback_days=int(config["twitter"].get("lookback_days", 60)),
            bucket_days=int(config["twitter"].get("bucket_days", 3)),
            search_limit=int(config["twitter"].get("search_limit", 50)),
            force_refresh=bool(config["twitter"].get("refresh_raw_data", False)),
        )

    twitter_df = load_twitter_json(config["twitter"]["raw_dir"])
    analyzer = SentimentAnalyzer(
        backend=str(config["sentiment"].get("backend", "auto")),
        model_name=str(config["sentiment"].get("model_name", "ProsusAI/finbert")),
        batch_size=int(config["sentiment"].get("batch_size", 16)),
        fallback_backend=str(config["sentiment"].get("fallback_backend", "lexicon")),
    )
    processed_df = process_twitter_data(twitter_df, analyzer=analyzer)
    features_df = build_features(
        processed_df=processed_df,
        rolling_window_days=int(config["feature"]["rolling_window_days"]),
    )
    sentiment_threshold = float(config["feature"]["min_sentiment_threshold"])
    mention_growth_threshold = float(config["feature"]["min_mention_growth"])
    if bool(config["feature"].get("auto_calibrate_thresholds", False)):
        sentiment_threshold, mention_growth_threshold = calibrate_thresholds(
            features_df=features_df,
            target_min_signals=int(config["feature"].get("target_min_signals", 4)),
            default_sentiment_threshold=sentiment_threshold,
            default_mention_growth=mention_growth_threshold,
        )
    signals_df = generate_signals(
        features_df=features_df,
        min_sentiment_threshold=sentiment_threshold,
        min_mention_growth=mention_growth_threshold,
    )

    price_start, price_end = build_price_window(int(config["prices"]["period_days"]))
    prices_df = get_prices(
        tickers=list(config["tickers"]),
        start=price_start,
        end=price_end,
        cache_dir=config["prices"]["raw_dir"],
        use_cache=bool(config["prices"].get("use_cache", True)),
    )
    backtest_df = run_backtest(signal_df=signals_df, price_df=prices_df)
    metrics = evaluate_backtest(backtest_df)

    output = config["output"]
    Path(output["processed_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(output["features_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(output["signals_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(output["backtest_path"]).parent.mkdir(parents=True, exist_ok=True)

    processed_df.to_csv(output["processed_path"], index=False)
    features_df.reset_index().to_csv(output["features_path"], index=False)
    signals_df.to_csv(output["signals_path"], index=False)
    backtest_df.to_csv(output["backtest_path"], index=False)
    save_metrics(metrics, output["metrics_path"])
    tracker_info = log_experiment(
        params={
            "tickers": ",".join(config["tickers"]),
            "twitter_lookback_days": config["twitter"]["lookback_days"],
            "twitter_bucket_days": config["twitter"]["bucket_days"],
            "rolling_window_days": config["feature"]["rolling_window_days"],
            "min_sentiment_threshold": sentiment_threshold,
            "min_mention_growth": mention_growth_threshold,
            "sentiment_backend": analyzer._resolved_backend,
        },
        metrics=metrics,
        artifact_paths={
            "processed": output["processed_path"],
            "features": output["features_path"],
            "signals": output["signals_path"],
            "backtest": output["backtest_path"],
            "metrics": output["metrics_path"],
        },
        backend=str(config["tracker"].get("backend", "auto")),
        experiment_name=str(config["tracker"].get("experiment_name", "ai_trader_sentiment_backtest")),
        tracking_uri=str(config["tracker"].get("tracking_uri", "")),
    )
    logging.getLogger(__name__).info("Tracker recorded run: %s", tracker_info)
    print_report(metrics)


if __name__ == "__main__":
    main()
