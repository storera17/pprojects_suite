from __future__ import annotations


def handle_galaxy_selection(state, selection=None) -> None:
    if not selection:
        points = []
    elif isinstance(selection, dict):
        points = selection.get("points", [])
    else:
        points = selection

    cluster_ids: list[str] = []
    molecule_ids: list[str] = []
    scaffold_names: list[str] = []
    for point in points:
        customdata = getattr(point, "customdata", None)
        if customdata is None and isinstance(point, dict):
            customdata = point.get("customdata")
        customdata = customdata or []
        if customdata:
            cluster_id = customdata[0]
            if cluster_id and cluster_id not in cluster_ids:
                cluster_ids.append(cluster_id)
            if len(customdata) > 1:
                molecule_id = customdata[1]
                if molecule_id and molecule_id not in molecule_ids:
                    molecule_ids.append(molecule_id)
            if len(customdata) > 2:
                scaffold_name = customdata[2]
                if scaffold_name and scaffold_name not in scaffold_names:
                    scaffold_names.append(scaffold_name)
    state.selected_molecule_ids = molecule_ids
    state.selected_point_ids = molecule_ids
    state.selected_scaffold = scaffold_names[0] if len(scaffold_names) == 1 else ""
    state._update_selection_totals()
    state.select_cluster(cluster_ids)


def clear_selection(state) -> None:
    state.selected_cluster_ids = []
    state.selected_scaffold = ""
    state.selected_molecule_ids = []
    state.selected_point_ids = []
    state.selected_evidence_count = 0
    state.selected_funding_total = 0.0
    state._refresh_dashboard_view()
    state.persist_current_payload("desktop-clear-selection")


def reset_dashboard(state) -> None:
    state.search_query = ""
    state.selected_cluster_ids = []
    state.selected_scaffold = ""
    state.selected_molecule_ids = []
    state.selected_point_ids = []
    state.selected_evidence_count = 0
    state.selected_funding_total = 0.0
    state._refresh_dashboard_view()
    state.persist_current_payload("desktop-reset")


def set_search_query(state, value: str) -> None:
    state.search_query = value.strip()
    state.selected_cluster_ids = []
    state.selected_scaffold = ""
    state.selected_molecule_ids = []
    state.selected_point_ids = []
    state.selected_evidence_count = 0
    state.selected_funding_total = 0.0
    state._refresh_dashboard_view()
    state.persist_current_payload("desktop-search")


def select_cluster(state, cluster_ids: list[str]) -> None:
    unique_cluster_ids = list(dict.fromkeys(cluster_ids))
    state.selected_cluster_ids = unique_cluster_ids
    if len(state.selected_point_ids) != 1:
        state.selected_scaffold = ""
    state._refresh_dashboard_view()
    state.persist_current_payload("desktop-cluster-selection")


def select_scaffold(state, scaffold_name: str) -> None:
    state.selected_scaffold = scaffold_name
    state.selected_cluster_ids = []
    state.selected_point_ids = []
    state.selected_molecule_ids = []
    state._refresh_dashboard_view()
    state.persist_current_payload("desktop-scaffold-selection")


def update_selection_totals(state) -> None:
    selected_points = [
        point
        for point in state.galaxy_points
        if (state.selected_scaffold and point.get("scaffold") == state.selected_scaffold)
        or (state.selected_cluster_ids and point.get("cluster_id") in state.selected_cluster_ids)
        or (state.selected_point_ids and point.get("molecule_id", point.get("id", "")) in state.selected_point_ids)
    ]
    unique_scaffolds = {}
    for point in selected_points:
        scaffold = point.get("scaffold")
        if scaffold and scaffold not in unique_scaffolds:
            unique_scaffolds[scaffold] = point
    state.selected_evidence_count = int(sum(int(point.get("evidence_count") or 0) for point in unique_scaffolds.values()))
    state.selected_funding_total = float(sum(float(point.get("funding_usd") or 0.0) for point in unique_scaffolds.values()))
