"""Git information."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import pygit2


class GitInfo:
    """Git information."""

    def __init__(self, repo: pygit2.Repository | None = None) -> None:
        """Initialize the GitInfo object."""
        self.repo = repo or self.get_git_repo()

        self.attributes: dict[str, str | None] = {
            "atla.git.branch": self.get_git_branch(),
            "atla.git.commit.hash": self.get_git_commit_hash(),
            "atla.git.commit.message": self.get_git_commit_message(),
            "atla.git.commit.timestamp": self.get_git_commit_timestamp(),
            "atla.git.repo": self.get_git_repo_url(),
            "atla.git.semver": self.get_git_semver(),
        }

    def get_git_repo(self) -> Optional[pygit2.Repository]:
        """Get the current Git repository."""
        try:
            return pygit2.Repository(".")
        except Exception:
            return None

    def get_git_repo_url(self) -> Optional[str]:
        """Get the current Git repository remote URL."""
        try:
            if repo_url := os.environ.get("ATLA_GIT_REPO"):
                return repo_url
            if self.repo is None:
                return None
            if self.repo.remotes is None:
                return None
            return self.repo.remotes["origin"].url
        except Exception:
            return None

    def get_git_branch(self) -> Optional[str]:
        """Get the current Git branch name."""
        try:
            if git_branch := os.environ.get("ATLA_GIT_BRANCH"):
                return git_branch
            if self.repo is None:
                return None
            if self.repo.head_is_unborn:
                return None
            return self.repo.head.shorthand

        except Exception:
            return None

    def get_git_commit_hash(self) -> Optional[str]:
        """Get the current Git commit hash."""
        try:
            if git_commit_hash := os.environ.get("ATLA_GIT_COMMIT_HASH"):
                return git_commit_hash
            if self.repo is None:
                return None
            if self.repo.head_is_unborn:
                return None
            return str(self.repo.head.target)
        except Exception:
            return None

    def get_git_commit_message(self) -> Optional[str]:
        """Get the current Git commit message."""
        try:
            if git_commit_message := os.environ.get("ATLA_GIT_COMMIT_MESSAGE"):
                return git_commit_message
            if self.repo is None:
                return None
            if self.repo.head_is_unborn:
                return None
            commit = self.repo[self.repo.head.target]
            return commit.message.strip()  # type: ignore[attr-defined]
        except Exception:
            return None

    def get_git_commit_timestamp(self) -> Optional[str]:
        """Get the current Git commit message."""
        try:
            if git_commit_timestamp := os.environ.get("ATLA_GIT_COMMIT_TIMESTAMP"):
                return git_commit_timestamp
            if self.repo is None:
                return None
            if self.repo.head_is_unborn:
                return None
            commit = self.repo[self.repo.head.target]
            tz = timezone(timedelta(minutes=commit.commit_time_offset))  # type: ignore[attr-defined]
            return datetime.fromtimestamp(commit.commit_time, tz=tz).isoformat()  # type: ignore[attr-defined]
        except Exception:
            return None

    def get_git_semver(self) -> Optional[str]:
        """Get the current Git commit message."""
        try:
            if git_semver := os.environ.get("ATLA_GIT_SEMVER"):
                return git_semver
            if self.repo is None:
                return None
            if self.repo.head_is_unborn:
                return None
            commit = self.repo[self.repo.head.target]
            return self.repo.describe(
                commit,  # type: ignore[arg-type]
                describe_strategy=pygit2.GIT_DESCRIBE_TAGS,  # type: ignore[arg-type]
                abbreviated_size=0,
            )
        except Exception:
            return None
