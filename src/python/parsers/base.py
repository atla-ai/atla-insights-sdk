"""Base parser for the atla_insights package."""

from abc import ABC, abstractmethod
from typing import Any, Generator

from atla_insights.constants import SUPPORTED_LLM_FORMAT


class BaseParser(ABC):
    """Base parser for the atla_insights package."""

    name: SUPPORTED_LLM_FORMAT

    @abstractmethod
    def parse_request_body(
        self,
        request: dict[str, Any],
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the raw request body sent to a certain LLM provider.

        :param request (dict[str, Any]): The raw request body.
        :return (Generator[tuple[str, Any], None, None]): A generator of tuples that
            represent the span attribute key-value pairs of the request body.
        """
        ...

    @abstractmethod
    def parse_response_body(
        self,
        response: dict[str, Any],
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the raw response body received from a certain LLM provider.

        :param response (dict[str, Any]): The raw response body.
        :return (Generator[tuple[str, Any], None, None]): A generator of tuples that
            represent the span attribute key-value pairs of the response body.
        """
        ...
