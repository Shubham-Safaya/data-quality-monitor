"""Tests for DataProfiler."""

from datetime import datetime, timedelta, timezone

from data_quality.profiler import DataProfiler


def test_profile_numeric_column():
    data = [{"score": 10}, {"score": 20}, {"score": 30}]
    profiler = DataProfiler()
    result = profiler.profile(data)

    assert "score" in result
    stats = result["score"]
    assert stats["count"] == 3
    assert stats["null_count"] == 0
    assert stats["null_rate"] == 0.0
    assert stats["inferred_type"] == "numeric"
    assert stats["min"] == 10.0
    assert stats["max"] == 30.0
    assert stats["mean"] == 20.0
    assert stats["median"] == 20.0


def test_profile_string_column():
    data = [{"city": "NYC"}, {"city": "LA"}, {"city": "NYC"}, {"city": "Chicago"}]
    profiler = DataProfiler()
    result = profiler.profile(data)

    stats = result["city"]
    assert stats["inferred_type"] == "string"
    assert stats["min_length"] == 2
    assert stats["max_length"] == 7
    assert stats["unique_count"] == 3
    # Top values should include NYC with count 2
    top_vals = {v["value"]: v["count"] for v in stats["top_values"]}
    assert top_vals["NYC"] == 2


def test_profile_datetime_column():
    now = datetime.now(tz=timezone.utc)
    data = [
        {"ts": (now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S")},
        {"ts": (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")},
    ]
    profiler = DataProfiler()
    result = profiler.profile(data)

    stats = result["ts"]
    assert stats["inferred_type"] == "datetime"
    assert "min_date" in stats
    assert "max_date" in stats
    assert "freshness_hours" in stats


def test_profile_with_nulls():
    data = [{"val": 1}, {"val": None}, {"val": 3}]
    profiler = DataProfiler()
    result = profiler.profile(data)

    stats = result["val"]
    assert stats["null_count"] == 1
    assert stats["null_rate"] == 1 / 3


def test_profile_unique_rate():
    data = [{"x": "a"}, {"x": "b"}, {"x": "a"}]
    profiler = DataProfiler()
    result = profiler.profile(data)

    stats = result["x"]
    assert stats["unique_count"] == 2
    assert stats["unique_rate"] == 2 / 3


def test_profile_empty_data():
    profiler = DataProfiler()
    result = profiler.profile([])
    assert result == {}


def test_profile_all_nulls():
    data = [{"x": None}, {"x": None}]
    profiler = DataProfiler()
    result = profiler.profile(data)

    stats = result["x"]
    assert stats["null_count"] == 2
    assert stats["null_rate"] == 1.0
    assert stats["unique_count"] == 0
    assert stats["inferred_type"] == "unknown"


def test_profile_mixed_columns():
    data = [
        {"id": 1, "name": "Alice", "created": "2025-01-01"},
        {"id": 2, "name": "Bob", "created": "2025-06-15"},
    ]
    profiler = DataProfiler()
    result = profiler.profile(data)

    assert result["id"]["inferred_type"] == "numeric"
    assert result["name"]["inferred_type"] == "string"
    assert result["created"]["inferred_type"] == "datetime"


def test_profile_single_numeric_stddev():
    data = [{"val": 42}]
    profiler = DataProfiler()
    result = profiler.profile(data)
    # stddev of a single value should be 0
    assert result["val"]["stddev"] == 0.0


def test_profile_missing_keys_across_rows():
    data = [{"a": 1, "b": 2}, {"a": 3}]
    profiler = DataProfiler()
    result = profiler.profile(data)

    assert result["b"]["null_count"] == 1
    assert result["a"]["null_count"] == 0


def test_profile_date_only_strings():
    data = [{"d": "2025-01-15"}, {"d": "2025-06-20"}]
    profiler = DataProfiler()
    result = profiler.profile(data)
    assert result["d"]["inferred_type"] == "datetime"


def test_profile_datetime_objects():
    now = datetime.now(tz=timezone.utc)
    data = [
        {"ts": now - timedelta(hours=10)},
        {"ts": now - timedelta(hours=2)},
    ]
    profiler = DataProfiler()
    result = profiler.profile(data)
    assert result["ts"]["inferred_type"] == "datetime"
    assert result["ts"]["freshness_hours"] >= 1.0
