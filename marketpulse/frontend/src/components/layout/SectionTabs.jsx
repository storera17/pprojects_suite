import { SECTION_TABS } from "../../constants/tabs.js";

export function SectionTabs({ active, onSelect }) {
  return (
    <nav className="section-tabs" aria-label="Ticker page sections">
      {SECTION_TABS.map(([value, label]) => (
        <button
          key={value}
          className={active === value ? "section-tab active" : "section-tab"}
          onClick={() => onSelect(value)}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}
