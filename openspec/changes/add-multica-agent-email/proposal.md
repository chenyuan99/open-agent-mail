# Add Multica agent-to-agent email

## Why

Multica agents can collaborate through Issues, comments, Chat, and Autopilots, but they do not receive native email inboxes or remain alive waiting for notifications. Open Agent Mail needs a controlled MCP and webhook integration so independently triggered agents can exchange durable, correlated work handoffs through external mailboxes without leaking credentials or creating mail loops.

## What changes

- Add externally backed mailbox identities mapped one-to-one to Multica workspace agents.
- Add a transport-neutral email MCP surface for sending, listing, reading, claiming, completing, and optionally replying to messages.
- Add authenticated inbound webhooks and provider adapters for SMTP/IMAP or an email API.
- Add durable state, idempotency, processing leases, delivery states, correlation metadata, audit events, and operator controls.
- Add a Multica trigger model for one-time sends, scheduled polling through Autopilots, and verified webhook-to-Issue automation.
- Enforce sender identity, recipient allowlists, message limits, replay protection, loop prevention, and prompt-injection boundaries independently of agent prompts.

## Capabilities

### New capabilities

- `agent-email`: controlled agent mailbox identity, MCP operations, inbound ingestion, Multica correlation, and safety policy.

### Modified capabilities

- None. The current local mailbox behavior remains the default until the proposed integration is enabled.

## Impact

- Introduces durable storage and authentication, both currently deferred in the root specification.
- Adds an MCP server process or MCP endpoint plus at least one external mail transport.
- Adds provider credentials, webhook secrets, operational monitoring, and incident-response responsibilities.
- Requires staging configuration in Multica and validation against the chosen coding runtime's MCP support.

## Out of scope

- Bulk or marketing email.
- Autonomous mailbox or DNS provisioning.
- Automatic execution of attachments or untrusted HTML.
- Replacing Multica Issues and comments as the authoritative work record.
- Exactly-once delivery across the public email network; processing is idempotent over at-least-once ingestion.
