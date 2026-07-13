// Glossary entries for the "genai" deck. Each entry:
// { m: [matchers...], d: 'definition with «cloze phrases»', how, ex, we, mk, src: [{title,kind,ref}] }
// Grounded in backend/content-pipeline/extracted/... per backend/content-pipeline/taxonomy.mjs sourcePaths.
//
// sd-text-mining-spark — ISA 632 Module 3 "Text Mining on Spark"
const SD_TEXT_MINING_SPARK_SRC = [
  { title: 'ISA 632: Big Data Analytics & Modern AI — Text Mining on Spark', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3, Dr. Jay Shan)' },
];

// sd-spark-nlp-llm — ISA 632 Module 7 "Spark NLP & LLM"
const SD_SPARK_NLP_LLM_SRC = [
  { title: 'ISA 632: Big Data Analytics & Modern AI — Spark NLP & LLM', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 7, Dr. Jay Shan)' },
];

// sd-prompt-rag — ISA 632 Module 8 "GenAI (1) - Prompt Engineering & RAG"
const SD_PROMPT_RAG_SRC = [
  { title: 'ISA 632: Big Data Analytics & Modern AI — Generative AI: Prompt Engineering & RAG', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 8, Dr. Jay Shan)' },
];

// sd-genai-eval-deploy — ISA 632 Module 9 "GenAI (2) - Evaluation & Deployment"
const SD_GENAI_EVAL_DEPLOY_SRC = [
  { title: 'ISA 632: Big Data Analytics & Modern AI — Generative AI: Evaluation & Deployment', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 9, Dr. Jay Shan)' },
];

// sd-agentic-finetuning — ISA 632 Module 10 "GenAI (3) - Agentic AI & LLM Fine-Tuning"
const SD_AGENTIC_FINETUNING_SRC = [
  { title: 'ISA 632: Big Data Analytics & Modern AI — Generative AI: Agentic AI and LLM Fine-Tuning', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 10, Dr. Jay Shan)' },
];

