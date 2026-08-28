---
name: arxiv-search
description: Searches arXiv for preprints and academic papers, retrieves abstracts, and filters by topic. Use when the user asks to find research papers, search arXiv, look up preprints, find academic articles in physics, math, CS, biology, statistics, or related fields.
---
> **모드 A 전용 — 네트워크(I7).** 무인 러너(모드 B)에서는 pre-tool 훅이 네트워크를 차단한다 — 사람이 승인 루프에 있는 대화형에서만 쓴다.

# arXiv Search Skill

## Usage

Run the bundled Python script using the absolute skills directory path from your system prompt:

```bash
.venv/bin/python [YOUR_SKILLS_DIR]/arxiv-search/arxiv_search.py "your search query" [--max-papers N]
```

- `query` (required): Search query string
- `--max-papers` (optional): Maximum results to retrieve (default: 10)

### Example

```bash
.venv/bin/python ~/workspace/agent-athena/skills/arxiv-search/arxiv_search.py "deep learning drug discovery" --max-papers 5
```

Returns title and abstract for each matching paper, sorted by relevance.

## Dependencies

Requires the `arxiv` Python package. If missing, install with:

```bash
.venv/bin/python -m pip install arxiv
```
