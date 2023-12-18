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
