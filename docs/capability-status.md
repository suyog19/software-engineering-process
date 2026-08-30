# Capability status

Current process release: **1.3.0**.

Status terms: **implemented** is executable and tested; **partial** works with stated prerequisites/limits; **experimental** is usable but compatibility may change; **designed** has an accepted contract but no complete implementation; **deferred** is intentionally postponed with tracked rationale. Material implementation and release changes must update this matrix.

| Capability | Status | Limits / prerequisites |
|---|---|---|
| Locked policy inheritance and upgrades | implemented | Immutable Git revision and reviewed upgrade required. |
| Trusted Git classification | implemented | Full Git history/base must be available. |
| Exact-SHA evidence and producer trust | implemented | Standard/Protected require out-of-band platform provenance. |
| Agent-execution security | partial | Policy and GitHub mapping implemented; adopters supply native sandbox/egress enforcement. |
| End-to-end GitHub reference flow | implemented | Repository configures authorized workflow refs and review Environment. |
| Outcome metrics | experimental | Optional repository aggregation; completeness depends on supplied events. |
| Delegation assessment | experimental | Advisory only; does not grant authority. |
| Dependency assurance | partial | Signals/obligations implemented; ecosystem-native commands supply registry/security facts. |
| Context truth maintenance | implemented | Deterministic hooks only; no LLM assertion is accepted as proof. |
| Progressive adoption modes | implemented | Modes describe achieved infrastructure, not weaker controls. |
| Lean/Standard/Protected assurance profiles | implemented | Delivery assurance remains separate from adoption mode and delegation. |
| Strict v2 manifest/extensions and GitHub adapter | implemented | v1 remains migration-compatible; v2 required for strict separation. |
| Optional scoped GitHub Copilot instructions | implemented | Generated, hash-locked, compact, non-canonical. |
| Cross-repository coordination | deferred | Out of scope; see epic #7 non-goals and future measured need. |
| Additional native assistant formats | designed | Add only from stable semantics; track follow-up after #23. |

The historical [target architecture](design/common-software-engineering-process-design-v4.md) remains a design reference. It is not evidence that every described capability is delivered.
