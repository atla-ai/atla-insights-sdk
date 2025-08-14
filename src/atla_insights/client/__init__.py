"""Client for the Atla Insights data API."""

from datetime import datetime
from typing import List, Optional

from atla_insights.client._generated_client import (
    ApiClient,
    Configuration,
    GetTraceById200Response,
    GetTracesByIds200Response,
    ListTraces200Response,
    SDKApi,
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
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> ListTraces200Response:
        """List traces with pagination and filtering.

        Args:
            start_timestamp: Filter traces from this timestamp
            end_timestamp: Filter traces until this timestamp
            page: Page number for pagination
            page_size: Number of traces per page

        Returns:
            Response with traces, total count, and pagination info
        """
        return self._sdk.list_traces(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            page=page,
            page_size=page_size,
        )

    def get_trace(
        self, trace_id: str, include: Optional[List[str]] = None
    ) -> GetTraceById200Response:
        """Get a single trace by ID.

        Args:
            trace_id: Unique identifier for the trace
            include: Additional data to include in response

        Returns:
            Complete trace data including spans, annotations, and metrics
        """
        return self._sdk.get_trace_by_id(trace_id, include=include)

    def get_traces(
        self, trace_ids: List[str], include: Optional[List[str]] = None
    ) -> GetTracesByIds200Response:
        """Get multiple traces by their IDs.

        Args:
            trace_ids: List of trace IDs to retrieve
            include: Additional data to include in response

        Returns:
            Response containing all found traces
        """
        return self._sdk.get_traces_by_ids(ids=trace_ids, include=include)
