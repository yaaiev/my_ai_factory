# 数据模型

## 设计目标

- 同时承载原始证据、结构化事件、知识图谱关系和预测结果
- 区分事实数据与推断数据
- 支持时间线、实体对齐、聚类和 watchlist 分析

## 核心对象

- `person`
- `company`
- `source`
- `raw_document`
- `event`
- `event_cluster`
- `entity_link`
- `trend_signal`
- `prediction`
- `investment_memo`

## 事件结构化 Schema

```json
{
  "person": "",
  "platform": "",
  "timestamp": "",
  "event_type": "",
  "summary": "",
  "sentiment": "",
  "risk_score": 0,
  "relevance_score": 0,
  "link": "",
  "raw_text": ""
}
```

## 推荐表

### `persons`

- `id`
- `name`
- `primary_role`
- `current_company_id`
- `twitter_handle`
- `github_login`
- `scholar_url`
- `personal_website`
- `crunchbase_url`
- `influence_index`
- `created_at`
- `updated_at`

### `companies`

- `id`
- `name`
- `type`
- `hq_region`
- `status`
- `created_at`
- `updated_at`

### `sources`

- `id`
- `source_type`
- `source_name`
- `base_url`
- `signal_tier`
- `access_mode`
- `notes`

### `raw_documents`

- `id`
- `source_id`
- `external_id`
- `url`
- `author_name`
- `published_at`
- `title`
- `raw_text`
- `language`
- `ingested_at`
- `content_hash`

### `events`

- `id`
- `primary_person_id`
- `primary_company_id`
- `source_document_id`
- `event_type`
- `event_time`
- `summary`
- `sentiment`
- `risk_score`
- `opportunity_score`
- `relevance_score`
- `signal_strength`
- `is_rumor`
- `status`
- `created_at`

### `event_clusters`

- `id`
- `cluster_key`
- `canonical_event_id`
- `cluster_summary`
- `confidence_score`
- `first_seen_at`
- `last_seen_at`

### `event_cluster_members`

- `cluster_id`
- `event_id`
- `similarity_score`

### `entity_relationships`

- `id`
- `src_entity_type`
- `src_entity_id`
- `relation_type`
- `dst_entity_type`
- `dst_entity_id`
- `evidence_event_id`
- `confidence_score`
- `valid_from`
- `valid_to`

### `predictions`

- `id`
- `prediction_type`
- `subject_entity_type`
- `subject_entity_id`
- `time_horizon`
- `prediction_text`
- `confidence_score`
- `supporting_cluster_ids`
- `created_at`

### `delivery_artifacts`

- `id`
- `artifact_type`
- `artifact_date`
- `title`
- `body_markdown`
- `source_scope`
- `created_at`

## 图谱映射

- `Person -> Company`: `works_for`, `worked_for`
- `Person -> Person`: `collaborates_with`, `mentions`, `invests_in`
- `Company -> Model`: `develops`
- `Model -> Paper`: `described_by`
- `Event -> Person`: `involves`
- `Event -> Company`: `impacts`

## MVP 数据库建议

- 关系库：PostgreSQL
- 分析层：DuckDB
- 向量索引：后续按 embedding 方案补充
- 图谱层：先用 `entity_relationships` 和派生视图，不急着拆到独立图库
