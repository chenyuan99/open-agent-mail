---
name: open-agent-mail
description: Build, modify, diagnose, or verify the Open Agent Mail local inbox in this repository. Use for its Python HTTP API, in-memory mailbox/message model, vanilla HTML/CSS/JavaScript interface, CLI behavior, product specification, or automated tests.
---

# Work on Open Agent Mail

1. Read `AGENT.md` and `SPEC.md` at the repository root.
2. Inspect the relevant implementation and existing tests before editing.
3. Keep behavioral changes aligned across the server, browser client, specification, and tests.
4. Preserve the standard-library-only Python runtime and framework-free frontend unless the user changes that constraint.
5. Validate request data server-side and escape untrusted values before HTML insertion.
6. Run the commands in the verification section of `AGENT.md`.
7. For interface changes, start the local server and manually verify the affected flow at desktop and narrow viewport widths.

Prefer focused patches over architectural expansion. Treat persistence, authentication, mail protocols, and deployment as deferred scope unless explicitly requested.
