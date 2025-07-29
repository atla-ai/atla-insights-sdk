"""Custom metrics for the atla_insights package."""

import logging
from itertools import islice
from typing import Annotated, Literal, Optional, TypedDict, Union

from pydantic import Field

from atla_insights.constants import (
    MAX_CUSTOM_METRICS_FIELDS,
    MAX_CUSTOM_METRICS_KEY_CHARS,
    OTEL_MODULE_NAME,
)
from atla_insights.context import custom_metrics_var
from atla_insights.utils import truncate_value

logger = logging.getLogger(OTEL_MODULE_NAME)


class Likert1To5Metric(TypedDict):
    """Custom metric on a likert scale of 1 to 5."""

    data_type: Literal["likert_1_to_5"]
    value: Literal[1, 2, 3, 4, 5]


class BooleanMetric(TypedDict):
    """Custom metric."""

    data_type: Literal["boolean"]
    value: bool


CustomMetric = Annotated[
    Union[Likert1To5Metric, BooleanMetric], Field(discriminator="data_type")
]


def validate_custom_metrics(
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

    return custom_metrics


def set_custom_metrics(custom_metrics: dict[str, CustomMetric]) -> None:
    """Set the custom metrics for the current trace."""
    custom_metrics = validate_custom_metrics(custom_metrics)
    custom_metrics_var.set(custom_metrics)


def get_custom_metrics() -> Optional[dict[str, CustomMetric]]:
    """Get the custom metrics for the current trace."""
    return custom_metrics_var.get()
