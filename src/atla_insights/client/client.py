"""Client for the Atla Insights data API."""

import json
from datetime import datetime
from typing import Dict, Iterator, List, Optional

from atla_insights.client._generated_client import ApiClient, Configuration, SDKApi
from atla_insights.client.types import (
    DetailedTraceListResponse,
    TraceDetailResponse,
    TraceListResponse,
)

DEFAULT_HOST = "https://app.atla-ai.com"


class Client:
    """Client for the Atla Insights data API.

    Usage:
    ```python
    from atla_insights.client import Client

    client = Client(api_key="your_api_key")
    traces = client.list_traces(page_size=10)
    trace = client.get_trace("trace_id_123")
    health = client.health_check()
    ```
    """

    def __init__(self, api_key: str, host: str = DEFAULT_HOST):
        """Initialize client with API key authentication.

        Args:
            api_key: API key for authentication
            host: Base URL for the API
        """
        self.api_key = api_key
        self.host = host

        # Setup generated client
        config = Configuration()
        config.host = host

        api_client = ApiClient(
            config, header_name="Authorization", header_value=f"Bearer {api_key}"
        )

        self._sdk = SDKApi(api_client)

    def list_traces(
        self,
        start_timestamp: Optional[datetime] = None,
        end_timestamp: Optional[datetime] = None,
        metadata_filter: Optional[List[Dict[str, str]]] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> TraceListResponse:
        """List traces with pagination and filtering.

        Args:
            start_timestamp: Filter traces from this timestamp
            end_timestamp: Filter traces until this timestamp
            metadata_filter: Filter traces by metadata
            page: Page number for pagination
            page_size: Number of traces per page

        Returns:
            Response with traces, total count, and pagination info
        """
        # Pre-serialize metadata filter.
        if metadata_filter is not None:
            metadata_filter_str = json.dumps(metadata_filter)
            return self._sdk.list_traces(
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                metadata_filter=metadata_filter_str,
                page=page,
                page_size=page_size,
            )

        return self._sdk.list_traces(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            page=page,
            page_size=page_size,
        )

    def get_trace(self, trace_id: str) -> TraceDetailResponse:
        """Get a single trace by ID.

        Args:
            trace_id: Unique identifier for the trace
        Returns:
            Response containing complete trace data
        """
        return self._sdk.get_trace_by_id(
            trace_id,
            # Automatically include all data.
            include=[
                "spans",
                "annotations",
                "customMetrics",
            ],
        )

    def get_traces(self, trace_ids: List[str]) -> DetailedTraceListResponse:
        """Get multiple traces by their IDs.

        Args:
            trace_ids: List of trace IDs to retrieve
            include: Additional data to include in response. Options are: "spans",
                "annotations", and "custom_metrics". If "annotations" is included,
                "spans" will be included automatically.

        Returns:
            Response containing complete trace data
        """
        return self._sdk.get_traces_by_ids(
            ids=trace_ids,
            # Automatically include all data.
            include=[
                "spans",
                "annotations",
                "customMetrics",
            ],
        )

    def get_audio(self, audio_id: str) -> bytearray:
        """Get audio file by ID.

        ```python
        from atla_insights.client import Client

        client = Client(api_key="your_api_key_here")

        # Retrieves audio bytes
        result = client.get_audio("my_audio_id")

        # Saves audio to MP3 file
        with open("my_file.mp3", "wb") as f:
            f.write(result)
        ```

        Args:
            audio_id: ID of audio file to retrieve.

        Returns:
            Response containing the audio bytes.
        """
        return self._sdk.get_audio_by_id(audio_id)

    def get_audio_stream(self, audio_id: str, chunk_size: int = 8192) -> Iterator[bytes]:
        """Get audio file by ID as a streaming iterator.

        ```python
        from atla_insights.client import Client

        client = Client(api_key="your_api_key_here")

        # Initialize audio bytes stream
        result = client.get_audio_stream("my_audio_id")

        # Consume stream and save audio to MP3 file
        with open("my_file.mp3", "wb") as f:
            for chunk in result:
                f.write(chunk)
        ```

        Args:
            audio_id: ID of audio file to retrieve.
            chunk_size: Size of chunks to stream (default: 8k bytes).

        Returns:
            Iterator yielding audio data in chunks.
        """
        response = self._sdk.get_audio_by_id_without_preload_content(audio_id)
        try:
            for chunk in response.stream(amt=chunk_size):
                yield chunk
        finally:
            response.release_conn()
