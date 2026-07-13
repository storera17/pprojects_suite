// Glossary entries for the "tools" deck. Each entry:
// { m: [matchers...], d: 'definition with «cloze phrases»', how, ex, we, mk, src: [{title,kind,ref}] }
// Grounded in backend/content-pipeline/extracted/... per backend/content-pipeline/taxonomy.mjs sourcePaths.
//
// sd-data-warehousing — Kimball's "The Data Warehouse Toolkit" (Ch. 1, 3, 5) and
// "The Data Warehouse ETL Toolkit" (backend/content-pipeline/extracted/lit-data-eng/).
const SD_DATA_WAREHOUSING_SRC = [
  { title: 'The Data Warehouse Toolkit, 3rd ed.', kind: 'textbook', ref: 'Ralph Kimball & Margy Ross (Ch. 1: "Data Warehousing, Business Intelligence, and Dimensional Modeling Primer"; Ch. 5: "Procurement")' },
  { title: 'The Data Warehouse ETL Toolkit', kind: 'textbook', ref: 'Ralph Kimball & Joe Caserta (Introduction)' },
];

// sd-modern-data-stack — "Snowflake: The Definitive Guide" (Ch. 2) and
// "Analytics Engineering with SQL and dbt" (Ch. 1-2)
const SD_MODERN_DATA_STACK_SRC = [
  { title: 'Snowflake: The Definitive Guide', kind: 'textbook', ref: 'Joyce Kay Avila (Ch. 2: "Creating and Managing the Snowflake Architecture")' },
  { title: 'Analytics Engineering with SQL and dbt', kind: 'textbook', ref: 'Rui Machado & Christophe Oudar (Ch. 1-2)' },
];

export const GLOSSARY_tools = [
  {
    m: ['star schema'],
    d: 'A star schema is a dimensional model implemented in a relational database — «a central fact table surrounded by dimension tables, resembling a star» — chosen over a fully normalized (3NF) model because it delivers user understandability and query performance instead of pure data-redundancy minimization.',
    how: 'Normalized 3NF models are great for transactional updates (touch the database in one place) but too complex for BI queries; dimensional/star models trade some redundancy for a schema business users can actually navigate.',
    src: SD_DATA_WAREHOUSING_SRC,
  },
  {
    m: ['fact table'],
    d: 'A fact table stores «the numeric performance measurements resulting from a business process event», with each row at a single, consistent level of detail called the grain, and foreign keys connecting to its dimension tables.',
    how: 'Every fact table row should be at the same grain (e.g., one row per sales transaction line) — mixing grains in one fact table risks double-counting measurements.',
    ex: 'A retail sales fact table\'s grain might be "one row per product sold in a single transaction," with columns for sales dollars and sales units plus foreign keys to date, product, and store dimensions.',
    mk: 'Filling a fact table with zero-rows for "no activity" — fact tables should stay sparse, recording only events that actually happened, or they balloon out of control.',
    src: SD_DATA_WAREHOUSING_SRC,
  },
  {
    m: ['dimension table'],
    d: 'A dimension table holds «the descriptive textual context for a fact table — the who, what, where, when, how, and why of a measurement event» — providing the labels, filters, and groupings used in every report.',
    ex: 'A product dimension table might have 50+ descriptive attributes (brand, category, department, package type) that all roll up to one product key referenced by the fact table.',
    mk: 'Burying meaningful operational codes inside the fact table or leaving them as cryptic codes — they belong as verbose, decoded attributes in the dimension table so reports stay readable.',
    src: SD_DATA_WAREHOUSING_SRC,
  },
  {
    m: ['slowly changing dimension', 'scd', 'scd type 1', 'scd type 2'],
    d: 'A slowly changing dimension (SCD) handles how a dimension attribute\'s value changes over time: «Type 1 simply overwrites the old value (losing history) while Type 2 adds an entirely new dimension row with effective/expiration dates (preserving full history)».',
    ex: 'If a product moves from the "Education" department to the "Strategy" department, a Type 1 response overwrites the department field on the existing row, while a Type 2 response inserts a new row for the product so old sales still report as "Education" and new sales report as "Strategy."',
    mk: 'Defaulting to Type 1 for every attribute change without considering whether the business actually needs historical accuracy — Type 1 silently rewrites history and is hard to walk back from later.',
    src: SD_DATA_WAREHOUSING_SRC,
  },
  {
    m: ['etl', 'extract transform load', 'extract, clean, conform, deliver'],
    d: 'ETL (extract, transform, load) is the system that «gets data out of source systems, cleans/conforms it, and loads it into the data warehouse» — adding real value along the way by removing mistakes, documenting confidence in the data, and structuring it for end-user tools, not just moving data from A to B.',
    how: 'A more actionable breakdown of the classic three ETL steps is extract, clean, conform, and deliver — explicitly separating data-quality cleanup and cross-source conforming from the final load step.',
    src: SD_DATA_WAREHOUSING_SRC,
  },

  // ---- sd-modern-data-stack ----
  {
    m: ['elt', 'extract load transform', 'etl vs elt'],
    d: 'ELT (extract, load, transform) is a newer alternative to ETL where «data is loaded into the target system first and transformed afterward, in place» — made practical by powerful cloud warehouses, and offering more flexibility and faster insight than transforming data before it ever lands.',
    mk: 'Assuming ELT skips data cleaning altogether because the load happens before transformation — without proper cleaning and standardization at some stage, data still ends up inaccurate or unusable regardless of whether you call it ETL or ELT.',
    src: SD_MODERN_DATA_STACK_SRC,
  },
  {
    m: ['snowflake architecture', 'separation of storage and compute'],
    d: 'Snowflake\'s architecture is built on «physically separating but logically integrating storage and compute» across three layers — cloud services, query processing (virtual warehouses), and data storage — so multiple compute clusters can query the same data concurrently without contending with each other.',
    ex: 'Two teams can run heavy, unrelated queries against the same underlying tables at the same time, each on its own virtual warehouse, with zero performance impact on the other.',
    src: SD_MODERN_DATA_STACK_SRC,
  },
  {
    m: ['virtual warehouse'],
    d: 'A Snowflake virtual warehouse is «a dynamic, independently scalable cluster of compute resources (CPU, memory, temporary storage)» used to execute queries and DML operations — it can be resized ("scale up") or have clusters added ("scale out") at any time, even while running.',
    how: 'Because Snowflake bills per second, it can be cheaper to run a larger warehouse and suspend it when idle than to run a small warehouse continuously — except when running many small, simple queries, where the extra capacity goes unused.',
    src: SD_MODERN_DATA_STACK_SRC,
  },
  {
    m: ['dbt', 'data building tool'],
    d: 'dbt (Data Building Tool) is an open-source command-line tool that handles «the transform step of an ELT workflow by letting analytics engineers write data transformations as version-controlled, testable, documented SQL» instead of complex custom ETL scripts.',
    ex: 'A dbt model that computes total revenue by summing order amounts is just a SQL SELECT statement saved as a model file — dbt handles dependency resolution (via ref()), materialization, testing, and documentation around it.',
    src: SD_MODERN_DATA_STACK_SRC,
  },
];