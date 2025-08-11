"""Environment utilities for Atla Insights."""

import os
from typing import Optional

from atla_insights.constants import (
    DEFAULT_ENVIRONMENT,
    ENVIRONMENT_OPTIONS,
    ENVIRONMENT_VAR_NAME,
)


def validate_environment(environment: str) -> ENVIRONMENT_OPTIONS:
    """Validate and return the environment value.

    :param environment (str): The environment to validate.
    :return (SUPPORTED_ENVIRONMENT): The validated environment.
    :raises ValueError: If the environment is not supported.
    """
    if environment not in ("dev", "prod"):
        raise ValueError(
            f"Invalid environment '{environment}'. Only 'dev' and 'prod' are supported."
        )
    return environment  # type: ignore[return-value]


def get_environment(
    environment: Optional[ENVIRONMENT_OPTIONS] = None,
) -> ENVIRONMENT_OPTIONS:
    """Get the environment value from parameter or environment variable.

    Priority:
    1. environment parameter (if provided)
    2. ATLA_INSIGHTS_ENVIRONMENT environment variable
    3. DEFAULT_ENVIRONMENT ("prod")

    :param environment (Optional[SUPPORTED_ENVIRONMENT]): The environment parameter.
    :return (SUPPORTED_ENVIRONMENT): The validated environment.
    """
    # Use parameter if provided, otherwise check environment variable, otherwise default
    env_value = environment or os.getenv(ENVIRONMENT_VAR_NAME, DEFAULT_ENVIRONMENT)
    return validate_environment(env_value)
