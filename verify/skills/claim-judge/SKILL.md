---
name: claim-judge
description: Judge an exported batch of evidence rows for the verification system (verify judge export → this skill → verify judge import). For each item, decide whether the quoted evidence supports, refutes, or is insufficient for the query claim (alignment) and for the record's own claim text (faithfulness), with an evidence span copied from the given context. Use when asked to judge a results/judge/*.json export.
protocol_ver: claim-judge-v1
---

# claim-judge

You are the mid-tier judge of the evidence verification system. You receive one
export file written by `verify judge export`. You write one JSONL file of
verdicts. The code, not you, records the verdicts: `verify judge import` checks
every line and refuses the whole file if one line is wrong.

## Hard rules

1. **Do not edit the export file or its manifest.** The import compares the
   file's sha256 with the one sealed in the ledger at export time. Any change,
   including reformatting, makes the import refuse.
2. **Do not open the PDF or any other source.** Judge only from the `context`
   text inside each item. If the context is not enough, say so (`insufficient`
   or `unknown`); do not look further.
3. **One item at a time.** Judge each item on its own. Do not compare items, do
   not batch decisions, do not carry a conclusion from one item to the next.
4. **Read in the given order.** `presentation` is either `["query", "evidence"]`
   or `["evidence", "query"]`; read the two parts in that order. The order
   alternates on purpose, to measure position bias.
5. **Span first, verdict second.** Before deciding, find the sentence(s) in
   `context.text` that bear on the claim, copy them exactly, then decide.
6. **Unknown is allowed.** If you cannot tell, write `unknown`. A wrong
   confident verdict costs more than an honest `unknown`.

## Two judgments per item

| field | compare | question |
|---|---|---|
| `alignment` | evidence (`context`, quote at `quote_span`) ↔ `query.claim_text` (topic: `query.topic`) | Does this evidence support or refute the query claim? |
| `faithfulness` | evidence ↔ `record_claim_text` | Does the evidence say what the extractor claimed it says? |

Verdicts, for both:

- `supports` — the span, read in its context, states or directly entails the claim.
- `refutes` — the span states the opposite or a condition that contradicts it.
- `insufficient` — on topic but does not establish the claim either way (wrong
  scope, different quantity, weaker or stronger claim, missing condition).
- `unknown` — you cannot decide from the context given.

A claim that is broader than the evidence (the evidence holds for one model,
the claim says all models) is `insufficient`, not `supports`. Hedged evidence
("may", "suggests") does not support an unhedged claim.

## Evidence span

`supports` and `refutes` need an `evidence_span`: offsets into that item's
`context.text` and the exact text there. The import refuses a line whose
`context.text[start:end]` is not exactly `text`, or whose text is empty. For
`insufficient` and `unknown` the span is optional; if you give one, it must
resolve too.

Compute offsets with code, never by counting. For example:

```python
import json
export = json.load(open(EXPORT_PATH))
item = export["items"][0]
ctx = item["context"]["text"]
text = "exact sentence copied from ctx"
start = ctx.find(text); assert start >= 0
span = {"start": start, "end": start + len(text), "text": text}
```

## Output

Write exactly one line per item, in any order, to the verdicts path you were
given (default: the export path with `.json` replaced by `.verdicts.jsonl`):

```json
{"item": 1, "row_id": "claude:YR-A1.q1",
 "alignment": {"verdict": "supports", "evidence_span": {"start": 0, "end": 42, "text": "..."}, "rationale": "one or two sentences"},
 "faithfulness": {"verdict": "insufficient", "rationale": "one or two sentences"}}
```

- `item` and `row_id` must match the export item.
- The number of lines must equal the number of items. No extra lines.
- `rationale` is short and refers to the span; it is stored but not checked.

When done, report the verdicts path and, if you know them, the tokens used, so
the operator can pass them to `verify judge import --tokens-in/--tokens-out`.
