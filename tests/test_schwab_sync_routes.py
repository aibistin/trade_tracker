"""
Route tests for the Schwab sync endpoints (POST/GET /api/schwab/sync...).

start_sync, get_job_status, and get_last_sync are mocked at the route's
import site — their own behavior is covered by tests/test_sync_service.py
and tests/test_schwab_transactions.py. These tests only verify request
parsing, status codes, and response shape.
"""
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.extensions import db
from tests.helpers import create_test_app


class TestSchwabSyncRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_post_sync_without_body_starts_global_sync(self):
        with patch('app.routes.api_routes.start_sync', return_value=42) as mock_start:
            response = self.client.post('/api/schwab/sync')

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json(), {'job_id': 42})
        mock_start.assert_called_once_with(symbol=None)

    def test_post_sync_with_symbol_passes_it_uppercased(self):
        with patch('app.routes.api_routes.start_sync', return_value=7) as mock_start:
            response = self.client.post('/api/schwab/sync', json={'symbol': 'aapl'})

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json(), {'job_id': 7})
        mock_start.assert_called_once_with(symbol='AAPL')

    def test_get_sync_job_returns_job_status(self):
        job = {
            'id': 5, 'symbol': None, 'status': 'success',
            'started_at': '2026-07-01T00:00:00+00:00',
            'finished_at': '2026-07-01T00:00:05+00:00',
            'inserted': 2, 'skipped_existing': 1, 'skipped_invalid': 0,
            'error_message': None,
        }
        with patch('app.routes.api_routes.get_job_status', return_value=job) as mock_status:
            response = self.client.get('/api/schwab/sync/5')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), job)
        mock_status.assert_called_once_with(5)

    def test_get_sync_job_unknown_id_returns_404(self):
        with patch('app.routes.api_routes.get_job_status', return_value=None):
            response = self.client.get('/api/schwab/sync/999')

        self.assertEqual(response.status_code, 404)

    def test_get_sync_last_returns_iso_timestamp(self):
        ts = datetime(2026, 7, 20, 12, 30, tzinfo=timezone.utc)
        with patch('app.routes.api_routes.get_last_sync', return_value=ts) as mock_last:
            response = self.client.get('/api/schwab/sync/last')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'last_synced_at': ts.isoformat()})
        mock_last.assert_called_once_with(symbol=None)

    def test_get_sync_last_returns_null_when_never_synced(self):
        with patch('app.routes.api_routes.get_last_sync', return_value=None):
            response = self.client.get('/api/schwab/sync/last')

        self.assertEqual(response.get_json(), {'last_synced_at': None})

    def test_get_sync_last_with_symbol_query_param_uppercases_it(self):
        with patch('app.routes.api_routes.get_last_sync', return_value=None) as mock_last:
            response = self.client.get('/api/schwab/sync/last?symbol=aapl')

        self.assertEqual(response.status_code, 200)
        mock_last.assert_called_once_with(symbol='AAPL')


if __name__ == '__main__':
    unittest.main()
