import asyncio
import logging
from datetime import timedelta
from typing import Dict, List, Tuple, Union
from uuid import uuid4
​
from temporalio import activity, workflow
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
​
​
class MyActivities:
    @staticmethod
    @activity.defn
    async def my_activity() -> Dict[
        str, Dict[str, List[Dict[str, Union[str, int, Tuple[str, ...]]]]]
    ]:
        res: Dict[str, Dict[str, List[Dict[str, Union[str, int, Tuple[str, ...]]]]]] = {
            "egress": {"8876": [{"ips": "adasd", "ports": ("123",), "range": 0}]}
        }
        return res
​
​
@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self) -> None:
        res = await workflow.execute_activity(
            MyActivities.my_activity, start_to_close_timeout=timedelta(hours=1)
        )
        workflow.logger.info(f"Activity result: {res}")
​
​
async def main():
    logging.basicConfig(level=logging.INFO)
​
    async with await WorkflowEnvironment.start_local() as env:
        logging.info("Starting worker")
        task_queue = f"tq-{uuid4()}"
        async with Worker(
            env.client,
            task_queue=task_queue,
            activities=[MyActivities.my_activity],
            workflows=[MyWorkflow],
        ):
            logging.info("Running workflow")
            await env.client.execute_workflow(
                MyWorkflow.run,
                id=f"wf-{uuid4()}",
                task_queue=task_queue,
            )
​
​
if __name__ == "__main__":
    asyncio.run(main())
