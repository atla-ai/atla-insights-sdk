"""Basic instrumentation example."""

import os
from typing import Optional

from atla_insights import configure, instrument, set_metadata
from atla_insights.sampling import MetadataSampler


@instrument("The function I want to sample")
def feature_1() -> str:
    """The function I want to sample."""
    set_metadata({"feature": "feature_1"})
    return "Hello, world!"


@instrument("The function I don't want to sample")
def feature_2() -> str:
    """The function I don't want to sample."""
    set_metadata({"feature": "feature_2"})
    return "Hello, world!"


def sampling_fn(metadata: Optional[dict[str, str]]) -> bool:
    """Decision function for metadata sampling.

    :param metadata (Optional[dict[str, str]]): The metadata to sample.
    :return (bool): Whether to sample the trace.
    """
    if metadata is None:
        return False

    return metadata.get("feature") == "feature_1"


def main() -> None:
    """Main function."""
    # Configure the client
    configure(
        token=os.environ["ATLA_INSIGHTS_TOKEN"],
        sampler=MetadataSampler(sampling_fn),
    )

    # This will be sampled
    feature_1()

    # This will not be sampled
    feature_2()


if __name__ == "__main__":
    main()
