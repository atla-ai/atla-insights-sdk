"""Base parser for the atla_insights package."""

from abc import ABC, abstractmethod
from typing import Any, Generator


class BaseParser(ABC):
    """Base parser for the atla_insights package."""

    name: str

    @abstractmethod
    def parse_request_body(
        self,
        request: dict[str, Any],
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the raw request body."""
        ...

    @abstractmethod
    def parse_response_body(
        self,
        response: dict[str, Any],
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the raw response body."""
        ...
