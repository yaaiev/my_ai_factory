from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def log_experiment(
    params: dict[str, object],
    metrics: dict[str, float],
    artifact_paths: dict[str, str],
    backend: str = "auto",
    experiment_name: str = "ai_trader_sentiment_backtest",
    tracking_uri: str | None = None,
) -> dict[str, str]:
    if backend in {"auto", "mlflow"}:
        try:
            return _log_with_mlflow(
                params=params,
                metrics=metrics,
                artifact_paths=artifact_paths,
                experiment_name=experiment_name,
                tracking_uri=tracking_uri,
            )
        except Exception as exc:  # pragma: no cover - depends on local runtime
            LOGGER.warning("MLflow logging failed, falling back to local JSON tracker: %s", exc)
    return _log_to_json(
        params=params,
        metrics=metrics,
        artifact_paths=artifact_paths,
        tracking_uri=tracking_uri,
    )


def _log_with_mlflow(
    params: dict[str, object],
    metrics: dict[str, float],
    artifact_paths: dict[str, str],
    experiment_name: str,
    tracking_uri: str | None,
) -> dict[str, str]:
    import mlflow  # type: ignore

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run() as run:
        mlflow.log_params({key: str(value) for key, value in params.items()})
        mlflow.log_metrics(metrics)
        for name, path in artifact_paths.items():
            artifact_path = Path(path)
            if artifact_path.exists():
                mlflow.log_artifact(str(artifact_path), artifact_path=name)
    run_id = run.info.run_id
    return {"backend": "mlflow", "run_id": run_id}


def _log_to_json(
    params: dict[str, object],
    metrics: dict[str, float],
    artifact_paths: dict[str, str],
    tracking_uri: str | None,
) -> dict[str, str]:
    target_dir = _resolve_local_tracking_dir(tracking_uri)
    target_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "run_id": run_id,
        "params": params,
        "metrics": metrics,
        "artifacts": artifact_paths,
    }
    output_path = target_dir / f"{run_id}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"backend": "json", "run_id": run_id, "path": str(output_path)}


def _resolve_local_tracking_dir(tracking_uri: str | None) -> Path:
    if tracking_uri and tracking_uri.startswith("file://"):
        return Path(tracking_uri.removeprefix("file://"))
    if tracking_uri:
        return Path(tracking_uri)
    return Path.cwd() / "mlruns"
