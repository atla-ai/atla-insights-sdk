"""Utils for the atla_insights package."""

import json
import logging
from itertools import islice
from typing import Optional

from atla_insights.constants import (
    MAX_METADATA_FIELDS,
    MAX_METADATA_KEY_CHARS,
    MAX_METADATA_VALUE_CHARS,
    METADATA_MARK,
    OTEL_MODULE_NAME,
)
from atla_insights.context import metadata_var, root_span_var

logger = logging.getLogger(OTEL_MODULE_NAME)

_GLOBAL_METADATA: Optional[dict[str, str]] = None


def _truncate_value(value: str, max_chars: int) -> str:
    """Truncate a value to a maximum number of characters.

    :param value (str): The value to truncate.
    :param max_chars (int): The maximum number of characters to allow.
    :return (str): The truncated value.
    """
    if len(value) > max_chars:
        return value[: (max_chars - 3)] + "..."
    return value


def validate_metadata(metadata: dict[str, str]) -> dict[str, str]:
    """Validate the user-provided metadata field.

    :param metadata (dict[str, str]): The metadata field to validate.
    :return (dict[str, str]): The validated metadata.
    """
    if not isinstance(metadata, dict):
        raise ValueError("The metadata field must be a dictionary.")

    if not all(isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()):
        logger.error("The metadata field must be a mapping of string to string.")
        metadata = {str(k): str(v) for k, v in metadata.items()}

    if len(metadata) > MAX_METADATA_FIELDS:
        logger.error(
            f"The metadata field has {len(metadata)} fields, "
            f"but the maximum is {MAX_METADATA_FIELDS}."
        )
        metadata = dict(islice(metadata.items(), MAX_METADATA_FIELDS))

    if any(len(k) > MAX_METADATA_KEY_CHARS for k in metadata.keys()):
        logger.error(
            "The metadata field must have keys with less than "
            f"{MAX_METADATA_KEY_CHARS} characters."
        )
        metadata = {
            _truncate_value(k, MAX_METADATA_KEY_CHARS): v for k, v in metadata.items()
        }

    if any(len(v) > MAX_METADATA_VALUE_CHARS for v in metadata.values()):
        logger.error(
            "The metadata field must have values with less than "
            f"{MAX_METADATA_VALUE_CHARS} characters."
        )
        metadata = {
            k: _truncate_value(v, MAX_METADATA_VALUE_CHARS) for k, v in metadata.items()
        }

    return metadata


def get_metadata() -> Optional[dict[str, str]]:
    """Get the metadata for the current trace.

    :return (Optional[dict[str, str]]): The metadata for the current trace.
    """
    return metadata_var.get() or _GLOBAL_METADATA


def set_global_metadata(metadata: dict[str, str]) -> None:
    """Set the global metadata.

    :param metadata (dict[str, str]): The global metadata.
    """
    metadata = validate_metadata(metadata)

    global _GLOBAL_METADATA
    _GLOBAL_METADATA = metadata


def set_metadata(metadata: dict[str, str]) -> None:
    """Set the metadata for the current trace.

    ```py
    from atla_insights import instrument, set_metadata

    @instrument("My Function")
    def my_function():
        set_metadata({"some_key": "some_value", "other_key": "other_value"})
        ...
    ```

    :param metadata (dict[str, str]): The metadata to set for the current trace.
    """
    metadata = validate_metadata(metadata)

    metadata_var.set(metadata)
    if root_span := root_span_var.get():
        # If the root span already exists, we can assign the metadata to it.
        # If not, it will be assigned the `metadata_var` context var on creation.
        root_span.set_attribute(METADATA_MARK, json.dumps(metadata))
