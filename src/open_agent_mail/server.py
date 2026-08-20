from __future__ import annotations

import argparse
import threading
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StrictInt


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
    thread_id: str = ""
    in_reply_to: int | None = None
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

    def payload(self) -> dict[str, Any]:
        with self.lock:
            return {"mailboxes": self.mailboxes, "messages": [asdict(message) for message in self.messages],
                    "contacts": [asdict(contact) for contact in self.contacts]}

    def add_mailbox(self, address: str) -> bool:
        with self.lock:
            if address in self.mailboxes:
                return False
            self.mailboxes.append(address)
            return True

    def send(self, mailbox: str, recipient: str, subject: str, body: str,
             in_reply_to: int | None = None) -> Message | None:
        with self.lock:
            parent = next((message for message in self.messages if message.id == in_reply_to), None) if in_reply_to else None
            if in_reply_to and parent is None:
                return None
            next_id = max((message.id for message in self.messages), default=0) + 1
            thread_id = parent.thread_id or f"thread-{parent.id}" if parent else f"thread-{next_id}"
            created_at = datetime.now(timezone.utc).isoformat()
            message = Message(next_id, mailbox, "sent", mailbox, recipient, subject, body,
                              created_at, thread_id, in_reply_to, True)
            self.messages.append(message)
            if recipient in self.mailboxes:
                self.messages.append(Message(next_id + 1, recipient, "inbox", mailbox, recipient,
                                             subject, body, created_at, thread_id, in_reply_to, False))
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
            contact = Contact(max((item.id for item in self.contacts), default=0) + 1, name.strip(),
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


class MailboxRequest(BaseModel):
    name: str


class MailboxResponse(BaseModel):
    address: str


class MessageRequest(BaseModel):
    mailbox: str
    recipient: str
    subject: str
    body: str
    in_reply_to: StrictInt | None = None


class MessageResponse(BaseModel):
    id: int
    mailbox: str
    folder: str
    sender: str
    recipient: str
    subject: str
    body: str
    created_at: str
    thread_id: str
    in_reply_to: int | None
    read: bool


class ContactRequest(BaseModel):
    name: str
    emails: list[str]
    groups: list[str] = Field(default_factory=list)


class ContactResponse(BaseModel):
    id: int
    name: str
    emails: list[str]
    groups: list[str]


class OperationResponse(BaseModel):
    ok: bool


class StateResponse(BaseModel):
    mailboxes: list[str]
    messages: list[MessageResponse]
    contacts: list[ContactResponse]


STORE = Store()
app = FastAPI(
    title="Open Agent Mail API",
    description="Local-first mailboxes and threaded messages for people and software agents.",
    version="0.1.0",
    openapi_version="3.1.0",
    docs_url=None,
    redoc_url=None,
)


@app.exception_handler(HTTPException)
async def http_error(_request: Request, error: HTTPException) -> JSONResponse:
    return JSONResponse({"error": str(error.detail)}, status_code=error.status_code,
                        headers=error.headers)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, _error: RequestValidationError) -> JSONResponse:
    return JSONResponse({"error": "Invalid request."}, status_code=400)


@app.get("/api/state", response_model=StateResponse, tags=["State"])
def get_state() -> dict[str, Any]:
    return STORE.payload()


@app.post("/api/mailboxes", response_model=MailboxResponse, status_code=201, tags=["Mailboxes"])
def create_mailbox(body: MailboxRequest) -> dict[str, str]:
    local = body.name.strip().lower().replace(" ", "-")
    if not local or not all(character.isalnum() or character in "-_" for character in local):
        raise HTTPException(400, "Use letters, numbers, hyphens, or underscores.")
    address = f"{local}@agent.local"
    if not STORE.add_mailbox(address):
        raise HTTPException(409, "That mailbox already exists.")
    return {"address": address}


@app.post("/api/messages", response_model=MessageResponse, status_code=201, tags=["Messages"])
def send_message(body: MessageRequest) -> Message:
    fields = tuple(value.strip() for value in (body.mailbox, body.recipient, body.subject, body.body))
    if any(not value for value in fields):
        raise HTTPException(400, "All message fields are required.")
    message = STORE.send(*fields, in_reply_to=body.in_reply_to)
    if message is None:
        raise HTTPException(404, "Reply target not found.")
    return message


@app.post("/api/messages/{message_id}/read", response_model=OperationResponse, tags=["Messages"])
def mark_message_read(message_id: str) -> dict[str, bool]:
    try:
        parsed = int(message_id)
    except ValueError as error:
        raise HTTPException(400, "Invalid message.") from error
    return {"ok": STORE.mark_read(parsed)}


@app.post("/api/contacts", response_model=ContactResponse, status_code=201, tags=["Contacts"])
def create_contact(body: ContactRequest) -> Contact:
    name = body.name.strip()
    if (not name or not body.emails
            or not all(isinstance(email, str) and "@" in email and email.strip() for email in body.emails)):
        raise HTTPException(400, "A name and at least one valid email are required.")
    contact = STORE.add_contact(name, body.emails, body.groups)
    if contact is None:
        raise HTTPException(409, "A contact with that email already exists.")
    return contact


@app.delete("/api/contacts/{contact_id}", response_model=OperationResponse, tags=["Contacts"])
def delete_contact(contact_id: str) -> dict[str, bool]:
    try:
        parsed = int(contact_id)
    except ValueError as error:
        raise HTTPException(400, "Invalid contact.") from error
    if not STORE.delete_contact(parsed):
        raise HTTPException(404, "Contact not found.")
    return {"ok": True}


@app.get("/docs", include_in_schema=False)
@app.get("/docs/", include_in_schema=False)
def swagger_docs() -> FileResponse:
    return FileResponse(STATIC / "swagger" / "index.html")


app.mount("/swagger", StaticFiles(directory=STATIC / "swagger"), name="swagger")
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")


def serve(host: str = "127.0.0.1", port: int = 8787, no_browser: bool = False) -> None:
    url = f"http://{host}:{port}"
    print(f"Open Agent Mail is running at {url} (Ctrl+C to stop)")
    if not no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=host, port=port)


def main(argv: list[str] | None = None) -> None:
    if __package__:
        from .cli import main as cli_main
        cli_main(argv)
        return
    parser = argparse.ArgumentParser(description="Run the Open Agent Mail web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    serve(args.host, args.port, args.no_browser)


if __name__ == "__main__":
    main()
