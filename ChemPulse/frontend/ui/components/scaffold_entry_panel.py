from __future__ import annotations

import reflex as rx


def scaffold_entry_panel(
    name,
    category,
    family,
    smiles,
    status,
    on_name_change,
    on_category_change,
    on_family_change,
    on_smiles_change,
    on_add,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("Add Scaffold", size="5", color="white"),
            rx.input(
                placeholder="Name, e.g. Custom oxazole",
                value=name,
                on_change=on_name_change,
                width="100%",
                bg="rgba(255,255,255,0.06)",
                border="1px solid rgba(255,255,255,0.10)",
            ),
            rx.input(
                placeholder="Category, e.g. Amino acid",
                value=category,
                on_change=on_category_change,
                width="100%",
                bg="rgba(255,255,255,0.06)",
                border="1px solid rgba(255,255,255,0.10)",
            ),
            rx.input(
                placeholder="Family, e.g. Proteinogenic amino acids",
                value=family,
                on_change=on_family_change,
                width="100%",
                bg="rgba(255,255,255,0.06)",
                border="1px solid rgba(255,255,255,0.10)",
            ),
            rx.input(
                placeholder="SMILES",
                value=smiles,
                on_change=on_smiles_change,
                width="100%",
                bg="rgba(255,255,255,0.06)",
                border="1px solid rgba(255,255,255,0.10)",
            ),
            rx.button("Validate and add", on_click=on_add, variant="soft", color_scheme="green", width="100%"),
            rx.cond(status != "", rx.text(status, color="#CBD5E1", size="2")),
            align="stretch",
            spacing="3",
        ),
        class_name="bento-card",
        grid_column="span 4",
        min_height="360px",
    )


