"""Lecture 05: page-level vector search."""

import argparse
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from collections import defaultdict, deque
from pathlib import Path

from google import genai
from google.genai import types
from pydantic_ai.exceptions import ModelHTTPError
import sqlite_vec

from app.config import (
    EMBEDDING_DIMENSIONS, EMBEDDING_MAX_TOKENS, EMBEDDING_MODEL,
    RAG_DB, RAG_DOCUMENT_IDS, RAG_SOURCE, RAG_TOP_K, RAG_TREE, get_api_key,
    RAG_GRAPH, GRAPH_START_K, GRAPH_HOPS, GRAPH_MAX_RESULTS,
)


def get_all_materials() -> str:
    """Combine all materials into one string with lecture, section, and page metadata."""
    documents = json.loads(RAG_SOURCE.read_text(encoding="utf-8"))
    return "\n\n".join(
        f"Document: {document['id']} / {document['title']}\n"
        f"Section: {section['section']}\n"
        f"Page: PDF p.{page['page']} / {page['title']}\n{page['content']}"
        for document in documents
        for section in document["content"]
        for page in section["content"]
    )

def load_pages(source: Path = RAG_SOURCE) -> list[dict]:
    """Convert document → section → page JSON into a page list for the selected materials."""
    documents = json.loads(source.read_text(encoding="utf-8"))
    pages = []
    for document in documents:
        if document["id"] not in RAG_DOCUMENT_IDS:
            continue
        for section in document["content"]:
            for page in section["content"]:
                pages.append({"page_id": page["id"], "document_id": document["id"],
                              "lecture": int(document["id"][3:5]), "document_title": document["title"],
                              "section": section["section"], "title": page["title"],
                              "page": page["page"], "content": page["content"]})
    return pages


def browse_tree(node_id: str | None = None) -> dict:
    """Return the first sentence for child pages and the full text for the selected page itself."""
    tree = json.loads(RAG_TREE.read_text(encoding="utf-8"))
    tree["children"] = [node for node in tree["children"] if node["id"] in RAG_DOCUMENT_IDS]
    node_id = node_id or tree["id"]
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}

    def describe(node, full=False):
        info = {key: node[key] for key in ("id", "kind", "title")}
        if node["kind"] == "page":
            info.update({key: value for key, value in pages[node["id"]].items() if key != "page_id"})
            if not full:
                info["content"] = re.split(r"(?<=[。！？])|\n", info["content"].strip(), maxsplit=1)[0]
        return info

    remaining = [tree]
    while remaining:
        node = remaining.pop()
        if node["id"] == node_id:
            return {
                "node": describe(node, full=True),
                "children": [describe(child) for child in node.get("children", [])],
            }
        remaining.extend(node.get("children", []))
    raise ValueError("The requested table-of-contents node was not found.")


def read_page(page_id: str) -> dict:
    """Return text and citation metadata for one specified page from the main materials for Lectures 01–03."""
    for page in load_pages(RAG_SOURCE):
        if page["page_id"] == page_id:
            return page
    raise ValueError("The requested page was not found.")


def normalized_vector(values: list[float]) -> list[float]:
    """Normalize the vector to unit length."""
    norm = math.hypot(*values)
    if norm == 0:
        raise ValueError("The embedding is a zero vector.")
    return [value / norm for value in values]


def embed_text(text: str, task_type: str) -> list[float]:
    """Embed text with Gemini. Stop instead of truncating if the input limit is exceeded."""
    with genai.Client(api_key=get_api_key()) as client:
        count = client.models.count_tokens(model=EMBEDDING_MODEL, contents=text).total_tokens
        if count is None or count > EMBEDDING_MAX_TOKENS:
            raise ValueError(f"Embedding input exceeds the limit or could not be measured: {count} tokens.")
        response = client.models.embed_content(
            model=EMBEDDING_MODEL, contents=text,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBEDDING_DIMENSIONS),
        )
    embedding = response.embeddings[0]
    if embedding.statistics and embedding.statistics.truncated:
        raise ValueError("The embedding API truncated the text.")
    return normalized_vector(embedding.values)


@contextmanager
def open_index(path: Path):
    """Open an existing search database read-only and close it on exit."""
    if not path.is_file():
        raise FileNotFoundError("Search database not found.")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        db.row_factory = sqlite3.Row
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        yield db
    finally:
        db.close()


