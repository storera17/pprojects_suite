from __future__ import annotations

from frontend.ui.pages.chemical_intelligence import chemical_intelligence_page
from frontend.ui.pages.dashboard import dashboard_page
from frontend.ui.pages.launcher import launcher_page


def test_launcher_page_renders_shared_shell() -> None:
    rendered = str(launcher_page().render())

    assert "cp-shell" in rendered
    assert "ChemPulse OS" in rendered
    assert "DiscoveryOS" in rendered


def test_dashboard_page_renders_shared_shell() -> None:
    rendered = str(dashboard_page().render())

    assert "cp-shell" in rendered
    assert "Last refreshed:" in rendered
    assert "Search scaffold, journal, DOI, catalyst, transformation..." in rendered


def test_chemical_intelligence_page_renders_pricing_tab() -> None:
    rendered = str(chemical_intelligence_page().render())

    assert "cp-shell" in rendered
    assert "Source Pricing" in rendered
    assert "Search workspace..." in rendered