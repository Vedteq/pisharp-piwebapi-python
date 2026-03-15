"""Example: Execute batch requests to PI Web API."""

from pisharp_piwebapi import PIWebAPIClient

with PIWebAPIClient(
    base_url="https://your-server/piwebapi",
    username="your-username",
    password="your-password",
    verify_ssl=False,
) as client:
    # Execute multiple requests in a single HTTP call
    results = client.execute_batch({
        "1": {
            "Method": "GET",
            "Resource": "https://your-server/piwebapi/points?path=\\\\SERVER\\sinusoid",
        },
        "2": {
            "Method": "GET",
            "Resource": "https://your-server/piwebapi/points?path=\\\\SERVER\\cdt158",
        },
    })

    for request_id, response in results.items():
        status = response.get("Status", 0)
        content = response.get("Content", {})
        name = content.get("Name", "unknown")
        print(f"Request {request_id}: status={status}, point={name}")
