// Glossary entries for the "optimization" deck. Each entry:
// { m: [matchers...], d: 'definition with «cloze phrases»', how, ex, we, mk, src: [{title,kind,ref}] }
// Grounded in backend/content-pipeline/extracted/... per backend/content-pipeline/taxonomy.mjs sourcePaths.
//
// sd-complexity — ISA 634 "Complexity & Algorithm Analysis" lecture
// (backend/content-pipeline/extracted/isa634/Day 1 - 8-26-2025/Handout - Complexity/ and 8-28-25/).
const SD_COMPLEXITY_SRC = [
  { title: 'ISA 634: Systems Modeling & Optimization — Complexity & Algorithm Analysis lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Day 1 handout, 8/26/25)' },
];

// sd-opt-intro — ISA 634 "Introduction to Modeling" lecture (Handout 0, Day 1)
const SD_OPT_INTRO_SRC = [
  { title: 'ISA 634: Systems Modeling & Optimization — Introduction to Modeling lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 0, Day 1)' },
];

// sd-math-programming — ISA 634 "Introduction to Mathematical Programming" lecture (Handout 01, Day 2)
const SD_MATH_PROGRAMMING_SRC = [
  { title: 'ISA 634: Systems Modeling & Optimization — Introduction to Mathematical Programming lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 01, Day 2)' },
];

// sd-lp — ISA 634 "Intro to LP" lecture + Diet Problem worked example (9/9, 9/11)
const SD_LP_SRC = [
  { title: 'ISA 634: Systems Modeling & Optimization — Introduction to Linear Programming lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 02)' },
];

// sd-transportation-assignment — ISA 634 Handout 05
const SD_TRANSPORT_SRC = [
  { title: 'ISA 634: Systems Modeling & Optimization — Transportation & Assignment Problems lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 05)' },
];

// sd-network-flow — ISA 634 Handout 06
const SD_NETWORK_FLOW_SRC = [
  { title: 'ISA 634: Systems Modeling & Optimization — Network Flow Problems lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 06)' },
];

// sd-ip — ISA 634 Handout 07/08 (Integer Programming)
const SD_IP_SRC = [
  { title: 'ISA 634: Systems Modeling & Optimization — Introduction to Integer Programming lecture', kind: 'course', ref: 'Miami University, Farmer School of Business (Handout 07/08)' },
];

