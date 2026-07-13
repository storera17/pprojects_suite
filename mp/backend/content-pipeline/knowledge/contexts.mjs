// Per-subdeck teaching context: domain framing, why-it-matters, a workplace
// scenario, common mistakes, and the evidence sources backing that subdeck.
// Keyed by subdeck id (see pipeline/taxonomy.mjs). Filled in during the
// authoring pass — each entry should be grounded in the subdeck's
// sourcePaths (pipeline/extracted/...) and, where relevant, a textbook.
//
// Shape per entry:
// {
//   domain: string,           // short label shown as a card tag
//   overview: string,         // 1-2 sentence framing of the subdeck
//   why: string,              // why this matters
//   workplace: string,        // a concrete workplace scenario
//   mistakes: string[],       // common mistakes/misconceptions
//   sources: Source[],        // { title, kind, ref }
// }

export const CONTEXTS = {
  'sd-ai-overview': {
    domain: 'analytics foundations',
    overview: 'The shared vocabulary that separates business analytics, business intelligence, data science, and the analytics maturity curve (descriptive → predictive → prescriptive).',
    why: 'These terms get used loosely in industry — knowing the precise distinctions lets you understand exactly what a colleague, job posting, or tool is actually claiming to do.',
    workplace: 'A new analyst joins a team and needs to follow standups without asking what every term means — knowing the difference between a BI dashboard and a predictive model changes what questions are even answerable.',
    mistakes: [
      'Using "business intelligence," "business analytics," and "data science" interchangeably when they describe different scopes of work.',
      'Calling any historical report "predictive" just because it includes a chart that trends upward.',
    ],
    sources: [
      { title: 'ISA 591: Data Mining — Background Vocabulary (pre-term review)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 0)' },
    ],
  },
  'sd-bigdata-overview': {
    domain: 'big data foundations',
    overview: 'Why big data became a thing now (cheap storage, abundant collection), what makes data "big" beyond sheer size, and the technology stack (Hadoop, Spark, cloud) built to manage it.',
    why: 'Before learning any specific big-data tool, you need the framing for why traditional single-machine tools (a spreadsheet, a single SQL server) stop working — that\'s what motivates the whole rest of the big-data toolchain.',
    workplace: 'A retail analytics team realizes their nightly batch reports can no longer keep up with point-of-sale data streaming in from hundreds of stores in real time — a textbook Volume + Velocity problem that pushes them toward distributed, streaming infrastructure.',
    mistakes: [
      'Equating "big data" with just "a lot of data" — Variety (unstructured formats) and Velocity (speed of arrival) are just as defining as Volume.',
      'Assuming a single powerful server can substitute for distributed storage and parallel processing once data volume and velocity cross a certain threshold.',
    ],
    sources: [
      { title: 'ISA 514: Managing Big Data — Big Data Overview lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1, Dr. Jay Shan)' },
    ],
  },
  'sd-complexity': {
    domain: 'algorithm complexity',
    overview: 'How we measure the inherent difficulty of a computational problem and judge whether an algorithm solves it efficiently.',
    why: 'Before building an optimization model, you need to know whether an exact optimal solution is even reachable in practical time — complexity analysis is what tells you that, and steers you toward exact methods, heuristics, or approximations.',
    workplace: 'A supply-chain analyst is asked to find the truly optimal routing for 200 delivery trucks. Recognizing this as an NP-hard combinatorial problem, she chooses a heuristic that returns a good solution in minutes instead of an exact algorithm that would not finish before the delivery window closes.',
    mistakes: [
      'Treating "the algorithm finished quickly on my test case" as proof of good worst-case performance — small inputs hide exponential blowup.',
      'Assuming polynomial-time always means "fast in practice" — a high-degree polynomial like O(n^10) can still be unusable at real-world scale.',
    ],
    sources: [
      { title: 'ISA 634: Systems Modeling & Optimization — Complexity & Algorithm Analysis lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Day 1 handout, 8/26/25)' },
    ],
  },
  'sd-opt-intro': {
    domain: 'prescriptive analytics',
    overview: 'How operations research / management science frames a decision problem so it can be solved with optimization techniques.',
    why: 'Before you can write any model, you need to translate a real business decision into decisions, constraints, and an objective function — get that framing wrong and the "optimal" answer the solver gives you is optimal for the wrong problem.',
    workplace: 'A hospital administrator wants to "optimize" the nurse schedule. Before any math happens, she has to decide: what exactly is being chosen (shift assignments), what limits apply (labor law, nurse availability), and what is actually being maximized or minimized (coverage? cost? fairness?).',
    mistakes: [
      'Jumping straight to a solver without first naming the decisions, constraints, and objective function in words.',
      'Treating "descriptive", "predictive", and "prescriptive" analytics as the same thing — they answer different questions (what happened, what will happen, what should we do).',
    ],
    sources: [
      { title: 'ISA 634: Systems Modeling & Optimization — Introduction to Modeling lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 0, Day 1)' },
    ],
  },
  'sd-math-programming': {
    domain: 'mathematical programming',
    overview: 'The general structure of an optimization model and the three practical ways to solve one.',
    why: 'Knowing whether a model can be enumerated, solved graphically, or needs a software solver tells you immediately whether a problem is tractable by hand or needs Excel/Gurobi/CPLEX.',
    workplace: 'An operations analyst is handed a two-variable production-mix problem and a 500-variable supply-chain problem on the same day — she solves the first graphically in five minutes and recognizes the second needs a solver.',
    mistakes: [
      'Trying to enumerate all solutions for a problem with continuous decision variables — enumeration only works for integer/discrete problems.',
      'Forgetting that strict inequality constraints ("<" or ">") can make a model fail to have a well-defined optimum.',
    ],
    sources: [
      { title: 'ISA 634: Systems Modeling & Optimization — Introduction to Mathematical Programming lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 01, Day 2)' },
    ],
  },
  'sd-lp': {
    domain: 'linear programming',
    overview: 'The mathematical structure of a linear program and the assumptions (proportionality, additivity) that make it linear.',
    why: 'LP is the workhorse of prescriptive analytics — recognizing whether a real problem actually satisfies LP\'s linearity assumptions tells you whether a fast, reliable solver applies or whether you need a more complex nonlinear model.',
    workplace: 'A bakery wants to set a low-cost ingredient mix that still meets nutrition requirements — formulated correctly, this becomes a small LP (the classic "diet problem") solvable in seconds with a solver.',
    mistakes: [
      'Assuming a real cost or benefit is proportional to quantity when it actually has volume discounts or diminishing returns.',
      'Forgetting that LP decision variables are continuous — if the real decision must be a whole number, you need integer programming instead.',
    ],
    sources: [
      { title: 'ISA 634: Systems Modeling & Optimization — Introduction to Linear Programming lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 02)' },
    ],
  },
  'sd-transportation-assignment': {
    domain: 'network flow',
    overview: 'Two classic LP special cases: shipping goods from supply points to demand points (transportation), and matching agents to tasks one-to-one (assignment).',
    why: 'Both problems show up constantly in logistics and operations, and — unlike general LPs — their optimal solutions come out integral automatically, which is a useful guarantee to recognize.',
    workplace: 'A manufacturer with two plants and three customer cities needs the cheapest shipping plan that meets every city\'s demand without exceeding either plant\'s supply — a direct transportation problem.',
    mistakes: [
      'Treating the assignment problem as needing only one set of constraints — it needs both "each machine used once" and "each task covered once" to force a valid one-to-one match.',
      'Forgetting the transportation problem\'s integrality guarantee depends on integral supply, demand, and sufficient total supply to meet demand.',
    ],
    sources: [
      { title: 'ISA 634: Systems Modeling & Optimization — Transportation & Assignment Problems lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 05)' },
    ],
  },
  'sd-network-flow': {
    domain: 'network flow',
    overview: 'How nodes and arcs model the movement of goods, information, or resources through a network, and the three classic network flow problems.',
    why: 'Recognizing a problem as a network flow problem (rather than a generic LP) means specialized, much faster solution algorithms apply.',
    workplace: 'A telecom company modeling how data packets move through routers, or a logistics firm modeling trucks moving goods between warehouses, are both using network flow models under the hood.',
    mistakes: [
      'Forgetting that the supply/demand values across all nodes in a network flow model must sum to zero for a feasible solution to exist.',
      'Confusing the goal of minimum cost flow problems (minimize shipping cost) with maximum flow problems (maximize volume from source to sink) — they optimize different things.',
    ],
    sources: [
      { title: 'ISA 634: Systems Modeling & Optimization — Network Flow Problems lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 06)' },
    ],
  },
  'sd-ip': {
    domain: 'integer programming',
    overview: 'Optimization models where some or all decisions must take whole-number (or yes/no) values, and why that makes them fundamentally harder than LPs.',
    why: 'Many real decisions are inherently discrete — open a facility or not, hire this candidate or not — and treating them as continuous and rounding the answer can give a solution that isn\'t even feasible.',
    workplace: 'A company deciding which of 20 candidate warehouse sites to open, subject to a budget, models each site as a binary 0/1 decision variable — a facility-location integer program.',
    mistakes: [
      'Solving the LP relaxation and simply rounding to the nearest integer, then assuming that\'s the optimal integer solution — it often isn\'t, and may even violate a constraint.',
      'Underestimating how much harder IP/MIP is to solve than LP — running time tends to grow exponentially with the number of integer variables.',
    ],
    sources: [
      { title: 'ISA 634: Systems Modeling & Optimization — Introduction to Integer Programming lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 07/08)' },
    ],
  },
  'sd-eda': {
    domain: 'exploratory data analysis',
    overview: 'Investigating a dataset — encoding, missing values, outliers, and skewness — to get it ready for modeling.',
    why: 'Most predictive-modeling failures trace back to data problems caught (or missed) at this stage — a model is only as good as the data prep that fed it.',
    workplace: 'A nonprofit\'s analytics team explores a donor database before building a response model: they find a 6-level status column that needs dummy coding, three variables with 10%+ missingness, and a heavily skewed donation-amount field.',
    mistakes: [
      'Dropping every row with a missing value instead of imputing or flagging it — with enough variables, this can silently discard most of the dataset.',
      'Keeping all K dummy columns for a K-category variable instead of K−1, creating multicollinearity.',
    ],
    sources: [
      { title: 'ISA 591: Data Mining — Exploratory Data Analysis lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2, Day 1 & 2 notes)' },
    ],
  },
  'sd-data-mining-intro': {
    domain: 'data mining',
    overview: 'The core task types in data mining (classification, prediction, association rules, dimension reduction) and the end-to-end process for building a model.',
    why: 'Knowing which task type a business question maps to (predict a category? a number? find co-occurring items?) determines which family of algorithms is even relevant.',
    workplace: 'A subscription company wants to "reduce churn" — translating that into a concrete data-mining task (classification: will this customer churn, yes/no?) is the first real step, before any algorithm gets chosen.',
    mistakes: [
      'Picking an algorithm before clearly defining whether the target variable is categorical (classification) or numeric (prediction).',
      'Evaluating a model only on the data used to train it instead of a held-out test set.',
    ],
    sources: [
      { title: 'ISA 591: Data Mining — Data Mining Overview lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1, Day 1 notes)' },
    ],
  },
  'sd-dimension-reduction': {
    domain: 'dimension reduction',
    overview: 'Why too many variables hurts models (the curse of dimensionality), the leakage traps to avoid, and PCA as the main quantitative reduction technique.',
    why: 'High-dimensional, leaky, or redundant data quietly inflates a model\'s apparent performance during development and then disappoints in production — catching this early saves a failed deployment.',
    workplace: 'A credit-risk team finds their model performs suspiciously well in testing; on inspection, one predictor (a "final account status" field) was only ever populated after a loan had already defaulted — classic target leakage.',
    mistakes: [
      'Standardizing or imputing using statistics computed from the full dataset (including the test set) before splitting train/test.',
      'Running PCA on categorical or uncorrelated continuous variables, where it provides no real reduction benefit.',
    ],
    sources: [
      { title: 'ISA 591: Data Mining — Dimension Reduction lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3, Day 1 & 2 notes)' },
    ],
  },
  'sd-model-evaluation': {
    domain: 'model evaluation',
    overview: 'How to honestly measure a predictive model\'s performance on continuous targets — accuracy metrics, naive benchmarks, and ranking-quality tools like gain and lift.',
    why: 'A model that looks great on training data can still be worthless in production — every one of these metrics exists to separate genuine predictive skill from overfitting.',
    workplace: 'A used-car dealership builds a price-prediction model and uses a cumulative gains chart to decide which cars in inventory to prioritize selling first, based on which are most underpriced relative to predicted value.',
    mistakes: [
      'Reporting R² or RMSE computed on the training data as if it measures real-world predictive performance — it must be computed on a holdout sample.',
      'Confusing lift (per-decile ratio to average) with cumulative gain (running total share captured) — they\'re related but not the same chart.',
    ],
    sources: [
      { title: 'ISA 591: Data Mining — Evaluating Model Performance lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 4, Day 1 notes)' },
    ],
  },
  'sd-regularized-regression': {
    domain: 'regularized regression',
    overview: 'How to choose which predictors belong in a regression model — stepwise selection, and the more flexible shrinkage approach of ridge/lasso regularization — validated honestly via cross-validation.',
    why: 'Including too many or too few predictors both hurt a model in different ways; regularization gives a principled, tunable way to navigate that bias-variance tradeoff instead of guessing.',
    workplace: 'A real-estate analytics team has 60 candidate predictors for a home-price model; lasso regression automatically shrinks the least useful ones to zero, leaving a simpler, more generalizable model.',
    mistakes: [
      'Treating ridge and lasso as interchangeable — only lasso\'s L1 penalty can zero out coefficients and perform variable selection; ridge only shrinks them.',
      'Picking the regularization tuning parameter λ by eye instead of via cross-validation.',
    ],
    sources: [
      { title: 'ISA 591: Data Mining — Regularized Regression lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 5 notes)' },
    ],
  },
  'sd-tree-models': {
    domain: 'tree-based models',
    overview: 'How decision trees split data via impurity measures, why they overfit easily, and how pruning and variable importance help manage that.',
    why: 'Trees are one of the most interpretable model families available, but their tendency to overfit makes pruning and holdout evaluation essential rather than optional.',
    workplace: 'A bank builds a decision tree to predict which customers will accept a personal loan offer, then prunes it using cross-validation and checks variable importance to confirm Income and Education are the strongest drivers.',
    mistakes: [
      'Evaluating a decision tree\'s quality only on training-data fit — that hides overfitting, which trees are especially prone to.',
      'Treating a single tree\'s structure as stable — small changes in the training sample can produce a meaningfully different tree.',
    ],
    sources: [
      { title: 'ISA 591: Data Mining — Tree-Based Models lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 6, Day 1 & 2 notes)' },
    ],
  },
  'sd-logistic-regression': {
    domain: 'logistic regression',
    overview: 'How logistic regression models a binary outcome as a probability via the logistic function, and how to interpret its coefficients through odds ratios rather than additive effects.',
    why: 'Ordinary linear regression breaks down on a 0/1 target — logistic regression is the standard fix, but its odds-based coefficient interpretation trips up almost everyone the first time they see it.',
    workplace: 'A bank fits a logistic regression to predict loan default (yes/no) from income and credit score, then explains to a loan officer that each $1,000 increase in income multiplies the odds of repayment by a specific factor.',
    mistakes: [
      'Fitting ordinary linear regression to a binary 0/1 outcome instead of logistic regression.',
      'Interpreting a logistic regression coefficient as a direct change in probability rather than a multiplicative change in odds.',
    ],
    sources: [
      { title: 'ISA 591: Data Mining — Logistic Regression lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 7, Day 1 notes)' },
    ],
  },
  'sd-text-mining': {
    domain: 'text mining',
    overview: 'How to turn unstructured text into a structured, model-ready dataset — sentiment scoring, the document-term matrix, and TF-IDF weighting — plus the cleaning steps that make it work well.',
    why: 'Most business data isn\'t tabular — reviews, emails, support tickets, articles — and these are the standard techniques for unlocking predictive value from that text.',
    workplace: 'A SPAM filter team converts raw email text into a document-term matrix weighted by TF-IDF, so that classification models can flag emails with rare, telling words like "consignment" or "Viagra" without being fooled by common filler words like "the."',
    mistakes: [
      'Using raw term frequency alone to judge a word\'s importance — common words can have high frequency but zero discriminating power; that\'s what IDF corrects for.',
      'Skipping text cleaning (stopword removal, stemming) before building a document-term matrix, which inflates the variable count with low-information noise.',
    ],
    sources: [
      { title: 'ISA 514: Managing Big Data — Text Mining lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 7 slides, Dr. Jay Shan)' },
    ],
  },
  'sd-data-warehousing': {
    domain: 'data warehousing & ETL',
    overview: 'How Kimball-style dimensional modeling (star schemas, fact/dimension tables, slowly changing dimensions) structures data for analytics, and how an ETL system extracts, cleans, and loads it.',
    why: 'Almost every BI dashboard and analytics model ultimately reads from a dimensionally modeled warehouse — understanding fact/dimension design and SCDs explains why warehouse data looks the way it does and why historical reports can change.',
    workplace: 'An analytics engineer designs a retail sales fact table at "one row per transaction line" grain, joined to date/product/store dimension tables, and chooses a Type 2 SCD for the product dimension so departmental reassignments don\'t silently rewrite sales history.',
    mistakes: [
      'Defaulting to a Type 1 (overwrite) slowly changing dimension without checking whether the business actually needs to preserve history — Type 1 silently rewrites the past.',
      'Mixing two different levels of detail (grains) in one fact table, which risks double-counting measurements.',
    ],
    sources: [
      { title: 'The Data Warehouse Toolkit, 3rd ed.', kind: 'textbook', ref: 'Ralph Kimball & Margy Ross (Ch. 1, 5)' },
      { title: 'The Data Warehouse ETL Toolkit', kind: 'textbook', ref: 'Ralph Kimball & Joe Caserta (Introduction)' },
    ],
  },
  'sd-modern-data-stack': {
    domain: 'modern data stack',
    overview: 'How cloud data warehouses like Snowflake separate storage from compute, and how dbt brings software-engineering discipline (version control, tests, docs) to the SQL transformation step of an ELT pipeline.',
    why: 'The classic ETL/on-prem warehouse model is being replaced by ELT-plus-cloud-warehouse stacks — recognizing the new vocabulary (virtual warehouse, dbt model) is table stakes for working with any modern analytics team.',
    workplace: 'An analytics engineering team loads raw data into Snowflake first (the "L" in ELT), then uses dbt models to transform it into clean, tested, documented tables — all version-controlled in git alongside the rest of the codebase.',
    mistakes: [
      'Assuming ELT means data cleaning becomes optional — it just happens after loading instead of before; bad data is still bad data.',
      'Running one large, always-on Snowflake virtual warehouse for every workload instead of right-sizing and suspending warehouses when idle.',
    ],
    sources: [
      { title: 'Snowflake: The Definitive Guide', kind: 'textbook', ref: 'Joyce Kay Avila (Ch. 2)' },
      { title: 'Analytics Engineering with SQL and dbt', kind: 'textbook', ref: 'Rui Machado & Christophe Oudar (Ch. 1-2)' },
    ],
  },
  'sd-dax': {
    domain: 'DAX & data preparation',
    overview: 'How DAX evaluation contexts (filter and row context) determine what a formula actually computes, plus the core table functions (FILTER, ALL, VALUES, RELATEDTABLE) built around them.',
    why: 'Evaluation context is the single hardest DAX concept to internalize and the single most common source of "why is my measure showing the wrong number" bugs — every other DAX skill builds on top of it.',
    workplace: 'A BI developer\'s measure works perfectly as a calculated column but throws a "single value cannot be determined" error as a measure — recognizing this as a missing row context (not a syntax bug) is the difference between a five-minute fix and an hour of confused debugging.',
    mistakes: [
      'Treating a calculated column and a measure as interchangeable — measures lack the automatic row context that columns get for free.',
      'Setting relationships to bi-directional filtering by default — it can introduce model ambiguity and performance problems for a convenience that\'s rarely needed.',
    ],
    sources: [
      { title: 'ISA 512: Data Preparation using DAX Query Language', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.3-1.4)' },
    ],
  },
  'sd-powerbi-modeling': {
    domain: 'Power BI data modeling',
    overview: 'How to keep a Power BI model unambiguous (denormalization, role dimensions), how to handle facts that can\'t simply be summed, and the three ways to segment data depending on how often the segment changes.',
    why: 'A technically working DAX formula can still return the wrong number if the underlying model is ambiguous or the fact isn\'t additive in the way you assumed — modeling discipline prevents silent wrong-answer bugs.',
    workplace: 'A finance team builds an account-balance dashboard and discovers SUM() gives a nonsensical monthly total — switching to LASTDATE to report the balance as of period-end fixes the semi-additive fact correctly.',
    mistakes: [
      'Applying SUM to every numeric fact column without checking whether it\'s additive, semi-additive, or non-additive.',
      'Letting a data lake grow without governance until it becomes an unusable data swamp.',
    ],
    sources: [
      { title: 'ISA 512: Data Modeling using Power BI', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2.1, 2.2, 2.5, 2.7)' },
    ],
  },
  'sd-dashboards': {
    domain: 'data visualization & dashboards',
    overview: 'How to match data types to visual attributes (data encoding), the concrete design rules that make a dashboard readable at a glance, and the storytelling structure that turns a chart into a memorable insight.',
    why: 'A technically correct dashboard can still fail at its actual job — communicating — if it ignores how the human visual system perceives color, position, and hierarchy.',
    workplace: 'An analyst redesigns a cluttered sales dashboard: removing matrix tables in favor of bar charts, shortening "$1,156,780" to "$1.16M," adding a prior-year comparison for context, and switching from red/green to a single highlight color so colorblind viewers can read it too.',
    mistakes: [
      'Using red/green to signal bad/good performance — a large share of viewers with red-green color blindness can\'t reliably distinguish them.',
      'Designing one dashboard to serve several unrelated audiences or goals instead of scoping it to a single target and purpose.',
    ],
    sources: [
      { title: 'ISA 512: Data Visualization, Dashboards, and Storytelling', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3.1-3.3)' },
    ],
  },
  'sd-python': {
    domain: 'Python for data analysis',
    overview: 'Python\'s core data structures (lists, dictionaries, tuples), the CRISP-DM process that frames any data mining project, and the NumPy/Pandas libraries that do the heavy lifting of numerical and tabular data wrangling.',
    why: 'Almost every later module in this curriculum — text mining, machine learning, big data platforms — assumes fluency with Pandas DataFrames and an intuition for why data preparation dominates real project timelines.',
    workplace: 'An analyst pulls flight-delay data from a MySQL database and immediately re-expresses the SQL query as Pandas operations (groupby, filtering, sorting) to keep exploring the data interactively in a notebook instead of writing new SQL for every question.',
    mistakes: [
      'Treating CRISP-DM as a strict one-pass pipeline instead of the iterative, repetitive process it actually is in practice.',
      'Trying to mutate a tuple in place — tuples are immutable; that\'s what makes them efficient and safe for use as fixed keys or temporary unpacking targets.',
    ],
    sources: [
      { title: 'ISA 514: Managing Big Data — Python Programming I & II', kind: 'course', ref: 'Miami University, Farmer School of Business (Modules 2-3)' },
    ],
  },
  'sd-web-api': {
    domain: 'web APIs',
    overview: 'How REST APIs use HTTP methods and URLs to request data, how API authorization works, and how JSON/XML structure the data that comes back.',
    why: 'External data sources almost never hand you a clean CSV — they hand you a REST endpoint, an API key requirement, and a nested JSON response you need to parse, so this is the practical skill behind "collecting data from the web."',
    workplace: 'A social-media monitoring analyst writes a Python script that GETs the NY Times API with a query parameter for "Microsoft," authenticates with an API key, and parses the nested JSON response down to just the article snippets and URLs.',
    mistakes: [
      'Forgetting that most Web APIs require an API key/token for authorization — a request without one typically fails outright, not partially.',
      'Trying to read a deeply nested JSON response without first thinking of it as a hierarchical tree of objects and arrays.',
    ],
    sources: [
      { title: 'ISA 514: Managing Big Data — Data Collection from Web API', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 4)' },
    ],
  },
  'sd-nosql': {
    domain: 'NoSQL databases',
    overview: 'Why non-relational data stores exist alongside RDBMSs, the four main kinds of NoSQL database, and how MongoDB\'s document model maps onto familiar relational vocabulary.',
    why: 'Big-data systems routinely need to store unstructured or rapidly evolving data at a scale and flexibility that a fixed relational schema struggles with — recognizing when NoSQL fits (and which kind) is a core big-data-management skill.',
    workplace: 'A team storing rapidly evolving, semi-structured customer-support ticket data chooses MongoDB over a relational database specifically because different tickets need different fields and a fixed schema would require constant migrations.',
    mistakes: [
      'Treating NoSQL as a single thing — key-value, graph, document, and column-family stores solve different problems and aren\'t interchangeable.',
      'Assuming NoSQL databases enforce a fixed schema the way RDBMS tables do — MongoDB documents in the same collection can have different fields entirely.',
    ],
    sources: [
      { title: 'ISA 514: Managing Big Data — NoSQL Database (MongoDB Basics)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 5)' },
    ],
  },
  'sd-bigdata-systems': {
    domain: 'big data systems',
    overview: 'How Hadoop\'s HDFS splits and replicates data across a cluster, and how MapReduce turns that distributed storage into distributed computation via Map, Shuffle-and-Sort, and Reduce.',
    why: 'Spark and every modern big-data platform are direct responses to Hadoop\'s strengths and limitations — understanding HDFS and MapReduce first is what makes "why Spark is faster" actually click later.',
    workplace: 'A data engineering team builds a nightly job that counts word frequency across millions of log files spread across a cluster — the Map step counts words independently per block, and the Reduce step sums those partial counts into a final total, exactly like the classic chopped-vegetable cooking analogy.',
    mistakes: [
      'Assuming the Name Node is replicated and protected the same way ordinary HDFS data blocks are — it\'s a special, less-redundant case.',
      'Writing a Map function whose result depends on another node\'s computation — Map tasks must be fully independent for the distributed model to work.',
    ],
    sources: [
      { title: 'ISA 514: Managing Big Data — Big Data Systems (From Hadoop to Spark)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 8)' },
    ],
  },
  'sd-spark': {
    domain: 'Apache Spark',
    overview: 'Why Spark is faster and more flexible than classic MapReduce (in-memory caching, no explicit map/reduce coding), and how its core abstractions (RDD, DataFrame) let you write Pandas/SQL-like code that runs across a cluster.',
    why: 'Spark is the dominant big-data processing engine in industry today — its DataFrame API is deliberately designed to feel like Pandas and SQL so the skills from earlier modules transfer directly.',
    workplace: 'A data engineering team migrates a slow, disk-bound MapReduce job to Spark and sees a 10-50x speedup just from in-memory caching, without changing the underlying business logic.',
    mistakes: [
      'Trying to modify a Spark DataFrame in place — like Pandas DataFrames, they\'re immutable; every transformation returns a new one.',
      'Assuming Spark always requires explicitly written map/reduce functions the way classic MapReduce does — Spark\'s DataFrame API handles that under the hood.',
    ],
    sources: [
      { title: 'ISA 632: Big Data Analytics & Modern AI — Apache Spark', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
    ],
  },
  'sd-distributed-computing': {
    domain: 'distributed computing on Spark',
    overview: 'How Spark splits DataFrame work into transformations (parallel, lazy) and actions (which trigger execution and return results to the driver), and why that lazy model lets Spark optimize whole chains of operations at once.',
    why: 'Counterintuitive performance bugs in Spark almost always trace back to misunderstanding lazy evaluation or calling an action (like collect()) that pulls too much data back to the driver.',
    workplace: 'A data engineer chains five transformations together expecting each one to run immediately, then is confused when nothing happens until they finally call .show() — recognizing Spark\'s lazy execution model explains exactly why.',
    mistakes: [
      'Calling collect() on a very large DataFrame without considering that it pulls all rows back into the driver\'s memory.',
      'Expecting each transformation in a chain to execute immediately, the way ordinary line-by-line code does — Spark defers all of it until an action is called.',
    ],
    sources: [
      { title: 'ISA 632: Big Data Analytics & Modern AI — Apache Spark (DataFrame Operations & Lazy Execution)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2, slides 24-28)' },
    ],
  },
  'sd-ml-at-scale': {
    domain: 'machine learning at scale',
    overview: 'How Spark MLlib scales standard ML algorithms across a cluster, how hyperparameter tuning (grid search, Hyperopt) works at scale, and how MLOps/MLflow track and operationalize the resulting experiments.',
    why: '"More data beats a better algorithm" only pays off if your tooling can actually train and tune models at that scale — MLlib, Hyperopt, and MLflow are the practical answer to that constraint.',
    workplace: 'A data science team running hundreds of hyperparameter combinations for a churn model uses MLflow Tracking to log every run\'s parameters and RMSE, so weeks later they can instantly identify which configuration actually won.',
    mistakes: [
      'Trying to combine distributed model training with distributed hyperparameter tuning at the same time — the two approaches don\'t mix well together.',
      'Cranking CrossValidator parallelism arbitrarily high without checking it against actual cluster resources — beyond a point, it stops helping.',
    ],
    sources: [
      { title: 'ISA 632: Big Data Analytics & Modern AI — Machine Learning at Scale', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 5)' },
    ],
  },
  'sd-recommender-systems': {
    domain: 'recommender systems',
    overview: 'The two fundamental recommendation strategies — content-based filtering (using item attributes) and collaborative filtering (using similar users\' behavior) — plus the practical challenges (cold start, feedback type) that shape real systems.',
    why: 'Recommenders drive a huge share of online engagement and revenue (Netflix: 80% of watched content is recommended; Amazon: ~35% of revenue) — and the cold-start problem in particular shapes how any new product or feature actually has to launch.',
    workplace: 'A startup launching a new streaming app has zero user history, so it starts with content-based recommendations (genre, actor, director matching) and gradually shifts to collaborative filtering as enough viewing data accumulates — exactly the cold-start workaround taught in this module.',
    mistakes: [
      'Launching with pure collaborative filtering when there\'s no interaction data yet — that\'s the cold start problem; content-based filtering is the practical starting point.',
      'Treating implicit feedback (e.g., a user watched a movie) as a reliable positive signal — it\'s inherently noisy and only an indirect guess at true preference.',
    ],
    sources: [
      { title: 'ISA 632: Big Data Analytics & Modern AI — Recommender Systems and ALS', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 6)' },
      { title: 'Dive Into Deep Learning — Recommender Systems', kind: 'textbook', ref: 'Zhang, Lipton, Li & Smola' },
    ],
  },
  'sd-nn-intro': {
    domain: 'neural networks introduction',
    overview: 'How a neural network turns weighted sums and activation functions into a flexible, non-linear predictive model, and how backpropagation + gradient descent actually learn the weights from data.',
    why: 'Every deep learning architecture in later subdecks (CNNs, RNNs, autoencoders) is built from these same basic pieces — activation functions, loss, backpropagation — so getting this foundation solid pays off across the whole deck.',
    workplace: 'A data scientist fitting a neural network with caret\'s nnet package realizes the model "just works" because train() automatically runs forward passes, computes gradients via backpropagation, and updates weights via gradient descent under the hood.',
    mistakes: [
      'Conflating backpropagation (computing gradients via the chain rule) with gradient descent (using those gradients to update weights) — they\'re two distinct, sequential steps.',
      'Forgetting that without an activation function, a multi-layer network collapses to an ordinary linear model no matter how many layers it has.',
    ],
    sources: [
      { title: 'ISA 591: Data Mining — Neural Networks lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 8, Day 1 notes)' },
    ],
  },
  'sd-matrix-tensor': {
    domain: 'matrix & tensor algebra',
    overview: 'The linear algebra vocabulary (vectors, dot products, norms, matrix operations, tensors) that every deep learning framework and formula is built on.',
    why: 'Every neural network operation — a weighted sum, a regularization penalty, a batch of images — is literally a vector/matrix/tensor operation under the hood; without this vocabulary, the math in later deep learning subdecks is opaque notation instead of operations you can reason about.',
    workplace: 'A data scientist debugging a "shapes don\'t match" error in a neural network traces it back to a matrix multiplication where the inner dimensions didn\'t line up — recognizing the conformability rule turns a cryptic stack trace into an obvious fix.',
    mistakes: [
      'Confusing the L1 norm (can zero out weights entirely) with the L2 norm (shrinks weights close to zero but rarely all the way) when reasoning about regularization.',
      'Attempting matrix multiplication without verifying the inner dimensions match (first matrix\'s columns = second matrix\'s rows).',
    ],
    sources: [
      { title: 'ISA 630: Deep Learning — Matrix/Tensor Algebra lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 0)' },
    ],
  },
  'sd-gradients-regularization': {
    domain: 'gradients & regularization',
    overview: 'The precise distinction between loss and cost functions, why convexity matters for optimization, how gradient descent actually updates parameters step by step, and how ridge regression\'s L2 penalty regularizes a model.',
    why: 'Every model-training process in this curriculum — from logistic regression to deep neural networks — is "minimize a cost function via some form of gradient descent," so this vocabulary underlies essentially everything that comes after it.',
    workplace: 'A data scientist tuning a ridge regression model uses cross-validation to choose λ rather than guessing, because too small a value gives no real regularization benefit and too large a value makes the model underfit.',
    mistakes: [
      'Treating "loss function" and "cost function" as synonyms — loss is the error on a single instance; cost aggregates loss across the whole dataset.',
      'Confusing metrics (used to monitor training progress) with the cost function the algorithm is actually minimizing internally — they aren\'t always the same thing.',
    ],
    sources: [
      { title: 'ISA 630: Deep Learning — Loss Functions, Gradients & Regularization lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1)' },
    ],
  },
  'sd-classification-deep-dive': {
    domain: 'classification deep dive',
    overview: 'The three classification problem types — binary, multi-class, and multi-label — and the loss function each one actually requires (binary cross-entropy, categorical cross-entropy, and per-label binary relevance).',
    why: 'Picking the wrong classification framing (e.g., treating a multi-label problem as multi-class) leads to a model architecture and loss function that structurally can\'t represent the real problem, no matter how well it\'s tuned.',
    workplace: 'A content-tagging team realizes their "categorize this article" task is actually multi-label (an article can be both "politics" and "economy" at once), not multi-class, and switches from categorical cross-entropy to a Binary Relevance setup with one classifier per tag.',
    mistakes: [
      'Treating a multi-label problem (an instance can have several labels at once) as multi-class (an instance has exactly one label) — they need different loss functions and output structures.',
      'Forgetting that one-hot encoding is how multi-class labels are typically represented for categorical cross-entropy.',
    ],
    sources: [
      { title: 'ISA 630: Deep Learning — Classification Deep Dive (Binary, Multi-Class, Multi-Label)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
    ],
  },
  'sd-feedforward': {
    domain: 'feed-forward architectures',
    overview: 'How a single perceptron generalizes into a Multi-Layer Perceptron, which activation function fits which layer/response type, and how the forward pass produces a prediction before backpropagation kicks in.',
    why: 'A feed-forward network is the simplest deep learning architecture and the direct foundation for every more specialized architecture (CNNs, RNNs, autoencoders) covered later in this deck.',
    workplace: 'A developer building a digit-classification network picks ReLU for the hidden layers and softmax for the output layer — matching the activation choice to "hidden layer" and "multi-class response" respectively, rather than guessing.',
    mistakes: [
      'Using softmax anywhere other than a multi-class output layer — it\'s not a general-purpose hidden-layer activation.',
      'Ignoring the total parameter count of a network relative to dataset size — that ratio is a useful early warning sign for overfitting risk.',
    ],
    sources: [
      { title: 'ISA 630: Deep Learning — Feed-Forward Architectures lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3)' },
    ],
  },
  'sd-autoencoders': {
    domain: 'autoencoders',
    overview: 'How an autoencoder\'s encoder/decoder structure and latent-space bottleneck enable dimensionality reduction, denoising, and anomaly detection — plus the three main variants (undercomplete, sparse, denoising).',
    why: 'Autoencoders are the conceptual bridge between basic feed-forward networks and more specialized unsupervised deep learning — and their reconstruction-error trick for anomaly detection is genuinely used in production fraud/defect detection systems.',
    workplace: 'A manufacturing QA team trains an autoencoder only on images of non-defective parts; at inference time, a part image that reconstructs poorly (high reconstruction error) gets flagged as a likely defect — no labeled defect examples needed.',
    mistakes: [
      'Confusing a sparse autoencoder (penalty added to push activations toward zero) with an undercomplete one (just relies on a smaller bottleneck dimension) — both reduce information flow, but via different mechanisms.',
      'Forgetting that PCA only captures linear structure — autoencoders can outperform it specifically on large or non-linear datasets.',
    ],
    sources: [
      { title: 'ISA 630: Deep Learning — AutoEncoders lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 4)' },
    ],
  },
  'sd-cnn': {
    domain: 'convolutional neural networks',
    overview: 'Why ordinary feed-forward networks struggle with images, and how convolutions, pooling, padding, and stride together let a CNN learn spatial features efficiently instead of flattening everything into one giant vector.',
    why: 'CNNs are the dominant architecture for image-related tasks precisely because they preserve spatial structure that a flattened feed-forward network throws away — understanding convolution/pooling/padding/stride is the prerequisite for reading any CNN architecture diagram.',
    workplace: 'An engineer debugging a CNN that\'s shrinking the image too aggressively after several layers realizes the network has no padding — adding padding=1 keeps the spatial dimensions stable across layers instead of collapsing them.',
    mistakes: [
      'Flattening an image directly into a feed-forward network instead of using convolutional layers — this discards translation invariance and creates an unmanageable number of parameters.',
      'Reasoning about stride or padding in isolation — the two jointly determine a convolutional layer\'s output size and need to be considered together.',
    ],
    sources: [
      { title: 'ISA 630: Deep Learning — Convolutional Neural Networks lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 5)' },
    ],
  },
  'sd-rnn': {
    domain: 'recurrent neural networks',
    overview: 'How RNNs process sequences via a feedback loop, why plain RNNs forget long-range context (vanishing gradient), and how LSTMs/GRUs and attention mechanisms address that with gating and learned focus.',
    why: 'Sequence data — time series, text, sensor streams — is everywhere in business analytics, and the progression from plain RNN → LSTM/GRU → attention is exactly the progression of fixes to the same core weakness: forgetting long-range context.',
    workplace: 'A demand-forecasting team adds an attention layer to their sales model and discovers it automatically learns to weight holiday weeks and promotional periods far more heavily than ordinary weeks — exactly the kind of dynamic focus a plain RNN can\'t represent.',
    mistakes: [
      'Expecting a plain/simple RNN to retain information from far back in a long sequence — that\'s the vanishing-gradient weakness LSTMs and GRUs exist to fix.',
      'Treating every time step as equally important when building a sequence model — attention exists precisely because some time steps (e.g., holidays) matter far more than others.',
    ],
    sources: [
      { title: 'ISA 630: Deep Learning — Recurrent Neural Networks lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 6)' },
    ],
  },
  'sd-svm': {
    domain: 'support vector machines',
    overview: 'How SVMs choose the best of infinitely many separating hyperplanes (maximum margin), how they handle imperfectly separable data (soft margin, the C parameter), and how the kernel trick extends them to non-linear problems.',
    why: 'SVMs remain a strong, interpretable baseline for classification, and the maximum-margin idea — picking the decision boundary with the widest buffer, not just any boundary that works — shows up conceptually well beyond SVMs.',
    workplace: 'A data scientist tuning an SVM\'s C parameter realizes a large C (very low tolerance for margin violations) overfits noisy training data, while a smaller C accepts a few misclassifications in exchange for a more robust, generalizable boundary.',
    mistakes: [
      'Treating any separating hyperplane as good as any other — without maximizing the margin, the chosen boundary can be fragile and generalize poorly.',
      'Assuming the kernel trick explicitly computes a higher-dimensional transformation of every point — its whole point is avoiding that computation via kernel functions.',
    ],
    sources: [
      { title: 'ISA 630: Machine Learning for Business Applications — Support Vector Machines lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 7)' },
    ],
  },
  'sd-ensemble-hybrid': {
    domain: 'ensemble & hybrid learning',
    overview: 'How the bias-variance-irreducible error decomposition motivates ensemble methods, and the two main families — bagging (parallel, variance reduction, e.g. Random Forest) and boosting (sequential, bias reduction, e.g. AdaBoost) — that result from it.',
    why: 'Nearly every top-performing tabular-data model in practice is some form of ensemble (Random Forest, Gradient Boosting) — understanding why ensembling works (bias-variance tradeoff) explains why these methods consistently beat single models.',
    workplace: 'A data scientist choosing between Random Forest and AdaBoost for a noisy dataset picks Random Forest, recalling that boosting methods like AdaBoost are more prone to overfitting noisy data than bagging methods are.',
    mistakes: [
      'Choosing a stable, low-variance base learner (like logistic regression) for bagging — bagging\'s main benefit is variance reduction, so it pays off most with unstable, high-variance learners like decision trees.',
      'Confusing bagging (parallel, independent learners on bootstrap samples) with boosting (sequential learners, each correcting previous mistakes) — they reduce different error components and have different overfitting risk profiles.',
    ],
    sources: [
      { title: 'ISA 630: Machine Learning for Business Applications — Ensemble Learning lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 8)' },
    ],
  },
  'sd-experiments-intro': {
    domain: 'experiments & causality',
    overview: 'Why observational data can only show correlation while experiments can establish causation, the four-step structure of a proper experiment, and the classic traps (lurking variables, sample selection bias) that make causal claims from observational data unreliable.',
    why: 'Nearly every later subdeck in this course — A/B testing, factorial designs, causal inference — is really just an elaboration on these foundational ideas: random assignment is what makes a causal claim defensible, and observational data alone usually isn\'t enough.',
    workplace: 'A product analyst notices that customers who use a new feature have higher retention, but recognizes this is observational data with a likely lurking variable (more engaged customers might both adopt new features and naturally retain better) — so they push for a randomized experiment before claiming the feature caused the retention lift.',
    mistakes: [
      'Treating a strong correlation in observational data as proof of causation without considering lurking variables.',
      'Assuming a larger sample size can fix sample selection bias — it\'s a problem with how the data was generated, not how much was collected.',
    ],
    sources: [
      { title: 'ISA 633: Business Experiments — Introduction to Business Experiments lecture notes', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1)' },
    ],
  },
  'sd-ab-testing': {
    domain: 'A/B testing',
    overview: 'The statistical machinery behind A/B tests: sampling distributions and standard error (why we can\'t just compare two raw averages), and the Type I/Type II error and power framework that determines how big a sample you actually need.',
    why: 'Online and offline A/B tests are the most common business experiment in practice, and most A/B testing mistakes trace back to skipping a power calculation or misreading what a p-value/Type I error rate actually promises.',
    workplace: 'A checkout-flow team wants to detect a $0.50 increase in average user spend, knows the spend standard deviation is $25, and runs a power calculation before launching — discovering they need about 39,000 users per variant to reliably detect that effect at 80% power.',
    mistakes: [
      'Launching an A/B test without a power calculation, then later interpreting a "no significant difference" result as proof there\'s no effect, when the sample may have simply been too small to detect it.',
      'Treating the Type I error rate (α) as something fixed by nature — it\'s a risk tolerance the experimenter chooses in advance, not a property of the data.',
    ],
    sources: [
      { title: 'ISA 633: Business Experiments — A/B Testing lecture notes', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
    ],
  },
  'sd-abn-testing': {
    domain: 'A/B/n testing',
    overview: 'How ANOVA extends A/B testing to three or more treatment groups, why it answers a different question than a regression on the same data, and how Tukey HSD safely compares every treatment pair afterward.',
    why: 'Most real business experiments compare more than two variants at once (A/B/n, not just A/B) — ANOVA plus a correctly-controlled post-hoc test is the standard, statistically sound way to handle that.',
    workplace: 'A marketing team testing three landing-page variants runs an ANOVA first to confirm at least one variant differs, then uses Tukey HSD (not five separate pairwise t-tests) to find out exactly which variants differ from each other without inflating the false-positive rate.',
    mistakes: [
      'Running separate pairwise t-tests across three or more groups instead of ANOVA followed by a proper post-hoc test like Tukey HSD — that approach inflates the overall false-positive rate.',
      'Reading a regression coefficient on a treatment variable as answering "do these treatments differ overall" — that\'s the ANOVA F-test\'s job; the coefficient only describes one specific contrast.',
    ],
    sources: [
      { title: 'ISA 633: Business Experiments — A/B/n Testing lecture notes', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3)' },
    ],
  },
  'sd-blocking': {
    domain: 'blocking designs',
    overview: 'How to handle a known, controllable nuisance factor in an experiment: the Randomized Complete Block Design (RCBD) for one blocking factor, and the Latin Squares Design for two blocking factors at once.',
    why: 'Real experiments almost always have at least one nuisance variable (which agent handles the call, which store runs the test, which week it happens) — blocking removes its effect from the comparison instead of letting it inflate the error term and mask the real treatment effect.',
    workplace: 'A retailer testing four checkout-display designs across four stores and four weeks uses a 4×4 Latin Squares Design so that store and week effects (both nuisance factors) are removed from the comparison, isolating the actual display effect.',
    mistakes: [
      'Lumping a known nuisance factor\'s variation into the error term instead of explicitly blocking on it — this inflates the error term and makes the treatment test less sensitive.',
      'Forgetting that in an RCBD ANOVA output, only the treatment\'s p-value answers the research question — the block\'s p-value is not the thing being tested.',
    ],
    sources: [
      { title: 'ISA 633: Business Experiments — Blocking lecture notes', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 4)' },
    ],
  },
  'sd-bandits': {
    domain: 'multi-armed bandits',
    overview: 'How bandit algorithms (epsilon-greedy, Thompson Sampling) automate the exploration-exploitation tradeoff to minimize regret in online testing, and why that adaptivity comes at the cost of biased data for clean statistical inference.',
    why: 'Unlike a fixed-allocation A/B test, a bandit shifts traffic toward the winning variant in real time — minimizing the cost of exposing customers to an inferior option, which matters a lot when testing is expensive or ongoing.',
    workplace: 'A site running a long-term bandit test on its checkout button color keeps a small, fixed, randomly-allocated holdout slice of traffic specifically so analysts can later get an unbiased read on the true effect size, since the adaptively-allocated majority of traffic isn\'t suitable for standard confidence intervals.',
    mistakes: [
      'Treating bandit-collected data as if it were an unbiased random sample suitable for ordinary hypothesis testing — adaptive allocation systematically biases which arms accumulate more data.',
      'Trying to compute exact regret from live experiment data — regret requires knowing the true reward of arms that weren\'t pulled, which is only knowable in simulation, not in a real deployment.',
    ],
    sources: [
      { title: 'ISA 633: Business Experiments — Introduction to Multi-Arm Bandits lecture notes', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 5)' },
    ],
  },
  'sd-factorial-designs': {
    domain: 'factorial & fractional factorial designs',
    overview: 'Why testing multiple factors together (a factorial design) beats running separate A/B tests per factor — it detects interactions and gives more power per run — and how fractional factorial designs trim the run count for larger factor sets at the cost of aliasing some higher-order effects.',
    why: 'Real product changes (page layout, pricing, messaging) rarely act independently — a factorial design is the only way to discover that two changes interact, and fractional designs make testing many factors at once practical instead of prohibitively expensive.',
    workplace: 'A growth team testing four website elements at once (background, font size, text color, signup button) runs a single factorial experiment instead of four separate A/B tests, and discovers a background/font-size interaction that no single-factor test could have revealed.',
    mistakes: [
      'Running separate A/B tests per factor instead of a combined factorial design — that approach can never detect interactions between factors.',
      'Attributing a significant effect in a fractional factorial design to a main effect without checking what it\'s aliased with — the result could equally be due to the confounded higher-order interaction.',
    ],
    sources: [
      { title: 'ISA 633: Business Experiments — Factorial Designs lecture notes', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 6)' },
      { title: 'ISA 633: Business Experiments — Fractional Factorial and Screening Designs lecture notes', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 6)' },
    ],
  },
  'sd-switchback': {
    domain: 'switchback experiments',
    overview: 'Why system-wide treatments (pricing algorithms, marketplace rules) can\'t be tested with ordinary user-level A/B tests, how switchback experiments (built on clinical crossover designs) alternate treatment by time period instead, and how carryover effects and design balance/uniformity determine whether the resulting treatment estimate is trustworthy.',
    why: 'Marketplace and platform-level changes — dynamic pricing, recommendation algorithms, staffing rules — create interference across users that ordinary randomization can\'t handle; switchback experiments are the standard way to test these system-wide changes cleanly.',
    workplace: 'A ride-sharing platform testing a new pricing algorithm can\'t show different prices to different riders simultaneously without distorting the marketplace, so it switches the entire system between old and new pricing by time block, then checks whether the design is uniform and balanced before trusting the treatment-effect estimate.',
    mistakes: [
      'Running a standard user-level A/B test for a treatment that operates on the whole system (pricing, marketplace rules) — interference across users biases the result; a switchback design is needed instead.',
      'Trusting a crossover/switchback design\'s treatment estimate without checking it\'s uniform and balanced for carryover effects — an unbalanced design lets carryover effects contaminate the direct treatment comparison.',
    ],
    sources: [
      { title: 'ISA 633: Business Experiments — Introduction to Switchback Experiments lecture notes', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 7)' },
    ],
  },
  'sd-causal-inference': {
    domain: 'causal inference',
    overview: 'The potential outcomes framework that formally defines a causal effect via an unobservable counterfactual, the decomposition of an observed outcome gap into true treatment effect plus selection bias, and the distinct ATE/ATT/ATU averages that summarize a treatment effect across different populations.',
    why: 'This module is the theoretical foundation underlying everything else in the course — every A/B test, blocking design, and switchback experiment is ultimately a strategy for estimating one of ATE/ATT/ATU while making the selection-bias term in the basic identity vanish or become estimable.',
    workplace: 'A data scientist analyzing observational data (no randomization) for a new feature\'s impact on retention explicitly separates "the causal effect" from "selection bias" in their write-up, flagging that without randomization the two are confounded and the raw retention gap overstates the true causal effect if more engaged users self-selected into using the feature.',
    mistakes: [
      'Treating a raw outcome difference between treated and untreated groups in observational data as the causal effect — without randomization, that gap also contains selection bias.',
      'Conflating ATE with ATT — they answer different questions ("what if everyone got treated" vs. "did it help those who were actually treated") and can differ substantially when people self-select into treatment.',
    ],
    sources: [
      { title: 'ISA 633: Business Experiments — Introduction to Causal Inference lecture notes', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 8)' },
    ],
  },
  'sd-text-mining-spark': {
    domain: 'text mining on Spark',
    overview: 'How Spark MLlib handles text processing without a dedicated text-mining module — folding it into the general feature/clustering API — and why dense word embeddings (Word2Vec) replace sparse Document-Term Matrix representations for capturing word relationships at scale.',
    why: 'Distributed NLP pipelines (Spark MLlib\'s Tokenizer → StopWordsRemover → TF-IDF chain) are the bridge between the classical text-mining concepts learned earlier in the course and the large-scale GenAI/LLM pipelines covered next.',
    workplace: 'A data engineer building a sentiment-classification pipeline on millions of customer reviews uses Spark\'s feature module (Tokenizer, StopWordsRemover, TF-IDF) rather than a single-machine NLP library, since the dataset doesn\'t fit in one machine\'s memory.',
    mistakes: [
      'Assuming a Document-Term Matrix captures word relationships just because it counts word frequencies — DTM is purely a count; it has no notion of semantic similarity between terms.',
      'Looking for a single dedicated "text mining" module in Spark MLlib — text processing is deliberately split across the general feature and clustering APIs (pyspark.ml.feature).',
    ],
    sources: [
      { title: 'ISA 632: Big Data Analytics & Modern AI — Text Mining on Spark', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3, Dr. Jay Shan)' },
    ],
  },
  'sd-spark-nlp-llm': {
    domain: 'Spark NLP & large language models',
    overview: 'How Spark NLP scales NLP pipelines across a cluster, the Transformer architecture that replaced RNN/LSTM as the backbone of modern NLP, and how BERT and GPT diverge in using that architecture — plus the key lesson that scaling model size alone doesn\'t guarantee a model follows user intent.',
    why: 'This module bridges classical distributed text mining (Module 3) and the GenAI/LLM applications covered next — understanding the encoder/decoder split between BERT and GPT explains why later modules on prompting and RAG focus specifically on decoder-only models like GPT.',
    workplace: 'An engineer deciding between fine-tuning a BERT-style model versus prompting a GPT-style model for a classification task recalls that BERT pairs pre-training with fine-tuning on labeled data, while GPT pairs pre-training with zero/few-shot prompting — guiding which approach fits the available labeled data and task.',
    mistakes: [
      'Assuming GPT and BERT use the Transformer the same way — GPT uses only the decoder (unidirectional next-word prediction); BERT uses only the encoder (bidirectional, fine-tuned for downstream tasks).',
      'Assuming a bigger language model automatically becomes more aligned with user intent — GPT-3\'s well-documented limitations showed scale improves raw capability but not necessarily instruction-following, which is why fine-tuning with human feedback became necessary.',
    ],
    sources: [
      { title: 'ISA 632: Big Data Analytics & Modern AI — Spark NLP & LLM', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 7, Dr. Jay Shan)' },
    ],
  },
  'sd-prompt-rag': {
    domain: 'prompt engineering & RAG',
    overview: 'How generative AI differs from predictive AI, how autoregressive base LLMs work and how prompt structure shapes their output, and how Retrieval Augmented Generation (RAG) closes the LLM\'s knowledge gap by grounding responses in retrieved documents.',
    why: 'RAG is the standard production pattern for getting an LLM to answer accurately about private, current, or domain-specific data without the cost and complexity of retraining or fine-tuning the model itself.',
    workplace: 'A company builds an internal Q&A chatbot using RAG: it embeds its internal documentation into a vector database, retrieves the most relevant passages for each user question via similarity search, and injects them into the prompt — grounding the LLM\'s answer in real company policy instead of relying on what it learned during pre-training.',
    mistakes: [
      'Assuming a prompt that works well on one LLM transfers directly to another — prompts are model-specific and often need rephrasing across models.',
      'Treating RAG as just "retrieval + generation" — skipping filtering/reranking and prompt augmentation lets noisy or irrelevant retrieved documents undermine response quality.',
    ],
    sources: [
      { title: 'ISA 632: Big Data Analytics & Modern AI — Generative AI: Prompt Engineering & RAG', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 8, Dr. Jay Shan)' },
    ],
  },
  'sd-genai-eval-deploy': {
    domain: 'GenAI evaluation & deployment',
    overview: 'The distinct retrieval metrics (Context Precision/Relevance/Recall) and generation metrics (Faithfulness/Answer Relevancy/Answer Correctness) used to evaluate a RAG pipeline, plus how human feedback and production-grade serving/governance infrastructure round out a deployed GenAI system.',
    why: 'A RAG system can fail in retrieval, in generation, or in both — using the right metric for each component (rather than one vague "is the answer good" check) is what lets a team actually diagnose and fix the specific stage that\'s underperforming.',
    workplace: 'A team whose RAG chatbot gives wrong answers checks Context Recall first (is the right information even being retrieved?) before assuming the generator itself is the problem — separating retrieval failure from generation failure is exactly what these distinct metrics are designed to enable.',
    mistakes: [
      'Confusing Faithfulness (does the answer match the provided context) with Answer Correctness (does the answer match ground truth) — a faithful answer can still be wrong if the retrieved context itself was incomplete or flawed.',
      'Using different evaluation criteria in production monitoring than were used during development testing, making it impossible to tell whether a quality drop is a real regression or just a different yardstick.',
    ],
    sources: [
      { title: 'ISA 632: Big Data Analytics & Modern AI — Generative AI: Evaluation & Deployment', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 9, Dr. Jay Shan)' },
    ],
  },
  'sd-agentic-finetuning': {
    domain: 'agentic AI & LLM fine-tuning',
    overview: 'How prompting frameworks progress from zero-shot to multi-shot to Chain-of-Thought to ReAct\'s tool-using reason-act loop, what separates agentic from non-agentic workflows, and when to reach for LLM fine-tuning (full or parameter-efficient via LoRA) instead of prompting or RAG alone.',
    why: 'This is the capstone module of the entire GenAI sequence — it answers "what do you do when prompting and RAG aren\'t enough," moving from giving an LLM better instructions/context to giving it the ability to act (agents) or genuinely customizing its behavior (fine-tuning).',
    workplace: 'An enterprise team building a customer-support assistant on proprietary data first establishes a baseline with prompting and RAG, and only reaches for LoRA-based fine-tuning once they\'ve confirmed simpler approaches can\'t hit the required domain-specific accuracy — exactly the decision discipline the module teaches: don\'t jump to fine-tuning before you have a baseline, a test set, and a simpler alternative to compare against.',
    mistakes: [
      'Defaulting to zero-shot prompting for tasks that need a specific output format — multi-shot examples are required to teach the model that format from the prompt alone.',
      'Jumping straight to full fine-tuning before establishing a baseline and confirming a simpler approach (prompting, RAG) is genuinely insufficient — fine-tuning is the most expensive, highest-risk customization option.',
    ],
    sources: [
      { title: 'ISA 632: Big Data Analytics & Modern AI — Generative AI: Agentic AI and LLM Fine-Tuning', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 10, Dr. Jay Shan)' },
    ],
  },

  // ── ITS 241: Database Management Systems ─────────────────────────────────

  'sd-data-mgmt-intro': {
    domain: 'database fundamentals & DBMS',
    overview: 'How organizations evolved from paper and flat-file systems to database management systems, why DBMS solves the fundamental problems of file-based data management (redundancy, anomalies, structural dependence), and what the five components of a database system are.',
    why: 'Every database, analytics, and data engineering course assumes you can articulate why a DBMS exists — this module provides the "why databases at all" foundation before any SQL or design work begins.',
    workplace: 'A junior analyst who understands structural vs. data independence can make better decisions about when to use a DBMS vs. flat files, and can explain to non-technical stakeholders why storing the same data in multiple Excel spreadsheets is dangerous.',
    mistakes: [
      'Confusing the database (the data itself) with the DBMS (the software managing it).',
      'Ignoring DBMS costs: hardware/software investment, complexity, maintenance, and vendor lock-in are real trade-offs, not just theoretical concerns.',
    ],
    sources: [
      { title: 'ITS 241: Data Management in Organization lectures (Havelka)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.1)' },
      { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 1)' },
    ],
  },
  'sd-data-modeling': {
    domain: 'data modeling & schema architecture',
    overview: 'What data models are, why they are graphical and narrative abstractions of real-world domains, how the four building blocks (entity, attribute, association, constraint) compose a model, and how the three-schema architecture separates external/conceptual/internal views to achieve logical and physical independence.',
    why: 'Data modeling is the translation layer between what a business needs and what the DBMS stores. Without a sound conceptual model, database designs are built on shaky requirements.',
    workplace: 'A data analyst working with a developer to add a new feature needs to speak the shared language of entities, attributes, and relationships—this module provides that vocabulary and the ability to read ER diagrams produced by the DBAs.',
    mistakes: [
      'Stopping at the diagram without writing narrative constraints: diagrams cannot capture all rules (e.g., "an order must have at least one line item").',
      'Conflating the conceptual schema (ER model, DBMS-independent) with the internal schema (DDL in a specific RDBMS).',
    ],
    sources: [
      { title: 'ITS 241: Data Modeling Fundamentals & Data Abstraction lectures (Havelka)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.2)' },
      { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 2)' },
    ],
  },
  'sd-relational-db': {
    domain: 'relational database model',
    overview: 'The logical structure of relational tables (tuples, domains, key types), how functional dependency and determination underpin all key definitions, the role of the data dictionary as metadata infrastructure, and how indexes trade write performance for read speed.',
    why: 'The relational model is the dominant paradigm for structured data storage — understanding its precise definitions (what makes a valid relation, what integrity really means) is prerequisite knowledge for normalization, SQL, and database design.',
    workplace: 'When a database query returns duplicate rows or unexpected NULLs, understanding entity integrity (PK never null) and referential integrity (FK must match PK or be null) allows you to diagnose the root cause quickly.',
    mistakes: [
      'Treating NULLs as zero or empty string: NULL means unknown/not applicable, and NULL ≠ NULL in SQL three-valued logic.',
      'Over-indexing: adding indexes to every column slows write performance and wastes storage — index selectively on high-cardinality, frequently filtered columns.',
    ],
    sources: [
      { title: 'ITS 241: The Relational Database Model (Coronel Module 3)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.3)' },
      { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 3)' },
    ],
  },
  'sd-erd': {
    domain: 'entity-relationship modeling',
    overview: 'How to construct an ERD using entities, attribute types (simple, composite, derived, multivalued), and relationships characterized by connectivity (1:1, 1:M, M:N) and cardinality. Distinguishing weak from strong entities, and identifying vs. non-identifying relationship strength in Crow\'s Foot notation.',
    why: 'ERDs are the universal language of database design — the blueprint that DBAs, developers, and analysts read together before any DDL is written.',
    workplace: 'Before building a new reporting feature, a business analyst draws an ERD with stakeholders to confirm which entities exist, how they relate, and what cardinality constraints apply — catching design errors before they reach the database.',
    mistakes: [
      'Leaving M:N relationships unresolved in the physical design — relational databases require a junction/bridge table to implement M:N.',
      'Confusing optional participation (FK can be null) with a weak entity (existence-dependent AND PK includes FK from parent).',
    ],
    sources: [
      { title: 'ITS 241: Entity Relationship Diagrams (Coronel Module 4)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.4)' },
      { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 4–5)' },
    ],
  },
  'sd-normalization': {
    domain: 'database normalization',
    overview: 'The normalization process — from identifying functional dependencies to converting tables through 1NF (no repeating groups), 2NF (no partial dependencies), 3NF (no transitive dependencies), and BCNF (every determinant is a candidate key). When to stop normalizing and deliberately denormalize for performance.',
    why: 'Normalization directly prevents data anomalies that cause inconsistent data — the silent killer of database-driven applications. Understanding it is essential for both designing new schemas and diagnosing existing data quality problems.',
    workplace: 'A data engineer reviewing a proposed table design runs a quick normalization check: find the PK, list all FDs, look for partial (2NF) and transitive (3NF) dependencies, and flag violations before the schema is implemented in production.',
    mistakes: [
      'Applying 2NF checks to tables with single-attribute PKs: partial dependencies can only exist when the PK is composite — wasted effort otherwise.',
      'Over-normalizing analytical databases: OLAP star schemas are intentionally denormalized for query performance; normalizing them to 3NF destroys analytical efficiency.',
    ],
    sources: [
      { title: 'ITS 241: Normalization of Database Tables (Coronel Module 6)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.5)' },
      { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 6)' },
    ],
  },
  'sd-bi-datawarehouse': {
    domain: 'business intelligence & data warehousing',
    overview: 'The BI framework (data → information → knowledge → wisdom), operational vs. decision support data differences, the four ISNV properties of a data warehouse, star schema design (fact/dimension tables), and OLAP multidimensional analysis (ROLAP vs. MOLAP, drill-down, roll-up, slice, dice).',
    why: 'This module bridges the transactional database world to the analytics world — understanding why organizations need a separate analytical infrastructure (the warehouse) and how star schemas make complex aggregated queries tractable.',
    workplace: 'A BI developer designing a new sales dashboard creates a star schema with a FACT_SALES table surrounded by DIM_TIME, DIM_CUSTOMER, DIM_PRODUCT dimensions — this module provides the design vocabulary and rationale for that pattern.',
    mistakes: [
      'Running heavy analytical queries directly against the operational OLTP database — warehouse separation exists precisely to protect transactional performance.',
      'Normalizing the fact table: fact tables should hold only numeric measures and dimension FKs; descriptive attributes belong in dimension tables.',
    ],
    sources: [
      { title: 'ITS 241: Business Intelligence and Data Warehouses (Coronel Module 13)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1.6)' },
      { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 13)' },
    ],
  },
  'sd-sql-fundamentals': {
    domain: 'SQL fundamentals',
    overview: 'The four SQL language categories (DML, DDL, TCL, DCL), the six SELECT clauses and their logical execution order, WHERE filtering with comparison/logical/special operators (BETWEEN, IN, LIKE, IS NULL), ORDER BY and DISTINCT, and column aliases with computed columns.',
    why: 'SQL is the universal language for relational databases — every analyst, data scientist, and engineer needs to read and write it fluently. This module covers the foundational grammar that all advanced SQL builds on.',
    workplace: 'Writing a one-time report for a stakeholder: start with FROM (which tables), add WHERE (filter criteria), use SELECT to pick and compute columns, and ORDER BY to sort results sensibly — all within minutes.',
    mistakes: [
      'Testing for NULL with = NULL instead of IS NULL: SQL three-valued logic means NULL = NULL evaluates to UNKNOWN, never TRUE.',
      'Using an alias defined in SELECT inside a WHERE clause: WHERE is evaluated before SELECT, so the alias doesn\'t exist yet — repeat the expression or use a subquery.',
    ],
    sources: [
      { title: 'ITS 241: Introduction to SQL (Coronel Module 7)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
      { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 7)' },
    ],
  },
  'sd-sql-joins-agg': {
    domain: 'SQL JOINs & aggregate functions',
    overview: 'INNER JOIN vs. OUTER JOIN types (LEFT, RIGHT, FULL) and when unmatched rows require an outer join; the five aggregate functions (COUNT, MIN, MAX, SUM, AVG); GROUP BY for per-group aggregation; HAVING to filter aggregated groups.',
    why: 'Almost every real-world SQL query combines data from multiple tables and summarizes it — JOINs and aggregates are the two most-used features beyond basic SELECT.',
    workplace: 'A sales analyst writes a weekly query joining ORDERS to CUSTOMERS to PRODUCTS, groups by sales rep, aggregates revenue with SUM, and uses HAVING to flag reps below quota — this module covers exactly that pattern.',
    mistakes: [
      'Using INNER JOIN when you need to see all rows from one table regardless of matches — INNER JOIN silently drops unmatched rows; use LEFT OUTER JOIN.',
      'Placing aggregate functions in WHERE: WHERE runs before aggregation, so aggregate conditions must go in HAVING.',
    ],
    sources: [
      { title: 'ITS 241: SQL JOINs & Aggregate Functions (Coronel Module 7)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
      { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 7)' },
    ],
  },
  'sd-sql-advanced': {
    domain: 'advanced SQL',
    overview: 'Subqueries (scalar, multi-row IN, FROM inline views, attribute-list), correlated subqueries and EXISTS/NOT EXISTS for per-row logic, date/numeric/string/conversion functions, set operators (UNION, UNION ALL, INTERSECT, EXCEPT/MINUS), and principled query-building (FROM-first build order).',
    why: 'Advanced SQL skills separate analysts who can answer any data question from those who can only run simple lookups — subqueries and set operators unlock recursive, comparative, and combinatorial analyses impossible with basic SELECT.',
    workplace: 'Finding customers who bought in 2024 but not 2025 (lapsed customers) is a classic EXCEPT query: SELECT CustID FROM ORDERS WHERE Year=2024 MINUS SELECT CustID FROM ORDERS WHERE Year=2025 — this module makes that pattern second nature.',
    mistakes: [
      'Using = with a subquery that returns multiple rows — use IN for multi-row subqueries or a scalar subquery if exactly one row is guaranteed.',
      'Choosing UNION over UNION ALL unnecessarily — UNION deduplicates (extra sort), which is wasted overhead if duplicates can\'t occur or don\'t matter.',
    ],
    sources: [
      { title: 'ITS 241: SQL Subqueries, Functions & Set Operators (Coronel Module 7)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
      { title: 'Database Systems: Design, Implementation, and Management, 14th Edition', kind: 'textbook', ref: 'Coronel & Morris, Cengage, 2023 (Ch 7)' },
    ],
  },
};