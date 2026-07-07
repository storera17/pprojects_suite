from __future__ import annotations

GOLD_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS gold_scaffold_stats (
    scaffold VARCHAR PRIMARY KEY,
    evidence_count INTEGER NOT NULL,
    representative_doi VARCHAR NOT NULL,
    top_funder VARCHAR NOT NULL,
    total_funding DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS gold_galaxy_points (
    id VARCHAR PRIMARY KEY,
    x DOUBLE NOT NULL,
    y DOUBLE NOT NULL,
    z DOUBLE NOT NULL,
    cluster_id VARCHAR NOT NULL,
    scaffold VARCHAR NOT NULL,
    funding_usd DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS scaffold_entries (
    name VARCHAR PRIMARY KEY,
    category VARCHAR NOT NULL,
    family VARCHAR NOT NULL,
    canonical_smiles VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE OR REPLACE VIEW gold_cluster_points AS
SELECT * FROM gold_galaxy_points;
"""

REQUIRED_GOLD_TABLES = ("gold_scaffold_stats", "gold_galaxy_points")

CORE_INGESTION_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS bronze_core_publications (
    core_id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    doi VARCHAR,
    year_published INTEGER,
    published_date VARCHAR,
    authors_json VARCHAR NOT NULL,
    journal VARCHAR,
    abstract VARCHAR,
    topics_json VARCHAR NOT NULL,
    full_text_url VARCHAR,
    source_url VARCHAR,
    raw_json VARCHAR NOT NULL,
    query VARCHAR NOT NULL,
    fetched_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS core_ingestion_runs (
    run_id VARCHAR PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    query VARCHAR NOT NULL,
    initial_query VARCHAR,
    status VARCHAR NOT NULL,
    requested_limit INTEGER NOT NULL,
    page_size INTEGER NOT NULL,
    downloaded_count INTEGER NOT NULL DEFAULT 0,
    inserted_count INTEGER NOT NULL,
    updated_count INTEGER NOT NULL,
    diagnosis_path VARCHAR,
    error_message VARCHAR
);

CREATE TABLE IF NOT EXISTS core_ingestion_cursors (
    source VARCHAR PRIMARY KEY,
    frontier_core_id VARCHAR NOT NULL,
    frontier_published_date VARCHAR,
    query VARCHAR NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    metadata_json VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS chempulse_payloads (
    payload_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    source VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    record_count INTEGER NOT NULL,
    last_error VARCHAR,
    payload_json VARCHAR NOT NULL
);
"""
