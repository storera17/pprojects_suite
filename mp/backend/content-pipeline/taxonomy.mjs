// Deck/subdeck skeleton for MomentumProdigy.
//
// Unlike CORTEX (which derived structure from a hand-typed Excel sheet),
// this taxonomy is grounded directly in the real module folders of the
// included courses (see backend/content-pipeline/extracted/<bucket>/... , produced by
// backend/content-pipeline/extract-sources.mjs) plus a few supporting textbooks.
//
// Each subdeck's `concepts` array is filled in progressively during the
// authoring pass (see backend/content-pipeline/authoring-manifest.json) — an empty array
// means that subdeck hasn't been authored yet. `sourcePaths` point at the
// extracted-text directories an author should read before writing the
// subdeck's glossary entries in backend/content-pipeline/knowledge/glossary/<deckId>.mjs.

export const DECKS = [
  {
    id: 'foundations', title: 'Foundations of Analytics',
    tagline: 'The shared vocabulary of business analytics, big data, and AI.',
    order: 0,
  },
  {
    id: 'tools', title: 'Professional Tools & Workflow',
    tagline: 'The day-to-day stack of a working analyst and data engineer.',
    order: 1,
  },
  {
    id: 'powerbi', title: 'Power BI, DAX & Visualization',
    tagline: 'Model, calculate, and communicate with the Microsoft BI stack.',
    order: 2,
  },
  {
    id: 'python-data', title: 'Python, APIs & NoSQL',
    tagline: 'Acquire, shape, and store data programmatically.',
    order: 3,
  },
  {
    id: 'mining', title: 'Data Mining & Predictive Modeling',
    tagline: 'From raw records to validated predictive models.',
    order: 4,
  },
  {
    id: 'deep-learning', title: 'Machine Learning & Deep Learning',
    tagline: 'Neural architectures, gradients, and the models behind modern AI.',
    order: 5,
  },
  {
    id: 'optimization', title: 'Optimization & Decision Science',
    tagline: 'Prescriptive analytics: mathematical programming and algorithms.',
    order: 6,
  },
  {
    id: 'bigdata', title: 'Big Data & Spark',
    tagline: 'Distributed storage, distributed compute, and ML at scale.',
    order: 7,
  },
  {
    id: 'experiments', title: 'Experimentation & Causal Inference',
    tagline: 'Design trustworthy experiments and estimate true causal effects.',
    order: 8,
  },
  {
    id: 'genai', title: 'Generative AI & LLMs',
    tagline: 'NLP, prompting, RAG, agents, evaluation, and deployment.',
    order: 9,
  },
  {
    id: 'databases', title: 'Database Management Systems',
    tagline: 'Design, build, and query relational databases from first principles.',
    order: 10,
  },
];

/**
 * Each subdeck:
 *  - id, deckId, title, difficulty (1-3), order (within deck)
 *  - sourcePaths: extracted-text directories (relative to backend/content-pipeline/extracted/)
 *    that ground this subdeck's content
 *  - concepts: ordered list of concept terms authored so far (empty = pending)
 */
