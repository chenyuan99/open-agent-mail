from __future__ import annotations

import json
from io import StringIO
import socket
import threading
import time
import unittest
from http.client import HTTPConnection

import uvicorn

import open_agent_mail.server as server_module
from open_agent_mail.server import Store
from open_agent_mail.cli import run as run_cli


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store()

    def test_seed_data_has_two_mailboxes_and_three_messages(self) -> None:
        payload = self.store.payload()
        self.assertEqual(2, len(payload["mailboxes"]))
        self.assertEqual(3, len(payload["messages"]))
        self.assertEqual(2, len(payload["contacts"]))

    def test_mailboxes_are_unique(self) -> None:
        self.assertTrue(self.store.add_mailbox("builder@agent.local"))
        self.assertFalse(self.store.add_mailbox("builder@agent.local"))

    def test_send_creates_read_sent_message(self) -> None:
        message = self.store.send("hello@agent.local", "person@example.com", "Status", "Complete")
        self.assertEqual("sent", message.folder)
        self.assertTrue(message.read)
        self.assertEqual(4, message.id)
        self.assertEqual("thread-4", message.thread_id)

    def test_local_delivery_and_reply_preserve_thread(self) -> None:
        first = self.store.send("hello@agent.local", "research@agent.local", "Review", "Please review")
        inbox_copy = self.store.payload()["messages"][-1]
        self.assertEqual("inbox", inbox_copy["folder"])
        self.assertEqual(first.thread_id, inbox_copy["thread_id"])
        reply = self.store.send("research@agent.local", "hello@agent.local", "Re: Review", "Approved", inbox_copy["id"])
        self.assertEqual(first.thread_id, reply.thread_id)
        self.assertEqual(inbox_copy["id"], reply.in_reply_to)

    def test_complete_company_handoff_stays_in_one_thread(self) -> None:
        roles = ["analyst", "research-manager", "trader", "risk", "portfolio-manager"]
        for role in roles:
            self.assertTrue(self.store.add_mailbox(f"{role}@agent.local"))

        parent_id = None
        thread_id = None
        for sender, recipient in zip(roles, roles[1:]):
            message = self.store.send(
                f"{sender}@agent.local",
                f"{recipient}@agent.local",
                "[TRADE-REVIEW] [AAPL] 2026-08-19",
                f"Handoff from {sender} to {recipient}",
                parent_id,
            )
            self.assertIsNotNone(message)
            thread_id = thread_id or message.thread_id
            self.assertEqual(thread_id, message.thread_id)
            recipient_copy = self.store.payload()["messages"][-1]
            self.assertEqual(f"{recipient}@agent.local", recipient_copy["mailbox"])
            self.assertEqual("inbox", recipient_copy["folder"])
            self.assertEqual(thread_id, recipient_copy["thread_id"])
            parent_id = recipient_copy["id"]

        records = [message for message in self.store.payload()["messages"] if message["thread_id"] == thread_id]
        self.assertEqual(2 * (len(roles) - 1), len(records))
        self.assertEqual(1, sum(message["mailbox"] == "analyst@agent.local" for message in records))
        self.assertEqual(1, sum(message["mailbox"] == "portfolio-manager@agent.local" for message in records))

    def test_mark_read_reports_presence(self) -> None:
        self.assertTrue(self.store.mark_read(1))
        self.assertFalse(self.store.mark_read(999))
        self.assertTrue(self.store.payload()["messages"][0]["read"])

    def test_contact_lifecycle_and_duplicate_email(self) -> None:
        contact = self.store.add_contact("Builder", ["BUILDER@agent.local"], ["Agents", "Agents"])
        self.assertEqual(["builder@agent.local"], contact.emails)
        self.assertEqual(["Agents"], contact.groups)
        self.assertIsNone(self.store.add_contact("Duplicate", ["builder@agent.local"], []))
        self.assertTrue(self.store.delete_contact(contact.id))
        self.assertFalse(self.store.delete_contact(contact.id))


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original_store = server_module.STORE
        with socket.socket() as available:
            available.bind(("127.0.0.1", 0))
            cls.server_port = available.getsockname()[1]
        config = uvicorn.Config(server_module.app, host="127.0.0.1", port=cls.server_port, log_level="error")
        cls.httpd = uvicorn.Server(config)
        cls.thread = threading.Thread(target=cls.httpd.run, daemon=True)
        cls.thread.start()
        for _ in range(100):
            if cls.httpd.started:
                break
            time.sleep(0.02)
        if not cls.httpd.started:
            raise RuntimeError("Test API server did not start.")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.should_exit = True
        cls.thread.join(timeout=5)
        server_module.STORE = cls.original_store

    def setUp(self) -> None:
        server_module.STORE = Store()

    def request(self, method: str, path: str, payload: dict | None = None):
        connection = HTTPConnection("127.0.0.1", self.server_port, timeout=3)
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
        self.assertIn(b"helpDialog", body)

    def test_serves_help_center_assets(self) -> None:
        status, content_type, body = self.request("GET", "/help.css")
        self.assertEqual(200, status)
        self.assertIn("text/css", content_type)
        self.assertIn(b"help-dialog", body)
        status, _, body = self.request("GET", "/app.js")
        self.assertEqual(200, status)
        self.assertIn("HELP_ARTICLES".encode(), body)
        self.assertIn("recipient".encode(), body)

    def test_serves_semantic_theme_assets(self) -> None:
        status, content_type, body = self.request("GET", "/shadcn-theme.css")
        self.assertEqual(200, status)
        self.assertIn("text/css", content_type)
        self.assertIn(b"--primary", body)
        self.assertIn(b"prefers-reduced-motion", body)
        status, _, body = self.request("GET", "/")
        self.assertEqual(200, status)
        self.assertIn(b"themeToggle", body)
        self.assertIn(b"shadcn-theme.css", body)

    def test_state_endpoint(self) -> None:
        status, _, body = self.request("GET", "/api/state")
        self.assertEqual(200, status)
        self.assertEqual(2, len(json.loads(body)["mailboxes"]))

    def test_openapi_schema_documents_every_api_path(self) -> None:
        status, content_type, body = self.request("GET", "/openapi.json")
        schema = json.loads(body)
        self.assertEqual(200, status)
        self.assertIn("application/json", content_type)
        self.assertEqual("3.1.0", schema["openapi"])
        self.assertEqual({
            "/api/state", "/api/mailboxes", "/api/messages", "/api/messages/{message_id}/read",
            "/api/contacts", "/api/contacts/{contact_id}",
        }, set(schema["paths"]))
        self.assertIn("MessageResponse", schema["components"]["schemas"])

    def test_serves_same_origin_swagger_ui(self) -> None:
        status, content_type, body = self.request("GET", "/docs")
        self.assertEqual(200, status)
        self.assertIn("text/html", content_type)
        self.assertIn(b"/openapi.json", body)
        self.assertIn(b"/swagger/swagger-ui-bundle.js", body)
        self.assertNotIn(b"https://", body)
        for path, expected_type, marker in (
            ("/swagger/swagger-ui.css", "text/css", b".swagger-ui"),
            ("/swagger/swagger-ui-bundle.js", "javascript", b"SwaggerUIBundle"),
            ("/swagger/LICENSE", "application/octet-stream", b"Apache License"),
        ):
            status, content_type, asset = self.request("GET", path)
            self.assertEqual(200, status)
            self.assertIn(expected_type, content_type)
            self.assertIn(marker, asset)

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

    def test_rejects_unknown_reply_target(self) -> None:
        status, _, body = self.request("POST", "/api/messages", {
            "mailbox": "hello@agent.local", "recipient": "research@agent.local",
            "subject": "Re: Missing", "body": "Reply", "in_reply_to": 999,
        })
        self.assertEqual(404, status)
        self.assertIn("error", json.loads(body))

    def test_agent_cli_send_list_read_and_reply(self) -> None:
        base = f"http://127.0.0.1:{self.server_port}"
        output = StringIO()
        self.assertEqual(0, run_cli(["send", "--url", base, "--from", "hello@agent.local",
                                    "--to", "research@agent.local", "--subject", "Review", "--body", "Check it"], output))
        sent = json.loads(output.getvalue())
        output = StringIO()
        self.assertEqual(0, run_cli(["inbox", "--url", base, "--mailbox", "research@agent.local", "--unread"], output))
        inbox = json.loads(output.getvalue())["messages"]
        delivered = next(message for message in inbox if message["thread_id"] == sent["thread_id"])
        output = StringIO()
        self.assertEqual(0, run_cli(["read", "--url", base, "--mailbox", "research@agent.local",
                                    str(delivered["id"])], output))
        output = StringIO()
        self.assertEqual(0, run_cli(["reply", "--url", base, "--from", "research@agent.local",
                                    str(delivered["id"]), "--body", "Approved"], output))
        self.assertEqual(sent["thread_id"], json.loads(output.getvalue())["thread_id"])

    def test_agent_cli_unknown_reply_is_json_error_without_mutation(self) -> None:
        base = f"http://127.0.0.1:{self.server_port}"
        before = len(server_module.STORE.payload()["messages"])
        output, errors = StringIO(), StringIO()
        status = run_cli(["reply", "--url", base, "--from", "hello@agent.local",
                          "999", "--body", "Should not send"], output, errors)
        self.assertEqual(1, status)
        self.assertEqual("", output.getvalue())
        self.assertEqual({"error": "Message not found in that mailbox."}, json.loads(errors.getvalue()))
        self.assertEqual(before, len(server_module.STORE.payload()["messages"]))

    def test_agent_cli_unreachable_server_is_json_error(self) -> None:
        output, errors = StringIO(), StringIO()
        status = run_cli(["mailboxes", "--url", "http://127.0.0.1:1"], output, errors)
        self.assertEqual(1, status)
        self.assertEqual("", output.getvalue())
        self.assertIn("Cannot connect", json.loads(errors.getvalue())["error"])

    def test_contact_api_create_duplicate_validate_and_delete(self) -> None:
        status, _, body = self.request("POST", "/api/contacts", {
            "name": "Builder", "emails": ["builder@agent.local"], "groups": ["Agents"]
        })
        contact = json.loads(body)
        self.assertEqual(201, status)
        self.assertEqual("Builder", contact["name"])
        status, _, _ = self.request("POST", "/api/contacts", {
            "name": "Other", "emails": ["builder@agent.local"], "groups": []
        })
        self.assertEqual(409, status)
        status, _, _ = self.request("POST", "/api/contacts", {"name": "Invalid", "emails": []})
        self.assertEqual(400, status)
        status, _, body = self.request("DELETE", f"/api/contacts/{contact['id']}")
        self.assertEqual(200, status)
        self.assertTrue(json.loads(body)["ok"])
        status, _, _ = self.request("DELETE", f"/api/contacts/{contact['id']}")
        self.assertEqual(404, status)

    def test_malformed_read_id_and_missing_resource(self) -> None:
        status, _, _ = self.request("POST", "/api/messages/not-a-number/read", {})
        self.assertEqual(400, status)
        status, _, _ = self.request("GET", "/missing.txt")
        self.assertEqual(404, status)


if __name__ == "__main__":
    unittest.main()
