# Architecture

## Boundaries

The canonical YAML policy and profiles describe organizational intent, authority, mandatory perspectives, prohibited actions, evidence, and gates. The semantic layer performs only the parts schemas cannot: override monotonicity, deterministic/semantic classification combination, obligation selection, generated-file drift checks, evidence joins, and sufficiency invariants.

The platform does not plan implementation steps, manage agent conversations, choose code structure, or recreate CI/GitHub enforcement. Adapters are compact generated bootstraps. Skills contain only specialist procedure. GitHub remains responsible for branch/ruleset, status-check, and environment approval enforcement.

## Trusted classification

Declared intent, repository policy, changed paths/config, deterministic rules, and semantic judgment are combined. Classification strength is ordered `Lean < Standard < Protected`. Deterministic Protected matches and unresolved Protected values force Protected. Semantic/declarative input may strengthen but never downgrade the result. The explanation output preserves signals and rationale.

## Evidence and independence

Evidence follows the in-toto Statement shape with one `gitCommit` subject and a Software Signal predicate type. Every predicate carries the process version/revision, producer identity/context, verdict, and timestamp. Readiness joins predicates only for the requested repository SHA and pinned process revision.

Independent review requires a fresh context distinct from implementation plus structured v2 basis: issue/acceptance criteria, exact full diff, applicable context, validation evidence, counterexample search, findings, residual risks, and unverified areas. Model/vendor diversity is not used as a proxy for independence. V1 evidence remains historical compatibility data and cannot satisfy new v2 obligations. Producer trust comes from the Phase 1 out-of-band transport index.

## Solution Sufficiency

The steward triages non-mandatory recommendations, but mandatory categories are mechanically promoted to `must_address`. Readiness can stop with optional deferred/rejected improvements when acceptance, controls, tests, required reviews, blocking findings, and residual-risk recording are complete.

## Implementation decisions

- YAML + JSON Schema + Python semantic layer; no OPA/Rego because current policy composition is small and explicit.
- Single-profile manifests today; composite/full-stack is deferred until a real repository needs conflict semantics.
- Exact Git SHA is authoritative; semantic version is human-readable compatibility metadata.
- Skills are materialized under `.engineering/skills`, a vendor-neutral location. Thin adapters can later synchronize platform-native locations.
- No cryptographic signing, cross-repository coordinator, or custom agent runtime without measured need.
