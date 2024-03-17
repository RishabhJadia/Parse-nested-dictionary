import asyncio
from datetime import timedelta

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
    ScheduleState,
)
from your_workflows import YourSchedulesWorkflow, YourSchedulesWorkflow1


async def main():
    client = await Client.connect("localhost:7233")
    await client.create_schedule(
        "workflow-schedule-id",
        Schedule(
            action=ScheduleActionStartWorkflow(
                YourSchedulesWorkflow.run,
                "my schedule arg",
                id="schedules-workflow-id",
                task_queue="schedules-task-queue",
            ),
            spec=ScheduleSpec(
                # intervals=[ScheduleIntervalSpec(every=timedelta(seconds=10))]
                cron_expressions=["42 8 * * *"], # UTC
                # cron_expressions=["*/1 * * * *"], # every 1min
            ),
            state=ScheduleState(note="Here's a note on my Schedule."),
        ),
    )
    # await asyncio.sleep(20)
    # await client.create_schedule(
    #     "workflow-schedule-id1",
    #     Schedule(
    #         action=ScheduleActionStartWorkflow(
    #             YourSchedulesWorkflow1.run,
    #             "my schedule arg",
    #             id="schedules-workflow-id1",
    #             task_queue="schedules-task-queue",
    #         ),
    #         spec=ScheduleSpec(
    #             intervals=[ScheduleIntervalSpec(every=timedelta(seconds=10))]
    #         ),
    #         state=ScheduleState(note="Here's a note on my Schedule."),
    #     ),
    # )


if __name__ == "__main__":
    asyncio.run(main())
