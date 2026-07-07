GLOBAL_CSS = """
:root {
    --bg-dark: #09090b;
    --glass-bg: rgba(255, 255, 255, 0.06);
    --glass-border: rgba(255, 255, 255, 0.10);
    --accent-cyan: #22d3ee;
    --accent-purple: #a855f7;
    --text-soft: #94a3b8;
}

html, body {
    background: var(--bg-dark);
}

.bento-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 8px;
    padding: 1.5rem;
    transition: all 0.2s ease-in-out;
}

.kpi-card {
    overflow-wrap: anywhere;
}

.kpi-card h1 {
    font-size: clamp(1.65rem, 3.2vw, 2.7rem);
    line-height: 1.08;
}

.kpi-card p {
    letter-spacing: 0;
    overflow-wrap: anywhere;
}

.bento-card:hover {
    border-color: rgba(34, 211, 238, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
}

.glass-panel {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 20px;
}

.neon-cyan {
    box-shadow: 0 0 24px rgba(34, 211, 238, 0.15);
}

.neon-purple {
    box-shadow: 0 0 24px rgba(168, 85, 247, 0.15);
}

@media (max-width: 900px) {
    .dashboard-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    }

    .dashboard-grid > .bento-card {
        grid-column: span 2 !important;
    }

    .dashboard-grid > .kpi-card {
        grid-column: span 1 !important;
        min-height: 112px !important;
        padding: 1rem;
    }

    .manuscript-review-buckets {
        grid-template-columns: minmax(0, 1fr) !important;
    }
}

@media (max-width: 520px) {
    .dashboard-grid {
        grid-template-columns: minmax(0, 1fr) !important;
    }

    .dashboard-grid > .bento-card,
    .dashboard-grid > .kpi-card {
        grid-column: span 1 !important;
    }

    .bento-card {
        padding: 1rem;
    }
}
""".strip()
