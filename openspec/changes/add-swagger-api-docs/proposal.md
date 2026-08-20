# Add Swagger API documentation

## Why

Agent developers need a discoverable, interactive description of the local HTTP contract without reading server implementation code.

## What changes

- Expose an OpenAPI 3.1 document at `/openapi.json`.
- Serve a pinned, local Swagger UI at `/docs`.
- Document every current HTTP operation, request, response, and domain schema.

## Out of scope

Authentication flows, external API hosting, client generation, and provider-specific endpoints.