export const GLOSSARY_genai = [
  {
    m: ['spark text mining pipeline', 'spark mllib text mining'],
    d: 'Spark MLlib has no dedicated text-mining module — text processing instead lives inside the general feature and clustering modules (pyspark.ml.feature), supporting «Tokenizer, StopWordsRemover, CountVectorizer (TF), TF-IDF, Word2Vec, and LDA» — a typical TF-IDF pipeline chains seven steps: tokenization, stopword removal, TF, IDF, feature assembling, label indexing, and predictive modeling.',
    src: SD_TEXT_MINING_SPARK_SRC,
  },
  {
    m: ['word embedding (spark)', 'why word embeddings'],
    d: 'Word embeddings exist because a simple Document-Term Matrix representation «doesn\'t capture relationships between words and produces high-dimensional, sparse representations» — embeddings instead learn dense, low-dimensional vector representations that preserve semantic and syntactic relationships between words.',
    ex: 'A DTM treats "Berlin" and "Germany" as two unrelated columns; a word embedding captures that they\'re related the same way "New York" and "U.S." are — a relationship a sparse term-count matrix can\'t represent.',
    mk: 'Assuming a Document-Term Matrix preserves meaningful relationships between words just because it counts them — DTM is purely a frequency count; word embeddings are specifically designed to capture semantic/syntactic relationships that frequency counts miss.',
    src: SD_TEXT_MINING_SPARK_SRC,
  },

  // ---- sd-spark-nlp-llm ----
  {
    m: ['spark nlp'],
    d: 'Spark NLP is «an open-source NLP library, originally developed by John Snow Labs, built on top of Apache Spark and Spark MLlib» — its key features are accuracy, scalability, and speed, and it lets a pipeline scale to any Spark cluster with zero code changes, since Spark itself handles execution planning, caching, serialization, and shuffling.',
    src: SD_SPARK_NLP_LLM_SRC,
  },
  {
    m: ['annotator approaches vs. models', 'spark nlp annotation'],
    d: 'Spark NLP pipelines are built from two kinds of stages: «Annotator Approaches, which require a training stage (fit(data) trains a model on data and produces an annotator model), and Annotator Models, which are Spark transformers (transform(data) takes a DataFrame and adds a new column containing the annotation result)» — every annotation result itself carries an annotatorType, begin/end position, the result text, metadata, and optional embeddings.',
    src: SD_SPARK_NLP_LLM_SRC,
  },
  {
    m: ['transformer architecture'],
    d: 'The Transformer architecture uses «an encoder-decoder structure: the encoder generates encodings capturing which parts of the input are relevant to each other, and the decoder uses those encodings\' contextual information to generate an output sequence» — it succeeded RNN/LSTM as the dominant deep learning architecture for NLP (RNN → LSTM → Transformer).',
    src: SD_SPARK_NLP_LLM_SRC,
  },
  {
    m: ['bert vs. gpt', 'bert', 'gpt'],
    d: 'BERT and GPT are both built on the Transformer, but use it differently: «BERT (Bidirectional Encoder Representations from Transformers) pre-trains the encoder on large-scale unlabeled data, then fine-tunes on labeled data for specific downstream tasks — while GPT (Generative Pre-Training) uses only the decoder, unidirectionally predicting the next word from left to right».',
    how: 'This maps to two different two-stage paradigms: BERT pairs pre-training with fine-tuning, while GPT pairs pre-training with zero-shot or few-shot prompting instead of fine-tuning.',
    ex: 'GPT scaled dramatically across versions — GPT (2018, open-source) → GPT-2 (2019, 1.5B parameters) → GPT-3 (175B parameters, 45TB of training text) → GPT-4 (1.5 trillion parameters).',
    mk: 'Assuming GPT uses the same encoder-based architecture as BERT — GPT uses only the decoder half of the Transformer; BERT uses only the encoder half.',
    src: SD_SPARK_NLP_LLM_SRC,
  },
  {
    m: ['issues of gpt-3', 'scaling does not equal alignment'],
    d: 'A core lesson from GPT-3\'s limitations is that «making language models bigger does not inherently make them better at following the user\'s intent» — GPT-3 still couldn\'t reliably understand instructions the way humans do, which motivated a shift toward fine-tuning with human feedback rather than purely scaling model size.',
    mk: 'Assuming a larger language model automatically becomes more aligned with what users actually want — scale improves raw capability, but alignment with user intent requires deliberate techniques like fine-tuning with human feedback.',
    src: SD_SPARK_NLP_LLM_SRC,
  },

  // ---- sd-prompt-rag ----
  {
    m: ['generative vs. predictive ai', 'generative ai'],
    d: 'Generative AI models differ fundamentally from predictive/discriminative models: predictive models «are trained on labeled data and learn the relationship between input features and output labels, used to classify or forecast» — generative models instead «understand the distribution of the training data and how likely a given example is, then generate new data similar to what they were trained on».',
    src: SD_PROMPT_RAG_SRC,
  },
  {
    m: ['base llm', 'autoregressive llm'],
    d: 'A base LLM is autoregressive: «it generates text by predicting the next token in a sequence based on the tokens that came before it, assigning each candidate next-token a probability» — the temperature parameter controls how that probability distribution is sampled, with values near 0 always picking the top-predicted token and higher values flattening the distribution toward more random, creative choices.',
    ex: 'Given "The garden was full of beautiful ___", a base LLM might assign "flowers" 0.5 probability, "trees" 0.23, and "herbs" 0.05 — low temperature reliably picks "flowers"; high temperature gives the less-likely options a real chance.',
    src: SD_PROMPT_RAG_SRC,
  },
  {
    m: ['prompt engineering', 'prompt components'],
    d: 'A prompt is «an input or query given to an LLM to elicit a specific response», and prompt engineering is «the practice of designing and refining prompts to optimize the model\'s responses» — a well-formed prompt typically combines four components: an instruction (what the model should do), context (background information), the input/question itself, and the desired output type/format.',
    how: 'Prompts are model-specific (different models may need different phrasing for the same task), and iterative development is key — adjusting temperature higher for creative tasks or lower for focused, accurate ones, while always checking for biased or hallucinated output.',
    mk: 'Assuming a prompt that works well on one LLM will transfer directly to another — prompts are model-specific, and what elicits a good response from one model may need rephrasing for another.',
    src: SD_PROMPT_RAG_SRC,
  },
  {
    m: ['retrieval augmented generation', 'rag'],
    d: 'RAG (Retrieval Augmented Generation) is a pattern that improves LLM applications by «retrieving documents relevant to a question or task and providing them as context to augment the prompt sent to the LLM» — the main problem it solves is the LLM\'s knowledge gap (it doesn\'t know about your private/custom/recent data), improving response accuracy, relevance, and reducing hallucinations without retraining the model.',
    ex: 'A company Q&A chatbot uses RAG to retrieve relevant passages from internal documentation before answering, so the LLM\'s response is grounded in the company\'s actual current policies rather than only what it learned during pre-training.',
    src: SD_PROMPT_RAG_SRC,
  },
  {
    m: ['rag workflow components', 'vector database'],
    d: 'A RAG pipeline chains several components: «(1) Index & Embed — an embedding model creates vector representations of documents and queries; (2) a Vector Store/Database holds those vectors for retrieval; (3) Retrieval finds relevant vectors via similarity search; (4) Filtering & Reranking selects/ranks the best matches; (5) Prompt Augmentation injects the retrieved content into the prompt; (6) Generation — the LLM produces the final response».',
    how: 'A vector database is specifically optimized to store and query high-dimensional embedding vectors, retrieving the vectors most similar to a query vector — this similarity search is what makes step 3 (Retrieval) computationally practical at scale.',
    mk: 'Treating "Retrieval" and "Generation" as the only two RAG steps — without Filtering & Reranking and Prompt Augmentation in between, irrelevant or noisy retrieved documents get dumped straight into the prompt, undermining the whole point of RAG.',
    src: SD_PROMPT_RAG_SRC,
  },

  // ---- sd-genai-eval-deploy ----
  {
    m: ['retrieval-related metrics (rag)', 'context precision', 'context relevance', 'context recall'],
    d: 'RAG retrieval is evaluated with three distinct metrics: «Context Precision (the signal-to-noise ratio of retrieved context — whether relevant chunks rank higher than irrelevant ones), Context Relevance (how well the retrieved context supports answering the query, without judging factual accuracy), and Context Recall (the extent to which all relevant information is actually retrieved, measured against ground truth)».',
    mk: 'Treating Context Relevance as a check on factual accuracy — it specifically measures whether retrieved context is on-topic for the query, not whether the eventual answer is correct.',
    src: SD_GENAI_EVAL_DEPLOY_SRC,
  },
  {
    m: ['generation-related metrics (rag)', 'faithfulness', 'answer relevancy', 'answer correctness'],
    d: 'RAG generation is evaluated with three distinct metrics: «Faithfulness (the factual accuracy of the generated answer relative to the retrieved context it was given), Answer Relevancy (how pertinent the response is to the user\'s actual query), and Answer Correctness (how the generated answer compares to ground truth, combining both semantic and factual similarity)».',
    how: 'Faithfulness and Answer Correctness sound similar but check different things: Faithfulness asks "does the answer match the context it was given" (catches hallucination relative to retrieved docs), while Answer Correctness asks "does the answer match the actual ground truth" (catches errors even if the context itself was good).',
    mk: 'Confusing Faithfulness (answer vs. the context provided) with Answer Correctness (answer vs. ground truth) — a response can be perfectly faithful to a flawed or incomplete retrieved context while still being factually wrong relative to ground truth.',
    src: SD_GENAI_EVAL_DEPLOY_SRC,
  },
  {
    m: ['evaluating the whole genai system', 'cost vs. performance vs. custom metrics'],
    d: 'Evaluating an entire GenAI system goes beyond retrieval/generation metrics to cover three categories: «cost metrics (resources and time consumed), performance metrics (direct and indirect business value), and custom metrics tailored to the specific use case» — and a full RAG pipeline should be evaluated both component-by-component (chunking, embedding model, vector store, retrieval/reranker, generator) and as an integrated whole.',
    src: SD_GENAI_EVAL_DEPLOY_SRC,
  },
  {
    m: ['review app (human feedback)', 'monitoring quality in production'],
    d: 'Beyond automated metrics, GenAI systems rely on human feedback collected via a Review App — «a pre-built feedback interface that lets stakeholders interact directly with the deployed agent and provide feedback» — and in production, the same evaluation scorers used during development are run automatically on live traces to continuously monitor quality, ensuring consistent evaluation criteria across both stages.',
    mk: 'Using different evaluation criteria in production monitoring than were used during development testing — that inconsistency makes it impossible to tell whether a quality change is a real regression or just a different yardstick.',
    src: SD_GENAI_EVAL_DEPLOY_SRC,
  },
  {
    m: ['mosaic ai gateway', 'production-grade model serving'],
    d: 'Deploying a GenAI model into production at scale requires dedicated infrastructure: production-grade serving provides «highly available, low-latency, scalable serving for small and large workloads», while a centralized gateway layer adds governance features like «usage tracking and observability, payload logging for debugging, unified guardrails such as PII detection for compliance, and support for A/B testing and traffic policies».',
    ex: 'Payload logging captures every request/response pair in a governed catalog, so a team can later debug exactly why the model gave a problematic answer to a specific user query.',
    src: SD_GENAI_EVAL_DEPLOY_SRC,
  },

  // ---- sd-agentic-finetuning ----
  {
    m: ['prompting framework progression', 'zero-shot, multi-shot, chain-of-thought'],
    d: 'Prompting frameworks form a progression of increasing guidance: «zero-shot (ask directly, relying entirely on the model\'s pre-trained knowledge with no examples — works for common, well-defined tasks but fails on specialized formats), multi-shot (include 2-5 worked examples before the actual query, significantly improving accuracy on tasks needing a specific format or reasoning style), and Chain-of-Thought (guide the model to reason step-by-step through intermediate steps before the final answer, reducing errors on multi-step problems)».',
    ex: 'Triggering Chain-of-Thought reasoning can be as simple as adding "Think step by step" to the prompt, or showing a worked example with explicit intermediate reasoning.',
    mk: 'Defaulting to zero-shot prompting for a task that needs a very specific output format — zero-shot relies entirely on the model\'s general training and has no way to learn a custom format from the prompt alone; multi-shot examples are needed for that.',
    src: SD_AGENTIC_FINETUNING_SRC,
  },
  {
    m: ['react framework'],
    d: 'The ReAct framework combines reasoning and acting in an iterative loop: «Thought (reason about what to do next) → Action (call a tool — search, API, code) → Observation (read the tool\'s output and decide the next step)» — this loop repeats until the task is complete, enabling dynamic, tool-grounded reasoning rather than a single fixed response.',
    src: SD_AGENTIC_FINETUNING_SRC,
  },
  {
    m: ['agentic vs. non-agentic workflows'],
    d: 'Non-agentic (static) workflows use «hardcoded prompt-response pipelines with deterministic actions», while agentic (dynamic, iterative) workflows feature «AI-driven planning and execution, tool calling by the AI itself, non-deterministic actions, and iterative refinement» — the agentic approach trades predictability for the ability to handle open-ended, multi-step tasks a fixed pipeline can\'t anticipate.',
    src: SD_AGENTIC_FINETUNING_SRC,
  },
  {
    m: ['agent planning', 'agent reflection'],
    d: 'An autonomous agent\'s reasoning splits into planning (four steps: «goal definition, task decomposition into sub-tasks, action sequencing to determine operation order and dependencies, and monitor & adapt»), and reflection — a separate loop of «Action → Outcome → Reflection (analyze what worked and why) → Adjustment (refine strategy for the next iteration)» that lets the agent self-correct without human intervention.',
    src: SD_AGENTIC_FINETUNING_SRC,
  },
  {
    m: ['llm fine-tuning', 'pre-training vs. fine-tuning'],
    d: 'LLM fine-tuning is «the process of taking a pre-trained LLM and continuing its training on a targeted, task-specific labeled dataset» — pre-training builds general language understanding from massive unlabeled data using hundreds of GPUs over months, while fine-tuning builds domain expertise and task accuracy from high-quality labeled data using only a few GPUs over hours to days.',
    ex: 'A general-purpose LLM like ChatGPT works well for demos but isn\'t secure or specialized enough for enterprise use on proprietary data — fine-tuning is how an enterprise adapts a pre-trained model to its own domain and data while keeping deployment secure.',
    mk: 'Jumping straight to fine-tuning before establishing a baseline, a test set, and a simpler alternative to compare against — fine-tuning is expensive and risky, so it should be justified by evidence that simpler approaches (prompting, RAG) aren\'t sufficient.',
    src: SD_AGENTIC_FINETUNING_SRC,
  },
  {
    m: ['full fine-tuning vs. peft', 'parameter-efficient fine-tuning', 'lora'],
    d: 'Full fine-tuning «updates all or most of a model\'s weights — powerful but expensive and harder to manage». Parameter-Efficient Fine-Tuning (PEFT) instead «trains only a small number of extra parameters while freezing the pretrained weights», motivated by the cost of full fine-tuning (a separate full copy of a 7B model costs ~14GB per task). LoRA (Low-Rank Adaptation) is the most common PEFT method: «it injects small trainable low-rank matrices into selected transformer layers while leaving the original model mostly unchanged».',
    how: 'PEFT/LoRA\'s benefits are lower memory requirements and better throughput, since you\'re training a tiny fraction of the parameters a full fine-tune would touch — at some cost to maximum achievable performance compared to full fine-tuning.',
    mk: 'Assuming PEFT/LoRA always matches full fine-tuning\'s performance ceiling — PEFT trades some customization power for dramatically lower cost; full fine-tuning is still preferred when performance gains justify the extra cost and risk.',
    src: SD_AGENTIC_FINETUNING_SRC,
  },
];