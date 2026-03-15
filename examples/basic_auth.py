"""Example: Connect to PI Web API with Basic authentication."""

from pisharp_piwebapi import PIWebAPIClient

# Replace with your PI Web API server details
client = PIWebAPIClient(
    base_url="https://your-server/piwebapi",
    username="your-username",
    password="your-password",
    verify_ssl=False,  # Set True in production with proper certs
)

# Verify the connection by looking up a known point
try:
    point = client.points.get_by_path(r"\\SERVER\sinusoid")
    print(f"Connected! Found point: {point.name} (WebID: {point.web_id})")
except Exception as e:
    print(f"Connection failed: {e}")
finally:
    client.close()
