# Quality Engine Protocol

Reference for the evidence-driven scoring system in `scripts/quality_engine.py`.
Cannibalized from oh-my-claudecode (Yeachan-Heo/oh-my-claudecode)
`benchmarks/harsh-critic/scoring/scorer.ts` + `benchmarks/shared/types.ts` and
adapted to Python stdlib (no TypeScript runtime).

## Why Evidence-Driven

Skill optimization without measurement is vibes. The Quality Engine flips that:

- **Mission** — define what improvement you want.
- **Fixtures** — ground-truth JSON files listing the findings a top-tier agent should surface.
- **Score** — match agent output against fixtures, compute TPR / severity / missing / evidence rates.
- **A/B** — compare two prompt versions on the same fixtures, get a quantitative delta.
- **Baseline registry** — store TPR/FNR snapshots so future runs detect regressions.
- **Process flags** — boolean checks that the agent followed protocol structure
  (pre-commitment, multi-perspective, gap analysis), not just outcome.

## Composite Score Formula

```
composite = TPR              × 0.30
          + severity_accuracy × 0.15
          + missing_coverage × 0.20
          + perspective_coverage × 0.15
          + evidence_rate    × 0.10
          + process_compliance × 0.10
```

Weights live in `DEFAULT_WEIGHTS` in `quality_engine.py` and can be overridden
per-run via `--weights weights.json`. Weights MUST sum to 1.0 (no enforcement —
self-discipline).

| Metric | What it measures | Why weighted this way |
|--------|------------------|------------------------|
| `true_positive_rate` | matched / total ground-truth findings | Baseline competence — finds the obvious issues |
| `severity_accuracy` | correct severity / matched | Calibration — distinguishes CRITICAL from MINOR |
| `missing_coverage` | gap-category findings matched | Differentiator — ordinary reviews miss this |
| `perspective_coverage` | perspective-category matched | Differentiator — multi-perspective surfaces hidden issues |
| `evidence_rate` | CRITICAL+MAJOR with `file:line` / total | Forces concrete citations |
| `process_compliance` | avg(pre_commitment, multi_perspective, gap_analysis) | Protocol structural conformance |

## Process Compliance Flags

Distinct from outcome metrics — these are **structural booleans** detecting whether
the agent followed the protocol:

| Flag | Detection regex | Why it matters |
|------|-----------------|----------------|
| `pre_commitment` | "Pre-commitment Predictions" heading or bold marker | Critic protocol Phase 1 — predicts likely issues before reading details. Activates deliberate search. |
| `multi_perspective` | "Multi-Perspective" heading or "as a {security/new-hire/ops/executor/stakeholder/skeptic}" phrasings | Phase 3 — different lenses surface different classes of issue. |
| `gap_analysis` | "What's Missing" or "Gaps Analysis" heading | Phase 4 — explicit search for absent things, not just present problems. |

A skill can have high TPR but fail process flags if it found issues by accident
without following the protocol — that's a regression signal even when current
output looks good.

## A/B Comparison

```bash
quality_engine.py ab \
  --fixture fixtures/code-async-cache.json \
  --baseline path/to/old-reviewer-output.md \
  --candidate path/to/new-reviewer-output.md
```

Returns `delta_composite` and a `verdict` of `candidate-wins | baseline-wins | neutral`
(threshold ±0.05 by default — below that delta is not statistically meaningful for
small fixture counts).

## Baseline Registry

```bash
# Register today's reviewer as the baseline for future regression checks
quality_engine.py score --fixture fixtures/code-async-cache.json \
  --output reviewer-output.md > /tmp/scores.json
quality_engine.py baseline --register reviewer-2026-05-08 --report /tmp/scores.json
```

Stored in `data/baselines.json`. When a future skill update lands, run
A/B against the registered baseline — if composite drops by > 0.05, flag the
regression and require the change owner to justify it.

## Fixture Authoring Discipline

1. Write fixtures **once**, before optimizing the skill — pre-commitment principle.
2. Keywords MUST be discriminating — see `fixtures/README.md` for selection rules.
3. Categorize findings as `finding` / `missing` / `perspective` so coverage subscores work.
4. Top-tier reviewer should score ≥ 0.7 composite — if not, fixture is over-specified.
5. Keep fixtures small (3-8 findings) — the value is in the discrimination, not breadth.

## Limitations vs OMC Original

| Aspect | OMC TS implementation | Workshop Python port |
|--------|----------------------|----------------------|
| Runtime | Bun + Vitest | Python 3.12 stdlib |
| Parser | Markdown AST + structured types | Regex-based heading/list parser |
| Severity adjacency | Strict + tolerant modes | Tolerant by default (`ALLOW_ADJACENT_SEVERITY=True`) |
| Latency tracking | Tokens + ms | Not implemented (Workshop tracks separately) |
| Multi-fixture aggregate | Built-in | Per-fixture only — aggregate via shell |

The TS port has more polish; this Python port covers the **decision-grade core**
(score, A/B, baseline) without dragging in a TS runtime as a Workshop dependency.

## When to Use

- **Before** changing a reviewer/critic skill's core protocol — establish baseline.
- **After** any skill change touching Phase 1-5 of the Investigation Protocol — confirm
  regression hasn't occurred.
- **Periodically** (e.g., quarterly) on the canonical fixture set to track drift.
- **NOT** for routine reviews — the engine is for protocol calibration, not day-to-day
  review evaluation.

## Source

- `benchmarks/harsh-critic/scoring/scorer.ts` (matching, severity adjacency, keyword normalization)
- `benchmarks/shared/types.ts` L130-149 (BenchmarkScores fields, process compliance flags)
- `benchmarks/baselines/2026-03-08-consolidation.json` (baseline registry pattern)
- `benchmarks/code-reviewer/ground-truth/code-payment-refund.json` (fixture schema)

Repo: github.com/Yeachan-Heo/oh-my-claudecode
