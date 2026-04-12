"""
相对路径：projects/ai-intel-terminal/tests/smoke_test_pipeline.py
文件说明：不依赖外网的本地 smoke test，验证人物匹配、去重和事件抽取。
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from connectors.contracts import RawDocument
from etl.dedup import dedupe_documents, dedupe_events
from etl.event_extractor import extract_event
from etl.person_matcher import match_people
from seeds.registry import load_seed_people


def main() -> None:
    seed_people = load_seed_people(PROJECT_ROOT / "data" / "seed_persons.json")
    documents = [
        RawDocument(
            source_key="ai_news_rss",
            external_id="doc-1",
            url="https://example.com/openai-launch",
            title="Sam Altman says OpenAI will launch a new model",
            author_name="Reporter",
            published_at="2026-04-12T00:00:00Z",
            raw_text="OpenAI CEO Sam Altman discussed a launch timeline.",
        ),
        RawDocument(
            source_key="ai_news_rss",
            external_id="doc-2",
            url="https://example.com/openai-launch",
            title="Sam Altman says OpenAI will launch a new model",
            author_name="Reporter",
            published_at="2026-04-12T00:00:00Z",
            raw_text="OpenAI CEO Sam Altman discussed a launch timeline.",
        ),
    ]

    unique_documents = dedupe_documents(documents)
    assert len(unique_documents) == 1, "document dedupe failed"

    matches = match_people(unique_documents[0], seed_people)
    assert matches, "seed person match failed"
    assert matches[0].key == "sam_altman", "unexpected matched person"

    event = extract_event(unique_documents[0])
    event.person = matches[0].name
    event.matched_person_keys = [person.key for person in matches]
    deduped_events = dedupe_events([event, event])
    assert len(deduped_events) == 1, "event dedupe failed"
    assert deduped_events[0].event_type == "model_release", "event classification failed"

    print("smoke test passed")


if __name__ == "__main__":
    main()
