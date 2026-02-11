---
name: skill-optimizer
description: >-
  This skill should be used when the user asks to "optimize a skill",
  "review skill performance", "update skill based on feedback",
  "improve this skill", "改進 skill", "優化技能", "skill 需要更新",
  "剛剛那個流程可以改進", or after a skill execution encounters errors,
  workarounds, user corrections, or outdated behavior.
version: 0.1.0
argument-hint: "skill name (or leave blank to auto-detect from context)"
---

# Skill Optimizer

Analyze skill execution results, identify improvements, and apply targeted updates
to keep skills effective and current. Preserve core principles and logic while
adapting tools, techniques, and implementation details as technology evolves.

## Design Philosophy

**Separate the stable from the volatile:**

| Layer | Stability | Examples | Update Policy |
|-------|-----------|----------|---------------|
| **Principles** | Stable | "Route to the best platform", "Optimize prompts before submission" | Rarely change; only with fundamental rethinking |
| **Logic / Flow** | Semi-stable | "Step 1 → Step 2 → Step 3", decision trees, fallback chains | Adjust when better patterns emerge |
| **Tools / Tech** | Volatile | Specific MCP tools, APIs, URL patterns, CSS selectors | Replace freely when better alternatives exist |

When updating a skill, always ask: *Is this a principle change or a tool change?*
Tool changes are safe and encouraged. Principle changes require explicit user discussion.

## Core Workflow

### Step 1 — Identify Target Skill

Determine which skill to optimize:

- **From argument**: User specifies skill name (e.g., `image-gen`, `smart-search`)
- **Auto-detect**: Scan recent conversation for skill invocations. Look for:
  - Skill tool calls in the conversation
  - References to skill names or `/skill-name` commands
  - Files read from `~/.claude/skills/*/`

Load the target skill's files:
- `~/.claude/skills/<name>/SKILL.md` (required)
- `~/.claude/skills/<name>/references/*` (if any)
- `~/.claude/skills/<name>/scripts/*` (if any)

### Step 2 — Gather Evidence

Analyze the conversation context for improvement signals. Collect evidence in these categories:

#### Error Signals
- Exceptions, timeouts, or failed tool calls during execution
- Retry loops or repeated attempts at the same step
- Fallback paths that were triggered

#### Workaround Signals
- Steps not documented in the skill that were improvised
- Alternative approaches used when the documented approach failed
- Manual interventions by the user

#### User Correction Signals
- User redirecting the workflow ("no, do it this way instead")
- User providing information the skill should have known
- User expressing dissatisfaction with results

#### Outdated Technology Signals
- API endpoints returning errors or changed responses
- UI elements not matching the documented selectors/refs
- Tools or services that have been deprecated or replaced
- New capabilities available that the skill doesn't leverage

#### Efficiency Signals
- Steps that could be parallelized but are run sequentially
- Redundant operations (reading the same file twice, unnecessary snapshots)
- Overly complex flows that could be simplified

### Step 3 — Classify Changes

For each piece of evidence, classify the required change:

| Category | Icon | Description | Risk | Approval |
|----------|------|-------------|------|----------|
| Bug Fix | `fix` | Something broke or produces wrong results | Low | Auto-apply |
| Enhancement | `enhance` | Better approach discovered during execution | Low | Auto-apply |
| Tech Update | `tech` | Tool, API, or platform changed | Medium | Summarize, then apply |
| New Edge Case | `edge` | Scenario not covered by current skill | Medium | Summarize, then apply |
| Flow Restructure | `flow` | Workflow steps need reordering or redesign | High | Discuss with user first |
| Principle Change | `principle` | Core assumptions or goals need rethinking | Critical | Full discussion required |

### Step 4 — Propose Changes

Present findings as a structured change list. For each change:

```
### [category] Brief title

**Evidence**: What happened in the conversation that triggered this
**Current**: What the skill currently says/does
**Proposed**: What it should say/do instead
**Rationale**: Why this change improves the skill
**Risk**: Low / Medium / High
```

Group changes by file (SKILL.md, references, scripts) for clarity.

### Step 5 — Apply Changes

After user reviews and approves:

1. **Edit skill files** — Apply each approved change using the Edit tool
   - For tool/tech changes: replace the specific tool or technique, keep the surrounding logic
   - For flow changes: restructure steps while preserving the overall goal
   - For edge cases: add handling without bloating the main flow (use references for details)
2. **Bump version** — Update the `version` field in frontmatter:
   - Bug fix / edge case: patch bump (0.1.0 → 0.1.1)
   - Enhancement / tech update: minor bump (0.1.0 → 0.2.0)
   - Flow restructure / principle change: major bump (0.1.0 → 1.0.0)
3. **Update references** — If the change involves detailed technical content, update
   or create reference files rather than bloating SKILL.md
4. **Commit and push** — Use a descriptive commit message:
   ```
   [skill-name] category: brief description of change

   Evidence: what triggered the update
   ```

### Step 6 — Record Learning (Optional)

If the improvement reveals a pattern that applies across multiple skills,
record it in auto-memory (`~/.claude/projects/.../memory/`) for future reference.

Examples of cross-skill learnings:
- "Playwright CDN downloads require Navigate-to-Image approach"
- "Always check BrowserTools network logs before attempting direct URL access"
- "Canvas toDataURL only works on same-origin images"

## Analysis Quick Reference

### Common Skill Decay Patterns

| Pattern | Symptom | Typical Fix |
|---------|---------|-------------|
| API drift | Endpoints return 404/403, response format changed | Update URLs, parsing logic |
| UI change | Element refs don't match, buttons moved | Re-snapshot, update selectors |
| Rate limit change | Previously working requests now throttled | Update limits table, adjust retry logic |
| New capability | Platform added features the skill doesn't use | Add new options to decision tree |
| Dependency deprecated | Required tool/service no longer available | Replace with alternative, preserve logic |
| Context overflow | Skill instructions too long for effective use | Move details to references, keep SKILL.md lean |

### What NOT to Change

- Working flows that "could be slightly better" — if it works, leave it
- Cosmetic formatting or wording preferences
- Adding speculative features the user hasn't needed
- Removing fallback paths just because the primary path worked this time

## Additional Resources

### Reference Files
- **`references/analysis-framework.md`** — Detailed checklist for analyzing skill execution,
  technology lifecycle tracking, and cross-skill improvement patterns
