"""Read PI data into a pandas DataFrame for analysis."""

from pisharp_piwebapi import PIWebAPIClient

BASE_URL = "https://your-server/piwebapi"


def main() -> None:
    with PIWebAPIClient(
        base_url=BASE_URL,
        username="your-user",
        password="your-password",
        verify_ssl=False,
    ) as client:
        # Look up a point
        point = client.points.get_by_path(r"\\SERVER\sinusoid")

        # Read 24 hours of recorded data
        values = client.streams.get_recorded(
            point.web_id,
            start_time="-24h",
            end_time="*",
            max_count=10000,
        )
        print(f"Retrieved {len(values)} recorded values")

        # Convert to pandas DataFrame
        df = values.to_dataframe()
        print(f"\nDataFrame shape: {df.shape}")
        print(f"\nStatistics:\n{df['value'].describe()}")

        # Read interpolated data at regular intervals
        interpolated = client.streams.get_interpolated(
            point.web_id,
            start_time="-24h",
            end_time="*",
            interval="15m",
        )
        df_interp = interpolated.to_dataframe()
        print(f"\nInterpolated DataFrame shape: {df_interp.shape}")
        print(f"\nFirst 5 rows:\n{df_interp.head()}")


if __name__ == "__main__":
    main()
