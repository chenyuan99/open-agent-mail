# Agent communication end-to-end test plan

## Objective

Verify that independently invoked agents can exchange bounded, correlated work through Open Agent Mail without losing messages, duplicating work, crossing mailbox boundaries, leaking authority, or entering reply loops.

The canonical workflow is:

```text
Analyst reports → Research Manager → Trader
    → Aggressive → Conservative → Neutral risk review
    → Portfolio Manager final decision
```

LangGraph or another controller chooses the next role. Email transports the work product and records the conversation. A successful test must verify both layers.

## Test environments

| Environment | Purpose | Dependencies | Status |
| --- | --- | --- | --- |
| Unit | Validation, thread identity, local delivery | Python standard library | Available |
| Local integration | HTTP server plus agent CLI | Loopback server | Available |
| Orchestrator integration | TradingAgents nodes invoking mail tools | TradingAgents and model stubs | To build |
| Provider contract | Cloudflare adapter and webhook | Mock HTTP provider | Proposed |
| Staging end-to-end | Real custom-domain delivery | Staging domain and scoped secrets | Proposed |

Production addresses and credentials must never be used in automated tests.

## Canonical test data

- Run: `run-aapl-2026-08-19-001`
- Project: `trading-agents-staging`
- Subject: `[TRADE-REVIEW] [AAPL] 2026-08-19`
- One mailbox per role
- One thread created by the initial handoff and preserved through replies
- Deterministic message fixtures instead of live model prose

Assertions use IDs and structured correlation metadata, not subject parsing alone.

## Gate A: Current local product

| ID | Test | Expected result | Automation |
| --- | --- | --- | --- |
| LOC-01 | Create every role mailbox | Unique normalized addresses | Existing HTTP tests plus table-driven cases |
| LOC-02 | Analyst sends to manager | Sent and unread inbox copies share `thread_id` | Existing store/CLI test |
| LOC-03 | Manager reads and replies | Read state changes; reply preserves thread and parent | Existing CLI test |
| LOC-04 | Complete five-role chain | Expected chronological turns and mailbox copies | Automated store integration test |
| LOC-05 | Unknown reply target | JSON error, exit 1, and no mutation | Automated HTTP and CLI tests |
| LOC-06 | Server unavailable | JSON error on stderr and exit 1 | Automated CLI test |
| LOC-07 | Browser thread view | Chronological, escaped, accessible, responsive | Manual desktop/narrow check |
| LOC-08 | Restart | Test mail disappears and seeds return | Expected until persistence ships |

Gate A passes only when tests, compilation, diff checks, and the browser checklist pass.

## Gate B: TradingAgents orchestration

Use deterministic fake model responses and a recording mail tool. CI must not call a live LLM.

| ID | Test | Expected result |
| --- | --- | --- |
| ORCH-01 | Analyst handoff | Each analyst sends exactly one correlated report to its next role |
| ORCH-02 | Bull/Bear debate | Turns alternate in one thread and stop at the configured limit |
| ORCH-03 | Manager judgment | Manager receives both cases and sends one decision to Trader |
| ORCH-04 | Risk debate | Three risk roles speak in order and stop at the limit |
| ORCH-05 | Portfolio decision | Final decision is produced once and linked to the run/thread |
| ORCH-06 | Missing email | Controller records blocked state and does not silently advance |
| ORCH-07 | Duplicate delivery | Same provider ID or idempotency key causes one agent action |
| ORCH-08 | Crash after claim | No concurrent action; work returns only after lease expiry |
| ORCH-09 | Invalid recipient edge | Policy rejects the handoff before delivery |
| ORCH-10 | Loop attempt | Hop/turn limit stops replies and surfaces a failure |

After every node, compare the email transcript with LangGraph state: reports, active speaker, turn count, thread ID, and final decision must agree.

## Gate C: Security and authorization

| ID | Attack or failure | Required assertion |
| --- | --- | --- |
| SEC-01 | Caller overrides From | Authenticated identity wins or request is rejected |
| SEC-02 | Agent reads another mailbox | No metadata or body is returned |
| SEC-03 | Body requests secrets or authority | Agent refuses; nothing sensitive reaches mail or logs |
| SEC-04 | HTML/script payload | Active content is removed or escaped |
| SEC-05 | Oversized body | Rejected before storage/provider delivery |
| SEC-06 | Hourly limit exceeded | Rejected with retry metadata |
| SEC-07 | Reply to ACK/bounce/auto mail | Automatic reply is suppressed |
| SEC-08 | Hop limit exceeded | Reply rejected and workflow marked blocked |
| SEC-09 | Invalid webhook signature | Rejected before payload parsing |
| SEC-10 | Replayed provider event | One stored message and one action |

Security failures must not print sensitive bodies while reporting errors.

## Gate D: Cloudflare contract

Run against a fake HTTP server before staging.

| ID | Provider behavior | Expected result |
| --- | --- | --- |
| CF-01 | Send accepted | Accepted/queued state and provider ID recorded |
| CF-02 | Transient 429/5xx | Bounded retry scheduled; agent does not sleep |
| CF-03 | Invalid recipient | Terminal failure without retry |
| CF-04 | Timeout after acceptance | Same idempotency key prevents duplicate send |
| CF-05 | Valid Worker webhook | Signature passes; message normalized once |
| CF-06 | Webhook and sync overlap | Both resolve to one provider message |
| CF-07 | Transport kill switch | No external call or inbound mutation |

## Gate E: Staging end-to-end

1. Provision two allowlisted agent identities.
2. Trigger Alpha from a staging task.
3. Send one correlated work request through Cloudflare.
4. Confirm provider acceptance and recipient delivery.
5. Trigger Beta through a verified webhook or one scheduler run.
6. Claim, read, and reply in the original thread.
7. Confirm Alpha receives the reply and the task records message, delivery, claim, and completion IDs.
8. Replay webhook and completion requests to prove idempotency.
9. Disable the transport and prove further delivery is blocked.
10. Revoke staging credentials and retain only redacted evidence.

## Invariants after every turn

- Sender identity matches the authenticated role.
- Recipient belongs to an allowed workflow edge.
- Thread, workspace, project, issue, and run correlation remain unchanged.
- `in_reply_to` identifies a message visible to the sender.
- One logical send creates at most one provider delivery.
- One inbound provider message creates at most one unit of work.
- Turn and hop counters increase exactly once.
- Email content cannot expand task authority.
- Terminal decisions stop automatic replies.
- Logs contain identifiers and error classes, never credentials or routine bodies.

## CI layout and evidence

```text
tests/unit/                 domain, policy, routing, serialization
tests/integration/local/    server + CLI + threads
tests/integration/orch/     fake TradingAgents + recording transport
tests/contract/cloudflare/  fake REST and signed webhooks
tests/e2e/staging/          explicitly enabled staging tests
```

Every test records its ID. CI publishes JUnit results and redacted lifecycle metadata. Staging tests are opt-in and never run for untrusted pull requests.

## Current verification

```powershell
$env:PYTHONPATH = "src"
C:\Python314\python.exe -m unittest discover -s tests -v
C:\Python314\python.exe -m compileall -q src tests
Remove-Item Env:\PYTHONPATH
git diff --check
```

## Exit criteria

- Gate A is required for the local release.
- Gates B and C are required before agents act automatically on mail.
- Gate D is required before Cloudflare is enabled.
- Gate E is required before a production-domain pilot.
- Duplicate action, cross-mailbox disclosure, secret exposure, uncontrolled loops, or an uncorrelated final decision blocks release.