def search(query: str) -> list[dict]:
    """Embed the query and return up to RAG_TOP_K similar pages."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("The search query is empty.")
    with open_index(RAG_DB) as db:
        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
        rows = db.execute("""
            SELECT page_id, document_id, lecture, document_title, section, title, page, content,
                   vec_distance_cosine(embedding, ?) AS distance
            FROM chunks ORDER BY distance, page_id LIMIT ?
        """, (sqlite_vec.serialize_float32(vector), RAG_TOP_K))
        return [dict(row) for row in rows]


def search_graph(query: str) -> dict:
    """Start with vector search, then expand candidates through adjacent pages and shared terms."""
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in graph["nodes"]
             if node["kind"] == "term" or node["id"] in pages}
    adjacent = defaultdict(set)
    for edge in graph["edges"]:
        a, b = edge["source"], edge["target"]
        if edge["relation"] in ("next_page", "mentions") and a in nodes and b in nodes:
            adjacent[a].add(b)
            adjacent[b].add(a)

    seeds = [hit for hit in search(query) if hit["page_id"] in pages][:min(GRAPH_START_K, GRAPH_MAX_RESULTS)]
    seed_ids = {seed["page_id"] for seed in seeds}
    results, candidates = [], {}
    for rank, seed in enumerate(seeds):
        root = seed["page_id"]
        results.append({**pages[root], "distance": seed["distance"], "hops": 0,
                        "path": [{"id": root, "title": pages[root]["title"]}]})
        queue = deque([(root, [root])])
        visited = {root}
        while queue:
            current, path = queue.popleft()
            if len(path) - 1 >= GRAPH_HOPS:
                continue
            # At the same depth, follow terms with fewer connections first.
            neighbors = sorted(adjacent[current], key=lambda n: (len(adjacent[n]), n))
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                route = path + [neighbor]
                queue.append((neighbor, route))
                if neighbor not in pages or neighbor in seed_ids:
                    continue
                frequency = max((len(adjacent[n]) for n in route if nodes[n]["kind"] == "term"), default=0)
                priority = (len(route) - 1, frequency, rank, neighbor)
                candidate = {**pages[neighbor], "hops": len(route) - 1,
                             "path": [{"id": n, "title": nodes[n]["title"]} for n in route]}
                if neighbor not in candidates or priority < candidates[neighbor][0]:
                    candidates[neighbor] = (priority, candidate)
    expanded = [candidate for _, candidate in sorted(candidates.values())]
    return {"seeds": results, "expanded": expanded[:max(0, GRAPH_MAX_RESULTS - len(results))],
            "max_hops": GRAPH_HOPS}


def _typed_adjacency(graph: dict, pages: dict[str, dict]) -> dict[str, list[tuple[str, str]]]:
    """Return {node: [(neighbor, relation), ...]} for the page and term nodes used in retrieval.

    Unlike search_graph, the relation type is kept so that term-to-term edges can be treated differently.
    """
    usable = {n["id"] for n in graph["nodes"] if n["kind"] == "term" or n["id"] in pages}
    adjacency = defaultdict(list)
    for edge in graph["edges"]:
        a, b, relation = edge["source"], edge["target"], edge["relation"]
        if relation in ("next_page", "mentions", "related_term") and a in usable and b in usable:
            adjacency[a].append((b, relation))
            adjacency[b].append((a, relation))
    return adjacency


def _reachable_pages(root: str, adjacency: dict, pages: dict[str, dict], bridge_related_terms: bool) -> dict[str, tuple[int, list[str]]]:
    """Return {page_id: (hops, path)} for pages within GRAPH_HOPS steps of root.

    A page-to-term, term-to-page, or page-to-page step costs one hop. When bridge_related_terms is set, a route
    may also use one related_term step between two terms at no hop cost, so a term can lead to pages of a
    closely related term. A route uses at most one such step; longer chains drift away from the topic.
    """
    start = (root, False)
    cost, paths, queue = {start: 0}, {start: [root]}, deque([start])
    while queue:
        state = queue.popleft()
        node, bridged = state
        for neighbor, relation in sorted(adjacency[node]):
            is_bridge = relation == "related_term"
            if is_bridge and (bridged or not bridge_related_terms):
                continue
            nxt, total = (neighbor, bridged or is_bridge), cost[state] + (0 if is_bridge else 1)
            if total > GRAPH_HOPS or total >= cost.get(nxt, GRAPH_HOPS + 1):
                continue
            cost[nxt], paths[nxt] = total, paths[state] + [neighbor]
            queue.appendleft(nxt) if is_bridge else queue.append(nxt)
    best: dict[str, tuple[int, list[str]]] = {}
    for state, total in cost.items():
        if state[0] in pages and state[0] != root and (state[0] not in best or total < best[state[0]][0]):
            best[state[0]] = (total, paths[state])
    return best


def _candidate_pages(seed_ids: list[str], adjacency: dict, pages: dict[str, dict], bridge_related_terms: bool) -> dict[str, tuple[int, list[str]]]:
    """Merge the pages reachable from every seed, keeping the shortest route to each page."""
    found: dict[str, tuple[int, list[str]]] = {}
    for seed_id in seed_ids:
        for page_id, route in _reachable_pages(seed_id, adjacency, pages, bridge_related_terms).items():
            if page_id not in seed_ids and (page_id not in found or route[0] < found[page_id][0]):
                found[page_id] = route
    return found


def _distances_to(db: sqlite3.Connection, vector: list[float], page_ids: list[str]) -> dict[str, float]:
    """Return the cosine distance between the query vector and each stored page embedding (no API call)."""
    marks = ",".join("?" * len(page_ids))
    rows = db.execute(
        f"SELECT page_id, vec_distance_cosine(embedding, ?) AS distance FROM chunks WHERE page_id IN ({marks})",
        (sqlite_vec.serialize_float32(vector), *page_ids),
    )
    return {row["page_id"]: row["distance"] for row in rows}


def search_graph_ranked(query: str, bridge_related_terms: bool = True, rerank: bool = True) -> dict:
    """Graph retrieval whose expanded candidates are ordered by similarity to the query.

    Same seeds as search_graph (the top GRAPH_START_K vector hits). Candidates come from adjacent pages and
    shared terms within GRAPH_HOPS, plus pages of related terms when bridge_related_terms is set. With rerank,
    candidates are sorted by cosine distance to the query, using the stored page embeddings, instead of by
    graph position. The result has the same shape as search_graph.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("The search query is empty.")
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    titles = {node["id"]: node["title"] for node in graph["nodes"]}
    with open_index(RAG_DB) as db:
        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
        hits = [hit for hit in _nearest(db, vector) if hit["page_id"] in pages][:min(GRAPH_START_K, GRAPH_MAX_RESULTS)]
        seed_ids = [hit["page_id"] for hit in hits]
        found = _candidate_pages(seed_ids, _typed_adjacency(graph, pages), pages, bridge_related_terms)
        distances = _distances_to(db, vector, list(found)) if found else {}
    order = sorted(found, key=lambda p: (distances[p], p) if rerank else (found[p][0], len(found[p][1]), p))

    def describe(page_id: str, hops: int, path: list[str], distance: float) -> dict:
        return {**pages[page_id], "distance": distance, "hops": hops,
                "path": [{"id": n, "title": titles[n]} for n in path]}

    seeds = [describe(hit["page_id"], 0, [hit["page_id"]], hit["distance"]) for hit in hits]
    expanded = [describe(p, found[p][0], found[p][1], distances[p]) for p in order]
    return {"seeds": seeds, "expanded": expanded[:max(0, GRAPH_MAX_RESULTS - len(seeds))], "max_hops": GRAPH_HOPS}


