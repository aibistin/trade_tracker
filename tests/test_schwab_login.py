import unittest
from unittest.mock import patch

from bin.schwab_login import main


class TestSchwabLogin(unittest.TestCase):
    def test_no_existing_token_logs_in(self):
        with patch("bin.schwab_login.os.path.exists", return_value=False), \
             patch("bin.schwab_login.os.remove") as mock_remove, \
             patch("bin.schwab_login.login") as mock_login:
            main(force=False)

        mock_login.assert_called_once()
        mock_remove.assert_not_called()

    def test_existing_token_without_force_skips_login(self):
        with patch("bin.schwab_login.os.path.exists", return_value=True), \
             patch("bin.schwab_login.os.remove") as mock_remove, \
             patch("bin.schwab_login.login") as mock_login:
            main(force=False)

        mock_login.assert_not_called()
        mock_remove.assert_not_called()

    def test_existing_token_with_force_removes_then_logs_in(self):
        with patch("bin.schwab_login.os.path.exists", return_value=True), \
             patch("bin.schwab_login.os.remove") as mock_remove, \
             patch("bin.schwab_login.login") as mock_login:
            main(force=True)

        mock_remove.assert_called_once()
        mock_login.assert_called_once()


if __name__ == "__main__":
    unittest.main()
