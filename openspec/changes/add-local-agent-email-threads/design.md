# Design: Local agent email threads

The in-memory store remains authoritative. A send always creates a sent record; if the recipient matches a local mailbox it also creates an unread inbox record. Both copies share a `thread_id`. A reply references a visible message ID with `in_reply_to` and inherits its thread. The browser derives a mailbox-scoped conversation from that identifier. LangGraph or another orchestrator remains responsible for choosing the next role, bounding turns, and invoking the HTTP API.
