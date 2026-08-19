# Local Agent Email Threads Specification

### Requirement: Local delivery

Messages sent to an existing local agent mailbox SHALL create a sent copy and an unread recipient inbox copy.

#### Scenario: Agent sends a handoff

- **GIVEN** two local agent mailboxes
- **WHEN** one sends a message to the other
- **THEN** both mailbox views SHALL contain their respective copy with the same thread ID

### Requirement: Threaded replies

A reply SHALL reference an existing message and inherit its stable thread identifier.

#### Scenario: Agent replies to a handoff

- **GIVEN** a delivered local message
- **WHEN** its recipient replies using `in_reply_to`
- **THEN** the reply SHALL appear in the same conversation
- **AND** an unknown reply target SHALL be rejected

### Requirement: Agent command line tools

The system SHALL expose JSON-output commands for mailbox discovery, creation, sending, listing, reading, and threaded replies.

#### Scenario: Agent completes an email handoff

- **GIVEN** the local server is running
- **WHEN** an agent sends a message and another agent lists, reads, and replies through the CLI
- **THEN** every successful command SHALL return parseable JSON
- **AND** the reply SHALL retain the original thread identifier
