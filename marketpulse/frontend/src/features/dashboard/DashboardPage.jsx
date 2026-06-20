import { useState } from "react";

import { BarChart } from "../../components/common/BarChart.jsx";
import { Badge } from "../../components/common/Badge.jsx";
import { EmptyState } from "../../components/common/EmptyState.jsx";
import { LineChart } from "../../components/common/LineChart.jsx";
import { AppShell } from "../../components/layout/AppShell.jsx";
import { HeroHeader } from "../../components/layout/HeroHeader.jsx";
import { SectionTabs } from "../../components/layout/SectionTabs.jsx";
import { TickerTabs } from "../../components/layout/TickerTabs.jsx";
import { useAgent } from "../../hooks/useAgent.js";
import { useCensusDiscovery } from "../../hooks/useCensusDiscovery.js";
import { useDashboard } from "../../hooks/useDashboard.js";
import { useTickerStorage } from "../../hooks/useTickerStorage.js";
import { ensureArray, ensureObject, firstSeries } from "../../utils/arrays.js";
import { titleCase } from "../../utils/formatters.js";
import { AutoAgentPanel } from "../agent/AutoAgentPanel.jsx";
import { ChatPanel } from "../chat/ChatPanel.jsx";
import { CensusDiscoveryPanel } from "../census/CensusDiscoveryPanel.jsx";
import { DataFreshness } from "./DataFreshness.jsx";
import { NewsPanel } from "./NewsPanel.jsx";
import { OverviewPanel } from "./OverviewPanel.jsx";
import { PricePanel } from "./PricePanel.jsx";
import { ProviderPanel } from "./ProviderPanel.jsx";
import { QualityStrip } from "./QualityStrip.jsx";
import { SentimentPanel } from "./SentimentPanel.jsx";
import { DailyBriefPanel } from "../reports/DailyBriefPanel.jsx";
import { ReportPanel } from "../reports/ReportPanel.jsx";
import { TickerStoragePanel } from "../storage/TickerStoragePanel.jsx";

function latestRowsBySymbol(rows) {
  return Object.values(
    ensureArray(rows).reduce((accumulator, row) => {
      const symbol = row.symbol || row.title || row.provider || "unknown";
      const currentDate = row.event_date || row.created_at || "";
      const previousDate = accumulator[symbol]?.date || "";
      if (!accumulator[symbol] || currentDate >= previousDate) {
        accumulator[symbol] = {
          symbol,
          value: row.value_primary,
          provider: row.provider,
          date: currentDate,
        };
      }
      return accumulator;
    }, {}),
  );
}

function CrossAssetPanel({ dashboard }) {
  const cryptoRows = ensureArray(dashboard.crypto);
  const fxRows = ensureArray(dashboard.fx);
  const cryptoSeries = ensureObject(dashboard.crypto_series);
  const fxSeries = ensureObject(dashboard.fx_series);
  const latestCrypto = latestRowsBySymbol(cryptoRows);
  const latestFx = latestRowsBySymbol(fxRows);

  return (
    <section className="panel wide">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Cross-asset coverage</p>
          <h2>Crypto and FX Overview</h2>
        </div>
        <span className="muted small">
          {cryptoRows.length} crypto rows | {fxRows.length} FX rows
        </span>
      </div>

      <div className="analytics-grid two">
        <div className="chart-card">
          <h3>Latest Crypto Prices</h3>
          <BarChart rows={latestCrypto} valueKey="value" labelKey="symbol" label="latest crypto prices" />
        </div>
        <div className="chart-card">
          <h3>Latest FX Rates</h3>
          <BarChart rows={latestFx} valueKey="value" labelKey="symbol" label="latest fx rates" />
        </div>

        {Object.entries(cryptoSeries)
          .slice(0, 4)
          .map(([symbol, rows]) => (
            <div className="chart-card" key={symbol}>
              <h3>{symbol} History</h3>
              <LineChart rows={rows} valueKey="value" label={`${symbol} crypto history`} />
            </div>
          ))}

        {Object.entries(fxSeries)
          .slice(0, 4)
          .map(([symbol, rows]) => (
            <div className="chart-card" key={symbol}>
              <h3>{symbol} FX History</h3>
              <LineChart rows={rows} valueKey="value" label={`${symbol} FX history`} />
            </div>
          ))}
      </div>
    </section>
  );
}

