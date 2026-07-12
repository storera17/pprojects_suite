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


# MentorOS learning surface was removed during ChemPulse onboarding (Meta-OS M7). The
# mentor_* tables are no longer created. Any pre-existing mentor_* data is left untouched
# (not dropped). See command-center/docs/meta-os/onboarding/chempulse/05-REMOVAL-REVIEW.md.


# Reaction Intelligence (docs/REACTION_INTELLIGENCE.md). Extends the medallion pattern with a
# reaction/mechanism/provenance layer. Applied idempotently the same way GOLD/CORE schemas are
# (ReactionRepository.ensure_schema), so it never disturbs the publication-era tables above.
REACTION_INTELLIGENCE_SCHEMA_SQL = """
-- Bronze: one row per raw ingested source artifact.
CREATE TABLE IF NOT EXISTS bronze_documents (
    doc_id VARCHAR PRIMARY KEY,
    source_kind VARCHAR NOT NULL,
    title VARCHAR,
    doi VARCHAR,
    url VARCHAR,
    local_path VARCHAR,
    credibility_tier INTEGER NOT NULL DEFAULT 3,
    fetched_at TIMESTAMP NOT NULL,
    raw_text VARCHAR,
    meta_json VARCHAR NOT NULL DEFAULT '{}'
);

-- Bronze: figures/reaction schemes extracted from a document, pending structure recognition.
CREATE TABLE IF NOT EXISTS bronze_scheme_images (
    image_id VARCHAR PRIMARY KEY,
    doc_id VARCHAR NOT NULL,
    page INTEGER,
    bbox_json VARCHAR NOT NULL DEFAULT '[]',
    image_path VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'pending'
);

-- Silver: parsed, canonical, one row per reaction step.
CREATE TABLE IF NOT EXISTS silver_reactions (
    reaction_id VARCHAR PRIMARY KEY,
    route_id VARCHAR,
    step_index INTEGER NOT NULL DEFAULT 0,
    reaction_smiles VARCHAR,
    reactants_json VARCHAR NOT NULL DEFAULT '[]',
    reagents_json VARCHAR NOT NULL DEFAULT '[]',
    catalysts_json VARCHAR NOT NULL DEFAULT '[]',
    solvents_json VARCHAR NOT NULL DEFAULT '[]',
    products_json VARCHAR NOT NULL DEFAULT '[]',
    byproducts_json VARCHAR NOT NULL DEFAULT '[]',
    temperature_c DOUBLE,
    time_text VARCHAR,
    atmosphere VARCHAR,
    pressure_text VARCHAR,
    procedure_text VARCHAR,
    yield_pct DOUBLE,
    stereochemistry_json VARCHAR NOT NULL DEFAULT '{}',
    mechanism_json VARCHAR NOT NULL DEFAULT '[]',
    mechanism_source VARCHAR NOT NULL DEFAULT 'not_available',
    mechanism_confidence DOUBLE NOT NULL DEFAULT 0.0,
    product_inchikey VARCHAR,
    source_doc_ids_json VARCHAR NOT NULL DEFAULT '[]',
    corroboration_count INTEGER NOT NULL DEFAULT 1,
    credibility_score DOUBLE NOT NULL DEFAULT 0.0,
    extractor_version VARCHAR NOT NULL DEFAULT '',
    extracted_at TIMESTAMP NOT NULL
);

-- Silver: normalized analytical data attached to a reaction.
CREATE TABLE IF NOT EXISTS silver_spectra (
    spectrum_id VARCHAR PRIMARY KEY,
    reaction_id VARCHAR NOT NULL,
    kind VARCHAR NOT NULL,
    peaks_json VARCHAR NOT NULL DEFAULT '[]',
    raw_text VARCHAR,
    molecular_weight DOUBLE,
    molecular_formula VARCHAR
);

-- Silver: multi-step synthesis route grouping.
CREATE TABLE IF NOT EXISTS reaction_routes (
    route_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    target_smiles VARCHAR,
    step_count INTEGER NOT NULL DEFAULT 0,
    source_doc_ids_json VARCHAR NOT NULL DEFAULT '[]'
);

-- Gold: one row per training example (feature vector reference + labels).
CREATE TABLE IF NOT EXISTS gold_reaction_features (
    feature_id VARCHAR PRIMARY KEY,
    reaction_id VARCHAR NOT NULL,
    feature_vector_json VARCHAR NOT NULL DEFAULT '[]',
    product_scaffold VARCHAR,
    product_class VARCHAR,
    yield_target DOUBLE,
    dataset_hash VARCHAR,
    created_at TIMESTAMP NOT NULL
);

-- Gold: training/evaluation bookkeeping (accommodates the deferred transformer upgrade path).
CREATE TABLE IF NOT EXISTS gold_model_runs (
    run_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    model_name VARCHAR NOT NULL,
    task VARCHAR NOT NULL,
    dataset_hash VARCHAR,
    split_json VARCHAR NOT NULL DEFAULT '{}',
    preprocessing_summary_json VARCHAR NOT NULL DEFAULT '{}',
    metrics_json VARCHAR NOT NULL DEFAULT '{}',
    artifact_path VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'pending'
);
"""


REACTION_INTELLIGENCE_TABLES = (
    "bronze_documents",
    "bronze_scheme_images",
    "silver_reactions",
    "silver_spectra",
    "reaction_routes",
    "gold_reaction_features",
    "gold_model_runs",
)
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


