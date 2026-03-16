"""Work with PI AF Event Frames — search, view, and acknowledge."""

from pisharp_piwebapi import PIWebAPIClient

BASE_URL = "https://your-server/piwebapi"


def main() -> None:
    with PIWebAPIClient(
        base_url=BASE_URL,
        username="your-user",
        password="your-password",
        verify_ssl=False,
    ) as client:
        # Search for event frames in the last 7 days
        events = client.eventframes.search("*", start_time="-7d", end_time="*")
        print(f"Found {len(events)} event frames in the last 7 days\n")

        for ef in events:
            print(f"  {ef.name}")
            print(f"    Severity:     {ef.severity}")
            print(f"    Start:        {ef.start_time}")
            print(f"    End:          {ef.end_time}")
            print(f"    Acknowledged: {ef.is_acknowledged}")
            print()

        # Get event frames for a specific element
        element = client.elements.get_by_path(r"\\AF\Production\Pump-001")
        element_events = client.eventframes.get_by_element(
            element.web_id,
            start_time="-30d",
        )
        print(f"\nEvent frames for {element.name}: {len(element_events)}")

        # Acknowledge unacknowledged events
        for ef in element_events:
            if ef.can_be_acknowledged and not ef.is_acknowledged:
                client.eventframes.acknowledge(ef.web_id)
                print(f"  Acknowledged: {ef.name}")

        # Create a new event frame
        client.eventframes.create(
            element.web_id,
            name="Manual Inspection",
            start_time="*",
            end_time="*+1h",
            description="Scheduled manual inspection",
            severity="Information",
        )
        print("\nCreated 'Manual Inspection' event frame")


if __name__ == "__main__":
    main()
