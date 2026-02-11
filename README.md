[English](README.md) | [繁體中文](README.zh.md)

# skill-optimizer

A meta-skill for Claude Code that analyzes skill execution results and applies targeted improvements. Keeps skills effective and current by adapting tools and techniques while preserving core principles and logic.

## What It Does

1. Detects which skill was recently executed (or accepts a skill name)
2. Analyzes conversation context for errors, workarounds, user corrections, and outdated patterns
3. Classifies each finding by category and risk level
4. Proposes structured changes with before/after comparisons
5. Applies approved changes, bumps version, commits, and pushes

## Design Philosophy

> **Principles are stable. Tools are replaceable.**

| Layer | Stability | Update Policy |
|-------|-----------|---------------|
| Principles & Goals | Stable | Rarely change |
| Logic & Flow | Semi-stable | Adjust when better patterns emerge |
| Tools & Techniques | Volatile | Replace freely |

## Prerequisites

- Skills installed in `~/.claude/skills/`
- Git configured for skill repositories

## Installation

```bash
git clone https://github.com/joneshong-skills/skill-optimizer.git ~/.claude/skills/skill-optimizer
```

## Usage

After a skill execution has issues or could be improved:

- *"optimize image-gen based on what just happened"*
- *"剛剛那個流程可以改進"*
- *"review smart-search skill performance"*
- *"skill 需要更新"*

## Change Categories

| Category | Risk | Approval |
|----------|------|----------|
| Bug Fix | Low | Auto-apply |
| Enhancement | Low | Auto-apply |
| Tech Update | Medium | Summarize first |
| Edge Case | Medium | Summarize first |
| Flow Restructure | High | Discuss first |
| Principle Change | Critical | Full discussion |

## Project Structure

```
skill-optimizer/
├── SKILL.md                        # Skill definition and workflow
├── README.md                       # This file
├── README.zh.md                    # Traditional Chinese README
└── references/
    └── analysis-framework.md       # Detailed analysis checklist and patterns
```

## License

MIT
