"""Example: Read current and recorded values from PI."""

from pisharp_piwebapi import PIWebAPIClient

with PIWebAPIClient(
    base_url="https://your-server/piwebapi",
    username="your-username",
    password="your-password",
    verify_ssl=False,
) as client:
    # Look up a point
    point = client.points.get_by_path(r"\\SERVER\sinusoid")

    # Read the current value
    current = client.streams.get_value(point.web_id)
    print(f"Current: {current.value} at {current.timestamp}")

    # Read the last hour of recorded values
    recorded = client.streams.get_recorded(
        point.web_id,
        start_time="-1h",
        end_time="*",
    )
    print(f"\nRecorded values ({len(recorded)} points):")
    for v in recorded:
        print(f"  {v.timestamp}: {v.value}")

    # Read interpolated values (every 10 minutes for the last hour)
    interpolated = client.streams.get_interpolated(
        point.web_id,
        start_time="-1h",
        end_time="*",
        interval="10m",
    )
    print(f"\nInterpolated values ({len(interpolated)} points):")
    for v in interpolated:
        print(f"  {v.timestamp}: {v.value}")