export const SUBDECKS = [
  // ---- foundations ----
  {
    id: 'sd-ai-overview', deckId: 'foundations', title: 'AI & Analytics Overview', difficulty: 1, order: 0,
    sourcePaths: ['isa632/Module 1. AI Overview', 'lit-ai', 'isa591/Module 0 - Pre-Term Review Material'],
    concepts: [
      'Business Analytics',
      'Descriptive Analytics',
      'Predictive Analytics',
      'Business Intelligence',
      'Data Science vs. Business Analytics',
      'Big Data',
      'Data-Driven Decision Making',
      'Supervised Learning',
      'Unsupervised Learning',
    ],
  },
  {
    id: 'sd-bigdata-overview', deckId: 'foundations', title: 'Big Data Basics', difficulty: 1, order: 1,
    sourcePaths: ['isa514/Module 1 - Big Data Overview'],
    concepts: [
      'Volume, Variety, Velocity',
      'Big Data Analytics Challenges',
      'Big Data Management Technologies',
    ],
  },

  // ---- tools ----
  {
    id: 'sd-data-warehousing', deckId: 'tools', title: 'Data Warehousing & ETL', difficulty: 2, order: 0,
    sourcePaths: ['lit-data-eng'],
    concepts: [
      'Star Schema',
      'Fact Table',
      'Dimension Table',
      'Slowly Changing Dimension',
      'ETL',
    ],
  },
  {
    id: 'sd-modern-data-stack', deckId: 'tools', title: 'Modern Data Stack (Snowflake & dbt)', difficulty: 2, order: 1,
    sourcePaths: ['lit-data-eng'],
    concepts: [
      'ELT',
      'Snowflake Architecture',
      'Virtual Warehouse',
      'dbt',
    ],
  },

  // ---- powerbi (ISA 512) ----
  {
    id: 'sd-dax', deckId: 'powerbi', title: 'Data Preparation & DAX', difficulty: 3, order: 0,
    sourcePaths: ['isa512/ISA 512/Module 1 - Data Preparation using DAX Query Language'],
    concepts: [
      'Evaluation Context',
      'Filter Context',
      'Row Context',
      'FILTER (DAX)',
      'ALL vs. ALLSELECTED',
      'DISTINCT vs. VALUES',
      'Bi-Directional Cross Filter',
    ],
  },
  {
    id: 'sd-powerbi-modeling', deckId: 'powerbi', title: 'Data Modeling using Power BI', difficulty: 2, order: 1,
    sourcePaths: ['isa512/ISA 512/Module 2 - Data Modeling using Power BI'],
    concepts: [
      'Data Lake',
      'Data Swamp',
      'Model Ambiguity',
      'Semi-Additive Fact',
      'Segmentation (Power BI)',
    ],
  },
  {
    id: 'sd-dashboards', deckId: 'powerbi', title: 'Visualization, Dashboards & Storytelling', difficulty: 1, order: 2,
    sourcePaths: ['isa512/ISA 512/Module 3 - Data Visualization, Dashboards, and Storytelling'],
    concepts: [
      'Data Encoding',
      'Dashboard (Definition)',
      'Dashboard Design Principles',
      'Visual Hierarchy',
    ],
  },

  // ---- python-data (ISA 514) ----
  {
    id: 'sd-python', deckId: 'python-data', title: 'Python Programming', difficulty: 1, order: 0,
    sourcePaths: ['isa514/Module 2 - Python', 'isa514/Module 3 - Python (II)'],
    concepts: [
      'Python List',
      'Python Dictionary',
      'Python Tuple',
      'CRISP-DM',
      'NumPy',
      'Pandas DataFrame',
    ],
  },
  {
    id: 'sd-web-api', deckId: 'python-data', title: 'Data Collection from Web APIs', difficulty: 2, order: 1,
    sourcePaths: ['isa514/Module 4 - Data Collection from Web API'],
    concepts: [
      'Web API',
      'API Key',
      'JSON',
      'XML',
    ],
  },
  {
    id: 'sd-nosql', deckId: 'python-data', title: 'NoSQL Databases', difficulty: 2, order: 2,
    sourcePaths: ['isa514/Module 5 - NoSQL Database'],
    concepts: [
      'NoSQL',
      'Document-Oriented Database',
      'MongoDB vs RDBMS Terminology',
    ],
  },

  // ---- mining (ISA 514 + ISA 591) ----
  {
    id: 'sd-data-mining-intro', deckId: 'mining', title: 'Data Mining Overview', difficulty: 1, order: 0,
    sourcePaths: ['isa514/Module 6 - Data Mining', 'isa591/Module 1 - Data Mining Overview', 'isa591/Module 0 - Pre-Term Review Material'],
    concepts: [
      'Classification (Data Mining Task)',
      'Prediction (Data Mining Task)',
      'Association Rules',
      'Data and Dimension Reduction',
      'The Data Mining Process',
      'Training, Test, and Holdout Partitions',
    ],
  },
  {
    id: 'sd-text-mining', deckId: 'mining', title: 'Text Mining', difficulty: 2, order: 1,
    sourcePaths: ['isa514/Module 7 - Text Mining'],
    concepts: [
      'Sentiment Analysis',
      'Bag of Words',
      'Document-Term Matrix',
      'Term Frequency',
      'Inverse Document Frequency',
      'TF-IDF',
      'Text Cleaning',
    ],
  },
  {
    id: 'sd-eda', deckId: 'mining', title: 'Exploratory Data Analysis', difficulty: 2, order: 2,
    sourcePaths: ['isa591/Module 2 - Exploratory Data Analysis'],
    concepts: [
      'Exploratory Data Analysis (EDA)',
      'Dummy Variable Encoding',
      'Missing Value Indicator',
      'Missing Data',
      'Outliers',
      'Variable Transformation',
    ],
  },
  {
    id: 'sd-dimension-reduction', deckId: 'mining', title: 'Dimension Reduction', difficulty: 2, order: 3,
    sourcePaths: ['isa591/Module 3 - Dimension Reduction'],
    concepts: [
      'Curse of Dimensionality',
      'Data Leakage',
      'Principal Components Analysis (PCA)',
    ],
  },
  {
    id: 'sd-model-evaluation', deckId: 'mining', title: 'Evaluating Model Performance', difficulty: 2, order: 4,
    sourcePaths: ['isa591/Module 4 - Evaluating Model Performance'],
    concepts: [
      'Predictive Accuracy vs. Model Fit',
      'Naive Benchmark',
      'RMSE',
      'MAE',
      'Cumulative Gain',
      'Lift',
    ],
  },
  {
    id: 'sd-regularized-regression', deckId: 'mining', title: 'Regularized Regression', difficulty: 2, order: 5,
    sourcePaths: ['isa591/Module 5 - Regularized Regression'],
    concepts: [
      'Bias-Variance Tradeoff',
      'Stepwise Selection',
      'Regularization',
      'Ridge Regression',
      'Lasso Regression',
      'K-Fold Cross-Validation',
    ],
  },
  {
    id: 'sd-tree-models', deckId: 'mining', title: 'Tree-Based Models', difficulty: 2, order: 6,
    sourcePaths: ['isa591/Module 6 - Tree-Based Models'],
    concepts: [
      'Overfitting (Decision Tree)',
      'Recursive Partitioning',
      'Gini Index (Decision Tree)',
      'Entropy (Decision Tree)',
      'Pruning a Decision Tree',
      'Variable Importance (Decision Tree)',
    ],
  },
  {
    id: 'sd-logistic-regression', deckId: 'mining', title: 'Logistic Regression', difficulty: 2, order: 7,
    sourcePaths: ['isa591/Module 7 - Logistic Regression'],
    concepts: [
      'Logistic Regression',
      'Logistic Function',
      'Odds (Logistic Regression)',
      'Interpreting Logistic Regression Coefficients',
      'Deviance (Logistic Regression)',
    ],
  },

  // ---- deep-learning (ISA 591 Module 8 + ISA 630 + d2l) ----
  {
    id: 'sd-nn-intro', deckId: 'deep-learning', title: 'Neural Networks Introduction', difficulty: 2, order: 0,
    sourcePaths: ['isa591/Module 8 - Neural Networks'],
    concepts: [
      'Activation Function',
      'Sigmoid Activation Function',
      'ReLU Activation Function',
      'Gradient Descent',
      'Backpropagation',
    ],
  },
  {
    id: 'sd-matrix-tensor', deckId: 'deep-learning', title: 'Matrix & Tensor Algebra', difficulty: 2, order: 1,
    sourcePaths: ['isa630/Module 0_ [Matrix-Tensor Algebra]'],
    concepts: [
      'Dot Product',
      'Vector Norm',
      'Matrix Multiplication',
      'Matrix Transpose',
      'Linear Dependence',
      'Sparse vs. Dense Matrix',
      'Tensor',
    ],
  },
  {
    id: 'sd-gradients-regularization', deckId: 'deep-learning', title: 'Gradients & Regularization', difficulty: 3, order: 2,
    sourcePaths: ['isa630/Module 1_ [Gradients, Regularization]'],
    concepts: [
      'Loss Function',
      'Cost Function',
      'Convex Cost Function',
      'Gradient (Cost Function)',
      'Gradient Descent Algorithm',
      'Ridge Regression (Gradients)',
    ],
  },
  {
    id: 'sd-classification-deep-dive', deckId: 'deep-learning', title: 'Classification Deep Dive', difficulty: 3, order: 3,
    sourcePaths: ['isa630/Module 2_ [Classification Deep Dive]'],
    concepts: [
      'Binary Classification (Deep Dive)',
      'Binary Cross-Entropy',
      'Multi-Class Classification',
      'Multi-Label Classification',
    ],
  },
  {
    id: 'sd-feedforward', deckId: 'deep-learning', title: 'Feed-Forward Architectures', difficulty: 3, order: 4,
    sourcePaths: ['isa630/Module 3_ [Deep Learning_ Feed-Forward Architectures]', 'lit-d2l/chapter_multilayer-perceptrons'],
    concepts: [
      'Perceptron',
      'Multi-Layer Perceptron',
      'Choosing an Activation Function',
      'Forward Pass',
      'Number of Estimated Parameters (Neural Network)',
    ],
  },
  {
    id: 'sd-autoencoders', deckId: 'deep-learning', title: 'AutoEncoders', difficulty: 3, order: 5,
    sourcePaths: ['isa630/Module 4_ [Deep Learning_ AutoEncoders]'],
    concepts: [
      'Autoencoder',
      'Latent Space (Autoencoder)',
      'Undercomplete Autoencoder',
      'Sparse Autoencoder',
      'Denoising Autoencoder',
      'Why Use Autoencoders',
    ],
  },
  {
    id: 'sd-cnn', deckId: 'deep-learning', title: 'Convolutional Neural Networks', difficulty: 3, order: 6,
    sourcePaths: ['isa630/Module 5_ [Convolution Neural Networks]', 'lit-d2l/chapter_convolutional-neural-networks', 'lit-d2l/chapter_convolutional-modern'],
    concepts: [
      'Feed-Forward NNs for Images',
      'Convolution (CNN)',
      'Pooling (CNN)',
      'Padding (CNN)',
      'Stride (CNN)',
    ],
  },
  {
    id: 'sd-rnn', deckId: 'deep-learning', title: 'Recurrent Neural Networks', difficulty: 3, order: 7,
    sourcePaths: ['isa630/Module 6_ [Recurrent Neural Networks]', 'lit-d2l/chapter_recurrent-neural-networks', 'lit-d2l/chapter_recurrent-modern'],
    concepts: [
      'Sliding Window (Sequences)',
      'Recurrent Neural Network',
      'Vanishing Gradient (RNN)',
      'LSTM',
      'LSTM Gates',
      'GRU',
      'Bidirectional LSTM',
      'Attention (RNN)',
    ],
  },
  {
    id: 'sd-svm', deckId: 'deep-learning', title: 'Support Vector Machines', difficulty: 3, order: 8,
    sourcePaths: ['isa630/Module 7_ [Support Vector Machines]'],
    concepts: [
      'Separating Hyperplane (SVM)',
      'Margin (SVM)',
      'Soft Margin Classifier',
      'Kernel Trick',
    ],
  },
  {
    id: 'sd-ensemble-hybrid', deckId: 'deep-learning', title: 'Ensemble & Hybrid Learning', difficulty: 3, order: 9,
    sourcePaths: ['isa630/Module 8_ [Ensemble-Hybrid Learning]'],
    concepts: [
      'Bias-Variance-Irreducible Error Decomposition',
      'Bootstrapping',
      'Bagging',
      'Random Forest',
      'Boosting',
    ],
  },

  // ---- optimization (ISA 634) ----
  {
    id: 'sd-opt-intro', deckId: 'optimization', title: 'Modeling & Optimization Overview', difficulty: 1, order: 0,
    sourcePaths: ['isa634/Day 1 - 8-26-2025/Handout - Intro'],
    concepts: [
      'Operations Research',
      'Prescriptive Analytics',
      'Decision Variables',
      'Objective Function',
      'Constraints',
    ],
  },
  {
    id: 'sd-complexity', deckId: 'optimization', title: 'Complexity & Algorithm Analysis', difficulty: 2, order: 1,
    sourcePaths: ['isa634/Day 1 - 8-26-2025/Handout - Complexity', 'isa634/8-28-25'],
    concepts: [
      'Computational Complexity',
      'Worst-Case Running Time',
      'Big O Notation',
      'Polynomial Time Algorithm',
      'Exponential Time Algorithm',
      'Brute-Force Algorithm',
      'Breadth-First Search',
      'Depth-First Search',
      'Class P',
      'NP-Completeness',
    ],
  },
  {
    id: 'sd-math-programming', deckId: 'optimization', title: 'Introduction to Mathematical Programming', difficulty: 2, order: 2,
    sourcePaths: ['isa634/Day 2 - 9-02-2025/Handout - Intro to Mathematical Programming', 'isa634/9-2-25'],
    concepts: [
      'Mathematical Programming Model',
      'Enumeration Method',
      'Graphical Solution Method',
      'Unconstrained Optimization',
      'Decision Variable Types',
    ],
  },
  {
    id: 'sd-lp', deckId: 'optimization', title: 'Linear Programming', difficulty: 3, order: 3,
    sourcePaths: ['isa634/9-9-25', 'isa634/9-11-25', 'isa634/Diet problem'],
    concepts: [
      'Linear Programming (LP)',
      'Standard Form of an LP',
      'Proportionality Assumption',
      'Additivity Assumption',
    ],
  },
  {
    id: 'sd-transportation-assignment', deckId: 'optimization', title: 'Transportation & Assignment Problems', difficulty: 2, order: 4,
    sourcePaths: ['isa634/Exam 2/Topic 1. Transportation and Assignment Problems', 'isa634/10-9-2025'],
    concepts: [
      'Transportation Problem',
      'Assignment Problem',
    ],
  },
  {
    id: 'sd-network-flow', deckId: 'optimization', title: 'Network Flow Problems', difficulty: 2, order: 5,
    // Note: Exam 2/Topic 2 folder is empty on disk; real content lives under 10-9-2025.
    sourcePaths: ['isa634/10-9-2025'],
    concepts: [
      'Network Flow Problem',
      'Source Node',
    ],
  },
  {
    id: 'sd-ip', deckId: 'optimization', title: 'Integer Programming', difficulty: 3, order: 6,
    sourcePaths: ['isa634/9-23-2025', 'isa634/10 21 2025'],
    concepts: [
      'Integer Programming (IP)',
      'Mixed Integer Programming (MIP)',
      'LP Relaxation',
    ],
  },

  // ---- bigdata (ISA 514 Module 8 + ISA 632 Spark) ----
  {
    id: 'sd-bigdata-systems', deckId: 'bigdata', title: 'Big Data Systems', difficulty: 2, order: 0,
    sourcePaths: ['isa514/Module 8 - Big Data Systems'],
    concepts: [
      'Hadoop',
      'HDFS',
      'MapReduce',
    ],
  },
  {
    id: 'sd-spark', deckId: 'bigdata', title: 'Apache Spark', difficulty: 2, order: 1,
    sourcePaths: ['isa632/Module 2. Spark'],
    concepts: [
      'Apache Spark',
      'RDD',
      'Spark DataFrame',
    ],
  },
  {
    id: 'sd-distributed-computing', deckId: 'bigdata', title: 'Distributed Computing on Spark', difficulty: 3, order: 2,
    sourcePaths: ['isa632/Module 2. Spark/ISA632-M02_Spark_20260127.pdf.txt'],
    concepts: [
      'Transformations vs. Actions',
      'Lazy Evaluation (Spark)',
      'Driver and Executors',
    ],
  },
  {
    id: 'sd-ml-at-scale', deckId: 'bigdata', title: 'Machine Learning at Scale', difficulty: 3, order: 3,
    sourcePaths: ['isa632/Module 5. Machine Learning at Scale'],
    concepts: [
      'Spark MLlib',
      'Hyperparameter Tuning (MLlib)',
      'Hyperopt',
      'MLOps',
      'MLflow',
    ],
  },
  {
    id: 'sd-recommender-systems', deckId: 'bigdata', title: 'Recommender Systems', difficulty: 2, order: 4,
    sourcePaths: ['isa632/Module 6. Recommender Systems', 'lit-d2l/chapter_recommender-systems'],
    concepts: [
      'Content-Based Recommender',
      'Collaborative Filtering',
      'Explicit vs. Implicit Feedback',
      'Cold Start Problem',
      'Hybrid Recommender',
    ],
  },

  // ---- experiments (ISA 633) ----
  {
    id: 'sd-experiments-intro', deckId: 'experiments', title: 'Introduction to Experiments & Causality', difficulty: 1, order: 0,
    sourcePaths: ['isa633/1. Module 1_ Introduction to Experiments and Causality'],
    concepts: [
      'Observational vs. Experimental Data',
      'Four Steps of an Experiment',
      'Big Three Criteria for Causality',
      'Lurking Variable',
      'Sample Selection Bias',
    ],
  },
  {
    id: 'sd-ab-testing', deckId: 'experiments', title: 'A/B Testing', difficulty: 3, order: 1,
    sourcePaths: ['isa633/2. Module 2_ A-B Testing'],
    concepts: [
      'A/B Testing',
      'Sampling Distribution',
      'Type I Error',
      'Type II Error',
      'Statistical Power',
    ],
  },
  {
    id: 'sd-abn-testing', deckId: 'experiments', title: 'A/B/n Testing', difficulty: 2, order: 2,
    sourcePaths: ['isa633/3. Module 3_ A-B-n Testing'],
    concepts: [
      'ANOVA',
      'ANOVA vs. Regression',
      'Multiple Testing Problem (ABN)',
    ],
  },
  {
    id: 'sd-blocking', deckId: 'experiments', title: 'Blocking', difficulty: 2, order: 3,
    sourcePaths: ['isa633/4. Module 4_ Blocking'],
    concepts: [
      'Blocking Factor',
      'Randomized Complete Block Design',
      'Latin Squares Design',
    ],
  },
  {
    id: 'sd-bandits', deckId: 'experiments', title: 'Multi-Armed Bandits', difficulty: 3, order: 4,
    sourcePaths: ['isa633/6. Module 5_ Multi-arm bandits'],
    concepts: [
      'Exploration vs. Exploitation',
      'Regret (Bandits)',
      'Epsilon-Greedy',
      'Thompson Sampling',
      'Cautions with Bandits (Biased Data)',
    ],
  },
  {
    id: 'sd-factorial-designs', deckId: 'experiments', title: 'Factorial & Fractional Factorial Designs', difficulty: 3, order: 5,
    sourcePaths: ['isa633/7. Module 6_ Factorial and Fractional Factorial Designs'],
    concepts: [
      'Factorial Design',
      'Fractional Factorial Design',
      'Aliasing (Confounding)',
    ],
  },
  {
    id: 'sd-switchback', deckId: 'experiments', title: 'Switchback Experiments', difficulty: 2, order: 6,
    sourcePaths: ['isa633/8. Module 7_ Switchback Experiments'],
    concepts: [
      'Switchback Experiment',
      'Crossover Design',
      'Carryover Effect',
      'Balanced Design (Crossover)',
    ],
  },
  {
    id: 'sd-causal-inference', deckId: 'experiments', title: 'Causal Inference', difficulty: 3, order: 7,
    sourcePaths: ['isa633/10. Module 8_ Causal Inference'],
    concepts: [
      'Counterfactual',
      'Selection Bias (Causal Decomposition)',
      'ATE, ATT, ATU',
    ],
  },

  // ---- genai (ISA 632) ----
  {
    id: 'sd-text-mining-spark', deckId: 'genai', title: 'Text Mining on Spark', difficulty: 2, order: 0,
    sourcePaths: ['isa632/Module 3. Text Mining on Spark'],
    concepts: [
      'Spark Text Mining Pipeline',
      'Word Embedding (Spark)',
    ],
  },
  {
    id: 'sd-spark-nlp-llm', deckId: 'genai', title: 'Spark NLP & LLMs', difficulty: 2, order: 1,
    sourcePaths: ['isa632/Module 7. Spark NLP & LLM'],
    concepts: [
      'Spark NLP',
      'Annotator Approaches vs. Models',
      'Transformer Architecture',
      'BERT vs. GPT',
      'Issues of GPT-3',
    ],
  },
  {
    id: 'sd-prompt-rag', deckId: 'genai', title: 'Prompt Engineering & RAG', difficulty: 2, order: 2,
    sourcePaths: ['isa632/Module 8. GenAI (1) -  Prompt Engineering & RAG'],
    concepts: [
      'Generative vs. Predictive AI',
      'Base LLM',
      'Prompt Engineering',
      'Retrieval Augmented Generation',
      'RAG Workflow Components',
    ],
  },
  {
    id: 'sd-genai-eval-deploy', deckId: 'genai', title: 'GenAI Evaluation & Deployment', difficulty: 3, order: 3,
    sourcePaths: ['isa632/Module 9. GenAI(2) - Evaluation & Deployment'],
    concepts: [
      'Retrieval-Related Metrics (RAG)',
      'Generation-Related Metrics (RAG)',
      'Evaluating the Whole GenAI System',
      'Review App (Human Feedback)',
      'Mosaic AI Gateway',
    ],
  },
  {
    id: 'sd-agentic-finetuning', deckId: 'genai', title: 'Agentic AI & LLM Fine-Tuning', difficulty: 3, order: 4,
    sourcePaths: ['isa632/Module 10. GenAI(3) - Agentic AI & LLM Fine-tuning'],
    concepts: [
      'Prompting Framework Progression',
      'ReAct Framework',
      'Agentic vs. Non-Agentic Workflows',
      'Agent Planning & Reflection',
      'LLM Fine-Tuning',
      'Full Fine-Tuning vs. PEFT/LoRA',
    ],
  },

  // ── databases (ITS 241) ───────────────────────────────────────────────────
  {
    id: 'sd-data-mgmt-intro', deckId: 'databases', title: 'Data Management & DBMS Fundamentals', difficulty: 1, order: 0,
    sourcePaths: [
      'its241/Module 1 - Introduction to Data Management/1. Data Management in Organization',
    ],
    concepts: [
      'Database vs File System',
      'DBMS Functions & Advantages',
      'Data Redundancy & Integrity Problems',
      'Structural vs Data Independence',
      'Database System Components',
    ],
  },
  {
    id: 'sd-data-modeling', deckId: 'databases', title: 'Data Modeling & Schema Architecture', difficulty: 2, order: 1,
    sourcePaths: [
      'its241/Module 1 - Introduction to Data Management/2. Data Modeling',
    ],
    concepts: [
      'Data Model Purpose & Components',
      'Entity, Attribute & Association',
      'Three-Schema Architecture',
      'Logical vs Physical Data Models',
      'Data Independence (Logical & Physical)',
    ],
  },
  {
    id: 'sd-relational-db', deckId: 'databases', title: 'The Relational Database Model', difficulty: 2, order: 2,
    sourcePaths: [
      'its241/Module 1 - Introduction to Data Management/3. Relational Databases ',
    ],
    concepts: [
      'Relational Table Characteristics',
      'Keys in the Relational Model',
      'Functional Dependency & Determination',
      'Data Dictionary & System Catalog',
      'Indexes in a Relational Database',
    ],
  },
  {
    id: 'sd-erd', deckId: 'databases', title: 'Entity-Relationship Modeling', difficulty: 2, order: 3,
    sourcePaths: [
      'its241/Module 1 - Introduction to Data Management/4. Entity Relationship Diagrams',
    ],
    concepts: [
      'ERD Components',
      'Cardinality & Connectivity',
      'Weak vs Strong Entities',
      'Relationship Strength',
      'Composite & Derived Attributes',
    ],
  },
  {
    id: 'sd-normalization', deckId: 'databases', title: 'Normalization', difficulty: 3, order: 4,
    sourcePaths: [
      'its241/Module 1 - Introduction to Data Management/5. Normalization',
    ],
    concepts: [
      'Normalization Purpose & Data Anomalies',
      'First Normal Form (1NF)',
      'Second Normal Form (2NF) & Partial Dependency',
      'Third Normal Form (3NF) & Transitive Dependency',
      'BCNF & Higher Normal Forms',
    ],
  },
  {
    id: 'sd-bi-datawarehouse', deckId: 'databases', title: 'Business Intelligence & Data Warehouses', difficulty: 2, order: 5,
    sourcePaths: [
      'its241/Module 1 - Introduction to Data Management/6. Analytics-Oriented Databases',
    ],
    concepts: [
      'Business Intelligence Framework',
      'Operational vs Decision Support Data',
      'Data Warehouse (ISNV Properties)',
      'Star Schema',
      'OLAP',
    ],
  },
  {
    id: 'sd-sql-fundamentals', deckId: 'databases', title: 'SQL Fundamentals', difficulty: 1, order: 6,
    sourcePaths: [
      'its241/Module 2 - SQL',
    ],
    concepts: [
      'SQL Language Categories',
      'SELECT Statement Structure',
      'WHERE Clause & Comparison Operators',
      'ORDER BY & DISTINCT',
      'Column Aliases & Computed Columns',
    ],
  },
  {
    id: 'sd-sql-joins-agg', deckId: 'databases', title: 'SQL JOINs & Aggregate Functions', difficulty: 2, order: 7,
    sourcePaths: [
      'its241/Module 2 - SQL',
    ],
    concepts: [
      'INNER JOIN',
      'OUTER JOIN Types',
      'Aggregate Functions',
      'GROUP BY Clause',
      'HAVING Clause',
    ],
  },
  {
    id: 'sd-sql-advanced', deckId: 'databases', title: 'Advanced SQL', difficulty: 3, order: 8,
    sourcePaths: [
      'its241/Module 2 - SQL',
    ],
    concepts: [
      'Subqueries',
      'Correlated Subqueries & EXISTS',
      'SQL Functions',
      'Set Operators',
      'Crafting SELECT Queries',
    ],
  },
];

/** Lessons of 5-9 concepts, preserving authored order. */
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
  const first = concepts[0] ?? 'Lesson';
  return `${String(first).slice(0, 46)}`;
}

/** Build the deck -> subdeck skeleton (only subdecks with authored concepts). */
export function buildStructure() {
  return DECKS.map((d) => ({
    id: d.id, title: d.title, tagline: d.tagline, order: d.order,
    subdecks: SUBDECKS
      .filter((s) => s.deckId === d.id && s.concepts.length > 0)
      .sort((a, b) => a.order - b.order),
  })).filter((d) => d.subdecks.length > 0);
}