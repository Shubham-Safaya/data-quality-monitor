"""Quality report generation from check results."""

from __future__ import annotations

from typing import Any

from data_quality.checks import CheckResult


class QualityReport:
    """Aggregated report of data quality check results."""

    def __init__(self, results: list[CheckResult]) -> None:
        self.results = results

    @property
    def passed(self) -> bool:
        """True if every check passed."""
        return all(r.passed for r in self.results)

    @property
    def pass_rate(self) -> float:
        """Fraction of checks that passed (0.0 to 1.0)."""
        if not self.results:
            return 1.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    @property
    def failing_checks(self) -> list[CheckResult]:
        """List of CheckResults that did not pass."""
        return [r for r in self.results if not r.passed]

    @property
    def passing_checks(self) -> list[CheckResult]:
        """List of CheckResults that passed."""
        return [r for r in self.results if r.passed]

    def summary(self) -> str:
        """Human-readable summary of the report."""
        total = len(self.results)
        passed = len(self.passing_checks)
        failed = len(self.failing_checks)
        rate = self.pass_rate * 100

        lines = [
            f"Data Quality Report",
            f"{'=' * 40}",
            f"Total checks: {total}",
            f"Passed:       {passed}",
            f"Failed:       {failed}",
            f"Pass rate:    {rate:.1f}%",
            f"{'=' * 40}",
        ]

        if self.failing_checks:
            lines.append("")
            lines.append("Failed checks:")
            for r in self.failing_checks:
                lines.append(f"  - {r.check_name}: {r.message}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serializable dictionary representation."""
        return {
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "total_checks": len(self.results),
            "passed_count": len(self.passing_checks),
            "failed_count": len(self.failing_checks),
            "results": [r.to_dict() for r in self.results],
        }

    def __repr__(self) -> str:
        return f"QualityReport(passed={self.passed}, pass_rate={self.pass_rate:.2f}, checks={len(self.results)})"