# MentorOS learning surface was removed during ChemPulse onboarding (Meta-OS M7). The
# mentor_* tables are no longer created. Any pre-existing mentor_* data is left untouched
# (not dropped). See command-center/docs/meta-os/onboarding/chempulse/05-REMOVAL-REVIEW.md.


# Reaction Intelligence (docs/REACTION_INTELLIGENCE.md). Extends the medallion pattern with a
# reaction/mechanism/provenance layer. Applied idempotently the same way GOLD/CORE schemas are
# (ReactionRepository.ensure_schema), so it never disturbs the publication-era tables above.
REACTION_INTELLIGENCE_SCHEMA_SQL = """
-- Bronze: one row per raw ingested source artifact.
CREATE TABLE IF NOT EXISTS bronze_documents (
    doc_id VARCHAR PRIMARY KEY,
    source_kind VARCHAR NOT NULL,
    title VARCHAR,
    doi VARCHAR,
    url VARCHAR,
    local_path VARCHAR,
    credibility_tier INTEGER NOT NULL DEFAULT 3,
    fetched_at TIMESTAMP NOT NULL,
    raw_text VARCHAR,
    meta_json VARCHAR NOT NULL DEFAULT '{}'
);

-- Bronze: figures/reaction schemes extracted from a document, pending structure recognition.
CREATE TABLE IF NOT EXISTS bronze_scheme_images (
    image_id VARCHAR PRIMARY KEY,
    doc_id VARCHAR NOT NULL,
    page INTEGER,
    bbox_json VARCHAR NOT NULL DEFAULT '[]',
    image_path VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'pending'
);

-- Silver: parsed, canonical, one row per reaction step.
CREATE TABLE IF NOT EXISTS silver_reactions (
    reaction_id VARCHAR PRIMARY KEY,
    route_id VARCHAR,
    step_index INTEGER NOT NULL DEFAULT 0,
    reaction_smiles VARCHAR,
    reactants_json VARCHAR NOT NULL DEFAULT '[]',
    reagents_json VARCHAR NOT NULL DEFAULT '[]',
    catalysts_json VARCHAR NOT NULL DEFAULT '[]',
    solvents_json VARCHAR NOT NULL DEFAULT '[]',
    products_json VARCHAR NOT NULL DEFAULT '[]',
    byproducts_json VARCHAR NOT NULL DEFAULT '[]',
    temperature_c DOUBLE,
    time_text VARCHAR,
    atmosphere VARCHAR,
    pressure_text VARCHAR,
    procedure_text VARCHAR,
    yield_pct DOUBLE,
    stereochemistry_json VARCHAR NOT NULL DEFAULT '{}',
    mechanism_json VARCHAR NOT NULL DEFAULT '[]',
    mechanism_source VARCHAR NOT NULL DEFAULT 'not_available',
    mechanism_confidence DOUBLE NOT NULL DEFAULT 0.0,
    product_inchikey VARCHAR,
    source_doc_ids_json VARCHAR NOT NULL DEFAULT '[]',
    corroboration_count INTEGER NOT NULL DEFAULT 1,
    credibility_score DOUBLE NOT NULL DEFAULT 0.0,
    extractor_version VARCHAR NOT NULL DEFAULT '',
    extracted_at TIMESTAMP NOT NULL
);

-- Silver: normalized analytical data attached to a reaction.
CREATE TABLE IF NOT EXISTS silver_spectra (
    spectrum_id VARCHAR PRIMARY KEY,
    reaction_id VARCHAR NOT NULL,
    kind VARCHAR NOT NULL,
    peaks_json VARCHAR NOT NULL DEFAULT '[]',
    raw_text VARCHAR,
    molecular_weight DOUBLE,
    molecular_formula VARCHAR
);

-- Silver: multi-step synthesis route grouping.
CREATE TABLE IF NOT EXISTS reaction_routes (
    route_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    target_smiles VARCHAR,
    step_count INTEGER NOT NULL DEFAULT 0,
    source_doc_ids_json VARCHAR NOT NULL DEFAULT '[]'
);

-- Gold: one row per training example (feature vector reference + labels).
CREATE TABLE IF NOT EXISTS gold_reaction_features (
    feature_id VARCHAR PRIMARY KEY,
    reaction_id VARCHAR NOT NULL,
    feature_vector_json VARCHAR NOT NULL DEFAULT '[]',
    product_scaffold VARCHAR,
    product_class VARCHAR,
    yield_target DOUBLE,
    dataset_hash VARCHAR,
    created_at TIMESTAMP NOT NULL
);

-- Gold: training/evaluation bookkeeping (accommodates the deferred transformer upgrade path).
CREATE TABLE IF NOT EXISTS gold_model_runs (
    run_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    model_name VARCHAR NOT NULL,
    task VARCHAR NOT NULL,
    dataset_hash VARCHAR,
    split_json VARCHAR NOT NULL DEFAULT '{}',
    preprocessing_summary_json VARCHAR NOT NULL DEFAULT '{}',
    metrics_json VARCHAR NOT NULL DEFAULT '{}',
    artifact_path VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'pending'
);
"""


REACTION_INTELLIGENCE_TABLES = (
    "bronze_documents",
    "bronze_scheme_images",
    "silver_reactions",
    "silver_spectra",
    "reaction_routes",
    "gold_reaction_features",
    "gold_model_runs",
)
