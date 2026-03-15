"""Example: Write values to PI."""

from pisharp_piwebapi import PIWebAPIClient

with PIWebAPIClient(
    base_url="https://your-server/piwebapi",
    username="your-username",
    password="your-password",
    verify_ssl=False,
) as client:
    point = client.points.get_by_path(r"\\SERVER\my-tag")

    # Write a single value (timestamp defaults to now)
    client.streams.update_value(point.web_id, value=42.0)
    print("Wrote single value: 42.0")

    # Write a single value with a specific timestamp
    client.streams.update_value(
        point.web_id,
        value=99.5,
        timestamp="2024-01-15T10:30:00Z",
    )
    print("Wrote value with timestamp: 99.5 at 2024-01-15T10:30:00Z")

    # Write multiple values at once
    client.streams.update_values(
        point.web_id,
        values=[
            {"Value": 10.0, "Timestamp": "2024-01-15T10:00:00Z"},
            {"Value": 20.0, "Timestamp": "2024-01-15T10:05:00Z"},
            {"Value": 30.0, "Timestamp": "2024-01-15T10:10:00Z"},
        ],
    )
    print("Wrote 3 bulk values")
