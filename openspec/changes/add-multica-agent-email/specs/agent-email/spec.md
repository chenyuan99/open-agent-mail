# Agent Email Specification

## Purpose

Define verifiable behavior for safe email exchange between Multica-managed agents through Open Agent Mail and an external mail transport.

## Requirements

### Requirement: Stable mailbox identity

The system SHALL map each active agent mailbox to exactly one Multica workspace and agent, and SHALL derive the outbound sender from the authenticated identity rather than caller input.

#### Scenario: Authenticated sender sends mail

- **GIVEN** Agent Alpha is authenticated for mailbox `alpha-agent@agents.example.com`
- **WHEN** Alpha sends a message through the MCP server
- **THEN** the provider From address SHALL be `alpha-agent@agents.example.com`
- **AND** the caller SHALL NOT be able to override it

#### Scenario: Archived agent attempts mail access

- **GIVEN** an agent or its mailbox is disabled or archived
- **WHEN** its credential is used for any email tool
- **THEN** the system SHALL reject the request before accessing the provider

### Requirement: Scoped MCP tools

The system SHALL expose separate tools for sending, listing, reading, claiming, and completing messages, with authorization scoped by workspace, agent, mailbox, and operation.

#### Scenario: Receiver lists matching work

- **GIVEN** Agent Beta may read only `beta-agent@agents.example.com`
- **WHEN** Beta lists unprocessed messages from Alpha with subject tag `[LOG-REPORT]`
- **THEN** the system SHALL return bounded message summaries matching every filter
- **AND** SHALL NOT return another mailbox's messages

#### Scenario: Unauthorized operation

- **GIVEN** a token lacks outbound permission
- **WHEN** its agent calls `send_email`
- **THEN** the system SHALL reject the call without provider delivery

### Requirement: Idempotent outbound delivery

The system SHALL require an idempotency key for agent-originated messages and SHALL prevent a repeated key within the same mailbox from creating another provider delivery.

#### Scenario: Ambiguous send is retried

- **GIVEN** an initial send may have succeeded but its response timed out
- **WHEN** the agent repeats `send_email` with the same idempotency key
- **THEN** the system SHALL return the original message and delivery result
- **AND** SHALL NOT send another email

### Requirement: Durable inbound ingestion

The system SHALL normalize provider messages into durable records and deduplicate by provider and provider message identifier.

#### Scenario: Webhook and mailbox sync overlap

- **GIVEN** a provider webhook has stored a message
- **WHEN** a later IMAP or provider sync encounters the same provider message ID
- **THEN** the system SHALL reference the existing record
- **AND** SHALL NOT create duplicate work

#### Scenario: Invalid webhook signature

- **GIVEN** an inbound webhook has a missing, invalid, or expired signature
- **WHEN** it reaches the ingestion endpoint
- **THEN** the system SHALL reject it before parsing message content
- **AND** SHALL record a security event without storing the body

### Requirement: Exclusive processing lease

The system SHALL require a receiver to atomically claim an unprocessed message with a bounded lease before acting on it.

#### Scenario: Concurrent receiver runs

- **GIVEN** two Beta runs discover the same unprocessed message
- **WHEN** both attempt to claim it
- **THEN** exactly one claim SHALL succeed
- **AND** the other run SHALL skip the message

#### Scenario: Receiver crashes

- **GIVEN** a receiver claimed a message and its run ended without completion
- **WHEN** the lease expires
- **THEN** a later authorized run MAY claim the message

### Requirement: Idempotent completion

The system SHALL record a terminal processing state with the Multica run and resulting Issue or comment identifiers, and repeated completion SHALL not duplicate side effects.

#### Scenario: Completion is repeated

- **GIVEN** a message is already marked processed by a run
- **WHEN** the same completion request is repeated
- **THEN** the system SHALL return the stored completion result unchanged

### Requirement: Explicit Multica triggers

The integration SHALL run receiving agents only through supported Multica triggers and SHALL NOT assume agents receive notifications or remain alive between runs.

#### Scenario: Thirty-minute inbox polling

- **GIVEN** Beta must inspect mail every 30 minutes
- **WHEN** the workflow is configured
- **THEN** a Multica Autopilot or external scheduler SHALL start a discrete Beta run every 30 minutes
- **AND** the agent SHALL NOT sleep while waiting for the next interval

#### Scenario: Inbound message requests immediate work

- **GIVEN** a valid webhook stores a message for Beta
- **WHEN** immediate processing is enabled
- **THEN** an allowlisted automation SHALL create or update a Multica Issue and trigger Beta
- **AND** arbitrary message content SHALL NOT directly start an unrestricted run

