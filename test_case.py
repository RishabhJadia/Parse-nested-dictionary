
import unittest
from unittest.mock import Mock, patch
from my_module import ACM

class TestACM(unittest.TestCase):

    def setUp(self):
        self.prepare_acm_response = [
            ({'key1': 'value1'}, {'key2': 'value2'}),
            ({'key3': 'value3'}, {'key4': 'value4'})
        ]
        self.sid = '123'

    @patch('my_module.Service')
    def test_submit_acm(self, mock_service):
        # Mock the `Service.service_url` method to return a mock URL.
        mock_service.return_value.service_url.return_value = 'http://mocked-service-url.com'

        # Mock the `requests.post` function to return a mock response.
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post = Mock(return_value=mock_response)

        # Create an instance of the `ACM` class.
        acm = ACM()

        # Call the `submit_acm` method with the prepared input values.
        with patch('my_module.requests.post', mock_post):
            result = acm.submit_acm(self.prepare_acm_response, self.sid)

        # Assert that `Service.service_url` was called once with no arguments.
        mock_service.return_value.service_url.assert_called_once_with()

        # Assert that `requests.post` was called twice with the expected arguments.
        expected_calls = [
            ((acm.url, {'json': self.prepare_acm_response[0][0]}),),
            ((acm.url, {'json': self.prepare_acm_response[1][0]}),)
        ]
        self.assertEqual(mock_post.call_args_list, expected_calls)

        # Assert that the response has the expected format and values.
        expected_response = [{'haserror': False}, {'haserror': False}]
        self.assertEqual(result, expected_response)

    @patch('my_module.Service')
    def test_submit_acm_with_error(self, mock_service):
        # Mock the `Service.service_url` method to return a mock URL.
        mock_service.return_value.service_url.return_value = 'http://mocked-service-url.com'

        # Mock the `requests.post` function to raise an exception.
        mock_post = Mock(side_effect=Exception("Mocked error"))

        # Create an instance of the `ACM` class.
        acm = ACM()

        # Call the `submit_acm` method with the prepared input values.
        with patch('my_module.requests.post', mock_post):
            result = acm.submit_acm(self.prepare_acm_response, self.sid)

        # Assert that `Service.service_url` was called once with no arguments.
        mock_service.return_value.service_url.assert_called_once_with()

        # Assert that `requests.post` was called twice with the expected arguments.
        expected_calls = [
            ((acm.url, {'json': self.prepare_acm_response[0][0]}),),
            ((acm.url, {'json': self.prepare_acm_response[1][0]}),)
        ]
        self.assertEqual(mock_post.call_args_list, expected_calls)

        # Assert that the response has the expected format and values.
        expected_response = [{'haserror': True}, {'haserror': True}]
        self.assertEqual(result, expected_response)
---------------------------------------------------------------------------------------------
import unittest
from unittest.mock import Mock, patch
from my_module import ACM

