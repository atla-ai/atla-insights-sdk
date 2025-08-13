"""Test the tool decorator."""

from tests._otel import BaseLocalOtel


class TestTool(BaseLocalOtel):
    """Test the tool decorator."""

    def test_basic(self) -> None:
        """Test the tool decorator."""
        from atla_insights import tool

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

    def test_no_params(self) -> None:
        """Test the tool decorator without arguments."""
        from atla_insights import tool

        @tool
        def test_function() -> str:
            """Test function."""
            return "some-result"

        test_function()

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "test_function"

        assert span.attributes is not None
        assert span.attributes.get("tool.parameters") is None

    def test_mixed_params(self) -> None:
        """Test the tool decorator with mixed parameters."""
        from atla_insights import tool

        @tool
        def test_function(some_arg: str, other_arg: int) -> str:
            """Test function."""
            return "some-result"

        test_function("some-value", other_arg=1)

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "test_function"

        assert span.attributes is not None
        assert (
            span.attributes.get("tool.parameters")
            == '{"some_arg": "some-value", "other_arg": 1}'
        )

    def test_class_tool(self) -> None:
        """Test the tool decorator with a class tool."""
        from atla_insights import tool

        class TestClass:
            @tool
            def test_function(self, some_arg: str, other_arg: int) -> str:
                """Test function."""
                return "some-result"

        TestClass().test_function("some-value", other_arg=1)

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "test_function"

        assert span.attributes is not None
        assert (
            span.attributes.get("tool.parameters")
            == '{"some_arg": "some-value", "other_arg": 1}'
        )

    def test_class_method(self) -> None:
        """Test the tool decorator with a class method."""
        from atla_insights import tool

        class TestClass:
            @classmethod
            @tool
            def test_function(cls, some_arg: str, other_arg: int) -> str:
                """Test function."""
                return "some-result"

        TestClass.test_function("some-value", other_arg=1)

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "test_function"

        assert span.attributes is not None
        assert (
            span.attributes.get("tool.parameters")
            == '{"some_arg": "some-value", "other_arg": 1}'
        )

    def test_arbitrary(self) -> None:
        """Test the tool decorator with a class method."""
        from atla_insights import tool

        @tool
        def test_function(*args, **kwargs) -> str:
            """Test function."""
            return "some-result"

        test_function("some-arg", "other-arg", "third-arg", some_kwarg=1, other_kwarg=2)

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "test_function"

        assert span.attributes is not None
        assert (
            span.attributes.get("tool.parameters")
            == '{"args": ["some-arg", "other-arg", "third-arg"], "kwargs": {"some_kwarg": 1, "other_kwarg": 2}}'  # noqa: E501
        )

    def test_default_args(self) -> None:
        """Test the tool decorator with default arguments."""
        from atla_insights import tool

        @tool
        def test_function(some_arg: str, other_arg: str = "other-value") -> str:
            """Test function."""
            return "some-result"

        test_function("some-value")

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "test_function"

        assert span.attributes is not None
        assert (
            span.attributes.get("tool.parameters")
            == '{"some_arg": "some-value", "other_arg": "other-value"}'
        )

    def test_exception(self) -> None:
        """Test the tool decorator with a failing tool."""
        from atla_insights import tool

        @tool
        def test_function(some_arg: str) -> str:
            """Test function."""
            raise ValueError("some-error")

        try:
            test_function(some_arg="some-value")
        except ValueError:
            pass

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
        assert span.attributes.get("output.value") is None

        assert span.events is not None
        assert len(span.events) == 1

        [event] = span.events

        assert event.name == "exception"
        assert event.attributes is not None
        assert event.attributes.get("exception.type") == "ValueError"
        assert event.attributes.get("exception.message") == "some-error"
