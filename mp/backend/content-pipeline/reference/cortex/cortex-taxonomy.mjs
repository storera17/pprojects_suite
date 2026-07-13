// Taxonomy: maps the 55 spreadsheet classes onto a foundational→advanced
// deck structure, semantically clusters rows with no class value, and
// chunks each subdeck into ordered lessons.
import { norm, slug, shorten } from './util.mjs';

/**
 * Decks in learning order. Each subdeck lists the source class names (in
 * pedagogical order — not spreadsheet order) plus a difficulty tier 1–3
 * that drives card volume.
 */
export const DECKS = [
  {
    id: 'foundations', title: 'Foundations of Analytics',
    tagline: 'The shared vocabulary of business analytics, big data, and AI.',
    classes: [
      ['Background Vocabulary', 1],
      ['Basics of Big Data Analytics', 1],
      ['AI Overview', 1],
    ],
  },
  {
    id: 'tools', title: 'Professional Tools & Workflow',
    tagline: 'The day-to-day stack of a working analyst and data engineer.',
    classes: [], // populated by clustering unclassified rows
  },
  {
    id: 'powerbi', title: 'Power BI, DAX & Visualization',
    tagline: 'Model, calculate, and communicate with the Microsoft BI stack.',
    classes: [
      ['Data Modeling using Power BI', 2],
      ['Dax Query Language', 3],
      ['Data Visualization, Dashboards, & Storytelling', 1],
    ],
  },
  {
    id: 'python-data', title: 'Python, APIs & NoSQL',
    tagline: 'Acquire, shape, and store data programmatically.',
    classes: [
      ['Python Programming Language', 1],
      ['Data Collection from Web API', 2],
      ['NoSQL Databases', 2],
    ],
  },
  {
    id: 'mining', title: 'Data Mining & Predictive Modeling',
    tagline: 'From raw records to validated predictive models.',
    classes: [
      ['Data Mining', 1],
      ['Regression Review with the Data Mining Process', 1],
      ['Exploratory Data Analysis (EDA)', 2],
      ['Dimension Reduction', 2],
      ['Evaluating Model Performance', 2],
      ['Evaluating Model Performance - Classification Models', 2],
      ['Evaluating Model Performance - Classification and Ranking Models', 3],
      ['Predictive Use of Regression', 2],
      ['Logistic Rgeression Models', 2],
      ['Tree-Based Models', 2],
      ['Ensembling Tree', 3],
      ['Text Mining', 2],
    ],
  },
  {
    id: 'deep-learning', title: 'Machine Learning & Deep Learning',
    tagline: 'Neural architectures, gradients, and the models behind modern AI.',
    classes: [
      ['Neural Networks', 2],
      ['Gradients and Regularization', 3],
      ['Classification Deep Dive', 3],
      ['Feed-Forward Architecture', 3],
      ['Support Vector Machines', 3],
      ['AutoEncoders', 3],
      ['Convolutional Neural Networks (CNNs)', 3],
      ['Recurrent Neural Networks (RNNs)', 3],
      ['Ensemble-Hybrid Learning', 3],
    ],
  },
  {
    id: 'optimization', title: 'Optimization & Decision Science',
    tagline: 'Prescriptive analytics: mathematical programming and algorithms.',
    classes: [
      ['Introduction & Overview to Modeling and Optimization', 1],
      ['Introduction into Mathematical Programming', 2],
      ['Complexity and Algorithm Analysis', 2],
      ['Linear Programming (LP)', 3],
      ['Integer Programming (IP)', 3],
      ['Transportation and Assignment Problems', 2],
      ['Network Flow Problems', 2],
    ],
  },
  {
    id: 'bigdata', title: 'Big Data & Spark',
    tagline: 'Distributed storage, distributed compute, and ML at scale.',
    classes: [
      ['Big Data Systems', 2],
      ['Analytics on Big Data Platform - Apache Spark', 2],
      ['Distributed Computing on Spark', 3],
      ['Machine Learning at Scale', 3],
      ['Recommender Systems', 2],
    ],
  },
  {
    id: 'experiments', title: 'Experimentation & Causal Inference',
    tagline: 'Design trustworthy experiments and estimate true causal effects.',
    classes: [
      ['Introduction to Business Experiments', 1],
      ['A/B Tesing', 3],
      ['A/B/n Testing', 2],
      ['Blocking', 2],
      ['Factorial Designs', 3],
      ['Multi-Armed Bandits in Online Testing', 3],
      ['Switchback Experiments', 2],
      ['Causal Inference', 3],
    ],
  },
  {
    id: 'genai', title: 'Generative AI & LLMs',
    tagline: 'NLP, prompting, RAG, agents, evaluation, and deployment.',
    classes: [
      ['Spark NLP & LLM', 2],
      ['Prompt Engineering and RAG', 2],
      ['Evaluation and Deployment of GenAI', 3],
      ['Agentic AI and LLM Fine-Tuning', 3],
    ],
  },
];

/**
 * Semantic clustering rules for rows with a blank Class. First matching
 * rule wins; every cluster becomes a subdeck of "Professional Tools".
 */