### Requirement: Correlated work handoffs

The system SHALL correlate each agent work message with its Multica workspace, Issue, and run using stored metadata independent of subject parsing.

#### Scenario: Receiver processes a report

- **GIVEN** a `[LOG-REPORT]` message contains valid correlation metadata for Beta's workspace
- **WHEN** Beta claims the message
- **THEN** Beta SHALL update the linked Issue with progress and evidence
- **AND** completion SHALL store the resulting Multica identifiers

#### Scenario: Message has no valid workspace link

- **GIVEN** a message is unlinked, cross-workspace, or spoofed
- **WHEN** the receiver evaluates it
- **THEN** the system SHALL quarantine or ignore it
- **AND** SHALL NOT create agent work

### Requirement: Enforced sending policy

The transport SHALL enforce rate, recipient, size, and content policies independently of agent instructions.

#### Scenario: Hourly rate exceeded

- **GIVEN** the default mailbox limit is five outbound messages per rolling hour
- **WHEN** the mailbox requests a sixth message
- **THEN** the system SHALL reject it before provider delivery
- **AND** SHALL return retry-after metadata

#### Scenario: Recipient is not allowlisted

- **GIVEN** a work-handoff recipient is outside the mailbox allowlist
- **WHEN** the agent calls `send_email`
- **THEN** the system SHALL reject the recipient before provider delivery

#### Scenario: Body exceeds policy

- **GIVEN** normalized text exceeds 256 KiB
- **WHEN** an agent sends or ingests the message
- **THEN** the system SHALL reject or quarantine it according to direction

### Requirement: Automated loop prevention

The system SHALL limit automated reply depth and SHALL suppress replies to acknowledgements, bounces, bulk messages, and auto-submitted messages.

#### Scenario: Hop limit reached

- **GIVEN** an agent thread already contains three automated hops
- **WHEN** another automated reply is requested
- **THEN** the system SHALL reject the reply
- **AND** SHALL expose the rejection to the linked Multica Issue

#### Scenario: Acknowledgement received

- **GIVEN** an inbound message has type `[ACK]`
- **WHEN** an automatic reply rule evaluates it
- **THEN** no reply SHALL be generated

### Requirement: Untrusted message handling

The system and receiving agents SHALL treat email headers, bodies, HTML, and attachments as untrusted data that cannot expand the triggering task's authority.

#### Scenario: Email requests a secret

- **GIVEN** an allowlisted sender's message asks Beta to reveal a token
- **WHEN** Beta processes the message
- **THEN** Beta SHALL refuse the request
- **AND** SHALL NOT expose secrets in email, files, logs, or Multica comments

#### Scenario: HTML message is received

- **GIVEN** an inbound message contains HTML
- **WHEN** it is presented to an agent or user
- **THEN** the system SHALL omit or sanitize active content
- **AND** SHALL provide a safe normalized text representation

### Requirement: Auditable lifecycle

The system SHALL record identity, correlation, policy decision, provider status, claim, completion, and error metadata for every message action without including routine message bodies or credentials in logs.

#### Scenario: Operator investigates failed delivery

- **GIVEN** a provider permanently rejects a recipient
- **WHEN** an operator inspects the audit record
- **THEN** the record SHALL identify mailbox, agent, Multica Issue/run, provider message, policy decision, and failure class
- **AND** credentials and body content SHALL be absent

### Requirement: Bounded failure recovery

The system SHALL classify transient and permanent failures, use bounded retry with jitter for transient failures, and SHALL NOT keep an agent run alive to wait for retry time.

#### Scenario: Provider throttles a send

- **GIVEN** the provider returns a transient rate limit
- **WHEN** the adapter handles the response
- **THEN** the system SHALL record retry eligibility and a future retry time
- **AND** a scheduler SHALL trigger later work instead of sleeping in the agent run

#### Scenario: Recipient is permanently invalid

- **GIVEN** the provider reports a permanent invalid-recipient failure
- **WHEN** delivery status is processed
- **THEN** the system SHALL mark the message failed
- **AND** SHALL update the linked Issue without automatic retry

### Requirement: Operator control

The system SHALL provide kill switches for each mailbox, workspace, and external transport.

#### Scenario: Transport incident

- **GIVEN** an operator disables the external transport
- **WHEN** any agent attempts to send or ingest mail
- **THEN** the system SHALL prevent external mail activity
- **AND** SHALL preserve queued state for investigation
