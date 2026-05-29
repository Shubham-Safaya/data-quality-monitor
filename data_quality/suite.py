"""CheckSuite groups checks and runs them together."""

from __future__ import annotations

from data_quality.checks import Check
from data_quality.report import QualityReport


class CheckSuite:
    """A collection of checks that run against the same dataset."""

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._checks: list[Check] = []

    def add_check(self, check: Check) -> "CheckSuite":
        """Add a single check. Returns self for chaining."""
        self._checks.append(check)
        return self

    def add_checks(self, checks: list[Check]) -> "CheckSuite":
        """Add multiple checks. Returns self for chaining."""
        self._checks.extend(checks)
        return self

    @property
    def checks(self) -> list[Check]:
        return list(self._checks)

    def run(self, data: list[dict]) -> QualityReport:
        """Run all checks and return a QualityReport."""
        results = [check.run(data) for check in self._checks]
        return QualityReport(results)

    def run_with_threshold(self, data: list[dict], min_pass_rate: float = 0.95) -> QualityReport:
        """Run all checks and attach a threshold-based overall pass/fail.

        The returned QualityReport still contains individual results.
        The report's pass_rate can be compared against min_pass_rate
        by the caller to decide whether the dataset is acceptable.

        Returns the QualityReport. Use report.pass_rate >= min_pass_rate
        to check if the threshold is met.
        """
        report = self.run(data)
        return report

    def __len__(self) -> int:
        return len(self._checks)

    def __repr__(self) -> str:
        return f"CheckSuite(name={self.name!r}, checks={len(self._checks)})"
