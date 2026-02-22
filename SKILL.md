---
name: skill-optimizer
description: >-
  This skill should be used when the user asks to "optimize a skill",
  "review skill performance", "update skill based on feedback",
  "improve this skill", "改進 skill", "優化技能", "skill 需要更新",
  "剛剛那個流程可以改進", or after a skill execution encounters errors,
  workarounds, user corrections, or outdated behavior.
version: 0.3.0
tools: Read, Glob, Grep, Edit, Bash, Write, Task, WebSearch
argument-hint: "skill name (or leave blank to auto-detect from context)"
---

# Skill Optimizer

Analyze skill execution results, identify improvements, and apply targeted updates
to keep skills effective and current. Preserve core principles and logic while
adapting tools, techniques, and implementation details as technology evolves.

## Agent Delegation

Delegate skill review to `reviewer` agent. Use `explorer` for pattern analysis.

## Prerequisites

- The **smart-search** skill installed (`~/.claude/skills/smart-search/`) — for external research
- Skills installed in `~/.claude/skills/` with git repositories
- WebSearch tool available as fallback when smart-search is unavailable

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

### Step 2 — Gather Internal Evidence

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

### Step 3 — External Research (Conditional)

**When to research**: Skills involving external platforms (web UIs, APIs, third-party services).
**When to skip**: Pure code/logic skills (like orchestrators, validators) where issues are
reproducible locally. Proceed directly to Step 4.

When research is needed, use **smart-search** or **WebSearch** to verify findings:

- **Platform changes**: UI updates, API drift, new capabilities
- **Deprecations**: Tools or services referenced in the skill
- **Alternatives**: Better approaches when workarounds were needed

After research, **cross-reference with user feedback** — the user's actual experience is
the ultimate authority. Prioritize: **User feedback > Internal evidence > External research**.

See `references/analysis-framework.md` § "Evidence Synthesis" for the full source-weighting table.

### Step 4 — Multi-Agent Evaluation

Use parallel sub-agents (Task tool, `subagent_type=general-purpose`) to evaluate
proposed changes from three perspectives:

| Agent | Core Question |
|-------|--------------|
| **Advocate** | "Why should we make this change?" |
| **Skeptic** | "Why should we NOT change this?" |
| **Pragmatist** | "What's the minimal effective change?" |

Each returns: assessment (change/defer/reject), confidence (low/medium/high), 2-3 bullet points.

Synthesis: **Consensus** → proceed. **Majority** → note dissent. **Split** → user decides.
See `references/analysis-framework.md` § "Multi-Agent Evaluation Framework" for prompt
templates and detailed synthesis rules.

### Step 5 — Decide: Act Now or Defer

Not every finding warrants immediate action. Apply the **confidence threshold** to decide.

#### Act Now — When ALL of these are true:
- Evidence confirmed by 2+ sources (internal + external, or internal + user)
- Multi-agent evaluation reaches consensus or strong majority
- The change fixes something currently broken, or risk of inaction is high
- The skill is actively used and the issue will recur

#### Defer to Observation Log — When ANY of these are true:
- Only one source of evidence (single execution, single search result)
- Agents are split or confidence is low
- The change is "nice to have" but nothing is broken
- The technology is in flux (new release, beta feature, unconfirmed reports)
- Need more data points from future executions to confirm the pattern

#### Observation Log

Store deferred findings in `~/.claude/skills/<skill-name>/observations.md`.
When the optimizer runs again on the same skill, **check observations.md first** —
if a pending observation now has additional evidence, it may cross the threshold for action.

See `references/analysis-framework.md` § "Observation Log Guidelines" for the template
format and promotion/cleanup criteria.

### Step 6 — Classify and Propose Changes

For findings that pass the "Act Now" threshold:

| Category | Description | Risk | Approval |
|----------|-------------|------|----------|
| Bug Fix | Something broke or produces wrong results | Low | Auto-apply |
| Enhancement | Better approach discovered during execution | Low | Auto-apply |
| Tech Update | Tool, API, or platform changed | Medium | Summarize, then apply |
| New Edge Case | Scenario not covered by current skill | Medium | Summarize, then apply |
| Flow Restructure | Workflow steps need reordering or redesign | High | Discuss with user first |
| Principle Change | Core assumptions or goals need rethinking | Critical | Full discussion required |

Present each change:

```
### [category] Brief title

**Evidence**: What happened (internal) + what research found (external)
**Agent consensus**: Advocate / Skeptic / Pragmatist views
**Current**: What the skill currently says/does
**Proposed**: What it should say/do instead
**Rationale**: Why this change improves the skill (cite sources)
**Risk**: Low / Medium / High
```

Group changes by file (SKILL.md, references, scripts) for clarity.

### Step 7 — Apply Changes

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
4. **Update observations.md** — Move resolved observations from Pending to Resolved
5. **Commit and push** — Use a descriptive commit message:
   ```
   [skill-name] category: brief description of change

   Evidence: what triggered the update
   Agent consensus: advocate/skeptic/pragmatist assessment
   ```

### Step 8 — Record Learning (Optional)

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

## Continuous Improvement

This skill evolves with each use. After every invocation:

1. **Reflect** — Identify what worked, what caused friction, and any unexpected issues
2. **Record** — Append a concise lesson to `lessons.md` in this skill's directory
3. **Refine** — When a pattern recurs (2+ times), update SKILL.md directly

### lessons.md Entry Format

```
### YYYY-MM-DD — Brief title
- **Friction**: What went wrong or was suboptimal
- **Fix**: How it was resolved
- **Rule**: Generalizable takeaway for future invocations
```

Accumulated lessons signal when to run `/skill-optimizer` for a deeper structural review.

## Additional Resources

### Reference Files
- **`references/analysis-framework.md`** — Detailed checklist for analyzing skill execution,
  technology lifecycle tracking, and cross-skill improvement patterns
