---
name: self-improve
description: Tournament-style evolutionary improvement loop — research, plan N variants in parallel, execute, benchmark, merge winner, repeat until target / plateau / cap. Designed for benchmarkable AI/ML or perf work.
argument-hint: "<improvement goal> [--n=<2-5>] [--max-iter=<N>]"
---

[SELF-IMPROVE ACTIVATED]

<Purpose>
For improvement problems with a measurable benchmark — model accuracy, latency,
memory, code quality metric, etc. Single-agent improvements get stuck in local
optima; self-improve runs a tournament: each iteration generates N independently
planned variants, executes them in parallel, and merges only the variant that
benchmarks better than the current best. Plateau detection and circuit breakers
prevent infinite cycling.

Sibling to continuous-overnight (both autonomous + envelope-bound) but with
a tournament loop instead of hypothesis-driven sequential execution.
</Purpose>

<Use_When>
- Goal has a clear benchmark command and direction (higher_is_better / lower_is_better)
- Improvement is iterable — small variant changes, not a single big rewrite
- AI/ML perf, accuracy, latency, code quality metric, etc.
- User wants autonomous iteration over many tries
</Use_When>

<Do_Not_Use_When>
- No benchmark — use ralph or autopilot with explicit acceptance criteria instead
- Single-shot fix → executor or autopilot
- No clear "winner" definition — would loop forever picking arbitrarily
- Modifying production code without isolation (would compound risk per iteration)
- Need user input on direction — use deep-interview / ralplan first to clarify, then self-improve
</Do_Not_Use_When>

<Trust_Gate>
Self-improve runs benchmark commands repeatedly inside the target repo,
which executes arbitrary code. Before starting, REQUIRE explicit user
confirmation:

1. Confirm target repo path + improvement branch name.
2. Confirm benchmark command (will run N×iterations times).
3. Confirm sealed-files list (paths the loop must NOT modify — typically
   the benchmark code itself, to prevent self-modification of the eval).
4. Acknowledge: "Self-improve will execute the benchmark command in
   {repo} repeatedly. Confirm? [yes/no]"

If user declines: abort. Do NOT proceed without explicit consent.
Once confirmed, persist `trust_confirmed: true` in state and skip on resume.
</Trust_Gate>

<State_Layout>
All runtime state under `.athena/self-improve/<topic-slug>/`:

```
.athena/self-improve/<slug>/
├── config/
│   ├── settings.json    # n_variants, benchmark_command, benchmark_direction,
│   │                    # max_iterations, plateau_threshold, plateau_window,
│   │                    # circuit_breaker_threshold, target_value, sealed_files,
│   │                    # repo_path, target_branch
│   └── goal.md          # Objective + target metric + scope
├── state/
│   ├── loop.json        # iteration, best_score, plateau_count, circuit_count, status
│   ├── iteration_state.json   # current step within iteration (for resume)
│   ├── plans/round-<N>/       # N planned variants per round
│   ├── results/round-<N>/     # benchmark output per variant
│   └── history.jsonl    # append-only iteration log
├── tracking/
│   └── raw_data.json    # all candidate scores ever
└── BLOCKED.md           # present iff status=blocked
```

`loop.json` schema:
```json
{
  "active": true,
  "status": "running | blocked | done",
  "iteration": <int>,
  "best_score": <number>,
  "baseline_score": <number>,
  "plateau_count": <int>,
  "circuit_count": <int>,
  "started_at": "<ISO>",
  "last_action_at": "<ISO>"
}
```
</State_Layout>

<Steps>

## Setup (first invocation only)

1. Run **Trust Gate** (above). Abort on decline.
2. Goal interview if not configured: ask user for objective, target metric, target value, scope. Save to `config/goal.md`.
3. Benchmark setup if not configured: ask user for benchmark command + direction (higher/lower is better) + acceptable runtime per iteration. Run baseline 3× to record `baseline_score` (median).
4. Sealed files: confirm list (default: benchmark code itself).
5. Initialize state: `loop.json`, `tracking/raw_data.json` with baseline.
6. Create improvement branch: `git -C <repo> checkout -b improve/<slug> <target_branch>` if missing.

## Improvement Loop

Run continuously until a stop condition fires (Step 9). NEVER ask the user mid-loop — autonomy is binding.

### Step 1 — Stale worktree cleanup
Remove any `worktrees/round_*` dirs from prior interrupted runs. Run `git worktree prune`. Idempotent.

### Step 2 — Stop check
Read `loop.json`. If `status` is `user_stopped` or external cancel: write BLOCKED.md (reason: user-cancelled), exit gracefully.

### Step 3 — Research (delegated to researcher)
Spawn **researcher** (opus) with goal + last K iterations' history. Output: research brief naming likely improvement directions, prior-art references, and gotchas. Save to `state/research_briefs/round-<N>.md`.
Failure → continue with history alone (researcher is best-effort).

