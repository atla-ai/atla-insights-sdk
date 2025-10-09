"""Test the experiments functionality."""

import pytest

from atla_insights.context import experiment_var
from tests._otel import BaseLocalOtel


class TestExperiments(BaseLocalOtel):
    """Test experiments functionality."""

    def test_run_experiment_basic(self) -> None:
        """Test basic experiment context manager functionality."""
        from atla_insights import run_experiment

        experiment_name = "test-experiment"
        description = "Test experiment description"

        with run_experiment(experiment_name, description) as exp_run:
            # Check that we get an experiment run back
            assert exp_run is not None
            assert exp_run["name"] == experiment_name
            assert exp_run["description"] == description

            # Check context variable is set
            current_run = experiment_var.get()
            assert current_run is not None
            assert current_run["name"] == experiment_name

        # Check context variable is cleared after exiting
        current_run = experiment_var.get()
        assert current_run is None

    def test_run_experiment_without_description(self) -> None:
        """Test experiment without description."""
        from atla_insights import run_experiment

        experiment_name = "test-experiment-no-desc"

        with run_experiment(experiment_name) as exp_run:
            assert exp_run["name"] == experiment_name
            assert exp_run["description"] is None

    def test_run_experiment_without_name(self) -> None:
        """Test experiment without name."""
        from atla_insights import run_experiment

        with run_experiment() as exp_run:
            assert exp_run["name"] is not None
            assert exp_run["description"] is None

    def test_run_experiment_context_cleanup_on_exception(self) -> None:
        """Test that context is properly cleaned up even when an exception occurs."""
        from atla_insights import run_experiment

        # Ensure context is initially clean
        assert experiment_var.get() is None

        with pytest.raises(ValueError, match="test error"):
            with run_experiment("test-experiment"):
                # Context should be set inside the context manager
                assert experiment_var.get() is not None
                raise ValueError("test error")

        # Context should be cleaned up even after exception
        assert experiment_var.get() is None

    def test_run_experiment_nested_contexts(self) -> None:
        """Test nested experiment contexts."""
        from atla_insights import run_experiment

        with run_experiment("outer-experiment"):
            # Check outer context is active
            current_run = experiment_var.get()
            assert current_run is not None

            with run_experiment("inner-experiment"):
                # Check inner context is now active
                current_run = experiment_var.get()
                assert current_run is not None
                assert current_run["name"] == "inner-experiment"

            # Check outer context is restored
            current_run = experiment_var.get()
            assert current_run is not None
            assert current_run["name"] == "outer-experiment"

        # Check all contexts are cleaned up
        assert experiment_var.get() is None

    def test_run_experiment_context_isolation(self) -> None:
        """Test that experiment contexts are isolated between different calls."""
        from atla_insights import run_experiment
        from atla_insights.context import experiment_var

        def get_current_experiment_name():
            """Helper to get current experiment ID from context."""
            run = experiment_var.get()
            return run["name"] if run else None

        # Initially no context
        assert get_current_experiment_name() is None

        with run_experiment("experiment-1"):
            assert get_current_experiment_name() == "experiment-1"

        # Context should be cleared
        assert get_current_experiment_name() is None

        with run_experiment("experiment-2"):
            assert get_current_experiment_name() == "experiment-2"

        # Context should be cleared again
        assert get_current_experiment_name() is None

    def test_run_experiment_concurrent_usage(self) -> None:
        """Test that multiple experiment contexts can be used concurrently."""
        from atla_insights import run_experiment

        results = []

        for i in range(5):
            with run_experiment(f"experiment-{i}", f"Description {i}") as exp_run:
                results.append(
                    {
                        "name": exp_run["name"],
                        "description": exp_run["description"],
                    }
                )

        for i, result in enumerate(results):
            assert result["name"] == f"experiment-{i}"
            assert result["description"] == f"Description {i}"

    def test_run_experiment_span_attributes_set(self) -> None:
        """Test that experiment run attributes are set on spans."""
        from atla_insights import instrument, run_experiment
        from atla_insights.constants import EXPERIMENT_NAMESPACE

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
        assert span.attributes.get(f"{EXPERIMENT_NAMESPACE}.name") == "test-experiment"
        assert (
            span.attributes.get(f"{EXPERIMENT_NAMESPACE}.description")
            == "Test description"
        )
