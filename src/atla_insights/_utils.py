"""Utils for the atla_insights package."""

from typing import Optional

from ._constants import (
    MAX_METADATA_FIELDS,
    MAX_METADATA_KEY_CHARS,
    MAX_METADATA_VALUE_CHARS,
)


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
