# Quality Engine Fixtures

Ground-truth JSON files used by `scripts/quality_engine.py` to score reviewer
or critic agent outputs against expected findings.

## Schema

```jsonc
{
  "fixtureId": "code-<slug>",
  "fixturePath": "fixtures/code/code-<slug>.md",
  "domain": "code | plan | analysis",
  "expectedVerdict": "ACCEPT | REVISE | REJECT",
  "isCleanBaseline": false,
  "description": "Short purpose statement",
  "findings": [
    {
      "id": "STABLE-ID-N",
      "severity": "CRITICAL | MAJOR | MINOR",
      "category": "finding | missing | perspective",
      "summary": "One-sentence headline",
      "keywords": ["minimum 3-5 keywords for matching"],
      "explanation": "Why it matters — used for reviewer self-check, not scoring"
    }
  ]
}
```

## Categories

- `finding` — explicit issues the agent should surface in main findings.
- `missing` — gaps the agent should call out under "What's Missing" / Gap Analysis.
- `perspective` — issues that only emerge from multi-perspective review (security/new-hire/ops or executor/stakeholder/skeptic).

`missing_coverage` and `perspective_coverage` scores measure how well the agent
hits the gap/perspective categories specifically — these are the differentiators
between a thorough review and a checklist pass.

## Keyword Selection Rules

- 3-7 keywords per finding. Less = false positives; more = noise dilutes the signal.
- Mix surface vocabulary (the literal term) with conceptual vocabulary (synonyms).
- Avoid generic terms ("issue", "problem", "bug"). Prefer technically-discriminating terms.
- The scorer requires a proportion of keywords (`ceil(0.4 × N)`, min 2) to declare a match.

## Severity Mapping

The scorer is severity-adjacency-tolerant by default — `MAJOR` for an expected
`CRITICAL` counts as a partial match (severity_accuracy < 1.0 but TPR not penalized).
`HIGH/MEDIUM/LOW` aliases are accepted (`HIGH→CRITICAL`, etc.).

## Adding a New Fixture

1. Write the source artifact (`.md` for plans, `.py`/`.ts` for code) — this is what
   the reviewer agent sees.
2. Author the JSON ground truth — list every finding you'd expect a top-tier
   reviewer to surface, with keywords and category.
3. Run the reference reviewer to baseline:
   ```bash
   ~/.local/bin/python3 scripts/quality_engine.py score \
     --fixture fixtures/code-yourname.json \
     --output /path/to/reviewer-output.md
   ```
4. Iterate keywords until top-tier output scores ≥ 0.7 composite. If a great
   review fails to match, your keywords are too narrow.

## Existing Fixtures

| ID | Domain | Severity Mix | Purpose |
|----|--------|--------------|---------|
| code-async-cache | code | 2 CRITICAL / 1 MAJOR / 1 MINOR | Smoke test fixture; covers race + memory + observability + ops perspective |

## Source

Schema cannibalized from oh-my-claudecode `benchmarks/code-reviewer/ground-truth/*.json`
+ `benchmarks/shared/types.ts`. Adapted to JSON-only (no TypeScript runtime needed).