function TopicSummary({ topics }) {
  const items = ensureArray(topics).slice(0, 10);
  if (!items.length) {
    return <EmptyState title="No topic clusters yet">Refresh news/search providers to create topic clusters.</EmptyState>;
  }
  return (
    <div className="topic-grid">
      {items.map((topic, index) => (
        <article className="topic-pill" key={topic.id || index}>
          <span>{topic.source || "local"}</span>
          <strong>{topic.label || "Untitled cluster"}</strong>
          <small>{ensureArray(topic.keywords).slice(0, 10).join(", ")}</small>
        </article>
      ))}
    </div>
  );
}

function SentimentTimeline({ rows }) {
  const items = ensureArray(rows).slice(-20);
  if (!items.length) {
    return <p className="muted small">No sentiment timeline buckets are available yet.</p>;
  }
  return (
    <div className="sentiment-timeline">
      {items.map((row, index) => (
        <span
          key={`${row.date}-${index}`}
          className={`sentiment-point ${row.label || "neutral"}`}
          title={`${row.date}: ${row.label} (${row.sentiment}) | ${row.count} item(s)`}
        >
          {row.date}
        </span>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const dashboardState = useDashboard();
  const storageState = useTickerStorage(dashboardState.activeTicker);
  const censusState = useCensusDiscovery();
  const [range, setRange] = useState("day");

  async function syncAll() {
    await dashboardState.reloadDashboard();
    await storageState.inspectStorage(dashboardState.activeTicker, storageState.filters);
  }

  const agentState = useAgent({
    activeTicker: dashboardState.activeTicker,
    period: dashboardState.period,
    watchlist: dashboardState.watchlist,
    onSync: syncAll,
  });

  const summary = ensureObject(dashboardState.dashboard.summary);
  const quality = ensureObject(dashboardState.dashboard.quality);
  const dbSummary = ensureObject(dashboardState.dashboard.db_summary);
  const pricePeriods = ensureObject(dashboardState.dashboard.price_periods);
  const priceRows = ensureArray(pricePeriods[range]).length ? ensureArray(pricePeriods[range]) : firstSeries(dashboardState.dashboard.price_history);
  const volumeRows = firstSeries(dashboardState.dashboard.volume_history);
  const sentimentSeries = ensureArray(dashboardState.dashboard.sentiment_series);
  const sentimentTimeline = ensureArray(dashboardState.dashboard.sentiment_timeline);
  const newsItems = ensureArray(dashboardState.dashboard.news);
  const topics = ensureArray(dashboardState.dashboard.topics);

  return (
    <AppShell
      header={
        <HeroHeader
          activeTicker={dashboardState.activeTicker}
          period={dashboardState.period}
          pendingTicker={dashboardState.pendingTicker}
          loading={dashboardState.loading}
          validating={dashboardState.validating}
          notice={dashboardState.notice}
          onActiveTickerChange={dashboardState.setActiveTicker}
          onTickerBlur={dashboardState.reloadDashboard}
          onPeriodChange={dashboardState.changePeriod}
          onPendingTickerChange={dashboardState.setPendingTicker}
          onAddTicker={dashboardState.validatePendingTicker}
          onReload={dashboardState.reloadDashboard}
          onRefreshTicker={async () => {
            await dashboardState.refreshActiveTicker();
            await storageState.inspectStorage(dashboardState.activeTicker, storageState.filters);
          }}
          onRefreshWatchlist={async () => {
            await dashboardState.refreshWatchlist();
            await storageState.inspectStorage(dashboardState.activeTicker, storageState.filters);
            await agentState.reloadAgent();
          }}
        />
      }
      freshness={<DataFreshness summary={summary} health={dashboardState.health} />}
      agentPanel={
        <AutoAgentPanel
          agent={agentState.status}
          runs={agentState.runs}
          onRefreshStale={agentState.refreshStale}
          onRunNow={agentState.runNow}
        />
      }
      quality={<QualityStrip quality={quality} />}
      tickerTabs={
        <TickerTabs
          tickers={dashboardState.watchlist}
          selected={dashboardState.activeTicker}
          onSelect={dashboardState.selectTicker}
        />
      }
      sectionTabs={
        <SectionTabs
          active={dashboardState.activeSection}
          onSelect={dashboardState.setActiveSection}
        />
      }
    >
      {dashboardState.activeSection === "overview" ? (
        <>
          <OverviewPanel ticker={dashboardState.activeTicker} summary={summary} dbSummary={dbSummary} />

          <TickerStoragePanel
            ticker={dashboardState.activeTicker}
            storageSymbol={storageState.storageSymbol}
            onStorageSymbolChange={storageState.setStorageSymbol}
            availability={storageState.availability}
            recordsPayload={storageState.recordsPayload}
            loading={storageState.loading}
            error={storageState.error}
            filters={storageState.filters}
            onFilterChange={storageState.updateFilter}
            onInspect={() => storageState.inspectStorage(storageState.storageSymbol, storageState.filters)}
            onUseActiveTicker={storageState.useActiveTicker}
          />

          <section className="dashboard-grid">
            <div className="panel">
              <div className="panel-heading">
                <h2>Price Trend</h2>
                <span>{priceRows.length} rows</span>
              </div>
              <LineChart rows={priceRows} valueKey="close" label={`${dashboardState.activeTicker} ${range} price`} />
            </div>

            <div className="panel">
              <div className="panel-heading">
                <h2>Sentiment Trend</h2>
                <span>{sentimentSeries.length} buckets</span>
              </div>
              <LineChart rows={sentimentSeries} valueKey="sentiment" label={`${dashboardState.activeTicker} sentiment`} />
              <SentimentTimeline rows={sentimentTimeline} />
              {!quality.sentiment_available ? (
                <p className="muted small">
                  Sentiment is shown only when ticker-relevant English news/search text exists.
                </p>
              ) : null}
            </div>

            <ProviderPanel providers={dashboardState.providerStatuses} keyStatus={dashboardState.keyStatus} />

            <section className="panel">
              <div className="panel-heading">
                <h2>Topic Clusters</h2>
                <span>{topics.length}</span>
              </div>
              <TopicSummary topics={topics} />
            </section>
          </section>
        </>
      ) : null}

      {dashboardState.activeSection === "price" ? (
        <PricePanel
          ticker={dashboardState.activeTicker}
          range={range}
          onRangeChange={setRange}
          priceRows={priceRows}
          volumeRows={volumeRows}
          dailyChange={ensureObject(dashboardState.dashboard.daily_change || summary.daily_change)}
          volumeAvailable={quality.volume_available}
        />
      ) : null}

      {dashboardState.activeSection === "sentiment" ? (
        <SentimentPanel
          ticker={dashboardState.activeTicker}
          sentimentSeries={sentimentSeries}
          sentimentTimeline={sentimentTimeline}
          topics={topics}
          sentimentLabel={summary.sentiment_label}
          sentimentAvailable={quality.sentiment_available}
        />
      ) : null}

      {dashboardState.activeSection === "news" ? (
        <NewsPanel ticker={dashboardState.activeTicker} items={newsItems} />
      ) : null}

      {dashboardState.activeSection === "crypto-fx" ? (
        <CrossAssetPanel dashboard={dashboardState.dashboard} />
      ) : null}

      {dashboardState.activeSection === "providers" ? (
        <ProviderPanel providers={dashboardState.providerStatuses} keyStatus={dashboardState.keyStatus} />
      ) : null}

      {dashboardState.activeSection === "macro-discovery" ? (
        <CensusDiscoveryPanel
          query={censusState.query}
          onQueryChange={censusState.setQuery}
          kind={censusState.kind}
          onKindChange={censusState.changeKind}
          results={censusState.results}
          loading={censusState.loading}
          error={censusState.error}
          onSearch={(event) => {
            event.preventDefault();
            return censusState.search(censusState.query, censusState.kind);
          }}
          onChooseQuery={censusState.chooseFeaturedQuery}
          compareItems={censusState.compareItems}
          onToggleCompare={censusState.toggleCompare}
          onClearCompare={censusState.clearCompare}
        />
      ) : null}

      {dashboardState.activeSection === "report" ? (
        <section className="dashboard-grid one">
          <DailyBriefPanel
            brief={dashboardState.latestBrief}
            loading={dashboardState.briefLoading}
            onGenerate={dashboardState.generateDailyBrief}
          />
          <ReportPanel
            ticker={dashboardState.activeTicker}
            report={dashboardState.reportText}
            onGenerate={dashboardState.generateReport}
          />
        </section>
      ) : null}

      {dashboardState.activeSection === "chat" ? (
        <ChatPanel
          ticker={dashboardState.activeTicker}
          messages={agentState.messages}
          onSend={agentState.sendMessage}
        />
      ) : null}
    </AppShell>
  );
}
