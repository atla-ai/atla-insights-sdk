"""Experiment support for the atla_insights package."""

from contextlib import contextmanager
from typing import Generator, Optional, TypedDict

from atla_insights.context import experiment_run_var
from atla_insights.utils import (
    generate_cuid,
    get_git_branch,
    get_git_commit_hash,
    get_git_commit_message,
)


class ExperimentRun(TypedDict):
    """A run of an experiment."""

    id: str
    experiment_id: str

    description: Optional[str]

    git_branch: Optional[str]
    git_commit_hash: Optional[str]
    git_commit_message: Optional[str]


@contextmanager
def run_experiment(
    experiment_id: str,
    description: Optional[str] = None,
) -> Generator[ExperimentRun, None, None]:
    """Context manager for running experiments with automatic tracking.

    This sets up experiment and experiment run context variables and
    ensures proper OpenTelemetry attributes are set for tracking.

    Args:
        experiment_id: ID of the experiment to generate a run for
        description: Optional description for this experiment run

    Yields:
        ExperimentRun: The experiment run instance
    """
    # Create experiment run object in context
    experiment_run = ExperimentRun(
        id=generate_cuid(),
        experiment_id=experiment_id,
        description=description,
        git_branch=get_git_branch(),
        git_commit_hash=get_git_commit_hash(),
        git_commit_message=get_git_commit_message(),
    )
    experiment_run_token = experiment_run_var.set(experiment_run)

    # The context variable is now available to the root span processor
    try:
        yield experiment_run
    finally:
        # Clean up context
        experiment_run_var.reset(experiment_run_token)
