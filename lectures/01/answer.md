# Lecture 01 Answers

## Exercises

- Model's answer: It did not know the AIE2026-specific homework levels and asked for course materials.
- Glossary comparison: The levels are Basic (review lecture content), Implementation (write your own code), and Advanced (research and experimentation). Completing any one level completes the homework. The model appropriately did not guess.
- Token counts displayed (input / output): 18 / 79.

## Homework

- Levels completed: Basic, Implementation, and Advanced.

### Basic

Asked `What is machine learning? Answer in exactly one sentence.` three times using `gemini-3.5-flash-lite`:

| Temperature | Response time | Input tokens | Output tokens | Answer summary |
|---:|---:|---:|---:|---|
| 0.0 | 0.63 s | 12 | 27 | Learns from data and improves without explicit programming. |
| 0.7 | 0.65 s | 12 | 30 | Adds that learning improves performance on specific tasks. |
| 1.3 | 0.77 s | 12 | 30 | Similar to 0.7; mentions identifying patterns and specific tasks. |

All three answers had the same core meaning. Wording and token count varied slightly; the higher temperature did not make the response noticeably more diverse in this small sample.

### Implementation

Added `--interactive` mode to `app/ask.py`. It uses one SDK chat session for the initial question and follow-ups, retaining conversation history until `quit` or `exit`. Verified by asking the model to remember "cedar" and then asking for the remembered word; it answered correctly. The first turn used 11 input / 16 output tokens, and the follow-up used 38 input / 7 output tokens, showing the earlier conversation was included in the next request.

### Advanced

The command now reports response time around each model request and input/output tokens. For a model comparison, I used the same prompt, `What is machine learning? Answer in exactly one sentence.`, at each model's default temperature:

| Model | Response time | Input tokens | Output tokens | Answer summary |
|---|---:|---:|---:|---|
| `gemini-3.1-flash-lite` | 0.72 s | 12 | 31 | Learns patterns from data and improves task performance. |
| `gemini-3.5-flash-lite` | 0.68 s | 12 | 30 | Learns from data and improves task performance. |
| `gemini-3.5-flash` | 3.02 s | 12 | 28 | Learns from data to identify patterns and make predictions. |
| `gemini-3.6-flash` | 2.88 s | 12 | 30 | Learns patterns from data and makes decisions or predictions. |
| `gemini-3.8-flash` | 125.28 s | 12 | 26 | Learns patterns from data to make predictions or decisions. |

All five models gave similar one-sentence definitions, with output lengths of 26-31 tokens. Latency varied substantially; the 125.28 s result for `gemini-3.8-flash` is a single observation and may reflect transient service or network delay rather than typical performance.

Using `gemini-3.5-flash-lite` at its default temperature, changing the question also changed usage:

| Question | Response time | Input tokens | Output tokens |
|---|---:|---:|---:|
| What is a token in an LLM? | 0.72 s | 16 | 38 |
| What are the AIE2026 homework levels? | 0.72 s | 18 | 79 |

The course-specific question used more output tokens because the model explained that it did not know the course details. These are single observations, so latency and output length can vary between runs and do not establish typical model performance.

Free-tier rate limits can constrain requests and token throughput over time, and limits may differ by model and change. Longer answers and history-bearing follow-ups consume more input/output tokens; repeated calls can also reach request limits even when each response is short. A `429` means a limit was reached, so reduce repeated calls, wait before retrying, and check the current AI Studio quota for exact limits. The timings here measure response latency, not quota usage or total end-to-end setup time.
