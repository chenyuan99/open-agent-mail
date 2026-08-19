from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


STATIC = Path(__file__).with_name("static")


@dataclass
class Message:
    id: int
    mailbox: str
    folder: str
    sender: str
    recipient: str
    subject: str
    body: str
    created_at: str
    read: bool = False


@dataclass
class Contact:
    id: int
    name: str
    emails: list[str]
    groups: list[str]


class Store:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.mailboxes = ["hello@agent.local", "research@agent.local"]
        self.messages = [
            Message(1, self.mailboxes[0], "inbox", "Open Agent Mail", self.mailboxes[0],
                    "Your agent inbox is ready", "Welcome! This inbox is ready for agents, tools, and humans. Compose a message to try it out.",
                    "2026-08-19T12:10:00+00:00"),
            Message(2, self.mailboxes[0], "inbox", "Scout Agent", self.mailboxes[0],
                    "Research run complete", "I reviewed the launch checklist. The brief and competitive notes are ready for your review.",
                    "2026-08-19T10:42:00+00:00"),
            Message(3, self.mailboxes[1], "inbox", "Planner Agent", self.mailboxes[1],
                    "Three sources need review", "Three sources have conflicting dates. I flagged them instead of guessing.",
                    "2026-08-18T17:20:00+00:00"),
        ]
        self.contacts = [
            Contact(1, "Scout Agent", ["scout@agent.local"], ["Agents"]),
            Contact(2, "Project Team", ["team@example.com"], ["Work"]),
        ]

    def payload(self) -> dict:
        with self.lock:
            return {"mailboxes": self.mailboxes, "messages": [asdict(m) for m in self.messages],
                    "contacts": [asdict(c) for c in self.contacts]}

    def add_mailbox(self, address: str) -> bool:
        with self.lock:
            if address in self.mailboxes:
                return False
            self.mailboxes.append(address)
            return True

    def send(self, mailbox: str, recipient: str, subject: str, body: str) -> Message:
        with self.lock:
            message = Message(max((m.id for m in self.messages), default=0) + 1, mailbox, "sent", mailbox,
                              recipient, subject, body, datetime.now(timezone.utc).isoformat(), True)
            self.messages.append(message)
            return message

    def mark_read(self, message_id: int) -> bool:
        with self.lock:
            for message in self.messages:
                if message.id == message_id:
                    message.read = True
                    return True
            return False

    def add_contact(self, name: str, emails: list[str], groups: list[str]) -> Contact | None:
        with self.lock:
            normalized = [email.strip().lower() for email in emails if email.strip()]
            if any(email in contact.emails for contact in self.contacts for email in normalized):
                return None
            contact = Contact(max((c.id for c in self.contacts), default=0) + 1, name.strip(),
                              normalized, sorted({group.strip() for group in groups if group.strip()}))
            self.contacts.append(contact)
            return contact

    def delete_contact(self, contact_id: int) -> bool:
        with self.lock:
            for index, contact in enumerate(self.contacts):
                if contact.id == contact_id:
                    self.contacts.pop(index)
                    return True
            return False


STORE = Store()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[open-agent-mail] {fmt % args}")

    def _json(self, value: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        size = int(self.headers.get("Content-Length", "0"))
        try:
            return json.loads(self.rfile.read(size) or b"{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/state":
            self._json(STORE.payload())
            return
        file = STATIC / ("index.html" if path == "/" else path.lstrip("/"))
        if not file.is_file() or STATIC not in file.resolve().parents:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = file.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        path, body = urlparse(self.path).path, self._body()
        if path == "/api/mailboxes":
            local = str(body.get("name", "")).strip().lower().replace(" ", "-")
            if not local or not all(c.isalnum() or c in "-_" for c in local):
                self._json({"error": "Use letters, numbers, hyphens, or underscores."}, HTTPStatus.BAD_REQUEST)
                return
            address = f"{local}@agent.local"
            if not STORE.add_mailbox(address):
                self._json({"error": "That mailbox already exists."}, HTTPStatus.CONFLICT)
                return
            self._json({"address": address}, HTTPStatus.CREATED)
            return
        if path == "/api/messages":
            required = ("mailbox", "recipient", "subject", "body")
            if any(not str(body.get(key, "")).strip() for key in required):
                self._json({"error": "All message fields are required."}, HTTPStatus.BAD_REQUEST)
                return
            message = STORE.send(*(str(body[key]).strip() for key in required))
            self._json(asdict(message), HTTPStatus.CREATED)
            return
        if path == "/api/contacts":
            name, emails, groups = str(body.get("name", "")).strip(), body.get("emails", []), body.get("groups", [])
            if not name or not isinstance(emails, list) or not emails or not all(
                isinstance(email, str) and "@" in email and email.strip() for email in emails
            ) or not isinstance(groups, list):
                self._json({"error": "A name and at least one valid email are required."}, HTTPStatus.BAD_REQUEST)
                return
            contact = STORE.add_contact(name, emails, groups)
            if contact is None:
                self._json({"error": "A contact with that email already exists."}, HTTPStatus.CONFLICT)
                return
            self._json(asdict(contact), HTTPStatus.CREATED)
            return
        if path.startswith("/api/messages/") and path.endswith("/read"):
            try:
                message_id = int(path.split("/")[3])
            except (ValueError, IndexError):
                self._json({"error": "Invalid message."}, HTTPStatus.BAD_REQUEST)
                return
            self._json({"ok": STORE.mark_read(message_id)})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/api/contacts/"):
            try:
                contact_id = int(path.split("/")[3])
            except (ValueError, IndexError):
                self._json({"error": "Invalid contact."}, HTTPStatus.BAD_REQUEST)
                return
            if not STORE.delete_contact(contact_id):
                self._json({"error": "Contact not found."}, HTTPStatus.NOT_FOUND)
                return
            self._json({"ok": True})
            return
        self.send_error(HTTPStatus.NOT_FOUND)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Open Agent Mail web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"Open Agent Mail is running at {url} (Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
