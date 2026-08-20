# API Documentation Specification

### Requirement: Machine-readable API contract

The server SHALL expose an OpenAPI 3.1 document describing every current HTTP API operation and its JSON schemas.

#### Scenario: Agent discovers the API

- **GIVEN** Open Agent Mail is running
- **WHEN** a client requests `/openapi.json`
- **THEN** the server SHALL return JSON with an OpenAPI 3.1 version
- **AND** every supported API path SHALL be represented

### Requirement: Local interactive documentation

The server SHALL provide Swagger UI without requiring browser access to a third-party CDN.

#### Scenario: Developer opens documentation

- **GIVEN** Open Agent Mail is running without internet access
- **WHEN** a developer opens `/docs`
- **THEN** Swagger UI SHALL load from same-origin vendored assets
- **AND** SHALL use `/openapi.json` for interactive requests
