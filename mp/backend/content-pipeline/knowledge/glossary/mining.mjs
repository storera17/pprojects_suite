// Glossary entries for the "mining" deck. Each entry:
// { m: [matchers...], d: 'definition with «cloze phrases»', how, ex, we, mk, src: [{title,kind,ref}] }
// Grounded in backend/content-pipeline/extracted/... per backend/content-pipeline/taxonomy.mjs sourcePaths.
//
// sd-eda — ISA 591 "Exploratory Data Analysis" lecture (Module 2, Day 1 & 2 notes)
const SD_EDA_SRC = [
  { title: 'ISA 591: Data Mining — Exploratory Data Analysis lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2, Day 1 & 2 notes)' },
];

// sd-data-mining-intro — ISA 591 "Data Mining Overview" lecture (Module 1, Day 1 notes)
const SD_DM_INTRO_SRC = [
  { title: 'ISA 591: Data Mining — Data Mining Overview lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1, Day 1 notes)' },
];

// sd-dimension-reduction — ISA 591 "Dimension Reduction" lecture (Module 3, Day 1 & 2 notes)
const SD_DIM_REDUCTION_SRC = [
  { title: 'ISA 591: Data Mining — Dimension Reduction lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3, Day 1 & 2 notes)' },
];

// sd-model-evaluation — ISA 591 "Evaluating Model Performance" lecture (Module 4, Day 1 notes)
const SD_MODEL_EVAL_SRC = [
  { title: 'ISA 591: Data Mining — Evaluating Model Performance lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 4, Day 1 notes)' },
];

// sd-regularized-regression — ISA 591 "Regularized Regression" lecture (Module 5 notes)
const SD_REG_REGRESSION_SRC = [
  { title: 'ISA 591: Data Mining — Regularized Regression lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 5 notes)' },
];

// sd-tree-models — ISA 591 "Tree-Based Models" lecture (Module 6, Day 1 & 2 notes)
const SD_TREE_MODELS_SRC = [
  { title: 'ISA 591: Data Mining — Tree-Based Models lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 6, Day 1 & 2 notes)' },
];

// sd-logistic-regression — ISA 591 "Logistic Regression" lecture (Module 7 Day 1 notes)
const SD_LOGISTIC_REGRESSION_SRC = [
  { title: 'ISA 591: Data Mining — Logistic Regression lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 7, Day 1 notes)' },
];

// sd-text-mining — ISA 514 "Text Mining" lecture (Module 7 slides)
const SD_TEXT_MINING_SRC = [
  { title: 'ISA 514: Managing Big Data — Text Mining lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 7 slides, Dr. Jay Shan)' },
];

