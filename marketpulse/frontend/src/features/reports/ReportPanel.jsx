import { EmptyState } from "../../components/common/EmptyState.jsx";

export function ReportPanel({ ticker, report, onGenerate }) {
  const sections = String(report || "").split(/\n\n+/).filter(Boolean);

  return (
    <section className="panel wide" id="report">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Executive package</p>
          <h2>{ticker} Daily Report</h2>
        </div>
        <button onClick={onGenerate}>Generate Report</button>
      </div>

      {!report ? (
        <EmptyState title="Report not generated yet">
          Generate a local report from the SQLite dashboard snapshot.
        </EmptyState>
      ) : (
        <div className="report-sections">
          {sections.map((section, index) => (
            <article className="report-section" key={index}>
              <pre>{section}</pre>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
