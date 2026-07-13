// Public demo course generator.
//
// This intentionally uses synthetic concepts and sources so the GitHub build
// can be exercised without publishing raw course files, extracted textbook
// text, or the full private generated course.
import { mkdirSync, writeFileSync } from 'node:fs';
import { assembleCourse } from './generate-course.mjs';
import { normalizeGlossary } from './synthesize.mjs';

const DEMO_CONTEXTS = {
  'sd-demo-foundations': {
    domain: 'analytics foundations',
    overview: 'A compact synthetic overview of how teams turn data into decisions.',
    why: 'Shared vocabulary lets product, finance, and operations teams make decisions from the same facts.',
    workplace: 'A small operations team reviews a dashboard, checks a forecast, and decides which bottleneck to fix first.',
    mistakes: ['Treating a metric movement as causal before checking the business process behind it.'],
    sources: [
      { title: 'MomentumProdigy Synthetic Demo Notes', kind: 'course', ref: 'Demo content only' },
      { title: 'Internal Demo Analytics Handbook', kind: 'docs', ref: 'Synthetic reference' },
    ],
  },
  'sd-demo-modeling': {
    domain: 'predictive modeling',
    overview: 'A compact synthetic modeling workflow from feature design to validation.',
    why: 'Model quality depends on trustworthy data, appropriate validation, and clear interpretation.',
    workplace: 'A customer-success team scores accounts for churn risk and uses explanations to plan outreach.',
    mistakes: ['Optimizing validation accuracy while ignoring whether the model can be acted on.'],
    sources: [
      { title: 'MomentumProdigy Synthetic Modeling Notes', kind: 'course', ref: 'Demo content only' },
      { title: 'Internal Demo Model Review Checklist', kind: 'docs', ref: 'Synthetic reference' },
    ],
  },
  'sd-demo-bi': {
    domain: 'business intelligence',
    overview: 'A compact synthetic BI workflow covering metrics, slices, and dashboard trust.',
    why: 'Dashboards become decision systems only when metrics are consistently defined and easy to audit.',
    workplace: 'A revenue team compares weekly pipeline conversion by segment and checks whether the definition changed.',
    mistakes: ['Building attractive charts before agreeing on the metric definition and grain.'],
    sources: [
      { title: 'MomentumProdigy Synthetic BI Notes', kind: 'course', ref: 'Demo content only' },
      { title: 'Internal Demo Dashboard Standards', kind: 'docs', ref: 'Synthetic reference' },
    ],
  },
};

const DEMO_GLOSSARY = normalizeGlossary([
  {
    m: ['decision metric'],
    d: 'A decision metric is a «clearly defined number tied to a specific business choice».',
    how: 'State the owner, formula, grain, refresh cadence, and action threshold before using it in a review.',
    ex: 'Weekly qualified-pipeline conversion by segment is used to decide where sales enablement should focus.',
    mk: 'Reporting a number without saying what decision it is meant to inform.',
    src: [{ title: 'MomentumProdigy Synthetic Demo Notes', kind: 'course', ref: 'Demo content only' }],
  },
  {
    m: ['data provenance'],
    d: 'Data provenance records «where a dataset came from and how it was transformed».',
    how: 'Track source systems, extraction time, transformations, joins, filters, and known exclusions.',
    ex: 'A dashboard footnote says revenue comes from booked invoices, excludes test accounts, and refreshes nightly.',
    mk: 'Trusting a polished dashboard without checking whether the data lineage matches the question.',
    src: [{ title: 'Internal Demo Analytics Handbook', kind: 'docs', ref: 'Synthetic reference' }],
  },
  {
    m: ['validation split'],
    d: 'A validation split is a «held-out portion of data used to estimate performance before final deployment».',
    how: 'Separate training and validation records in a way that matches future use, especially for time-based data.',
    ex: 'A churn model trains on January through September and validates on October accounts.',
    mk: 'Randomly splitting time-series data in a way that leaks future behavior into training.',
    src: [{ title: 'MomentumProdigy Synthetic Modeling Notes', kind: 'course', ref: 'Demo content only' }],
  },
  {
    m: ['feature leakage'],
    d: 'Feature leakage happens when a model uses «information that would not be available at prediction time».',
    how: 'Review every feature against the exact moment the prediction would be made in production.',
    ex: 'Using cancellation-date fields to predict cancellation risk creates artificially high validation scores.',
    mk: 'Celebrating high accuracy before auditing whether features are available at scoring time.',
    src: [{ title: 'Internal Demo Model Review Checklist', kind: 'docs', ref: 'Synthetic reference' }],
  },
  {
    m: ['metric grain'],
    d: 'Metric grain is the «level at which a metric is counted or aggregated».',
    how: 'Declare whether each row represents an account, order, user, session, week, or other unit.',
    ex: 'Average revenue per account and average revenue per order answer different questions.',
    mk: 'Joining metrics with different grains and accidentally duplicating totals.',
    src: [{ title: 'MomentumProdigy Synthetic BI Notes', kind: 'course', ref: 'Demo content only' }],
  },
  {
    m: ['filter context'],
    d: 'Filter context is the «set of active filters that determines which records contribute to a result».',
    how: 'Read slicers, page filters, visual filters, and formula-level filters before interpreting a number.',
    ex: 'A conversion rate changes when the dashboard is sliced to enterprise accounts only.',
    mk: 'Assuming a dashboard total and a filtered visual use the same denominator.',
    src: [{ title: 'Internal Demo Dashboard Standards', kind: 'docs', ref: 'Synthetic reference' }],
  },
]);

const DEMO_SKELETON = [
  {
    id: 'foundations',
    title: 'Analytics Foundations',
    tagline: 'Synthetic demo concepts for decision-ready analytics.',
    order: 0,
    subdecks: [
      {
        id: 'sd-demo-foundations',
        deckId: 'foundations',
        title: 'Decision-Ready Analytics',
        difficulty: 1,
        concepts: ['decision metric', 'data provenance'],
      },
    ],
  },
  {
    id: 'modeling',
    title: 'Modeling Workflow',
    tagline: 'Synthetic demo concepts for model validation and risk.',
    order: 1,
    subdecks: [
      {
        id: 'sd-demo-modeling',
        deckId: 'modeling',
        title: 'Model Validation',
        difficulty: 2,
        concepts: ['validation split', 'feature leakage'],
      },
    ],
  },
  {
    id: 'bi',
    title: 'Business Intelligence',
    tagline: 'Synthetic demo concepts for trustworthy dashboards.',
    order: 2,
    subdecks: [
      {
        id: 'sd-demo-bi',
        deckId: 'bi',
        title: 'Dashboard Trust',
        difficulty: 2,
        concepts: ['metric grain', 'filter context'],
      },
    ],
  },
];

const course = assembleCourse(DEMO_SKELETON, {
  contexts: DEMO_CONTEXTS,
  entries: DEMO_GLOSSARY,
});

course.meta.name = 'MomentumProdigy Public Demo Course';
course.meta.generatedAt = new Date().toISOString();
course.meta.publicDemo = true;

mkdirSync(new URL('../../frontend/public/course/', import.meta.url), { recursive: true });
writeFileSync(new URL('../../frontend/public/course/course.json', import.meta.url), JSON.stringify(course, null, 2));
console.log('Synthetic demo course generated -> frontend/public/course/course.json');