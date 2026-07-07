from __future__ import annotations

from typing import Any

from backend.data.db import available_table_name, query_records

class GoldRepository:
    """
    Read-only access to the shaped dashboard tables.
    """

    @staticmethod
    def top_scaffolds(limit: int = 10) -> list[dict[str, Any]]:
        if not available_table_name("gold_scaffold_stats"):
            return []

        return query_records(
            """
            SELECT
                scaffold AS name,
                evidence_count AS count,
                total_funding,
                top_funder,
                representative_doi
            FROM gold_scaffold_stats
            ORDER BY evidence_count DESC, scaffold ASC
            LIMIT ?
            """,
            [limit],
        )

    @staticmethod
    def top_scaffolds_for_clusters(cluster_ids: list[str], limit: int = 10) -> list[dict[str, Any]]:
        points_table = available_table_name("gold_cluster_points", "gold_galaxy_points")
        if not cluster_ids or not points_table or not available_table_name("gold_scaffold_stats"):
            return []

        placeholders = ", ".join(["?"] * len(cluster_ids))
        return query_records(
            f"""
            WITH filtered AS (
                SELECT scaffold, funding_usd
                FROM {points_table}
                WHERE cluster_id IN ({placeholders})
            )
            SELECT
                f.scaffold AS name,
                COUNT(*)::INTEGER AS count,
                SUM(f.funding_usd) AS total_funding,
                COALESCE(MAX(gs.top_funder), '') AS top_funder,
                COALESCE(MAX(gs.representative_doi), '') AS representative_doi
            FROM filtered AS f
            LEFT JOIN gold_scaffold_stats AS gs
                ON f.scaffold = gs.scaffold
            GROUP BY f.scaffold
            ORDER BY count DESC, total_funding DESC, name ASC
            LIMIT ?
            """,
            [*cluster_ids, limit],
        )

    @staticmethod
    def scaffold_detail(scaffold_name: str) -> dict[str, Any] | None:
        if not scaffold_name.strip() or not available_table_name("gold_scaffold_stats"):
            return None

        rows = query_records(
            """
            SELECT
                scaffold AS name,
                evidence_count AS count,
                total_funding,
                top_funder,
                representative_doi
            FROM gold_scaffold_stats
            WHERE LOWER(scaffold) = ?
            LIMIT 1
            """,
            [scaffold_name.strip().lower()],
        )
        return rows[0] if rows else None

    @staticmethod
    def search_scaffolds(query: str, limit: int = 10) -> list[dict[str, Any]]:
        if not query.strip() or not available_table_name("gold_scaffold_stats"):
            return []

        search_term = f"%{query.strip().lower()}%"
        return query_records(
            """
            SELECT
                scaffold AS name,
                evidence_count AS count,
                total_funding,
                top_funder,
                representative_doi
            FROM gold_scaffold_stats
            WHERE
                LOWER(scaffold) LIKE ?
                OR LOWER(top_funder) LIKE ?
                OR LOWER(representative_doi) LIKE ?
            ORDER BY evidence_count DESC, total_funding DESC, scaffold ASC
            LIMIT ?
            """,
            [search_term, search_term, search_term, limit],
        )

    @staticmethod
    def scaffold_entries(limit: int = 1000, query: str = "") -> list[dict[str, Any]]:
        if not available_table_name("scaffold_entries"):
            return []

        params: list[Any] = []
        where_clause = "WHERE status = 'active'"
        if query.strip():
            term = f"%{query.strip().lower()}%"
            where_clause += """
                AND (
                    LOWER(name) LIKE ?
                    OR LOWER(category) LIKE ?
                    OR LOWER(family) LIKE ?
                    OR LOWER(canonical_smiles) LIKE ?
                )
            """
            params.extend([term, term, term, term])
        params.append(limit)
        return query_records(
            f"""
            SELECT
                name,
                category,
                family,
                canonical_smiles,
                source,
                status
            FROM scaffold_entries
            {where_clause}
            ORDER BY category ASC, family ASC, name ASC
            LIMIT ?
            """,
            params,
        )

    @staticmethod
    def funding_slices() -> list[dict[str, Any]]:
        if not available_table_name("gold_scaffold_stats"):
            return []

        return query_records(
            """
            SELECT top_funder AS label, SUM(total_funding) AS total_funding
            FROM gold_scaffold_stats
            GROUP BY top_funder
            ORDER BY total_funding DESC, label ASC
            """
        )

    @staticmethod
    def funding_slices_detailed() -> list[dict[str, Any]]:
        if not available_table_name("gold_scaffold_stats"):
            return []

        return query_records(
            """
            SELECT
                top_funder AS label,
                SUM(total_funding) AS total_funding,
                SUM(evidence_count)::INTEGER AS evidence_count,
                COUNT(*)::INTEGER AS scaffold_count
            FROM gold_scaffold_stats
            GROUP BY top_funder
            ORDER BY total_funding DESC, label ASC
            """
        )

    @staticmethod
    def funding_slices_for_clusters(cluster_ids: list[str]) -> list[dict[str, Any]]:
        points_table = available_table_name("gold_cluster_points", "gold_galaxy_points")
        if not cluster_ids or not points_table or not available_table_name("gold_scaffold_stats"):
            return []

        placeholders = ", ".join(["?"] * len(cluster_ids))
        return query_records(
            f"""
            SELECT
                COALESCE(gs.top_funder, 'Unknown') AS label,
                SUM(gp.funding_usd) AS total_funding
            FROM {points_table} AS gp
            LEFT JOIN gold_scaffold_stats AS gs
                ON gp.scaffold = gs.scaffold
            WHERE gp.cluster_id IN ({placeholders})
            GROUP BY label
            ORDER BY total_funding DESC, label ASC
            """,
            cluster_ids,
        )

    @staticmethod
    def journal_publication_slices() -> list[dict[str, Any]]:
        if not available_table_name("gold_scaffold_stats"):
            return []

        return query_records(
            """
            SELECT
                COALESCE(NULLIF(top_funder, ''), 'Unknown source') AS label,
                SUM(evidence_count)::INTEGER AS publication_count,
                COUNT(*)::INTEGER AS scaffold_count,
                COALESCE(SUM(total_funding), 0) AS funding_usd
            FROM gold_scaffold_stats
            GROUP BY label
            ORDER BY publication_count DESC, scaffold_count DESC, label ASC
            """
        )

    @staticmethod
    def journal_publication_slices_for_clusters(cluster_ids: list[str]) -> list[dict[str, Any]]:
        points_table = available_table_name("gold_cluster_points", "gold_galaxy_points")
        if not cluster_ids or not points_table or not available_table_name("gold_scaffold_stats"):
            return []

        placeholders = ", ".join(["?"] * len(cluster_ids))
        return query_records(
            f"""
            WITH selected_scaffolds AS (
                SELECT DISTINCT scaffold
                FROM {points_table}
                WHERE cluster_id IN ({placeholders})
            )
            SELECT
                COALESCE(NULLIF(gs.top_funder, ''), 'Unknown source') AS label,
                SUM(gs.evidence_count)::INTEGER AS publication_count,
                COUNT(*)::INTEGER AS scaffold_count,
                COALESCE(SUM(gs.total_funding), 0) AS funding_usd
            FROM selected_scaffolds AS ss
            JOIN gold_scaffold_stats AS gs
                ON gs.scaffold = ss.scaffold
            GROUP BY label
            ORDER BY publication_count DESC, scaffold_count DESC, label ASC
            """,
            cluster_ids,
        )

    @staticmethod
    def scaffold_journal_breakdown(limit: int = 10) -> list[dict[str, Any]]:
        if not available_table_name("gold_scaffold_stats"):
            return []

        return query_records(
            """
            SELECT
                scaffold,
                COALESCE(NULLIF(top_funder, ''), 'Unknown source') AS journal,
                evidence_count::INTEGER AS publication_count,
                total_funding AS funding_usd
            FROM gold_scaffold_stats
            ORDER BY evidence_count DESC, scaffold ASC
            LIMIT ?
            """,
            [limit],
        )

    @staticmethod
    def publication_year_counts() -> list[dict[str, Any]]:
        if not available_table_name("bronze_core_publications"):
            return []

        return query_records(
            """
            SELECT
                COALESCE(year_published, 0)::INTEGER AS year,
                COUNT(*)::INTEGER AS publication_count
            FROM bronze_core_publications
            WHERE year_published IS NOT NULL
            GROUP BY year
            ORDER BY year ASC
            """
        )

    @staticmethod
    def overview_metrics() -> dict[str, Any]:
        points_table = available_table_name("gold_cluster_points", "gold_galaxy_points")
        if not points_table:
            return {}

        records = query_records(
            f"""
            SELECT
                COUNT(*)::INTEGER AS total_documents,
                COALESCE(SUM(funding_usd), 0) AS total_funding_usd
            FROM {points_table}
            """
        )
        return records[0] if records else {}

    @staticmethod
    def scaffold_overview_metrics() -> dict[str, Any]:
        if not available_table_name("gold_scaffold_stats"):
            return {}

        records = query_records(
            """
            SELECT
                COUNT(*)::INTEGER AS active_scaffolds,
                COALESCE(SUM(evidence_count), 0)::INTEGER AS total_evidence_records,
                COALESCE(SUM(total_funding), 0) AS total_funding_usd
            FROM gold_scaffold_stats
            """
        )
        return records[0] if records else {}

    @staticmethod
    def galaxy_points() -> list[dict[str, Any]]:
        points_table = available_table_name("gold_cluster_points", "gold_galaxy_points")
        if not points_table or not available_table_name("gold_scaffold_stats"):
            return []

        return query_records(
            f"""
            WITH point_rollup AS (
                SELECT
                    scaffold,
                    AVG(x) AS x,
                    AVG(y) AS y,
                    AVG(z) AS z,
                    MIN(cluster_id) AS cluster_id,
                    COUNT(*)::INTEGER AS molecule_count,
                    SUM(funding_usd) AS point_funding
                FROM {points_table}
                GROUP BY scaffold
            )
            SELECT
                'scaffold_' || LOWER(REPLACE(gs.scaffold, ' ', '_')) AS molecule_id,
                'scaffold_' || LOWER(REPLACE(gs.scaffold, ' ', '_')) AS id,
                pr.x,
                pr.y,
                pr.z,
                COALESCE(pr.cluster_id, 'cluster_scaffold_' || LPAD(CAST(ROW_NUMBER() OVER (ORDER BY gs.evidence_count DESC, gs.scaffold) AS VARCHAR), 2, '0')) AS cluster_id,
                COALESCE(pr.cluster_id, 'scaffold_centroid') AS cluster,
                gs.scaffold,
                gs.total_funding AS funding_usd,
                gs.evidence_count,
                gs.representative_doi,
                gs.top_funder,
                COALESCE(pr.molecule_count, 0) AS molecule_count,
                gs.evidence_count AS publication_count,
                'Scaffold evidence' AS top_topic
            FROM gold_scaffold_stats AS gs
            LEFT JOIN point_rollup AS pr
                ON pr.scaffold = gs.scaffold
            ORDER BY gs.evidence_count DESC, gs.total_funding DESC, gs.scaffold ASC
            """
        )

    @staticmethod
    def search_galaxy_points(query: str) -> list[dict[str, Any]]:
        points_table = available_table_name("gold_cluster_points", "gold_galaxy_points")
        if not query.strip() or not points_table or not available_table_name("gold_scaffold_stats"):
            return []

        search_term = f"%{query.strip().lower()}%"
        return query_records(
            f"""
            WITH point_rollup AS (
                SELECT
                    scaffold,
                    AVG(x) AS x,
                    AVG(y) AS y,
                    AVG(z) AS z,
                    MIN(cluster_id) AS cluster_id,
                    COUNT(*)::INTEGER AS molecule_count,
                    SUM(funding_usd) AS point_funding
                FROM {points_table}
                GROUP BY scaffold
            )
            SELECT
                'scaffold_' || LOWER(REPLACE(gs.scaffold, ' ', '_')) AS molecule_id,
                'scaffold_' || LOWER(REPLACE(gs.scaffold, ' ', '_')) AS id,
                pr.x,
                pr.y,
                pr.z,
                COALESCE(pr.cluster_id, 'cluster_scaffold_' || LPAD(CAST(ROW_NUMBER() OVER (ORDER BY gs.evidence_count DESC, gs.scaffold) AS VARCHAR), 2, '0')) AS cluster_id,
                COALESCE(pr.cluster_id, 'scaffold_centroid') AS cluster,
                gs.scaffold,
                gs.total_funding AS funding_usd,
                gs.evidence_count,
                gs.representative_doi,
                gs.top_funder,
                COALESCE(pr.molecule_count, 0) AS molecule_count,
                gs.evidence_count AS publication_count,
                'Scaffold evidence' AS top_topic
            FROM gold_scaffold_stats AS gs
            LEFT JOIN point_rollup AS pr
                ON pr.scaffold = gs.scaffold
            WHERE
                LOWER('scaffold_' || gs.scaffold) LIKE ?
                OR LOWER(COALESCE(pr.cluster_id, '')) LIKE ?
                OR LOWER(gs.scaffold) LIKE ?
                OR LOWER(COALESCE(gs.top_funder, '')) LIKE ?
                OR LOWER(COALESCE(gs.representative_doi, '')) LIKE ?
            ORDER BY gs.evidence_count DESC, gs.total_funding DESC, gs.scaffold ASC
            """,
            [search_term, search_term, search_term, search_term, search_term],
        )


