from __future__ import annotations

import reflex as rx


# The curiosity loop — the engine every app feeds.
CURIOSITY_LOOP = [
    "Wonder",
    "Question",
    "Mystery",
    "Exploration",
    "Understanding",
    "Creation",
]


# Status vocabulary for the OS.
#   live     -> a working surface you can use right now
#   building -> a real scaffold page; the module is coming online
#   planned  -> on the horizon, described but not yet scaffolded
STATUS_META = {
    "live": ("Live", "#86efac", "#052e16"),
    "building": ("Building", "#fcd34d", "#3b2f0b"),
    "planned": ("Planned", "#93c5fd", "#0b2540"),
}


# Every level of the vision, in curiosity-loop order, as an app tile.
MODULES: list[dict] = [
    {
        "slug": "discoveryos",
        "name": "DiscoveryOS",
        "level": "Learning Layer",
        "tagline": "Where learning actually happens.",
        "purpose": (
            "Learn, explore, simulate, investigate, apply, create, reflect — "
            "the active loop that separates this from being told facts."
        ),
        "accent": "#a855f7",
        "status": "building",
        "route": "/os/discoveryos",
        "components": [
            "Learn",
            "Explore",
            "Simulate",
            "Investigate",
            "Apply",
            "Create",
            "Reflect",
        ],
    },
    {
        "slug": "researchos",
        "name": "ResearchOS",
        "level": "Professional Layer",
        "tagline": "Contribute knowledge, not just consume it.",
        "purpose": (
            "Literature analysis, structure and reaction search, mechanism "
            "explanation and reports — already live as Chemical Intelligence "
            "over your local evidence.",
        ),
        "accent": "#38bdf8",
        "status": "live",
        "route": "/chemical-intelligence",
        "components": [
            "Literature Analysis",
            "Structure & Reaction Search",
            "Mechanism Explanation",
            "Hypothesis Generation",
            "Research Planning",
            "Publication Support",
        ],
    },
    {
        "slug": "chempulse",
        "name": "ChemPulse",
        "level": "ChemicalOS — First Domain",
        "tagline": "Scientific discovery platform for chemistry.",
        "purpose": (
            "The first domain made real: scaffolds, chemical space, "
            "publication radar, predictive lab and a DuckDB analytics core — "
            "the working proof of the whole stack."
        ),
        "accent": "#22d3ee",
        "status": "live",
        "route": "/chempulse",
        "components": [
            "Scaffolds & Chemical Space",
            "Publication Radar",
            "Predictive Lab",
            "Funding & Journal Intelligence",
            "RDKit Chemistry Engine",
        ],
    },
    {
        "slug": "journal-sentiment",
        "name": "Journal Sentiment",
        "level": "ChemicalOS — Signal",
        "tagline": "Read the mood of the literature.",
        "purpose": (
            "A live ChemPulse surface that tracks sentiment and momentum across "
            "journal and publication sources."
        ),
        "accent": "#2dd4bf",
        "status": "live",
        "route": "/journal-sentiment",
        "components": [
            "Source Sentiment",
            "Publication Momentum",
            "Journal Activity",
        ],
    },
    {
        "slug": "simulationos",
        "name": "SimulationOS",
        "level": "Visualization Layer",
        "tagline": "Make invisible things visible.",
        "purpose": (
            "Mechanism animations, reaction and molecular-dynamics simulation, "
            "pathway and quantum visualization, interactive labs. Mechanism "
            "explanation already runs inside ChemPulse."
        ),
        "accent": "#818cf8",
        "status": "building",
        "route": "/os/simulationos",
        "components": [
            "Mechanism Animations",
            "Reaction Simulations",
            "Molecular Dynamics",
            "Pathway Visualizations",
            "Quantum Visualizations",
            "Interactive Labs",
        ],
    },
    {
        "slug": "biomedicalos",
        "name": "BioMedicalOS",
        "level": "Long-Term Layer",
        "tagline": "Connect chemistry to biology and medicine.",
        "purpose": (
            "Drug mechanisms, disease pathways, biological systems, "
            "pharmacology and medical education — the long-term bridge out of "
            "pure chemistry."
        ),
        "accent": "#f87171",
        "status": "planned",
        "route": "/os/biomedicalos",
        "components": [
            "Drug Mechanisms",
            "Disease Pathways",
            "Biological Systems",
            "Pharmacology",
            "Physiology",
            "Medical Education",
        ],
    },
    {
        "slug": "platformos",
        "name": "PlatformOS",
        "level": "Infrastructure",
        "tagline": "The substrate everything runs on.",
        "purpose": (
            "Accounts, projects, the AI layer, knowledge graph, vector search, "
            "databases, APIs, collaboration and deployment. The DuckDB core and "
            "API routes are already live underneath ChemPulse."
        ),
        "accent": "#64748b",
        "status": "building",
        "route": "/os/platformos",
        "components": [
            "Accounts & Projects",
            "AI Layer",
            "Knowledge Graph",
            "Vector Search",
            "Databases & APIs",
            "Collaboration",
            "Deployment",
        ],
    },
]


