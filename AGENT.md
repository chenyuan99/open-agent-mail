# Open Agent Mail agent guide

## Mission

Maintain a small, local-first inbox for communication between people and software agents. Preserve the zero-runtime-dependency architecture unless a specification change explicitly requires otherwise.

## Source of truth

Read [SPEC.md](SPEC.md) before changing behavior. Update the specification in the same change whenever product behavior or an HTTP contract changes.

## Architecture

- `src/open_agent_mail/server.py`: in-memory domain store, HTTP API, static-file server, and CLI.
- `src/open_agent_mail/static/`: framework-free browser interface.
- `tests/`: standard-library unit and HTTP integration tests.
- `.agents/skills/open-agent-mail/`: reusable workflow for future agents.

## Working rules

- Keep the app runnable on Python 3.12+ without runtime packages.
- Treat all request data as untrusted. Validate input and escape data rendered in HTML.
- Keep API errors in the form `{"error": "message"}` with an appropriate HTTP status.
- Do not add durable storage accidentally; the current store intentionally resets on restart.
- Preserve keyboard access, responsive layout, and semantic HTML.
- Add or update tests for every behavior change.

## Verification

Run from the repository root:

```powershell
$env:PYTHONPATH = "src"
C:\Python314\python.exe -m unittest discover -s tests -v
C:\Python314\python.exe -m compileall -q src tests
Remove-Item Env:\PYTHONPATH
```

For a manual check:

```powershell
C:\Python314\python.exe src\open_agent_mail\server.py --no-browser
```

Open <http://127.0.0.1:8787> and exercise mailbox switching, search, message reading, composing, and sending.
