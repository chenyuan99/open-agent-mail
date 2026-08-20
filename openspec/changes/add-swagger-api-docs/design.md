# Design: Swagger API documentation

FastAPI generates the OpenAPI document from typed request/response models and registered routes. Swagger UI 5.32.11 assets are vendored under the existing static root and loaded only from same-origin paths. `/docs` maps to the local UI and `/openapi.json` uses FastAPI's generated schema. No CDN, telemetry, or external browser request is introduced.
