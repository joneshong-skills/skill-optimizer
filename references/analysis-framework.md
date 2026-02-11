# Analysis Framework for Skill Optimization

Detailed criteria for analyzing skill executions and identifying improvements.

---

## Evidence Collection Checklist

Run through this checklist after each skill execution to identify optimization opportunities.

### Execution Analysis

- [ ] Did the skill complete its goal on the first attempt?
- [ ] Were any steps skipped or replaced with alternatives?
- [ ] Did any tool calls fail or return unexpected results?
- [ ] Were there retry loops (same action attempted multiple times)?
- [ ] Did the user intervene to correct the workflow?
- [ ] Was the user satisfied with the final result?
- [ ] Were there unnecessary steps that could be removed?
- [ ] Were there missing steps that had to be improvised?

### Technology Currency

- [ ] Do all referenced URLs still resolve correctly?
- [ ] Do all referenced tools/MCP servers still exist?
- [ ] Have any APIs changed their response format?
- [ ] Have any platforms updated their UI structure?
- [ ] Are there newer tools/APIs that could replace current ones?
- [ ] Are rate limits and quotas still accurate?
- [ ] Do content policies still match what's documented?

### Skill Quality

- [ ] Is SKILL.md under 2,000 words? (move details to references if over)
- [ ] Are all referenced files up to date?
- [ ] Does the decision tree cover the common cases?
- [ ] Are error handling and fallback paths documented?
- [ ] Is the skill language-agnostic where possible?

---

## Technology Lifecycle Tracking

### Lifecycle Stages

| Stage | Description | Action |
|-------|-------------|--------|
| **Current** | Tool works as documented | No change needed |
| **Drifting** | Minor differences from documentation | Update docs to match reality |
| **Deprecated** | Official deprecation announced | Plan migration, document alternatives |
| **Broken** | No longer functional | Immediate replacement needed |
| **Superseded** | Better alternative exists | Evaluate migration when convenient |

### Tracking Signals

**Platform-specific signals:**

| Platform | What to Monitor | Where to Check |
|----------|-----------------|----------------|
| Grok (grok.com) | UI changes, rate limits, engine updates | Network logs, snapshot diffs |
| Gemini (gemini.google.com) | Model names, mode toggles, policies | Snapshot diffs, error messages |
| MCP Playwright | API changes, browser compatibility | Tool call errors, version notes |
| MCP BrowserTools | Available tools, data format | Tool call results |
| GitHub (gh CLI) | API changes, auth methods | Command output |

**General signals:**
- Tool calls returning new error types
- Response formats that don't match parsing logic
- New capabilities appearing in tool descriptions
- Community reports of breaking changes

---

## Change Impact Assessment

### Risk Matrix

| Change Scope | Single Skill | Multiple Skills | All Skills |
|-------------|-------------|-----------------|------------|
| **Config/URL** | Low | Low | Medium |
| **Tool swap** | Medium | Medium | High |
| **Flow change** | Medium | High | Critical |
| **Principle** | High | Critical | Critical |

### Rollback Strategy

For each change, consider:
1. **Is this reversible?** — File edits can always be reverted via git
2. **Does this break other skills?** — Check cross-skill dependencies
3. **Does the user need to do anything?** — New logins, tool installs, etc.

---

## Cross-Skill Improvement Patterns

Improvements discovered in one skill often apply to others. Common patterns:

### Browser Automation Skills
Skills that automate web interfaces share common challenges:
- **Navigate-to-Image**: When CDN images require browser auth, navigate directly
  to the image URL and extract via canvas (discovered in image-gen)
- **Snapshot before action**: Always take an accessibility snapshot before interacting
  with elements — UI layouts change frequently
- **Wait times**: Platform-specific; document observed ranges, not fixed values
- **Login detection**: Check for login pages via snapshot; instruct user to log in manually

### Search/Query Skills
Skills that query external sources:
- **Multi-source verification**: Cross-reference results from multiple sources
- **Fallback chains**: If primary source fails, try alternatives in order
- **Cache awareness**: Some sources cache aggressively; note freshness limits

### Code Generation Skills
Skills that produce code or configuration:
- **Framework versions**: Pin major versions in examples; note when examples may need updating
- **Dependency drift**: Package names and APIs change; verify before recommending
- **Platform specifics**: Clearly separate macOS/Linux/Windows differences

---

## Optimization Session Template

Use this template when running a full optimization session:

```markdown
## Optimization Report: [skill-name]

### Execution Summary
- **Date**: YYYY-MM-DD
- **Trigger**: [What prompted this optimization]
- **Skill Version**: [Current version before changes]

### Evidence Collected
1. [Evidence item with category tag]
2. [Evidence item with category tag]

### Proposed Changes
| # | Category | Description | Risk | Status |
|---|----------|-------------|------|--------|
| 1 | fix | ... | Low | Pending |
| 2 | tech | ... | Medium | Pending |

### Changes Applied
- [List of changes that were approved and applied]

### Version Bump
- Before: X.Y.Z
- After: X.Y.Z
- Reason: [Brief justification]

### Cross-Skill Notes
- [Any learnings that apply to other skills]
```
