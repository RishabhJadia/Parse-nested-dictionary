
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
