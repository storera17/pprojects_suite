from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from typing import Any

import duckdb

from backend.chemistry.rdkit_engine import ChemistryEngine
from backend.data.db import available_table_name, get_connection, get_db_path, query_records
from backend.data.schemas import REACTION_INTELLIGENCE_SCHEMA_SQL

# Credibility weight per source tier (1 = peer-reviewed / curated dataset ... 3 = unverified).
_TIER_WEIGHT: dict[int, float] = {1: 1.0, 2: 0.6, 3: 0.3}

_SCHEMA_READY_PATH: str | None = None


class ReactionRepository:
    """Read/write access to the reaction, provenance, and model-run tables."""

    # -- schema -----------------------------------------------------------------

    @staticmethod
    def ensure_schema() -> None:
        global _SCHEMA_READY_PATH
        db_path = str(get_db_path())
        if _SCHEMA_READY_PATH == db_path:
            return
        with _connection_with_retry(read_only=False) as con:
            con.execute(REACTION_INTELLIGENCE_SCHEMA_SQL)
        _SCHEMA_READY_PATH = db_path

    # -- provenance / credibility helpers --------------------------------------

    @staticmethod
    def tier_weight(tier: int | None) -> float:
        """Credibility weight for a source tier; unknown tiers get the lowest weight."""
        return _TIER_WEIGHT.get(int(tier) if tier is not None else 3, _TIER_WEIGHT[3])

    @staticmethod
    def compute_credibility_score(tiers: list[int], corroboration_count: int) -> float:
        """Combine best-available source quality with independent corroboration into [0, 1].

        Quality is the strongest tier among the sources (best evidence available);
        corroboration saturates at three independent sources. The two are blended 70/30
        so a lone tier-1 paper still outranks three tier-3 mentions, but corroboration
        meaningfully lifts a claim.
        """
        quality = max((ReactionRepository.tier_weight(t) for t in tiers), default=_TIER_WEIGHT[3])
        corroboration = min(1.0, max(1, int(corroboration_count)) / 3.0)
        return round(0.7 * quality + 0.3 * corroboration, 4)

    @staticmethod
    def reaction_signature(reactants: list[str], products: list[str]) -> str:
        """Stable id for a reaction from its canonical reactant/product structures.

        Same chemistry (regardless of source or ordering) hashes to the same id, which is
        what lets multi-source reports collapse into one corroborated row.
        """
        canon_reactants = sorted(_canonical_many(reactants))
        canon_products = sorted(_canonical_many(products))
        raw = ">>".join([".".join(canon_reactants), ".".join(canon_products)])
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
        return f"rxn_{digest}"

    # -- bronze writes ----------------------------------------------------------

    @staticmethod
    def upsert_document(
        doc_id: str,
        source_kind: str,
        *,
        title: str = "",
        doi: str = "",
        url: str = "",
        local_path: str = "",
        credibility_tier: int = 3,
        raw_text: str | None = None,
        meta: dict[str, Any] | None = None,
        fetched_at: datetime | None = None,
    ) -> str:
        ReactionRepository.ensure_schema()
        stamp = fetched_at or _utc_now()
        with _connection_with_retry(read_only=False) as con:
            con.execute(
                """
                INSERT INTO bronze_documents (
                    doc_id, source_kind, title, doi, url, local_path,
                    credibility_tier, fetched_at, raw_text, meta_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    source_kind = excluded.source_kind,
                    title = excluded.title,
                    doi = excluded.doi,
                    url = excluded.url,
                    local_path = excluded.local_path,
                    credibility_tier = excluded.credibility_tier,
                    fetched_at = excluded.fetched_at,
                    raw_text = excluded.raw_text,
                    meta_json = excluded.meta_json
                """,
                [
                    doc_id,
                    source_kind,
                    title,
                    doi,
                    url,
                    local_path,
                    int(credibility_tier),
                    stamp,
                    raw_text,
                    json.dumps(meta or {}),
                ],
            )
        return doc_id

    @staticmethod
    def add_scheme_image(
        image_id: str,
        doc_id: str,
        *,
        page: int | None = None,
        bbox: list[float] | None = None,
        image_path: str = "",
        status: str = "pending",
    ) -> str:
        ReactionRepository.ensure_schema()
        with _connection_with_retry(read_only=False) as con:
            con.execute(
                """
                INSERT INTO bronze_scheme_images (image_id, doc_id, page, bbox_json, image_path, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(image_id) DO UPDATE SET
                    doc_id = excluded.doc_id,
                    page = excluded.page,
                    bbox_json = excluded.bbox_json,
                    image_path = excluded.image_path,
                    status = excluded.status
                """,
                [image_id, doc_id, page, json.dumps(bbox or []), image_path, status],
            )
        return image_id

    # -- silver writes ----------------------------------------------------------

    @staticmethod
    def upsert_reaction(record: dict[str, Any]) -> dict[str, Any]:
        """Insert or corroborate a reaction, deduplicated by canonical structure.

        Roles are canonicalized through RDKit. If a reaction with the same structural
        signature already exists, its source documents are merged (not overwritten),
        ``corroboration_count`` becomes the number of distinct sources, and
        ``credibility_score`` is recomputed. Conflicting scalar values (e.g. a second
        paper's yield) are preserved under ``meta``/``stereochemistry`` by the caller;
        this method never silently discards the incoming record's provenance.
        """
        ReactionRepository.ensure_schema()

        reactants = _canonical_many(record.get("reactants") or [])
        products = _canonical_many(record.get("products") or [])
        reaction_id = record.get("reaction_id") or ReactionRepository.reaction_signature(reactants, products)

        incoming_docs = [str(d) for d in (record.get("source_doc_ids") or []) if str(d)]
        incoming_tier = int(record.get("credibility_tier", 3))

        existing = ReactionRepository.get_reaction(reaction_id)
        if existing:
            merged_docs = _unique_preserving_order([*existing.get("source_doc_ids", []), *incoming_docs])
            tiers = _document_tiers(merged_docs) or [incoming_tier]
        else:
            merged_docs = _unique_preserving_order(incoming_docs)
            tiers = _document_tiers(merged_docs) or [incoming_tier]

        corroboration = max(1, len(merged_docs))
        credibility = ReactionRepository.compute_credibility_score(tiers, corroboration)

        product_inchikey = record.get("product_inchikey") or _primary_inchikey(products)
        row = {
            "reaction_id": reaction_id,
            "route_id": record.get("route_id"),
            "step_index": int(record.get("step_index", 0)),
            "reaction_smiles": record.get("reaction_smiles") or _reaction_smiles(reactants, products),
            "reactants_json": json.dumps(reactants),
            "reagents_json": json.dumps(_canonical_many(record.get("reagents") or [])),
            "catalysts_json": json.dumps(_canonical_many(record.get("catalysts") or [])),
            "solvents_json": json.dumps(_canonical_many(record.get("solvents") or [])),
            "products_json": json.dumps(products),
            "byproducts_json": json.dumps(_canonical_many(record.get("byproducts") or [])),
            "temperature_c": _as_float(record.get("temperature_c")),
            "time_text": record.get("time_text"),
            "atmosphere": record.get("atmosphere"),
            "pressure_text": record.get("pressure_text"),
            "procedure_text": record.get("procedure_text"),
            "yield_pct": _as_float(record.get("yield_pct")),
            "stereochemistry_json": json.dumps(record.get("stereochemistry") or {}),
            "mechanism_json": json.dumps(record.get("mechanism") or []),
            "mechanism_source": record.get("mechanism_source") or "not_available",
            "mechanism_confidence": _as_float(record.get("mechanism_confidence")) or 0.0,
            "product_inchikey": product_inchikey,
            "source_doc_ids_json": json.dumps(merged_docs),
            "corroboration_count": corroboration,
            "credibility_score": credibility,
            "extractor_version": record.get("extractor_version") or "",
            "extracted_at": record.get("extracted_at") or _utc_now(),
        }

        columns = list(row.keys())
        placeholders = ", ".join(["?"] * len(columns))
        updates = ", ".join(f"{col} = excluded.{col}" for col in columns if col != "reaction_id")
        with _connection_with_retry(read_only=False) as con:
            con.execute(
                f"""
                INSERT INTO silver_reactions ({", ".join(columns)})
                VALUES ({placeholders})
                ON CONFLICT(reaction_id) DO UPDATE SET {updates}
                """,
                [row[col] for col in columns],
            )
        return {**row, "source_doc_ids": merged_docs}

    @staticmethod
    def add_spectrum(
        reaction_id: str,
        kind: str,
        *,
        spectrum_id: str = "",
        peaks: list[Any] | None = None,
        raw_text: str = "",
        molecular_weight: float | None = None,
        molecular_formula: str = "",
    ) -> str:
        ReactionRepository.ensure_schema()
        resolved_id = spectrum_id or _spectrum_id(reaction_id, kind, raw_text)
        with _connection_with_retry(read_only=False) as con:
            con.execute(
                """
                INSERT INTO silver_spectra (
                    spectrum_id, reaction_id, kind, peaks_json, raw_text, molecular_weight, molecular_formula
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(spectrum_id) DO UPDATE SET
                    reaction_id = excluded.reaction_id,
                    kind = excluded.kind,
                    peaks_json = excluded.peaks_json,
                    raw_text = excluded.raw_text,
                    molecular_weight = excluded.molecular_weight,
                    molecular_formula = excluded.molecular_formula
                """,
                [
                    resolved_id,
                    reaction_id,
                    kind,
                    json.dumps(peaks or []),
                    raw_text,
                    molecular_weight,
                    molecular_formula,
                ],
            )
        return resolved_id

    @staticmethod
    def upsert_route(
        route_id: str,
        *,
        title: str = "",
        target_smiles: str = "",
        step_count: int = 0,
        source_doc_ids: list[str] | None = None,
    ) -> str:
        ReactionRepository.ensure_schema()
        with _connection_with_retry(read_only=False) as con:
            con.execute(
                """
                INSERT INTO reaction_routes (route_id, title, target_smiles, step_count, source_doc_ids_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(route_id) DO UPDATE SET
                    title = excluded.title,
                    target_smiles = excluded.target_smiles,
                    step_count = excluded.step_count,
                    source_doc_ids_json = excluded.source_doc_ids_json
                """,
                [route_id, title, target_smiles, int(step_count), json.dumps(source_doc_ids or [])],
            )
        return route_id

    # -- gold writes ------------------------------------------------------------

    @staticmethod
    def write_feature(
        reaction_id: str,
        *,
        feature_id: str = "",
        feature_vector: list[float] | None = None,
        product_scaffold: str = "",
        product_class: str = "",
        yield_target: float | None = None,
        dataset_hash: str = "",
    ) -> str:
        ReactionRepository.ensure_schema()
        resolved_id = feature_id or f"feat_{reaction_id}"
        with _connection_with_retry(read_only=False) as con:
            con.execute(
                """
                INSERT INTO gold_reaction_features (
                    feature_id, reaction_id, feature_vector_json, product_scaffold,
                    product_class, yield_target, dataset_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(feature_id) DO UPDATE SET
                    reaction_id = excluded.reaction_id,
                    feature_vector_json = excluded.feature_vector_json,
                    product_scaffold = excluded.product_scaffold,
                    product_class = excluded.product_class,
                    yield_target = excluded.yield_target,
                    dataset_hash = excluded.dataset_hash,
                    created_at = excluded.created_at
                """,
                [
                    resolved_id,
                    reaction_id,
                    json.dumps(feature_vector or []),
                    product_scaffold,
                    product_class,
                    yield_target,
                    dataset_hash,
                    _utc_now(),
                ],
            )
        return resolved_id

    @staticmethod
    def record_model_run(
        run_id: str,
        model_name: str,
        task: str,
        *,
        dataset_hash: str = "",
        split: dict[str, Any] | None = None,
        preprocessing_summary: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        artifact_path: str = "",
        status: str = "completed",
        created_at: datetime | None = None,
    ) -> str:
        ReactionRepository.ensure_schema()
        with _connection_with_retry(read_only=False) as con:
            con.execute(
                """
                INSERT INTO gold_model_runs (
                    run_id, created_at, model_name, task, dataset_hash, split_json,
                    preprocessing_summary_json, metrics_json, artifact_path, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    created_at = excluded.created_at,
                    model_name = excluded.model_name,
                    task = excluded.task,
                    dataset_hash = excluded.dataset_hash,
                    split_json = excluded.split_json,
                    preprocessing_summary_json = excluded.preprocessing_summary_json,
                    metrics_json = excluded.metrics_json,
                    artifact_path = excluded.artifact_path,
                    status = excluded.status
                """,
                [
                    run_id,
                    created_at or _utc_now(),
                    model_name,
                    task,
                    dataset_hash,
                    json.dumps(split or {}),
                    json.dumps(preprocessing_summary or {}),
                    json.dumps(metrics or {}),
                    artifact_path,
                    status,
                ],
            )
        return run_id

    # -- reads ------------------------------------------------------------------

    @staticmethod
    def list_documents(limit: int = 500) -> list[dict[str, Any]]:
        if not available_table_name("bronze_documents"):
            return []
        rows = query_records(
            """
            SELECT doc_id, source_kind, title, doi, url, local_path,
                   credibility_tier, fetched_at, meta_json
            FROM bronze_documents
            ORDER BY fetched_at DESC, doc_id ASC
            LIMIT ?
            """,
            [limit],
        )
        for row in rows:
            row["meta"] = _load_json(row.pop("meta_json"), {})
        return rows

    @staticmethod
    def list_reactions(limit: int = 200) -> list[dict[str, Any]]:
        if not available_table_name("silver_reactions"):
            return []
        rows = query_records(
            """
            SELECT * FROM silver_reactions
            ORDER BY credibility_score DESC, corroboration_count DESC, reaction_id ASC
            LIMIT ?
            """,
            [limit],
        )
        return [_hydrate_reaction(row) for row in rows]

    @staticmethod
    def list_reactions_summary(limit: int = 200) -> list[dict[str, Any]]:
        """Lightweight list view: only the columns list/graph consumers need.

        Avoids ``SELECT *`` + full JSON hydration (mechanism, spectra, stereochemistry,
        provenance) for every row — those are fetched on demand via ``get_reaction``.
        """
        if not available_table_name("silver_reactions"):
            return []
        rows = query_records(
            """
            SELECT reaction_id, reaction_smiles, reactants_json, products_json, yield_pct,
                   mechanism_source, corroboration_count, credibility_score
            FROM silver_reactions
            ORDER BY credibility_score DESC, corroboration_count DESC, reaction_id ASC
            LIMIT ?
            """,
            [limit],
        )
        for row in rows:
            row["reactants"] = _load_json(row.pop("reactants_json"), [])
            row["products"] = _load_json(row.pop("products_json"), [])
        return rows

    @staticmethod
    def get_reaction(reaction_id: str) -> dict[str, Any] | None:
        if not reaction_id or not available_table_name("silver_reactions"):
            return None
        rows = query_records("SELECT * FROM silver_reactions WHERE reaction_id = ? LIMIT 1", [reaction_id])
        if not rows:
            return None
        reaction = _hydrate_reaction(rows[0])
        reaction["spectra"] = ReactionRepository.spectra_for_reaction(reaction_id)
        return reaction

    @staticmethod
    def spectra_for_reaction(reaction_id: str) -> list[dict[str, Any]]:
        if not available_table_name("silver_spectra"):
            return []
        rows = query_records(
            "SELECT * FROM silver_spectra WHERE reaction_id = ? ORDER BY kind ASC, spectrum_id ASC",
            [reaction_id],
        )
        for row in rows:
            row["peaks"] = _load_json(row.pop("peaks_json"), [])
        return rows

    @staticmethod
    def list_model_runs(limit: int = 100) -> list[dict[str, Any]]:
        if not available_table_name("gold_model_runs"):
            return []
        rows = query_records(
            "SELECT * FROM gold_model_runs ORDER BY created_at DESC, run_id ASC LIMIT ?",
            [limit],
        )
        for row in rows:
            row["split"] = _load_json(row.pop("split_json"), {})
            row["preprocessing_summary"] = _load_json(row.pop("preprocessing_summary_json"), {})
            row["metrics"] = _load_json(row.pop("metrics_json"), {})
        return rows

    @staticmethod
    def reaction_count() -> int:
        if not available_table_name("silver_reactions"):
            return 0
        rows = query_records("SELECT COUNT(*)::INTEGER AS n FROM silver_reactions")
        return int(rows[0]["n"]) if rows else 0


