import asyncio
import os
from datetime import timedelta
from typing import Collection

import requests

# List of endpoints to poll
ENDPOINTS = [
    "https://example.com/api/endpoint1",
    "https://example.com/api/endpoint2",
    "https://example.com/api/endpoint3",
]

# Base path for storing the response files
BASE_PATH = "responses"

# Polling interval (default: 5 minutes)
POLLING_INTERVAL = timedelta(minutes=5)


class Loop:
    """
    Main loop class.
    """

    def __init__(self, accounts: Collection[str]) -> None:
        self.accounts = accounts or []


async def poll_endpoint(endpoint):
    """
    Polls the given endpoint and stores the response in a text file.
    """
    try:
        response = requests.get(endpoint)
        response.raise_for_status()

        # Create the base path if it doesn't exist
        os.makedirs(BASE_PATH, exist_ok=True)

        # Construct the file path based on the endpoint
        file_path = os.path.join(
            BASE_PATH, f"{endpoint.replace('https://', '').replace('/', '_')}.txt"
        )

        # Save the response to a text file
        with open(file_path, "w") as file:
            file.write(response.text)

        print(f"Saved response for {endpoint} to {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error polling {endpoint}: {e}")


async def main():
    """
    Main async loop that periodically polls the endpoints and stores their responses.
    """
    while True:
        # Poll each endpoint
        await asyncio.gather(*[poll_endpoint(endpoint) for endpoint in ENDPOINTS])

        # Wait for the next polling interval
        await asyncio.sleep(POLLING_INTERVAL.total_seconds())


if __name__ == "__main__":
    asyncio.run(main())
