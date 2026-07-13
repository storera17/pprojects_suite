// Glossary entries for the "powerbi" deck. Each entry:
// { m: [matchers...], d: 'definition with «cloze phrases»', how, ex, we, mk, src: [{title,kind,ref}] }
// Grounded in backend/content-pipeline/extracted/... per backend/content-pipeline/taxonomy.mjs sourcePaths.
//
// sd-dax — ISA 512 Module 1 "Data Preparation using DAX Query Language"
// (M1.3 Table Functions, M1.4 Evaluation Contexts slides)
const SD_DAX_SRC = [
  { title: 'ISA 512: Data Preparation using DAX Query Language', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.3 Table Functions, 1.4 Evaluation Contexts)' },
];

// sd-powerbi-modeling — ISA 512 Module 2 "Data Modeling using Power BI"
// (M2.1 Data Warehouses & Data Lakes, M2.2 Denormalization, M2.5 Segmentation, M2.7 Semi/Non-Additive Facts)
const SD_POWERBI_MODELING_SRC = [
  { title: 'ISA 512: Data Modeling using Power BI', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2.1, 2.2, 2.5, 2.7)' },
];

// sd-dashboards — ISA 512 Module 3 "Data Visualization, Dashboards, and Storytelling"
// (M3.1 Data Encoding, M3.2 Dashboard Design Principles, M3.3 Visual Hierarchy & Storytelling)
const SD_DASHBOARDS_SRC = [
  { title: 'ISA 512: Data Visualization, Dashboards, and Storytelling', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3.1-3.3, citing Stephen Few and Cole Nussbaumer Knaflic)' },
];

