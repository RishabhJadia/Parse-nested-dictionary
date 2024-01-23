import unittest
from unittest.mock import MagicMock, patch
import pymqi

class MessageProcessor:
    @staticmethod
    def process_message(queue_obj, method, mqmd, gmo):
        try:
            if method == "GET":
                message = queue_obj.get(None, mqmd, gmo)
            else:
                message = "PUT OPERATION"
        except pymqi.MQMIError as e:
            if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                print("no more message")
                message = None
            else:
                raise e
        return message

class TestMessageProcessor(unittest.TestCase):

    @patch('pymqi.Queue')
    def test_process_message_get(self, mock_queue_class):
        # Set up mocks
        mock_queue_instance = mock_queue_class.return_value
        mock_queue_instance.get.return_value = b"Test Message"

        # Set up test parameters
        queue_obj = mock_queue_instance
        method = "GET"
        mqmd = MagicMock()
        gmo = MagicMock()

        # Call the process_message method
        result = MessageProcessor.process_message(queue_obj, method, mqmd, gmo)

        # Assert that the get method of the queue_obj was called with the correct parameters
        mock_queue_instance.get.assert_called_once_with(None, mqmd, gmo)

        # Assert the result
        self.assertEqual(result, b"Test Message")

    @patch('pymqi.Queue')
    def test_process_message_put(self, mock_queue_class):
        # Set up mocks
        mock_queue_instance = mock_queue_class.return_value

        # Set up test parameters
        queue_obj = mock_queue_instance
        method = "PUT"
        mqmd = MagicMock()
        gmo = MagicMock()

        # Call the process_message method
        result = MessageProcessor.process_message(queue_obj, method, mqmd, gmo)

        # Assert that the get method of the queue_obj was not called
        mock_queue_instance.get.assert_not_called()

        # Assert the result
        self.assertEqual(result, "PUT OPERATION")

    @patch('pymqi.Queue')
    def test_process_message_no_msg_available(self, mock_queue_class):
        # Set up mocks
        mock_queue_instance = mock_queue_class.return_value
        mock_queue_instance.get.side_effect = pymqi.MQMIError(
            comp=pymqi.CMQC.MQCC_FAILED,
            reason=pymqi.CMQC.MQRC_NO_MSG_AVAILABLE,
            msg='No message available'
        )

        # Set up test parameters
        queue_obj = mock_queue_instance
        method = "GET"
        mqmd = MagicMock()
        gmo = MagicMock()

        # Call the process_message method
        result = MessageProcessor.process_message(queue_obj, method, mqmd, gmo)

        # Assert that the get method of the queue_obj was called with the correct parameters
        mock_queue_instance.get.assert_called_once_with(None, mqmd, gmo)

        # Assert the result
        self.assertIsNone(result)

    @patch('pymqi.Queue')
    def test_process_message_other_error(self, mock_queue_class):
        # Set up mocks
        mock_queue_instance = mock_queue_class.return_value
        mock_queue_instance.get.side_effect = pymqi.MQMIError(
            comp=pymqi.CMQC.MQCC_FAILED,
            reason=999,  # Some other reason code
            msg='Other error'
        )

        # Set up test parameters
        queue_obj = mock_queue_instance
        method = "GET"
        mqmd = MagicMock()
        gmo = MagicMock()

        # Call the process_message method and expect an exception to be raised
        with self.assertRaises(pymqi.MQMIError):
            MessageProcessor.process_message(queue_obj, method, mqmd, gmo)

        # Assert that the get method of the queue_obj was called with the correct parameters
        mock_queue_instance.get.assert_called_once_with(None, mqmd, gmo)

if __name__ == '__main__':
    unittest.main()
