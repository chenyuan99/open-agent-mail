# HTTP Runtime Specification

### Requirement: Typed ASGI service

The application SHALL expose its HTTP and static interfaces through FastAPI and SHALL run them with Uvicorn.

#### Scenario: Existing client upgrades

- **GIVEN** a client using the documented local API or CLI
- **WHEN** the FastAPI-based version starts
- **THEN** existing paths, successful payloads, status codes, and error envelopes SHALL remain compatible

### Requirement: Generated API contract

The OpenAPI document SHALL be generated from the registered FastAPI operations and typed request/response models.

#### Scenario: Route model changes

- **GIVEN** a typed API operation changes
- **WHEN** `/openapi.json` is requested
- **THEN** the generated document SHALL reflect the current operation without a separately maintained schema

### Requirement: Production-shaped integration tests

HTTP integration tests SHALL exercise the ASGI application through a live ephemeral Uvicorn server.

#### Scenario: CLI test sends mail

- **GIVEN** the test Uvicorn server is running on loopback
- **WHEN** the CLI sends, lists, reads, or replies
- **THEN** the request SHALL pass through the same ASGI stack used by the executable server
