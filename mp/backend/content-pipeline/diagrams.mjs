// Original Jarvis-styled SVG diagrams with labeled, occludable regions.
// Diagrams are generated from declarative specs (no copyrighted assets).
// Each region {id,label,x,y,w,h} can be masked for image-occlusion cards.

const W = 720, H = 420;
const FG = '#9be8f7', DIM = '#3a7d96', BG = '#071826', GLOW = '#19b8e0';

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function nodeSvg(n) {
  const lines = String(n.label).split('\n');
  const lh = 15;
  const ty = n.y + n.h / 2 - ((lines.length - 1) * lh) / 2;
  const text = lines
    .map((l, i) => `<text x="${n.x + n.w / 2}" y="${ty + i * lh}" fill="${n.accent ? '#ffd97a' : FG}" font-size="12.5" text-anchor="middle" dominant-baseline="middle" font-family="Segoe UI, sans-serif">${esc(l)}</text>`)
    .join('');
  return `<rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="9" fill="${n.fill || 'rgba(20,60,84,0.55)'}" stroke="${n.accent ? '#ffd97a' : GLOW}" stroke-width="1.3"/>${text}`;
}

function edgeSvg(e, nodes) {
  const a = nodes.find((n) => n.id === e[0]);
  const b = nodes.find((n) => n.id === e[1]);
  if (!a || !b) return '';
  const ax = a.x + a.w / 2, ay = a.y + a.h / 2, bx = b.x + b.w / 2, by = b.y + b.h / 2;
  // Trim line ends to node borders (approximate, axis-dominant).
  const dx = bx - ax, dy = by - ay;
  const horiz = Math.abs(dx) > Math.abs(dy);
  const x1 = horiz ? ax + Math.sign(dx) * a.w / 2 : ax;
  const y1 = horiz ? ay : ay + Math.sign(dy) * a.h / 2;
  const x2 = horiz ? bx - Math.sign(dx) * b.w / 2 : bx;
  const y2 = horiz ? by : by - Math.sign(dy) * b.h / 2;
  const lbl = e[2]
    ? `<text x="${(x1 + x2) / 2}" y="${(y1 + y2) / 2 - 6}" fill="${DIM}" font-size="10.5" text-anchor="middle" font-family="Segoe UI, sans-serif">${esc(e[2])}</text>`
    : '';
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${DIM}" stroke-width="1.4" marker-end="url(#arr)"/>${lbl}`;
}

/** Compose a themed SVG from a spec {title, nodes, edges, extra}. */
export function composeSvg(spec) {
  const nodes = spec.nodes || [];
  const body =
    (spec.extra || '') +
    (spec.edges || []).map((e) => edgeSvg(e, nodes)).join('') +
    nodes.map(nodeSvg).join('');
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" font-family="Segoe UI, sans-serif">` +
    `<defs><marker id="arr" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L8,4L0,8z" fill="${DIM}"/></marker>` +
    `<radialGradient id="bgg" cx="50%" cy="40%" r="80%"><stop offset="0%" stop-color="#0b2538"/><stop offset="100%" stop-color="${BG}"/></radialGradient></defs>` +
    `<rect width="${W}" height="${H}" fill="url(#bgg)" rx="12"/>` +
    `<text x="${W / 2}" y="28" fill="${FG}" font-size="16" text-anchor="middle" letter-spacing="2">${esc(spec.title.toUpperCase())}</text>` +
    `<line x1="40" y1="40" x2="${W - 40}" y2="40" stroke="${DIM}" stroke-width="0.7" opacity="0.6"/>` +
    body +
    `</svg>`
  );
}

const N = (id, label, x, y, w = 120, h = 44, opts = {}) => ({ id, label, x, y, w, h, ...opts });

