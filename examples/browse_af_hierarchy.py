"""Browse the PI AF hierarchy — servers, databases, elements, and attributes."""

from pisharp_piwebapi import PIWebAPIClient

BASE_URL = "https://your-server/piwebapi"


def main() -> None:
    with PIWebAPIClient(
        base_url=BASE_URL,
        username="your-user",
        password="your-password",
        verify_ssl=False,
    ) as client:
        # List all AF servers
        servers = client.assetservers.list()
        for svr in servers:
            print(f"AF Server: {svr.name} (connected={svr.is_connected})")

            # List databases on each server
            databases = client.assetservers.get_databases(svr.web_id)
            for db in databases:
                print(f"  Database: {db.name}")

                # Get top-level elements
                elements = client.databases.get_elements(db.web_id, max_count=10)
                for elem in elements:
                    print(f"    Element: {elem.name} (template={elem.template_name})")

                    # Get attributes
                    attrs = client.elements.get_attributes(elem.web_id, max_count=5)
                    for attr in attrs:
                        print(f"      Attribute: {attr.name} ({attr.type})")

                    # Get child elements
                    if elem.has_children:
                        children = client.elements.get_children(elem.web_id, max_count=5)
                        for child in children:
                            print(f"      Child: {child.name}")


if __name__ == "__main__":
    main()
