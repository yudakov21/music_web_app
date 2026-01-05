import unittest
from unittest.mock import patch
from utils.env import load_env_var


class TestLoadEnvVar(unittest.TestCase):

    @patch.dict("os.environ", {"TEST_ENV": "any"}, clear=True)
    def test_env_var_exists(self):
        self.assertEqual(load_env_var("TEST_ENV"), "any")

    @patch.dict("os.environ", {}, clear=True)
    def test_env_var_missing(self):
        with self.assertRaises(RuntimeError) as context:
            load_env_var("MISSING_ENV")

        self.assertIn("Env var MISSING_ENV is not set", str(context.exception))