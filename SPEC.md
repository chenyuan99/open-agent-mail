# Open Agent Mail specification

## 1. Product intent

Open Agent Mail is a local web inbox for short messages exchanged between humans and software agents. The initial release optimizes for immediate local use, legible status, and a small trusted codebase.

## 2. Runtime

- Support Python 3.12 or newer.
- Require no third-party runtime dependencies.
- Listen on `127.0.0.1:8787` by default.
- Accept `--host`, `--port`, and `--no-browser` command-line options.
- Store data in memory. Restarting the process restores seeded data.

## 3. Domain model

A mailbox is a unique address ending in `@agent.local`. A message contains:

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | integer | Process-local unique identifier |
| `mailbox` | string | Owning mailbox |
| `folder` | `inbox` or `sent` | View containing the message |
| `sender` | string | Sender display address or name |
| `recipient` | string | Recipient address |
| `subject` | string | Non-empty subject |
| `body` | string | Non-empty plain-text body |
| `created_at` | ISO-8601 string | UTC creation time |
| `read` | boolean | Whether the message has been opened |

Mailbox names accept ASCII letters, numbers, hyphens, and underscores. Input is lowercased, spaces become hyphens, and the `@agent.local` suffix is added by the server.

## 4. HTTP contract

### `GET /api/state`

Return `200` with `{ "mailboxes": [...], "messages": [...] }`.

### `POST /api/mailboxes`

Accept `{ "name": string }`. Return `201` with `{ "address": string }`. Return `400` for invalid names and `409` for duplicates.

### `POST /api/messages`

Accept non-empty `mailbox`, `recipient`, `subject`, and `body` strings. Create a read message in the selected mailbox's `sent` folder and return it with `201`. Return `400` when any required field is empty.

### `POST /api/messages/{id}/read`

Mark an existing message as read and return `200` with `{ "ok": true }`. Unknown identifiers return `200` with `{ "ok": false }`; malformed identifiers return `400`.

Static files are served from the packaged `static` directory. Requests must not escape that directory.

## 5. Interface behavior

- Show every mailbox and allow switching without a page reload.
- Show the selected address, unread inbox count, and approximate storage usage.
- Provide Inbox and Sent tabs and client-side full-text search.
- Sort visible messages newest first.
- Opening a message shows its complete content and marks it read.
- Compose requires recipient, subject, and body. Successful sends select the Sent view and show confirmation.
- `Ctrl+K` or `Cmd+K` opens Compose; Escape closes open dialogs.
- Adapt to narrow mobile layouts without horizontal page scrolling.

## 6. Security and privacy

- Bind to loopback unless the operator explicitly selects another host.
- Escape message-derived values before inserting HTML.
- Serve only files whose resolved path is below the static root.
- Do not transmit data to external services.

## 7. Acceptance criteria

The standard-library test suite must cover the store, static page, complete API happy path, validation failures, duplicate mailboxes, read state, and missing resources. Python compilation and tests must pass before handoff.

## 8. Deferred scope

Durable storage, authentication, SMTP/IMAP, attachments, deletion, threading, remote agent protocols, and production deployment are intentionally deferred.
