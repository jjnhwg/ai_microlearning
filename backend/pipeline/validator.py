"""Numeric-claim validator — the non-LLM gate on generated feedback.

docs/PLAN.md requires that a post-generation validator reject any report whose
numeric claims don't match the computed metrics. This module does exactly that,
deterministically: for every insight it (1) confirms the numbers the insight
*claims* to assert actually match the metrics row from features.analyze(), and
(2) confirms every number that appears in the human-readable message is one of
those asserted numbers — so no stray or hallucinated figure can slip through a
phraser. It also requires at least one citation per insight, since an ungrounded
qualitative claim is not allowed either.
"""

import re

_NUMBER = re.compile(r"\d+(?:\.\d+)?")

# How each criterion's asserted numbers must line up with the analysis metrics.
# Maps criterion -> list of (metric path into analysis) whose values are the only
# numbers that criterion may state.
_EXPECTED: dict[str, list[tuple[str, str]]] = {
    "fillers": [("fillers", "count"), ("fillers", "rate_per_min")],
    "pacing": [
        ("wpm", "overall_wpm"),
        ("pauses", "count"),
        ("pauses", "total_duration"),
    ],
}


def _as_floats(tokens: list[str]) -> set[float]:
    return {float(t) for t in tokens}


def _matches(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def validate_report(report: dict, analysis: dict) -> dict:
    """Check every numeric claim in a report against the computed metrics.

    report: the dict from generation.generate_report().
    analysis: the metrics dict from features.analyze() the report was built on.

    Returns {"ok": bool, "issues": [str, ...]}. `ok` is True only when, for every
    insight: it has at least one citation; the numbers it declares match the
    corresponding analysis metrics; and every number appearing in its message is
    one of those declared numbers. Any mismatch is reported as a human-readable
    issue rather than raised, so callers can log or surface all problems at once.
    """
    issues: list[str] = []

    for insight in report.get("insights", []):
        criterion = insight.get("criterion", "?")

        if not insight.get("citations"):
            issues.append(f"{criterion}: insight has no citation")

        # (1) declared numbers must equal the analysis metrics for this criterion
        allowed: set[float] = set()
        for group, key in _EXPECTED.get(criterion, []):
            metric_val = analysis.get(group, {}).get(key)
            if metric_val is None:
                issues.append(f"{criterion}: missing metric {group}.{key} in analysis")
                continue
            allowed.add(float(metric_val))

        declared = _as_floats(insight.get("numbers", []))
        for d in declared:
            if not any(_matches(d, a) for a in allowed):
                issues.append(
                    f"{criterion}: declared number {d} does not match any computed metric"
                )

        # (2) every number in the message must be a declared number
        in_message = _as_floats(_NUMBER.findall(insight.get("message", "")))
        for m in in_message:
            if not any(_matches(m, d) for d in declared):
                issues.append(
                    f"{criterion}: message states {m}, which is not a declared metric"
                )

    return {"ok": not issues, "issues": issues}
