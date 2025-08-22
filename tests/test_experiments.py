"""Test the experiments functionality."""

from unittest.mock import patch

import pytest

from atla_insights.context import experiment_run_var
from tests._otel import BaseLocalOtel


class TestExperiments(BaseLocalOtel):
    """Test experiments functionality."""

    def test_run_experiment_basic(self) -> None:
        """Test basic experiment context manager functionality."""
        from atla_insights import run_experiment

        experiment_id = "test-experiment"
        description = "Test experiment description"

        with run_experiment(experiment_id, description) as exp_run:
            # Check that we get an experiment run back
            assert exp_run is not None
            assert exp_run["experiment_id"] == experiment_id
            assert exp_run["description"] == description
            assert exp_run["id"] is not None
            assert len(exp_run["id"]) > 0

            # Check context variable is set
            current_run = experiment_run_var.get()
            assert current_run is not None
            assert current_run["id"] == exp_run["id"]
            assert current_run["experiment_id"] == experiment_id

        # Check context variable is cleared after exiting
        current_run = experiment_run_var.get()
        assert current_run is None

    def test_run_experiment_without_description(self) -> None:
        """Test experiment without description."""
        from atla_insights import run_experiment

        experiment_id = "test-experiment-no-desc"

        with run_experiment(experiment_id) as exp_run:
            assert exp_run["experiment_id"] == experiment_id
            assert exp_run["description"] is None
            assert exp_run["id"] is not None

    def test_run_experiment_unique_ids(self) -> None:
        """Test that each experiment run gets a unique ID."""
        from atla_insights import run_experiment

        experiment_id = "test-experiment"
        run_ids = []

        for _ in range(3):
            with run_experiment(experiment_id) as exp_run:
                run_ids.append(exp_run["id"])

        # All IDs should be unique
        assert len(run_ids) == 3
        assert len(set(run_ids)) == 3

    def test_run_experiment_with_git_info(self) -> None:
        """Test that Git information is captured correctly."""
        from atla_insights import run_experiment

        # Mock Git functions to return predictable values
        with (
            patch("atla_insights.experiments.get_git_branch", return_value="main"),
            patch("atla_insights.experiments.get_git_commit_hash", return_value="abc123"),
            patch(
                "atla_insights.experiments.get_git_commit_message",
                return_value="Test commit",
            ),
        ):
            with run_experiment("test-experiment") as exp_run:
                assert exp_run["git_branch"] == "main"
                assert exp_run["git_commit_hash"] == "abc123"
                assert exp_run["git_commit_message"] == "Test commit"

    def test_run_experiment_with_no_git_info(self) -> None:
        """Test behavior when Git information is not available."""
        from atla_insights import run_experiment

        # Mock Git functions to return None (no Git repo)
        with (
            patch("atla_insights.experiments.get_git_branch", return_value=None),
            patch("atla_insights.experiments.get_git_commit_hash", return_value=None),
            patch("atla_insights.experiments.get_git_commit_message", return_value=None),
        ):
            with run_experiment("test-experiment") as exp_run:
                assert exp_run["git_branch"] is None
                assert exp_run["git_commit_hash"] is None
                assert exp_run["git_commit_message"] is None

    def test_run_experiment_context_cleanup_on_exception(self) -> None:
        """Test that context is properly cleaned up even when an exception occurs."""
        from atla_insights import run_experiment

        # Ensure context is initially clean
        assert experiment_run_var.get() is None

        with pytest.raises(ValueError, match="test error"):
            with run_experiment("test-experiment"):
                # Context should be set inside the context manager
                assert experiment_run_var.get() is not None
                raise ValueError("test error")

        # Context should be cleaned up even after exception
        assert experiment_run_var.get() is None

    def test_run_experiment_nested_contexts(self) -> None:
        """Test nested experiment contexts."""
        from atla_insights import run_experiment

        with run_experiment("outer-experiment") as outer_run:
            outer_run_id = outer_run["id"]

            # Check outer context is active
            current_run = experiment_run_var.get()
            assert current_run is not None
            assert current_run["id"] == outer_run_id

            with run_experiment("inner-experiment") as inner_run:
                inner_run_id = inner_run["id"]

                # Check inner context is now active
                current_run = experiment_run_var.get()
                assert current_run is not None
                assert current_run["id"] == inner_run_id
                assert current_run["experiment_id"] == "inner-experiment"

            # Check outer context is restored
            current_run = experiment_run_var.get()
            assert current_run is not None
            assert current_run["id"] == outer_run_id
            assert current_run["experiment_id"] == "outer-experiment"

        # Check all contexts are cleaned up
        assert experiment_run_var.get() is None

    def test_run_experiment_cuid_generation(self) -> None:
        """Test that experiment runs use CUID for unique IDs."""
        from atla_insights import run_experiment

        with run_experiment("test-experiment") as exp_run:
            run_id = exp_run["id"]

            # CUID should be a string with specific characteristics
            assert isinstance(run_id, str)
            assert len(run_id) > 20  # CUIDs are typically > 20 characters
            # CUIDs start with 'c' in cuid2
            assert run_id[0].islower()

    def test_run_experiment_context_isolation(self) -> None:
        """Test that experiment contexts are isolated between different calls."""
        from atla_insights import run_experiment
        from atla_insights.context import experiment_run_var

        def get_current_experiment_id():
            """Helper to get current experiment ID from context."""
            run = experiment_run_var.get()
            return run["experiment_id"] if run else None

        # Initially no context
        assert get_current_experiment_id() is None

        with run_experiment("experiment-1"):
            assert get_current_experiment_id() == "experiment-1"

        # Context should be cleared
        assert get_current_experiment_id() is None

        with run_experiment("experiment-2"):
            assert get_current_experiment_id() == "experiment-2"

        # Context should be cleared again
        assert get_current_experiment_id() is None

    def test_run_experiment_context_variable_types(self) -> None:
        """Test that the experiment run context variable has correct types."""
        from atla_insights import run_experiment

        with run_experiment("test-experiment", "Test description") as exp_run:
            # Check all fields have expected types
            assert isinstance(exp_run["id"], str)
            assert isinstance(exp_run["experiment_id"], str)
            assert isinstance(exp_run["description"], str)

            # Git fields can be None or str
            assert exp_run["git_branch"] is None or isinstance(exp_run["git_branch"], str)
            assert exp_run["git_commit_hash"] is None or isinstance(
                exp_run["git_commit_hash"], str
            )
            assert exp_run["git_commit_message"] is None or isinstance(
                exp_run["git_commit_message"], str
            )

    def test_run_experiment_concurrent_usage(self) -> None:
        """Test that multiple experiment contexts can be used concurrently."""
        from atla_insights import run_experiment

        results = []

        for i in range(5):
            with run_experiment(f"experiment-{i}", f"Description {i}") as exp_run:
                results.append(
                    {
                        "id": exp_run["id"],
                        "experiment_id": exp_run["experiment_id"],
                        "description": exp_run["description"],
                    }
                )

        # All experiments should have unique run IDs but correct experiment IDs
        run_ids = [r["id"] for r in results]
        assert len(set(run_ids)) == 5  # All unique

        for i, result in enumerate(results):
            assert result["experiment_id"] == f"experiment-{i}"
            assert result["description"] == f"Description {i}"

    def test_run_experiment_environment_warning_when_not_dev(self) -> None:
        """Test that warning is raised when environment is not 'dev' during experiment."""
        import warnings

        from atla_insights import instrument, run_experiment

        # Test that warning is issued when environment is 'unit-testing' (not 'dev')
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            with run_experiment("test-experiment") as exp_run:
                assert exp_run is not None

                # Create a span within the experiment context to trigger warning
                @instrument("test_span")
                def test_function():
                    return "test"

                test_function()

            # Check that a warning was issued (since unit-testing != dev)
            assert len(warning_list) >= 1
            warning_msgs = [str(w.message) for w in warning_list]
            assert any(
                "Setting environment to 'dev' during experiment run" in msg
                for msg in warning_msgs
            )

    def test_run_experiment_span_attributes_set(self) -> None:
        """Test that experiment run attributes are set on spans."""
        from atla_insights import instrument, run_experiment
        from atla_insights.constants import EXPERIMENT_RUN_NAMESPACE

        with run_experiment("test-experiment", "Test description") as exp_run:
            assert exp_run is not None

            # Create a span within the experiment context
            @instrument("test_span")
            def test_function():
                return "test"

            test_function()

        # Check the span attributes
        spans = self.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]

        assert span.attributes is not None

        # Check experiment run attributes were set
        assert span.attributes.get(f"{EXPERIMENT_RUN_NAMESPACE}.id") == exp_run["id"]
        assert (
            span.attributes.get(f"{EXPERIMENT_RUN_NAMESPACE}.experiment_id")
            == "test-experiment"
        )
        assert (
            span.attributes.get(f"{EXPERIMENT_RUN_NAMESPACE}.description")
            == "Test description"
        )
