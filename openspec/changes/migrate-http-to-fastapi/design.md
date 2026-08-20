# Design: FastAPI migration

`server.py` retains the process-local store and exposes an ASGI `app`. Pydantic models define request and response boundaries. Exception handlers normalize framework validation and HTTP errors to the existing `{ "error": "message" }` contract. API and documentation routes are registered before static mounts. Uvicorn is invoked only by the server CLI; tests run the same app on an ephemeral loopback port.

The migration intentionally does not add persistence, authentication, background queues, or asynchronous store methods. Those capabilities can later enter through FastAPI dependencies without changing the current behavior.
