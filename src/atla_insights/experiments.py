"""Experiment support for the atla_insights package."""

import uuid
from contextlib import contextmanager
from typing import Generator, Optional, TypedDict

from human_id import generate_id

from atla_insights.context import experiment_run_var
from atla_insights.utils import generate_cuid


class ExperimentRun(TypedDict):
    """A run of an experiment."""

    id: str
    experiment_id: str
    description: Optional[str]


@contextmanager
def run_experiment(
    experiment_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Generator[ExperimentRun, None, None]:
    """Context manager for running experiments with automatic tracking.

    This sets up experiment and experiment run context variables and
    ensures proper OpenTelemetry attributes are set for tracking.

    Args:
        experiment_id (Optional[str]): ID of the experiment to generate a run for.
            Defaults to a human-readable random ID.
        description (Optional[str]): Optional description for this experiment run.
            Defaults to None.

    Yields:
        ExperimentRun: The experiment run instance
    """
    if experiment_id is None:
        experiment_id = generate_id(word_count=3) + "-" + uuid.uuid4().hex[:8]

    # Create experiment run object in context
    experiment_run = ExperimentRun(
        id=generate_cuid(),
        experiment_id=experiment_id,
        description=description,
    )
    experiment_run_token = experiment_run_var.set(experiment_run)

    # The context variable is now available to the root span processor
    try:
        yield experiment_run
    finally:
        # Clean up context
        experiment_run_var.reset(experiment_run_token)
