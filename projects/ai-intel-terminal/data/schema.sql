-- 相对路径：projects/ai-intel-terminal/data/schema.sql
-- 文件说明：AI 情报终端 MVP 关系模型草案。

create table if not exists persons (
    id integer primary key,
    name text not null,
    primary_role text,
    current_company_id integer,
    twitter_handle text,
    github_login text,
    scholar_url text,
    personal_website text,
    crunchbase_url text,
    influence_index real default 0,
    created_at text not null,
    updated_at text not null
);

create table if not exists companies (
    id integer primary key,
    name text not null,
    type text,
    hq_region text,
    status text,
    created_at text not null,
    updated_at text not null
);

create table if not exists sources (
    id integer primary key,
    source_type text not null,
    source_name text not null,
    base_url text,
    signal_tier text,
    access_mode text,
    notes text
);

create table if not exists raw_documents (
    id integer primary key,
    source_id integer not null,
    external_id text,
    url text,
    author_name text,
    published_at text,
    title text,
    raw_text text not null,
    language text,
    ingested_at text not null,
    content_hash text not null
);

create table if not exists events (
    id integer primary key,
    primary_person_id integer,
    primary_company_id integer,
    source_document_id integer not null,
    event_type text not null,
    event_time text not null,
    summary text not null,
    sentiment text,
    risk_score real default 0,
    opportunity_score real default 0,
    relevance_score real default 0,
    signal_strength text,
    is_rumor integer default 0,
    status text default 'candidate',
    created_at text not null
);

create table if not exists event_clusters (
    id integer primary key,
    cluster_key text not null,
    canonical_event_id integer,
    cluster_summary text,
    confidence_score real default 0,
    first_seen_at text,
    last_seen_at text
);

create table if not exists event_cluster_members (
    cluster_id integer not null,
    event_id integer not null,
    similarity_score real default 0,
    primary key (cluster_id, event_id)
);

create table if not exists entity_relationships (
    id integer primary key,
    src_entity_type text not null,
    src_entity_id integer not null,
    relation_type text not null,
    dst_entity_type text not null,
    dst_entity_id integer not null,
    evidence_event_id integer,
    confidence_score real default 0,
    valid_from text,
    valid_to text
);

create table if not exists predictions (
    id integer primary key,
    prediction_type text not null,
    subject_entity_type text not null,
    subject_entity_id integer not null,
    time_horizon text,
    prediction_text text not null,
    confidence_score real default 0,
    supporting_cluster_ids text,
    created_at text not null
);

create table if not exists delivery_artifacts (
    id integer primary key,
    artifact_type text not null,
    artifact_date text not null,
    title text not null,
    body_markdown text not null,
    source_scope text,
    created_at text not null
);
