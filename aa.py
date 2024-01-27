import unittest
from unittest.mock import patch, MagicMock
from your_module import authentiate

class TestAuthenticate(unittest.TestCase):
    @patch('your_module.get_connection')
    @patch('your_module.get_obo_token')
    @patch('your_module.decode_token')
    @patch('your_module.request')
    def test_authenticate_with_success(self, mock_request, mock_decode_token, mock_get_obo_token, mock_get_connection):
        # Mocking return values for functions
        mock_decode_token.return_value = {"haserror": False, "message": "Token decoded successfully", "identifier": "mock_fid"}
        mock_get_obo_token.return_value = {"haserror": False, "message": "OBO token retrieved successfully"}
        mock_get_connection.return_value = MagicMock()  # Mocking a connection object
        
        # Mocking request headers
        mock_request.headers.get.return_value = 'Bearer mock_access_token'
        payload = {'fid': 'mock_fid', 'qmgr': 'mock_qmgr', 'channel': 'mock_channel'}
        
        # Calling the function under test
        response, hcon = authentiate(payload)
        
        # Assertions
        self.assertFalse(response['haserror'])
        self.assertEqual(response['message'], 'Connection  Established')
        self.assertIsNotNone(hcon)
        mock_decode_token.assert_called_once_with(any_params_here)  # Assert arguments passed to decode_token
        mock_get_obo_token.assert_called_once_with('mock_access_token')  # Assert arguments passed to get_obo_token
        mock_get_connection.assert_called_once_with('mock_qmgr', any_other_params_here)  # Assert arguments passed to get_connection
        mock_request.headers.get.assert_called_once_with('Authorization')  # Assert request headers accessed correctly
    
    @patch('your_module.get_connection')
    @patch('your_module.get_obo_token')
    @patch('your_module.decode_token')
    @patch('your_module.request')
    def test_authenticate_with_failure(self, mock_request, mock_decode_token, mock_get_obo_token, mock_get_connection):
        # Mocking return values for functions
        mock_decode_token.return_value = {"haserror": True, "message": "Token decoding failed"}
        mock_get_obo_token.return_value = {"haserror": False, "message": "OBO token retrieved successfully"}
        mock_get_connection.return_value = None
        
        # Mocking request headers
        mock_request.headers.get.return_value = 'Bearer mock_access_token'
        payload = {'fid': 'mock_fid', 'qmgr': 'mock_qmgr', 'channel': 'mock_channel'}
        
        # Calling the function under test
        response, hcon = authentiate(payload)
        
        # Assertions
        self.assertTrue(response['haserror'])
        self.assertEqual(response['message'], 'Token decoding failed')
        self.assertIsNone(hcon)
        mock_decode_token.assert_called_once_with(any_params_here)  # Assert arguments passed to decode_token
        mock_get_obo_token.assert_called_once_with('mock_access_token')  # Assert arguments passed to get_obo_token
        mock_get_connection.assert_not_called()  # Ensure get_connection was not called
        mock_request.headers.get.assert_called_once_with('Authorization')  # Assert request headers accessed correctly
        
if __name__ == '__main__':
    unittest.main()
