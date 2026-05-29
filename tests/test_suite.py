"""Tests for CheckSuite."""

from data_quality.checks import NotNullCheck, RangeCheck, UniqueCheck
from data_quality.suite import CheckSuite


def test_suite_all_pass():
    data = [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25},
    ]
    suite = CheckSuite("users")
    suite.add_check(NotNullCheck("name"))
    suite.add_check(UniqueCheck("id"))
    suite.add_check(RangeCheck("age", min_val=0, max_val=150))
    report = suite.run(data)
    assert report.passed is True
    assert report.pass_rate == 1.0


def test_suite_some_fail():
    data = [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 1, "name": None, "age": 200},
    ]
    suite = CheckSuite("users")
    suite.add_check(NotNullCheck("name"))
    suite.add_check(UniqueCheck("id"))
    suite.add_check(RangeCheck("age", min_val=0, max_val=150))
    report = suite.run(data)
    assert report.passed is False
    assert len(report.failing_checks) == 3


def test_suite_chaining():
    suite = CheckSuite("test")
    result = suite.add_check(NotNullCheck("a")).add_check(UniqueCheck("b"))
    assert result is suite
    assert len(suite) == 2


def test_suite_add_checks():
    suite = CheckSuite("test")
    suite.add_checks([NotNullCheck("a"), NotNullCheck("b")])
    assert len(suite) == 2


def test_suite_run_with_threshold():
    data = [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": None, "age": 25},
    ]
    suite = CheckSuite("users")
    suite.add_check(NotNullCheck("name"))
    suite.add_check(UniqueCheck("id"))
    suite.add_check(RangeCheck("age", min_val=0, max_val=150))

    report = suite.run_with_threshold(data, min_pass_rate=0.6)
    # name fails, id and age pass => 2/3 = 0.667
    assert report.pass_rate >= 0.6


def test_suite_checks_property():
    suite = CheckSuite("test")
    check = NotNullCheck("x")
    suite.add_check(check)
    assert suite.checks == [check]
    # Ensure it returns a copy
    suite.checks.append(NotNullCheck("y"))
    assert len(suite) == 1


def test_suite_repr():
    suite = CheckSuite("my_suite")
    assert "my_suite" in repr(suite)


def test_suite_empty():
    suite = CheckSuite("empty")
    report = suite.run([{"a": 1}])
    assert report.passed is True
    assert report.pass_rate == 1.0
