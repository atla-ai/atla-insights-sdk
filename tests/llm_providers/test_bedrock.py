"""Test Bedrock instrumentation."""

import json

from tests._otel import BaseLocalOtel


class TestBedrockInstrumentation(BaseLocalOtel):
    """Test the Bedrock instrumentation."""

    def test_basic(self, bedrock_client_factory) -> None:
        """Test basic Bedrock instrumentation."""
        from atla_insights import instrument_bedrock
        from tests.conftest import _MOCK_RESPONSES

        model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        response_content = _MOCK_RESPONSES["bedrock_anthropic_invoke_model"]

        with instrument_bedrock():
            # Factory now handles both client creation and response setup
            client, _ = bedrock_client_factory(model_id, response_content)
            body = json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Hello"}],
                }
            )
            client.invoke_model(body=body, modelId=model_id)

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None

        assert span.name == "bedrock.invoke_model"

        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert span.attributes.get("llm.input_messages.0.message.content") == "Hello"

        assert span.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            span.attributes.get("llm.output_messages.0.message.content")
            == "Hello! How are you doing today? Is there anything I can help you with?"
        )

    def test_ctx(self, bedrock_client_factory) -> None:
        """Test context manager behavior."""
        from atla_insights import instrument_bedrock
        from tests.conftest import _MOCK_RESPONSES

        model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        response_content = _MOCK_RESPONSES["bedrock_anthropic_invoke_model"]

        with instrument_bedrock():
            client, _ = bedrock_client_factory(model_id, response_content)
            client.invoke_model(
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 100,
                        "messages": [{"role": "user", "content": "Hello"}],
                    }
                ),
                modelId=model_id,
            )

        client, _ = bedrock_client_factory(model_id, response_content)
        client.invoke_model(
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Hello"}],
                }
            ),
            modelId=model_id,
        )

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1
