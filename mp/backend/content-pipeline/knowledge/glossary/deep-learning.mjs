// Glossary entries for the "deep-learning" deck. Each entry:
// { m: [matchers...], d: 'definition with «cloze phrases»', how, ex, we, mk, src: [{title,kind,ref}] }
// Grounded in backend/content-pipeline/extracted/... per backend/content-pipeline/taxonomy.mjs sourcePaths.
//
// sd-nn-intro — ISA 591 "Neural Networks" lecture (Module 8, Day 1 notes)
const SD_NN_INTRO_SRC = [
  { title: 'ISA 591: Data Mining — Neural Networks lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 8, Day 1 notes)' },
];

// sd-matrix-tensor — ISA 630 Module 0 "Matrix/Tensor Algebra" slides
const SD_MATRIX_TENSOR_SRC = [
  { title: 'ISA 630: Deep Learning — Matrix/Tensor Algebra lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 0)' },
];

// sd-gradients-regularization — ISA 630 Module 1 "Gradients, Regularization"
const SD_GRADIENTS_REG_SRC = [
  { title: 'ISA 630: Deep Learning — Loss Functions, Gradients & Regularization lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 1)' },
];

// sd-classification-deep-dive — ISA 630 Module 2 "Classification Deep Dive"
// (Binary, Multi-Class, Multi-Label Classification)
const SD_CLASSIFICATION_DD_SRC = [
  { title: 'ISA 630: Deep Learning — Classification Deep Dive (Binary, Multi-Class, Multi-Label)', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 2)' },
];

// sd-feedforward — ISA 630 Module 3 "Feed-Forward Architectures" (Neurons/Activations/Parameters, Forward & Backward Propagation)
const SD_FEEDFORWARD_SRC = [
  { title: 'ISA 630: Deep Learning — Feed-Forward Architectures lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 3)' },
];

// sd-autoencoders — ISA 630 Module 4 "AutoEncoders"
const SD_AUTOENCODERS_SRC = [
  { title: 'ISA 630: Deep Learning — AutoEncoders lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 4)' },
];

// sd-cnn — ISA 630 Module 5 "Convolutional Neural Networks" (Convolutions, CNN Implementations)
const SD_CNN_SRC = [
  { title: 'ISA 630: Deep Learning — Convolutional Neural Networks lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 5)' },
];

// sd-rnn — ISA 630 Module 6 "Recurrent Neural Networks" (RNN basics, LSTMs/GRUs, Attention)
const SD_RNN_SRC = [
  { title: 'ISA 630: Deep Learning — Recurrent Neural Networks lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 6)' },
];

// sd-svm — ISA 630 Module 7 "Support Vector Machines" (Maximum Margin, Soft Margin, Kernel Trick)
const SD_SVM_SRC = [
  { title: 'ISA 630: Machine Learning for Business Applications — Support Vector Machines lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 7)' },
];

// sd-ensemble-hybrid — ISA 630 Module 8 "Ensemble-Hybrid Learning" (Bias/Variance,
// Bootstrapping/Bagging, Random Forests, AdaBoost/Gradient Boosting)
const SD_ENSEMBLE_SRC = [
  { title: 'ISA 630: Machine Learning for Business Applications — Ensemble Learning lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Module 8)' },
];

