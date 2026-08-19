#!/usr/bin/env python3
"""
audit-scan.py — Static skill quality analysis (A1 + A4 dimensions).

Performs structural completeness and complexity checks on Claude skills.
A2 (Freshness), A3 (Consistency), A5 (Usage Signals) require LLM reasoning
and are handled in the main skill-optimizer context.

Usage:
  python3 audit-scan.py ~/.claude/skills/{skill-name}/
  python3 audit-scan.py --batch                          # scan all skills
  python3 audit-scan.py --json ~/.claude/skills/{name}/  # JSON output

Exit codes:
  0 = clean (no findings or info-only)
  1 = findings detected (WARN or FAIL)
  2 = error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# --- A1: Required section patterns ---

REQUIRED_SECTIONS = [
    {
        "name": "Frontmatter",
        "pattern": r"^---\s*$",
        "severity": "Critical",
        "description": "YAML frontmatter block (---)",
    },
    {
        "name": "Agent Delegation",
        "pattern": r"^##\s+Agent\s+Delegation",
        "severity": "Medium",
        "description": "Agent Delegation section",
    },
    {
        "name": "Core Workflow",
        "pattern": r"^##\s+(?:Core\s+Workflow|The\s+Process|Workflow|How\s+(?:to|it)\s+Work)",
        "severity": "High",
        "description": "Core Workflow / Process section",
    },
    {
        "name": "Output Format",
        "pattern": r"^##\s+(?:Output\s+Format|Report\s+Output|Response\s+Format|Output)",
        "severity": "Medium",
        "description": "Output Format section",
    },
    {
        "name": "Continuous Improvement",
        "pattern": r"^##\s+Continuous\s+Improvement",
        "severity": "Medium",
        "description": "Continuous Improvement section with lessons.md",
    },
]

# --- A1: Frontmatter field checks ---

REQUIRED_FRONTMATTER = ["name", "description"]
RECOMMENDED_FRONTMATTER = ["version", "tools", "argument-hint"]

# --- A4: Complexity thresholds ---

SKILL_MD_WARN = 500
SKILL_MD_FAIL = 800
REF_FILE_WARN = 300
TOTAL_SKILL_WARN = 2000
MAX_WORKFLOW_STEPS = 10
MAX_HEADING_DEPTH = 4


def parse_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from SKILL.md content."""
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    fm_text = content[3:end].strip()
    # Simple key-value parser (avoid PyYAML dependency)
    result = {}
    current_key = None
    for line in fm_text.split("\n"):
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val.startswith(">-") or val.startswith(">"):
                current_key = key
                result[key] = ""
            else:
                result[key] = val
                current_key = None
        elif current_key and line.strip():
            result[current_key] += " " + line.strip()
    for k in result:
        result[k] = result[k].strip()
    return result


def count_body_lines(content: str) -> int:
    """Count lines after frontmatter."""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            body = content[end + 3:]
            return len(body.strip().split("\n"))
    return len(content.strip().split("\n"))


