"""Experiment support for the atla_insights package."""

import uuid
from contextlib import contextmanager
from typing import Generator, Optional, TypedDict

from human_id import generate_id

from atla_insights.context import experiment_var
from atla_insights.main import logger


class Experiment(TypedDict):
    """A run of an experiment."""

    name: str
    description: Optional[str]


@contextmanager
def run_experiment(
    experiment_name: Optional[str] = None,
    description: Optional[str] = None,
) -> Generator[Experiment, None, None]:
    """Context manager for running experiments with automatic tracking.

    This sets up experiment and experiment run context variables and
    ensures proper OpenTelemetry attributes are set for tracking.

    Args:
        experiment_name (Optional[str]): Name of the experiment. Defaults to a
            human-readable random ID.
        description (Optional[str]): Optional description for this experiment run.
            Defaults to None.

    Yields:
        Experiment: The experiment instance
    """
    if experiment_name is None:
        experiment_name = generate_id(word_count=3) + "-" + uuid.uuid4().hex[:8]

    logger.info(f"Running experiment {experiment_name}...")

    # Create experiment run object in context
    experiment = Experiment(name=experiment_name, description=description)
    experiment_token = experiment_var.set(experiment)

    # The context variable is now available to the root span processor
    try:
        yield experiment
    finally:
        experiment_var.reset(experiment_token)

    logger.info(f"Ended experiment {experiment_name} ✅")
