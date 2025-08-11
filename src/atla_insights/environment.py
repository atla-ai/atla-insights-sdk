"""Environment utilities for Atla Insights."""

import os
from typing import Optional

from atla_insights.constants import (
    ENVIRONMENT_DEFAULT,
    ENVIRONMENT_OPTIONS,
    ENVIRONMENT_VAR_NAME,
)


def validate_environment(environment: str) -> str:
    """Validate and return the environment value.

    :param environment (str): The environment to validate.
    :return (SUPPORTED_ENVIRONMENT): The validated environment.
    :raises ValueError: If the environment is not supported.
    """
    if environment not in ENVIRONMENT_OPTIONS:
        raise ValueError(
            f"Invalid environment '{environment}'. "
            f"Only '{ENVIRONMENT_OPTIONS}' are supported."
        )
    return environment


def resolve_environment(
    environment: Optional[str] = None,
) -> str:
    """Resolve the environment value from parameter or environment variable.

    Priority:
    1. environment parameter (if provided)
    2. ATLA_INSIGHTS_ENVIRONMENT environment variable
    3. DEFAULT_ENVIRONMENT ("prod")

    :param environment (Optional[str]): The environment parameter.
    :return (str): The validated environment.
    """
    # Use parameter if provided, otherwise check environment variable, otherwise default
    env_value = environment or os.getenv(ENVIRONMENT_VAR_NAME, ENVIRONMENT_DEFAULT)
    assert isinstance(env_value, str), "Unable to resolve environment."
    return validate_environment(env_value)
