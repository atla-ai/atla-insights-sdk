"""WebSocket-related mocks."""


class _MockWebSocket:
    """Mock websocket-like object for testing synchronous flows."""

    def __init__(self, message: str) -> None:
        self.message = message

    def send(self, *_) -> None:
        pass

    def recv(self, **_) -> str:
        return self.message

    def close(self) -> None:
        pass


class _MockAsyncWebSocket:
    """Mock websocket-like object for testing asynchronous flows."""

    def __init__(self, message: str) -> None:
        self.message = message

    async def send(self, *_) -> None:
        pass

    async def recv(self) -> str:
        return self.message

    async def close(self) -> None:
        pass


class MockWebSocketConnection:
    """Mock websocket-like connection for testing synchronous flows."""

    def __init__(self, message: str) -> None:
        self._ws = _MockWebSocket(message)

    def __enter__(self) -> _MockWebSocket:
        return self._ws

    def __exit__(self, *_) -> None:
        self._ws.close()


class MockAsyncWebSocketConnection:
    """Mock websocket-like connection for testing asynchronous flows."""

    def __init__(self, message: str) -> None:
        self._ws = _MockAsyncWebSocket(message)

    async def __aenter__(self) -> _MockAsyncWebSocket:
        return self._ws

    async def __aexit__(self, *_) -> None:
        await self._ws.close()
