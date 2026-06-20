import { Badge } from "../../components/common/Badge.jsx";
import { EmptyState } from "../../components/common/EmptyState.jsx";
import { ensureArray } from "../../utils/arrays.js";

function NewsCard({ item }) {
  return (
    <article className="news-card">
      <div className="news-meta">
        <span>{item.provider}</span>
        <Badge value={item.market_relevance || "unscored"} />
      </div>
      <h3>{item.title || "Untitled item"}</h3>
      <p>{item.summary || "No summary stored for this item."}</p>
      <footer>
        <span>{item.event_date || "No date"}</span>
        {item.url ? (
          <a href={item.url} target="_blank" rel="noreferrer">
            Open source
          </a>
        ) : null}
      </footer>
    </article>
  );
}

export function NewsPanel({ ticker, items }) {
  const newsItems = ensureArray(items).slice(0, 12);

  return (
    <section className="panel wide">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Relevance-filtered news</p>
          <h2>{ticker} News and Search Items</h2>
        </div>
        <span>{newsItems.length} shown</span>
      </div>

      {newsItems.length ? (
        <div className="news-grid">
          {newsItems.map((item, index) => (
            <NewsCard item={item} key={item.id || index} />
          ))}
        </div>
      ) : (
        <EmptyState title="No news rows stored" />
      )}
    </section>
  );
}
