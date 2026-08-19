# Tasks: Add Multica agent-to-agent email

## 1. Foundations

- [ ] 1.1 Add transport-neutral domain types for identities, messages, delivery states, claims, and processing results.
- [ ] 1.2 Introduce repository interfaces without changing the current in-memory default.
- [ ] 1.3 Implement durable transactional storage and schema migrations.
- [ ] 1.4 Add unique constraints for provider deduplication and outbound idempotency.
- [ ] 1.5 Add unit tests for state transitions, constraints, and migration rollback.

## 2. Identity and policy

- [ ] 2.1 Implement workspace/agent/mailbox identity mapping and credential resolution.
- [ ] 2.2 Enforce operation scopes, sender binding, recipient allowlists, and disabled identities.
- [ ] 2.3 Implement rolling send/recipient limits, body limits, and retry-after responses.
- [ ] 2.4 Implement thread hop tracking and automatic-reply suppression.
- [ ] 2.5 Add mailbox, workspace, and transport kill switches.
- [ ] 2.6 Test all policy rejection scenarios from the capability spec.

## 3. MCP surface

- [ ] 3.1 Implement MCP authentication with one scoped identity per credential.
- [ ] 3.2 Implement `send_email` with required idempotency keys.
- [ ] 3.3 Implement bounded `list_messages` and safe `get_message`.
- [ ] 3.4 Implement atomic `claim_message` with opaque lease tokens and expiry.
- [ ] 3.5 Implement idempotent `complete_message` with Multica result correlation.
- [ ] 3.6 Add optional `reply_email` only after loop controls pass tests.
- [ ] 3.7 Add tool-contract, authorization, and secret-redaction tests.

## 4. External transport

- [ ] 4.1 Select the first provider and document staging credentials and domain prerequisites.
- [ ] 4.2 Implement the outbound adapter and normalized provider status mapping.
- [ ] 4.3 Implement webhook signature verification before body parsing.
- [ ] 4.4 Implement inbound normalization and provider-message deduplication.
- [ ] 4.5 Add bounded transient retries and permanent-failure handling through scheduled work.
- [ ] 4.6 Test against mocked provider contracts, then a staging domain.

## 5. Multica integration

- [ ] 5.1 Verify MCP support for the selected Multica coding runtimes.
- [ ] 5.2 Configure staging Alpha and Beta agents using file/stdin MCP configuration.
- [ ] 5.3 Add sender instructions and validate Issue/Chat-triggered delivery.
- [ ] 5.4 Add a 30-minute receiver Autopilot with bounded filters and per-run processing limits.
- [ ] 5.5 Add allowlisted webhook-to-Issue automation for optional immediate handling.
- [ ] 5.6 Verify Multica Issue comments capture message, delivery, processing, and failure IDs without secrets.

## 6. Operations and security

- [ ] 6.1 Add structured audit events and operational metrics.
- [ ] 6.2 Add dashboards and alerts for failures, signature rejection, throttling, loops, and backlog.
- [ ] 6.3 Document credential rotation, transport shutdown, recovery, and incident response.
- [ ] 6.4 Run prompt-injection, replay, duplicate, concurrency, loop, and rate-limit tests.
- [ ] 6.5 Perform a human-approved staging pilot with only the Alpha/Beta pair.

## 7. Completion

- [ ] 7.1 Map every behavioral scenario to automated or staged integration evidence.
- [ ] 7.2 Update user and operator documentation with the final configuration surface.
- [ ] 7.3 Sync the future-state `agent-email` spec into `openspec/specs/agent-email/spec.md`.
- [ ] 7.4 Archive this change only after all required tasks pass and the capability is shipped.
