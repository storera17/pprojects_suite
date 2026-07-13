// Glossary entries for the "python-data" deck. Each entry:
// { m: [matchers...], d: 'definition with «cloze phrases»', how, ex, we, mk, src: [{title,kind,ref}] }
// Grounded in backend/content-pipeline/extracted/... per backend/content-pipeline/taxonomy.mjs sourcePaths.
//
// sd-python — ISA 514 Module 2 "Python Programming (I): Basics" and
// Module 3 "Python Programming (II): Data Wrangling"
const SD_PYTHON_SRC = [
  { title: 'ISA 514: Managing Big Data — Python Programming I (Basics)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2, Dr. Jay Shan, citing Python for Everybody)' },
  { title: 'ISA 514: Managing Big Data — Python Programming II (Data Wrangling)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3, Dr. Jay Shan, citing the Python Data Science Handbook)' },
];

// sd-web-api — ISA 514 Module 4 "Data Collection from Web API"
const SD_WEB_API_SRC = [
  { title: 'ISA 514: Managing Big Data — Data Collection from Web API', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 4, Dr. Jay Shan)' },
];

// sd-nosql — ISA 514 Module 5 "NoSQL Database" (MongoDB Basics)
const SD_NOSQL_SRC = [
  { title: 'ISA 514: Managing Big Data — NoSQL Database (MongoDB Basics)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 5, Dr. Jay Shan)' },
];

