"""Test the metadata."""

import asyncio
import json
from typing import cast

import pytest

from tests._otel import BaseLocalOtel


class TestMetadata(BaseLocalOtel):
    """Test the metadata."""

    def test_metadata(self) -> None:
        """Test that run metadata is added to the root span correctly."""
        from atla_insights import instrument
        from atla_insights.constants import METADATA_MARK

        @instrument()
        def test_function():
            return "test result"

        test_function()
        spans = self.get_finished_spans()

        assert len(spans) == 1
        [span] = spans

        assert span.attributes is not None
        assert span.attributes.get(METADATA_MARK) is not None

        metadata = json.loads(cast(str, span.attributes.get(METADATA_MARK)))
        assert metadata == {"environment": "unit-testing"}

    def test_get_set_metadata(self) -> None:
        """Test that the metadata is set and retrieved correctly."""
        from atla_insights import get_metadata, instrument, set_metadata
        from atla_insights.constants import METADATA_MARK

        @instrument()
        def test_function():
            set_metadata({"some_key": "some-value"})
            assert get_metadata() == {"some_key": "some-value"}

            set_metadata({"environment": "unit-testing"})
            assert get_metadata() == {"environment": "unit-testing"}

            return "test result"

        test_function()
        spans = self.get_finished_spans()

        assert len(spans) == 1
        [span] = spans

        assert span.attributes is not None
        assert span.attributes.get(METADATA_MARK) is not None

    def test_metadata_api_context_simulation(self) -> None:
        """Test metadata functionality in a server context."""
        from atla_insights import get_metadata, instrument, set_metadata

        @instrument("mock_api_request")
        def simulate_api_request(user_id: str, session_id: str) -> bool:
            """Simulate a API request handler."""
            # Set request metadata
            request_metadata = {
                "user_id": user_id,
                "session_id": session_id,
                "endpoint": "test_api",
            }
            set_metadata(request_metadata)

            # Verify metadata was set correctly
            current = get_metadata()
            assert current == request_metadata

            # Update metadata during processing
            updated = request_metadata.copy()
            updated["status"] = "processed"
            set_metadata(updated)

            # Verify final metadata
            final = get_metadata()
            return final == updated

        # Test multiple "requests" in sequence
        assert simulate_api_request("user1", "session1")
        assert simulate_api_request("user2", "session2")

    @pytest.mark.asyncio
    async def test_metadata_api_context_simulation_async(self) -> None:
        """Test metadata functionality in async server context."""
        from atla_insights import get_metadata, instrument, set_metadata

        @instrument("mock_async_api_request")
        async def simulate_async_api_request(user_id: str, session_id: str) -> bool:
            """Simulate an async API request handler."""
            # Set request metadata
            request_metadata = {
                "user_id": user_id,
                "session_id": session_id,
                "endpoint": "test_async_api",
            }
            set_metadata(request_metadata)

            # Simulate some async operation
            await asyncio.sleep(0.01)

            # Verify metadata was preserved across await
            current = get_metadata()
            assert current == request_metadata

            # Update metadata during processing
            updated = request_metadata.copy()
            updated["status"] = "processed"
            set_metadata(updated)

            # Another async operation
            await asyncio.sleep(0.01)

            # Verify final metadata after async operations
            final = get_metadata()
            return final == updated

        # Test multiple async "requests"
        assert await simulate_async_api_request("user1", "session1")
        assert await simulate_async_api_request("user2", "session2")

    @pytest.mark.parametrize(
        "metadata, is_valid",
        [
            pytest.param({"key": "value"}, True, id="valid"),
            pytest.param({"key": "value" * 100}, False, id="long values"),
            pytest.param({"key" * 100: "value"}, False, id="long keys"),
            pytest.param({f"{i}": f"{i}" for i in range(100)}, False, id="too much data"),
        ],
    )
    def test_validate_metadata(self, metadata: dict[str, str], is_valid: bool) -> None:
        """Test validate_metadata function."""
        from atla_insights.metadata import validate_metadata

        validated_metadata = validate_metadata(metadata)

        if is_valid:
            assert validated_metadata == metadata
        else:
            assert validated_metadata != metadata

            # If the metadata is invalid, the truncated metadata should be valid.
            revalidated_metadata = validate_metadata(validated_metadata)
            assert revalidated_metadata == validated_metadata
