import os
import tempfile
import unittest

from lib.ignore_symbols import get_ignored_symbols


class TestGetIgnoredSymbols(unittest.TestCase):
    def _write(self, content):
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        return path

    def test_missing_file_returns_empty_set(self):
        self.assertEqual(get_ignored_symbols("/no/such/file.txt"), set())

    def test_parses_one_symbol_per_line(self):
        path = self._write("TRHC\nFOO\n")
        self.assertEqual(get_ignored_symbols(path), {"TRHC", "FOO"})

    def test_skips_blank_lines_and_comments(self):
        path = self._write("TRHC\n\n# a comment\n   \nFOO\n")
        self.assertEqual(get_ignored_symbols(path), {"TRHC", "FOO"})

    def test_normalizes_case_and_whitespace(self):
        path = self._write("  trhc  \n")
        self.assertEqual(get_ignored_symbols(path), {"TRHC"})

    def test_empty_file_returns_empty_set(self):
        path = self._write("")
        self.assertEqual(get_ignored_symbols(path), set())


if __name__ == "__main__":
    unittest.main()
