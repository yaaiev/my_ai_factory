from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

LOGGER = logging.getLogger(__name__)


def load_twitter_json(raw_dir: str | Path) -> pd.DataFrame:
    raw_path = Path(raw_dir)
    rows: list[dict[str, object]] = []
    for file_path in sorted(raw_path.glob("*.json")):
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = [payload]
        for item in payload:
            rows.append(
                {
                    "timestamp": item.get("timestamp") or item.get("created_at"),
                    "entity": item.get("entity") or item.get("ticker"),
                    "content": item.get("content") or item.get("text"),
                    "author": item.get("author") or item.get("screen_name") or item.get("name"),
                    "likes": item.get("likes", 0),
                    "views": item.get("views", 0),
                }
            )
    frame = pd.DataFrame(rows, columns=["timestamp", "entity", "content", "author", "likes", "views"])
    if frame.empty:
        return frame
    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        format="%a %b %d %H:%M:%S %z %Y",
        utc=True,
        errors="coerce",
    )
    if frame["timestamp"].isna().any():
        frame["timestamp"] = frame["timestamp"].fillna(
            pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        )
    return frame


def bootstrap_twitter_raw_data(
    tickers: list[str],
    raw_dir: str | Path,
    search_terms: dict[str, object],
    lookback_days: int = 21,
    bucket_days: int = 3,
    search_limit: int = 20,
    binary: str = "opencli",
    force_refresh: bool = False,
) -> None:
    raw_path = Path(raw_dir)
    raw_path.mkdir(parents=True, exist_ok=True)
    target_files = [raw_path / f"{ticker.lower()}.json" for ticker in tickers]
    if not force_refresh and all(path.exists() and path.stat().st_size > 2 for path in target_files):
        LOGGER.info("Twitter raw files already exist for all tickers, reusing cached files")
        return
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=lookback_days)
    bucket_days = max(bucket_days, 1)
    bucket_starts = list(range(0, lookback_days, bucket_days))
    for ticker in tickers:
        query_terms = _resolve_query_terms(search_terms.get(ticker, ticker))
        normalized: list[dict[str, object]] = []
        for offset in bucket_starts:
            bucket_start = start_date + timedelta(days=offset)
            bucket_end = min(bucket_start + timedelta(days=bucket_days), end_date + timedelta(days=1))
            for term in query_terms:
                query = f"({term}) since:{bucket_start.isoformat()} until:{bucket_end.isoformat()}"
                LOGGER.info(
                    "Fetching Twitter mentions via OpenCLI for %s term %s in bucket %s -> %s",
                    ticker,
                    term,
                    bucket_start.isoformat(),
                    bucket_end.isoformat(),
                )
                result = subprocess.run(
                    [
                        binary,
                        "twitter",
                        "search",
                        query,
                        "--filter",
                        "live",
                        "--limit",
                        str(search_limit),
                        "-f",
                        "json",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    detail = (result.stderr or result.stdout).strip()
                    raise RuntimeError(f"opencli twitter search failed for {ticker}: {detail}")
                payload = _extract_json_payload(result.stdout)
                parsed = json.loads(payload) if payload else []
                normalized.extend(_normalize_opencli_item(item, ticker) for item in parsed)
        normalized = _dedupe_twitter_rows(normalized)
        target_path = raw_path / f"{ticker.lower()}.json"
        temp_path = raw_path / f"{ticker.lower()}.json.tmp"
        temp_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(target_path)


def download_price_data(tickers: list[str], output_dir: str | Path, period_days: int = 60) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    period = f"{period_days}d"
    LOGGER.info("Downloading price data for %s tickers in one batch", len(tickers))
    history = yf.download(
        tickers=tickers,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
        group_by="ticker",
    )
    if history.empty:
        LOGGER.warning("No batched price history returned")
        return

    for ticker in tickers:
        try:
            if isinstance(history.columns, pd.MultiIndex):
                ticker_frame = history[ticker][["Open", "Close"]].dropna(how="all")
            else:
                ticker_frame = history[["Open", "Close"]].dropna(how="all")
            if ticker_frame.empty:
                LOGGER.warning("No price history returned for %s", ticker)
                continue
            price_frame = ticker_frame.reset_index().copy()
            price_frame.columns = ["date", "open", "close"]
            price_frame["date"] = pd.to_datetime(price_frame["date"]).dt.date.astype(str)
            price_frame.to_csv(output_path / f"{ticker}.csv", index=False)
        except KeyError:
            LOGGER.warning("Ticker %s missing from batched price response", ticker)


def load_price_data(price_dir: str | Path) -> pd.DataFrame:
    price_path = Path(price_dir)
    rows: list[pd.DataFrame] = []
    for file_path in sorted(price_path.glob("*.csv")):
        ticker = file_path.stem.upper()
        frame = pd.read_csv(file_path)
        if frame.empty:
            continue
        frame.columns = [column.lower() for column in frame.columns]
        frame["entity"] = ticker
        frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
        rows.append(frame[["date", "entity", "open", "close"]])
    if not rows:
        return pd.DataFrame(columns=["date", "entity", "open", "close"])
    return pd.concat(rows, ignore_index=True)


def _extract_json_payload(stdout: str) -> str:
    lines = stdout.splitlines()
    collected: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not started and stripped.startswith(("[", "{")):
            started = True
        if started:
            if stripped.startswith("Update available:") or stripped.startswith("Run: npm install"):
                break
            collected.append(line)
    return "\n".join(collected).strip()


def _normalize_opencli_item(item: dict[str, object], ticker: str) -> dict[str, object]:
    return {
        "timestamp": item.get("created_at", ""),
        "entity": ticker,
        "content": item.get("text", ""),
        "author": item.get("author", ""),
        "url": item.get("url", ""),
        "likes": item.get("likes", 0),
        "views": item.get("views", 0),
    }


def _dedupe_twitter_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (str(row.get("url", "")), str(row.get("timestamp", "")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _resolve_query_terms(value: object) -> list[str]:
    if isinstance(value, list):
        terms = [str(item).strip() for item in value if str(item).strip()]
        return terms or [""]
    term = str(value).strip()
    return [term] if term else [""]