export const GLOSSARY_deep_learning = [
  {
    m: ['activation function'],
    d: 'An activation function is applied at each hidden and output node «after computing the weighted sum of inputs, introducing non-linearity into the model» — without it, a neural network of any depth would behave just like an ordinary linear model.',
    how: 'Each hidden node computes a weighted sum s = θ + w₁x₁ + w₂x₂ + ..., then applies an activation function g(s) to produce its output, which feeds forward into the next layer.',
    src: SD_NN_INTRO_SRC,
  },
  {
    m: ['sigmoid activation function', 'sigmoid function'],
    d: 'The sigmoid activation function, g(s) = 1/(1+e⁻ˢ), «squashes any real-valued input into the range (0, 1)» — making it especially useful when the output should be interpreted as a probability, as in binary classification.',
    src: SD_NN_INTRO_SRC,
  },
  {
    m: ['relu activation function', 'relu', 'rectified linear unit'],
    d: 'ReLU (Rectified Linear Unit), g(s) = max(0, s), «outputs the input directly if positive, otherwise zero» — it\'s computationally cheap, helps avoid the vanishing gradient problem in deep networks, and tends to converge faster than sigmoid or tanh.',
    mk: 'Assuming sigmoid is always the default choice for hidden layers — ReLU is generally preferred there specifically because it avoids the vanishing-gradient slowdown sigmoid can cause in deep networks.',
    src: SD_NN_INTRO_SRC,
  },
  {
    m: ['gradient descent', 'stochastic gradient descent', 'sgd'],
    d: 'Gradient descent is the core optimization method that «minimizes a loss function by repeatedly nudging weights in the direction that reduces error, based on the gradient (slope) of the loss» — Stochastic Gradient Descent (SGD) is a variant that updates weights using a single observation at a time, trading some stability for speed.',
    src: SD_NN_INTRO_SRC,
  },
  {
    m: ['backpropagation', 'backpropagation of error'],
    d: 'Backpropagation is the algorithm that «uses the chain rule of calculus to efficiently compute how much each weight contributed to the output error, working backward from the output layer to the input layer» — those gradients are then handed to an optimization method like gradient descent to actually update the weights.',
    how: 'The four-step cycle: (1) Forward Pass — compute predictions from input to output; (2) Compute Error — compare prediction to actual target via the loss function; (3) Backward Pass — use the chain rule to compute each weight\'s gradient; (4) Update Weights — apply gradient descent: w_new = w_old − η·(∂L/∂w), where η is the learning rate.',
    mk: 'Treating backpropagation and gradient descent as the same thing — backpropagation computes the gradients; gradient descent (or a variant) is what actually uses those gradients to update the weights.',
    src: SD_NN_INTRO_SRC,
  },

  // ---- sd-matrix-tensor ----
  {
    m: ['dot product'],
    d: 'The dot product of two vectors is «the sum of the products of their corresponding components» — a fundamental operation in machine learning, used everywhere from computing weighted sums in a neural network to measuring vector similarity.',
    src: SD_MATRIX_TENSOR_SRC,
  },
  {
    m: ['vector norm', 'l1 norm', 'l2 norm'],
    d: 'Vector norms are added to a cost function (like SSE or MSE) as a regularization penalty on the weights: «the L1 norm tends to zero out unimportant weights entirely, while the L2 norm tends to shrink weights toward (but not all the way to) zero».',
    mk: 'Mixing up which norm actually zeroes out weights — L1 can drive a weight exactly to zero (effective variable selection); L2 only shrinks weights close to zero without eliminating them.',
    src: SD_MATRIX_TENSOR_SRC,
  },
  {
    m: ['matrix multiplication'],
    d: 'Two matrices can be multiplied only if they\'re «conformable — the first matrix\'s number of columns must equal the second matrix\'s number of rows (inner dimensions must match)» — the resulting matrix takes the outer dimensions of the two original matrices.',
    mk: 'Trying to multiply two matrices without checking that the inner dimensions match — matrix multiplication isn\'t defined unless the first matrix\'s column count equals the second matrix\'s row count.',
    src: SD_MATRIX_TENSOR_SRC,
  },
  {
    m: ['matrix transpose'],
    d: 'The transpose of a matrix is «obtained by interchanging its rows and columns» — turning an m×n matrix into an n×m matrix.',
    src: SD_MATRIX_TENSOR_SRC,
  },
  {
    m: ['linear dependence', 'rank of a matrix'],
    d: 'A matrix is linearly dependent if «at least one of its rows (or columns) can be written as a linear combination of the others» — the rank of a matrix is the number of columns (or rows) that are actually independent.',
    src: SD_MATRIX_TENSOR_SRC,
  },
  {
    m: ['sparse vs. dense matrix', 'sparse matrix', 'dense matrix'],
    d: 'A sparse matrix is «one in which most of the elements are zero», as opposed to a dense matrix where most elements are non-zero — the distinction matters for storage and computation efficiency at scale.',
    src: SD_MATRIX_TENSOR_SRC,
  },
  {
    m: ['tensor'],
    d: 'A tensor is «a generalization of vectors and matrices to higher dimensions» — a vector is a 1-D tensor, a matrix is a 2-D tensor, and deep learning frameworks (NumPy, TensorFlow) represent everything from images to neural network weights as tensors of the appropriate dimensionality.',
    src: SD_MATRIX_TENSOR_SRC,
  },

  // ---- sd-gradients-regularization ----
  {
    m: ['loss function'],
    d: 'A loss function measures the «distance between an ML algorithm\'s output and the expected output for a single training instance» — it calculates the error of the hypothesis on just one example.',
    mk: 'Using "loss function" and "cost function" interchangeably without distinction — loss is per-instance error; cost aggregates loss across the whole dataset.',
    src: SD_GRADIENTS_REG_SRC,
  },
  {
    m: ['cost function'],
    d: 'A cost function is «the sum (or average) of the loss function across all observations in the dataset», and it\'s what the learning algorithm actually minimizes to obtain its parameter estimates.',
    src: SD_GRADIENTS_REG_SRC,
  },
  {
    m: ['convex cost function', 'convex vs. non-convex'],
    d: 'A convex cost function «has a single global minimum and no local minima», making optimization straightforward — a non-convex cost function has both local and global minima and needs more advanced optimization (often gradient descent) to avoid getting stuck in a local minimum instead of finding the true global one.',
    ex: 'Linear regression\'s cost function (residual sum of squares) is convex, which is why it has a clean closed-form solution; many neural network cost functions are non-convex.',
    src: SD_GRADIENTS_REG_SRC,
  },
  {
    m: ['gradient (cost function)', 'gradient of a cost function'],
    d: 'The gradient of a cost function is «the derivative of the cost function with respect to the estimated parameters — the instantaneous rate of change» — a minimum of the cost function occurs exactly where this gradient equals zero, and an optimizer\'s job includes escaping local minima rather than settling for the first zero-gradient point it finds.',
    mk: 'Confusing metrics (used by a practitioner to monitor training progress) with the cost function (used internally by the algorithm to update weights, and not necessarily visible to the practitioner) — they serve different purposes.',
    src: SD_GRADIENTS_REG_SRC,
  },
  {
    m: ['gradient descent algorithm', 'gradient descent steps'],
    d: 'The gradient descent algorithm updates parameters in four steps: «(1) initialize parameters with random values, (2) measure the local gradient of the cost function, (3) update the parameters in the direction of descent scaled by a step size (learning rate), and (4) repeat until convergence — i.e., until the update becomes very small».',
    src: SD_GRADIENTS_REG_SRC,
  },
  {
    m: ['ridge regression (gradients)', 'l2 penalty (ridge)'],
    d: 'Ridge regression modifies the ordinary regression cost function by adding «an L2 penalty term that forces parameter estimates closer to zero, controlled by a tuning parameter λ (when λ=0, you\'re back to plain regression)» — its cost function remains convex, so it\'s still fast to compute and even has a closed-form solution.',
    how: 'The tuning parameter λ should be chosen via cross-validation, not guessed — too small and there\'s no real regularization effect; too large and the model underfits.',
    src: SD_GRADIENTS_REG_SRC,
  },

  // ---- sd-classification-deep-dive ----
  {
    m: ['binary classification (deep dive)', 'separating hyperplane'],
    d: 'Binary classification is «the task of classifying elements of a set into one of two groups (classes)» — a model separates the two classes with a hyperplane that can be linear or non-linear, and outputs the probability (propensity) of belonging to a particular class.',
    src: SD_CLASSIFICATION_DD_SRC,
  },
  {
    m: ['binary cross-entropy', 'bce loss'],
    d: 'Binary cross-entropy (BCE) is «the most common loss function for binary classification, measuring the distance between the predicted probability vector and the true label vector» — the binary cross-entropy cost function then averages this loss across all observations in the dataset.',
    src: SD_CLASSIFICATION_DD_SRC,
  },
  {
    m: ['multi-class classification'],
    d: 'Multi-class classification is «a classification task with more than two classes», where each instance still belongs to exactly one class — labels are typically represented as one-hot encoded vectors (e.g., class 2 of 3 becomes [0,1,0]), and the standard loss function is categorical cross-entropy, which measures the distance between predicted and true probability matrices.',
    mk: 'Confusing multi-class classification (each instance gets exactly one label, from more than two possible classes) with multi-label classification (each instance can get several labels at once) — they require different loss functions and modeling approaches.',
    src: SD_CLASSIFICATION_DD_SRC,
  },
  {
    m: ['multi-label classification'],
    d: 'Multi-label classification is «the supervised learning problem where a single instance may be associated with multiple labels simultaneously» (represented as a response matrix with multiple 1s per row) — a common strategy is Binary Relevance, which decomposes the task into independent binary classification problems, fitting one model per label/response.',
    ex: 'A news article could simultaneously be tagged "politics," "economy," and "international" — three labels at once, which is exactly the multi-label setting Binary Relevance handles by training three separate binary classifiers.',
    src: SD_CLASSIFICATION_DD_SRC,
  },

  // ---- sd-feedforward ----
  {
    m: ['perceptron'],
    d: 'The perceptron is «the most basic neural network unit — a single neuron whose activation is (classically) a threshold logical unit» — choosing different activations turns it into familiar models: a "linear" activation makes it equivalent to linear regression, while a "sigmoid" activation makes it equivalent to logistic regression.',
    src: SD_FEEDFORWARD_SRC,
  },
  {
    m: ['multi-layer perceptron', 'mlp', 'feed-forward architecture'],
    d: 'A Multi-Layer Perceptron (MLP) connects neurons in a strictly «forward, unidirectional flow — input nodes feed hidden nodes, which feed output nodes» — with every weight and bias acting as an independently tunable "knob."',
    src: SD_FEEDFORWARD_SRC,
  },
  {
    m: ['choosing an activation function', 'activation function by layer'],
    d: 'Different activation functions suit different layers and response types: «linear for a numeric output layer; ReLU for hidden layers or a positive numeric output; sigmoid or tanh for hidden layers or a binary output; softmax for a multi-class output layer».',
    mk: 'Using softmax in a hidden layer or for a numeric (regression) output — softmax is specifically designed to produce a multi-class probability distribution at the output layer, not a general-purpose hidden-layer activation.',
    src: SD_FEEDFORWARD_SRC,
  },
  {
    m: ['forward pass', 'forward propagation'],
    d: 'The forward pass is the step where information «flows from the input nodes through the hidden nodes to the output nodes, producing a prediction» — it is the same directional flow that gives feed-forward networks their name, and it is the first half of the train-step cycle (forward pass, then backward pass).',
    src: SD_FEEDFORWARD_SRC,
  },
  {
    m: ['number of estimated parameters (neural network)', 'neural network parameter count'],
    d: 'Knowing the number of estimated parameters (weights and biases) in a neural network is «useful for anticipating when the model might overfit» — more parameters relative to the amount of training data generally raises overfitting risk.',
    src: SD_FEEDFORWARD_SRC,
  },

  // ---- sd-autoencoders ----
  {
    m: ['autoencoder'],
    d: 'An autoencoder is an «unsupervised learning neural network trained to reconstruct its own input after compressing it» — it learns two functions, an Encoder (compresses input to a lower dimension) and a Decoder (reconstructs the original input from that compressed form), with reconstruction loss measuring how well it succeeds.',
    src: SD_AUTOENCODERS_SRC,
  },
  {
    m: ['latent space (autoencoder)', 'bottleneck (autoencoder)'],
    d: 'The latent space (or bottleneck) is «the compressed, lower-dimensional representation sitting between an autoencoder\'s encoder and decoder» — it forces the network to learn the input\'s most important, information-dense features rather than just copying it through.',
    ex: 'Autoencoders can outperform PCA at dimensionality reduction on large or non-linear datasets, precisely because the latent space can capture non-linear structure that PCA\'s linear projections cannot.',
    src: SD_AUTOENCODERS_SRC,
  },
  {
    m: ['undercomplete autoencoder', 'deep autoencoder'],
    d: 'An undercomplete (deep) autoencoder is the basic form: «it takes an input and predicts that same input as output, using one or more hidden layers to force the data through a lower-dimensional bottleneck» — using multiple hidden layers on each side is what makes it a "deep" autoencoder.',
    src: SD_AUTOENCODERS_SRC,
  },
  {
    m: ['sparse autoencoder'],
    d: 'A sparse autoencoder adds «a sparsity penalty (commonly an L1 or L2 norm) to the loss function», encouraging most of the latent representation\'s activations toward zero — pushing the network to rely on a small, selective subset of features rather than spreading information across all of them.',
    src: SD_AUTOENCODERS_SRC,
  },
  {
    m: ['denoising autoencoder'],
    d: 'A denoising autoencoder is trained by «feeding it a noise-corrupted version of an image as input, while the target output is the clean, noise-free image» — teaching the network to remove noise from a signal rather than just compress and reconstruct it as-is.',
    src: SD_AUTOENCODERS_SRC,
  },
  {
    m: ['why use autoencoders', 'autoencoder use cases'],
    d: 'Beyond simple reconstruction, autoencoders are commonly used for «dimension reduction, noise reduction (denoising), anomaly detection, and feature extraction» — each application reuses the same encoder/decoder structure for a different practical purpose.',
    ex: 'For anomaly detection, an autoencoder trained only on "normal" data will reconstruct normal inputs well but poorly reconstruct anomalous ones — a high reconstruction error becomes the anomaly signal.',
    src: SD_AUTOENCODERS_SRC,
  },

  // ---- sd-cnn ----
  {
    m: ['feed-forward nns for images', 'flattening images', 'translation invariance'],
    d: 'Ordinary feed-forward networks struggle with images for two main reasons: «flattening an image tensor into a single vector creates an enormous number of features (hurting predictive power as parameter count grows), and it discards translation invariance (the network can\'t recognize the same object when it shifts position in the frame)».',
    src: SD_CNN_SRC,
  },
  {
    m: ['convolution (cnn)', 'kernel (cnn)', 'filter (cnn)'],
    d: 'A convolution (also called a kernel, mask, or filter) is «a small matrix that slides over an image to produce blurring, sharpening, embossing, or edge-detection effects» — stacking multiple convolutions together forms a convolutional layer that learns to extract useful new features from the raw pixels.',
    ex: 'Combining several different convolutional filters lets a CNN simultaneously detect edges, textures, and shapes at different parts of an image — features a flattened feed-forward network would have a much harder time learning.',
    src: SD_CNN_SRC,
  },
  {
    m: ['pooling (cnn)'],
    d: 'A pooling filter «downsamples an image (or feature map), reducing its spatial dimensions» — the most common variants are max pooling (keeps the largest value in each region), min pooling, and average pooling (keeps the average).',
    src: SD_CNN_SRC,
  },
  {
    m: ['padding (cnn)'],
    d: 'Padding adds extra border pixels (e.g., a ring of zeros) around an image «to preserve its spatial dimensions» after a convolution is applied — without it, every convolution shrinks the image, and stacking many convolutional layers would shrink it down to nothing.',
    src: SD_CNN_SRC,
  },
  {
    m: ['stride (cnn)'],
    d: 'Stride is «the number of pixels a convolution\'s kernel shifts at each step as it slides across the image» — a larger stride produces a smaller output (more downsampling), while a stride of 1 moves the kernel one pixel at a time, preserving more detail.',
    mk: 'Forgetting that padding and stride jointly determine the output size of a convolution — increasing stride shrinks the output, while padding can offset that shrinkage; the two need to be reasoned about together.',
    src: SD_CNN_SRC,
  },

  // ---- sd-rnn ----
  {
    m: ['sliding window (sequences)', 'window size and horizon'],
    d: 'The sliding window method creates features from a sequence by «defining a window size (how many past steps to use as input) and a horizon (how many steps ahead to predict)» — e.g., a window size of 7 and horizon of 1 uses the last 7 observations to predict the next one.',
    src: SD_RNN_SRC,
  },
  {
    m: ['recurrent neural network', 'rnn'],
    d: 'A Recurrent Neural Network (RNN) contains «a feedback loop so each neuron\'s output also feeds back as input for the next time step» — letting it process sequences by maintaining a hidden state that carries information forward; common configurations include sequence-to-sequence, sequence-to-vector, and vector-to-sequence.',
    src: SD_RNN_SRC,
  },
  {
    m: ['vanishing gradient (rnn)', 'backpropagation over time'],
    d: 'In an RNN, errors are propagated backward across time steps (backpropagation through time) — but «the vanishing (or exploding) gradient problem causes early values in a long sequence to lose influence quickly, so short-term memory fades fast» in a plain/simple RNN.',
    mk: 'Expecting a simple RNN to remember information from far back in a long sequence — that\'s exactly the vanishing-gradient weakness LSTMs and GRUs were designed to fix.',
    src: SD_RNN_SRC,
  },
  {
    m: ['lstm', 'long short-term memory'],
    d: 'Long Short-Term Memory (LSTM) is an RNN variant designed to «solve the vanishing gradient problem and let information persist over the long term» by maintaining two states — a hidden state (short-term memory) and an internal/cell state (long-term memory) — managed by gates.',
    src: SD_RNN_SRC,
  },
  {
    m: ['lstm forget gate', 'lstm input gate', 'lstm output gate', 'lstm gates'],
    d: 'LSTM gates control what the cell remembers: «the Forget Gate decides how much of the previous internal (long-term) state to keep or discard (output 0-1); the Input Gate decides how much new information to add to long-term memory; the Output Gate decides how much of the updated internal state contributes to the new hidden state».',
    src: SD_RNN_SRC,
  },
  {
    m: ['gru', 'gated recurrent unit'],
    d: 'A Gated Recurrent Unit (GRU) is «a streamlined version of the LSTM that achieves comparable performance with a simpler gating structure» — making it computationally cheaper while still addressing the vanishing-gradient weakness of plain RNNs.',
    src: SD_RNN_SRC,
  },
  {
    m: ['bidirectional lstm', 'bilstm'],
    d: 'A Bidirectional LSTM (BiLSTM) «runs two LSTM layers over the same sequence — one forward, one backward — capturing information from both past and future context», which enhances sequence understanding compared to a standard (one-direction) LSTM.',
    src: SD_RNN_SRC,
  },
  {
    m: ['attention (rnn)', 'attention mechanism', 'context vector'],
    d: 'Attention is a mechanism that lets a sequence model «learn where to focus dynamically, instead of treating every time step equally» — it scores each time step, applies softmax to turn the scores into weights, multiplies each hidden state by its weight, and sums the results into a single context vector summarizing the important parts of the sequence.',
    ex: 'In sales forecasting, an attention layer can learn to weight holiday seasons and promotional weeks much more heavily than ordinary weeks when predicting future demand.',
    src: SD_RNN_SRC,
  },

  // ---- sd-svm ----
  {
    m: ['separating hyperplane (svm)', 'hyperplane (svm)'],
    d: 'A hyperplane is «a subspace whose dimension is one less than the space it lives in» (a line in 2D, a plane in 3D); a separating hyperplane is one that splits the data so points from each class fall on opposite sides — but for most datasets, infinitely many separating hyperplanes exist, which raises the question of which one is "best."',
    src: SD_SVM_SRC,
  },
  {
    m: ['margin (svm)', 'maximum margin classifier'],
    d: 'The margin is «the distance between the separating hyperplane and the closest points (from each class) to it» — the Maximum Margin Classifier picks the one separating hyperplane that maximizes this margin, on the principle that a wider margin generalizes better to new data than a narrow one.',
    mk: 'Assuming any separating hyperplane is as good as any other — without maximizing the margin, you could pick a hyperplane that barely separates the classes and is fragile to new data.',
    src: SD_SVM_SRC,
  },
  {
    m: ['soft margin classifier', 'support vector classifier', 'svc'],
    d: 'The Soft Margin Classifier (Support Vector Classifier, SVC) extends the Maximum Margin Classifier to handle data that isn\'t perfectly separable: «it allows some observations to fall within the margin, or even be misclassified, by an amount controlled by a slack variable» — this is necessary because a strict hard margin doesn\'t work on all real-world data.',
    how: 'A regularization parameter C controls the tradeoff: a large C allows more observations to violate the margin (a softer, more flexible boundary), while a small C enforces a stricter margin (scikit-learn actually parameterizes this as the inverse of C internally).',
    src: SD_SVM_SRC,
  },
  {
    m: ['kernel trick'],
    d: 'The kernel trick solves SVM\'s non-linear classification problem by «implicitly mapping data into a higher-dimensional space (where the classes become linearly separable) without ever computing that transformation explicitly» — done by replacing the dot product in the SVM\'s optimization with a kernel function.',
    ex: 'Data that needs a curved (non-linear) separating boundary in its original space can become linearly separable after a polynomial kernel transformation maps it into a higher-dimensional feature space.',
    mk: 'Assuming the kernel trick literally transforms every data point into the higher-dimensional space — the "trick" is specifically that it avoids ever computing those coordinates explicitly, working only through kernel (dot-product-like) evaluations.',
    src: SD_SVM_SRC,
  },

  // ---- sd-ensemble-hybrid ----
  {
    m: ['bias-variance-irreducible error decomposition', 'generalization error decomposition'],
    d: 'A learning algorithm\'s generalization error decomposes into three components: «bias (the difference between the true function and the average learner output), variance (how much the learner\'s predictions vary across different training samples), and irreducible error (random noise no model can ever eliminate)» — and this breakdown shifts as model complexity changes.',
    how: 'As a learner\'s complexity increases, bias generally decreases but variance increases — the classic bias-variance tradeoff that ensemble methods are specifically designed to navigate.',
    src: SD_ENSEMBLE_SRC,
  },
  {
    m: ['bootstrapping', 'bootstrap sampling'],
    d: 'Bootstrapping is a statistical procedure that «resamples a single dataset with replacement to create many simulated samples» — each bootstrap sample is the same size as the original dataset but, because of sampling with replacement, contains some repeated observations and omits others.',
    src: SD_ENSEMBLE_SRC,
  },
  {
    m: ['bagging', 'bootstrap aggregating'],
    d: 'Bagging (Bootstrap Aggregating) trains «multiple classifiers, each on a different bootstrap sample of the data, then combines them — majority vote for classification, averaging for regression» — directly motivated by the question "if we have a low-bias, high-variance method, can we reduce the variance while keeping the bias low?"',
    how: 'Bagging works best with an unstable base estimator (low bias, high variance, like a decision tree) — a stable algorithm like logistic regression doesn\'t benefit nearly as much, since bagging mainly reduces variance.',
    mk: 'Picking a stable, low-variance base learner (like plain logistic regression) for bagging — bagging\'s main benefit is variance reduction, so it pays off most with unstable, high-variance learners like decision trees.',
    src: SD_ENSEMBLE_SRC,
  },
  {
    m: ['random forest'],
    d: 'A Random Forest is a bagging ensemble specifically built from decision trees, where «for classification, the trees\' predictions are aggregated by majority vote, and for regression, by averaging» — each tree is grown on a different bootstrap sample (and typically a random subset of features at each split).',
    src: SD_ENSEMBLE_SRC,
  },
  {
    m: ['boosting', 'adaboost'],
    d: 'Boosting converts a weak learning algorithm into a strong one by «training learners sequentially, where each new learner pays more attention to the observations the previous learners misclassified» — the final prediction combines all learners in a weighted sum, with more accurate learners getting higher weight.',
    ex: 'AdaBoost increases the weight of misclassified observations before training the next weak learner, so each successive learner focuses more on the cases the ensemble is still getting wrong.',
    mk: 'Confusing boosting (sequential learners, each correcting the previous ones\' mistakes) with bagging (independent learners trained in parallel on different bootstrap samples) — boosting reduces bias more than bagging does, but is also more prone to overfitting on noisy data.',
    src: SD_ENSEMBLE_SRC,
  },
];