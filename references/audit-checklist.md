# Skill Audit Checklist (A1-A5)

Detailed criteria for proactive skill quality analysis. Used by `--audit` mode
and `scripts/audit-scan.py`.

---

## A1: Structural Completeness

Verify that SKILL.md contains all required sections for a well-formed skill.

### Required Sections

| Section | Detection Pattern | Severity |
|---------|------------------|----------|
| **Frontmatter** | `^---` YAML block with `name`, `description` | Critical |
| **Agent Delegation** | `## Agent Delegation` (or explanation why not needed) | Medium |
| **Core Workflow** | `## Core Workflow` or `## The Process` or `## Workflow` | High |
| **Output Format** | `## Output Format` or `## Report Output` or `## Response Format` | Medium |
| **Continuous Improvement** | `## Continuous Improvement` with lessons.md reference | Medium |

### Conditional Sections

| Section | Condition | Detection |
|---------|-----------|-----------|
| `references/` directory | SKILL.md body > 200 lines | Glob check |
| `scripts/` directory | Skill calls external tools or batch operations | Grep for `Bash`, `sandbox` |
| `## Prerequisites` | Skill depends on other skills or tools | Grep for skill names, MCP tools |

### Frontmatter Fields

| Field | Required | Validation |
|-------|----------|------------|
| `name` | Yes | Must match directory name |
| `description` | Yes | Must be non-empty, < 300 chars |
| `version` | Recommended | Semver format (X.Y.Z) |
| `tools` | Recommended | Comma-separated tool names |
| `argument-hint` | Recommended | Short usage hint |

---

## A2: Freshness

Detect references to outdated tools, APIs, models, or practices.

### Outdated Model IDs

```
WARN: claude-3-opus, claude-3-sonnet, claude-3-haiku (superseded by 4.x family)
WARN: gpt-4-turbo, gpt-4o (check if still current)
WARN: Any model ID with date suffix older than 6 months
```

### Outdated Tool References

```
WARN: BrowserTools MCP (check if still maintained)
WARN: References to specific MCP tool versions
WARN: Hardcoded URLs to services that may have changed
```

### Version Staleness

```
INFO: version field not updated in 90+ days (check git log)
WARN: version 0.1.0 with significant content (likely never bumped)
```

### Date References

```
WARN: Hardcoded year references (2024, 2025) in non-historical context
WARN: "Latest as of {date}" where date > 6 months old
```

---

## A3: Consistency with Rules

Cross-reference SKILL.md content against `~/.claude/rules/*.md` and `~/.claude/CLAUDE.md`.

### Security Rules (`rules/security.md`)

| SKILL.md Pattern | Rule Violation |
|-----------------|----------------|
| Recommends JWT | security.md mandates signed cookies |
| Uses `requests` library | sandbox uses SDK http_get/http_post |
| Stores secrets in files | Should use env vars |

### Bash Safety (`rules/bash-safety.md`)

| SKILL.md Pattern | Rule Violation |
|-----------------|----------------|
| Uses `--no-verify` | Blocked by bash-safety hook |
| Uses `rm -rf` on protected paths | Blocked by dual-layer defense |
| Uses `sudo` | Hard-denied by Layer 1+2 |

### Output Convention (`CLAUDE.md`)

| SKILL.md Pattern | Rule Violation |
|-----------------|----------------|
| Writes to `~/` root | Must use `~/workshop/` or `~/workshop/outputs/` |
| Writes to `~/Desktop` or `~/Downloads` | Explicitly forbidden |
| No output path specified | Should define output convention |

### Sub-Agent Rules (`rules/sub-agent.md`)

| SKILL.md Pattern | Rule Violation |
|-----------------|----------------|
| Delegates MCP work to `browser` agent | Only `general-purpose` has mcpproxy |
| No `max_turns` on Task calls | Should set max_turns |
| No summary output requirement | Sub-agents should return summaries |

### Tool Usage (`CLAUDE.md` built-in rules)

| SKILL.md Pattern | Rule Violation |
|-----------------|----------------|
| Uses `cat` / `head` / `tail` | Should use Read tool |
| Uses `grep` / `rg` in Bash | Should use Grep tool |
| Uses `find` in Bash | Should use Glob tool |
| Uses `sed` / `awk` for edits | Should use Edit tool |

---

## A4: Complexity

Assess cognitive load and maintainability.

### Line Count Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| SKILL.md body (excluding frontmatter) | > 500 lines | WARN: Extract to references/ |
| SKILL.md body | > 800 lines | FAIL: Must restructure |
| Single reference file | > 300 lines | WARN: Consider splitting |
| Total skill size (all files) | > 2000 lines | INFO: Large skill, review scope |

### Structural Complexity

| Signal | Detection | Severity |
|--------|-----------|----------|
| Deep nesting (4+ heading levels) | Count `####` headings | WARN |
| Too many workflow steps (> 10) | Count `### Step N` | WARN |
| Decision tree with 5+ branches | Count conditional paths | INFO |
| Duplicate content across files | Hash-compare paragraphs | WARN |

### Cognitive Load Indicators

| Signal | Detection |
|--------|-----------|
| Multiple agent delegation patterns | Count `subagent_type` references |
| Many tool dependencies | Count tools in frontmatter |
| Complex fallback chains (3+ levels) | Count fallback/else/if-unavailable patterns |

---

## A5: Usage Signal Analysis

Check if recurring friction from `lessons.md` has been absorbed into SKILL.md.

### Friction Pattern Detection

1. **Read** `~/.claude/skills/<name>/lessons.md` (if exists)
2. **Extract** all `**Friction**:` entries
3. **Check** if corresponding `**Fix**:` or `**Rule**:` has been applied to SKILL.md
4. **Flag** recurring patterns (same friction keyword 2+ times) not yet in SKILL.md

### Observation Staleness

1. **Read** `~/.claude/skills/<name>/observations.md` (if exists)
2. **Count** pending observations older than 90 days
3. **Flag** observations with `trigger_condition` that should have been checked

### lessons.md Quality

| Signal | Detection | Severity |
|--------|-----------|----------|
| No lessons.md | File missing | INFO (new skill) |
| lessons.md empty | 0 entries | INFO |
| Entries without dates | Missing `### YYYY-MM-DD` | WARN |
| Same friction 3+ times | Keyword frequency | HIGH: unresolved pattern |

---

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **Critical** | Skill will malfunction or violate hard rules | Must fix immediately |
| **High** | Significant quality issue, likely causes problems | Should fix in next optimization |
| **Medium** | Quality gap, may cause issues | Fix when convenient |
| **Low** | Minor improvement opportunity | Defer unless batch-fixing |
| **Info** | Observation, no action needed | Record for awareness |

---

## Audit Report Format

```markdown
# Audit Report: {skill-name}

**Audit Level**: Quick (A1+A4) | Full (A1-A5)
**Timestamp**: {ISO-8601}
**Skill Version**: {version from frontmatter}
**Result**: PASS | WARN ({n} findings) | FAIL ({n} critical)

## Summary
{1-2 sentence overall assessment}

## Findings

| # | Dimension | Category | Description | Severity |
|---|-----------|----------|-------------|----------|
| 1 | A1 | Missing section | No "Agent Delegation" section | Medium |
| 2 | A4 | Complexity | SKILL.md is 623 lines (threshold: 500) | WARN |

## Recommendations
1. {Specific remediation step}
2. {Specific remediation step}
```
