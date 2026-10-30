"""Unit tests for Config loader."""

import os
import unittest
from unittest.mock import patch

from src.config import Config


class TestConfig(unittest.TestCase):
    def test_missing_credentials_raises_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                Config.from_env()

    def test_valid_config(self):
        env_vars = {
            "MYWHOOSH_EMAIL": "test@example.com",
            "MYWHOOSH_PASSWORD": "secretpassword",
            "GARMIN_USERNAME": "garmin_user",
            "GARMIN_PASSWORD": "garmin_pass",
            "SYNC_INTERVAL_MINUTES": "30",
            "SPOOF_GARMIN_DEVICE": "true",
            "DEVICE_PRODUCT_ID": "4024",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            cfg = Config.from_env()
            self.assertEqual(cfg.mywhoosh_email, "test@example.com")
            self.assertEqual(cfg.mywhoosh_password, "secretpassword")
            self.assertEqual(cfg.sync_interval_minutes, 30)
            self.assertTrue(cfg.spoof_garmin_device)
            self.assertEqual(cfg.device_product_id, 4024)

    def test_default_values(self):
        env_vars = {
            "MYWHOOSH_EMAIL": "test@example.com",
            "MYWHOOSH_PASSWORD": "secretpassword",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            cfg = Config.from_env()
            self.assertEqual(cfg.sync_interval_minutes, 60)
            self.assertEqual(cfg.garmin_token_dir, cfg.data_dir / "garmin_tokens")
            self.assertTrue(cfg.webhook_enabled)
            self.assertEqual(cfg.webhook_host, "0.0.0.0")
            self.assertEqual(cfg.webhook_port, 8080)
            self.assertEqual(cfg.webhook_token, "")

    def test_webhook_config_custom(self):
        env_vars = {
            "MYWHOOSH_EMAIL": "test@example.com",
            "MYWHOOSH_PASSWORD": "secretpassword",
            "WEBHOOK_ENABLED": "false",
            "WEBHOOK_HOST": "127.0.0.1",
            "WEBHOOK_PORT": "9090",
            "WEBHOOK_TOKEN": "secret_abc_123",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            cfg = Config.from_env()
            self.assertFalse(cfg.webhook_enabled)
            self.assertEqual(cfg.webhook_host, "127.0.0.1")
            self.assertEqual(cfg.webhook_port, 9090)
            self.assertEqual(cfg.webhook_token, "secret_abc_123")


if __name__ == "__main__":
    unittest.main()
