import asyncio
from temporalio import activity
from your_dataobject import YourParams


@activity.defn
async def your_activity(input: YourParams) -> str:
    await asyncio.sleep(20)
    print("-----------------")
    return f"{input.greeting}, {input.name}!"
