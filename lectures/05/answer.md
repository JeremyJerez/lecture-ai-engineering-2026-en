# Lecture 05 Answers

## Exercises

- Answering model (`[model]` shown during execution): `gemini-3.5-flash-lite`
- Comparison question: "In Lecture 02, what does LoRA freeze and what does it train? What does QLoRA add?"
- Target materials (also record the difference in scope between full context and the other methods): Full context passed all 9 documents (438 pages, 233,723 characters). Vector search, Tree and Graph used only the main materials for Lectures 01 to 03 (214 pages). The `data/rag_data/` files are the Japanese originals from the pinned revision, so all answers are in Japanese.

### Results by Method

The correct answer, from Lecture 02 p.52: LoRA keeps the original weights fixed and trains only two small low-rank matrices A and B; QLoRA also compresses the original weights to 4 bits. All four answers say this. Each method was run once (one run, no repetition).

| Method | Key points and correctness of the answer | Cited pages and evidence | Time (seconds) | Input/output tokens | Model responses | Estimated generation API cost (USD) |
|---|---|---|---|---|---|---|
| Full context | Correct. Original weights fixed, a small added part trained; QLoRA adds 4-bit compression. Short answer. | Lecture 02 main p.52, and Lecture 02 exercise p.21 (a page outside the 214-page scope of the other methods; I did not read it) | 3.97 | 117,027 / 181 | 1 | 0.035561 |
| Vector search | Correct. Frozen original weights, trained low-rank matrices A and B; QLoRA adds 4-bit compression. | Lecture 02 p.51 and p.52 | 5.42 | 3,005 / 237 | 2 | 0.001494 |
| Tree | Correct. Same content, with the extra detail that less than 1% of the parameters can be trained. | Lecture 02 p.51 to 52 (the model opened both pages) | 6.17 | 13,694 / 384 | 6 | 0.005068 |
| Graph | Correct. Same content; adds that one GPU can tune a large model. | Lecture 02 p.51 and p.52 | 7.61 | 16,474 / 308 | 3 | 0.004612 |

The first Tree run failed with a `ConnectTimeout` (a network error on this machine, before any answer). I ran it again and the table shows only the second run. Full context was accepted without an input-limit error. No cost was unavailable.

