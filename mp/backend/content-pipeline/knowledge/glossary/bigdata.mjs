// Glossary entries for the "bigdata" deck. Each entry:
// { m: [matchers...], d: 'definition with «cloze phrases»', how, ex, we, mk, src: [{title,kind,ref}] }
// Grounded in backend/content-pipeline/extracted/... per backend/content-pipeline/taxonomy.mjs sourcePaths.
//
// sd-bigdata-systems — ISA 514 Module 8 "Big Data Systems: From Hadoop to Spark"
const SD_BIGDATA_SYSTEMS_SRC = [
  { title: 'ISA 514: Managing Big Data — Big Data Systems (From Hadoop to Spark)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 8, Dr. Jay Shan)' },
];

// sd-spark — ISA 632 Module 2 "Apache Spark"
const SD_SPARK_SRC = [
  { title: 'ISA 632: Big Data Analytics & Modern AI — Apache Spark', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2, Dr. Jay Shan)' },
];

// sd-distributed-computing — ISA 632 Module 2 "Apache Spark" lecture, "DataFrame
// Operations" and "Eager and Lazy Execution" sections (slides 24-28)
const SD_DISTRIBUTED_COMPUTING_SRC = [
  { title: 'ISA 632: Big Data Analytics & Modern AI — Apache Spark (DataFrame Operations & Lazy Execution)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2, slides 24-28)' },
];

// sd-ml-at-scale — ISA 632 Module 5 "Machine Learning at Scale" (Scalable ML & MLOps/MLflow lectures)
const SD_ML_AT_SCALE_SRC = [
  { title: 'ISA 632: Big Data Analytics & Modern AI — Machine Learning at Scale', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 5, Dr. Jay Shan)' },
];

// sd-recommender-systems — ISA 632 Module 6 "Recommender Systems and ALS"
const SD_RECOMMENDER_SYSTEMS_SRC = [
  { title: 'ISA 632: Big Data Analytics & Modern AI — Recommender Systems and ALS', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 6, Dr. Jay Shan)' },
  { title: 'Dive Into Deep Learning — Recommender Systems', kind: 'textbook', ref: 'Zhang, Lipton, Li & Smola (Ch. "Overview of Recommender Systems")' },
];

