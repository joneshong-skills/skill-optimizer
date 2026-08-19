# Auto-Evolve Protocol — Detail Reference

Invoked via `/skill-optimizer evolve [subcommand]`.

## Pattern Extraction (Post-Invocation Signals)

After any skill runs, scan for:

| Signal | Criteria |
|--------|----------|
| Repeated manual corrections | User fixed the same type of issue 2+ times in same skill |
| Tool call failures with workarounds | Documented in lessons.md as fallback or retry |
| Missing capabilities | Skill fell back to other tools for functionality it should own |
| Mid-session prompt refinement | User rephrased or redirected to get better output |

## Evolution Triggers

| Condition | Action |
|-----------|--------|
| Same friction pattern in 3+ sessions | Auto-generate SKILL.md patch candidate |
| A lesson appears in `lessons.md` 2+ times | Promote to SKILL.md rule |
| New CLI/tool consistently used alongside skill | Add to `tools:` frontmatter + workflow |

## Subcommands

### `evolve scan`
1. Glob all `~/.claude/skills/*/lessons.md`
2. Read each file; extract `**Friction**` and `**Rule**` lines
3. Group by keyword similarity (shared nouns/verbs across entries)
4. Report: skill name, occurrence count, representative friction summary

### `evolve suggest`
1. Run `evolve scan` internally
2. For groups with 2+ entries, draft a minimal SKILL.md edit per group
3. Present top 3 friction points with before/after diff preview:
   ```
   Skill: <name>  |  Pattern: <keyword>  |  Occurrences: N
   --- current
   +++ proposed
   ```
4. Do NOT apply — await user approval

### `evolve apply`
1. Display each suggested patch (as above)
2. Prompt user: "Apply this patch? [y/n/skip]"
3. On `y`: use Edit tool to apply; bump patch version in frontmatter
4. On `n`: write to `observations.md` as deferred finding
5. After all patches, commit with message:
   ```
   [<skill-name>] evolve: <brief description>

   Source: lessons.md pattern, N occurrences
   ```

## Signal Sources

In addition to `lessons.md`, evolve scan also reads:
- `observations.md` `## Instincts` section — auto-extracted friction signals from sessions
  (staged by `instinct_distiller.py`, reviewed via `/review-instincts`)
- Instincts carry `occurrences` counts — treat 3+ occurrences as equivalent to 2+ lessons.md entries

When evolve scan finds a pattern appearing in **3+ different skills**, flag it for
`/rules-distill` instead of patching individual SKILL.md files — cross-skill patterns
belong in `~/.claude/rules/`, not in individual skills.

## Constraints

- Evolve only patches `tools:` list, step descriptions, and quick-reference tables
- Never auto-modify Design Philosophy, Principles, or Core Workflow structure
- Each generated patch must cite the source lessons.md entries
- Patches exceeding 20 lines → split into multiple smaller proposals