# -- module-level helpers -------------------------------------------------------


def _hydrate_reaction(row: dict[str, Any]) -> dict[str, Any]:
    """Turn a raw silver_reactions row into JSON-decoded roles/mechanism/provenance."""
    role_fields = {
        "reactants_json": "reactants",
        "reagents_json": "reagents",
        "catalysts_json": "catalysts",
        "solvents_json": "solvents",
        "products_json": "products",
        "byproducts_json": "byproducts",
    }
    for raw_key, clean_key in role_fields.items():
        row[clean_key] = _load_json(row.pop(raw_key), [])
    row["stereochemistry"] = _load_json(row.pop("stereochemistry_json"), {})
    row["mechanism"] = _load_json(row.pop("mechanism_json"), [])
    row["source_doc_ids"] = _load_json(row.pop("source_doc_ids_json"), [])
    return row


def _document_tiers(doc_ids: list[str]) -> list[int]:
    if not doc_ids or not available_table_name("bronze_documents"):
        return []
    placeholders = ", ".join(["?"] * len(doc_ids))
    rows = query_records(
        f"SELECT credibility_tier FROM bronze_documents WHERE doc_id IN ({placeholders})",
        doc_ids,
    )
    return [int(row["credibility_tier"]) for row in rows if row.get("credibility_tier") is not None]


