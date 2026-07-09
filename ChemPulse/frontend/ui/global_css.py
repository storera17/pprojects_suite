from __future__ import annotations

from backend.core.palette_catalog import DEFAULT_PALETTE_KEY, PALETTE_CATALOG, palette_vars


def _css_vars(var_map: dict[str, str]) -> str:
    return "\n".join(f"    {name}: {value};" for name, value in var_map.items())


_DEFAULT_VAR_BLOCK = _css_vars(palette_vars(DEFAULT_PALETTE_KEY))
_PALETTE_BLOCKS = "\n\n".join(
    f".cp-theme-{key} {{\n{_css_vars(palette['vars'])}\n}}"
    for key, palette in PALETTE_CATALOG.items()
)


GLOBAL_CSS = f"""
:root {{
{_DEFAULT_VAR_BLOCK}
    --cp-radius-lg: 22px;
    --cp-radius-md: 16px;
    --cp-radius-sm: 12px;
}}

{_PALETTE_BLOCKS}

html, body {{
    background:
        radial-gradient(circle at top left, var(--cp-page-glow-a), transparent 28%),
        radial-gradient(circle at bottom right, var(--cp-page-glow-b), transparent 24%),
        linear-gradient(180deg, var(--cp-bg-shell) 0%, var(--cp-bg-app) 52%, var(--cp-bg-app-deep) 100%);
    color: var(--cp-text);
    font-family: "Segoe UI", "Inter", sans-serif;
}}

body {{
    margin: 0;
}}

a {{
    color: inherit;
}}

code, pre {{
    font-family: "IBM Plex Mono", "Consolas", monospace;
}}

.cp-app-root {{
    min-height: 100vh;
    padding: 18px;
}}

.cp-shell {{
    min-height: calc(100vh - 36px);
    border-radius: 28px;
    border: 1px solid var(--cp-shell-border);
    background: linear-gradient(180deg, var(--cp-shell-top), var(--cp-shell-bottom));
    box-shadow: 0 28px 80px rgba(0, 0, 0, 0.24);
    overflow: hidden;
}}

.cp-sidebar {{
    width: 120px;
    min-width: 120px;
    height: 100%;
    padding: 20px 14px;
    background: linear-gradient(180deg, var(--cp-sidebar-top), var(--cp-sidebar-bottom));
    border-right: 1px solid var(--cp-border);
}}

.cp-sidebar-brand {{
    color: var(--cp-text);
    font-size: 0.95rem;
    font-weight: 600;
}}

.cp-brand-mark {{
    width: 1.1rem;
    height: 1.1rem;
    border-radius: 0.38rem;
    border: 1px solid var(--cp-border-strong);
    background:
        radial-gradient(circle at 30% 30%, color-mix(in srgb, var(--cp-accent-2) 34%, transparent), transparent 55%),
        color-mix(in srgb, var(--cp-accent) 12%, var(--cp-bg-elevated));
    box-shadow: 0 0 0 1px rgba(255,255,255,0.02), 0 0 16px color-mix(in srgb, var(--cp-accent-2) 18%, transparent);
}}

.cp-sidebar-nav {{
    margin-top: 10px;
}}

.cp-nav-link, .cp-nav-link-active {{
    text-decoration: none;
    display: block;
    width: 100%;
    border-radius: var(--cp-radius-sm);
    transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}}

.cp-nav-link {{
    border: 1px solid transparent;
}}

.cp-nav-link:hover {{
    background: color-mix(in srgb, var(--cp-accent-2) 6%, transparent);
    border-color: color-mix(in srgb, var(--cp-accent-2) 18%, transparent);
}}

.cp-nav-link-active {{
    background: linear-gradient(180deg, color-mix(in srgb, var(--cp-accent) 18%, var(--cp-bg-elevated)), color-mix(in srgb, var(--cp-accent) 12%, var(--cp-bg-panel)));
    border: 1px solid var(--cp-border-strong);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 12px 20px rgba(0,0,0,0.14);
}}

.cp-nav-link-inner {{
    padding: 12px 10px;
}}

.cp-nav-glyph {{
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 0.28rem;
    border: 1px solid color-mix(in srgb, var(--cp-accent) 34%, transparent);
    background: color-mix(in srgb, var(--cp-accent) 12%, transparent);
}}

.cp-nav-label {{
    color: var(--cp-text-muted);
    font-size: 0.78rem;
    font-weight: 600;
}}

.cp-nav-link-active .cp-nav-label {{
    color: var(--cp-text);
}}

.cp-sidebar-section-title {{
    color: var(--cp-text-soft);
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}

.cp-main {{
    flex: 1;
    min-width: 0;
}}

.cp-topbar {{
    padding: 18px 24px 16px;
    border-bottom: 1px solid var(--cp-border);
    background: var(--cp-topbar-bg);
    backdrop-filter: blur(22px);
    -webkit-backdrop-filter: blur(22px);
}}

.cp-topbar-brand {{
    min-width: 0;
}}

.cp-topbar-title {{
    color: var(--cp-text);
    font-size: 1rem;
    font-weight: 600;
}}

.cp-topbar-search {{
    width: min(420px, 100%);
}}

.cp-topbar-actions {{
    flex-wrap: wrap;
}}

.cp-main-scroll {{
    padding: 24px;
}}

.cp-page-content {{
    width: 100%;
}}

.cp-eyebrow {{
    color: var(--cp-text-soft);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}}

.cp-page-title {{
    color: var(--cp-text);
    letter-spacing: -0.03em;
}}

.cp-page-subtitle {{
    color: var(--cp-text-muted);
    max-width: 760px;
    line-height: 1.6;
}}

.cp-panel {{
    background: linear-gradient(180deg, var(--cp-panel-top), var(--cp-panel-bottom));
    border: 1px solid var(--cp-border);
    border-radius: var(--cp-radius-lg);
    box-shadow: var(--cp-shadow);
}}

.cp-panel-stack {{
    min-height: 100%;
}}

.cp-panel-title {{
    color: var(--cp-text);
}}

.cp-panel-footer {{
    padding-top: 0.8rem;
    border-top: 1px solid var(--cp-border);
    color: var(--cp-text-soft);
    font-size: 0.78rem;
}}

.cp-status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    border-radius: 999px;
    padding: 0.22rem 0.65rem;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}}

.cp-status-pill-live {{
    background: var(--cp-live-bg);
    color: var(--cp-live-text);
    border: 1px solid var(--cp-live-border);
}}

.cp-status-pill-building {{
    background: var(--cp-building-bg);
    color: var(--cp-building-text);
    border: 1px solid var(--cp-building-border);
}}

.cp-status-pill-planned {{
    background: var(--cp-planned-bg);
    color: var(--cp-planned-text);
    border: 1px solid var(--cp-planned-border);
}}

.cp-status-pill-neutral {{
    background: var(--cp-neutral-bg);
    color: var(--cp-neutral-text);
    border: 1px solid var(--cp-neutral-border);
}}

.cp-status-pill-danger {{
    background: var(--cp-danger-bg);
    color: var(--cp-danger-text);
    border: 1px solid var(--cp-danger-border);
}}

.cp-metric-panel {{
    min-height: 138px;
    border-radius: var(--cp-radius-md);
}}

.cp-accent-cyan {{
    box-shadow: 0 0 0 1px rgba(255,255,255,0.02), 0 16px 36px rgba(0,0,0,0.20), inset 2px 0 0 var(--cp-accent-2);
}}

.cp-accent-green {{
    box-shadow: 0 0 0 1px rgba(255,255,255,0.02), 0 16px 36px rgba(0,0,0,0.20), inset 2px 0 0 var(--cp-accent);
}}

.cp-accent-amber {{
    box-shadow: 0 0 0 1px rgba(255,255,255,0.02), 0 16px 36px rgba(0,0,0,0.20), inset 2px 0 0 var(--cp-accent-warm);
}}

.cp-card-label {{
    color: var(--cp-text-soft);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}

.cp-card-value {{
    color: var(--cp-text);
}}

.cp-card-detail {{
    color: var(--cp-text-muted);
    font-size: 0.82rem;
}}

.cp-search-shell input,
.cp-topbar-search input,
.cp-utility-search input {{
    background: var(--cp-bg-input) !important;
    border: 1px solid var(--cp-border) !important;
    border-radius: 999px !important;
    color: var(--cp-text) !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}}

.rt-TextFieldRoot,
.rt-SelectTrigger {{
    background: var(--cp-bg-input) !important;
    border-color: var(--cp-border) !important;
    color: var(--cp-text) !important;
}}

.rt-TextFieldInput,
.rt-SelectTriggerInner,
.rt-SelectValue,
.rt-SelectItem {{
    color: var(--cp-text) !important;
}}

.rt-SelectContent {{
    background: var(--cp-bg-panel) !important;
    border: 1px solid var(--cp-border) !important;
    color: var(--cp-text) !important;
}}

.cp-dashboard-grid {{
    display: grid;
    grid-template-columns: minmax(0, 1.5fr) minmax(320px, 0.85fr);
    gap: 16px;
}}

.cp-dashboard-main {{
    display: grid;
    grid-template-columns: repeat(12, minmax(0, 1fr));
    gap: 16px;
}}

.cp-dashboard-sidebar {{
    display: grid;
    gap: 16px;
}}

.cp-grid-span-12 {{ grid-column: span 12; }}
.cp-grid-span-8 {{ grid-column: span 8; }}
.cp-grid-span-7 {{ grid-column: span 7; }}
.cp-grid-span-6 {{ grid-column: span 6; }}
.cp-grid-span-5 {{ grid-column: span 5; }}
.cp-grid-span-4 {{ grid-column: span 4; }}
.cp-grid-span-3 {{ grid-column: span 3; }}

.bento-card {{
    background: var(--cp-bg-panel);
    border: 1px solid var(--cp-border);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: var(--cp-radius-md);
    padding: 1.1rem;
    transition: all 0.2s ease-in-out;
    box-shadow: var(--cp-shadow);
}}

.kpi-card {{
    overflow-wrap: anywhere;
}}

.kpi-card h1 {{
    font-size: clamp(1.65rem, 3.2vw, 2.7rem);
    line-height: 1.08;
}}

.kpi-card p {{
    letter-spacing: 0;
    overflow-wrap: anywhere;
}}

.bento-card:hover {{
    border-color: color-mix(in srgb, var(--cp-accent) 28%, transparent);
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.20);
}}

.glass-panel {{
    background: var(--cp-bg-panel-soft);
    border: 1px solid var(--cp-border);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 20px;
}}

.neon-cyan {{
    box-shadow: 0 0 24px color-mix(in srgb, var(--cp-accent-2) 22%, transparent);
}}

.neon-purple {{
    box-shadow: 0 0 24px color-mix(in srgb, var(--cp-accent-warm) 20%, transparent);
}}

.cp-inline-muted {{
    color: var(--cp-text-soft);
    font-size: 0.78rem;
}}

.cp-warning-banner {{
    padding: 0.8rem 1rem;
    border-radius: var(--cp-radius-sm);
    border: 1px solid var(--cp-building-border);
    background: var(--cp-building-bg);
    color: var(--cp-building-text);
}}

.cp-live-banner {{
    padding: 0.9rem 1rem;
    border-radius: var(--cp-radius-sm);
    border: 1px solid var(--cp-live-border);
    background: color-mix(in srgb, var(--cp-live-bg) 52%, var(--cp-bg-panel));
}}

.cp-link {{
    color: var(--cp-link);
    text-decoration: none;
    font-weight: 600;
}}

.cp-link:hover {{
    text-decoration: underline;
}}

.cp-surface-soft {{
    background: var(--cp-bg-panel-soft);
    border: 1px solid var(--cp-border);
}}

.cp-surface-elevated {{
    background: var(--cp-bg-elevated);
    border: 1px solid var(--cp-border);
}}

.cp-theme-option-button {{
    border: 0;
    background: transparent;
}}

.cp-theme-option-button:hover {{
    transform: translateY(-1px);
}}

.cp-theme-option-button .rt-ButtonInner,
.cp-theme-option-button .rt-reset {{
    width: 100%;
}}

.cp-theme-option-button-selected .bento-card,
.cp-theme-option-button-selected > div {{
    border-color: var(--cp-border-strong);
}}

.cp-theme-option-title {{
    color: var(--cp-text);
    font-weight: 700;
    font-size: 0.95rem;
}}

.cp-theme-swatch-row {{
    margin-top: 0.15rem;
}}

.cp-theme-swatch {{
    width: 1rem;
    height: 1rem;
    border-radius: 999px;
    border: 1px solid rgba(0, 0, 0, 0.08);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.18);
}}

.cp-os-card {{
    min-height: 100%;
}}

@media (max-width: 900px) {{
    .cp-app-root {{
        padding: 10px;
    }}

    .cp-shell {{
        min-height: calc(100vh - 20px);
    }}

    .cp-sidebar {{
        width: 92px;
        min-width: 92px;
        padding: 14px 10px;
    }}

    .cp-sidebar-brand {{
        font-size: 0.82rem;
    }}

    .cp-main-scroll,
    .cp-topbar {{
        padding-left: 16px;
        padding-right: 16px;
    }}

    .cp-dashboard-grid {{
        grid-template-columns: 1fr;
    }}

    .dashboard-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    }}

    .dashboard-grid > .bento-card {{
        grid-column: span 2 !important;
    }}

    .dashboard-grid > .kpi-card {{
        grid-column: span 1 !important;
        min-height: 112px !important;
        padding: 1rem;
    }}

    .manuscript-review-buckets {{
        grid-template-columns: minmax(0, 1fr) !important;
    }}

    .cp-grid-span-12,
    .cp-grid-span-8,
    .cp-grid-span-7,
    .cp-grid-span-6,
    .cp-grid-span-5,
    .cp-grid-span-4,
    .cp-grid-span-3 {{
        grid-column: span 12;
    }}
}}

@media (max-width: 520px) {{
    .cp-shell {{
        display: block;
    }}

    .cp-sidebar {{
        width: auto;
        min-width: 0;
        border-right: 0;
        border-bottom: 1px solid var(--cp-border);
    }}

    .cp-sidebar-nav {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
    }}

    .cp-topbar {{
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: stretch;
    }}

    .cp-topbar-search {{
        width: 100%;
    }}

    .dashboard-grid {{
        grid-template-columns: minmax(0, 1fr) !important;
    }}

    .dashboard-grid > .bento-card,
    .dashboard-grid > .kpi-card {{
        grid-column: span 1 !important;
    }}

    .bento-card {{
        padding: 1rem;
    }}
}}
""".strip()