export const GLOSSARY_optimization = [
  {
    m: ['computational complexity', 'complexity'],
    d: 'Computational complexity is a «method for quantifying how difficult a problem is to solve», independent of any particular computer. It lets you compare the inherent difficulty of different problem classes and define what counts as an «efficient algorithm».',
    how: 'Instead of timing an algorithm on one machine (which depends on hardware), express the number of «primitive operations» the algorithm needs as a function of the input size, written T(n). This running-time function is what complexity analysis studies.',
    ex: 'A network analyst needs to decide whether an exact subgraph-detection algorithm will finish before a reporting deadline. Complexity analysis tells her the algorithm scales as O(2^n), so for the network sizes she has, an exact run is not realistic.',
    we: 'A planner trying to find the absolute best delivery route for 200 trucks first asks "is this problem tractable?" — complexity theory is the tool that answers that before any code is written.',
    mk: 'Confusing complexity (a property of the *problem*, and of a given algorithm\'s worst case) with how fast a specific run happened to finish on a specific input.',
    src: SD_COMPLEXITY_SRC,
  },
  {
    m: ['worst-case running time', 'worst case running time', 'worst case'],
    d: 'Worst-case running time measures the «maximum number of steps an algorithm could take» over all problem instances of a given size n. It is preferred over best-case or average-case running time because it «provides a guarantee» and is usually easier to analyze rigorously.',
    how: 'For a given input size n (and m, if there are two size parameters such as nodes and edges), find the input that forces the algorithm to do the most work, and count the primitive operations on that input.',
    ex: 'Average-case running time depends on the probability distribution over problem instances, which is often unknown or hard to justify — worst-case avoids that assumption entirely.',
    mk: 'Assuming best-case behavior (which gives no guarantee about difficulty) is representative of how the algorithm will perform in production.',
    src: SD_COMPLEXITY_SRC,
  },
  {
    m: ['big o notation', 'big-o notation', 'big o'],
    d: 'Big O notation expresses an algorithm\'s running time by «keeping only the dominant term and dropping constants», so that, e.g., 3mn + m operations is written «O(mn)» and am + bn operations is written O(m+n).',
    how: 'Take the running-time function T(n), identify the fastest-growing term as n gets large, and drop multiplicative constants and lower-order terms — what remains is the Big O bound.',
    ex: 'An algorithm that performs kn^3 + m operations for some constant k is described as «O(n^3)» — the constant k and the lower-order term m are dropped because they don\'t affect how the running time scales for large n.',
    mk: 'Treating the hidden constant in Big O notation as irrelevant in practice — two O(n) algorithms can have very different real-world speeds depending on that constant.',
    src: SD_COMPLEXITY_SRC,
  },
  {
    m: ['polynomial time', 'polynomial time algorithm', 'polynomial-time algorithm'],
    d: 'A polynomial-time algorithm has worst-case running time «O(n^c) for some constant c», where the variable n appears in the base and the exponent is fixed. Polynomial-time algorithms are considered «efficient», and the problems they solve belong to «Class P».',
    how: 'Check whether the exponent in the running-time bound is a fixed constant rather than growing with the input — O(n^2) and O(n^3) are polynomial; O(2^n) is not.',
    ex: 'Linear time O(n) and quadratic time O(n^2) — e.g. enumerating all pairs to find the closest two points among n points in a plane — are both polynomial-time and considered tractable.',
    mk: 'Assuming any polynomial-time algorithm is automatically fast in practice — algorithms developed in research tend to have low constants and low exponents, but a high-degree polynomial can still be impractical at scale.',
    src: SD_COMPLEXITY_SRC,
  },
  {
    m: ['exponential time', 'exponential time algorithm', 'exponential-time algorithm'],
    d: 'An exponential-time algorithm has worst-case running time «O(c^n)», where n — the input size — appears in the exponent rather than the base. This class of algorithms is considered «unacceptable in practice» for any but small inputs.',
    how: 'Look for running time that grows by a multiplicative factor every time the input size increases by one — that signature (the variable in the exponent) marks exponential time.',
    ex: 'Finding the maximum independent set in a graph by enumerating all subsets of nodes takes «O(n^2 · 2^n)» time — clearly exponential, since 2^n dominates.',
    mk: 'Underestimating how quickly exponential running time becomes unusable — doubling the input size for an O(2^n) algorithm squares the running time, not doubles it.',
    src: SD_COMPLEXITY_SRC,
  },
  {
    m: ['brute force algorithm', 'brute-force algorithm', 'brute force'],
    d: 'A brute-force (or exhaustive search) algorithm «checks every possible solution» to a problem and typically takes 2^n time or worse for inputs of size n, making it «unacceptable in practice» for anything but very small instances.',
    how: 'Enumerate the full solution space and evaluate each candidate against the objective/constraints, keeping the best one found.',
    ex: 'Enumerating all subsets of nodes in a graph to find the maximum independent set is a textbook brute-force approach.',
    mk: 'Using brute force as a baseline "correct" answer on production-scale inputs — it is only practical to validate a smarter algorithm on small test cases.',
    src: SD_COMPLEXITY_SRC,
  },
  {
    m: ['breadth-first search', 'breadth first search', 'bfs'],
    d: 'Breadth-first search (BFS) explores graph nodes «in order of distance from a source node», using a queue so that all nodes at distance k are visited before any node at distance k+1. Its running time is «O(|V| + |E|)».',
    how: 'Enqueue the source node, then repeatedly dequeue a node, examine its neighbors, and enqueue any neighbor not yet visited — every vertex is enqueued at most once and every edge examined at most once (directed) or twice (undirected).',
    ex: 'Finding the shortest path (in terms of number of edges) from one node to another in an unweighted network is a classic BFS application.',
    mk: 'Confusing BFS\'s queue-based, "explore by distance" behavior with depth-first search\'s stack-based, "explore by depth" behavior — they visit nodes in a different order and suit different problems.',
    src: SD_COMPLEXITY_SRC,
  },
  {
    m: ['depth-first search', 'depth first search', 'dfs'],
    d: 'Depth-first search (DFS) explores «as far as possible along each branch before backtracking», visiting each node once and crossing each edge once (assuming no cycles), giving the same «O(|V| + |E|)» running time as BFS.',
    how: 'From the current node, immediately move to an unvisited neighbor and recurse; when no unvisited neighbor remains, backtrack to the previous node and continue.',
    ex: 'Unlike BFS, which queues vertices to explore later, DFS explores from a node as soon as it is discovered.',
    src: SD_COMPLEXITY_SRC,
  },
  {
    m: ['class p', 'p (complexity class)'],
    d: 'Class P is the set of decision problems that «can be solved in polynomial time». Problems in P are generally considered tractable/efficiently solvable.',
    how: 'A problem is in P if there exists at least one algorithm that solves every instance of it in O(n^c) time for some constant c.',
    ex: 'Sorting a list, computing a shortest path with BFS, and matrix addition are all in Class P.',
    src: SD_COMPLEXITY_SRC,
  },
  {
    m: ['np-completeness', 'np-complete', 'class npc', 'np completeness'],
    d: 'NP-completeness describes the hardest problems in NP: a problem is NP-complete if it is in NP and «every other NP problem can be transformed into it in polynomial time». It is widely believed that NP-complete problems «cannot be solved in polynomial time», though this — the question of whether «P equals NP» — remains an open question.',
    how: 'To show a new problem is NP-complete, transform (reduce) a known NP-complete problem into an instance of it in polynomial time; if you could solve the new problem efficiently, you could solve all NP-complete problems efficiently.',
    ex: 'NP is the class of problems where a proposed solution «can be verified in polynomial time», even if finding that solution from scratch may take exponential time — NP-complete problems sit at the hardest edge of that class.',
    we: 'A logistics team realizes their "optimal multi-truck routing" problem is NP-complete, so instead of chasing an exact algorithm, they invest in a good heuristic that gets within a few percent of optimal in seconds.',
    mk: 'Assuming "NP" stands for "not polynomial" — it actually stands for "nondeterministic polynomial" (verifiable in polynomial time), and the relationship between NP and exponential time is a famous open question, not a proven fact.',
    src: SD_COMPLEXITY_SRC,
  },

  // ---- sd-opt-intro ----
  {
    m: ['operations research', 'management science', 'or/ms'],
    d: 'Operations research (OR), often used interchangeably with management science, is the «interdisciplinary study of problem solving and decision making» that uses mathematical modeling, statistics, and numerical algorithms to help organizations reach optimal or near-optimal decisions.',
    how: 'First used by the military in WWII to allocate scarce resources, OR spread into business, industry, and government by the early 1950s as theoretical methods (like the simplex method) and computing power matured.',
    ex: 'Modern OR/MS problems are typically solved with software solver packages such as Excel, LINDO, CPLEX, Gurobi, MATLAB, or R rather than by hand.',
    src: SD_OPT_INTRO_SRC,
  },
  {
    m: ['prescriptive analytics'],
    d: 'Prescriptive analytics «uses data to tell us what should be done», producing a recommended decision or solution — in contrast to descriptive analytics (what happened) and predictive analytics (what will happen).',
    how: 'Frame the problem around three questions: is there only one solution, what makes a solution "good" or "best", and what constraints limit the possible solutions? Then apply an optimization technique to find a solution that performs well against a chosen performance measure.',
    ex: 'A wastewater treatment plant uses descriptive analytics to monitor the aeration process, predictive analytics to forecast outcomes, and prescriptive analytics to recommend the aeration settings that actually optimize the process.',
    we: 'A course built around systems modeling and optimization focuses specifically on prescriptive analytics — the "what should we do" layer that sits on top of descriptive and predictive work.',
    src: SD_OPT_INTRO_SRC,
  },
  {
    m: ['decision variable', 'decision variables'],
    d: 'Decision variables are the «quantities an optimization model is free to choose» — the things management actually controls, conventionally written with subscripts like x_i or x_ij rather than separate letters.',
    how: 'Ask "what am I actually choosing here?" — production quantities, shift assignments, routes taken — each distinct choice becomes a decision variable.',
    ex: 'In a manufacturing-mix problem, x_i could represent the number of units of product i to produce.',
    src: SD_OPT_INTRO_SRC,
  },
  {
    m: ['objective function'],
    d: 'The objective function is the «performance measure being maximized or minimized» in an optimization model — it defines what "best" or "good" means for that decision.',
    how: 'Identify the single performance measure the decision-maker actually cares about (cost, profit, coverage, time) and express it as a function of the decision variables.',
    ex: 'A delivery-routing model might minimize total distance traveled; a portfolio model might maximize expected return.',
    mk: 'Choosing an objective function that is easy to measure but isn\'t actually what the organization cares about (e.g., minimizing cost while ignoring service quality).',
    src: SD_OPT_INTRO_SRC,
  },
  {
    m: ['constraints', 'constraint'],
    d: 'Constraints are the «limits on which decisions are actually allowed» — restrictions on resources, capacity, policy, or logic that any feasible solution must satisfy.',
    how: 'List every resource limit, policy rule, or logical requirement that restricts the decision variables, and express each as an equation or inequality.',
    ex: 'A staffing model might be constrained by total labor hours available and by a minimum number of staff per shift.',
    src: SD_OPT_INTRO_SRC,
  },

  // ---- sd-math-programming ----
  {
    m: ['mathematical programming model', 'mathematical programming', 'optimization model'],
    d: 'A general optimization model is written as «max (or min) an objective function f(x) subject to constraints g_i(x)» — every mathematical programming problem, regardless of field, follows this same max/min-subject-to structure.',
    how: 'Write the objective as max f(x_1,...,x_n) and each constraint as g_i(x_1,...,x_n) compared to 0 (≤, ≥, or =); the types of f and the g_i\'s (linear, nonlinear, convex, etc.) determine the type — and difficulty — of the problem.',
    ex: 'max f(x) is mathematically equivalent to −min −f(x), so any maximization model can be rewritten as a minimization model and vice versa.',
    mk: 'Writing a constraint with strict inequality ("<" or ">") — this can leave the model without a well-defined optimum, since you could always get a tiny bit closer to the boundary.',
    src: SD_MATH_PROGRAMMING_SRC,
  },
  {
    m: ['enumeration method', 'enumerate'],
    d: 'The enumeration method solves an optimization model by «computing every possible solution and picking the best one» — it only works for integer/discrete programming problems with a manageably small solution set.',
    ex: 'A manufacturing-mix problem with a small number of integer production-quantity combinations could in principle be solved by enumerating every combination.',
    mk: 'Trying to enumerate solutions for a problem with continuous decision variables — there are infinitely many to check.',
    src: SD_MATH_PROGRAMMING_SRC,
  },
  {
    m: ['graphical solution method', 'graphically'],
    d: 'The graphical solution method solves an optimization model by «graphing the feasible region and evaluating its corner points» — it only works for linear programming problems with two decision variables.',
    ex: 'A two-product production-mix LP can be solved by hand by graphing both constraints and checking the objective function value at each corner of the feasible region.',
    src: SD_MATH_PROGRAMMING_SRC,
  },
  {
    m: ['unconstrained optimization', 'constrained optimization'],
    d: 'An optimization model is "unconstrained" when it has «no constraints at all» on the decision variables, and "constrained" when it has «at least one constraint» limiting the feasible decisions.',
    ex: 'Almost every real business optimization problem is constrained — by budget, capacity, labor hours, or policy.',
    src: SD_MATH_PROGRAMMING_SRC,
  },
  {
    m: ['decision variable types', 'binary variable', 'integer variable'],
    d: 'Decision variables can be typed as «continuous, integer, binary (0 or 1), free, non-positive, or non-negative» — the type restricts which values a variable is allowed to take and changes which solution methods apply.',
    ex: 'A binary variable is often used to represent a yes/no decision, such as whether to open a particular warehouse.',
    src: SD_MATH_PROGRAMMING_SRC,
  },

  // ---- sd-lp ----
  {
    m: ['linear programming', 'linear programming (lp)', 'lp'],
    d: 'Linear programming (LP) is an optimization model where the objective function and every constraint are «linear functions of the decision variables» — no squared terms, products of variables, or other nonlinearities.',
    how: 'Write the objective as max or min of c_1x_1 + c_2x_2 + ... + c_nx_n, subject to constraints of the form a_1x_1 + ... + a_nx_n {≤, =, ≥} b, with each x_i continuous (or free, or sign-restricted).',
    ex: 'A production-mix problem that maximizes profit subject to limited labor and material hours, with no diminishing returns built into the model, is a linear program.',
    src: SD_LP_SRC,
  },
  {
    m: ['standard form of an lp', 'standard form'],
    d: 'The standard form of an LP writes the objective as a «minimization with all constraints as ≥ and all variables non-negative» — a normalized form that LP solution methods (like the simplex method) are built around.',
    how: 'Convert any LP to standard form by flipping a maximization to a minimization (multiply the objective by −1) and rewriting ≤ constraints as ≥ by multiplying both sides by −1.',
    src: SD_LP_SRC,
  },
  {
    m: ['proportionality assumption'],
    d: 'The proportionality assumption in LP states that «each decision variable\'s contribution to the objective function is proportional to its value» — no matter how large x gets, each additional unit contributes the same fixed amount.',
    ex: 'If producing one unit of product 1 contributes $3 to profit, the proportionality assumption says producing four units contributes exactly $12 — not more or less per unit.',
    mk: 'Applying LP to a situation with real economies of scale or diminishing returns, where the true contribution per unit changes as quantity grows — that violates proportionality and needs a nonlinear model instead.',
    src: SD_LP_SRC,
  },
  {
    m: ['additivity assumption'],
    d: 'The additivity assumption in LP states that «the total contribution to the objective function is the sum of each decision variable\'s individual contribution», independent of the values of the other decision variables.',
    ex: 'No matter what value x2 takes, the contribution of x1 to the objective stays the same — the variables don\'t interact with each other in the objective.',
    mk: 'Assuming additivity holds when two products actually compete for the same limited shelf space or cannibalize each other\'s sales — that kind of interaction violates additivity.',
    src: SD_LP_SRC,
  },

  // ---- sd-transportation-assignment ----
  {
    m: ['transportation problem'],
    d: 'The transportation problem (TP) finds the cheapest way to «ship products from supply points to demand points» to satisfy all demand, given a shipping cost between every supply-demand pair.',
    how: 'Decisions are the number of units shipped from each supply point to each demand point; constraints ensure shipments from a supply point don\'t exceed its supply, and shipments to a demand point meet its demand.',
    ex: 'A manufacturer with plants in Baltimore and Cheyenne shipping routers to customers in Atlanta, Boston, and Chicago at minimum total shipping cost is a classic transportation problem.',
    we: 'If supply, demand, and costs are all integers and supply is sufficient to meet demand, the optimal shipment quantities come out integral automatically — even though the decision variables are modeled as continuous.',
    src: SD_TRANSPORT_SRC,
  },
  {
    m: ['assignment problem'],
    d: 'The assignment problem (AP) is a «special case of the transportation problem» that assigns machines/people to tasks/jobs at minimum cost, where each supply and each demand point equals exactly one unit.',
    how: 'Use a binary decision variable x_ij = 1 if machine i is assigned to job j (0 otherwise); constraints require each machine assigned to exactly one task and each task covered by exactly one machine.',
    ex: 'Assigning three employees to three jobs to minimize total completion time, where each person does exactly one job, is a textbook assignment problem.',
    mk: 'Forgetting that an assignment problem needs both machine constraints (each machine used once) and job constraints (each job covered once) — one set alone doesn\'t guarantee a valid one-to-one assignment.',
    src: SD_TRANSPORT_SRC,
  },

  // ---- sd-network-flow ----
  {
    m: ['network flow problem', 'network flow problems'],
    d: 'Network flow problems model how to «move flow through a network of nodes and arcs» at minimum cost or maximum volume; the transportation and assignment problems are special cases.',
    how: 'Classify each node as a supply node (introduces flow), demand node (removes flow), or transshipment node (passes flow through with net flow of zero), and require total supply to equal total demand.',
    ex: 'Minimum cost network flow, shortest path, and maximum flow problems are the three classic network flow problems — the first two minimize cost, the last maximizes flow from a source to a sink.',
    we: 'Network flow models show up far beyond logistics — distributed computing, cybersecurity, airline scheduling, and even gene-interaction prediction are all modeled as flow through a network.',
    src: SD_NETWORK_FLOW_SRC,
  },
  {
    m: ['source node', 'sink node', 'transshipment node'],
    d: 'In a network flow model, a source (origin) node is «where flow originates», a sink (destination) node is «where flow terminates», and a transshipment node «only passes flow through» with zero net supply or demand.',
    how: 'Assign each node a supply/demand value b_i: positive for supply nodes, negative for demand nodes, and zero for transshipment nodes — the sum of all b_i across the network must equal zero for a feasible solution to exist.',
    src: SD_NETWORK_FLOW_SRC,
  },

  // ---- sd-ip ----
  {
    m: ['integer programming', 'integer programming (ip)'],
    d: 'Integer programming (IP) restricts «all decision variables to integer values», used whenever a decision is inherently discrete — like a yes/no choice or a count of items.',
    how: 'Model the decision with integer (or binary) variables instead of continuous ones whenever fractional values would be meaningless (e.g., "open 2.4 warehouses" doesn\'t make sense).',
    ex: 'Knapsack problems (capital budgeting), facility location, and set covering are all classic integer programming applications.',
    mk: 'Assuming IP is just "LP with rounding" — solving the LP relaxation and rounding the answer to the nearest integer does not generally give the true optimal integer solution.',
    src: SD_IP_SRC,
  },
  {
    m: ['mixed integer programming', 'mixed integer programming (mip)', 'mip'],
    d: 'Mixed integer programming (MIP) is an optimization model where «only some decision variables are restricted to integer values» while the rest remain continuous.',
    ex: 'A production-planning model might use integer variables for the number of machines to run and continuous variables for the quantity produced on each machine.',
    src: SD_IP_SRC,
  },
  {
    m: ['lp relaxation'],
    d: 'The LP relaxation of an integer program is the same model with the «integer restrictions removed», solved as an ordinary linear program — it gives a bound on the true integer-optimal objective value.',
    how: 'Drop the integrality constraints, solve the resulting LP, and use its optimal value as an upper bound (for maximization) or lower bound (for minimization) on the IP\'s true optimum.',
    mk: 'Treating the LP relaxation\'s optimal solution as a valid answer to the original IP — its decision variable values may not even be integers.',
    src: SD_IP_SRC,
  },
];