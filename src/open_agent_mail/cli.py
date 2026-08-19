from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Sequence, TextIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


COMMANDS = {"mailboxes", "create-mailbox", "send", "inbox", "sent", "read", "reply"}


class Client:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode()
        request = Request(
            f"{self.base_url}{path}", data=data, method=method,
            headers={"Content-Type": "application/json"} if data is not None else {},
        )
        try:
            with urlopen(request, timeout=10) as response:
                return json.load(response)
        except HTTPError as error:
            try:
                detail = json.load(error)
            except (json.JSONDecodeError, UnicodeDecodeError):
                detail = {"error": error.reason}
            raise RuntimeError(detail.get("error", error.reason)) from error
        except URLError as error:
            raise RuntimeError(f"Cannot connect to {self.base_url}: {error.reason}") from error


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Agent CLI for Open Agent Mail")
    sub = root.add_subparsers(dest="command", required=True)

    def command(name: str, help_text: str) -> argparse.ArgumentParser:
        result = sub.add_parser(name, help=help_text)
        result.add_argument("--url", default=os.environ.get("OPEN_AGENT_MAIL_URL", "http://127.0.0.1:8787"))
        return result

    command("mailboxes", "List mailbox addresses")
    create = command("create-mailbox", "Create a local agent mailbox")
    create.add_argument("name")

    send = command("send", "Send a new email")
    send.add_argument("--from", dest="sender", required=True)
    send.add_argument("--to", dest="recipient", required=True)
    send.add_argument("--subject", required=True)
    send.add_argument("--body", required=True)

    for name in ("inbox", "sent"):
        listing = command(name, f"List {name} messages")
        listing.add_argument("--mailbox", required=True)
        listing.add_argument("--unread", action="store_true")

    read = command("read", "Read one message by ID")
    read.add_argument("message_id", type=int)
    read.add_argument("--mailbox", required=True)

    reply = command("reply", "Reply to a message in its thread")
    reply.add_argument("message_id", type=int)
    reply.add_argument("--from", dest="sender", required=True)
    reply.add_argument("--body", required=True)
    reply.add_argument("--subject")
    return root


def _find_message(state: dict[str, Any], message_id: int, mailbox: str) -> dict[str, Any]:
    message = next((item for item in state["messages"] if item["id"] == message_id and item["mailbox"] == mailbox), None)
    if message is None:
        raise RuntimeError("Message not found in that mailbox.")
    return message


def run(argv: Sequence[str], stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr) -> int:
    args = parser().parse_args(list(argv))
    client = Client(args.url)
    try:
        if args.command == "mailboxes":
            result: Any = {"mailboxes": client.request("GET", "/api/state")["mailboxes"]}
        elif args.command == "create-mailbox":
            result = client.request("POST", "/api/mailboxes", {"name": args.name})
        elif args.command == "send":
            result = client.request("POST", "/api/messages", {
                "mailbox": args.sender, "recipient": args.recipient,
                "subject": args.subject, "body": args.body,
            })
        elif args.command in {"inbox", "sent"}:
            state = client.request("GET", "/api/state")
            messages = [item for item in state["messages"] if item["mailbox"] == args.mailbox
                        and item["folder"] == args.command and (not args.unread or not item["read"])]
            result = {"messages": sorted(messages, key=lambda item: item["created_at"], reverse=True)}
        elif args.command == "read":
            state = client.request("GET", "/api/state")
            result = _find_message(state, args.message_id, args.mailbox)
            client.request("POST", f"/api/messages/{args.message_id}/read", {})
        else:
            state = client.request("GET", "/api/state")
            parent = _find_message(state, args.message_id, args.sender)
            recipient = parent["recipient"] if parent["sender"] == args.sender else parent["sender"]
            subject = args.subject or (parent["subject"] if parent["subject"].lower().startswith("re:")
                                       else f"Re: {parent['subject']}")
            result = client.request("POST", "/api/messages", {
                "mailbox": args.sender, "recipient": recipient, "subject": subject,
                "body": args.body, "in_reply_to": args.message_id,
            })
        json.dump(result, stdout, ensure_ascii=False)
        stdout.write("\n")
        return 0
    except RuntimeError as error:
        json.dump({"error": str(error)}, stderr)
        stderr.write("\n")
        return 1


def main(argv: Sequence[str] | None = None) -> None:
    values = list(sys.argv[1:] if argv is None else argv)
    if values and values[0] in COMMANDS:
        raise SystemExit(run(values))
    from .server import main as serve
    serve(values)
