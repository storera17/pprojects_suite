// Shared test fixture: a small, self-contained course built through the
// REAL pipeline (synthesis → cards → embeddings), but with its own fixture
// taxonomy/contexts/glossary — deliberately decoupled from the real,
// progressively-authored content in backend/content-pipeline/knowledge/, so engine tests
// stay deterministic as authoring continues across sessions.
// @ts-expect-error — pipeline is plain ESM JS
import { assembleCourse } from '../content-pipeline/generate-course.mjs';
// @ts-expect-error — pipeline is plain ESM JS
import { normalizeGlossary } from '../content-pipeline/synthesize.mjs';
import type { Course } from '../src/core/types';

const FIXTURE_CONTEXTS: Record<string, any> = {
  'sd-foundations': {
    domain: 'foundations', overview: 'Core analytics vocabulary.',
    why: 'Shared terms let teams communicate precisely about data work.',
    workplace: 'A new analyst joins a team and needs to follow standups without asking what every term means.',
    mistakes: ['Using "analytics" terms interchangeably without precision.'],
    sources: [
      { title: 'Foundations Course Notes', kind: 'course', ref: 'Fixture Course A' },
      { title: 'Foundations Reference', kind: 'docs', ref: 'Fixture Docs A' },
    ],
  },
  'sd-trees': {
    domain: 'data mining', overview: 'Tree-based predictive modeling.',
    why: 'Tree models are interpretable and widely used baselines.',
    workplace: 'A churn-modeling team builds a decision tree to explain which factors drive cancellations.',
    mistakes: ['Growing a tree too deep and overfitting the training data.'],
    sources: [
      { title: 'Tree Models Course Notes', kind: 'course', ref: 'Fixture Course B' },
      { title: 'Tree Models Reference', kind: 'docs', ref: 'Fixture Docs B' },
    ],
  },
  'sd-dax': {
    domain: 'power bi', overview: 'DAX calculation concepts.',
    why: 'Correct filter context is the difference between a right and wrong number on a dashboard.',
    workplace: 'A BI developer debugs why a CALCULATE measure returns the wrong total after adding a slicer.',
    mistakes: ['Forgetting that CALCULATE modifies filter context, not just adds a filter.'],
    sources: [
      { title: 'DAX Course Notes', kind: 'course', ref: 'Fixture Course C' },
      { title: 'DAX Reference', kind: 'docs', ref: 'Fixture Docs C' },
    ],
  },
};

const FIXTURE_GLOSSARY = normalizeGlossary([
  {
    m: ['descriptive analytics'],
    d: 'Descriptive analytics «summarizes what already happened» in the data.',
    how: 'Aggregate historical data into summaries, dashboards, and reports.',
    ex: 'A monthly sales dashboard showing last quarter\'s revenue by region.',
    src: [{ title: 'Foundations Course Notes', kind: 'course', ref: 'Fixture Course A' }],
  },
  {
    m: ['predictive analytics'],
    d: 'Predictive analytics «uses historical data to estimate future outcomes».',
    how: 'Fit a model on historical data, then score new records with it.',
    ex: 'Predicting which customers are likely to churn next month.',
    src: [{ title: 'Foundations Course Notes', kind: 'course', ref: 'Fixture Course A' }],
  },
  {
    m: ['overfitting'],
    d: 'Overfitting happens when a model «memorizes noise in the training data instead of generalizing».',
    how: 'Compare training accuracy to held-out validation accuracy — a large gap signals overfitting.',
    ex: 'A decision tree grown to full depth scores 99% on training data but only 60% on new data.',
    mk: 'Judging a model only on training accuracy.',
    src: [{ title: 'Tree Models Course Notes', kind: 'course', ref: 'Fixture Course B' }],
  },
  {
    m: ['gini index'],
    d: 'The Gini index measures «node impurity» when choosing how to split a decision tree.',
    how: 'At each candidate split, compute the Gini index for the resulting groups and pick the split that minimizes it.',
    src: [{ title: 'Tree Models Course Notes', kind: 'course', ref: 'Fixture Course B' }],
  },
  {
    m: ['pruning the tree', 'pruning'],
    d: 'Pruning «removes branches that don\'t improve validation performance» to reduce overfitting.',
    how: 'Grow a full tree, then cut back branches that don\'t improve held-out accuracy.',
    src: [{ title: 'Tree Models Course Notes', kind: 'course', ref: 'Fixture Course B' }],
  },
  {
    m: ['confusion matrix'],
    d: 'A confusion matrix is a table that «cross-tabulates predicted vs. actual classes» for a classifier.',
    how: 'Count true positives, false positives, true negatives, and false negatives across a test set.',
    src: [{ title: 'Tree Models Course Notes', kind: 'course', ref: 'Fixture Course B' }],
  },
  {
    m: ['roc curves and auc', 'roc curve', 'auc'],
    d: 'An ROC curve plots true positive rate against false positive rate across thresholds; AUC is «the area under that curve», summarizing ranking quality in one number.',
    src: [{ title: 'Tree Models Course Notes', kind: 'course', ref: 'Fixture Course B' }],
  },
  {
    m: ['calculate function syntax', 'calculate'],
    d: 'CALCULATE «evaluates an expression in a modified filter context», making it the core function for filter manipulation in DAX.',
    how: 'Pass an expression plus one or more filter arguments; each filter argument overrides or adds to the existing filter context.',
    ex: 'CALCULATE(SUM(Sales[Amount]), Sales[Region]="West") totals sales for the West region regardless of any visual-level filter.',
    mk: 'Assuming CALCULATE only adds filters — it can also override existing filters on the same column.',
    src: [{ title: 'DAX Course Notes', kind: 'course', ref: 'Fixture Course C' }],
  },
  {
    m: ['filter context'],
    d: 'Filter context is «the set of filters in effect when a DAX measure is evaluated», determined by report visuals, slicers, and explicit CALCULATE filters.',
    how: 'Trace every slicer, visual-level filter, and CALCULATE argument that applies to a cell to know its filter context.',
    src: [{ title: 'DAX Course Notes', kind: 'course', ref: 'Fixture Course C' }],
  },
]);

const FIXTURE_SKELETON = [
  {
    id: 'foundations', title: 'Foundations', tagline: 'Fixture deck A', order: 0,
    subdecks: [
      {
        id: 'sd-foundations', deckId: 'foundations', title: 'Foundations', difficulty: 1,
        concepts: ['descriptive analytics', 'predictive analytics'],
      },
    ],
  },
  {
    id: 'mining', title: 'Mining', tagline: 'Fixture deck B', order: 1,
    subdecks: [
      {
        id: 'sd-trees', deckId: 'mining', title: 'Tree-Based Models', difficulty: 2,
        concepts: ['overfitting', 'gini index', 'pruning the tree', 'confusion matrix', 'ROC curves and AUC'],
      },
    ],
  },
  {
    id: 'powerbi', title: 'Power BI', tagline: 'Fixture deck C', order: 2,
    subdecks: [
      {
        id: 'sd-dax', deckId: 'powerbi', title: 'DAX', difficulty: 3,
        concepts: ['CALCULATE function syntax', 'filter context'],
      },
    ],
  },
];

let cached: Course | null = null;
export function fixtureCourse(): Course {
  if (!cached) {
    cached = assembleCourse(FIXTURE_SKELETON, {
      contexts: FIXTURE_CONTEXTS,
      entries: FIXTURE_GLOSSARY,
    }) as Course;
  }
  return cached;
}
