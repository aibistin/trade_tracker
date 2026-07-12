import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import lib.schwab_client as schwab_client
from lib.schwab_client import _credentials, get_client, login


class SchwabEnvMixin:
    """Sets/clears the Schwab credential env vars around each test."""

    def setUp(self):
        self._saved_env = {
            key: os.environ.pop(key, None)
            for key in ("SCHWAB_API_KEY", "SCHWAB_APP_SECRET", "SCHWAB_CALLBACK_URL")
        }
        os.environ["SCHWAB_API_KEY"] = "test-key"
        os.environ["SCHWAB_APP_SECRET"] = "test-secret"

    def tearDown(self):
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class TestCredentials(SchwabEnvMixin, unittest.TestCase):
    def test_returns_env_values_with_default_callback(self):
        api_key, app_secret, callback_url = _credentials()
        self.assertEqual(api_key, "test-key")
        self.assertEqual(app_secret, "test-secret")
        self.assertEqual(callback_url, "https://127.0.0.1:8182")

    def test_custom_callback_url(self):
        os.environ["SCHWAB_CALLBACK_URL"] = "https://127.0.0.1:9999"
        self.assertEqual(_credentials()[2], "https://127.0.0.1:9999")

    def test_missing_api_key_raises(self):
        del os.environ["SCHWAB_API_KEY"]
        with self.assertRaises(EnvironmentError):
            _credentials()

    def test_missing_app_secret_raises(self):
        del os.environ["SCHWAB_APP_SECRET"]
        with self.assertRaises(EnvironmentError):
            _credentials()


class TestGetClient(SchwabEnvMixin, unittest.TestCase):
    def test_missing_token_file_raises(self):
        with patch.object(schwab_client.os.path, "exists", return_value=False):
            with self.assertRaises(FileNotFoundError) as ctx:
                get_client()
        self.assertIn("Schwab token not found", str(ctx.exception))

    def test_loads_client_from_token_file(self):
        mock_schwab = MagicMock()
        with patch.dict(sys.modules, {"schwab": mock_schwab}), \
                patch.object(schwab_client.os.path, "exists", return_value=True):
            client = get_client()

        mock_schwab.auth.client_from_token_file.assert_called_once_with(
            schwab_client.TOKEN_PATH, "test-key", "test-secret"
        )
        self.assertIs(client, mock_schwab.auth.client_from_token_file.return_value)


class TestLogin(SchwabEnvMixin, unittest.TestCase):
    def test_login_runs_oauth_flow(self):
        mock_schwab = MagicMock()
        with patch.dict(sys.modules, {"schwab": mock_schwab}):
            client = login(interactive=True)

        mock_schwab.auth.client_from_login_flow.assert_called_once_with(
            api_key="test-key",
            app_secret="test-secret",
            callback_url="https://127.0.0.1:8182",
            token_path=schwab_client.TOKEN_PATH,
            interactive=True,
        )
        self.assertIs(client, mock_schwab.auth.client_from_login_flow.return_value)

    def test_login_defaults_to_non_interactive(self):
        mock_schwab = MagicMock()
        with patch.dict(sys.modules, {"schwab": mock_schwab}):
            login()
        kwargs = mock_schwab.auth.client_from_login_flow.call_args.kwargs
        self.assertFalse(kwargs["interactive"])


if __name__ == "__main__":
    unittest.main()