def audit_skill(skill_dir: str) -> dict:
    """Run A1 + A4 audit on a single skill directory."""
    skill_dir = os.path.expanduser(skill_dir)
    skill_name = os.path.basename(skill_dir.rstrip("/"))

    if not os.path.isdir(skill_dir):
        return {"error": f"Not a directory: {skill_dir}"}

    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md_path):
        return {
            "skill": skill_name,
            "result": "FAIL",
            "findings": [
                {
                    "dimension": "A1",
                    "category": "Missing file",
                    "description": "SKILL.md not found",
                    "severity": "Critical",
                }
            ],
        }

    try:
        with open(skill_md_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError as e:
        return {"error": f"Cannot read {skill_md_path}: {e}"}

    findings = []
    lines = content.split("\n")

    # --- A1: Frontmatter ---
    fm = parse_frontmatter(content)
    if fm is None:
        findings.append({
            "dimension": "A1",
            "category": "Missing frontmatter",
            "description": "No YAML frontmatter block found",
            "severity": "Critical",
        })
    else:
        for field in REQUIRED_FRONTMATTER:
            if field not in fm or not fm[field]:
                findings.append({
                    "dimension": "A1",
                    "category": "Missing field",
                    "description": f"Frontmatter missing required field: {field}",
                    "severity": "High",
                })
        for field in RECOMMENDED_FRONTMATTER:
            if field not in fm or not fm[field]:
                findings.append({
                    "dimension": "A1",
                    "category": "Missing field",
                    "description": f"Frontmatter missing recommended field: {field}",
                    "severity": "Info",
                })

        # Check name matches directory
        if fm.get("name") and fm["name"] != skill_name:
            findings.append({
                "dimension": "A1",
                "category": "Name mismatch",
                "description": f"Frontmatter name '{fm['name']}' != directory '{skill_name}'",
                "severity": "Medium",
            })

    # --- A1: Required sections ---
    for section in REQUIRED_SECTIONS:
        if section["name"] == "Frontmatter":
            continue  # Already checked above
        found = any(re.search(section["pattern"], line, re.IGNORECASE) for line in lines)
        if not found:
            findings.append({
                "dimension": "A1",
                "category": "Missing section",
                "description": f"No '{section['name']}' section found",
                "severity": section["severity"],
            })

    # --- A1: Conditional sections ---
    body_lines = count_body_lines(content)

    refs_dir = os.path.join(skill_dir, "references")
    if body_lines > 200 and not os.path.isdir(refs_dir):
        findings.append({
            "dimension": "A1",
            "category": "Missing references",
            "description": f"SKILL.md has {body_lines} lines but no references/ directory",
            "severity": "Medium",
        })

    # --- A4: Line count ---
    if body_lines > SKILL_MD_FAIL:
        findings.append({
            "dimension": "A4",
            "category": "Excessive length",
            "description": f"SKILL.md body is {body_lines} lines (threshold: {SKILL_MD_FAIL})",
            "severity": "High",
        })
    elif body_lines > SKILL_MD_WARN:
        findings.append({
            "dimension": "A4",
            "category": "Long SKILL.md",
            "description": f"SKILL.md body is {body_lines} lines (threshold: {SKILL_MD_WARN})",
            "severity": "Medium",
        })

    # --- A4: Reference file sizes ---
    if os.path.isdir(refs_dir):
        for fname in os.listdir(refs_dir):
            fpath = os.path.join(refs_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".md"):
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        ref_lines = len(f.read().strip().split("\n"))
                    if ref_lines > REF_FILE_WARN:
                        findings.append({
                            "dimension": "A4",
                            "category": "Long reference",
                            "description": f"references/{fname} is {ref_lines} lines (threshold: {REF_FILE_WARN})",
                            "severity": "Low",
                        })
                except OSError:
                    pass

    # --- A4: Total skill size ---
    total_lines = 0
    file_count = 0
    for root, _dirs, files in os.walk(skill_dir):
        # Skip hidden dirs
        rel = os.path.relpath(root, skill_dir)
        if rel != "." and any(part.startswith(".") for part in Path(rel).parts):
            continue
        for fname in files:
            fpath = os.path.join(root, fname)
            file_count += 1
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    total_lines += len(f.read().strip().split("\n"))
            except OSError:
                pass

    if total_lines > TOTAL_SKILL_WARN:
        findings.append({
            "dimension": "A4",
            "category": "Large skill",
            "description": f"Total skill is {total_lines} lines across {file_count} files (threshold: {TOTAL_SKILL_WARN})",
            "severity": "Info",
        })

    # --- A4: Heading depth ---
    deep_headings = sum(1 for line in lines if re.match(r"^#{5,}\s", line))
    if deep_headings > 0:
        findings.append({
            "dimension": "A4",
            "category": "Deep nesting",
            "description": f"{deep_headings} headings with depth 5+ (max recommended: {MAX_HEADING_DEPTH})",
            "severity": "Low",
        })

    # --- A4: Workflow step count ---
    step_count = sum(1 for line in lines if re.match(r"^###\s+Step\s+\d+", line, re.IGNORECASE))
    if step_count > MAX_WORKFLOW_STEPS:
        findings.append({
            "dimension": "A4",
            "category": "Many steps",
            "description": f"{step_count} workflow steps (threshold: {MAX_WORKFLOW_STEPS})",
            "severity": "Low",
        })

    # --- Result classification ---
    critical = sum(1 for f in findings if f["severity"] in ("Critical", "High"))
    warnings = sum(1 for f in findings if f["severity"] in ("Medium", "Low"))

    if critical > 0:
        result = "FAIL"
    elif warnings > 0:
        result = "WARN"
    else:
        result = "PASS"

    return {
        "skill": skill_name,
        "audit_level": "Quick (A1+A4)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_counted": file_count,
        "body_lines": body_lines,
        "total_lines": total_lines,
        "result": result,
        "findings_count": len(findings),
        "critical_count": critical,
        "findings": findings,
    }


def format_report(audit: dict) -> str:
    """Format audit result as markdown report."""
    lines = [
        f"# Audit Report: {audit['skill']}",
        "",
        f"**Audit Level**: {audit['audit_level']}",
        f"**Timestamp**: {audit['timestamp']}",
        f"**SKILL.md Body**: {audit['body_lines']} lines",
        f"**Total Skill Size**: {audit['total_lines']} lines ({audit['files_counted']} files)",
        f"**Result**: {audit['result']} ({audit['findings_count']} findings, {audit['critical_count']} critical)",
        "",
    ]

    if audit["findings"]:
        lines.append("## Findings")
        lines.append("")
        lines.append("| # | Dim | Category | Description | Severity |")
        lines.append("|---|-----|----------|-------------|----------|")

        for i, f in enumerate(audit["findings"], 1):
            desc = f["description"][:80].replace("|", "\\|")
            lines.append(
                f"| {i} | {f['dimension']} | {f['category']} | {desc} | {f['severity']} |"
            )
        lines.append("")
    else:
        lines.append("No findings. Skill passed A1+A4 structural audit.")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Skill quality audit (A1+A4)")
    parser.add_argument("path", nargs="?", help="Skill directory to audit")
    parser.add_argument("--batch", action="store_true", help="Audit all skills")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.batch:
        skills_dir = os.path.expanduser("~/.claude/skills")
        results = []
        for entry in sorted(os.listdir(skills_dir)):
            skill_path = os.path.join(skills_dir, entry)
            if os.path.isdir(skill_path) and not entry.startswith(("_", ".")):
                audit = audit_skill(skill_path)
                results.append(audit)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("# Batch Audit Results")
            print(f"\n**Timestamp**: {datetime.now(timezone.utc).isoformat()}")
            print(f"**Skills Audited**: {len(results)}\n")
            print("| Skill | Result | Body Lines | Total Lines | Findings | Critical |")
            print("|-------|--------|------------|-------------|----------|----------|")
            for r in results:
                if "error" in r:
                    print(f"| {r.get('skill', '?')} | ERROR | — | — | — | — |")
                else:
                    print(
                        f"| {r['skill']} | {r['result']} | {r['body_lines']} | "
                        f"{r['total_lines']} | {r['findings_count']} | {r['critical_count']} |"
                    )

            flagged = [r for r in results if r.get("result") not in ("PASS", None)]
            if flagged:
                print(f"\n## Flagged Skills ({len(flagged)})\n")
                for r in flagged:
                    print(format_report(r))

        sys.exit(1 if any(r.get("result") == "FAIL" for r in results) else 0)

    elif args.path:
        audit = audit_skill(args.path)
        if "error" in audit:
            print(f"Error: {audit['error']}", file=sys.stderr)
            sys.exit(2)
        if args.json:
            print(json.dumps(audit, indent=2))
        else:
            print(format_report(audit))
        sys.exit(1 if audit["result"] == "FAIL" else 0)

    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