export const GLOSSARY_mining = [
  {
    m: ['exploratory data analysis', 'exploratory data analysis (eda)', 'eda'],
    d: 'Exploratory data analysis (EDA) is the step where you «investigate a dataset to identify patterns, anomalies, and necessary preprocessing steps» before modeling — detecting missing values, outliers, and the variable transformations a dataset needs.',
    how: 'Load and inspect the data, summarize each variable, visualize distributions and relationships, then handle encoding issues, missing values, and outliers before any model is fit.',
    ex: 'Before building a model to predict which donors will give again, an analyst first explores the veterans\'-organization dataset to spot which variables are miscoded, which have missing values, and which are skewed.',
    mk: 'Treating EDA purely as a presentation step (charts for stakeholders) when its main job before modeling is preparing and cleaning the data.',
    src: SD_EDA_SRC,
  },
  {
    m: ['dummy variable encoding', 'dummy coding', 'dummy variables'],
    d: 'Dummy (binary) encoding represents a categorical variable with K categories as «K−1 binary indicator variables», each flagging membership in one category relative to a baseline.',
    how: 'Pick one category as the baseline and remove its dummy column — keeping all K dummy columns would make the variables perfectly collinear (multicollinearity).',
    ex: 'A "Home Owner" variable with two levels (yes/no) becomes a single dummy column; a 6-level status category becomes 5 dummy columns.',
    mk: 'Keeping all K dummy columns for a K-category variable instead of K−1 — that creates multicollinearity because the columns are fully determined by each other.',
    src: SD_EDA_SRC,
  },
  {
    m: ['missing value indicator', 'missing data indicator'],
    d: 'A missing value indicator is a binary variable that «flags whether a given observation\'s value was missing», added when a variable has a large share of missing data (commonly used above ~10% missing) because missingness itself can be predictive.',
    how: 'For a variable with substantial missingness, create a 0/1 column marking which rows were missing, in addition to (or instead of) imputing the missing values.',
    ex: 'If donors who don\'t disclose income are also less likely to donate, a missing-income indicator captures that signal directly rather than letting it disappear into an imputed value.',
    src: SD_EDA_SRC,
  },
  {
    m: ['missing data', 'handling missing data', 'imputation'],
    d: 'Dropping every observation with any missing value is usually a bad idea: with p variables each missing at rate α independently, only «(1 − α)^p» of rows are fully complete — at 5% missingness across 30 variables, that\'s only about 21.5% of the data.',
    how: 'Rather than dropping incomplete rows, impute missing values (e.g., with the mean/median or a model-based estimate) and, for heavily-missing variables, add a missing value indicator alongside the imputed value.',
    ex: 'A model requiring complete data for every row (like a linear or logistic regression equation) cannot use a row with any missing input — which is exactly why dropping rows is so costly.',
    mk: 'Underestimating how much data is lost by dropping incomplete rows — missingness compounds multiplicatively across variables, not additively.',
    src: SD_EDA_SRC,
  },
  {
    m: ['outlier', 'outliers', 'iqr rule'],
    d: 'Outliers are data points «significantly different from the other observations» in a dataset; the IQR rule flags a point as an outlier if it falls «below Q1 − 1.5×IQR or above Q3 + 1.5×IQR».',
    how: 'Compute the first and third quartiles (Q1, Q3) and the interquartile range (IQR = Q3 − Q1), then flag any value outside Q1 − 1.5×IQR to Q3 + 1.5×IQR.',
    ex: 'A boxplot is a quick way to visualize the IQR rule\'s outlier boundaries for each numeric variable.',
    mk: 'Automatically deleting every flagged outlier — some "outliers" are legitimate, important extreme cases (e.g., a genuinely huge donation), not data errors.',
    src: SD_EDA_SRC,
  },
  {
    m: ['variable transformation', 'transforming skewed variables', 'skewness'],
    d: 'Transformations like the «log or square root» can reduce skewness in a variable, which matters for models that assume normality (like linear regression) — but predictive algorithmic models like trees or neural networks «do not require this assumption» and may not benefit from it.',
    how: 'Visualize each numeric variable\'s distribution (e.g., a histogram), and if it is heavily skewed and feeding an explanatory statistical model, try a log or square-root transform and check whether it improves model fit.',
    mk: 'Transforming skewed variables by habit before fitting a tree-based or neural-network model — those models don\'t require the normality assumption the transform is meant to satisfy, so it may not help and can sometimes hurt.',
    src: SD_EDA_SRC,
  },

  // ---- sd-data-mining-intro ----
  {
    m: ['classification (data mining task)', 'classification'],
    d: 'Classification «predicts a categorical target variable» from input features — common algorithms include decision trees, logistic regression, and support vector machines.',
    ex: 'Predicting whether a customer will purchase a product (yes/no), or whether a transaction is fraudulent, are both classification tasks.',
    src: SD_DM_INTRO_SRC,
  },
  {
    m: ['prediction (data mining task)', 'numeric prediction'],
    d: 'Prediction (in the data-mining sense) «predicts a numerical target variable» — techniques include linear regression, neural networks, and ensemble methods like random forests.',
    ex: 'Forecasting sales revenue or customer lifetime value is a numeric prediction task, as opposed to a yes/no classification task.',
    src: SD_DM_INTRO_SRC,
  },
  {
    m: ['association rules'],
    d: 'Association rules «identify relationships between items in transaction data», such as "if item A is purchased, item B is also likely purchased" — the technique behind "customers who bought this also bought that" recommenders.',
    how: 'Algorithms like Apriori or collaborative filtering scan transaction data for frequent co-occurring itemsets and turn them into if-then rules.',
    src: SD_DM_INTRO_SRC,
  },
  {
    m: ['data and dimension reduction', 'data reduction', 'dimension reduction (overview)'],
    d: 'Data and dimension reduction «simplifies a large dataset into a more manageable form» by reducing the number of variables (e.g., PCA) or the number of observations (e.g., clustering), easing both preprocessing and visualization.',
    src: SD_DM_INTRO_SRC,
  },
  {
    m: ['the data mining process', 'steps for machine learning', 'data mining process'],
    d: 'The data mining process runs from «understanding the project\'s purpose, through obtaining and exploring data, reducing dimensions, partitioning data, applying techniques, and assessing results, to deploying the model».',
    how: 'Work the steps roughly in order: define the goal, gather data, explore/preprocess/prepare it, reduce dimensions if needed, partition into training/test sets, train and tune models, evaluate results, then deploy and monitor.',
    mk: 'Jumping straight to "choose an algorithm" before clearly defining the project\'s purpose — without that, you can\'t tell if the model is even solving the right problem.',
    src: SD_DM_INTRO_SRC,
  },
  {
    m: ['training, test, and holdout partitions', 'train/test/holdout partition', 'holdout partition'],
    d: 'For supervised tasks, data is split into a «training set (used to build the model), and a test/holdout set (used to evaluate it on unseen data)» — this guards against overfitting by checking performance on data the model never saw during training.',
    ex: 'A churn model is trained on one set of customers and then evaluated on a separate holdout set whose true churn outcome is known but was withheld from training.',
    mk: 'Evaluating a model\'s performance only on the data it was trained on — that overstates how well it will perform on new, unseen data.',
    src: SD_DM_INTRO_SRC,
  },

  // ---- sd-dimension-reduction ----
  {
    m: ['curse of dimensionality'],
    d: 'The curse of dimensionality describes how, as the number of variables (p) grows for a fixed amount of data, «data points become sparse, distance metrics break down, and models become more prone to overfitting».',
    how: 'Watch for symptoms: proximity-based methods (like k-Nearest Neighbors) stop working well, and models with many predictors start fitting noise instead of signal.',
    ex: 'A k-Nearest Neighbors model that works well with 5 features can perform far worse with 500 features, even on the same underlying data, because "closeness" becomes harder to define.',
    src: SD_DIM_REDUCTION_SRC,
  },
  {
    m: ['data leakage'],
    d: 'Data leakage occurs when «information that would not be available at prediction time sneaks into the model», giving it an unfair advantage during training that doesn\'t hold up in the real world.',
    how: 'Check every predictor: could you actually know this value before the target is realized? And always split data into train/test before any transformation, imputation, or standardization is computed.',
    ex: 'Target leakage: using a variable derived from (or only known after) the outcome itself as a predictor. Train-test leakage: standardizing using the mean/SD of the full dataset, including the test set, before splitting.',
    mk: 'Computing standardization, imputation, or other preprocessing statistics on the full dataset before splitting into train/test — that leaks test-set information into training.',
    src: SD_DIM_REDUCTION_SRC,
  },
  {
    m: ['principal components analysis', 'principal component analysis', 'pca'],
    d: 'Principal Components Analysis (PCA) reduces dimensionality by creating «new variables (principal components) that are linear combinations of the original correlated variables», ordered so the first component captures the most variance in the data.',
    how: 'Standardize the data first (PCA is sensitive to scale), then compute components such that PC1 aligns with the direction of maximum variance, PC2 is orthogonal to PC1 and captures the next-most variance, and so on — then keep only the first k components.',
    ex: 'Reducing 50 highly correlated financial ratios down to 5 principal components that capture most of the original variance, before feeding them into a predictive model.',
    mk: 'Applying PCA to categorical or uncorrelated continuous data — PCA only helps when the original variables are continuous and correlated; on uncorrelated data there\'s no shared variance to compress.',
    src: SD_DIM_REDUCTION_SRC,
  },

  // ---- sd-model-evaluation ----
  {
    m: ['predictive accuracy vs. model fit', 'predictive accuracy', 'model fit'],
    d: 'Predictive accuracy and model fit are not the same thing: «R² and MSE computed on the training data measure how well the model fits the data it was built on, not how well it will perform on new data» — true predictive accuracy must be assessed on a holdout/validation sample.',
    mk: 'Reporting R² or MSE computed on the training data as evidence of how well a model will generalize — that conflates fit with predictive accuracy.',
    src: SD_MODEL_EVAL_SRC,
  },
  {
    m: ['naive benchmark'],
    d: 'A naive benchmark is the «simplest possible baseline model» a more complex model must beat to be worth using — for a continuous target, the simplest benchmark is just predicting the average (Ȳ) for every observation.',
    how: 'Before trusting a complex model, check that it actually outperforms the naive benchmark — R² itself is built around this idea, comparing prediction error to the error from always predicting the mean.',
    ex: 'If a regression model\'s R² is close to 0, it is barely beating the naive benchmark of predicting the average for every case.',
    src: SD_MODEL_EVAL_SRC,
  },
  {
    m: ['rmse', 'root mean squared error'],
    d: 'RMSE (Root Mean Squared Error), computed on the «holdout sample», measures the average magnitude of prediction error in the same units as the target — it gives a heavier penalty to large errors than MAE does.',
    how: 'Compute the square root of the average squared difference between actual and predicted values on the holdout set.',
    src: SD_MODEL_EVAL_SRC,
  },
  {
    m: ['mae', 'mean absolute error'],
    d: 'MAE (Mean Absolute Error) measures the «average magnitude of prediction errors without regard to their direction», and is less sensitive to large errors than RMSE.',
    how: 'Average the absolute value of (actual − predicted) across the holdout sample.',
    src: SD_MODEL_EVAL_SRC,
  },
  {
    m: ['cumulative gain', 'cumulative gains chart'],
    d: 'A cumulative gains chart compares a model\'s ranking performance to a random baseline by plotting, for the top X% of cases ranked by predicted value, the «cumulative actual outcome captured so far as a share of the total» — a model that ranks well bows well above the random-baseline diagonal.',
    how: 'Sort holdout cases from highest to lowest predicted value, break them into deciles, and at each cumulative depth compute the share of the total actual outcome captured so far.',
    ex: 'A car-pricing model used to decide which cars to sell first: the cumulative gains chart shows how much more revenue you capture by selling the top-ranked cars first, versus selling randomly.',
    src: SD_MODEL_EVAL_SRC,
  },
  {
    m: ['lift', 'decile lift', 'cumulative lift'],
    d: 'Lift, computed by ranked decile, is the «ratio of the average actual outcome in that decile to the average actual outcome across the whole holdout set» — a lift of 1.76 in the top decile means those cases are worth 1.76× the average.',
    how: 'Rank holdout cases by predicted value, split into deciles, then divide each decile\'s mean actual outcome by the overall mean actual outcome.',
    ex: 'If selling the top 10% of cars (ranked by predicted price) earns 1.76× the revenue of a random 10% sample, the lift for that decile is 1.76.',
    mk: 'Confusing lift (a per-decile ratio to the overall average) with cumulative gain (a running share of total captured outcome) — they answer related but different questions.',
    src: SD_MODEL_EVAL_SRC,
  },

  // ---- sd-regularized-regression ----
  {
    m: ['bias-variance tradeoff', 'bias variance tradeoff'],
    d: 'The bias-variance tradeoff describes how «adding uncorrelated predictors increases a model\'s variance, while dropping predictors correlated with the target increases its bias» — affecting nearly all machine learning models, not just regression.',
    how: 'Balance model complexity: too few predictors underfits (high bias), too many irrelevant predictors overfits (high variance) — variable selection and regularization both aim to find the sweet spot.',
    src: SD_REG_REGRESSION_SRC,
  },
  {
    m: ['stepwise selection', 'forward selection', 'backward selection'],
    d: 'Stepwise selection is a computationally efficient variable-selection method: «forward selection adds the next-best variable at each step, backward selection removes the next-worst variable, and stepwise selection combines both».',
    ex: 'R\'s built-in step() function can perform forward, backward, or combined stepwise selection on a fitted regression model.',
    src: SD_REG_REGRESSION_SRC,
  },
  {
    m: ['regularization', 'shrinkage'],
    d: 'Regularization (shrinkage) is a more flexible alternative to dropping variables outright: instead of setting a coefficient exactly to zero, it «shrinks all coefficients toward zero» by adding a penalty — based on the coefficients\' size — to the model-fitting objective.',
    how: 'Add a penalty term to the sum of squared errors (SSE) being minimized; as the tuning parameter λ increases from 0, coefficients shrink progressively toward zero, with λ chosen via cross-validation.',
    src: SD_REG_REGRESSION_SRC,
  },
  {
    m: ['ridge regression', 'l2 regularization'],
    d: 'Ridge regression minimizes SSE plus a penalty on «the sum of the squared regression coefficients» (L2 regularization) — shrinking coefficients toward zero without ever setting them exactly to zero.',
    src: SD_REG_REGRESSION_SRC,
  },
  {
    m: ['lasso regression', 'l1 regularization', 'lasso'],
    d: 'Lasso regression minimizes SSE plus a penalty on «the sum of the absolute values of the regression coefficients» (L1 regularization) — unlike ridge, this can shrink some coefficients exactly to zero, effectively performing variable selection.',
    mk: 'Forgetting the key practical difference from ridge: lasso\'s L1 penalty can zero out coefficients entirely, while ridge\'s L2 penalty only shrinks them toward (but not to) zero.',
    src: SD_REG_REGRESSION_SRC,
  },
  {
    m: ['k-fold cross validation', 'cross validation', 'cross-validation'],
    d: 'K-fold cross-validation partitions the training data into «k equally sized folds, using each fold once as the validation sample while training on the remaining k−1 folds», then averages performance across all k runs to get a more reliable estimate.',
    how: 'Split the data into k folds; for each of the k rounds, hold out one fold for validation and train on the rest; average the resulting performance metric across all k rounds.',
    ex: 'Cross-validation is exactly how the regularization tuning parameter λ is chosen: try a range of λ values and pick the one with the best average cross-validated performance.',
    src: SD_REG_REGRESSION_SRC,
  },

  // ---- sd-tree-models ----
  {
    m: ['overfitting (decision tree)', 'overfitting'],
    d: 'Overfitting occurs when a model is «too complex and captures noise instead of the underlying pattern» — decision trees are especially prone to this because they can keep splitting until nodes are tiny and tailored to the training sample.',
    how: 'Always evaluate a tree (or any model) on unseen holdout data, not just the training data, to detect overfitting before it reaches production.',
    mk: 'Judging a decision tree purely by how well it fits the training data — an overfit tree can look excellent there and perform far worse on new data.',
    src: SD_TREE_MODELS_SRC,
  },
  {
    m: ['recursive partitioning', 'decision tree', 'building a decision tree'],
    d: 'Recursive partitioning builds a decision tree by «repeatedly selecting the best split at each node — based on an impurity measure — and dividing the data accordingly», stopping when a stopping criterion (like minimum node size or pure nodes) is met.',
    how: 'At each node, evaluate every possible split of every predictor, pick the one that most reduces impurity, split the data into two branches, and repeat recursively on each new node until a stopping rule is hit.',
    ex: 'In the classic Riding Mowers example, the first split divides homeowners by income, then each resulting group is split again on its own best predictor.',
    src: SD_TREE_MODELS_SRC,
  },
  {
    m: ['gini index (decision tree)', 'gini index'],
    d: 'For a tree node, the Gini Index measures impurity as «1 minus the sum of squared class proportions» — it equals 0 when all records in a node belong to one class, and is maximized when classes are evenly mixed.',
    how: 'Compute 1 − Σ(p_k²) for the proportions p_k of each class in the node; the impurity of a split is the weighted average of the Gini Index of its two resulting nodes.',
    ex: 'A node split into two classes 50/50 has Gini Index 1 − (0.5² + 0.5²) = 0.5, the maximum possible for two classes; a pure node has Gini Index 0.',
    src: SD_TREE_MODELS_SRC,
  },
  {
    m: ['entropy (decision tree)', 'entropy'],
    d: 'Entropy is an alternative impurity measure to the Gini Index, defined as «minus the sum of each class proportion times its log-base-2» — it equals 1 when classes are evenly split (for a binary target) and approaches 0 as a node becomes pure.',
    how: 'Compute −Σ(p_k · log2(p_k)) for the class proportions p_k in the node, then compare the weighted average entropy before and after a candidate split to measure its information gain.',
    src: SD_TREE_MODELS_SRC,
  },
  {
    m: ['pruning a decision tree', 'pruning the tree (decision tree)'],
    d: 'Pruning mitigates a decision tree\'s overfitting by «successively turning a decision node back into a leaf node», trading off model fit against tree complexity — the best-practice way to choose how much to prune is cross-validation (via a complexity parameter).',
    mk: 'Forgetting that decision trees are sample-dependent — even with pruning, a small change in the training sample can produce a noticeably different tree structure.',
    src: SD_TREE_MODELS_SRC,
  },
  {
    m: ['variable importance (decision tree)', 'variable importance'],
    d: 'Variable importance in a decision tree measures «how much each predictor contributes to reducing impurity across all the splits where it was used», weighted by how many observations passed through those splits.',
    ex: 'In a loan-acceptance tree, Income, Education, and Family might emerge as the three most important predictors based on their total impurity-reduction contribution.',
    src: SD_TREE_MODELS_SRC,
  },

  // ---- sd-logistic-regression ----
  {
    m: ['logistic regression'],
    d: 'Logistic regression is a statistical method for a «binary response variable» — its predicted values are probabilities of class membership, and it can be used for explanatory modeling, profiling (which predictors distinguish the classes), or predictive classification.',
    ex: 'Predicting loan approval/disapproval, classifying customers as returning or non-returning, and finding factors that differentiate male and female executives (profiling) are all logistic-regression use cases.',
    src: SD_LOGISTIC_REGRESSION_SRC,
  },
  {
    m: ['logistic function', 'logistic regression model'],
    d: 'The logistic regression model replaces the linear-regression equation with «the logistic function — an S-shaped curve that maps any input to a value strictly between 0 and 1» — so predicted values are valid probabilities instead of potentially negative or over-1 values.',
    how: 'p = exp(β₀+β₁x₁)/(1+exp(β₀+β₁x₁)) = 1/(1+exp(−(β₀+β₁x₁))); as x→−∞ the curve approaches 0, and as x→+∞ it approaches 1.',
    mk: 'Fitting an ordinary linear regression to a 0/1 response variable — it can predict probabilities below 0 or above 1 and violates the normal-error assumptions that logistic regression is specifically designed to avoid.',
    src: SD_LOGISTIC_REGRESSION_SRC,
  },
  {
    m: ['odds (logistic regression)', 'odds'],
    d: 'Odds are not the same as probability: odds are «the ratio of the probability an event occurs to the probability it does not occur», ranging from 0 to infinity, while probability is bounded between 0 and 1.',
    ex: 'Odds of 1 (1:1) correspond to a 50% probability; odds of 2 (2:1) correspond to a 66.67% probability; odds of 0.5 (1:2) correspond to a 33.33% probability.',
    src: SD_LOGISTIC_REGRESSION_SRC,
  },
  {
    m: ['interpreting logistic regression coefficients', 'logistic regression coefficient interpretation'],
    d: 'In logistic regression, a coefficient β_i means that «the odds of belonging to class 1 change by a multiplicative factor of exp(β_i) for each one-unit increase in x_i», holding all other predictors constant — unlike linear regression, where the effect is additive, not multiplicative.',
    mk: 'Trying to interpret a logistic regression coefficient directly in terms of probability change — that change isn\'t constant, since it depends on the current values of all the other predictors; only the odds-ratio interpretation (exp(β_i)) is constant.',
    src: SD_LOGISTIC_REGRESSION_SRC,
  },
  {
    m: ['deviance (logistic regression)', 'goodness of fit (logistic regression)'],
    d: 'Overall goodness of fit for a logistic regression model is assessed by comparing «the residual deviance of the fitted model to the null deviance of the baseline (intercept-only) model» using a chi-square test — a significant difference means the model explains meaningfully more than the baseline.',
    mk: 'Assuming R\'s glm() summary() output reports the goodness-of-fit chi-square test statistic and p-value automatically — it doesn\'t; the null vs. residual deviance comparison must be calculated by hand.',
    src: SD_LOGISTIC_REGRESSION_SRC,
  },

  // ---- sd-text-mining ----
  {
    m: ['sentiment analysis', 'vader sentiment analyzer'],
    d: 'Sentiment analysis determines «the overall positive/negative sentiment behind a piece of text», typically using a lexicon-based scorer like NLTK\'s VADER, which rates each word\'s positivity/negativity and combines them into a compound score standardized between -1 and 1.',
    how: 'Score > 0 means the text\'s overall sentiment is positive, score < 0 means negative, and score = 0 means neutral.',
    mk: 'Trusting lexicon-based sentiment scoring to catch sarcasm — the lexicon approach is a fairly naive bag-of-words-style method and misses tone cues that depend on context.',
    src: SD_TEXT_MINING_SRC,
  },
  {
    m: ['bag of words', 'bag-of-words'],
    d: 'The bag-of-words approach represents a document by «counting each individual word\'s occurrences while ignoring grammar, word order, and sentence structure» — simplistic, but powerful enough to drive most classic text mining tasks.',
    mk: 'Assuming bag-of-words preserves meaning from word order or context — it deliberately throws that away; only word counts survive.',
    src: SD_TEXT_MINING_SRC,
  },
  {
    m: ['document-term matrix', 'dtm'],
    d: 'A document-term matrix (DTM) imposes a tabular structure on text: «rows are documents, columns are individual words (terms), and cells hold a frequency measure» — this turns unstructured text into a structured dataset usable by ordinary predictive models.',
    ex: 'Three short hotel-review documents become a table where each column is a word like "hotel" or "bad," and each cell counts how often that word appears in that document.',
    src: SD_TEXT_MINING_SRC,
  },
  {
    m: ['term frequency', 'tf (text mining)'],
    d: 'Term frequency (TF) measures «how often a word occurs within a single document» — as binary TF (present or not, good for short texts like tweets), absolute TF (raw count), or normalized TF (count divided by document length, which corrects for documents of different lengths).',
    src: SD_TEXT_MINING_SRC,
  },
  {
    m: ['inverse document frequency', 'idf'],
    d: 'Inverse document frequency (IDF) measures «how rare a word is across the whole corpus» — common words that appear in nearly every document (like "the") get a low IDF, while rare, more discriminating words get a high IDF boost.',
    how: 'IDF(word) = log2(1 / p(word)), where p(word) is the fraction of documents in the corpus containing that word.',
    mk: 'Relying on term frequency alone to judge a word\'s importance — a word like "the" can have high TF in every document yet carry no discriminating power; only IDF captures that.',
    src: SD_TEXT_MINING_SRC,
  },
  {
    m: ['tf-idf'],
    d: 'TF-IDF combines both signals: it\'s «term frequency multiplied by inverse document frequency», so a word scores highly only if it\'s frequent within a document AND rare across the corpus — one of the most popular text-weighting metrics for exactly that reason.',
    ex: 'In a SPAM classifier, a rare-but-telling word like "consignment" gets a higher TF-IDF weight than a common word like "the," making it more useful for the classification task.',
    src: SD_TEXT_MINING_SRC,
  },
  {
    m: ['text cleaning', 'stemming', 'stopwords'],
    d: 'Text cleaning prepares raw text for a document-term matrix by «removing punctuation and numbers, lowercasing, removing stopwords (common low-information words like "the" or "an"), and stemming (reducing words to their root, e.g. "playing" → "play")» — together these steps shrink the number of variables before analysis.',
    src: SD_TEXT_MINING_SRC,
  },
];