"""Tests for individual check classes."""

from datetime import datetime, timedelta, timezone

from data_quality.checks import (
    CheckResult,
    CustomCheck,
    FreshnessCheck,
    NotNullCheck,
    RangeCheck,
    ReferentialCheck,
    RegexCheck,
    UniqueCheck,
)


# --- NotNullCheck ---

def test_not_null_all_present():
    data = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
    result = NotNullCheck("name").run(data)
    assert result.passed is True
    assert result.failures == []


def test_not_null_with_nulls():
    data = [{"name": "Alice"}, {"name": None}, {"name": "Charlie"}]
    result = NotNullCheck("name").run(data)
    assert result.passed is False
    assert result.failures == [1]


def test_not_null_missing_column():
    data = [{"name": "Alice"}, {"age": 30}]
    result = NotNullCheck("name").run(data)
    assert result.passed is False
    assert 1 in result.failures


def test_not_null_all_null():
    data = [{"name": None}, {"name": None}]
    result = NotNullCheck("name").run(data)
    assert result.passed is False
    assert result.failures == [0, 1]


# --- UniqueCheck ---

def test_unique_all_unique():
    data = [{"id": 1}, {"id": 2}, {"id": 3}]
    result = UniqueCheck("id").run(data)
    assert result.passed is True


def test_unique_with_duplicates():
    data = [{"id": 1}, {"id": 2}, {"id": 1}]
    result = UniqueCheck("id").run(data)
    assert result.passed is False
    assert 0 in result.failures
    assert 2 in result.failures


def test_unique_all_same():
    data = [{"id": "x"}, {"id": "x"}, {"id": "x"}]
    result = UniqueCheck("id").run(data)
    assert result.passed is False
    assert len(result.failures) == 3


# --- RangeCheck ---

def test_range_all_in_range():
    data = [{"age": 25}, {"age": 30}, {"age": 65}]
    result = RangeCheck("age", min_val=18, max_val=100).run(data)
    assert result.passed is True


def test_range_below_min():
    data = [{"age": 10}, {"age": 25}]
    result = RangeCheck("age", min_val=18, max_val=100).run(data)
    assert result.passed is False
    assert result.failures == [0]


def test_range_above_max():
    data = [{"age": 25}, {"age": 150}]
    result = RangeCheck("age", min_val=18, max_val=100).run(data)
    assert result.passed is False
    assert result.failures == [1]


def test_range_min_only():
    data = [{"score": -5}, {"score": 0}, {"score": 100}]
    result = RangeCheck("score", min_val=0).run(data)
    assert result.passed is False
    assert result.failures == [0]


def test_range_max_only():
    data = [{"score": 50}, {"score": 101}]
    result = RangeCheck("score", max_val=100).run(data)
    assert result.passed is False
    assert result.failures == [1]


def test_range_non_numeric():
    data = [{"age": "not_a_number"}]
    result = RangeCheck("age", min_val=0, max_val=100).run(data)
    assert result.passed is False
    assert result.failures == [0]


def test_range_skips_nulls():
    data = [{"age": None}, {"age": 25}]
    result = RangeCheck("age", min_val=0, max_val=100).run(data)
    assert result.passed is True


# --- RegexCheck ---

def test_regex_valid_emails():
    data = [{"email": "a@b.com"}, {"email": "test@example.org"}]
    result = RegexCheck("email", r".+@.+\..+").run(data)
    assert result.passed is True


def test_regex_invalid_email():
    data = [{"email": "a@b.com"}, {"email": "not-an-email"}]
    result = RegexCheck("email", r".+@.+\..+").run(data)
    assert result.passed is False
    assert result.failures == [1]


def test_regex_null_value():
    data = [{"email": None}]
    result = RegexCheck("email", r".+@.+\..+").run(data)
    assert result.passed is False
    assert result.failures == [0]


# --- ReferentialCheck ---

def test_referential_all_valid():
    data = [{"status": "active"}, {"status": "inactive"}]
    result = ReferentialCheck("status", {"active", "inactive", "pending"}).run(data)
    assert result.passed is True


def test_referential_invalid_value():
    data = [{"status": "active"}, {"status": "deleted"}]
    result = ReferentialCheck("status", {"active", "inactive"}).run(data)
    assert result.passed is False
    assert result.failures == [1]


def test_referential_null_not_in_set():
    data = [{"status": None}]
    result = ReferentialCheck("status", {"active"}).run(data)
    assert result.passed is False


# --- CustomCheck ---

def test_custom_check_passing():
    data = [{"score": 10}, {"score": 20}]
    result = CustomCheck("score", lambda v: v > 0, "positive score").run(data)
    assert result.passed is True


def test_custom_check_failing():
    data = [{"score": -1}, {"score": 20}]
    result = CustomCheck("score", lambda v: v > 0, "positive score").run(data)
    assert result.passed is False
    assert result.failures == [0]


def test_custom_check_exception_counts_as_failure():
    data = [{"val": "not_a_number"}]
    result = CustomCheck("val", lambda v: int(v) > 0, "integer check").run(data)
    assert result.passed is False


# --- FreshnessCheck ---

def test_freshness_recent():
    now = datetime.now(tz=timezone.utc)
    recent = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    data = [{"updated_at": recent}]
    result = FreshnessCheck("updated_at", max_age_hours=24).run(data, now=now)
    assert result.passed is True


def test_freshness_stale():
    now = datetime.now(tz=timezone.utc)
    old = (now - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%S")
    data = [{"updated_at": old}]
    result = FreshnessCheck("updated_at", max_age_hours=24).run(data, now=now)
    assert result.passed is False


def test_freshness_null_fails():
    data = [{"updated_at": None}]
    result = FreshnessCheck("updated_at", max_age_hours=24).run(data)
    assert result.passed is False


def test_freshness_unparseable_fails():
    data = [{"updated_at": "not-a-date"}]
    result = FreshnessCheck("updated_at", max_age_hours=24).run(data)
    assert result.passed is False


def test_freshness_datetime_object():
    now = datetime.now(tz=timezone.utc)
    recent = now - timedelta(hours=2)
    data = [{"updated_at": recent}]
    result = FreshnessCheck("updated_at", max_age_hours=24).run(data, now=now)
    assert result.passed is True


# --- CheckResult ---

def test_check_result_to_dict():
    result = CheckResult(
        check_name="NotNullCheck(name)",
        column="name",
        passed=False,
        failures=[1, 3],
        message="2 null value(s) found.",
    )
    d = result.to_dict()
    assert d["passed"] is False
    assert d["failure_count"] == 2
    assert d["failures"] == [1, 3]


# --- Empty data edge cases ---

def test_not_null_empty_data():
    result = NotNullCheck("name").run([])
    assert result.passed is True
    assert result.failures == []


def test_unique_empty_data():
    result = UniqueCheck("id").run([])
    assert result.passed is True


def test_range_empty_data():
    result = RangeCheck("age", min_val=0).run([])
    assert result.passed is True
