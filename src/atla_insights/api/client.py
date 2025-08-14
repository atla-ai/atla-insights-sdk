"""Main Atla Insights API client with functional interface."""

import logging
import os
from datetime import datetime
from typing import Any, Iterator, List, Optional
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from atla_insights.api.types import TraceView

logger = logging.getLogger(__name__)

ATLA_BASE_URL = "https://app.atla-ai.com/api/sdk/v1"


class AtlaInsightsClient:
    """Main client for Atla Insights API.

    Example:
        ```python
        from atla_insights.api import AtlaInsightsClient

        # Initialize client
        client = AtlaInsightsClient()

        # Functional API
        traces = client.list_traces(page_size=10)
        trace = client.fetch_trace("trace-id")
        batch = client.fetch_traces(["id1", "id2", "id3"])
        ```
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the Atla Insights client.

        Args:
            base_url: API base URL (defaults to ATLA_BASE_URL env var or Atla base URL)
            api_key: API key for authentication (defaults to ATLA_INSIGHTS_TOKEN env var)
            timeout: Request timeout in seconds

        Raises:
            ValueError: If API key is not provided and not found in env vars
        """
        # Resolve base URL
        self._base_url = self._resolve_base_url(base_url)

        # Resolve API key
        self._api_key = self._resolve_api_key(api_key)

        # Initialize HTTP client
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=timeout,
        )

    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()

    def _resolve_base_url(self, base_url: Optional[str]) -> str:
        """Resolve the API base URL.

        Args:
            base_url: Explicitly provided base URL

        Returns:
            Resolved base URL
        """
        if base_url:
            # Ensure the URL has a scheme
            parsed = urlparse(base_url)
            if not parsed.scheme or parsed.scheme not in ("http", "https"):
                base_url = f"https://{base_url}"
            return base_url.rstrip("/")

        # Try environment variables
        env_url = os.getenv("ATLA_BASE_URL")
        if env_url:
            parsed = urlparse(env_url)
            if not parsed.scheme or parsed.scheme not in ("http", "https"):
                env_url = f"https://{env_url}"
            return env_url.rstrip("/")

        # Default to production
        return ATLA_BASE_URL

    def _resolve_api_key(self, api_key: Optional[str]) -> str:
        """Resolve the API key for authentication.

        Args:
            api_key: Explicitly provided API key

        Returns:
            Resolved API key

        Raises:
            ValueError: If no API key can be resolved
        """
        if api_key:
            return api_key

        # Try environment variable
        env_key = os.getenv("ATLA_INSIGHTS_TOKEN")
        if env_key:
            return env_key

        raise ValueError(
            "API key is required. Provide it as a parameter or set the "
            "ATLA_INSIGHTS_TOKEN environment variable."
        )

    def auth_check(self) -> bool:
        """Check if the client is properly authenticated.

        Returns:
            True if authentication is valid, False otherwise
        """
        try:
            # Try to make a simple API call to verify auth
            self.list_traces(page_size=1)
            return True
        except Exception as e:
            logger.warning(f"Auth check failed: {e}")
            return False

    def list_traces(
        self,
        start_timestamp: Optional[datetime] = None,
        end_timestamp: Optional[datetime] = None,
        page: int = 0,
        page_size: int = 50,
        include: Optional[List[str]] = None,
    ) -> List[TraceView]:
        """List traces with optional filtering.

        Args:
            start_timestamp: Filter traces after this timestamp
            end_timestamp: Filter traces before this timestamp
            page: Page number (0-indexed)
            page_size: Number of traces per page (max 100)
            include: Array of what to include - 'spans', 'annotations', 'customMetrics'

        Returns:
            List of TraceView objects

        Raises:
            httpx.HTTPError: If the API request fails
            ValidationError: If the response doesn't match expected schema
        """
        params: dict[str, Any] = {
            "page": str(page),
            "pageSize": str(min(page_size, 100)),
        }

        if start_timestamp:
            params["startTimestamp"] = start_timestamp.isoformat()
        if end_timestamp:
            params["endTimestamp"] = end_timestamp.isoformat()
        if include:
            params["include"] = include

        url = f"{self._base_url}/traces"

        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return [TraceView.model_validate(trace) for trace in data["traces"]]

        except httpx.HTTPError as e:
            logger.error(f"HTTP error listing traces: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Invalid response format: {e}")
            raise

    def fetch_trace(
        self, trace_id: str, include: Optional[List[str]] = None
    ) -> Optional[TraceView]:
        """Fetch a single trace by ID.

        Args:
            trace_id: The trace ID to retrieve
            include: Array of what to include - 'spans', 'annotations', 'customMetrics'

        Returns:
            TraceView if found, None if not found

        Raises:
            httpx.HTTPError: If the API request fails (except 404)
            ValidationError: If the response doesn't match expected schema
        """
        params = {}
        if include:
            params["include"] = include

        url = f"{self._base_url}/traces/{trace_id}"

        response = None
        try:
            response = self._client.get(url, params=params)

            if response.status_code == 404:
                return None

            response.raise_for_status()

            data = response.json()
            return TraceView.model_validate(data["trace"])

        except httpx.HTTPError as e:
            if response is not None and response.status_code == 404:
                return None
            logger.error(f"HTTP error fetching trace {trace_id}: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Invalid response format for trace {trace_id}: {e}")
            raise

    def fetch_traces(
        self, trace_ids: List[str], include: Optional[List[str]] = None
    ) -> List[TraceView]:
        """Fetch multiple traces by their IDs.

        Args:
            trace_ids: List of trace IDs to retrieve
            include: Array of what to include - 'spans', 'annotations', 'customMetrics'

        Returns:
            List of found TraceView objects (may be shorter than input list)

        Raises:
            httpx.HTTPError: If the API request fails
            ValidationError: If the response doesn't match expected schema
        """
        if not trace_ids:
            return []

        params = {"ids": trace_ids}
        if include:
            params["include"] = include

        url = f"{self._base_url}/traces/ids"

        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return [TraceView.model_validate(trace) for trace in data["traces"]]

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching traces: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Invalid response format: {e}")
            raise

    def iter_all_traces(
        self,
        start_timestamp: Optional[datetime] = None,
        end_timestamp: Optional[datetime] = None,
        page_size: int = 50,
        include: Optional[List[str]] = None,
    ) -> Iterator[TraceView]:
        """Iterator that automatically handles pagination to fetch all traces.

        Args:
            start_timestamp: Filter traces after this timestamp
            end_timestamp: Filter traces before this timestamp
            page_size: Number of traces per page (max 100)
            include: Array of what to include - 'spans', 'annotations', 'customMetrics'

        Yields:
            TraceView objects one by one

        Raises:
            httpx.HTTPError: If any API request fails
            ValidationError: If any response doesn't match expected schema
        """
        page = 0

        while True:
            traces = self.list_traces(
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                page=page,
                page_size=page_size,
                include=include,
            )

            # If no traces returned, we're done
            if not traces:
                break

            # Yield each trace
            for trace in traces:
                yield trace

            # If we got fewer traces than requested, this was the last page
            if len(traces) < page_size:
                break

            page += 1
