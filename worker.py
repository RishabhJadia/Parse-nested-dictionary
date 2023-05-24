import asyncio
from typing import Callable

from temporalio.client import Client
from temporalio.worker import Worker


class DynamicWorker:
    """
    A class that can be used to create a dynamic worker.

    Args:
        json_file_path: The path to the JSON file that contains the critical parameters for the worker.

    """

    def __init__(self, json_file_path: str) -> None:
        """
        Create a new DynamicWorker instance.

        Args:
            json_file_path: The path to the JSON file that contains the critical parameters for the worker.

        """
        # Read the critical parameters from the JSON file.
        with open(json_file_path, "r") as f:
            data = json.load(f)

        # Set the critical parameters on the worker.
        self.target_host = data["target_host"]
        self.tls = data["tls"]
        self.task_queue = data["task_queue"]
        self.workflows = data["workflows"]
        self.activities = data["activities"]

        # Connect to Temporal.
        self.client = await Client.connect(target_host=self.target_host, tls=self.tls)

        # Create a worker.
        self.worker = Worker(client, task_queue=self.task_queue, workflows=self.workflows, activities=self.activities)

        # Set the interval seconds.
        self.interval_seconds = 10

        # Set the get_token function.
        self.get_token = get_token_from_json

    async def run(self) -> None:
        """
        Start the worker.

        """
        # Run the worker indefinitely.
        async with self.worker:
            while True:
                # Sleep for the interval seconds.
                await asyncio.sleep(self.interval_seconds)

                # Refresh the token.
                self.client.rpc_metadata = {"Authorization": f"Bearer {self.get_token()}"}


def get_token_from_json(json_file_path: str) -> str:
    """
    Get the token from the JSON file.

    Args:
        json_file_path: The path to the JSON file that contains the token.

    Returns:
        The token.

    """
    # Read the JSON file.
    with open(json_file_path, "r") as f:
        data = json.load(f)

    # Get the token.
    return data["token"]


if __name__ == "__main__":
    json_file_path = "/path/to/json/file"

    # Create a dynamic worker.
    dynamic_worker = DynamicWorker(json_file_path)

    # Start the worker.
    await dynamic_worker.run()
