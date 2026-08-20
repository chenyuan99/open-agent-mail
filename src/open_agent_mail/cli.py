from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Sequence, TextIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import typer


DEFAULT_URL = "http://127.0.0.1:8787"
app = typer.Typer(help="Run Open Agent Mail or use its agent-oriented JSON CLI.", no_args_is_help=False)


@dataclass
class Output:
    stdout: TextIO = sys.stdout
    stderr: TextIO = sys.stderr


class Client:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode()
        request = Request(f"{self.base_url}{path}", data=data, method=method,
                          headers={"Content-Type": "application/json"} if data is not None else {})
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


def _output(ctx: typer.Context) -> Output:
    return ctx.ensure_object(Output)


def _emit(ctx: typer.Context, value: Any) -> None:
    stream = _output(ctx).stdout
    json.dump(value, stream, ensure_ascii=False)
    stream.write("\n")


def _find_message(state: dict[str, Any], message_id: int, mailbox: str) -> dict[str, Any]:
    message = next((item for item in state["messages"] if item["id"] == message_id and item["mailbox"] == mailbox), None)
    if message is None:
        raise RuntimeError("Message not found in that mailbox.")
    return message


UrlOption = typer.Option(DEFAULT_URL, "--url", envvar="OPEN_AGENT_MAIL_URL", help="Open Agent Mail server URL.")


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context, host: str = "127.0.0.1", port: int = 8787,
         no_browser: bool = typer.Option(False, "--no-browser", help="Do not open the browser.")) -> None:
    if ctx.invoked_subcommand is None:
        from .server import serve
        serve(host, port, no_browser)


@app.command()
def mailboxes(ctx: typer.Context, url: str = UrlOption) -> None:
    _emit(ctx, {"mailboxes": Client(url).request("GET", "/api/state")["mailboxes"]})


@app.command("create-mailbox")
def create_mailbox(ctx: typer.Context, name: str, url: str = UrlOption) -> None:
    _emit(ctx, Client(url).request("POST", "/api/mailboxes", {"name": name}))


@app.command()
def send(ctx: typer.Context, sender: str = typer.Option(..., "--from"),
         recipient: str = typer.Option(..., "--to"), subject: str = typer.Option(...),
         body: str = typer.Option(...), url: str = UrlOption) -> None:
    _emit(ctx, Client(url).request("POST", "/api/messages", {
        "mailbox": sender, "recipient": recipient, "subject": subject, "body": body,
    }))


def _list_messages(ctx: typer.Context, folder: str, mailbox: str, unread: bool, url: str) -> None:
    state = Client(url).request("GET", "/api/state")
    messages = [item for item in state["messages"] if item["mailbox"] == mailbox
                and item["folder"] == folder and (not unread or not item["read"])]
    _emit(ctx, {"messages": sorted(messages, key=lambda item: item["created_at"], reverse=True)})


@app.command()
def inbox(ctx: typer.Context, mailbox: str = typer.Option(...), unread: bool = False,
          url: str = UrlOption) -> None:
    _list_messages(ctx, "inbox", mailbox, unread, url)


@app.command()
def sent(ctx: typer.Context, mailbox: str = typer.Option(...), unread: bool = False,
         url: str = UrlOption) -> None:
    _list_messages(ctx, "sent", mailbox, unread, url)


@app.command("read")
def read_message(ctx: typer.Context, message_id: int, mailbox: str = typer.Option(...),
                 url: str = UrlOption) -> None:
    client = Client(url)
    state = client.request("GET", "/api/state")
    result = _find_message(state, message_id, mailbox)
    client.request("POST", f"/api/messages/{message_id}/read", {})
    _emit(ctx, result)


@app.command()
def reply(ctx: typer.Context, message_id: int, sender: str = typer.Option(..., "--from"),
          body: str = typer.Option(...), subject: str | None = typer.Option(None),
          url: str = UrlOption) -> None:
    client = Client(url)
    state = client.request("GET", "/api/state")
    parent = _find_message(state, message_id, sender)
    recipient = parent["recipient"] if parent["sender"] == sender else parent["sender"]
    reply_subject = subject or (parent["subject"] if parent["subject"].lower().startswith("re:")
                                else f"Re: {parent['subject']}")
    _emit(ctx, client.request("POST", "/api/messages", {
        "mailbox": sender, "recipient": recipient, "subject": reply_subject,
        "body": body, "in_reply_to": message_id,
    }))


def run(argv: Sequence[str], stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr) -> int:
    try:
        app(args=list(argv), prog_name="open-agent-mail", standalone_mode=False, obj=Output(stdout, stderr))
        return 0
    except RuntimeError as error:
        json.dump({"error": str(error)}, stderr)
        stderr.write("\n")
        return 1


def main(argv: Sequence[str] | None = None) -> None:
    raise SystemExit(run(sys.argv[1:] if argv is None else argv))
