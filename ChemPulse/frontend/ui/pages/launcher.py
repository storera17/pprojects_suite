from __future__ import annotations

import reflex as rx

from frontend.state.theme_state import ThemeState
from frontend.ui.components.settings_panel import theme_settings_panel
from frontend.ui.shell import metric_panel, shell_link, shell_panel, status_pill, workspace_shell


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
    "live": ("Live", "#86efac", "#052e16", "live"),
    "building": ("Building", "#fcd34d", "#3b2f0b", "building"),
    "planned": ("Planned", "#93c5fd", "#0b2540", "planned"),
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
        "stats": ("Services", "12", "Agents", "24", "Pipelines", "7"),
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
        "stats": ("Projects", "18", "Libraries", "6", "Members", "32"),
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
        "stats": ("Documents", "2.4M", "Journals", "8,732", "Scaffolds", "1.6M"),
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
        "stats": ("Monitored", "1,245", "Analyzed", "70K", "Models", "3"),
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
        "stats": ("Jobs", "412", "Queues", "5", "GPUs", "16"),
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
        "stats": ("Datasets", "0", "Pipelines", "0", "Models", "0"),
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
        "stats": ("Services", "28", "Integrations", "14", "Uptime", "99.97%"),
    },
]


# Modules that need a generic scaffold page: those under /os/ that aren't yet
# backed by a live surface of their own.
SCAFFOLD_MODULES: list[dict] = [
    m for m in MODULES if m["route"].startswith("/os/") and m["status"] != "live"
]


def _status_badge(status: str) -> rx.Component:
    label, _fg, _bg, tone = STATUS_META.get(status, STATUS_META["planned"])
    return status_pill(label, tone=tone)


def _loop_band() -> rx.Component:
    pills: list[rx.Component] = []
    for index, stage in enumerate(CURIOSITY_LOOP):
        pills.append(
            rx.box(
                stage,
                color="var(--cp-text)",
                font_weight="700",
                font_size="0.85rem",
                padding="0.4rem 0.9rem",
                border_radius="999px",
                background="var(--cp-bg-panel-soft)",
                border="1px solid var(--cp-border)",
            )
        )
        if index < len(CURIOSITY_LOOP) - 1:
            pills.append(rx.text("→", color="var(--cp-text-soft)", font_weight="800"))
    return rx.flex(
        *pills,
        wrap="wrap",
        align="center",
        gap="0.5rem",
        margin_bottom="1.6rem",
    )


def _app_tile(module: dict) -> rx.Component:
    stat_label_a, stat_value_a, stat_label_b, stat_value_b, stat_label_c, stat_value_c = module["stats"]
    return rx.link(
        shell_panel(
            module["name"],
            rx.vstack(
                rx.text(
                    module["tagline"],
                    color=module["accent"],
                    font_weight="700",
                    font_size="0.95rem",
                    margin_top="0.1rem",
                ),
                rx.text(
                    module["purpose"],
                    color="var(--cp-text-muted)",
                    font_size="0.88rem",
                    line_height="1.5",
                    margin_top="0.25rem",
                ),
                rx.grid(
                    _module_stat(stat_label_a, stat_value_a),
                    _module_stat(stat_label_b, stat_value_b),
                    _module_stat(stat_label_c, stat_value_c),
                    columns="repeat(3, minmax(0, 1fr))",
                    gap="0.55rem",
                    width="100%",
                ),
                align="stretch",
                spacing="3",
            ),
            eyebrow=module["level"],
            badges=[_status_badge(module["status"])],
            class_name="cp-os-card",
        ),
        href=module["route"],
        is_external=False,
        text_decoration="none",
        width="100%",
        height="100%",
    )


def _module_stat(label: str, value: str) -> rx.Component:
    return rx.box(
        rx.text(label, color="var(--cp-text-soft)", font_size="0.7rem", text_transform="uppercase", letter_spacing="0.05em"),
        rx.text(value, color="var(--cp-text)", font_weight="700", font_size="0.9rem"),
        padding="0.55rem 0.6rem",
        border_radius="12px",
        background="var(--cp-bg-panel-soft)",
        border="1px solid var(--cp-border)",
    )