export const GLOSSARY_python_data = [
  {
    m: ['python list'],
    d: 'A Python list is «an ordered, mutable collection that holds many values in a single variable» — you can concatenate lists with +, add elements with .append(), and slice them with [start:stop] (where stop is "up to but not including").',
    ex: 'friends[1:3] returns the elements at index 1 and 2 (not 3) from the friends list.',
    src: SD_PYTHON_SRC,
  },
  {
    m: ['python dictionary'],
    d: 'A Python dictionary is «a "bag" of values, each labeled with its own key instead of a numeric index» — enabling fast, database-like lookups; .get(key, default) is the idiomatic way to safely read a key that might not exist yet, often used for counting occurrences.',
    ex: 'counts[name] = counts.get(name, 0) + 1 increments a running count for each name, defaulting to 0 the first time a name is seen.',
    src: SD_PYTHON_SRC,
  },
  {
    m: ['python tuple'],
    d: 'A Python tuple is «like a list, but immutable (cannot be altered) once created» — more efficient than a list, often preferred for temporary variables, and the only one of the two that can be compared element-by-element or unpacked directly into multiple variables on the left of an assignment.',
    ex: '(a, b) = (99, 98) unpacks a tuple directly into two variables; the dictionary .items() method returns its key-value pairs as a list of tuples.',
    mk: 'Trying to modify a tuple in place (e.g., reassigning one of its elements) — tuples are immutable by design; use a list if you need to mutate the collection.',
    src: SD_PYTHON_SRC,
  },
  {
    m: ['crisp-dm'],
    d: 'CRISP-DM (Cross-Industry Standard Process for Data Mining) is a six-step data mining process — «Business Understanding, Data Understanding, Data Preparation, Model Building, Testing and Evaluation, and Deployment» — that is highly repetitive and experimental in practice, not a strict linear pipeline.',
    how: 'Data Preparation alone accounts for roughly 85% of total project time in a typical data mining project — by far the most time-consuming step.',
    mk: 'Treating CRISP-DM as a one-pass linear sequence — in practice you constantly loop back to earlier steps (e.g., back to data understanding) as you learn more.',
    src: SD_PYTHON_SRC,
  },
  {
    m: ['numpy', 'ndarray'],
    d: 'NumPy provides «the ndarray object for storing and manipulating multidimensional numerical arrays, with vectorized (element-wise) arithmetic operations that significantly outperform plain Python loops» — many other libraries, including Pandas, are built directly on top of NumPy.',
    src: SD_PYTHON_SRC,
  },
  {
    m: ['pandas dataframe', 'dataframe'],
    d: 'A Pandas DataFrame is «like a NumPy array but with labeled rows and columns», providing SQL-like tools for reshaping, merging, sorting, slicing, grouping/aggregating, and handling missing data.',
    how: 'DataFrame operations map closely onto SQL: SELECT attr1, attr2 becomes df[[\'attr1\', \'attr2\']]; WHERE becomes boolean filtering like df[df[\'attr1\'] > 3]; GROUP BY becomes df.groupby([...]); ORDER BY becomes df.sort_values(by=[...]).',
    ex: 'SELECT AVG(attr1) in SQL corresponds to df[\'attr1\'].mean() in Pandas.',
    src: SD_PYTHON_SRC,
  },

  // ---- sd-web-api ----
  {
    m: ['web api', 'rest', 'restful'],
    d: 'A Web API (web service) lets software request data over the web following a protocol — most commonly «REST, which uses standard HTTP methods (GET, POST, PUT, DELETE) to retrieve, create, replace, or delete a resource» — with responses typically returned in JSON or XML.',
    how: 'GET retrieves an element or lists a collection, POST creates a new entry, PUT replaces an existing element, and DELETE removes an element — the same HTTP verbs used for ordinary web pages, applied to data resources instead.',
    ex: 'Requesting https://api.nytimes.com/svc/search/v2/articlesearch.json with a GET is conceptually identical to requesting any other web page — the response is just structured data instead of HTML.',
    src: SD_WEB_API_SRC,
  },
  {
    m: ['api key', 'api authorization'],
    d: 'An API key (or token) is «the credential a Web API requires to authorize a request» — most APIs deny access entirely without one, and it\'s typically passed as a key-value pair in the URL\'s query string.',
    ex: 'A request missing its key returns an error like "Failed to resolve API Key variable" — adding ?api-key=YOUR_KEY to the URL authorizes the request.',
    mk: 'Assuming every Web API is free and unlimited — many cap free usage (e.g., 500 calls/day) and require payment for higher volume or extra functionality.',
    src: SD_WEB_API_SRC,
  },
  {
    m: ['json'],
    d: 'JSON (JavaScript Object Notation) is a textual, language-independent data-interchange format built from two structures: «objects — unordered key/value pairs wrapped in { } — and arrays — ordered lists of values wrapped in [ ]» — and the two can nest inside each other to represent arbitrarily complex data.',
    how: 'The clearest way to interpret a JSON response is to read it as a hierarchical tree, since objects and arrays can be nested many levels deep.',
    ex: '{"name": "Jay", "dept": "ISA"} is a JSON object; ["Rick", "Michonne", "Negan"] is a JSON array; combining them lets a key like "menuitem" hold an array of objects, each with its own key/value pairs.',
    src: SD_WEB_API_SRC,
  },
  {
    m: ['xml'],
    d: 'XML is another data format (alongside JSON) for representing data with «a hierarchical, nested structure» — used by some web services and many legacy data exchange systems instead of JSON.',
    src: SD_WEB_API_SRC,
  },

  // ---- sd-nosql ----
  {
    m: ['nosql', 'kinds of nosql', 'nosql database'],
    d: 'NoSQL refers to a «class of non-relational data storage systems that don\'t use SQL as their query language and must scale well to very large sizes» — it complements rather than replaces a relational database, and comes in several kinds: key-value, graph, document-oriented, and column-family stores, each targeted at a different niche.',
    mk: 'Treating different NoSQL databases as interchangeable — a key-value store, a graph database, and a document store are built for very different access patterns and generally aren\'t drop-in substitutes for each other.',
    src: SD_NOSQL_SRC,
  },
  {
    m: ['document-oriented database', 'document database', 'mongodb'],
    d: 'A document-oriented database «stores documents (often JSON-like, semi-structured text) rather than relational tables», making it highly efficient for unstructured/textual data — MongoDB is the most common example, using flexible JSON-like schemas and supporting replication, load balancing, and easy integration with big data platforms like Spark.',
    src: SD_NOSQL_SRC,
  },
  {
    m: ['mongodb vs rdbms terminology', 'collection (mongodb)', 'document (mongodb)'],
    d: 'MongoDB and a relational database (RDBMS) use parallel but distinct vocabulary for similar concepts: «a MongoDB Collection corresponds to an RDBMS Table, a Document corresponds to a Row, a Field corresponds to a Column, an Embedded Document corresponds to a Join, a Reference corresponds to a Foreign Key, and a Shard corresponds to a Partition».',
    mk: 'Assuming MongoDB documents must follow a fixed schema the way RDBMS rows do — MongoDB\'s schema is flexible by design; different documents in the same collection can have different fields.',
    src: SD_NOSQL_SRC,
  },
];