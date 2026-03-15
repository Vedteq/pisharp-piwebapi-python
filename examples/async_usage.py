"""Example: Async PI Web API client usage."""

import asyncio

from pisharp_piwebapi import AsyncPIWebAPIClient


async def main() -> None:
    async with AsyncPIWebAPIClient(
        base_url="https://your-server/piwebapi",
        username="your-username",
        password="your-password",
        verify_ssl=False,
    ) as client:
        # Look up a point
        point = await client.points.get_by_path(r"\\SERVER\sinusoid")
        print(f"Point: {point.name} ({point.web_id})")

        # Read current value
        value = await client.streams.get_value(point.web_id)
        print(f"Current: {value.value} at {value.timestamp}")

        # Read recorded values
        recorded = await client.streams.get_recorded(
            point.web_id,
            start_time="-1h",
            end_time="*",
        )
        print(f"Recorded: {len(recorded)} values")


if __name__ == "__main__":
    asyncio.run(main())
