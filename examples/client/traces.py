"""Example of interacting with traces using the data API client."""

import os
from datetime import datetime, timezone

from atla_insights import Client
from atla_insights.client import TraceDetailResponse, TraceListResponse


def main() -> None:
    """Main function."""
    # Configure the API client.
    # Note: For this example we use Atla's Narcissus AI Agent data.
    # Check out https://app.atla-ai.com/app/narcissus to see more!
    client = Client(api_key=os.environ["ATLA_INSIGHTS_TOKEN"])
    response: TraceListResponse | TraceDetailResponse

    # List all traces
    response = client.list_traces()
    print(
        f"Found {response.total} traces, with the first trace being "
        f"{response.traces[0].id}."
    )
    # >> Found 60 traces, with the first trace being 01b035bd0a0b096e066d49e3ef5c49e7.

    # List traces with pagination
    response = client.list_traces(page=2, page_size=10)
    print(
        f"Found {len(response.traces)} out of {response.total} traces, with the first "
        f"trace being {response.traces[0].id}."
    )
    # >> Found 10 out of 60 traces, with the first trace being 0f15af9f4970298af7fde8a77b04e9e6. # noqa: E501

    # List traces with date range (note the use of timezone.utc)
    response = client.list_traces(
        start_timestamp=datetime(2025, 8, 10, tzinfo=timezone.utc),
        end_timestamp=datetime(2025, 8, 11, tzinfo=timezone.utc),
    )
    print(f"Found {response.total} traces.")
    # >> Found 6 traces.

    # List traces with metadata filter
    response = client.list_traces(metadata_filter=[{"key": "version", "value": "1"}])
    print(f"Found {response.total} traces.")
    # >> Found 3 traces.

    # Get a trace by id and look at its data.
    response = client.get_trace(trace_id="a278287f58ea99c2d585ad73b0913fd5")
    print(f"Found trace {response.trace.id}.")
    print(f"Found {len(response.trace.spans)} spans in trace.")  # type: ignore[arg-type]
    for span in response.trace.spans:  # type: ignore[union-attr]
        if span.annotations:
            print(
                f"Span {span.id} has an annotation: "
                f"failure_mode={span.annotations[0].failure_mode}, "
                f"critique={span.annotations[0].atla_critique}"
            )
            print("Span messages:")
            for event in span.otel_events:
                print(event)
    # >> Found trace a278287f58ea99c2d585ad73b0913fd5.
    # >> Found 8 spans in trace.
    # >> Span 40aed1fdd330bc06 has an annotation: failure_mode=user_communication_step_error, critique=The response presents an incorrect set of “competitors” and comparisons that do not match the search output or real market offerings. # noqa: E501
    # >> Span messages:
    # >> ...


if __name__ == "__main__":
    main()