export const TOOL_CLUSTERS = [
  {
    id: 'dev-tools', title: 'Version Control & AI Dev Tools', difficulty: 1,
    match: /\b(git|github|claude code|cursor|azure devops|agile|scrum)\b/i,
  },
  {
    id: 'data-stack', title: 'Modern Data Stack & BI Platforms', difficulty: 2,
    match: /\b(snowflake|dbt|sigma|alteryx|bi workflow|sql|tableau|looker)\b/i,
  },
  {
    id: 'excel', title: 'Excel & Office Analytics', difficulty: 1,
    match: /\b(excel|pivot tables?|lookups?|v-?lookups?|sumifs?|vba|macros?|microsoft access)\b/i,
  },
  {
    id: 'python-stack', title: 'Python Scientific Stack & MATLAB', difficulty: 2,
    match: /\b(numpy|pandas|pytorch|tensorflow|matlab|scipy|scikit)\b/i,
  },
  {
    id: 'cloud', title: 'Cloud Platforms', difficulty: 2,
    match: /\b(aws|azure|gcp|cloud)\b/i,
  },
  {
    id: 'enterprise', title: 'Enterprise & Supply Chain Systems', difficulty: 1,
    match: /\b(retailex|pos system|ariba|beeline|sharepoint|sps commerce|edi|order management|warehouse management|final mile|systems-facing|erp|sap)\b/i,
  },
  {
    id: 'simulation', title: 'Simulation & Defense Analytics Tools', difficulty: 2,
    match: /\b(piano|hal|hjmp|dakota|ms&a|afsim|ngts|itase|simulation)\b/i,
  },
];

export function clusterUnclassified(term) {
  for (const c of TOOL_CLUSTERS) if (c.match.test(term)) return c;
  // Fallback: generic professional-tools bucket.
  return TOOL_CLUSTERS.find((c) => c.id === 'enterprise');
}

/** Lessons of 5–9 concepts, preserving each class's pedagogical row order. */
export function chunkLessons(conceptList, target = 7) {
  const n = conceptList.length;
  if (n === 0) return [];
  const lessonCount = Math.max(1, Math.round(n / target));
  const size = Math.ceil(n / lessonCount);
  const lessons = [];
  for (let i = 0; i < n; i += size) lessons.push(conceptList.slice(i, i + size));
  return lessons;
}

export function lessonTitle(concepts, index) {
  const first = concepts[0]?.term ?? 'Lesson';
  return `${shorten(first.replace(/\?.*$/, '?'), 46)}`;
}

/** Build the full deck/subdeck/lesson skeleton from extracted rows. */
export function buildStructure(rows) {
  const classIndex = new Map(); // klass -> {deckId, difficulty, order}
  DECKS.forEach((d) => d.classes.forEach(([k, diff], i) => classIndex.set(k, { deckId: d.id, difficulty: diff, order: i })));

  const subdeckMap = new Map(); // key -> {id,deckId,title,difficulty,order,sourceClass,concepts[]}
  const ensureSubdeck = (key, props) => {
    if (!subdeckMap.has(key)) subdeckMap.set(key, { concepts: [], ...props });
    return subdeckMap.get(key);
  };

  let unknownClassCount = 0;
  for (const row of rows) {
    if (row.klass && classIndex.has(row.klass)) {
      const { deckId, difficulty, order } = classIndex.get(row.klass);
      const sd = ensureSubdeck(`cls:${row.klass}`, {
        id: `sd-${slug(row.klass)}`, deckId, title: cleanClassTitle(row.klass),
        difficulty, order, sourceClass: row.klass,
      });
      sd.concepts.push(row);
    } else if (row.klass) {
      // A class string we have no mapping for: best-fit by keyword overlap,
      // else file under foundations so nothing is dropped.
      unknownClassCount++;
      const sd = ensureSubdeck(`cls:${row.klass}`, {
        id: `sd-${slug(row.klass)}`, deckId: 'foundations', title: cleanClassTitle(row.klass),
        difficulty: 2, order: 90 + unknownClassCount, sourceClass: row.klass,
      });
      sd.concepts.push(row);
    } else {
      const cluster = clusterUnclassified(row.term);
      const sd = ensureSubdeck(`tool:${cluster.id}`, {
        id: `sd-${cluster.id}`, deckId: 'tools', title: cluster.title,
        difficulty: cluster.difficulty, order: TOOL_CLUSTERS.indexOf(cluster), sourceClass: null,
      });
      sd.concepts.push(row);
    }
  }

  const decks = DECKS.map((d, di) => ({
    id: d.id, title: d.title, tagline: d.tagline, order: di,
    subdecks: [...subdeckMap.values()]
      .filter((s) => s.deckId === d.id)
      .sort((a, b) => a.order - b.order),
  })).filter((d) => d.subdecks.length > 0);

  return decks;
}

function cleanClassTitle(k) {
  return k
    .replace(/Tesing/g, 'Testing')
    .replace(/Rgeression/g, 'Regression')
    .replace(/Dax Query Language/g, 'DAX Query Language')
    .replace(/Ensembling Tree\b/g, 'Ensembling Trees');
}