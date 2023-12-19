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
-----------------------------------------------------------------------------------
#semaphore test case
import unittest
from unittest.mock import AsyncMock, MagicMock
from your_module_with_QR_class import QR  # Replace with the actual import path

class TestFetchMethod(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_success(self):
        # Mocking a successful response (status 200)
        mock_response = MagicMock()
        mock_response.status = 200

        # Mock the get method of the session object
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        # Create an instance of QR with the mocked session
        qr = QR(mock_session)

        # Call the fetch method
        url = "https://jsonplaceholder.typicode.com/todos/1"
        response = await qr.fetch(url)

        # Assertions
        self.assertEqual(response['200'], [url])
        self.assertEqual(response['not_200'], [])

    async def test_fetch_failure(self):
        # Mocking a failed response (status 404)
        mock_response = MagicMock()
        mock_response.status = 404

        # Mock the get method of the session object
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        # Create an instance of QR with the mocked session
        qr = QR(mock_session)

        # Call the fetch method
        url = "https://jsonplaceholder.typicode.com/todos/1"
        response = await qr.fetch(url)

        # Assertions
        self.assertEqual(response['200'], [])
        self.assertEqual(response['not_200'], [url])

    async def test_fetch_exception_handling(self):
        # Mock an exception being raised
        mock_session = AsyncMock()
        mock_session.get.side_effect = aiohttp.ClientError('Error occurred')

        # Create an instance of QR with the mocked session
        qr = QR(mock_session)

        # Call the fetch method
        url = "https://jsonplaceholder.typicode.com/todos/1"
        response = await qr.fetch(url)

        # Assertions
        self.assertEqual(response['200'], [])
        self.assertEqual(response['not_200'], [url])

if __name__ == "__main__":
    unittest.main()
