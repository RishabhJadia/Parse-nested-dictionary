import asyncio

from temporalio.client import Client
from temporalio.worker import Worker
from your_activities import your_activity
from your_workflows import YourSchedulesWorkflow, YourSchedulesWorkflow1


async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="schedules-task-queue",
        workflows=[YourSchedulesWorkflow, YourSchedulesWorkflow1],
        activities=[your_activity],
    )
    print("worker start running")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
