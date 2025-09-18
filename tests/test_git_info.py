"""Test the git_info module."""

import os
from unittest.mock import patch

from atla_insights.constants import GIT_TRACKING_DISABLED_ENV_VAR
from tests._otel import BaseLocalOtel


class TestGitInfo(BaseLocalOtel):
    """Test the git_info module."""

    def test_git_info(self) -> None:
        """Test the get_git_info function."""
        from atla_insights import instrument

        @instrument("test_git_info")
        def test_function():
            """Test the get_git_info function."""
            ...

        test_function()

        [span] = self.get_finished_spans()

        assert span.attributes is not None

        assert span.attributes.get("atla.git.branch") is not None
        assert span.attributes.get("atla.git.commit.hash") is not None
        assert span.attributes.get("atla.git.commit.message") is not None
        assert span.attributes.get("atla.git.commit.timestamp") is not None
        assert span.attributes.get("atla.git.repo") is not None

    def test_git_info_opt_out(self) -> None:
        """Test the get_git_info function."""
        from atla_insights import instrument

        with patch.dict(os.environ, {GIT_TRACKING_DISABLED_ENV_VAR: "1"}):

            @instrument("test_git_info")
            def test_function():
                """Test the get_git_info function."""
                ...

            test_function()

            [span] = self.get_finished_spans()

        assert span.attributes is not None

        assert span.attributes.get("atla.git.branch") is None
        assert span.attributes.get("atla.git.commit.hash") is None
        assert span.attributes.get("atla.git.commit.message") is None
        assert span.attributes.get("atla.git.commit.timestamp") is None
        assert span.attributes.get("atla.git.repo") is None
