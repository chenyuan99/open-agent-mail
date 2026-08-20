# Tasks: Migrate HTTP service to FastAPI

- [x] Add FastAPI and Uvicorn runtime dependencies.
- [x] Replace handler routing with typed FastAPI operations.
- [x] Preserve API errors, status codes, static routes, CLI startup, and browser behavior.
- [x] Generate OpenAPI from application models and routes.
- [x] Move HTTP integration tests to a live ephemeral Uvicorn server.
- [x] Run automated compatibility verification against live Uvicorn.
- [x] Build the wheel and verify the live root, docs, and OpenAPI endpoints.
- [ ] Run manual browser verification when a browser surface is available.
- [ ] Sync the capability specification and archive the change.
