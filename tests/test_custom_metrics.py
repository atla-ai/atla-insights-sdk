"""Tests for the custom metrics module."""

import json
from typing import Any, Literal, cast

import pytest

from tests._otel import BaseLocalOtel


class TestCustomMetrics(BaseLocalOtel):
    """Test the custom metrics."""

    def test_custom_metrics(self) -> None:
        """Test that custom metrics are added to the root span correctly."""
        from atla_insights import instrument
        from atla_insights.constants import CUSTOM_METRICS_MARK
        from atla_insights.custom_metrics import set_custom_metrics

        @instrument()
        def test_function():
            set_custom_metrics({"test": {"data_type": "likert_1_to_5", "value": 1}})
            return "test result"

        test_function()
        spans = self.get_finished_spans()

        assert len(spans) == 1
        [span] = spans

        assert span.attributes is not None
        assert span.attributes.get(CUSTOM_METRICS_MARK) is not None

        custom_metrics = json.loads(cast(str, span.attributes.get(CUSTOM_METRICS_MARK)))
        assert custom_metrics == {"test": {"data_type": "likert_1_to_5", "value": 1}}

    def test_custom_metrics_run_isolation(self) -> None:
        """Test that custom metrics are isolated between runs."""
        from atla_insights import instrument
        from atla_insights.constants import CUSTOM_METRICS_MARK
        from atla_insights.custom_metrics import set_custom_metrics

        @instrument()
        def test_function():
            set_custom_metrics({"test": {"data_type": "likert_1_to_5", "value": 2}})
            return "test result"

        @instrument()
        def test_function_2():
            return "test result"

        test_function()
        test_function_2()

        spans = self.get_finished_spans()

        assert len(spans) == 2
        [span_1, span_2] = spans

        assert span_1.attributes is not None
        assert span_1.attributes.get(CUSTOM_METRICS_MARK) is not None

        assert span_2.attributes is not None
        assert span_2.attributes.get(CUSTOM_METRICS_MARK) is None

    def test_get_set_custom_metrics(self) -> None:
        """Test that the custom metrics is set and retrieved correctly."""
        from atla_insights import instrument
        from atla_insights.constants import CUSTOM_METRICS_MARK
        from atla_insights.custom_metrics import (
            CustomMetric,
            get_custom_metrics,
            set_custom_metrics,
        )

        @instrument()
        def test_function():
            metrics_1: dict[str, CustomMetric] = {  # type: ignore[annotation-unchecked]
                "test": {"data_type": "boolean", "value": False}
            }
            set_custom_metrics(metrics_1)
            assert get_custom_metrics() == metrics_1

            metrics_2: dict[str, CustomMetric] = {  # type: ignore[annotation-unchecked]
                "test": {"data_type": "boolean", "value": True}
            }
            set_custom_metrics(metrics_2)
            assert get_custom_metrics() == metrics_2

            return "test result"

        test_function()
        spans = self.get_finished_spans()

        assert len(spans) == 1
        [span] = spans

        assert span.attributes is not None
        assert span.attributes.get(CUSTOM_METRICS_MARK) is not None

    @pytest.mark.parametrize(
        "data_type,value,is_valid",
        [
            ("boolean", True, True),
            ("boolean", False, True),
            ("boolean", 1, False),
            ("likert_1_to_5", 1, True),
            ("likert_1_to_5", 2, True),
            ("likert_1_to_5", 3, True),
            ("likert_1_to_5", 4, True),
            ("likert_1_to_5", 5, True),
            ("likert_1_to_5", 0, False),
            ("likert_1_to_5", 6, False),
            ("likert_1_to_5", "1", False),
            ("likert_1_to_5", "2", False),
            ("likert_1_to_5", "3", False),
            ("likert_1_to_5", "4", False),
        ],
    )
    def test_validate_custom_metrics(
        self,
        data_type: Literal["boolean", "likert_1_to_5"],
        value: Any,
        is_valid: bool,
    ) -> None:
        """Test that the custom metrics are validated correctly."""
        from atla_insights.custom_metrics import _validate_custom_metrics

        custom_metrics = _validate_custom_metrics(
            {"test": {"data_type": data_type, "value": value}}  # type: ignore
        )

        if is_valid:
            assert custom_metrics == {"test": {"data_type": data_type, "value": value}}
        else:
            assert custom_metrics == {}
