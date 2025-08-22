"""Utility functions for Atla Insights."""

import importlib
from typing import Optional

import opentelemetry.trace
import pygit2
from cuid2 import Cuid
from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider
from opentelemetry.trace import ProxyTracerProvider, get_tracer_provider

_cuid_generator = Cuid()


def truncate_value(value: str, max_chars: int) -> str:
    """Truncate a value to a maximum number of characters.

    :param value (str): The value to truncate.
    :param max_chars (int): The maximum number of characters to allow.
    :return (str): The truncated value.
    """
    if len(value) > max_chars:
        return value[: (max_chars - 3)] + "..."
    return value


def maybe_get_existing_tracer_provider() -> SDKTracerProvider | None:
    """Get the existing tracer provider, if it exists."""
    existing_tracer_provider = get_tracer_provider()

    # If the existing tracer provider is a proxy, there is no existing OTEL setup.
    if isinstance(existing_tracer_provider, ProxyTracerProvider):
        return None

    # If there is an API tracer provider, but not an SDK tracer provider, it is a no-op
    # and we reload the module so we can reset the tracer provider safely.
    if not isinstance(existing_tracer_provider, SDKTracerProvider):
        importlib.reload(opentelemetry.trace)
        return None

    return existing_tracer_provider


def get_git_repo() -> Optional[pygit2.Repository]:
    """Get the current Git repository."""
    try:
        return pygit2.Repository(".")
    except Exception:
        return None


def get_git_branch(repo: Optional[pygit2.Repository] = None) -> Optional[str]:
    """Get the current Git branch name."""
    try:
        repo = repo or get_git_repo()
        if repo is None:
            return None
        if repo.head_is_unborn:
            return None
        return repo.head.shorthand

    except Exception:
        return None


def get_git_commit_hash(repo: Optional[pygit2.Repository] = None) -> Optional[str]:
    """Get the current Git commit hash."""
    try:
        repo = repo or get_git_repo()
        if repo is None:
            return None
        if repo.head_is_unborn:
            return None
        return str(repo.head.target)
    except Exception:
        return None


def get_git_commit_message(repo: Optional[pygit2.Repository] = None) -> Optional[str]:
    """Get the current Git commit message."""
    try:
        repo = repo or get_git_repo()
        if repo is None:
            return None
        if repo.head_is_unborn:
            return None
        commit = repo[repo.head.target]
        return commit.message.strip()  # type: ignore[attr-defined]
    except Exception:
        return None


def generate_cuid() -> str:
    """Generate a new CUID."""
    return _cuid_generator.generate()