// ---------------------------------------------------------------------------
// Diagram specs. Every node listed in `occlude` becomes a maskable region.
// ---------------------------------------------------------------------------
const SPECS = [
  {
    id: 'confusion-matrix', title: 'Confusion Matrix',
    match: /confusion matrix|sensitivity|specificity|precision\b|recall\b|true positive|false positive|false negative|f1|classification matrix|misclassification/i,
    nodes: [
      N('tp', 'True Positive\n(hit)', 250, 110, 150, 70, { fill: 'rgba(28,110,80,0.5)' }),
      N('fp', 'False Positive\n(Type I error)', 420, 110, 150, 70, { fill: 'rgba(120,50,50,0.5)' }),
      N('fn', 'False Negative\n(Type II error)', 250, 200, 150, 70, { fill: 'rgba(120,50,50,0.5)' }),
      N('tn', 'True Negative\n(correct reject)', 420, 200, 150, 70, { fill: 'rgba(28,110,80,0.5)' }),
      N('sens', 'Sensitivity / Recall\nTP ÷ (TP+FN)', 80, 300, 190, 52),
      N('prec', 'Precision\nTP ÷ (TP+FP)', 290, 300, 160, 52),
      N('spec', 'Specificity\nTN ÷ (TN+FP)', 470, 300, 170, 52),
    ],
    extra: `<text x="325" y="95" fill="${FG}" font-size="12" text-anchor="middle">Predicted +</text><text x="495" y="95" fill="${FG}" font-size="12" text-anchor="middle">Predicted −</text><text x="215" y="145" fill="${FG}" font-size="12" text-anchor="end">Actual +</text><text x="215" y="235" fill="${FG}" font-size="12" text-anchor="end">Actual −</text>`,
    occlude: ['tp', 'fp', 'fn', 'tn', 'sens', 'prec', 'spec'],
  },
  {
    id: 'nn-architecture', title: 'Neural Network Anatomy',
    match: /neural network|input layer|hidden layer|output layer|flow of information|components of the neural|shallow neural|deep neural|nn model|activation function|where are activation/i,
    nodes: [
      N('input', 'Input layer\n(features)', 70, 150, 130, 64),
      N('hidden', 'Hidden layer(s)\nweights + activation', 290, 150, 160, 64),
      N('output', 'Output layer\n(prediction)', 520, 150, 140, 64),
      N('loss', 'Loss function\nmeasures error', 520, 280, 140, 52),
      N('back', 'Backpropagation\nupdates weights', 250, 280, 170, 52),
    ],
    edges: [['input', 'hidden', 'weighted sums'], ['hidden', 'output'], ['output', 'loss'], ['loss', 'back', 'gradients'], ['back', 'hidden']],
    occlude: ['input', 'hidden', 'output', 'loss', 'back'],
  },
  {
    id: 'star-schema', title: 'Star Schema',
    match: /star schema|fact table|dimension table|data model(ing)? using power bi|relationships|cardinality|snowflake schema/i,
    nodes: [
      N('fact', 'FACT Sales\nkeys + measures', 290, 160, 150, 80, { accent: true }),
      N('dimd', 'Dim Date', 90, 80, 120, 46),
      N('dimp', 'Dim Product', 510, 80, 130, 46),
      N('dimc', 'Dim Customer', 90, 280, 130, 46),
      N('dims', 'Dim Store', 510, 280, 120, 46),
    ],
    edges: [['dimd', 'fact', '1 → many'], ['dimp', 'fact', '1 → many'], ['dimc', 'fact', '1 → many'], ['dims', 'fact', '1 → many']],
    occlude: ['fact', 'dimd', 'dimp', 'dimc', 'dims'],
  },
  {
    id: 'dax-context', title: 'DAX Evaluation Context',
    match: /evaluation context|filter context|row context|context transition|calculate function|filter propagation|calculate and|nesting row/i,
    nodes: [
      N('filter', 'FILTER CONTEXT\nfrom slicers, rows,\ncolumns of the report', 80, 110, 190, 80),
      N('row', 'ROW CONTEXT\nfrom iterators and\ncalculated columns', 450, 110, 190, 80),
      N('calc', 'CALCULATE\ntransforms row context\ninto filter context', 265, 250, 200, 80, { accent: true }),
    ],
    edges: [['row', 'calc', 'context transition'], ['calc', 'filter', 'modifies']],
    occlude: ['filter', 'row', 'calc'],
  },
  {
    id: 'hadoop-ecosystem', title: 'Hadoop Ecosystem',
    match: /hadoop|hdfs|yarn|name node|data node|block file|hive\b|sqoop/i,
    nodes: [
      N('hdfs', 'HDFS\ndistributed storage\n(replicated blocks)', 80, 250, 180, 70),
      N('yarn', 'YARN\nresource negotiator', 290, 250, 160, 70),
      N('mr', 'MapReduce / Spark\ndistributed compute', 480, 250, 170, 70),
      N('hive', 'Hive\nSQL on Hadoop', 130, 120, 140, 52),
      N('sqoop', 'Sqoop\nRDBMS ingest', 300, 120, 140, 52),
      N('nn', 'Name node = metadata\nData nodes = blocks', 470, 120, 180, 52),
    ],
    edges: [['hive', 'mr'], ['sqoop', 'hdfs'], ['yarn', 'mr', 'allocates'], ['nn', 'hdfs']],
    occlude: ['hdfs', 'yarn', 'mr', 'hive', 'sqoop', 'nn'],
  },
  {
    id: 'mapreduce-flow', title: 'MapReduce Flow',
    match: /mapreduce|mapper|reducer|sort and shuffle|map reduce/i,
    nodes: [
      N('inp', 'Input splits\n(blocks on HDFS)', 60, 160, 140, 60),
      N('map', 'MAP\nkey→value pairs\nruns where data lives', 230, 160, 160, 60),
      N('shuf', 'SORT & SHUFFLE\ngroup by key\nacross the network', 420, 160, 160, 60, { accent: true }),
      N('red', 'REDUCE\naggregate per key', 60, 300, 160, 56),
      N('out', 'Output\nresults to HDFS', 280, 300, 150, 56),
    ],
    edges: [['inp', 'map'], ['map', 'shuf'], ['shuf', 'red'], ['red', 'out']],
    occlude: ['map', 'shuf', 'red'],
  },
  {
    id: 'spark-architecture', title: 'Spark Architecture',
    match: /spark architecture|driver|executor|cluster manager|stages?\b.*tasks?|wide transformation|narrow transformation|lazy evaluation|rdd|partition/i,
    nodes: [
      N('driver', 'DRIVER\nplans jobs → stages → tasks\n(lazy until an action)', 250, 90, 220, 70, { accent: true }),
      N('cm', 'Cluster manager\nallocates resources', 40, 200, 170, 56),
      N('e1', 'Executor 1\ntasks on partitions', 250, 220, 150, 56),
      N('e2', 'Executor 2\ntasks on partitions', 420, 220, 150, 56),
      N('shuffle', 'SHUFFLE\nwide transformations\nmove data between stages', 250, 320, 220, 64),
    ],
    edges: [['driver', 'cm'], ['driver', 'e1'], ['driver', 'e2'], ['e1', 'shuffle'], ['e2', 'shuffle']],
    occlude: ['driver', 'cm', 'e1', 'shuffle'],
  },
  {
    id: 'rag-pipeline', title: 'RAG Pipeline',
    match: /rag pipeline|rag idea|context injection|why do we need rag|vector database|vector index|text embedding|sentence embedding|word embedding|semantic space|grounding/i,
    nodes: [
      N('docs', 'Documents\nchunked', 50, 120, 120, 56),
      N('embed', 'Embedding model\ntext → vectors', 210, 120, 150, 56),
      N('vdb', 'Vector database\nsimilarity index', 400, 120, 150, 56),
      N('q', 'User question', 50, 260, 120, 50),
      N('ret', 'Retrieve top-k\nrelevant chunks', 210, 260, 150, 56),
      N('llm', 'LLM answers\ngrounded in context', 420, 260, 170, 60, { accent: true }),
    ],
    edges: [['docs', 'embed'], ['embed', 'vdb'], ['q', 'ret'], ['vdb', 'ret'], ['ret', 'llm', 'context + question']],
    occlude: ['embed', 'vdb', 'ret', 'llm'],
  },
  {
    id: 'transformer', title: 'Transformer Core Ideas',
    match: /transformer|self-attention|multi-head|positional encoding|attention is all you need/i,
    nodes: [
      N('tok', 'Token embeddings', 60, 110, 160, 50),
      N('pos', 'Positional encoding\ninjects word order', 60, 200, 160, 56),
      N('attn', 'SELF-ATTENTION\nevery token attends to\nevery other token', 290, 140, 190, 80, { accent: true }),
      N('multi', 'Multi-head attention\nparallel attention views', 520, 110, 170, 56),
      N('ff', 'Feed-forward layers\n+ residuals, stacked N×', 520, 220, 170, 56),
    ],
    edges: [['tok', 'attn'], ['pos', 'attn'], ['attn', 'multi'], ['multi', 'ff']],
    occlude: ['pos', 'attn', 'multi', 'ff'],
  },
  {
    id: 'crisp-dm', title: 'Data Mining Process (CRISP-DM)',
    match: /data mining process|crisp|business understanding|steps? (of|for|in) data mining|semma/i,
    nodes: [
      N('bu', 'Business\nunderstanding', 60, 100, 130, 56),
      N('du', 'Data\nunderstanding', 240, 100, 130, 56),
      N('prep', 'Data\npreparation', 420, 100, 130, 56),
      N('model', 'Modeling', 420, 230, 130, 52),
      N('eval', 'Evaluation', 240, 230, 130, 52),
      N('deploy', 'Deployment\n& monitoring', 60, 230, 130, 56),
    ],
    edges: [['bu', 'du'], ['du', 'prep'], ['prep', 'model'], ['model', 'eval'], ['eval', 'deploy'], ['eval', 'bu', 'iterate']],
    occlude: ['bu', 'du', 'prep', 'model', 'eval', 'deploy'],
  },
  {
    id: 'data-partition', title: 'Data Partitioning',
    match: /training data|test data|validation data|holdout|partition|cross-validation|overfit/i,
    nodes: [
      N('all', 'All labeled data', 60, 120, 160, 50),
      N('train', 'TRAINING set\nfit the model', 290, 80, 160, 56),
      N('valid', 'VALIDATION set\ntune & compare models', 290, 170, 160, 56),
      N('test', 'TEST set\nfinal honest estimate\n(touch once)', 290, 270, 160, 64, { accent: true }),
      N('gap', 'Overfitting signal:\ntraining ≫ validation score', 510, 160, 180, 64),
    ],
    edges: [['all', 'train'], ['all', 'valid'], ['all', 'test'], ['valid', 'gap']],
    occlude: ['train', 'valid', 'test', 'gap'],
  },
  {
    id: 'roc-lift', title: 'ROC Curve & AUC',
    match: /roc|auc|lift chart|gains chart|decile|cutoff|threshold/i,
    nodes: [
      N('perfect', 'Perfect model\n(0,1) corner', 110, 90, 130, 50),
      N('auc', 'AUC = area under curve\n1.0 perfect · 0.5 random', 430, 110, 200, 56),
      N('diag', 'Diagonal =\nrandom guessing', 430, 290, 160, 56),
    ],
    extra: `<g transform="translate(110,80)"><rect x="0" y="0" width="260" height="260" fill="rgba(10,40,60,0.45)" stroke="${DIM}"/><path d="M0,260 C60,80 140,30 260,0" fill="none" stroke="${GLOW}" stroke-width="2.5"/><line x1="0" y1="260" x2="260" y2="0" stroke="${DIM}" stroke-dasharray="5 4"/><text x="130" y="285" fill="${FG}" font-size="11" text-anchor="middle">False positive rate →</text><text x="-14" y="130" fill="${FG}" font-size="11" text-anchor="middle" transform="rotate(-90,-14,130)">True positive rate →</text></g>`,
    occlude: ['perfect', 'auc', 'diag'],
  },
  {
    id: 'gradient-descent', title: 'Gradient Descent',
    match: /gradient descent|learning rate|loss surface|local minim|optimization (method|algorithm)|weight updating|sgd|stochastic/i,
    nodes: [
      N('lr', 'Learning rate\nstep size of each update', 460, 100, 200, 56),
      N('grad', 'Gradient\ndirection of steepest ascent\n(step the other way)', 460, 190, 200, 66),
      N('min', 'Minimum of loss\ntraining converges', 460, 290, 200, 56),
    ],
    extra: `<g transform="translate(70,90)"><path d="M0,40 C60,180 120,260 170,265 C230,260 300,170 340,30" fill="none" stroke="${GLOW}" stroke-width="2.5"/><circle cx="48" cy="118" r="6" fill="#ffd97a"/><circle cx="92" cy="196" r="6" fill="#ffd97a"/><circle cx="134" cy="244" r="6" fill="#ffd97a"/><circle cx="170" cy="263" r="7" fill="#7dffb0"/><text x="170" y="300" fill="${FG}" font-size="11" text-anchor="middle">loss surface — steps shrink toward the minimum</text></g>`,
    occlude: ['lr', 'grad', 'min'],
  },
  {
    id: 'decision-tree', title: 'Decision Tree Anatomy',
    match: /decision tree|root node|leaf|terminal node|split|pruning|gini|entropy|cart\b/i,
    nodes: [
      N('root', 'ROOT split\nbest predictor + cutpoint\n(max purity gain)', 270, 80, 190, 66, { accent: true }),
      N('int', 'Internal split\nIncome < 50k?', 110, 200, 150, 56),
      N('leafa', 'LEAF: predict\n"churn" (82%)', 60, 310, 130, 56),
      N('leafb', 'LEAF: predict\n"stay" (74%)', 230, 310, 130, 56),
      N('prune', 'Pruning removes\nweak branches to\nprevent overfitting', 470, 220, 170, 70),
    ],
    edges: [['root', 'int', 'yes'], ['root', 'prune', 'no'], ['int', 'leafa'], ['int', 'leafb']],
    occlude: ['root', 'int', 'leafa', 'prune'],
  },
  {
    id: 'ab-design', title: 'A/B Test Design',
    match: /a\/b test|controlled experiment|random assignment|treatment|control group|design checklist|average treatment effect|ate\b/i,
    nodes: [
      N('pop', 'Target population', 50, 110, 150, 50),
      N('sample', 'Random sample\n(external validity)', 240, 110, 160, 56),
      N('rand', 'RANDOM ASSIGNMENT\n(internal validity)', 440, 110, 190, 56, { accent: true }),
      N('a', 'Control (A)\ncurrent experience', 240, 230, 160, 56),
      N('b', 'Treatment (B)\nnew experience', 460, 230, 160, 56),
      N('kpi', 'Compare KPI → estimate ATE\nwith interval + significance test', 280, 330, 280, 56),
    ],
    edges: [['pop', 'sample'], ['sample', 'rand'], ['rand', 'a'], ['rand', 'b'], ['a', 'kpi'], ['b', 'kpi']],
    occlude: ['sample', 'rand', 'a', 'b', 'kpi'],
  },
  {
    id: 'type-errors', title: 'Type I & II Errors and Power',
    match: /type i|type ii|power|alpha|beta\b|null hypothesis|significance level|effect size/i,
    nodes: [
      N('t1', 'TYPE I error (α)\nfalse alarm: reject a\ntrue null hypothesis', 250, 110, 180, 76, { fill: 'rgba(120,50,50,0.5)' }),
      N('ok1', 'Correct\n(confidence 1−α)', 450, 110, 160, 76, { fill: 'rgba(28,110,80,0.5)' }),
      N('ok2', 'Correct = POWER\n(1−β) detects a\nreal effect', 250, 210, 180, 76, { fill: 'rgba(28,110,80,0.5)' }),
      N('t2', 'TYPE II error (β)\nmiss: fail to reject\na false null', 450, 210, 160, 76, { fill: 'rgba(120,50,50,0.5)' }),
      N('drv', 'Power ↑ with sample size,\neffect size, and α', 250, 320, 240, 50),
    ],
    extra: `<text x="340" y="95" fill="${FG}" font-size="12" text-anchor="middle">H₀ true</text><text x="530" y="95" fill="${FG}" font-size="12" text-anchor="middle">H₀ false</text><text x="215" y="150" fill="${FG}" font-size="12" text-anchor="end">Reject H₀</text><text x="215" y="250" fill="${FG}" font-size="12" text-anchor="end">Keep H₀</text>`,
    occlude: ['t1', 'ok2', 't2', 'drv'],
  },
  {
    id: 'lp-region', title: 'Linear Programming Geometry',
    match: /linear programming|feasible region|corner point|simplex|shadow price|binding constraint|objective function/i,
    nodes: [
      N('feas', 'FEASIBLE REGION\nall points satisfying\nevery constraint', 430, 110, 190, 70),
      N('corner', 'Optimum at a\nCORNER POINT\n(simplex walks them)', 430, 210, 190, 70, { accent: true }),
      N('shadow', 'Shadow price = objective\ngain per unit of a\nbinding constraint', 430, 310, 220, 66),
    ],
    extra: `<g transform="translate(70,80)"><polygon points="0,280 0,90 90,30 210,120 210,280" fill="rgba(25,120,160,0.25)" stroke="${GLOW}" stroke-width="2"/><circle cx="90" cy="30" r="7" fill="#7dffb0"/><line x1="-10" y1="120" x2="240" y2="40" stroke="#ffd97a" stroke-dasharray="6 4"/><text x="105" y="300" fill="${FG}" font-size="11" text-anchor="middle">constraints bound the polygon · dashed = objective line</text></g>`,
    occlude: ['feas', 'corner', 'shadow'],
  },
  {
    id: 'cnn-flow', title: 'CNN Pipeline',
    match: /convolution|cnn|pooling|filter|feature map|kernel/i,
    nodes: [
      N('img', 'Input image\npixel grid', 50, 160, 120, 60),
      N('conv', 'CONVOLUTION\nfilters detect local\npatterns (weight sharing)', 210, 150, 180, 76, { accent: true }),
      N('pool', 'POOLING\ndownsample,\nkeep strongest signal', 430, 150, 150, 76),
      N('dense', 'Dense layers\n→ softmax classes', 50, 300, 170, 56),
    ],
    edges: [['img', 'conv'], ['conv', 'pool'], ['pool', 'dense', 'stacked & flattened']],
    occlude: ['conv', 'pool', 'dense'],
  },
  {
    id: 'rnn-unrolled', title: 'RNN Unrolled in Time',
    match: /recurrent|rnn|lstm|gru|hidden state|sequence model|vanishing gradient/i,
    nodes: [
      N('h1', 'h₁\nhidden state', 110, 160, 110, 56),
      N('h2', 'h₂\ncarries memory', 300, 160, 110, 56),
      N('h3', 'h₃\n…through time', 490, 160, 110, 56),
      N('gate', 'LSTM gates decide what to\nkeep, forget, and output —\nfixing vanishing gradients', 250, 300, 240, 70, { accent: true }),
    ],
    edges: [['h1', 'h2', 'state'], ['h2', 'h3', 'state']],
    extra: `<text x="165" y="120" fill="${FG}" font-size="11" text-anchor="middle">x₁ ↓</text><text x="355" y="120" fill="${FG}" font-size="11" text-anchor="middle">x₂ ↓</text><text x="545" y="120" fill="${FG}" font-size="11" text-anchor="middle">x₃ ↓</text>`,
    occlude: ['h2', 'gate'],
  },
  {
    id: 'autoencoder', title: 'Autoencoder',
    match: /autoencoder|bottleneck|encoder|decoder|reconstruction/i,
    nodes: [
      N('enc', 'ENCODER\ncompresses input', 90, 150, 150, 64),
      N('code', 'BOTTLENECK\nlow-dimensional code', 300, 150, 160, 64, { accent: true }),
      N('dec', 'DECODER\nreconstructs input', 520, 150, 150, 64),
      N('err', 'Reconstruction error =\ntraining signal & anomaly score', 230, 300, 260, 56),
    ],
    edges: [['enc', 'code'], ['code', 'dec'], ['dec', 'err']],
    occlude: ['enc', 'code', 'dec', 'err'],
  },
  {
    id: 'api-flow', title: 'Web API Request Cycle',
    match: /api\b|http|rest|json|status code|request|response|endpoint|rate limit/i,
    nodes: [
      N('client', 'Client (Python)\nrequests.get(url,\nparams, headers)', 60, 130, 170, 70),
      N('auth', 'Auth: API key /\ntoken in header', 60, 270, 170, 56),
      N('server', 'API server\nendpoint routes request', 450, 130, 180, 70),
      N('resp', 'Response: status code\n200 OK · 401 auth · 429 rate\n+ JSON body to parse', 400, 270, 240, 70, { accent: true }),
    ],
    edges: [['client', 'server', 'HTTPS request'], ['server', 'resp'], ['auth', 'client']],
    occlude: ['client', 'auth', 'resp'],
  },
  {
    id: 'text-pipeline', title: 'Text Mining Pipeline',
    match: /tokeniz|stop ?word|stemming|lemmatiz|tf-?idf|bag of words|document-term|corpus|sentiment/i,
    nodes: [
      N('raw', 'Raw text\ncorpus', 50, 130, 110, 56),
      N('tok', 'Tokenize\nsplit into terms', 200, 130, 130, 56),
      N('norm', 'Normalize\nstopwords, stem/\nlemmatize, lowercase', 370, 120, 160, 72),
      N('tfidf', 'TF-IDF weighting\nfrequent here, rare overall', 200, 270, 200, 60, { accent: true }),
      N('dtm', 'Document-term matrix\n→ classify / cluster', 450, 270, 190, 60),
    ],
    edges: [['raw', 'tok'], ['tok', 'norm'], ['norm', 'tfidf'], ['tfidf', 'dtm']],
    occlude: ['tok', 'norm', 'tfidf', 'dtm'],
  },
  {
    id: 'causal-toolbox', title: 'Causal Inference Designs',
    match: /regression discontinuity|difference in difference|synthetic control|instrument|propensity score|interrupted time series|counterfactual|potential outcome/i,
    nodes: [
      N('cf', 'COUNTERFACTUAL\nwhat would have happened\nwithout treatment', 240, 80, 230, 64, { accent: true }),
      N('rd', 'Regression\ndiscontinuity:\ncompare near cutoff', 40, 200, 150, 70),
      N('did', 'Diff-in-diff:\ntreated vs control,\nbefore vs after', 220, 200, 150, 70),
      N('iv', 'Instrumental\nvariables: nature\nrandomizes for you', 400, 200, 150, 70),
      N('psm', 'Propensity matching:\ncompare statistical twins', 130, 310, 200, 56),
      N('sc', 'Synthetic control:\nweighted blend mimics\nthe treated unit', 400, 300, 180, 70),
    ],
    edges: [['rd', 'cf'], ['did', 'cf'], ['iv', 'cf'], ['psm', 'did'], ['sc', 'did']],
    occlude: ['cf', 'rd', 'did', 'iv', 'psm', 'sc'],
  },
  {
    id: 'bandit-loop', title: 'Multi-Armed Bandit Loop',
    match: /bandit|thompson|epsilon|ucb|explore|exploit|regret/i,
    nodes: [
      N('belief', 'Belief per arm\n(posterior / estimate)', 80, 120, 180, 60),
      N('choose', 'CHOOSE arm:\nexplore vs exploit\n(ε-greedy, UCB, Thompson)', 330, 110, 200, 76, { accent: true }),
      N('reward', 'Observe reward\n(click, conversion)', 330, 250, 180, 56),
      N('update', 'Update belief\nshift traffic to winners', 80, 250, 180, 60),
    ],
    edges: [['belief', 'choose'], ['choose', 'reward'], ['reward', 'update'], ['update', 'belief']],
    occlude: ['choose', 'reward', 'update'],
  },
];

/** Build all diagrams: id → {id,title,svg,regions}. */
export function buildDiagrams() {
  const out = {};
  for (const spec of SPECS) {
    const regions = spec.nodes
      .filter((n) => (spec.occlude || []).includes(n.id))
      .map((n) => ({ id: n.id, label: n.label.replace(/\n/g, ' '), x: n.x, y: n.y, w: n.w, h: n.h }));
    out[spec.id] = { id: spec.id, title: spec.title, svg: composeSvg(spec), regions, viewBox: `0 0 ${W} ${H}` };
  }
  return out;
}

/** Find the best diagram for a concept term (or null). */
export function diagramFor(term) {
  for (const spec of SPECS) if (spec.match.test(term)) return spec.id;
  return null;
}