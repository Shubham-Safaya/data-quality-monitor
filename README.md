# data-quality-monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Shubham-Safaya/data-quality-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/Shubham-Safaya/data-quality-monitor/actions)

**Lightweight data quality monitoring for Python. No YAML. No dependencies. Just checks.**

Define validation rules in pure Python, run them against your data, and get clear pass/fail reports. Zero runtime dependencies -- uses only the standard library.

## Install

```bash
pip install data-quality-monitor
```

## Quick Start

```python
from data_quality import CheckSuite, NotNullCheck, UniqueCheck, RangeCheck, RegexCheck

users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30},
    {"id": 2, "name": "Bob",   "email": "bob@example.com",   "age": 25},
    {"id": 3, "name": None,    "email": "not-an-email",       "age": 200},
]

suite = CheckSuite("user_validation")
suite.add_checks([
    NotNullCheck("name"),
    UniqueCheck("id"),
    RangeCheck("age", min_val=0, max_val=150),
    RegexCheck("email", r".+@.+\..+"),
])

report = suite.run(users)
print(report.summary())
# Pass rate: 50.0%
# Failed: NotNullCheck(name), RangeCheck(age), RegexCheck(email)
```

## Features

- **7 built-in checks**: NotNull, Unique, Range, Regex, Referential, Custom, Freshness
- **CheckSuite**: group checks, run them together, get a unified report
- **QualityReport**: pass/fail status, pass rate, serializable output via `to_dict()`
- **DataProfiler**: column-level statistics (nulls, uniques, numeric stats, string lengths, date freshness)
- **Threshold mode**: `run_with_threshold(data, min_pass_rate=0.95)` for soft validation
- **Zero dependencies**: stdlib only, works everywhere Python runs
- **Plain Python data**: operates on `list[dict]` -- no DataFrame library required

## Check Types

| Check | What it validates |
|-------|-------------------|
| `NotNullCheck(col)` | No None values |
| `UniqueCheck(col)` | No duplicate values |
| `RangeCheck(col, min, max)` | Numeric values within bounds |
| `RegexCheck(col, pattern)` | String values match regex |
| `ReferentialCheck(col, allowed)` | Values exist in reference set |
| `CustomCheck(col, func, desc)` | Arbitrary validation function |
| `FreshnessCheck(col, max_hours)` | Timestamps within age limit |

## Data Profiling

```python
from data_quality import DataProfiler

profiler = DataProfiler()
profile = profiler.profile(users)

# Returns per-column stats:
# - count, null_count, null_rate, unique_count, unique_rate
# - Numeric: min, max, mean, median, stddev
# - String: min_length, max_length, avg_length, top_values
# - Datetime: min_date, max_date, freshness_hours
```

## Comparison

| Feature | data-quality-monitor | Great Expectations | Soda | Deequ |
|---------|---------------------|--------------------|------|-------|
| Config format | Pure Python | YAML + Python | YAML | Scala/PySpark |
| Dependencies | 0 (stdlib) | 50+ packages | 20+ packages | Spark required |
| Setup time | 2 minutes | 30+ minutes | 15+ minutes | 30+ minutes |
| Learning curve | Minimal | Steep | Moderate | Steep |
| Data format | `list[dict]` | DataFrame | SQL/DataFrame | Spark DataFrame |
| Best for | Small-medium pipelines | Enterprise | Cloud DWH | Spark pipelines |

## Development

```bash
git clone https://github.com/Shubham-Safaya/data-quality-monitor.git
cd data-quality-monitor
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## License

MIT
