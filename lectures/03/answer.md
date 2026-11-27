# Lecture 03 Answers

## Exercises

- **Differences between the Lecture 01 (bare LLM) and agent answers**:
  - In **Lecture 01 (`app.ask`)**, the bare LLM had no access to course-specific data, so when asked `"What are the 3 homework levels in the AIE2026 course?"`, it stated that it did not know the AIE2026-specific levels and asked for the course syllabus.
  - In **Lecture 03 (`app.agent`)**, the agent first called `search_glossary({'query': 'homework levels'})`, retrieved the `homework-levels` entry from `data/glossary.json`, and accurately explained the three levels (**Basic**: review lecture content, **Implementation**: write your own code, **Advanced**: research and experimentation), noted that completing any one level fulfills the homework (and is ungraded), guided the learner on how to choose, and ended with `(Lecture 01)`.

- **Tool calls shown by `--trace` (tool names and arguments)**:
  - For `"What is the difference between LoRA and QLoRA?"`:
    - `[tool call] search_glossary({'query': 'LoRA'})`
    - `[tool call] search_glossary({'query': 'QLoRA'})`
  - For `"Give me one review question from Lecture 02"`:
    - `[tool call] make_quiz({'lecture': 2})`

- **Number of LLM calls for one question (`requests`)**:
  - `requests=2` (with `tool_calls=2` for the LoRA vs. QLoRA question, `input_tokens=1305`, `output_tokens=212`; and `requests=2`, `tool_calls=1`, `input_tokens=858`, `output_tokens=75` for the Lecture 02 review question).
  - Explanation: Request 1 sends the user prompt, system instructions, and tool schemas to the LLM, which decides to emit tool call(s). Request 2 sends the tool return value(s) back to the LLM so it can synthesize the final response.

- **Tool added and the description in its docstring**:
  - Tool function: `make_quiz(lecture: int) -> str` in `app/tools.py` (registered via `agent.tool_plain(tools.make_quiz)` in `app/agent.py`).
  - Docstring:
    ```text
    Create one review question and its reference answer from the glossary for a given lecture session (an integer starting at 1).

    Use when asked for a review question or quiz from a specific session, such as "Give me one review question from Lecture 02".
    ```

## Homework

- **Level attempted**: Advanced — Option (a): Rebuild the learning support agent with Google ADK (`google-adk`).

- **What you did**:
  1. Created `adk_agent/glossary_agent/__init__.py` and `adk_agent/glossary_agent/agent.py` to assemble `root_agent` using `google.adk.agents.Agent`.
  2. Reused `INSTRUCTIONS` from `app/agent.py` and the plain Python tool functions (`tools.search_glossary`, `tools.get_lecture_summary`, and `tools.make_quiz`) from `app/tools.py` without modifying `app/` beyond the exercise requirements.
  3. Ran the ADK agent interactively from the repository root using:
     ```bash
     PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
     ```
  4. Tested the exact same three exercise questions (`"What are the 3 homework levels in the AIE2026 course?"`, `"What is the difference between LoRA and QLoRA?"`, and `"Give me one review question from Lecture 02"`) and compared both the code structure and runtime outputs against the Pydantic AI implementation.

- **Results**:

  ### 1. Code & Architecture Comparison (Pydantic AI vs. Google ADK)

  | Aspect | Pydantic AI (`app/agent.py`) | Google ADK (`adk_agent/glossary_agent/agent.py`) |
  |---|---|---|
  | **Agent Initialization** | `agent = Agent(instructions=INSTRUCTIONS)` (model can be deferred to `run_sync(..., model=build_model())` for easy `TestModel` injection) | `root_agent = Agent(model="gemini-3.5-flash-lite", name="glossary_agent", instruction=INSTRUCTIONS, tools=[...])` (`name` is required; uses `instruction=` singular) |
  | **Tool Registration** | Imperative via `agent.tool_plain(fn)` or decorator `@agent.tool_plain`, or passed via `tools=[...]` | Declarative list of plain Python functions passed directly to `tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz]` |
  | **Tool Schema Generation** | Inspects function signature, type hints, and docstring | Inspects function signature, type hints, and docstring identically |
  | **Execution / CLI Loop** | Custom CLI written with `argparse` + `agent.run_sync(...)` (single-turn unless a loop with `message_history` is coded manually) | Built-in multi-turn interactive CLI runner (`adk run adk_agent/glossary_agent`) and web UI (`adk web`) out of the box |

  ### 2. Output Comparison on Exercise Questions

  - **Q1: `"What are the 3 homework levels in the AIE2026 course?"`**
    - **Pydantic AI**: Looked up `homework-levels` via `search_glossary`, listed Basic, Implementation, and Advanced, explained that completing any one level suffices, offered guidance on choosing a level, and ended with `(Lecture 01)`.
    - **Google ADK**: Called `search_glossary`, accurately listed Basic, Implementation, and Advanced from the glossary, reminded the student that completing any one level is sufficient, and ended with `(Lecture 01)`.
  - **Q2: `"What is the difference between LoRA and QLoRA?"`**
    - **Pydantic AI**: Called `search_glossary` twice (`'LoRA'` and `'QLoRA'`), contrasted low-rank adapters on frozen weights vs. 4-bit base weight quantization + LoRA, posed a guiding reflection question on GPU memory bottlenecks, and ended with `Lecture 02`.
    - **Google ADK**: Called `search_glossary` for both terms, explained low-rank decomposition in LoRA vs. 4-bit base weight quantization in QLoRA, asked a guiding question about hardware bottlenecks, and ended with `(Lecture 02)`.
  - **Q3: `"Give me one review question from Lecture 02"`**
    - **Pydantic AI**: Called `make_quiz({'lecture': 2})`, presented *"What does Pretraining mean?"*, gave a thinking hint without spoiling the reference definition, and ended with `(Lecture 02)`.
    - **Google ADK**: Called `make_quiz(lecture=2)`, presented *"What does Quantization mean?"*, gave a thinking hint about moving from 16-bit to 4-bit precision without revealing the answer directly, and ended with `(Lecture 02)`.

- **Observations and questions**:
  - **Portability of Tools and Instructions**: Because both Pydantic AI and Google ADK derive tool schemas directly from Python type annotations (`query: str`, `lecture: int`) and docstrings, the exact same `app/tools.py` functions and `INSTRUCTIONS` worked in ADK with zero changes to the tool code.
  - **Multi-turn Session State**: `adk run` automatically maintains conversation history across turns in the terminal session, whereas `app/agent.py` runs a single question per invocation unless `message_history` is explicitly passed in a loop.
  - **Testing Ergonomics**: Pydantic AI's ability to instantiate `Agent(instructions=INSTRUCTIONS)` without binding a live model up front—and override it with `TestModel()` in `pytest`—makes deterministic unit testing without API keys very ergonomic.