class TestACM(unittest.TestCase):

    def setUp(self):
        self.prepare_acm_response = [
            ({'key1': 'value1'}, {'key2': 'value2'}),
            ({'key3': 'value3'}, {'key4': 'value4'})
        ]
        self.sid = '123'

    def test_submit_acm(self):
        # Prepare the mock `Service` class and mock the `Service.service_url` method to return a mock URL.
        mock_service = Mock(spec=Service)
        mock_service.service_url.return_value = 'http://mocked-service-url.com'

        # Create an instance of the `ACM` class with the mocked `Service` class.
        acm = ACM(config={'service_url': mock_service})

        # Mock the `requests.post` function to return a mock response.
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post = Mock(return_value=mock_response)

        # Call the `submit_acm` method with the prepared input values.
        with patch('my_module.requests.post', mock_post):
            result = acm.submit_acm(self.prepare_acm_response, self.sid)

        # Assert that `Service.service_url` was called once with no arguments.
        mock_service.service_url.assert_called_once_with()

        # Assert that `requests.post` was called twice with the expected arguments.
        expected_calls = [
            ((acm.url, {'json': self.prepare_acm_response[0][0]}),),
            ((acm.url, {'json': self.prepare_acm_response[1][0]}),)
        ]
        self.assertEqual(mock_post.call_args_list, expected_calls)

        # Assert that the response has the expected format and values.
        expected_response = [{'haserror': False}, {'haserror': False}]
        self.assertEqual(result, expected_response)

    def test_submit_acm_with_error(self):
        # Prepare the mock `Service` class and mock the `Service.service_url` method to return a mock URL.
        mock_service = Mock(spec=Service)
        mock_service.service_url.return_value = 'http://mocked-service-url.com'

        # Create an instance of the `ACM` class with the mocked `Service` class.
        acm = ACM(config={'service_url': mock_service})

        # Mock the `requests.post` function to raise an exception.
        mock_post = Mock(side_effect=Exception("Mocked error"))

        # Call the `submit_acm` method with the prepared input values.
        with patch('my_module.requests.post', mock_post):
            result = acm.submit_acm(self.prepare_acm_response, self.sid)

        # Assert that `Service.service_url` was called once with no arguments.
        mock_service.service_url.assert_called_once_with()

        # Assert that `requests.post` was called twice with the expected arguments.
        expected_calls = [
            ((acm.url, {'json': self.prepare_acm_response[0][0]}),),
            ((acm.url, {'json': self.prepare_acm_response[1][0]}),)
        ]
        self.assertEqual(mock_post.call_args_list, expected_calls)

        # Assert that the response has the expected format and values.
        expected_response = [{'haserror': True}, {'haserror': True}]
        self.assertEqual(result, expected_response)
---------------------------------------------------------------------------------------
import unittest
from unittest.mock import Mock

class ACMTest(unittest.TestCase):

    def setUp(self):
        self.config = Mock()
        self.config.service_url.return_value = "http://localhost:8080"

        self.acm = ACM()

    def test_submit_acm(self):
        prepare_acm_response = [(1, 2), (3, 4)]
        sid = 5

        expected_response = [{'haserror': False}, {'haserror': False}]

        self.acm._prepare_data.return_value = {'rec': 1, 'rec1': 2}
        self.acm.send_data.return_value = {'haserror': False}

        actual_response = self.acm.submit_acm(prepare_acm_response, sid)

        self.assertEqual(actual_response, expected_response)
----------------------------------------------------------------------------------------
class TestSendData(unittest.TestCase):

    def test_send_data_success(self):
        url = 'https://example.com/api/v1/data'
        headers = {'Authorization': 'Bearer TOKEN'}
        json_object = {'key1': 'value1', 'key2': 'value2'}

        # Create a mock for the `requests.post` function.
        requests_post = Mock()
        requests_post.return_value = {'haserror': False}

        # Patch the `requests.post` function with the mock.
        with unittest.mock.patch('requests.post', requests_post):

            # Create a new instance of the `SendData` class.
            send_data = SendData(url, headers)

            # Call the `send_data` function and assert that the response is successful.
            resp = send_data.send_data(json_object)
            self.assertEqual(resp['haserror'], False)

    def test_send_data_failure(self):
        url = 'https://example.com/api/v1/data'
        headers = {'Authorization': 'Bearer TOKEN'}
        json_object = {'key1': 'value1', 'key2': 'value2'}

        # Create a mock for the `requests.post` function.
        requests_post = Mock()
        requests_post.side_effect = Exception('Error sending data')

        # Patch the `requests.post` function with the mock.
        with unittest.mock.patch('requests.post', requests_post):

            # Create a new instance of the `SendData` class.
            send_data = SendData(url, headers)

            # Call the `send_data` function and assert that the response is unsuccessful.
            resp = send_data.send_data(json_object)
            self.assertEqual(resp['haserror'], True)
