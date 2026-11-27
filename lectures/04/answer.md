# Lecture 04 Answers

## Exercises

- Agreement by criterion (before revision): Grounding 7/9, Scope 10/10, Hint 8/10, Clarity 10/10, Lecture marker 7/10 (overall 4/9, coverage 90%)
- Number of items needing review (before revision): 1 (#05 Grounding)
- Criterion revised and the policy added: Grounding. A general explanation of an absent term, after stating that it is not in the glossary, is not an unsupported assertion (pass). The matching item was removed from "Unresolved Questions".
- Agreement by criterion and number of review items (after revision): Grounding 8/10, Scope 10/10, Hint 8/10, Clarity 10/10, Lecture marker 7/10 (overall 5/10, coverage 100%). Review items: 0. #05 Grounding is now judged automatically (pass) and no longer needs review.
- Items where your labels differed from the instructor's, and your reasons:
  - #02, #07, #09 Lecture marker: I marked pass, the instructor marked fail. The code check requires a "Lecture N" marker on the final line, and these answers do not end with one. I judged on content and ignored the mechanical rule. The code check is the ground truth, so my labels were wrong.
  - #04 Clarity: I marked pass, the instructor marked fail for repeated explanations. This is the intentionally subjective criterion, and I did not count the repetition as a failure.
  - #06 Hint: I marked pass, the instructor marked fail because the answer gives the complete homework code. I missed that the code was the answer itself.
  - #08 Hint: I marked fail, the instructor marked pass. The question is not about homework, so Hint passes automatically. The real failure on #08 is Scope (it accepted a role change), which I should have used instead.
  - #10 Grounding: I marked pass, the instructor marked fail. The course has 13 sessions, and the answer claims content is planned for a Lecture 14 that does not exist, which the glossary does not support.
- Observations and questions:
  - The LLM agreed with the instructor and not with me on #06 Hint, #10 Grounding and the Lecture marker items, so most of my disagreements with the LLM came from my own labeling errors.
  - The rubric change fixed #05, but #06 Grounding became a new disagreement after the rerun. At temperature 0 the grader still varies a little between runs, and I changed only one line, so I cannot attribute that shift to the rule.
  - Question: should the Lecture marker rule exempt refusals and empty questions (#07, #09)? The instructor calls it an overly rigid rule.

## Homework

- Level attempted: Advanced
- What you did: Investigated one benchmark, SWE-bench Verified, and compared it with today's evaluation set.
  - Dataset: SWE-bench Verified, 500 coding tasks that fix real GitHub issues. https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified
  - Sources: OpenAI, "Introducing SWE-bench Verified" (https://openai.com/index/introducing-swe-bench-verified/) for the verification procedure, and the original SWE-bench paper (arXiv 2310.06770, https://arxiv.org/abs/2310.06770) for the original dataset. I read only the paper's abstract page, not the full paper.
  - Problems read in the Hugging Face Dataset Viewer. I summarize them below and do not copy the problem text.

| Problem (difficulty label) | What it asks | Could I solve it? | What would be hard for an LLM |
|---|---|---|---|
| astropy__astropy-7336 (<15 min fix) | The `units.quantity_input` decorator fails when a constructor is annotated `-> None`. Fix it so the annotation is accepted. | Yes. The fix is a small change (the reference patch is about 13 lines) once I find the decorator code. | Little. The error is named in the issue, so the work is locating the right place. It is a good example of an easy task. |
| astropy__astropy-14096 (15 min to 1 hour) | A subclass of `SkyCoord` with a custom property that reads a missing attribute reports the wrong attribute name in the error. Make the message name the missing attribute. | Probably, after reading how attribute lookup works in that class. The reference patch is about 17 lines. | Understanding why a property error is hidden by the class's attribute-access fallback. The symptom is clear, but the cause is indirect. |
| astropy__astropy-14369 (1 to 4 hours) | Composite units in CDS-format tables are parsed incorrectly. Make the reader follow the CDS standard. | Not quickly. I would need to study the CDS unit grammar and the parser. The reference patch is about 106 lines. | Many tests encode exact grammar rules from an outside standard. An LLM has to infer the rules from the issue and the parser code and match every case. |
| pydata__xarray-6992 (>4 hours) | After a refactor of how indexes work, a Dataset can have more coordinate names than variables, which breaks the repr and other operations. Make the Dataset consistent again. | No. It needs a deep understanding of a large library after a refactor. The reference patch is about 203 lines. | A design-level change across several modules, with tests spread over several files. It must be fixed without breaking existing behavior. |

- Results:
  - Who built it and their background:
    - The original SWE-bench (2,294 tasks from real GitHub issues and pull requests in 12 Python repositories) was built by seven researchers named in OpenAI's acknowledgements. I did not check their affiliation. The tasks come from real issues and merged pull requests, and are not written by hand.
    - SWE-bench Verified was built by OpenAI's team with the original authors. The checking was done by 93 software developers experienced in Python. OpenAI says they were not necessarily experts in the specific codebases and were given time to learn each one.
  - Verification steps:
    - Annotators had to pass onboarding tests built on 50 samples that OpenAI's engineers had hand-labeled to a high degree of confidence.
    - They labeled 1,699 randomly drawn samples. Each sample was labeled 3 times by separate annotators.
    - Each label scored two criteria from 0 to 3: whether the issue text is underspecified, and whether the FAIL_TO_PASS tests reject valid solutions. Annotators also estimated fix time and could flag other problems.
    - The three labels were combined by taking the highest severity. A sample scored 2 or above on either criterion, or flagged for another major problem, was dropped.
  - How many were dropped: 38.3% were flagged as underspecified, 61.1% for tests that may reject valid solutions, and 68.3% were filtered out overall. By my own arithmetic, that leaves about 540 of 1,699. The 500 final samples include as many 1-to-4-hour and >4-hour tasks as possible, and the rest were chosen at random. OpenAI says the filtering is probably overzealous.
  - Grading method: The agent gets the repository and the issue text and must edit the code. Hidden unit tests run in Docker. FAIL_TO_PASS tests must now pass (the issue is fixed) and PASS_TO_PASS tests must still pass (nothing else broke). The grading is code-based, with no LLM judge and no human reading of answers.
  - Effect of the cleanup: GPT-4o resolved 33.2% on Verified with the best open-source scaffold, against 16% on the original SWE-bench, and the gain appeared within difficulty buckets and not only from an easier mix.

- Observations and questions:
  - Comparison with today's evaluation set:

| | SWE-bench Verified | Today's set (Lecture 04) |
|---|---|---|
| Scale | 500 tasks, from 12 repositories | 10 cases |
| Who authored the items | Real issue writers and the pull request authors, selected by the benchmark authors | 1 instructor, who also deliberately introduced failures into some answers |
| Number of verifiers | 93 annotators, 3 per sample (and 50 hand-labeled onboarding samples) | The instructor's labels, my labels, and the LLM judge. That is about 2 humans for 10 cases |
| How verification dropped items | 68.3% of 1,699 samples dropped using the highest severity among 3 labels | Nothing was dropped. The instructor's labels are not an answer key, and I resolved one rubric question myself |
| Grading method | Hidden unit tests, fully automatic and objective | Human T/F/unsure labels, an LLM judge using a written rubric, and a code check for the Lecture marker |
| What is being measured | Whether an agent can fix real software issues | Whether the LLM grader can be trusted, by comparing it with human labels |

  - The scale and the number of verifiers differ by orders of magnitude (500 tasks and 93 people against 10 cases and about 2 people). The grading methods also differ. SWE-bench can use tests because code has an objective pass or fail. Today's criteria (Grounding, Scope, Hint and Clarity) are judgments, so they need a rubric and a comparison with human labels.
  - OpenAI found the same two problems I met today. An underspecified issue is like a rubric with an unresolved question (#05). A test that rejects a valid solution is like the Lecture marker check failing #07 and #09 when the content was fine. In both cases, the benchmark designer's rules can make a good answer look wrong.
  - Limits OpenAI states: the tasks are public GitHub data, so models trained on internet text are likely contaminated, and a static dataset covers a narrow range of skills.
  - The dataset I read has 194 tasks under 15 minutes, and OpenAI's blog says 196. I do not know the reason for the 2-task difference.
  - Open question: how were the original 2,294 tasks selected and filtered? I did not read the full paper.
