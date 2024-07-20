import unittest
from unittest.mock import patch, Mock
from service.metrics_collector import CustomCollector, fetch_data_from_api
from prometheus_client.core import CollectorRegistry

class TestMetricsCollector(unittest.TestCase):
    @patch('service.metrics_collector.requests.get')
    def test_fetch_data_from_api(self, mock_get):
        # Mock the API response
        mock_response = Mock()
        expected_data = [{'certype': 'type1', 'issuer': 'issuer1', 'fsid': 'fsid1', 'validto': '2025-01-01', 'validfrom': '2022-01-01'}]
        mock_response.json.return_value = expected_data
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        seal_id = 'seal_id_1'
        data = fetch_data_from_api(seal_id)
        
        self.assertEqual(data, expected_data)
        mock_get.assert_called_with('https://api.example.com/certificates', params={'seal_id': seal_id})

    @patch('service.metrics_collector.fetch_data_from_api')
    def test_collect(self, mock_fetch_data):
        # Mock the data returned by the API
        mock_fetch_data.return_value = [
            {'certype': 'type1', 'issuer': 'issuer1', 'fsid': 'fsid1', 'validto': '2025-01-01', 'validfrom': '2022-01-01'},
            {'certype': 'type2', 'issuer': 'issuer2', 'fsid': 'fsid2', 'validto': '2026-01-01', 'validfrom': '2023-01-01'}
        ]
        
        seal_ids = ["seal_id_1", "seal_id_2"]
        collector = CustomCollector(seal_ids)
        registry = CollectorRegistry()
        registry.register(collector)
        
        metrics = list(registry.collect())
        self.assertEqual(len(metrics), 1)
        metric = metrics[0]
        self.assertEqual(metric.name, 'certificate_info')
        self.assertEqual(len(metric.samples), 2)
        self.assertEqual(metric.samples[0].labels, {'certype': 'type1', 'issuer': 'issuer1', 'fsid': 'fsid1', 'validto': '2025-01-01', 'validfrom': '2022-01-01'})
        self.assertEqual(metric.samples[1].labels, {'certype': 'type2', 'issuer': 'issuer2', 'fsid': 'fsid2', 'validto': '2026-01-01', 'validfrom': '2023-01-01'})

if __name__ == '__main__':
    unittest.main()
------------------------------------------------------------------------------------------
import unittest
from unittest.mock import patch
from app import app

class TestEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('api.endpoints.initialize_collector')
    def test_metrics_endpoint(self, mock_initialize_collector):
        mock_registry = patch('api.endpoints.CollectorRegistry').start()
        mock_initialize_collector.return_value = mock_registry
        
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'# HELP certificate_info', response.data)

    def test_health_endpoint(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"OK")

if __name__ == '__main__':
    unittest.main()
--------------------------------------------------------------------
import unittest
from unittest.mock import patch, MagicMock
from utilities.utils import initialize_collector
from service.metrics_collector import CustomCollector
from prometheus_client.core import CollectorRegistry

class TestUtils(unittest.TestCase):
    @patch('utilities.utils.CustomCollector')
    @patch('utilities.utils.CollectorRegistry')
    def test_initialize_collector_default_seal_ids(self, mock_collector_registry, mock_custom_collector):
        # Setup the mocks
        mock_registry = MagicMock(spec=CollectorRegistry)
        mock_collector_registry.return_value = mock_registry
        
        mock_collector_instance = MagicMock(spec=CustomCollector)
        mock_custom_collector.return_value = mock_collector_instance
        
        # Call the function without seal_ids
        registry = initialize_collector()
        
        # Assertions
        mock_collector_registry.assert_called_once()
        mock_custom_collector.assert_called_once_with(["seal_id_1", "seal_id_2", "seal_id_3"])
        mock_registry.register.assert_called_once_with(mock_collector_instance)
        self.assertEqual(registry, mock_registry)

    @patch('utilities.utils.CustomCollector')
    @patch('utilities.utils.CollectorRegistry')
    def test_initialize_collector_with_custom_seal_ids(self, mock_collector_registry, mock_custom_collector):
        # Setup the mocks
        mock_registry = MagicMock(spec=CollectorRegistry)
        mock_collector_registry.return_value = mock_registry
        
        mock_collector_instance = MagicMock(spec=CustomCollector)
        mock_custom_collector.return_value = mock_collector_instance
        
        # Define custom seal IDs
        custom_seal_ids = ["custom_seal_id_1", "custom_seal_id_2"]
        
        # Call the function with custom seal_ids
        registry = initialize_collector(custom_seal_ids)
        
        # Assertions
        mock_collector_registry.assert_called_once()
        mock_custom_collector.assert_called_once_with(custom_seal_ids)
        mock_registry.register.assert_called_once_with(mock_collector_instance)
        self.assertEqual(registry, mock_registry)

if __name__ == '__main__':
    unittest.main()
:
    unittest.main()
