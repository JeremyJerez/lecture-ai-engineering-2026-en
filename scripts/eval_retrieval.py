"""Lecture 05 Advanced homework: compare which evidence pages each retrieval method returns.

Run: uv run --no-sync --env-file .env python -m scripts.eval_retrieval

Only retrieval is run (query embedding, no answer generation), so it is cheap and repeatable.
For each question it reports how many of the pages that must / may support the answer were returned.
"""

from dataclasses import dataclass

from app import retrieval


@dataclass(frozen=True)
class Case:
    """A target question with the pages that must and may support a correct answer."""
    name: str
    question: str
    required: frozenset[str]
    supporting: frozenset[str]


CASES = (
    Case("Q1 compaction vs memory",
         "In the Lecture 03 examples, how does compaction differ from memory across sessions? "
         "Do all daily notes go into long-term memory?",
         frozenset({"lec03-main-p013", "lec03-main-p039", "lec03-main-p040"}), frozenset()),
    Case("Q2 FT vs RAG vs memory",
         "The course compares fine-tuning, RAG and agent memory. Which one fits adding new knowledge "
         "to a chatbot, and does agent memory count as the model learning?",
         frozenset({"lec02-main-p046", "lec03-main-p013"}),
         frozenset({"lec02-main-p047", "lec02-main-p050"})),
    Case("Q3 tool-failure checks",
         "How do the three checks when a tool fails relate to idempotency and to deciding that a task is done?",
         frozenset({"lec03-main-p045", "lec03-main-p044", "lec03-main-p027"}),
         frozenset({"lec03-main-p046", "lec03-main-p048"})),
    Case("Q4 limiting agent damage",
         "What mechanisms does Lecture 03 describe for limiting the damage an agent can do with its tools, "
         "such as approvals, permissions and isolation?",
         frozenset({"lec03-main-p024", "lec03-main-p025", "lec03-main-p051", "lec03-main-p053"}),
         frozenset({"lec03-main-p026", "lec03-main-p028", "lec03-main-p067"})),
    Case("Q5 hallucination to false success",
         "Lecture 02 says a model can confidently answer things it does not know. How does Lecture 03 deal "
         "with an agent that reports success after it actually failed?",
         frozenset({"lec02-main-p014", "lec03-main-p046"}),
         frozenset({"lec03-main-p044", "lec03-main-p045"})),
)


def vector_pages(question: str) -> list[str]:
    """Return the pages of normal vector search (Basic RAG)."""
    return [hit["page_id"] for hit in retrieval.search(question)]


def graph_pages(question: str) -> list[str]:
    """Return the pages of the course Graph method."""
    result = retrieval.search_graph(question)
    return [page["page_id"] for page in result["seeds"] + result["expanded"]]


def ranked_pages(question: str, bridge: bool, rerank: bool) -> list[str]:
    """Return the pages of the improved graph method with the chosen options."""
    result = retrieval.search_graph_ranked(question, bridge_related_terms=bridge, rerank=rerank)
    return [page["page_id"] for page in result["seeds"] + result["expanded"]]


METHODS = {
    "A vector top-5 (Basic RAG)": vector_pages,
    "B course Graph": graph_pages,
    "C0 graph + rerank": lambda q: ranked_pages(q, bridge=False, rerank=True),
    "C1 graph + related terms": lambda q: ranked_pages(q, bridge=True, rerank=False),
    "C2 graph + related terms + rerank": lambda q: ranked_pages(q, bridge=True, rerank=True),
}


def main() -> None:
    """Print one table row per question and method."""
    print(f"{'question':<36}{'method':<36}{'pages':>6}{'required':>10}{'supporting':>12}{'relevant%':>11}")
    for case in CASES:
        for name, method in METHODS.items():
            pages = method(case.question)
            hit_required = len(case.required & set(pages))
            hit_supporting = len(case.supporting & set(pages))
            relevant = 100 * (hit_required + hit_supporting) / len(pages)
            print(f"{case.name:<36}{name:<36}{len(pages):>6}"
                  f"{f'{hit_required}/{len(case.required)}':>10}{f'{hit_supporting}/{len(case.supporting)}':>12}"
                  f"{relevant:>10.0f}%")
        print()


if __name__ == "__main__":
    main()
