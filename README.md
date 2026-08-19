# Open Agent Mail

A local-first inbox for messages between people and software agents. It includes multiple agent mailboxes, inbox and sent views, search, read state, and message composition, with no runtime dependencies.

## Run

```powershell
python -m open_agent_mail.server
```

When running directly from a fresh checkout, install the package first:

```powershell
python -m pip install -e .
open-agent-mail
```

The app opens at <http://127.0.0.1:8787>. Use `--no-browser`, `--host`, or `--port` to customize startup.
