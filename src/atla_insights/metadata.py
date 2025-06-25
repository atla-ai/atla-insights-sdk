"""Utils for the atla_insights package."""

import json
from typing import Optional

from atla_insights.constants import (
    MAX_METADATA_FIELDS,
    MAX_METADATA_KEY_CHARS,
    MAX_METADATA_VALUE_CHARS,
    METADATA_MARK,
)
from atla_insights.span_processors import _metadata, _root_span


def validate_metadata(metadata: Optional[dict[str, str]]) -> None:
    """Validate the user-provided metadata field.

    :param metadata (Optional[dict[str, str]]): The metadata field to validate.
    """
    if metadata is None:
        return

    if not isinstance(metadata, dict):
        raise ValueError("The metadata field must be a dictionary.")

    if not all(isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()):
        raise ValueError("The metadata field must be a mapping of string to string.")

    if len(metadata) > MAX_METADATA_FIELDS:
        raise ValueError(
            f"The metadata field has {len(metadata)} fields, "
            f"but the maximum is {MAX_METADATA_FIELDS}."
        )

    if any(len(k) > MAX_METADATA_KEY_CHARS for k in metadata.keys()):
        raise ValueError(
            "The metadata field must have keys with less than "
            f"{MAX_METADATA_KEY_CHARS} characters."
        )

    if any(len(v) > MAX_METADATA_VALUE_CHARS for v in metadata.values()):
        raise ValueError(
            "The metadata field must have values with less than "
            f"{MAX_METADATA_VALUE_CHARS} characters."
        )


def get_metadata() -> Optional[dict[str, str]]:
    """Get the metadata for the current trace.

    :return (Optional[dict[str, str]]): The metadata for the current trace.
    """
    return _metadata.get()


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
    validate_metadata(metadata)

    _metadata.set(metadata)
    if root_span := _root_span.get():
        # If the root span already exists, we can assign the metadata to it.
        # If not, it will be assigned the `_metadata` context var on creation.
        root_span.set_attribute(METADATA_MARK, json.dumps(metadata))
