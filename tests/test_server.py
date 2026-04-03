import os
import unittest
from unittest.mock import patch

import server


class MirrorServerTests(unittest.TestCase):
    def setUp(self):
        self.app = server.app
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

    def test_healthz(self):
        res = self.client.get("/healthz")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("missingWeights", body)

    def test_config_endpoint(self):
        os.environ["GEMINI_MODEL"] = "gemini-2.0-flash"
        res = self.client.get("/config")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertIn("serverKeyConfigured", body)
        self.assertIn("defaultModel", body)

    def test_weights_unknown_file(self):
        res = self.client.get("/weights/not-allowed-file.bin")
        self.assertEqual(res.status_code, 404)
        self.assertIn("error", res.get_json())

    def test_gemini_missing_body(self):
        res = self.client.post("/gemini", json={"key": "x"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())

    @patch("server.post_gemini_generate")
    def test_gemini_success(self, mock_post):
        payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "hello"}]
                    }
                }
            ]
        }
        mock_post.return_value = (200, payload, None)
        res = self.client.post(
            "/gemini",
            json={"key": "key", "body": {"contents": [{"parts": [{"text": "x"}]}]}},
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body["candidates"][0]["content"]["parts"][0]["text"], "hello")
        self.assertEqual(body["_meta"]["model"], "gemini-2.0-flash")

    @patch("server.post_gemini_generate")
    def test_gemini_network_error(self, mock_post):
        mock_post.return_value = (None, None, "timeout")
        res = self.client.post(
            "/gemini",
            json={"key": "key", "body": {"contents": [{"parts": [{"text": "x"}]}]}},
        )
        self.assertEqual(res.status_code, 502)
        self.assertIn("error", res.get_json())

    @patch("server.post_gemini_generate")
    def test_gemini_model_fallback(self, mock_post):
        not_found = (404, {"error": {"message": "Model not found"}}, None)
        success = (
            200,
            {"candidates": [{"content": {"parts": [{"text": "from fallback"}]}}]},
            None,
        )
        mock_post.side_effect = [not_found, success]
        res = self.client.post(
            "/gemini",
            json={
                "key": "key",
                "model": "invalid-model",
                "body": {"contents": [{"parts": [{"text": "x"}]}]},
            },
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body["candidates"][0]["content"]["parts"][0]["text"], "from fallback")
        self.assertEqual(body["_meta"]["model"], "gemini-2.0-flash")


if __name__ == "__main__":
    unittest.main()
