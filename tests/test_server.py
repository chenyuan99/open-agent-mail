from __future__ import annotations

import json
import threading
import unittest
from http.client import HTTPConnection

import open_agent_mail.server as server_module
from open_agent_mail.server import Handler, Store, ThreadingHTTPServer


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store()

    def test_seed_data_has_two_mailboxes_and_three_messages(self) -> None:
        payload = self.store.payload()
        self.assertEqual(2, len(payload["mailboxes"]))
        self.assertEqual(3, len(payload["messages"]))

    def test_mailboxes_are_unique(self) -> None:
        self.assertTrue(self.store.add_mailbox("builder@agent.local"))
        self.assertFalse(self.store.add_mailbox("builder@agent.local"))

    def test_send_creates_read_sent_message(self) -> None:
        message = self.store.send("hello@agent.local", "person@example.com", "Status", "Complete")
        self.assertEqual("sent", message.folder)
        self.assertTrue(message.read)
        self.assertEqual(4, message.id)

    def test_mark_read_reports_presence(self) -> None:
        self.assertTrue(self.store.mark_read(1))
        self.assertFalse(self.store.mark_read(999))
        self.assertTrue(self.store.payload()["messages"][0]["read"])


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original_store = server_module.STORE
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)
        server_module.STORE = cls.original_store

    def setUp(self) -> None:
        server_module.STORE = Store()

    def request(self, method: str, path: str, payload: dict | None = None):
        connection = HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
        body = None if payload is None else json.dumps(payload)
        headers = {} if payload is None else {"Content-Type": "application/json"}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        content = response.read()
        result = response.status, response.getheader("Content-Type"), content
        connection.close()
        return result

    def test_serves_application_shell(self) -> None:
        status, content_type, body = self.request("GET", "/")
        self.assertEqual(200, status)
        self.assertIn("text/html", content_type)
        self.assertIn(b"Open Agent Mail", body)

    def test_state_endpoint(self) -> None:
        status, _, body = self.request("GET", "/api/state")
        self.assertEqual(200, status)
        self.assertEqual(2, len(json.loads(body)["mailboxes"]))

    def test_complete_mailbox_and_message_flow(self) -> None:
        status, _, body = self.request("POST", "/api/mailboxes", {"name": "Build Bot"})
        self.assertEqual(201, status)
        self.assertEqual("build-bot@agent.local", json.loads(body)["address"])

        status, _, body = self.request("POST", "/api/messages", {
            "mailbox": "build-bot@agent.local",
            "recipient": "human@example.com",
            "subject": "Build complete",
            "body": "All checks passed.",
        })
        message = json.loads(body)
        self.assertEqual(201, status)
        self.assertEqual("sent", message["folder"])

        status, _, body = self.request("POST", f"/api/messages/{message['id']}/read", {})
        self.assertEqual(200, status)
        self.assertTrue(json.loads(body)["ok"])

    def test_rejects_invalid_and_duplicate_mailboxes(self) -> None:
        status, _, _ = self.request("POST", "/api/mailboxes", {"name": "bad/name"})
        self.assertEqual(400, status)
        status, _, _ = self.request("POST", "/api/mailboxes", {"name": "hello"})
        self.assertEqual(409, status)

    def test_rejects_incomplete_message(self) -> None:
        status, _, body = self.request("POST", "/api/messages", {"mailbox": "hello@agent.local"})
        self.assertEqual(400, status)
        self.assertIn("error", json.loads(body))

    def test_malformed_read_id_and_missing_resource(self) -> None:
        status, _, _ = self.request("POST", "/api/messages/not-a-number/read", {})
        self.assertEqual(400, status)
        status, _, _ = self.request("GET", "/missing.txt")
        self.assertEqual(404, status)


if __name__ == "__main__":
    unittest.main()
