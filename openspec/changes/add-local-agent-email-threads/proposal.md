# Add local agent email threads

## Why

Agents need a company-like handoff channel that can be exercised locally before external transports and credentials are introduced.

## What changes

- Deliver messages addressed to another local mailbox into its inbox.
- Correlate new messages and replies with stable thread identifiers.
- Let users read and reply to a complete conversation in the browser.
- Demonstrate a bounded TradingAgents-style role conversation.
- Provide JSON-first CLI commands for agent mailbox operations.

## Out of scope

External SMTP/IMAP, durable storage, authentication, autonomous polling, and unrestricted agent loops.
