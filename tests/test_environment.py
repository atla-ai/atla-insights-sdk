"""Test the environment functionality."""

import os
from unittest.mock import patch

import pytest

from tests._otel import BaseLocalOtel


class TestEnvironment(BaseLocalOtel):
    """Test the environment functionality."""

    def test_validate_environment_valid_values(self) -> None:
        """Test that validate_environment accepts valid values."""
        from atla_insights.environment import validate_environment

        assert validate_environment("dev") == "dev"
        assert validate_environment("prod") == "prod"

    def test_validate_environment_invalid_values(self) -> None:
        """Test that validate_environment rejects invalid values."""
        from atla_insights.environment import validate_environment

        with pytest.raises(ValueError, match="Invalid environment 'staging'"):
            validate_environment("staging")

        with pytest.raises(ValueError, match="Invalid environment 'test'"):
            validate_environment("test")

        with pytest.raises(ValueError, match="Invalid environment 'production'"):
            validate_environment("production")

    def test_get_environment_with_parameter(self) -> None:
        """Test get_environment with explicit parameter."""
        from atla_insights.environment import resolve_environment

        assert resolve_environment("dev") == "dev"
        assert resolve_environment("prod") == "prod"

    def test_get_environment_with_parameter_invalid(self) -> None:
        """Test get_environment with invalid parameter."""
        from atla_insights.environment import resolve_environment

        with pytest.raises(ValueError):
            resolve_environment("invalid")  # type: ignore[arg-type]

    @patch.dict(os.environ, {}, clear=True)
    def test_get_environment_no_env_var_defaults_to_prod(self) -> None:
        """Test get_environment defaults to prod when no env var is set."""
        from atla_insights.environment import resolve_environment

        assert resolve_environment() == "prod"

    @patch.dict(os.environ, {"ATLA_INSIGHTS_ENVIRONMENT": "dev"})
    def test_get_environment_from_env_var(self) -> None:
        """Test get_environment reads from environment variable."""
        from atla_insights.environment import resolve_environment

        assert resolve_environment() == "dev"

    @patch.dict(os.environ, {"ATLA_INSIGHTS_ENVIRONMENT": "prod"})
    def test_get_environment_from_env_var_prod(self) -> None:
        """Test get_environment reads prod from environment variable."""
        from atla_insights.environment import resolve_environment

        assert resolve_environment() == "prod"

    @patch.dict(os.environ, {"ATLA_INSIGHTS_ENVIRONMENT": "invalid"})
    def test_get_environment_invalid_env_var(self) -> None:
        """Test get_environment raises error for invalid env var."""
        from atla_insights.environment import resolve_environment

        with pytest.raises(ValueError, match="Invalid environment 'invalid'"):
            resolve_environment()

    @patch.dict(os.environ, {"ATLA_INSIGHTS_ENVIRONMENT": "dev"})
    def test_get_environment_parameter_overrides_env_var(self) -> None:
        """Test that parameter takes precedence over environment variable."""
        from atla_insights.environment import resolve_environment

        # Environment variable is "dev" but parameter is "prod"
        assert resolve_environment("prod") == "prod"

    def test_span_processor_environment_attribute(self) -> None:
        """Test that AtlaRootSpanProcessor adds environment attribute to spans."""
        from unittest.mock import Mock

        from opentelemetry.sdk.trace import Span

        from atla_insights.constants import ENVIRONMENT_MARK
        from atla_insights.span_processors import AtlaRootSpanProcessor

        # Test with dev environment
        processor_dev = AtlaRootSpanProcessor(debug=False, environment="dev")

        # Create a mock span
        mock_span = Mock(spec=Span)
        mock_span.parent = None
        mock_span.set_attribute = Mock()

        # Call on_start
        processor_dev.on_start(mock_span)

        # Verify environment attribute was set
        mock_span.set_attribute.assert_any_call(ENVIRONMENT_MARK, "dev")

        # Test with prod environment
        processor_prod = AtlaRootSpanProcessor(debug=False, environment="prod")
        mock_span_prod = Mock(spec=Span)
        mock_span_prod.parent = None
        mock_span_prod.set_attribute = Mock()

        processor_prod.on_start(mock_span_prod)
        mock_span_prod.set_attribute.assert_any_call(ENVIRONMENT_MARK, "prod")

    def test_configure_function_passes_environment_parameter(self) -> None:
        """Test that configure function properly passes environment to span processors."""
        from unittest.mock import patch

        from atla_insights.main import AtlaInsights

        atla_instance = AtlaInsights()

        with patch(
            "atla_insights.main.add_span_processors_to_tracer_provider"
        ) as mock_add_processors:
            atla_instance.configure(token="dummy", environment="dev")

            # Verify add_span_processors_to_tracer_provider was called with env="dev"
            mock_add_processors.assert_called_once()
            call_args = mock_add_processors.call_args
            assert call_args.kwargs["environment"] == "dev"

    @patch.dict(os.environ, {"ATLA_INSIGHTS_ENVIRONMENT": "dev"})
    def test_configure_function_uses_environment_variable(self) -> None:
        """Test configure function uses env variable when no parameter provided."""
        from unittest.mock import patch

        from atla_insights.main import AtlaInsights

        atla_instance = AtlaInsights()

        with patch(
            "atla_insights.main.add_span_processors_to_tracer_provider"
        ) as mock_add_processors:
            atla_instance.configure(token="dummy")  # No environment parameter

            # Verify environment variable was picked up
            call_args = mock_add_processors.call_args
            assert call_args.kwargs["environment"] == "dev"

    @patch.dict(os.environ, {"ATLA_INSIGHTS_ENVIRONMENT": "dev"})
    def test_configure_parameter_overrides_environment_variable(self) -> None:
        """Test that configure parameter overrides environment variable."""
        from unittest.mock import patch

        from atla_insights.main import AtlaInsights

        atla_instance = AtlaInsights()

        with patch(
            "atla_insights.main.add_span_processors_to_tracer_provider"
        ) as mock_add_processors:
            # Environment variable is "dev" but parameter is "prod"
            atla_instance.configure(token="dummy", environment="prod")

            # Verify parameter took precedence over environment variable
            call_args = mock_add_processors.call_args
            assert call_args.kwargs["environment"] == "prod"

    def test_configure_with_invalid_environment_parameter(self) -> None:
        """Test that configure raises error for invalid environment parameter."""
        from atla_insights.main import AtlaInsights

        atla_instance = AtlaInsights()

        with pytest.raises(ValueError, match="Invalid environment 'invalid'"):
            atla_instance.configure(token="dummy", environment="invalid")  # type: ignore[arg-type]
