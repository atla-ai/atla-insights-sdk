"""Custom metrics for the atla_insights package."""

import json
import logging
from itertools import islice
from typing import Literal, Optional, TypedDict, Union, cast

from atla_insights.constants import (
    CUSTOM_METRICS_MARK,
    MAX_CUSTOM_METRICS_FIELDS,
    MAX_CUSTOM_METRICS_KEY_CHARS,
    OTEL_MODULE_NAME,
)
from atla_insights.context import root_span_var
from atla_insights.suppression import is_instrumentation_suppressed
from atla_insights.utils import truncate_value

logger = logging.getLogger(OTEL_MODULE_NAME)


class Likert1To5Metric(TypedDict):
    """Custom metric on a Likert scale of 1 to 5."""

    data_type: Literal["likert_1_to_5"]
    value: Literal[1, 2, 3, 4, 5]


class BooleanMetric(TypedDict):
    """Custom metric."""

    data_type: Literal["boolean"]
    value: bool


CustomMetric = Union[Likert1To5Metric, BooleanMetric]


def _validate_custom_metrics(
    custom_metrics: dict[str, CustomMetric],
) -> dict[str, CustomMetric]:
    """Validate the user-provided custom metrics.

    :param custom_metrics (dict[str, CustomMetric]): The custom metrics to validate.
    :return (dict[str, CustomMetric]): The validated custom metrics.
    """
    if not isinstance(custom_metrics, dict):
        raise ValueError("The custom metrics field must be a dictionary.")

    if len(custom_metrics) > MAX_CUSTOM_METRICS_FIELDS:
        logger.error(
            f"The custom metrics field has {len(custom_metrics)} fields, "
            f"but the maximum is {MAX_CUSTOM_METRICS_FIELDS}."
        )
        custom_metrics = dict(islice(custom_metrics.items(), MAX_CUSTOM_METRICS_FIELDS))

    if any(len(k) > MAX_CUSTOM_METRICS_KEY_CHARS for k in custom_metrics.keys()):
        logger.error(
            "The custom metrics field must have keys with less than "
            f"{MAX_CUSTOM_METRICS_KEY_CHARS} characters."
        )
        custom_metrics = {
            truncate_value(k, MAX_CUSTOM_METRICS_KEY_CHARS): v
            for k, v in custom_metrics.items()
        }

    for k, v in custom_metrics.copy().items():
        match v["data_type"]:
            case "likert_1_to_5":
                if not isinstance(v["value"], int) or v["value"] not in [1, 2, 3, 4, 5]:
                    logger.error(
                        f"The custom metric {k} has an invalid value: {v['value']}. "
                        "The value must be an integer between 1 and 5."
                    )
                    custom_metrics.pop(k)
            case "boolean":
                if not isinstance(v["value"], bool):
                    logger.error(
                        f"The custom metric {k} has an invalid value: {v['value']}. "
                        "The value must be a boolean."
                    )
                    custom_metrics.pop(k)
            case _:
                logger.error(
                    f"The custom metric {k} has an invalid data type: {v['data_type']}. "
                    "The data type must be 'likert_1_to_5' or 'boolean'."
                )
                custom_metrics.pop(k)

    return custom_metrics


def set_custom_metrics(custom_metrics: dict[str, CustomMetric]) -> None:
    """Set the custom metrics for the current trace.

    ```py
    from atla_insights import instrument, set_custom_metrics

    @instrument()
    def my_function():
        # Some GenAI logic here
        eval_result = False
        set_custom_metrics({"my_metric": {"data_type": "boolean", "value": eval_result}})
    ```

    :param custom_metrics (dict[str, CustomMetric]): The custom metrics to set.
    """
    if is_instrumentation_suppressed():
        return

    custom_metrics = _validate_custom_metrics(custom_metrics)
    if not custom_metrics:
        return

    if root_span := root_span_var.get():
        root_span.set_attribute(CUSTOM_METRICS_MARK, json.dumps(custom_metrics))
    else:
        logger.error("Cannot set custom metrics outside of an active trace.")


def get_custom_metrics() -> Optional[dict[str, CustomMetric]]:
    """Get the custom metrics for the current trace.

    :return (Optional[dict[str, CustomMetric]]): The custom metrics for the current trace.
    """
    root_span = root_span_var.get()

    if root_span is None:
        return None

    if root_span.attributes is None:
        return None

    custom_metrics = root_span.attributes.get(CUSTOM_METRICS_MARK)

    if custom_metrics is None:
        return None

    return json.loads(cast(str, custom_metrics))
