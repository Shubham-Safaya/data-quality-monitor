"""Column-level data profiling and statistics."""

from __future__ import annotations

import math
import statistics
from collections import Counter
from datetime import datetime, timezone
from typing import Any


class DataProfiler:
    """Generate column-level statistics from a list of dictionaries."""

    _DATE_FORMATS = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d",
    ]

    def profile(self, data: list[dict]) -> dict[str, dict[str, Any]]:
        """Profile all columns in the dataset.

        Returns a dict mapping column names to their statistics.
        """
        if not data:
            return {}

        # Discover all columns
        columns: set[str] = set()
        for row in data:
            columns.update(row.keys())

        result: dict[str, dict[str, Any]] = {}
        for col in sorted(columns):
            values = [row.get(col) for row in data]
            result[col] = self._profile_column(col, values)

        return result

    def _profile_column(self, name: str, values: list[Any]) -> dict[str, Any]:
        """Compute statistics for a single column."""
        total = len(values)
        null_count = sum(1 for v in values if v is None)
        non_null = [v for v in values if v is not None]

        stats: dict[str, Any] = {
            "column": name,
            "count": total,
            "null_count": null_count,
            "null_rate": null_count / total if total > 0 else 0.0,
            "unique_count": len(set(non_null)),
            "unique_rate": len(set(non_null)) / len(non_null) if non_null else 0.0,
        }

        # Determine column type and add type-specific stats
        col_type = self._infer_type(non_null)
        stats["inferred_type"] = col_type

        if col_type == "numeric":
            stats.update(self._numeric_stats(non_null))
        elif col_type == "datetime":
            stats.update(self._datetime_stats(non_null))
        elif col_type == "string":
            stats.update(self._string_stats(non_null))

        return stats

    def _infer_type(self, values: list[Any]) -> str:
        """Infer the predominant type of non-null values."""
        if not values:
            return "unknown"

        numeric_count = 0
        datetime_count = 0
        string_count = 0

        for v in values:
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric_count += 1
            elif isinstance(v, datetime):
                datetime_count += 1
            elif isinstance(v, str):
                # Check if it looks like a date
                if self._try_parse_date(v) is not None:
                    datetime_count += 1
                else:
                    # Check if it's a numeric string
                    try:
                        float(v)
                        numeric_count += 1
                    except (ValueError, TypeError):
                        string_count += 1
            else:
                string_count += 1

        # Return the dominant type
        counts = {"numeric": numeric_count, "datetime": datetime_count, "string": string_count}
        return max(counts, key=counts.get)  # type: ignore[arg-type]

    def _try_parse_date(self, val: str) -> datetime | None:
        for fmt in self._DATE_FORMATS:
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue
        return None

    def _to_datetime(self, val: Any) -> datetime | None:
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            return self._try_parse_date(val)
        return None

    def _numeric_stats(self, values: list[Any]) -> dict[str, Any]:
        nums = []
        for v in values:
            try:
                nums.append(float(v))
            except (TypeError, ValueError):
                continue

        if not nums:
            return {}

        return {
            "min": min(nums),
            "max": max(nums),
            "mean": round(statistics.mean(nums), 4),
            "median": round(statistics.median(nums), 4),
            "stddev": round(statistics.stdev(nums), 4) if len(nums) > 1 else 0.0,
        }

    def _string_stats(self, values: list[Any]) -> dict[str, Any]:
        strings = [str(v) for v in values]
        lengths = [len(s) for s in strings]
        counter = Counter(strings)
        top = counter.most_common(5)

        return {
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
            "avg_length": round(statistics.mean(lengths), 2) if lengths else 0.0,
            "top_values": [{"value": v, "count": c} for v, c in top],
        }

    def _datetime_stats(self, values: list[Any]) -> dict[str, Any]:
        datetimes: list[datetime] = []
        for v in values:
            dt = self._to_datetime(v)
            if dt is not None:
                datetimes.append(dt)

        if not datetimes:
            return {}

        min_dt = min(datetimes)
        max_dt = max(datetimes)

        # Calculate freshness from most recent timestamp
        now = datetime.now(tz=timezone.utc)
        # Ensure max_dt is timezone-aware for comparison
        max_dt_aware = max_dt if max_dt.tzinfo else max_dt.replace(tzinfo=timezone.utc)
        freshness_hours = (now - max_dt_aware).total_seconds() / 3600

        return {
            "min_date": str(min_dt),
            "max_date": str(max_dt),
            "freshness_hours": round(freshness_hours, 2),
        }