def _canonical_many(smiles_list: list[str]) -> list[str]:
    canonical: list[str] = []
    for smiles in smiles_list:
        text = str(smiles).strip()
        if not text:
            continue
        result, error = ChemistryEngine.canonicalize_smiles(text)
        canonical.append(result if result and not error else text)
    return canonical


def _primary_inchikey(products: list[str]) -> str | None:
    for smiles in products:
        processed = ChemistryEngine.process_smiles(smiles)
        if processed and processed.get("inchi_key"):
            return str(processed["inchi_key"])
    return None


def _reaction_smiles(reactants: list[str], products: list[str]) -> str:
    return f"{'.'.join(reactants)}>>{'.'.join(products)}"


def _spectrum_id(reaction_id: str, kind: str, raw_text: str) -> str:
    digest = hashlib.sha1(f"{reaction_id}|{kind}|{raw_text}".encode()).hexdigest()[:12]
    return f"spec_{digest}"


def _unique_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_json(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _connection_with_retry(read_only: bool = False, attempts: int = 60, delay_seconds: float = 2.0):
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            return get_connection(read_only=read_only)
        except (duckdb.Error, OSError) as exc:
            last_error = exc
            if "lock" not in str(exc).lower() and "being used by another process" not in str(exc).lower():
                raise
            time.sleep(delay_seconds)
    raise RuntimeError(f"Timed out waiting for DuckDB database lock: {last_error}")