def launcher_page() -> rx.Component:
    summary_panels = rx.grid(
        metric_panel("ChemPulse", "Live", detail="Local chemical intelligence workspace", accent_class="cp-accent-green"),
        metric_panel("Routes", "3", detail="Launcher, dashboard, workspace", accent_class="cp-accent-cyan"),
        metric_panel("Collection", "Hybrid", detail="Live evidence with queued extensions", accent_class="cp-accent-amber"),
        columns=rx.breakpoints(initial="1", md="3"),
        gap="1rem",
        width="100%",
    )
    module_grid = rx.grid(
        *[_app_tile(module) for module in MODULES],
        columns=rx.breakpoints(initial="1", md="2"),
        spacing="4",
        width="100%",
    )
    hero = rx.vstack(
        rx.hstack(
            rx.box(class_name="cp-brand-mark"),
            rx.heading("ChemPulse OS", size="9", color="var(--cp-text)"),
            rx.spacer(),
            status_pill("v1.3.0", tone="neutral"),
            align="center",
            width="100%",
        ),
        rx.text(
            "The operating system for chemical discovery. Unify literature, molecules, reactions, and intelligence while keeping the current repository architecture and live local workflows intact.",
            color="var(--cp-text-muted)",
            font_size="1rem",
            max_width="760px",
            line_height="1.7",
        ),
        _loop_band(),
        align="stretch",
        spacing="4",
        width="100%",
    )
    footer = rx.hstack(
        status_pill("Operational", tone="live"),
        rx.spacer(),
        rx.text("© 2025 ChemPulse Labs", class_name="cp-inline-muted"),
        rx.text("Documentation", class_name="cp-inline-muted"),
        rx.text("Support", class_name="cp-inline-muted"),
        width="100%",
        align="center",
    )
    content = rx.vstack(
        summary_panels,
        shell_panel(
            "ChemPulse OS",
            rx.vstack(hero, module_grid, align="stretch", spacing="4"),
            eyebrow="Operating System",
            footer=footer,
        ),
        theme_settings_panel(),
        align="stretch",
        spacing="4",
    )
    return workspace_shell(
        active_nav="launcher",
        brand="ChemPulse OS",
        title="ChemPulse OS",
        description="A route-backed operating surface for discovery, research, and chemical intelligence workflows.",
        content=content,
        theme_class=ThemeState.palette_class,
        topbar_actions=[
            rx.hstack(
                status_pill("Desktop", tone="neutral"),
                status_pill("Live routes", tone="live"),
                align="center",
                spacing="2",
            ),
        ],
        status_text="Operational",
        status_tone="live",
    )


def _module_layout(module: dict) -> rx.Component:
    label, _fg, _bg, tone = STATUS_META.get(module["status"], STATUS_META["planned"])
    body = rx.vstack(
        rx.hstack(
            rx.heading(module["name"], size="8", color="var(--cp-text)"),
            rx.spacer(),
            status_pill(label, tone=tone),
            width="100%",
            align="center",
        ),
        rx.text(module["tagline"], color=module["accent"], font_size="1.05rem", font_weight="700"),
        rx.text(module["purpose"], color="var(--cp-text-muted)", font_size="0.96rem", line_height="1.7"),
        rx.grid(
            *[
                rx.box(
                    rx.text(component, color="var(--cp-text)", font_weight="600"),
                    padding="0.95rem 1rem",
                    border_radius="12px",
                    background="var(--cp-bg-panel-soft)",
                    border="1px solid var(--cp-border)",
                )
                for component in module["components"]
            ],
            columns=rx.breakpoints(initial="1", md="2", lg="3"),
            spacing="3",
            width="100%",
        ),
        align="stretch",
        spacing="4",
    )
    return workspace_shell(
        active_nav="launcher",
        brand="ChemPulse OS",
        title=module["name"],
        description=f"{module['level']} module detail and route-backed scaffold for {module['name']}.",
        theme_class=ThemeState.palette_class,
        content=shell_panel(
            module["name"],
            body,
            eyebrow=module["level"],
            footer=rx.text(
                f"{module['name']} is {label.lower()}. It shares the same platform core and grows from the current working ChemPulse architecture.",
                class_name="cp-inline-muted",
            ),
        ),
        topbar_actions=[
            shell_link("ChemPulse", "/chempulse"),
            shell_link("Chemical Intelligence", "/chemical-intelligence"),
        ],
        status_text=label,
        status_tone=tone,
    )


def make_module_page(module: dict):
    """Build a scaffold page bound to a single module."""

    def module_page() -> rx.Component:
        return _module_layout(module)

    return module_page