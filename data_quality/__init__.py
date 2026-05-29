"""Lightweight data quality monitoring for Python."""

from data_quality.checks import (
    Check,
    CheckResult,
    CustomCheck,
    FreshnessCheck,
    NotNullCheck,
    RangeCheck,
    ReferentialCheck,
    RegexCheck,
    UniqueCheck,
)
from data_quality.profiler import DataProfiler
from data_quality.report import QualityReport
from data_quality.suite import CheckSuite

__version__ = "0.1.0"

__all__ = [
    "Check",
    "CheckResult",
    "CheckSuite",
    "CustomCheck",
    "DataProfiler",
    "FreshnessCheck",
    "NotNullCheck",
    "QualityReport",
    "RangeCheck",
    "ReferentialCheck",
    "RegexCheck",
    "UniqueCheck",
]