# Modules that need a generic scaffold page: those under /os/ that aren't yet
# backed by a live surface of their own.
SCAFFOLD_MODULES: list[dict] = [
    m for m in MODULES if m["route"].startswith("/os/") and m["status"] != "live"
]


def _status_badge(status: str) -> rx.Component:
    label, fg, bg = STATUS_META.get(status, STATUS_META["planned"])
    return rx.box(
        label,
        color=fg,
        background=bg,
        font_size="0.7rem",
        font_weight="800",
        letter_spacing="0.06em",
        text_transform="uppercase",
        padding="0.15rem 0.55rem",
        border_radius="999px",
        border=f"1px solid {fg}55",
    )


def _loop_band() -> rx.Component:
    pills: list[rx.Component] = []
    for index, stage in enumerate(CURIOSITY_LOOP):
        pills.append(
            rx.box(
                stage,
                color="#E2E8F0",
                font_weight="700",
                font_size="0.85rem",
                padding="0.4rem 0.9rem",
                border_radius="999px",
                background="rgba(148,163,184,0.12)",
                border="1px solid rgba(148,163,184,0.22)",
            )
        )
        if index < len(CURIOSITY_LOOP) - 1:
            pills.append(rx.text("→", color="#64748B", font_weight="800"))
    return rx.flex(
        *pills,
        wrap="wrap",
        align="center",
        gap="0.5rem",
        margin_bottom="1.6rem",
    )


def _app_tile(module: dict) -> rx.Component:
    return rx.link(
        rx.box(
            rx.hstack(
                rx.text(
                    module["level"],
                    color="#94A3B8",
                    font_size="0.72rem",
                    font_weight="700",
                    letter_spacing="0.08em",
                    text_transform="uppercase",
                ),
                rx.spacer(),
                _status_badge(module["status"]),
                width="100%",
                align="center",
            ),
            rx.heading(
                module["name"],
                size="6",
                color="white",
                margin_top="0.5rem",
            ),
            rx.text(
                module["tagline"],
                color=module["accent"],
                font_weight="700",
                font_size="0.95rem",
                margin_top="0.1rem",
            ),
            rx.text(
                module["purpose"],
                color="#CBD5E1",
                font_size="0.88rem",
                line_height="1.5",
                margin_top="0.55rem",
            ),
            class_name="bento-card",
            padding="1.1rem 1.2rem",
            height="100%",
            border_top=f"2px solid {module['accent']}",
            box_shadow=f"0 12px 40px rgba(0,0,0,0.28), 0 0 22px {module['accent']}22",
            transition="transform 0.12s ease, box-shadow 0.12s ease",
            _hover={
                "transform": "translateY(-3px)",
                "box_shadow": f"0 18px 52px rgba(0,0,0,0.36), 0 0 30px {module['accent']}44",
            },
        ),
        href=module["route"],
        is_external=False,
        text_decoration="none",
        width="100%",
        height="100%",
    )


