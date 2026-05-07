#!/usr/bin/env python3
"""skill-optimizer Quality Engine — evidence-driven scoring for skill outputs.

Cannibalized from oh-my-claudecode (Yeachan-Heo/oh-my-claudecode)
benchmarks/harsh-critic/scoring/scorer.ts + benchmarks/shared/types.ts
+ benchmarks/baselines/2026-03-08-consolidation.json, adapted to Python stdlib.

Provides:
  - load_fixture(path)              — read a ground-truth JSON fixture
  - match_findings(...)             — keyword-based agent-finding-to-ground-truth matching
  - score_fixture(...)              — TPR / severity / missing / perspective / evidence rates
  - detect_process_flags(text)      — pre-commitment / multi-perspective / gap-analysis booleans
  - composite_score(scores, ...)    — weighted aggregate
  - compare_ab(...)                 — baseline vs candidate delta + verdict
  - load_baseline / save_baseline   — JSON registry under data/

CLI:
  quality_engine.py score   --fixture <path> --output <agent.md> [--weights <weights.json>]
  quality_engine.py ab      --fixture <path> --baseline <a.md> --candidate <b.md>
  quality_engine.py flags   --output <agent.md>
  quality_engine.py baseline --register <agent_id> --report <scores.json>

Python 3.12+ stdlib only — no external dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────────────────────

SEVERITY_ORDER = ["CRITICAL", "MAJOR", "MINOR"]
ALLOW_ADJACENT_SEVERITY = True  # treat MAJOR-when-CRITICAL-expected as partial match
MIN_KEYWORD_MATCHES = 2  # require at least this many keywords (or proportional ratio)

# Default composite weights — sum to 1.0
DEFAULT_WEIGHTS = {
    "true_positive_rate": 0.30,  # found / total ground-truth findings
    "severity_accuracy": 0.15,  # correct severity / matched
    "missing_coverage": 0.20,  # gap-analysis findings matched
    "perspective_coverage": 0.15,  # multi-perspective findings matched
    "evidence_rate": 0.10,  # CRITICAL+MAJOR with file:line / total CRITICAL+MAJOR
    "process_compliance": 0.10,  # avg of pre-commit / multi-perspective / gap-analysis flags
}

# Process compliance regex patterns — match the heading or characteristic phrasing
PROCESS_PATTERNS = {
    "pre_commitment": re.compile(
        # Match "Pre-commitment Predictions" as heading, bold marker, or section start.
        # Case-insensitive; accepts hyphen or space; predictions singular/plural optional.
        r"(?im)pre[- ]?commitment[\s\-]+predictions?"
    ),
    "multi_perspective": re.compile(
        r"(?im)multi[- ]?perspective"
        r"|(?:perspective[\s\-]+notes?)"
        r"|(?:as a security|as a new[- ]?hire|as an? ops"
        r"|as the executor|as the stakeholder|as the skeptic)"
    ),
    "gap_analysis": re.compile(
        r"(?im)what'?s\s+missing|gap[s]?\s*analysis|^\s*(?:#+\s*|\*\*\s*)gaps?\b"
    ),
}

# Severity-prefix regex for parsing agent output
SEVERITY_PREFIX = re.compile(
    r"\b(CRITICAL|MAJOR|MINOR|HIGH|MEDIUM|LOW)\b",
    re.IGNORECASE,
)

# Perspective-finding start: "As a security engineer:", "As the stakeholder:",
# "From the executor perspective:" — typically appear without a severity prefix
# in multi-perspective sections. Default severity for these is MINOR.
PERSPECTIVE_START = re.compile(
    r"^(?:as\s+(?:a|an|the)\s+[\w-]+(?:\s+[\w-]+)?\s*[:,]"
    r"|from\s+(?:a|an|the)\s+[\w-]+(?:\s+[\w-]+)?\s+perspective\s*[:,])",
    re.IGNORECASE,
)

# file:line evidence pattern (e.g. `auth.ts:42`, `src/foo.py:100-110`)
EVIDENCE_PATTERN = re.compile(
    r"[\w./-]+\.(?:py|ts|tsx|js|jsx|md|sql|sh|rs|go|java|c|cpp|h|hpp|yaml|yml|json|toml)"
    r":\d+(?:-\d+)?"
)

# ── Data classes ───────────────────────────────────────────────────


@dataclass
class GroundTruthFinding:
    id: str
    severity: str
    summary: str
    keywords: list[str]
    category: str = "finding"
    explanation: str = ""


@dataclass
class GroundTruth:
    fixture_id: str
    fixture_path: str = ""
    domain: str = "code"
    expected_verdict: str = ""
    is_clean_baseline: bool = False
    findings: list[GroundTruthFinding] = field(default_factory=list)


@dataclass
class FixtureScores:
    fixture_id: str
    matched_ids: list[str]
    missed_ids: list[str]
    spurious_texts: list[str]
    true_positive_rate: float
    severity_accuracy: float
    missing_coverage: float
    perspective_coverage: float
    evidence_rate: float
    process_compliance: float
    process_flags: dict[str, bool]
    composite: float


# ── Loading ────────────────────────────────────────────────────────


def load_fixture(path: str | Path) -> GroundTruth:
    """Load a ground-truth fixture JSON file."""
    p = Path(path)
    data = json.loads(p.read_text())
    findings = [
        GroundTruthFinding(
            id=f["id"],
            severity=f["severity"].upper(),
            summary=f["summary"],
            keywords=f.get("keywords", []),
            category=f.get("category", "finding"),
            explanation=f.get("explanation", ""),
        )
        for f in data.get("findings", [])
    ]
    return GroundTruth(
        fixture_id=data["fixtureId"],
        fixture_path=data.get("fixturePath", ""),
        domain=data.get("domain", "code"),
        expected_verdict=data.get("expectedVerdict", ""),
        is_clean_baseline=data.get("isCleanBaseline", False),
        findings=findings,
    )


# ── Text normalization & keyword matching ─────────────────────────


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[`*_#()\[\]{}<>\"'.,;!?|\\]", " ", text)
    text = re.sub(r"[-/:]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _keyword_in_text(text: str, keyword: str) -> bool:
    lt, lk = text.lower(), keyword.lower()
    if lk in lt:
        return True
    nt, nk = _normalize(text), _normalize(keyword)
    if not nk:
        return False
    if nk in nt:
        return True
    parts = [p for p in nk.split(" ") if p]
    if len(parts) <= 1:
        return False
    return all(p in nt for p in parts)


def _required_matches(keywords: list[str]) -> int:
    if not keywords:
        return 0
    proportional = max(1, (len(keywords) * 4 + 9) // 10)  # ceil(0.4 * n)
    return min(len(keywords), max(MIN_KEYWORD_MATCHES, proportional))


def _text_matches_gt(text: str, gt: GroundTruthFinding) -> bool:
    matches = sum(1 for kw in gt.keywords if _keyword_in_text(text, kw))
    return matches >= _required_matches(gt.keywords)


# ── Severity ───────────────────────────────────────────────────────


def _severity_distance(a: str, b: str) -> int:
    a, b = a.upper(), b.upper()
    # normalize HIGH→CRITICAL, MEDIUM→MAJOR, LOW→MINOR for adjacency check
    alias = {"HIGH": "CRITICAL", "MEDIUM": "MAJOR", "LOW": "MINOR"}
    a, b = alias.get(a, a), alias.get(b, b)
    try:
        return abs(SEVERITY_ORDER.index(a) - SEVERITY_ORDER.index(b))
    except ValueError:
        return 99


def _severity_matches(agent_sev: str, gt_sev: str) -> bool:
    d = _severity_distance(agent_sev, gt_sev)
    return d <= 1 if ALLOW_ADJACENT_SEVERITY else d == 0


# ── Agent-output parsing ───────────────────────────────────────────


@dataclass
class ParsedFinding:
    text: str
    severity: str = "UNKNOWN"
    has_evidence: bool = False


def parse_agent_output(text: str) -> list[ParsedFinding]:
    """Lightweight parser: split markdown into finding-sized blocks.

    A 'finding' is recognized as either:
      - A list item or numbered item containing a SEVERITY token
      - A heading line (## or ###) containing a SEVERITY token
      - A paragraph starting with a perspective marker ("As the stakeholder:",
        "From the executor perspective:") — common in Multi-Perspective sections
        where findings are cited without an explicit severity prefix. These
        default to MINOR severity.

    Blocks continue until the next finding starts.
    """
    findings: list[ParsedFinding] = []
    current: list[str] = []
    current_sev = "UNKNOWN"

    def flush():
        if current:
            block = "\n".join(current).strip()
            if block:
                findings.append(
                    ParsedFinding(
                        text=block,
                        severity=current_sev,
                        has_evidence=bool(EVIDENCE_PATTERN.search(block)),
                    )
                )

    lines = text.splitlines()
    in_finding = False
    for line in lines:
        stripped = line.strip()
        # Strip leading list/bullet markers for perspective-start detection,
        # so "- As the stakeholder: ..." also counts.
        delisted = re.sub(r"^(?:[-*]|\d+\.)\s+", "", stripped)
        is_structural_start = re.match(r"^(?:[-*]|\d+\.)\s+", stripped) or re.match(
            r"^#{2,4}\s+", stripped
        )
        is_perspective_start = bool(PERSPECTIVE_START.match(delisted))

        if is_structural_start and SEVERITY_PREFIX.search(stripped):
            flush()
            current = [stripped]
            m = SEVERITY_PREFIX.search(stripped)
            current_sev = m.group(1).upper() if m else "UNKNOWN"
            in_finding = True
        elif is_perspective_start:
            flush()
            current = [stripped]
            current_sev = "MINOR"  # perspective findings default to MINOR
            in_finding = True
        elif in_finding:
            if not stripped:
                current.append(line)
            elif re.match(r"^(?:[-*]|\d+\.)\s+", stripped) or re.match(r"^#{2,4}\s+", stripped):
                flush()
                current = [stripped]
                m = SEVERITY_PREFIX.search(stripped)
                if m:
                    current_sev = m.group(1).upper()
                elif PERSPECTIVE_START.match(delisted):
                    current_sev = "MINOR"
                else:
                    current = []
                    in_finding = False
            else:
                current.append(line)
    flush()
    return findings


# ── Scoring ────────────────────────────────────────────────────────


def match_findings(
    parsed: list[ParsedFinding],
    gt: GroundTruth,
) -> tuple[list[str], list[str], list[str], int]:
    """Return (matched_ids, missed_ids, spurious_texts, severity_correct_count)."""
    matched: list[str] = []
    severity_correct = 0
    consumed: set[int] = set()

    for gt_f in gt.findings:
        for idx, p in enumerate(parsed):
            if idx in consumed:
                continue
            if _text_matches_gt(p.text, gt_f):
                matched.append(gt_f.id)
                consumed.add(idx)
                if _severity_matches(p.severity, gt_f.severity):
                    severity_correct += 1
                break

    missed = [gt_f.id for gt_f in gt.findings if gt_f.id not in matched]
    spurious = [p.text[:200] for idx, p in enumerate(parsed) if idx not in consumed]
    return matched, missed, spurious, severity_correct


def detect_process_flags(text: str) -> dict[str, bool]:
    """Return process compliance booleans for the agent output."""
    return {name: bool(pattern.search(text)) for name, pattern in PROCESS_PATTERNS.items()}


def score_fixture(
    agent_output: str,
    gt: GroundTruth,
    weights: dict[str, float] | None = None,
) -> FixtureScores:
    """Score one agent output against one fixture."""
    weights = weights or DEFAULT_WEIGHTS
    parsed = parse_agent_output(agent_output)
    matched, missed, spurious, severity_correct = match_findings(parsed, gt)

    total_gt = len(gt.findings) or 1
    matched_count = len(matched)

    # Categorize ground-truth findings for missing/perspective coverage
    missing_cat_total = sum(1 for f in gt.findings if f.category == "missing")
    perspective_cat_total = sum(1 for f in gt.findings if f.category == "perspective")
    missing_matched = sum(1 for f in gt.findings if f.category == "missing" and f.id in matched)
    perspective_matched = sum(
        1 for f in gt.findings if f.category == "perspective" and f.id in matched
    )

    # Evidence rate = CRITICAL+MAJOR findings with file:line evidence
    crit_maj = [p for p in parsed if p.severity.upper() in {"CRITICAL", "MAJOR", "HIGH", "MEDIUM"}]
    evidence_rate = sum(1 for p in crit_maj if p.has_evidence) / len(crit_maj) if crit_maj else 0.0

    process_flags = detect_process_flags(agent_output)
    process_compliance = sum(process_flags.values()) / max(len(process_flags), 1)

    scores = {
        "true_positive_rate": matched_count / total_gt,
        "severity_accuracy": severity_correct / matched_count if matched_count else 0.0,
        "missing_coverage": (missing_matched / missing_cat_total if missing_cat_total else 1.0),
        "perspective_coverage": (
            perspective_matched / perspective_cat_total if perspective_cat_total else 1.0
        ),
        "evidence_rate": evidence_rate,
        "process_compliance": process_compliance,
    }

    composite = sum(scores[k] * weights.get(k, 0) for k in scores)

    return FixtureScores(
        fixture_id=gt.fixture_id,
        matched_ids=matched,
        missed_ids=missed,
        spurious_texts=spurious,
        true_positive_rate=scores["true_positive_rate"],
        severity_accuracy=scores["severity_accuracy"],
        missing_coverage=scores["missing_coverage"],
        perspective_coverage=scores["perspective_coverage"],
        evidence_rate=scores["evidence_rate"],
        process_compliance=scores["process_compliance"],
        process_flags=process_flags,
        composite=composite,
    )


# ── A/B comparison ─────────────────────────────────────────────────


def compare_ab(
    baseline_output: str,
    candidate_output: str,
    gt: GroundTruth,
    weights: dict[str, float] | None = None,
    significance_threshold: float = 0.05,
) -> dict[str, Any]:
    """Score both outputs against the same fixture and report delta."""
    base = score_fixture(baseline_output, gt, weights)
    cand = score_fixture(candidate_output, gt, weights)
    delta = cand.composite - base.composite
    if abs(delta) < significance_threshold:
        verdict = "neutral"
    elif delta > 0:
        verdict = "candidate-wins"
    else:
        verdict = "baseline-wins"
    return {
        "fixture_id": gt.fixture_id,
        "baseline": asdict(base),
        "candidate": asdict(cand),
        "delta_composite": round(delta, 4),
        "verdict": verdict,
        "significance_threshold": significance_threshold,
    }


# ── Baseline registry ──────────────────────────────────────────────


def baseline_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "baselines.json"


def load_baseline_registry() -> dict[str, Any]:
    p = baseline_path()
    if not p.exists():
        return {"baselines": [], "version": 1}
    return json.loads(p.read_text())


def register_baseline(agent_id: str, report: dict[str, Any]) -> Path:
    p = baseline_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    registry = load_baseline_registry()
    entry = {
        "agent_id": agent_id,
        "registered_at": datetime.now().isoformat(),
        "report": report,
    }
    registry.setdefault("baselines", []).append(entry)
    p.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    return p


# ── CLI ────────────────────────────────────────────────────────────


def cmd_score(args: argparse.Namespace) -> None:
    gt = load_fixture(args.fixture)
    output = Path(args.output).read_text() if Path(args.output).exists() else args.output
    weights = json.loads(Path(args.weights).read_text()) if args.weights else None
    scores = score_fixture(output, gt, weights)
    print(json.dumps(asdict(scores), indent=2, ensure_ascii=False))


def cmd_ab(args: argparse.Namespace) -> None:
    gt = load_fixture(args.fixture)
    base = Path(args.baseline).read_text()
    cand = Path(args.candidate).read_text()
    weights = json.loads(Path(args.weights).read_text()) if args.weights else None
    result = compare_ab(base, cand, gt, weights)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_flags(args: argparse.Namespace) -> None:
    text = Path(args.output).read_text() if Path(args.output).exists() else args.output
    flags = detect_process_flags(text)
    score = sum(flags.values()) / max(len(flags), 1)
    print(json.dumps({"flags": flags, "process_compliance": score}, indent=2))


def cmd_baseline(args: argparse.Namespace) -> None:
    if args.register and args.report:
        report = json.loads(Path(args.report).read_text())
        path = register_baseline(args.register, report)
        print(f"Registered baseline {args.register} -> {path}")
    else:
        registry = load_baseline_registry()
        print(json.dumps(registry, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="quality_engine",
        description="Evidence-driven quality scoring for skill outputs",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_score = sub.add_parser("score", help="Score one agent output against a fixture")
    p_score.add_argument("--fixture", required=True, help="Ground-truth fixture JSON")
    p_score.add_argument("--output", required=True, help="Agent output (file or text)")
    p_score.add_argument("--weights", help="Custom weights JSON file")
    p_score.set_defaults(func=cmd_score)

    p_ab = sub.add_parser("ab", help="Baseline vs candidate A/B comparison")
    p_ab.add_argument("--fixture", required=True)
    p_ab.add_argument("--baseline", required=True, help="Baseline agent output file")
    p_ab.add_argument("--candidate", required=True, help="Candidate agent output file")
    p_ab.add_argument("--weights")
    p_ab.set_defaults(func=cmd_ab)

    p_flags = sub.add_parser("flags", help="Show process compliance flags")
    p_flags.add_argument("--output", required=True, help="Agent output (file or text)")
    p_flags.set_defaults(func=cmd_flags)

    p_base = sub.add_parser("baseline", help="Manage baseline registry")
    p_base.add_argument("--register", help="Register baseline under this agent_id")
    p_base.add_argument("--report", help="Report JSON file to register")
    p_base.set_defaults(func=cmd_baseline)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
