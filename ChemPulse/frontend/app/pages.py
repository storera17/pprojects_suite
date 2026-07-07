from __future__ import annotations

import reflex as rx

from frontend.state.app_state import AppState
from frontend.state.journal_sentiment_state import JournalSentimentState
from frontend.ui.pages.chemical_intelligence import chemical_intelligence_page
from frontend.ui.pages.dashboard import dashboard_page
from frontend.ui.pages.journal_sentiment import journal_sentiment_page
from frontend.ui.pages.launcher import SCAFFOLD_MODULES, launcher_page, make_module_page


def register_pages(app: rx.App) -> None:
    app.add_page(
        launcher_page,
        route="/",
        title="ChemPulse OS",
    )

    app.add_page(
        dashboard_page,
        route="/chempulse",
        title="ChemPulse",
        on_load=AppState.initialize,
    )

    for module in SCAFFOLD_MODULES:
        app.add_page(
            make_module_page(module),
            route=module["route"],
            title=f"ChemPulse OS · {module['name']}",
        )

    app.add_page(
        journal_sentiment_page,
        route="/journal-sentiment",
        title="ChemPulse Journal Sentiment",
        on_load=JournalSentimentState.initialize,
    )

    app.add_page(
        chemical_intelligence_page,
        route="/chemical-intelligence",
        title="ChemPulse Chemical Intelligence",
    )
