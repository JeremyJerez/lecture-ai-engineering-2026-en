"""Lecture 01: a script that asks a bare LLM a single question.

Usage:
    uv run python -m app.ask "What is LoRA?"
    uv run python -m app.ask            # Ask a course-specific question if none is supplied

A "bare" call with no tools or conversation history.
Check that, when asked about course-specific information, it either says "I don't know"
or gives a plausible general answer (which differs from the actual course).
(In Lecture 03, improve it by making an agent that can search the glossary.)
"""

import argparse
from time import perf_counter

from google import genai
from google.genai.chats import Chat
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# A course-specific question. The correct answer is in homework-levels in data/glossary.json
DEFAULT_QUESTION = "What are the 3 homework levels in the AIE2026 course?"


def ask(question: str, chat: Chat) -> str:
    started_at = perf_counter()
    response = chat.send_message(question)
    elapsed = perf_counter() - started_at

    print(f"[time] response={elapsed:.2f}s")
    if response.usage_metadata is not None:
        print(
            f"[tokens] input={response.usage_metadata.prompt_token_count} "
            f"output={response.usage_metadata.candidates_token_count}"
        )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a bare LLM a question")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="continue the conversation with follow-up questions",
    )
    parser.add_argument("--temperature", type=float)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    if args.temperature is not None:
        print(f"[temperature] {args.temperature}")
    print(f"[question] {args.question}\n")
    try:
        client = genai.Client(api_key=get_api_key())
        config = (
            genai.types.GenerateContentConfig(temperature=args.temperature)
            if args.temperature is not None
            else None
        )
        chat = client.chats.create(model=MODEL, config=config)
        print(ask(args.question, chat))
        while args.interactive:
            try:
                question = input("\nYou (type 'quit' to exit): ").strip()
            except EOFError:
                break
            if question.lower() in {"quit", "exit"}:
                break
            if question:
                print(f"\n{ask(question, chat)}")
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
