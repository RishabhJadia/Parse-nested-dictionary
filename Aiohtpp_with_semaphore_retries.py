import asyncio
import aiohttp
import pandas as pd
import random

async def get_baseline(qmgr, headers, semaphore):
    df = pd.DataFrame()
    backoff = 1  # Initial backoff time
    retries = 3  # Number of retries
    async with semaphore:
        for _ in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=f"https://{qmgr}/baseline/{cs}", headers=headers, verify=False) as response:
                        if response.status != 200:
                            if response.status == 500:
                                await asyncio.sleep(backoff)
                                backoff *= 2  # Exponential backoff
                                continue
                            continue
                        data = await response.json()
                        df = df.append({"setting": data["setting"]})
                        return df  # Successful response, exit the loop
            except aiohttp.ClientResponseError as e:
                if e.status == 500:
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
--------------------------------------------------------------------------------------
import unittest
import asyncio
from unittest.mock import AsyncMock, patch
from typing import List, Dict

import your_module_with_QR_class

class TestQR(unittest.IsolatedAsyncioTestCase):
    async def test_query_mocked_success(self):
        expected_urls = [
            "https://jsonplaceholder.typicode.com/todos/1",
            "https://jsonplaceholder.typicode.com/todos/2"
        ]
        expected_responses = [
            {"200": [expected_urls[0]], "not_200": []},
            {"200": [expected_urls[1]], "not_200": []}
        ]

        # Mock ClientSession and its get method
        mock_get = AsyncMock()
        mock_get.status = 200

        async def mocked_get(*args, **kwargs):
            return mock_get

        with patch("aiohttp.ClientSession.get", new=mocked_get):
            # Instantiate QR object
            qr = your_module_with_QR_class.QR(AsyncMock())

            # Mock fetch method to return expected responses
            qr.fetch = AsyncMock(side_effect=expected_responses)

            # Run query and verify responses
            responses = await qr.query(expected_urls)
            self.assertEqual(responses, expected_responses)

if __name__ == "__main__":
    unittest.main()

                    continue
            except Exception as e:
                print(f"An exception occurred: {e}")
                break  # Exit the loop for other exceptions
    return df  # Return empty DataFrame in case of failure after retries

async def run_baseline():
    qmgrs = [...]  # Your list of qmgrs
    headers = {...}  # Your headers
    concurrent_requests = 5  # Number of concurrent requests
    semaphore = asyncio.Semaphore(concurrent_requests)
    tasks = [get_baseline(qmgr, headers, semaphore) for qmgr in qmgrs[:5]]  # Limiting to the first 5 qmgrs

    results = await asyncio.gather(*tasks)
    return pd.concat(results, ignore_index=True)

asyncio.run(run_baseline())
