# Open Agent Mail project context

## Purpose

Open Agent Mail is a local-first inbox for messages between humans and software agents. It provides a typed FastAPI/Uvicorn HTTP service, in-memory mailboxes/messages/contacts, and a framework-free browser client.

## Constraints

- Python 3.12 or newer.
- Runtime dependencies are limited to FastAPI, Typer, Uvicorn, and their transitive requirements unless a change explicitly revises this constraint.
- Loopback binding by default.
- Untrusted input is validated server-side and escaped before HTML insertion.
- Current storage is intentionally process-local and non-durable.
- Provider integrations remain behind transport-neutral boundaries.

## OpenSpec workflow

Current shipped behavior belongs in `openspec/specs/<capability>/spec.md`. Proposed behavior belongs in `openspec/changes/<change-name>/` with proposal, future-state specs, design, and tasks. After implementation and verification, sync the future-state specs into `openspec/specs/` and archive the change with a date prefix.

The root `SPEC.md` remains the compact specification for the shipped local application until its capabilities are fully migrated into OpenSpec.
