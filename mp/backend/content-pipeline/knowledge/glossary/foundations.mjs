// Glossary entries for the "foundations" deck. Each entry:
// { m: [matchers...], d: 'definition with «cloze phrases»', how, ex, we, mk, src: [{title,kind,ref}] }
// Grounded in backend/content-pipeline/extracted/... per backend/content-pipeline/taxonomy.mjs sourcePaths.
//
// sd-ai-overview — ISA 591 "Background Vocabulary" pre-term review
// (backend/content-pipeline/extracted/isa591/Module 0 - Pre-Term Review Material/).
const SD_AI_OVERVIEW_SRC = [
  { title: 'ISA 591: Data Mining — Background Vocabulary (pre-term review)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 0)' },
];

// sd-bigdata-overview — ISA 514 "Big Data Overview and Course Introduction" lecture (Module 1)
const SD_BIGDATA_OVERVIEW_SRC = [
  { title: 'ISA 514: Managing Big Data — Big Data Overview lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1, Dr. Jay Shan)' },
];

export const GLOSSARY_foundations = [
  {
    m: ['business analytics'],
    d: 'Business analytics is «the process of transforming data into insights for informed decision-making», driving efficiency, innovation, and competitive advantage.',
    how: 'Move from raw data to a decision by passing through description (what happened), prediction (what will happen), and prescription (what to do about it).',
    ex: 'Supply chain optimization, customer segmentation, and risk assessment are all business analytics applications.',
    src: SD_AI_OVERVIEW_SRC,
  },
  {
    m: ['descriptive analytics'],
    d: 'Descriptive analytics «analyzes historical data to understand what has happened», providing context and trends rather than forecasts or recommendations.',
    ex: 'Sales reports and web traffic analysis are classic descriptive analytics outputs.',
    mk: 'Treating a descriptive report (what happened) as if it tells you what will happen or what to do next — those are predictive and prescriptive questions.',
    src: SD_AI_OVERVIEW_SRC,
  },
  {
    m: ['predictive analytics'],
    d: 'Predictive analytics «uses models to predict future outcomes», anticipating trends and behaviors rather than just summarizing the past.',
    ex: 'Demand forecasting and churn prediction are typical predictive analytics applications.',
    src: SD_AI_OVERVIEW_SRC,
  },
  {
    m: ['business intelligence', 'bi vs. business analytics', 'bi vs business analytics'],
    d: 'Business intelligence (BI) «focuses on historical data and reporting», while business analytics (BA) extends that with predictive and prescriptive elements like forecasting and optimization.',
    how: 'Both BI and BA leverage data for insight, but BI stops at describing the past while BA also models the future and recommends actions.',
    mk: 'Treating "BI" and "BA" as interchangeable — a dashboard of historical KPIs is BI; a model that forecasts next quarter and recommends an action is BA.',
    src: SD_AI_OVERVIEW_SRC,
  },
  {
    m: ['data science vs. business analytics', 'data science vs business analytics'],
    d: 'Data science is «more technical, focused on algorithms and model development», while business analytics «emphasizes business context and impact» — both analyze data, but with different tools and end goals.',
    src: SD_AI_OVERVIEW_SRC,
  },
  {
    m: ['big data'],
    d: 'Big data refers to «large, complex datasets that require advanced tools» to analyze, characterized by the "five Vs": «Volume, Variety, Velocity, Veracity, and Value».',
    how: 'Check whether traditional data analysis tools (e.g., a spreadsheet) can no longer handle the size, speed, or variety of the data — if not, you are in big-data territory.',
    ex: 'A retailer streaming millions of point-of-sale transactions per hour across hundreds of stores, in multiple formats, needs big-data tools rather than a single spreadsheet.',
    src: SD_AI_OVERVIEW_SRC,
  },
  {
    m: ['data-driven decision making', 'data driven decision making'],
    d: 'Data-driven decision making means «using data to guide actions and strategies» rather than relying on intuition alone, which reduces bias and improves outcomes.',
    ex: 'Dynamic pricing and performance dashboards are common data-driven decision making tools.',
    src: SD_AI_OVERVIEW_SRC,
  },
  {
    m: ['supervised learning'],
    d: 'Supervised learning is a type of machine learning where the model is «trained on labeled data» — inputs paired with known outputs.',
    ex: 'Training a churn model on past customers where the outcome (churned or not) is already known is supervised learning.',
    src: SD_AI_OVERVIEW_SRC,
  },
  {
    m: ['unsupervised learning'],
    d: 'Unsupervised learning is a type of machine learning where the model «learns patterns and structures from unlabeled data» — there is no known output to predict.',
    ex: 'Clustering customers into segments without any predefined labels is unsupervised learning.',
    mk: 'Assuming unsupervised learning can be evaluated the same way as supervised learning — without ground-truth labels, there is no simple "accuracy" to compute.',
    src: SD_AI_OVERVIEW_SRC,
  },

  // ---- sd-bigdata-overview ----
  {
    m: ['volume, variety, velocity', 'three vs of big data', 'why is big data happening'],
    d: 'Big data is happening because current data is «easy to collect, cheap to store, and abundant» — and what makes it "big" isn\'t size alone but three dimensions: «Volume (more data), Variety (more unstructured/heterogeneous formats like text, images, video), and Velocity (the speed data must be created, stored, and analyzed)».',
    ex: 'A Google search immediately triggering a related ad on Facebook is an example of velocity — data captured and acted on in near real time.',
    src: SD_BIGDATA_OVERVIEW_SRC,
  },
  {
    m: ['big data analytics challenges', 'challenges of big data analytics'],
    d: 'Big data analytics faces two core challenges: «data volume and integration — capturing, storing, and combining huge amounts of data quickly and cost-effectively» — and «processing capabilities — handling unstructured data and processing it in near real time» via parallel/in-memory processing or stream analytics.',
    src: SD_BIGDATA_OVERVIEW_SRC,
  },
  {
    m: ['big data management technologies', 'computing clusters', 'distributed storage'],
    d: 'Modern big data management relies on «computing clusters, distributed storage (e.g., Hadoop HDFS), parallel/distributed analytics paradigms (e.g., Spark), and cloud computing platforms (e.g., AWS)» to collect, store, and analyze data sets too large or unstructured for a single machine.',
    src: SD_BIGDATA_OVERVIEW_SRC,
  },
];