export const GLOSSARY_bigdata = [
  {
    m: ['hadoop', 'hadoop ecosystem'],
    d: 'Hadoop (2006) is «a framework for distributed storage and computing that manages clusters of commodity machines» — its ecosystem bundles HDFS (distributed storage), YARN (job scheduling), MapReduce (a parallel programming model), Sqoop (RDBMS↔Hadoop data transfer), Hive (SQL-like queries over data-lake data), and Spark (in-memory processing).',
    src: SD_BIGDATA_SYSTEMS_SRC,
  },
  {
    m: ['hdfs', 'hadoop distributed file system'],
    d: 'HDFS (Hadoop Distributed File System) splits incoming data into «128 MB blocks, each replicated onto three different Data Nodes», while a central Name Node tracks which blocks belong to which file and where they live — without doing any data processing itself.',
    how: 'If a Data Node fails, HDFS detects it and reroutes work to one of the other nodes already holding a replica of that block — this is what makes Hadoop a robust distributed backup against disk crashes, accidental deletion, or even site disasters.',
    mk: 'Assuming the Name Node itself is protected by the same replication as ordinary data blocks — Hadoop\'s blocks are replicated across Data Nodes, but the Name Node is a special case and is not backed up the same way.',
    src: SD_BIGDATA_SYSTEMS_SRC,
  },
  {
    m: ['mapreduce'],
    d: 'MapReduce is «a programming model for distributed computation built on three steps: Map (a computation applied independently to each block of data), Shuffle-and-Sort (grouping outputs by key, done automatically), and Reduce (summarizing/aggregating the grouped outputs)» — the programmer only writes the Map and Reduce functions; both use key-value pairs as input and output.',
    ex: 'In the classic cooking analogy: Map = each of 3 helpers chops and weighs their own mixed bag of vegetables; Shuffle-and-Sort = regrouping all the chopped pieces by vegetable type across helpers; Reduce = summing each vegetable type into one labeled total (e.g., 26 lbs tomatoes total).',
    mk: 'Writing Map-step computations that depend on the input or output of another node\'s computation — each Map task must be fully independent for the parallel model to work at all.',
    src: SD_BIGDATA_SYSTEMS_SRC,
  },

  // ---- sd-spark ----
  {
    m: ['apache spark', 'spark'],
    d: 'Apache Spark is «a fast, general engine for large-scale distributed data processing» that, unlike MapReduce, doesn\'t require explicitly coding Map and Reduce tasks and uses in-memory caching (keeping data in nodes\' main memory across a job) — making complex tasks 10x to 100x faster than the classic MapReduce framework.',
    ex: 'A multi-step analytics pipeline that would require several slow disk-bound MapReduce jobs can run as one fast, in-memory Spark job instead.',
    src: SD_SPARK_SRC,
  },
  {
    m: ['rdd', 'resilient distributed dataset'],
    d: 'A Resilient Distributed Dataset (RDD) is «the fundamental Spark abstraction — Spark\'s core data structure, conceptually a "row," distributed and fault-tolerant across a cluster» — Spark also offers DataFrame ("table") and Dataset ("database") abstractions built on top of RDDs for more structured use cases.',
    src: SD_SPARK_SRC,
  },
  {
    m: ['spark dataframe'],
    d: 'A Spark DataFrame is «the primary representation of structured data in Spark SQL — a tabular collection of row objects organized into columns by a schema, modeled after relational database tables» — and like a Pandas DataFrame, it is immutable: you transform it into a new DataFrame rather than modifying it in place.',
    how: 'Spark DataFrame syntax closely mirrors both SQL and Pandas: SQL\'s SELECT attr1, attr2 becomes sdf.select(\'attr1\', \'attr2\'); WHERE becomes sdf.filter(...); GROUP BY becomes sdf.groupby(...).',
    mk: 'Trying to modify a Spark DataFrame in place the way you might mutate a Python list — Spark DataFrames are immutable; every transformation produces a new DataFrame.',
    src: SD_SPARK_SRC,
  },

  // ---- sd-distributed-computing ----
  {
    m: ['transformations vs. actions', 'transformations vs actions', 'spark transformation', 'spark action'],
    d: 'Spark DataFrame operations split into two kinds: «transformations create a new DataFrame from existing one(s) and run in parallel across the application\'s executors (e.g., select, where, orderBy, join, limit), while actions output actual data values — returning results to the driver or writing them to a file (e.g., count, first, show, collect, write)».',
    ex: 'sdf.where(\'rating > 4\') is a transformation (still lazy, no data moved yet); calling .show() afterward is the action that actually triggers execution and displays rows.',
    mk: 'Calling collect() on a huge DataFrame without thinking about it — that action pulls every row back to the driver\'s memory, which can crash the driver if the result set is large.',
    src: SD_DISTRIBUTED_COMPUTING_SRC,
  },
  {
    m: ['lazy evaluation (spark)', 'eager and lazy execution'],
    d: 'Spark executes transformations «lazily — building up a plan of operations without actually running them — until an action is called, which triggers the lazy execution of that whole chain of transformations at once» (DataFrame schemas, by contrast, are determined eagerly).',
    how: 'Chaining several transformations (groupby, mean, sort) costs nothing computationally until you call an action like show() or collect() — Spark can then optimize the entire chain before running it.',
    mk: 'Assuming each transformation in a chain executes immediately, one at a time, the way ordinary imperative code does — Spark defers all of it until an action forces evaluation.',
    src: SD_DISTRIBUTED_COMPUTING_SRC,
  },
  {
    m: ['driver and executors', 'spark driver', 'spark executor'],
    d: 'In Spark\'s execution model, «the driver is the main Spark program that coordinates the job, while executors are the worker processes that actually run transformations in parallel across the cluster» — action results are typically returned from the executors back to the driver, or written directly to a file.',
    src: SD_DISTRIBUTED_COMPUTING_SRC,
  },

  // ---- sd-ml-at-scale ----
  {
    m: ['spark mllib', 'mllib'],
    d: 'Spark MLlib is «Spark\'s machine learning library, built on top of the DataFrame API, that makes practical machine learning scalable» — supporting algorithms like Decision Tree, Random Forest, Linear Regression, and K-means directly on distributed data.',
    how: 'Banko and Brill\'s famous observation — "it\'s not who has the best algorithms that wins, it\'s who has the most data" — is the core motivation for MLlib: traditional single-machine ML libraries don\'t scale directly to very large datasets.',
    src: SD_ML_AT_SCALE_SRC,
  },
  {
    m: ['hyperparameter tuning (mllib)', 'cross validator (mllib)', 'paramgridbuilder'],
    d: 'MLlib\'s hyperparameter tuning combines three pieces: «an Estimator (the algorithm or Pipeline to tune), a ParamGridBuilder (the grid of hyperparameter values to search), and an Evaluator (the metric used to score each fitted model on held-out data)» — wrapped in a CrossValidator that finds the best parameter combination and refits on the full dataset.',
    how: 'Setting CrossValidator\'s parallelism to 2 or more runs multiple parameter combinations concurrently (a value of 1 runs serially) — but pushing parallelism past the cluster\'s actual resources stops helping and can even hurt performance.',
    src: SD_ML_AT_SCALE_SRC,
  },
  {
    m: ['hyperopt'],
    d: 'Hyperopt is «an open-source hyperparameter optimization package that uses a Bayesian approach (e.g., Tree of Parzen Estimators) to adaptively choose new hyperparameter settings based on prior results» — exploring the search space more intelligently than a plain grid search, and supporting both serial and parallel optimization.',
    mk: 'Trying to combine distributed training (e.g., MLlib across a cluster) with distributed hyperparameter tuning at the same time — the two don\'t mix; the standard patterns are single-machine Hyperopt tuning a distributed training algorithm, or distributed Hyperopt (via SparkTrials) tuning a single-machine algorithm like scikit-learn.',
    src: SD_ML_AT_SCALE_SRC,
  },
  {
    m: ['mlops'],
    d: 'MLOps applies DevOps-style discipline to machine learning systems — it\'s often summarized as «MLOps = DevOps + DataOps + ModelOps» — addressing core issues like tracking experiments, reproducing code, comparing models, and standardizing how models are packaged and deployed.',
    src: SD_ML_AT_SCALE_SRC,
  },
  {
    m: ['mlflow', 'mlflow tracking'],
    d: 'MLflow is «an open-source platform (developed by Databricks) for managing the machine learning lifecycle», with four core components — Tracking, Projects, Models, and Plugins — where MLflow Tracking specifically logs «parameters (hyperparameters), metrics (e.g., RMSE), artifacts (output files like models or images), and the source code» for every run.',
    ex: 'A data scientist running 50 different hyperparameter combinations can later query MLflow\'s tracking API to find exactly which run produced the lowest RMSE and what parameters it used.',
    src: SD_ML_AT_SCALE_SRC,
  },

  // ---- sd-recommender-systems ----
  {
    m: ['content-based recommender', 'content-based filtering'],
    d: 'A content-based recommender predicts preferences using «an item\'s own attributes (e.g., a movie\'s actor, director, genre) combined with a user\'s weighted preferences for those attributes» — it works well for brand-new items with no interaction history and is easy to explain.',
    ex: 'Recommending a movie because it shares the same director or genre as movies the user already rated highly is content-based filtering.',
    src: SD_RECOMMENDER_SYSTEMS_SRC,
  },
  {
    m: ['collaborative filtering'],
    d: 'Collaborative filtering recommends items based on «the preferences of similar users, rather than any knowledge of the items themselves» — making it domain-agnostic (the same algorithm recommends movies, products, or songs equally well), but it can\'t recommend anything for users or items with no interaction history yet.',
    how: 'User-based CF asks "what do users similar to you like?" while item-based CF asks "what items are similar to ones you already like?" — item-based CF (popularized by Amazon) usually scales better because most platforms have far more users than products.',
    ex: 'If Alice and Donna have rated movies very similarly so far, a user-based recommender will suggest a movie Donna loved (like "Eat Pray Love") to Alice, even though Alice hasn\'t seen it.',
    src: SD_RECOMMENDER_SYSTEMS_SRC,
  },
  {
    m: ['explicit vs. implicit feedback', 'explicit feedback', 'implicit feedback'],
    d: 'Recommender input preferences come in two forms: «explicit feedback, where users directly rate items (e.g., Netflix star ratings), and implicit feedback, inferred by observing behavior (e.g., which movies a customer watches, or whether they finish them)» — implicit feedback is noisier but far more abundant since it requires no extra user effort.',
    src: SD_RECOMMENDER_SYSTEMS_SRC,
  },
  {
    m: ['cold start problem'],
    d: 'The cold start problem is collaborative filtering\'s core weakness: «it needs existing user/item interaction data to find similar users, so a brand-new service with no users yet has nothing to base recommendations on» — a common workaround is starting with content-based filtering and transitioning to a hybrid, then fully collaborative approach as interaction data accumulates.',
    mk: 'Launching a new product with pure collaborative filtering from day one — with zero interaction history, there\'s no signal for it to work from; content-based filtering is the practical starting point.',
    src: SD_RECOMMENDER_SYSTEMS_SRC,
  },
  {
    m: ['hybrid recommender'],
    d: 'A hybrid recommender «combines content-based and collaborative filtering predictions (e.g., by averaging the two)», since each approach has complementary strengths and weaknesses — often producing better results than relying on either approach alone.',
    src: SD_RECOMMENDER_SYSTEMS_SRC,
  },
];