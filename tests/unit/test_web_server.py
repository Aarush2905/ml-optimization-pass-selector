"""
Unit Tests for Web Dashboard REST API Server
"""

import os
import json
import time
import threading
import unittest
import urllib.request
from src.web.server import HTTPServer, WebDashboardHandler


class TestWebServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.port = 8089
        cls.server = HTTPServer(("127.0.0.1", cls.port), WebDashboardHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_programs(self):
        url = f"http://127.0.0.1:{self.port}/api/programs"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_get_baseline_summary(self):
        url = f"http://127.0.0.1:{self.port}/api/baseline_summary"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertIn("summary", data)

    def test_get_dataset(self):
        url = f"http://127.0.0.1:{self.port}/api/dataset"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertIn("total_samples", data)
        self.assertIn("cv_accuracy", data)

    def test_get_ordering(self):
        url = f"http://127.0.0.1:{self.port}/api/ordering"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertIn("permutations", data)


if __name__ == "__main__":
    unittest.main()
