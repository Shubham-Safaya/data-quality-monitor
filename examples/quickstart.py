"""Quickstart example: validating a users dataset."""

from data_quality import (
    CheckSuite,
    CustomCheck,
    DataProfiler,
    NotNullCheck,
    RangeCheck,
    RegexCheck,
    UniqueCheck,
)

# Sample dataset
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25},
    {"id": 3, "name": None, "email": "charlie@example.com", "age": 35},
    {"id": 4, "name": "Diana", "email": "not-an-email", "age": 200},
    {"id": 2, "name": "Eve", "email": "eve@example.com", "age": 28},
]

# Define checks
suite = CheckSuite("user_validation")
suite.add_checks([
    NotNullCheck("name"),
    UniqueCheck("id"),
    RangeCheck("age", min_val=0, max_val=150),
    RegexCheck("email", r".+@.+\..+"),
    CustomCheck("name", lambda v: v is not None and len(v) >= 2, "name min length"),
])

# Run checks
report = suite.run(users)

# Print results
print(report.summary())
print()
print(f"Pass rate: {report.pass_rate:.0%}")
print(f"Overall passed: {report.passed}")
print()

# Show failing checks in detail
for check_result in report.failing_checks:
    print(f"FAILED: {check_result.check_name}")
    print(f"  Rows: {check_result.failures}")
    print(f"  Message: {check_result.message}")
    print()

# Profile the dataset
print("=" * 40)
print("Data Profile")
print("=" * 40)
profiler = DataProfiler()
profile = profiler.profile(users)
for col, stats in profile.items():
    print(f"\n{col}:")
    for key, val in stats.items():
        if key == "column":
            continue
        print(f"  {key}: {val}")
