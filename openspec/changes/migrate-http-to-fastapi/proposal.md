# Migrate HTTP service to FastAPI

## Why

Authentication, provider webhooks, durable repositories, and generated API documentation need typed validation and composable HTTP dependencies that would otherwise duplicate framework behavior in the standard-library handler.

## What changes

- Replace `BaseHTTPRequestHandler` and `ThreadingHTTPServer` with FastAPI and Uvicorn.
- Define typed request and response models that generate OpenAPI automatically.
- Preserve existing paths, payloads, error shape, CLI, static client, and in-memory store behavior.
- Exercise integration tests against a real ephemeral Uvicorn server.

## Impact

FastAPI, Uvicorn, Pydantic, and Starlette become runtime dependencies. The concurrent Typer CLI migration is preserved and Typer is declared explicitly. The frontend remains framework-free and build-free.
