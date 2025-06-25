"""Test the tool decorator."""

from tests._otel import BaseLocalOtel


class TestTool(BaseLocalOtel):
    """Test the tool decorator."""

    def test_tool(self) -> None:
        """Test the tool decorator."""
        from src.atla_insights import tool

        @tool
        def test_function(some_arg: str) -> str:
            """Test function."""
            return "some-result"

        test_function(some_arg="some-value")

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "test_function"

        assert span.attributes is not None

        assert span.attributes.get("openinference.span.kind") == "TOOL"

        assert span.attributes.get("tool.name") == "test_function"
        assert span.attributes.get("tool.description") == "Test function."
        assert span.attributes.get("tool.parameters") == '{"some_arg": "some-value"}'

        assert span.attributes.get("input.value") == '{"some_arg": "some-value"}'
        assert span.attributes.get("output.value") == "some-result"
