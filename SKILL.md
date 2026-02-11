---
name: skill-optimizer
description: >-
  This skill should be used when the user asks to "optimize a skill",
  "review skill performance", "update skill based on feedback",
  "improve this skill", "改進 skill", "優化技能", "skill 需要更新",
  "剛剛那個流程可以改進", or after a skill execution encounters errors,
  workarounds, user corrections, or outdated behavior.
version: 0.2.0
argument-hint: "skill name (or leave blank to auto-detect from context)"
---

# Skill Optimizer

Analyze skill execution results, identify improvements, and apply targeted updates
to keep skills effective and current. Preserve core principles and logic while
adapting tools, techniques, and implementation details as technology evolves.

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

### Step 3 — External Research

**This step is mandatory.** Internal evidence alone is insufficient — verify findings and
discover improvements through external sources before proposing any changes.

#### 3a. Research via smart-search

Invoke the **smart-search** skill to query relevant topics. Focus queries on:

- **Platform changes**: "Grok image generation API changes 2026", "Gemini web interface updates"
- **Tool updates**: "Playwright MCP new features", "BrowserTools latest capabilities"
- **Best practices**: "browser automation image download best practices"
- **Deprecations**: "deprecated APIs" or tools referenced in the skill
- **Alternatives**: "alternatives to [current approach]" when a workaround was needed

Select the most appropriate search source based on the query:
- **DeepWiki / Context7**: For library/framework documentation (free or precise)
- **Perplexity Pro**: For current events, platform policy changes, broad research
- **WebSearch**: For quick factual lookups when smart-search is unavailable

#### 3b. Cross-reference with User Feedback

After collecting external research results:

1. **Present a summary** of internal evidence + external findings to the user
2. **Ask specific questions** where research is ambiguous:
   - "Research shows Grok now supports 1:1 aspect ratios — have you noticed this?"
   - "Gemini's thinking mode quota may have changed — want me to verify?"
3. **Incorporate user knowledge** — the user may know things not available online
   (internal tools, unpublished changes, personal preferences)

#### 3c. Synthesize

Combine all three sources into a unified assessment:

| Source | Strength | Weakness |
|--------|----------|----------|
| Internal evidence | Specific, recent, contextual | Limited to one execution |
| External research | Broad, current, authoritative | May not match user's exact setup |
| User feedback | Ground truth for their environment | May be incomplete or assumed |

When sources conflict, prioritize: **User feedback > Internal evidence > External research**.
The user's actual experience in their environment is the ultimate authority.

### Step 4 — Multi-Agent Evaluation

**Do not rely on a single perspective.** Use parallel sub-agents (via the Task tool)
to evaluate proposed changes from different angles. This produces more objective,
well-reasoned decisions.

#### Launch 2-3 Parallel Agents

Use the Task tool with `subagent_type=general-purpose` to spawn agents simultaneously.
Each agent receives the same evidence package but evaluates from a different perspective:

| Agent | Perspective | Focus |
|-------|------------|-------|
| **Advocate** | "Why should we make this change?" | Benefits, improvements, future-proofing |
| **Skeptic** | "Why should we NOT change this?" | Risks, regressions, unnecessary churn |
| **Pragmatist** | "What's the minimal effective change?" | Cost-benefit, timing, priority |

Each agent should return:
- Their assessment (change / defer / reject)
- Confidence level (low / medium / high)
- Key reasoning (2-3 bullet points)

#### Synthesize Agent Results

After all agents complete, synthesize their outputs:
- **Consensus (all agree)** → Proceed with their shared recommendation
- **Majority (2 of 3)** → Present the majority view and the dissenting view to user
- **Split (no majority)** → Present all views, let the user decide

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
Create this file if it doesn't exist. Format:

```markdown
# Observations — <skill-name>

## Pending

### YYYY-MM-DD — Brief title
- **Category**: tech / edge / enhance / flow
- **Evidence**: What was observed
- **Research**: What external sources say
- **Confidence**: Low / Medium
- **Trigger**: What would confirm this needs action
  (e.g., "If this happens 2 more times" or "When platform officially announces")

## Resolved

### YYYY-MM-DD — Brief title (→ applied in v0.3.0 / dismissed)
- **Resolution**: What was decided and why
```

When the optimizer runs again on the same skill, **check observations.md first**.
If a pending observation now has additional evidence, it may cross the threshold
for action.

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

## Additional Resources

### Reference Files
- **`references/analysis-framework.md`** — Detailed checklist for analyzing skill execution,
  technology lifecycle tracking, and cross-skill improvement patterns
