"""Individual data quality check classes."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass
class CheckResult:
    """Result of running a single data quality check."""

    check_name: str
    column: str
    passed: bool
    failures: list[int] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "column": self.column,
            "passed": self.passed,
            "failure_count": len(self.failures),
            "failures": self.failures,
            "message": self.message,
        }


class Check(ABC):
    """Base class for all data quality checks."""

    def __init__(self, column: str) -> None:
        self.column = column

    @property
    def name(self) -> str:
        return f"{self.__class__.__name__}({self.column})"

    @abstractmethod
    def run(self, data: list[dict]) -> CheckResult:
        ...

    def _get_values(self, data: list[dict]) -> list[tuple[int, Any]]:
        """Return (row_index, value) pairs for the target column."""
        return [(i, row.get(self.column)) for i, row in enumerate(data)]


class NotNullCheck(Check):
    """Fails if any values in the column are None."""

    def run(self, data: list[dict]) -> CheckResult:
        failures = [i for i, val in self._get_values(data) if val is None]
        passed = len(failures) == 0
        message = "All values are non-null." if passed else f"{len(failures)} null value(s) found."
        return CheckResult(
            check_name=self.name,
            column=self.column,
            passed=passed,
            failures=failures,
            message=message,
        )


class UniqueCheck(Check):
    """Fails if any duplicate values exist in the column."""

    def run(self, data: list[dict]) -> CheckResult:
        seen: dict[Any, int] = {}
        failures: list[int] = []
        for i, val in self._get_values(data):
            if val in seen:
                failures.append(i)
                # Also mark the first occurrence if not already marked
                first = seen[val]
                if first not in failures:
                    failures.append(first)
            else:
                seen[val] = i
        failures.sort()
        passed = len(failures) == 0
        message = "All values are unique." if passed else f"{len(failures)} row(s) involved in duplicates."
        return CheckResult(
            check_name=self.name,
            column=self.column,
            passed=passed,
            failures=failures,
            message=message,
        )


class RangeCheck(Check):
    """Fails if any numeric value falls outside [min_val, max_val]."""

    def __init__(self, column: str, min_val: float | None = None, max_val: float | None = None) -> None:
        super().__init__(column)
        self.min_val = min_val
        self.max_val = max_val

    @property
    def name(self) -> str:
        return f"RangeCheck({self.column}, min={self.min_val}, max={self.max_val})"

    def run(self, data: list[dict]) -> CheckResult:
        failures: list[int] = []
        for i, val in self._get_values(data):
            if val is None:
                continue
            try:
                num = float(val)
            except (TypeError, ValueError):
                failures.append(i)
                continue
            if self.min_val is not None and num < self.min_val:
                failures.append(i)
            elif self.max_val is not None and num > self.max_val:
                failures.append(i)
        passed = len(failures) == 0
        message = "All values within range." if passed else f"{len(failures)} value(s) out of range."
        return CheckResult(
            check_name=self.name,
            column=self.column,
            passed=passed,
            failures=failures,
            message=message,
        )


class RegexCheck(Check):
    """Fails if any string value does not match the given regex pattern."""

    def __init__(self, column: str, pattern: str) -> None:
        super().__init__(column)
        self.pattern = pattern
        self._compiled = re.compile(pattern)

    @property
    def name(self) -> str:
        return f"RegexCheck({self.column}, pattern={self.pattern!r})"

    def run(self, data: list[dict]) -> CheckResult:
        failures: list[int] = []
        for i, val in self._get_values(data):
            if val is None:
                failures.append(i)
                continue
            if not self._compiled.fullmatch(str(val)):
                failures.append(i)
        passed = len(failures) == 0
        message = "All values match pattern." if passed else f"{len(failures)} value(s) do not match pattern."
        return CheckResult(
            check_name=self.name,
            column=self.column,
            passed=passed,
            failures=failures,
            message=message,
        )


class ReferentialCheck(Check):
    """Fails if any value is not in the set of allowed reference values."""

    def __init__(self, column: str, reference_values: set[Any] | list[Any]) -> None:
        super().__init__(column)
        self.reference_values = set(reference_values)

    @property
    def name(self) -> str:
        return f"ReferentialCheck({self.column})"

    def run(self, data: list[dict]) -> CheckResult:
        failures: list[int] = []
        for i, val in self._get_values(data):
            if val not in self.reference_values:
                failures.append(i)
        passed = len(failures) == 0
        message = (
            "All values found in reference set."
            if passed
            else f"{len(failures)} value(s) not in reference set."
        )
        return CheckResult(
            check_name=self.name,
            column=self.column,
            passed=passed,
            failures=failures,
            message=message,
        )


class CustomCheck(Check):
    """Runs an arbitrary function against each value. The function should return True for valid values."""

    def __init__(self, column: str, func: Callable[[Any], bool], description: str = "") -> None:
        super().__init__(column)
        self.func = func
        self.description = description or "custom check"

    @property
    def name(self) -> str:
        return f"CustomCheck({self.column}, {self.description})"

    def run(self, data: list[dict]) -> CheckResult:
        failures: list[int] = []
        for i, val in self._get_values(data):
            try:
                if not self.func(val):
                    failures.append(i)
            except Exception:
                failures.append(i)
        passed = len(failures) == 0
        message = (
            f"Custom check '{self.description}' passed."
            if passed
            else f"{len(failures)} value(s) failed custom check '{self.description}'."
        )
        return CheckResult(
            check_name=self.name,
            column=self.column,
            passed=passed,
            failures=failures,
            message=message,
        )


class FreshnessCheck(Check):
    """Fails if any timestamp is older than max_age_hours from now.

    Supports datetime objects and ISO-format date strings.
    """

    # Common ISO formats to try when parsing strings
    _FORMATS = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d",
    ]

    def __init__(self, column: str, max_age_hours: float) -> None:
        super().__init__(column)
        self.max_age_hours = max_age_hours

    @property
    def name(self) -> str:
        return f"FreshnessCheck({self.column}, max_age={self.max_age_hours}h)"

    def _parse_datetime(self, val: Any) -> datetime | None:
        if isinstance(val, datetime):
            return val
        if not isinstance(val, str):
            return None
        for fmt in self._FORMATS:
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue
        return None

    def run(self, data: list[dict], *, now: datetime | None = None) -> CheckResult:
        now = now or datetime.now(tz=timezone.utc)
        failures: list[int] = []
        for i, val in self._get_values(data):
            if val is None:
                failures.append(i)
                continue
            dt = self._parse_datetime(val)
            if dt is None:
                failures.append(i)
                continue
            # Make naive datetimes comparable by treating them as UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_hours = (now - dt).total_seconds() / 3600
            if age_hours > self.max_age_hours:
                failures.append(i)
        passed = len(failures) == 0
        message = (
            f"All timestamps within {self.max_age_hours}h."
            if passed
            else f"{len(failures)} timestamp(s) exceed {self.max_age_hours}h age limit."
        )
        return CheckResult(
            check_name=self.name,
            column=self.column,
            passed=passed,
            failures=failures,
            message=message,
        )
