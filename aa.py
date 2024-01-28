import unittest
from unittest.mock import patch, MagicMock
from http import HTTPStatus
from api.decorator import auth_validation_check

class TestAuthValidationCheck(unittest.TestCase):
    @patch('api.decorator.authenticate')
    @patch('api.decorator.request')
    @patch('api.decorator.schema')
    def test_auth_validation_check_with_success(self, mock_schema, mock_request, mock_authenticate):
        # Mocking schema
        mock_payload = MagicMock()
        mock_schema.parse_args.return_value = mock_payload
        mock_schema.payload = mock_payload
        
        # Mocking request method
        mock_request.method = 'GET'
        
        # Mocking authenticate
        mock_response = {"haserror": False, "message": "Authentication successful"}
        mock_hcon = MagicMock()
        mock_authenticate.return_value = (mock_response, mock_hcon)
        
        # Mocking function
        @auth_validation_check(mock_schema)
        def mock_function(*args, **kwargs):
            return {"haserror": False, "message": "Success"}, mock_hcon
        
        # Calling the function under test
        response, status_code = mock_function()
        
        # Assertions
        self.assertEqual(status_code, HTTPStatus.OK)
        self.assertEqual(response, {"haserror": False, "message": "Success"})
        mock_authenticate.assert_called_once_with(mock_payload)
        mock_schema.parse_args.assert_called_once()
        mock_function.assert_called_once()
        mock_hcon.disconnect.assert_called_once()
        
    # Add more test cases for other scenarios (e.g., authentication failure, different request methods, etc.)...

if __name__ == '__main__':
    unittest.main()