export const GLOSSARY_powerbi = [
  {
    m: ['evaluation context', 'evaluation contexts'],
    d: 'Evaluation context is the pillar concept of DAX: «the value of a formula depends on the context it\'s evaluated in» — there are two types, filter context and row context, and the same formula can return different results depending on which context surrounds it.',
    ex: 'Two calculated columns can use the literal same formula but produce different results because they sit in different row contexts (e.g., one calculated per customer segment, one per product category).',
    src: SD_DAX_SRC,
  },
  {
    m: ['filter context'],
    d: 'Filter context is defined by «row selection, column selection, report filters, and slicer selections» — any data outside the active filter context is excluded from the calculation entirely.',
    mk: 'Forgetting that report filters and slicers are part of the filter context too, not just the explicit DAX filter functions — a measure\'s result silently changes as a user clicks a slicer.',
    src: SD_DAX_SRC,
  },
  {
    m: ['row context'],
    d: 'Row context introduces the concept of a «"current row"», defined automatically by a calculated column definition, by iterator functions (SUMX, AVERAGEX), or by other functions like FILTER — it determines which row\'s column values a formula can directly reference.',
    ex: 'The formula Orders[Quantity] * Orders[Price] works as a calculated column (row context exists automatically) but fails as a measure with the error "a single value... cannot be determined" — really meaning "you need a row context."',
    mk: 'Writing a row-by-row formula as a measure instead of a calculated column — measures don\'t have an automatic row context, so the same expression that works as a column throws an ambiguous-value error as a measure.',
    src: SD_DAX_SRC,
  },
  {
    m: ['filter (dax)', 'filter function'],
    d: 'FILTER is a DAX table function that «restricts the rows of a table to those meeting a condition, and returns a table» — it needs a table as its first argument (which can itself be another table function) and is commonly nested inside other functions.',
    src: SD_DAX_SRC,
  },
  {
    m: ['all vs. allselected', 'all vs allselected', 'all (dax)', 'allselected (dax)'],
    d: 'ALL «returns all rows of a table, ignoring every existing filter» (used to calculate a value\'s contribution to the whole), while ALLSELECTED «removes context filters from the current query but retains all explicit filters» — they answer different "compared to what baseline?" questions.',
    src: SD_DAX_SRC,
  },
  {
    m: ['distinct vs. values', 'distinct vs values', 'distinct (dax)', 'values (dax)'],
    d: 'DISTINCT and VALUES both return the unique values of a column visible in the current filter context, but VALUES «additionally includes a blank row if it is visible in the filter context» (a row DAX creates to guarantee referential integrity) while DISTINCT does not.',
    src: SD_DAX_SRC,
  },
  {
    m: ['bi-directional cross filter', 'bidirectional filter', 'filter propagation'],
    d: 'Filter propagation across a relationship can be set to «single (propagates only from the one side to the many side) or both/bi-directional (propagates both ways)» — bi-directional filtering enables questions like "how many customers purchased each product" but risks performance degradation, confusing results, and model ambiguity.',
    mk: 'Defaulting every relationship to bi-directional filtering for convenience — it\'s powerful for specific cross-table questions but commonly introduces ambiguity and slows the model down.',
    src: SD_DAX_SRC,
  },

  // ---- sd-powerbi-modeling ----
  {
    m: ['data lake'],
    d: 'A data lake «retains all business data in its original form, supports every data type, and adapts easily to changing business needs» — trading some data quality (compared to a curated warehouse) for flexibility and faster access to raw data.',
    mk: 'Treating "more data, more flexibility" as a free lunch — without governance, a data lake degrades into a data swamp, where nobody knows what data exists, what it means, or who owns it.',
    src: SD_POWERBI_MODELING_SRC,
  },
  {
    m: ['data swamp'],
    d: 'A data swamp is what a data lake becomes when it lacks proper data governance: «poor metadata, irrelevant or low-quality data, and no clarity on what information exists, why it\'s there, what it means, or who owns it».',
    src: SD_POWERBI_MODELING_SRC,
  },
  {
    m: ['model ambiguity', 'snowflake schema'],
    d: 'Model ambiguity occurs when «multiple paths exist between two tables in a data model» — Power BI does not permit ambiguous models, so one relationship must be deactivated; this is resolved via inactive relationships activated on demand (USERELATIONSHIP), role-playing dimensions, or further denormalization.',
    ex: 'A "snowflaked" schema (where a dimension links to another dimension instead of directly to the fact table) doesn\'t violate the star-schema concept, but it\'s frequently eliminated through denormalization to keep the model simple and unambiguous.',
    src: SD_POWERBI_MODELING_SRC,
  },
  {
    m: ['semi-additive fact', 'non-additive fact'],
    d: 'Not every fact can be summed across every dimension: «non-additive facts (like unit price) can never be meaningfully added, while semi-additive facts (like account balance) can be summed across some dimensions but not across time» — these require special handling like the LASTDATE function instead of a plain SUM.',
    ex: 'Summing a daily account-balance column over a month gives a meaningless number; instead, you\'d use LASTDATE to pull just the balance as of the most recent day in the period.',
    mk: 'Applying SUM blindly to every numeric column in a fact table — quantities and sales dollars are additive, but unit prices, currency rates, and point-in-time balances are not.',
    src: SD_POWERBI_MODELING_SRC,
  },
  {
    m: ['segmentation (power bi)', 'static segmentation', 'dynamic segmentation'],
    d: 'Power BI segmentation comes in three flavors depending on how often the grouping changes: «static (fixed forever, e.g. a price-range calculated column), semi-static (changes slowly, e.g. an ABC/Pareto product-tier calculated column in a dimension table), and dynamic (changes per slice, requiring a measure that iterates over a segment-definition helper table)».',
    ex: 'Classifying customers into "high/medium/low value" segments that can shift year to year requires dynamic segmentation — a measure, not a calculated column, because the segment isn\'t fixed for a given customer.',
    mk: 'Trying to implement a segment that can change over time (dynamic segmentation) as a calculated column — calculated columns are computed once and stored, so they can\'t represent a value that depends on which year or filter context is active.',
    src: SD_POWERBI_MODELING_SRC,
  },

  // ---- sd-dashboards ----
  {
    m: ['data encoding'],
    d: 'Data encoding is «the representation of data using visual attributes like color and geometry, matched to the data type, so the human visual system can read it intuitively» — categorical data (nominal, ordinal) and quantitative data (interval, ratio) each pair best with different visual attributes.',
    how: 'Position and length are the visual attributes the brain reads most accurately and with the most distinguishable gradations, so reserve them for your most important quantitative measures rather than for less critical dimensions.',
    mk: 'Encoding an important quantitative measure with a weak visual attribute like area or color saturation (hard for the eye to compare precisely) instead of position or length.',
    src: SD_DASHBOARDS_SRC,
  },
  {
    m: ['dashboard (definition)', 'what is a dashboard'],
    d: 'A dashboard is «a visual display of the most important information needed to achieve one or more objectives, consolidated on a single screen so it can be monitored at a glance» (Stephen Few) — and it should be designed for one specific target person, group, or goal, not everything at once.',
    mk: 'Designing one dashboard to serve multiple unrelated goals or audiences (e.g., monitoring sales, inventory, and HR vacations all on one screen) — a good dashboard is scoped to a single target and purpose.',
    src: SD_DASHBOARDS_SRC,
  },
  {
    m: ['dashboard design principles', 'declutter (dashboard)', 'show the context (dashboard)'],
    d: 'Good dashboard design follows principles like: «keep everything at a glance (no scrolling), declutter (remove visual effects unrelated to data), align elements, use color and chart types consistently, shorten large numbers (1,156,780 → 1.16M), show context (prior period, target, trend), and never use tables/matrices» — each rule exists to reduce the cognitive load of reading the dashboard.',
    ex: 'Showing this quarter\'s sales next to last year\'s figure and a target line gives the number context — a bare "$1.16M" on its own tells the viewer almost nothing.',
    mk: 'Defaulting to a red/green color scheme for bad/good performance — that pattern is indistinguishable for the most common forms of color blindness; a single highlight color for bad performance (with neutral grayscale elsewhere) is more universally readable.',
    src: SD_DASHBOARDS_SRC,
  },
  {
    m: ['visual hierarchy', 'storytelling with data', 'narrative structure (data storytelling)'],
    d: 'Visual hierarchy is «using size, position, and contrast to guide the viewer\'s eye to the most important information first and deliver a clear message» — paired with the narrative structure of storytelling (setup, conflict, resolution) borrowed from fiction, applied to data presentations to make insights memorable rather than just accurate.',
    mk: 'Building a visualization that is technically correct but has no visual hierarchy or message — without it, viewers can\'t tell what they\'re supposed to take away from the chart.',
    src: SD_DASHBOARDS_SRC,
  },
];