def _nearest(db: sqlite3.Connection, vector: list[float]) -> list[sqlite3.Row]:
    """Return the RAG_TOP_K pages closest to the query vector, with their cosine distance."""
    return db.execute(
        "SELECT page_id, vec_distance_cosine(embedding, ?) AS distance FROM chunks ORDER BY distance, page_id LIMIT ?",
        (sqlite_vec.serialize_float32(vector), RAG_TOP_K),
    ).fetchall()


def run_full_context(agent, question: str, model, instructions: str, prompt_template: str):
    """Pass all materials at once and answer without retrieval tools."""
    prompt = prompt_template.format(materials=get_all_materials(), question=question)
    print(f"[full-context] Input: {len(prompt):,} characters")
    try:
        with agent.override(tools=[], instructions=instructions):
            return agent.run_sync(prompt, model=model)
    except ModelHTTPError as e:
        print(f"[full-context] API error HTTP {e.status_code}: {e.body}")
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search the lecture materials without using an agent")
    parser.add_argument("query", help="What to look up")
    args = parser.parse_args()
    for i, result in enumerate(search(args.query), 1):
        print(f"\n{'=' * 60}\nSearch result {i}\n{'=' * 60}")
        print(f"Lecture: {result['document_title']}")
        print(f"Section: {result['section']}")
        print(f"Title: {result['title']}")
        print(f"Page: {result['page']}")
        print(f"\n{result['content']}")