- Pages found by running search alone, and what their text confirmed: `python -m app.retrieval "LoRA QLoRA difference"` returned five Lecture 02 pages in this order: p.52 (LoRA and QLoRA), p.51 (PEFT), p.60 (today's exercise), p.47 (RAG versus fine-tuning, which mentions LoRA only through a research result) and p.61 (exercise instructions). Only p.52 states what is frozen and trained, and p.51 supports it. By title, p.60 and p.61 are exercise pages that share the terms and are not evidence for the answer. I read the text of p.52 and p.47 in the data file.
- Tool calls shown by `--trace`:
  - Vector search: one call, `search_materials({'query': 'LoRA freeze train QLoRA add'})`.
  - Graph: two calls, `search_graph({'query': 'LoRA freeze train QLoRA'})` and then `search_graph({'query': 'term:lora'})`. The second query is a term node ID that the model took from the first result.
  - Tree: five calls, `browse_tree({})`, then `lec02-main`, then the section `lec02-main-s045` ("when and how to fix the chosen model"), then the pages `lec02-main-p051` and `lec02-main-p052`. The path was lecture list, Lecture 02, section, page.
  - Full context: no tool calls.
- Examples where retrieved information was insufficient, or was retrieved but not used in the answer: None for this question; every method found p.52. Tree and Graph used about 4.6 and 5.5 times the input tokens of vector search for the same evidence. For Graph, the second search added nothing the first had not already returned, as far as the answers show (I did not compare the two tool outputs in full).
- Method you would adopt for this use case, your reasons, and limitations of the comparison conditions: Vector search for a question like this one, where a single page holds the answer. It used 3,005 input tokens and cost $0.0015, against $0.0356 for full context (about 24 times more) and $0.005 for Tree and $0.0046 for Graph. Limits: one run per method, one question, a model that picks its own search terms, and full context covering a larger scope than the others. The time differences (4 to 8 seconds) are small and can come from the network.
- Observations and questions: Full context answered correctly and fastest, because it needed one model call. This shows that a long input does not always fail. Its cost grows with the whole corpus on every question, though. It cited a page from an exercise document (Lecture 02 exercise p.21) that the scoped methods cannot reach, so the scopes are not equal. I did not check whether that page supports the answer. Question: for questions with no single answer page, does the order of cost and quality stay the same? The Advanced homework below tests this with five more questions.

## Homework

<!-- Completing any one of Basic, Implementation, or Advanced is sufficient. -->

- Level attempted: Advanced

### What I did

I improved the Graph method and compared it with Basic RAG (vector search) and the course Graph on the same questions.

**Problem with the course Graph.** `search_graph` takes the top 3 vector hits as seeds and expands them over `next_page` and `mentions` edges for 2 hops. It then orders the expanded pages by hop count and term frequency, so the order has nothing to do with the question. Pages that only sit next to a seed in slide order get in. For example, Lecture 03 appendix pages (p63 to p69) filled the expanded slots for the questions about memory (Q1) and about limiting an agent's damage (Q4). The graph also contains 141 `related_term` edges that it never uses.

**New method: `search_graph_ranked`** (added with the flag `--graph-ranked`).

- *Data shape and storage (unchanged, nothing was rebuilt).* One page per chunk, 214 pages from Lectures 01 to 03. `graph.json` has 438 page nodes, 72 term nodes, 25 section nodes, 9 document nodes, and the edges `mentions` (1,081), `contains` (472), `next_page` (429) and `related_term` (141). The 768-dimension page embeddings are stored in SQLite (`sqlite-vec`, table `chunks` in `index.sqlite3`).
- *Search.*
  1. Embed the query once and take the top 3 pages as seeds, as the course Graph does.
  2. Collect candidate pages within 2 hops over `next_page` and `mentions`. A route may also use one `related_term` step between two terms at no hop cost, so a term can lead to the pages of a closely related term.
  3. Sort the candidates by cosine distance to the query. The distances are computed from the embeddings already in the database, so there is no extra API call.
  4. Return 3 seeds plus the 7 closest candidates. This is the same budget of 10 pages as the course Graph, and the output has the same shape.
- *Reasons.* Ordering by similarity to the question uses information the database already holds and removes the query-independent ordering. A `related_term` step lets a route cross from one topic to a neighboring one. I limited a route to one such step. In a debug run with unlimited steps, the candidate pool grew from 93 to 168 pages. The route that reached Lecture 02 p.14 passed through 6 unrelated terms (tools, rate limit, token and others), so the pages it found were off topic.
- *Held fixed.* Same model, same materials, same instructions. `GRAPH_RANKED_INSTRUCTIONS` is `GRAPH_INSTRUCTIONS` with only the tool name replaced. The tool description differs slightly, because it mentions related terms and ordering by similarity.

Files changed: `app/retrieval.py` (`search_graph_ranked` and four small helpers), `app/tools.py` (new tool), `app/agent.py` (flag and instructions), and `scripts/eval_retrieval.py` (retrieval-only comparison). The existing 17 tests still pass. I copied `data/rag_data/` (the four files linked in the instructions, at the pinned revision) into the working tree. They are Japanese materials, so every answer came back in Japanese, even for English questions.

### Comparison questions and conditions held fixed

- Model `gemini-3.5-flash-lite` (default settings, not temperature 0). Target materials: Lectures 01 to 03 main materials only (214 pages), for all three methods. Full context was not used, because its scope is 438 pages.
- Methods: **A** Basic RAG (`search_materials`, top 5), **B** course Graph (`--graph`), **C** my method (`--graph-ranked`).
- Questions (evidence pages chosen by reading the page text; "required" pages must support a correct answer, "supporting" pages help):

| # | Question | Required pages | Supporting pages | Why chosen |
|---|---|---|---|---|
| Q1 | In the Lecture 03 examples, how does compaction differ from memory across sessions? Do all daily notes go into long-term memory? | L03 p13, p39, p40 | none | Instruction example; several pages in one part |
| Q2 | The course compares fine-tuning, RAG and agent memory. Which one fits adding new knowledge to a chatbot, and does agent memory count as the model learning? | L02 p46, L03 p13 | L02 p47, p50 | Compares related terms across two lectures |
| Q3 | How do the three checks when a tool fails relate to idempotency and to deciding that a task is done? | L03 p27, p44, p45 | L03 p46, p48 | Evidence in three parts of one lecture |
| Q4 | What mechanisms does Lecture 03 describe for limiting the damage an agent can do with its tools, such as approvals, permissions and isolation? | L03 p24, p25, p51, p53 | L03 p26, p28, p67 | A list that needs 7 or more pages |
| Q5 | Lecture 02 says a model can confidently answer things it does not know. How does Lecture 03 deal with an agent that reports success after it actually failed? | L02 p14, L03 p46 | L03 p44, p45 | Question with two parts in two lectures |
| Q6 | What are the measured average response time and accuracy of the RAG system we just built? | none (not in the materials) | none | Unanswerable; the correct answer says so |

- Runs: 3 runs per question and method (54 runs). In each run the order was Q1 to Q6, and within a question A, then B, then C, with a 2-second pause. The model writes its own search query, so the queries differ between runs.

### Results

**1. Retrieval only** (`uv run --no-sync --env-file .env python -m scripts.eval_retrieval`; deterministic; pages returned that are required / supporting):

| Method | Pages returned | Q1 req | Q2 req / sup | Q3 req / sup | Q4 req / sup | Q5 req / sup |
|---|---|---|---|---|---|---|
| A vector top-5 | 5 | 3/3 | 2/2, 1/2 | 3/3, 2/2 | 3/4, 2/3 | 1/2, 2/2 |
| B course Graph | 10 | 2/3 | 2/2, 1/2 | 3/3, 2/2 | 2/4, 3/3 | 1/2, 2/2 |
| C0 graph + rerank | 10 | 3/3 | 2/2, 1/2 | 3/3, 2/2 | 3/4, 3/3 | 1/2, 2/2 |
| C1 graph + related terms (no rerank) | 10 | 2/3 | 2/2, 1/2 | 3/3, 2/2 | 2/4, 2/3 | 1/2, 2/2 |
| C2 graph + related terms + rerank (my method) | 10 | 3/3 | 2/2, 1/2 | 3/3, 2/2 | **4/4**, 3/3 | 1/2, 2/2 |

Only 20% to 70% of the 10 pages from the graph methods are evidence pages, against 60% to 100% of the 5 pages from vector search. Reranking alone (C0) recovers the missed page on Q1 and one of the two missed pages on Q4. The related-term step helps only together with reranking (C2 on Q4). Without reranking it pushes out evidence (C1 on Q4: supporting pages fall from 3/3 to 2/3).

**2. End to end, required and supporting pages cited in the answer** (the citation "Lecture N / PDF p.N" in the answer text, parsed by a script; each cell lists the three runs):

| Question | A Basic RAG, required | B Graph, required | C Ranked, required |
|---|---|---|---|
| Q1 (3) | 2, 3, 2 | 2, 2, 2 | 2, 3, 3 |
| Q2 (2) | 2, 2, 2 | 2, 2, 2 | 2, 2, 2 |
| Q3 (3) | 2, 2, 3 | 3, 3, 3 | 2, 1, 2 |
| Q4 (4) | 3, 3, 3 | 2, 2, 2 | 3, 3, 4 |
| Q5 (2) | 1, 1, 1 | 1, 1, 1 | 1, 1, 1 |
| **Total required** | **32/42 (76%)** | **30/42 (71%)** | **32/42 (76%)** |
| **Total supporting** | 15/27 (56%) | 15/27 (56%) | 18/27 (67%) |

**3. Time, tokens and cost** (mean per run over Q1 to Q5, 15 runs per method; cost is the estimated generation cost shown by `[cost]`, which excludes embedding):

| Method | Search calls | Time (s) | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|---|
| A Basic RAG | 1.67 | 8.4 | 5,160 | 430 | 0.00259 |
| B Graph | 1.07 | 7.1 | 5,374 | 428 | 0.00250 |
| C Ranked graph | 1.13 | 7.4 | 6,317 | 434 | 0.00280 |

**4. Unanswerable question Q6** (9 runs): all nine answers said that the materials contain no measured response time or accuracy. None invented a number. Some added a page that is on topic but not evidence (Lecture 02 p.13, about running a test several times). Input tokens ranged from 5,817 to 17,145 for the ranked graph and 14,214 to 15,389 for the course Graph, against 7,737 to 8,076 for Basic RAG. The graph methods return 10 pages per call and often searched twice, which probably explains most of the difference.

Example `--trace` (Q4, method C, run 1): one call, `search_graph_ranked({'query': 'Lecture 03 agent tools damage limitations approvals permissions isolation'})`, then `[time] 4.94 seconds`, `[usage] Input 5,580 tokens / Output 410 tokens / Model responses 2`, `[cost] $0.002699 USD`. Its answer cited L03 pp.24, 25 to 26, 52 to 53 and 67.

### Improvements, failures and limitations

- **Improved: Q4 (list question).** The course Graph returned 2 of 4 required pages and its answers cited 2 of 4 every time. My method returned all 4 pages in retrieval, and the answers cited 3, 3 and 4 of 4. Basic RAG cited 3 of 4 every time.
- **Improved: Q1.** The course Graph never reached L03 p13 in retrieval (2/3). With reranking, retrieval had 3/3, and the answers cited 2, 3 and 3 (course Graph: 2, 2, 2).
- **Failure: Q3.** My method was worse than the course Graph here (cited required pages 2, 1 and 2, against 3, 3 and 3). In the retrieval-only test (the question text as the query) my method returned all three required pages. In run 2 the model made two searches with its own queries (14,070 input tokens) and wrote an answer about idempotency and about "done" that cites only L03 p45 to 46, not p27 or p44. I did not save the full tool output, so I cannot tell whether those pages were retrieved and not cited, or not retrieved with the model's queries. I did not find the cause.
- **Failure: Q5 (two-part question).** No method's answer cited L02 p14 in any run, and the retrieval-only test did not return it either. In all nine runs the model made a single search, and its query covered only the Lecture 03 half (for example "Lecture 03 agent success failure"). A route from Lecture 03 p46 to the page about hallucination needs about 6 `related_term` steps, so a graph limited to one step cannot connect them. The likely fix is to split the question into two searches, which is the model's job, not the graph's.
- **Cost.** My method uses about 22% more input tokens than Basic RAG (6,317 against 5,160), because it returns 10 pages and only part of them is evidence.
- **Limits of this comparison.** Five questions with three runs each is too little to rank methods: a difference of a single page in one run moves a total by 2 percentage points or more. Citations are not the same as correctness. I read only some answers in full (Q1 ranked run 1, Q3 run 2 for both graph methods, Q4 ranked run 1, and the Q6 answers), and I did not grade every answer for correctness. The citation parser may miss unusual formats. Time differences of 1 to 2 seconds are within the noise of the API. The evidence pages are my own judgment, and I defined "required" before looking at the results of the end-to-end runs.

### Would I adopt it?

Not as the default. On these questions it matches Basic RAG on required pages (76% each), gains a little on supporting pages (67% against 56%), and costs more tokens. It clearly beats the course Graph only on list-style questions (Q4) and on Q1, and it loses on Q3. For a course question-answering use case, I would keep vector search as the default and use the ranked graph as an option for questions that need many pages, such as Q4. Before relying on it, I would run more questions and repeat each more times. I would also add a step that splits two-part questions (Q5), because the graph cannot fix that.

### Observations and questions

- Why did the course Graph stop at 2 of 4 on Q4 with the same seeds as my method? The seeds are identical, so the gain comes from the candidate pool and from the order of the 7 expanded slots. In the ablation, reranking gave most of the gain, and the related-term step added to it only on Q4. This rests on five questions, so I cannot say it holds in general.
- Is p14 (hallucination) simply too far away in the graph, or is the term graph too coarse? 72 terms for 438 pages means a term such as "LLM" links many unrelated pages (it has 71 `mentions` edges, one of the most connected terms).
- All answers were in Japanese, because the materials are. For an English course the localized materials are needed before this comparison is meaningful for English users.

### AI tool use

I used Kiro (an AI coding assistant) to write `search_graph_ranked`, `scripts/eval_retrieval.py` and the run and summary scripts, and to run all the experiments above. Everything here was run on my machine with my own `GEMINI_API_KEY`, and the code was checked with the repository's tests (17 passed). The evidence pages were chosen by reading the page text in `lectures.json`.