### Step 4 — Plan N variants (parallel)
Spawn N **planner** agents (opus) in parallel, each producing exactly ONE testable hypothesis with:
- Approach family tag (architecture | training_config | data | infrastructure | optimization | testing | other)
- Target file refs
- Expected effect direction + magnitude
- Sealed-file violation check pre-built

Constraint: no two variants in the same round may share approach family (intra-round diversity). If planners propose duplicates, reject and respawn the duplicates with explicit "avoid family X, Y" instruction.

### Step 5 — Critic gate (sequential after Step 4)
For each plan, spawn **critic** (opus) with harness rules:
- H001: exactly one hypothesis (reject if zero or multiple)
- H002: no approach_family appears 3 rounds in a row (history check)
- H003: no sealed-file modification proposed
- Schema check on plan structure

Plans failing any → excluded from execution. If ALL plans rejected → skip to Step 8 (record + iterate).

### Step 6 — Execute (parallel)
For each approved plan:
1. Create worktree: `git worktree add worktrees/round_<N>_variant_<id> -b experiment/round_<N>_variant_<id> improve/<slug>`
2. Spawn **executor** (opus) with plan + worktree path + sealed-files list.
3. Executor implements + runs benchmark.
4. Capture benchmark result.

Failure → mark variant failed, do not abort the round.

### Step 7 — Tournament selection
1. Filter to `status=success`. If 0 → skip to Step 8.
2. Rank by benchmark score (respecting direction).
3. Ranked-candidate loop (best first):
   a. **No-regression check**: candidate score must improve or hold even vs `best_score`.
   b. Merge winner: `git merge experiment/round_<N>_variant_<winner> --no-ff -m "..."`
   c. **Re-benchmark on merged state** (3× median). If regression confirmed → `git reset --hard HEAD~1`, try next candidate.
   d. If conflict → `git merge --abort`, try next.
   e. First candidate that survives merge + re-benchmark → winner accepted, break.
4. If no candidate survived → no merge, improvement branch unchanged.
5. Archive losers (tag + delete branches).

### Step 8 — Record + visualize
1. Append round to `history.jsonl` (winner score, all candidate scores, decisions).
2. Update `loop.json`:
   - Winner with improvement >= plateau_threshold → update best_score, reset plateau_count + circuit_count.
   - Winner with improvement < threshold → update best_score (if strictly better), plateau_count++, reset circuit_count.
   - No winner → circuit_count++ (do NOT increment plateau_count — plateau tracks weak wins, not failures).
3. Append all candidate scores to `tracking/raw_data.json`.

### Step 9 — Stop conditions
Evaluate ALL — if ANY true, exit:
| Condition | Trigger |
|-----------|---------|
| User stop | `status == user_stopped` |
| Target reached | `best_score` meets `target_value` (respecting direction) |
| Plateau | `plateau_count >= plateau_window` (default window=3) |
| Max iterations | `iteration >= max_iterations` (default 20) |
| Circuit breaker | `circuit_count >= circuit_breaker_threshold` (default 5) |

If none fire → Step 1 of next iteration.

## Completion

When loop exits:
1. Set `loop.status = done`, write `SUMMARY.md` with: status, iterations run, best vs baseline, improvement %.
2. NEVER auto-PR. Print: "Run `gh pr create --head improve/<slug> --base <target>` manually if you want to ship."
3. Preserve all artifacts under `.athena/self-improve/<slug>/` for review.

</Steps>

<Rules>
- NEVER ask the user during the loop. Trust gate is the ONLY user touch (plus optional setup interview).
- Sealed files are absolute — any plan proposing modification is rejected by Step 5 critic.
- Re-benchmark on merged state is non-optional. Pre-merge benchmark on isolated worktree can flatter due to dependency state. Confirm gain post-merge or revert.
- No approach_family ≥3 rounds in a row — H002 enforces diversity. Loop should not pick "tweak hyperparam X" 5 times.
- Tournament respects benchmark direction — `higher_is_better: ≥ best_score` (not `>`). Equal scores hold the line; no regression allowed.
- Plateau tracks weak wins (improvement below threshold), circuit breaker tracks no-winner rounds. They are NOT the same counter.
- If trust gate fails: abort and never proceed. No partial setup.
</Rules>

<Final_Checklist>
- [ ] Trust gate confirmed (or `trust_confirmed: true` in state for resume)
- [ ] Baseline benchmark recorded (3× median in `tracking/raw_data.json`)
- [ ] N variants planned per round with diverse approach families
- [ ] Critic gate enforced (H001 / H002 / H003 + schema)
- [ ] Sealed files NEVER modified by any executor (verify with diff against sealed list pre-merge)
- [ ] Re-benchmark on merged state ran for the chosen winner
- [ ] history.jsonl has one row per iteration with all candidate scores
- [ ] Stop condition documented in SUMMARY.md
- [ ] No auto-PR on completion (user runs gh pr create manually)
</Final_Checklist>

Goal:
{{PROMPT}}