def launcher_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                "Chemical Intelligence Platform",
                color="#94A3B8",
                font_size="0.85rem",
                font_weight="700",
                letter_spacing="0.18em",
                text_transform="uppercase",
            ),
            rx.heading("ChemPulse OS", size="9", color="white"),
            rx.text(
                "Help people become more capable, curious, creative and "
                "knowledgeable through discovery. Open an app to begin — "
                "chemistry is live today, the rest is coming online.",
                color="#CBD5E1",
                font_size="1rem",
                max_width="760px",
                line_height="1.6",
                margin_top="0.3rem",
            ),
            align="start",
            spacing="1",
            margin_bottom="1.4rem",
        ),
        _loop_band(),
        rx.grid(
            *[_app_tile(module) for module in MODULES],
            columns=rx.breakpoints(initial="1", sm="2", lg="3"),
            spacing="4",
            width="100%",
        ),
        rx.text(
            "Every app feeds the same loop: Wonder → Question → Mystery → "
            "Exploration → Understanding → Creation.",
            color="#64748B",
            font_size="0.82rem",
            margin_top="1.6rem",
        ),
        padding="2.2rem",
        max_width="1280px",
        margin="0 auto",
    )


def _module_layout(module: dict) -> rx.Component:
    label, fg, bg = STATUS_META.get(module["status"], STATUS_META["planned"])
    return rx.box(
        rx.hstack(
            rx.link("← ChemPulse OS", href="/", color="#67E8F9", font_weight="700"),
            rx.spacer(),
            rx.link("ChemPulse", href="/chempulse", color="#67E8F9"),
            rx.link("Chemical Intelligence", href="/chemical-intelligence", color="#67E8F9"),
            width="100%",
            align="center",
            margin_bottom="1.6rem",
        ),
        rx.text(
            module["level"],
            color="#94A3B8",
            font_size="0.8rem",
            font_weight="700",
            letter_spacing="0.12em",
            text_transform="uppercase",
        ),
        rx.hstack(
            rx.heading(module["name"], size="9", color="white"),
            _status_badge(module["status"]),
            align="center",
            spacing="3",
            margin_top="0.2rem",
        ),
        rx.text(
            module["tagline"],
            color=module["accent"],
            font_size="1.15rem",
            font_weight="700",
            margin_top="0.4rem",
        ),
        rx.text(
            module["purpose"],
            color="#CBD5E1",
            font_size="1rem",
            max_width="760px",
            line_height="1.6",
            margin_top="0.7rem",
        ),
        rx.heading(
            "What this app will do",
            size="5",
            color="white",
            margin_top="1.8rem",
            margin_bottom="0.8rem",
        ),
        rx.grid(
            *[
                rx.box(
                    rx.text(component, color="#E2E8F0", font_weight="600"),
                    class_name="bento-card",
                    padding="0.9rem 1rem",
                    border_left=f"2px solid {module['accent']}",
                )
                for component in module["components"]
            ],
            columns=rx.breakpoints(initial="1", sm="2", lg="3"),
            spacing="3",
            width="100%",
        ),
        rx.box(
            rx.text(
                f"{module['name']} is {label.lower()}. It plugs into the same "
                "curiosity loop and shares ChemPulse's local data, AI and "
                "platform core — so it grows out of what already works rather "
                "than starting from zero.",
                color="#94A3B8",
                font_size="0.9rem",
                line_height="1.6",
            ),
            background=bg,
            border=f"1px solid {fg}44",
            border_radius="10px",
            padding="1rem 1.2rem",
            margin_top="1.8rem",
            max_width="820px",
        ),
        padding="2.2rem",
        max_width="1100px",
        margin="0 auto",
    )


def make_module_page(module: dict):
    """Build a scaffold page bound to a single module."""

    def module_page() -> rx.Component:
        return _module_layout(module)

    return module_page