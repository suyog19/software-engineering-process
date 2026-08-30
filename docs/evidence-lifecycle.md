# Exact-revision evidence lifecycle

This is the authoritative operational contract for process evidence. Evidence
JSON is data, never proof of its own producer. Canonical policy defines required
predicates and producer classes; a platform adapter verifies transport identity
and supplies a separate trust index.

## Sequence and storage

```text
push H -> trusted diff(base,H) -> classification(H, process P)
  -> CI/authenticated verdicts(H,P,repository) -> immutable artifact store
  -> readiness joins artifacts + verified provenance -> merge status
  -> merge creates M (H is stale) -> deployment-release(M,P) in release store
```

The manifest, lock, and policy are source controlled. Pre-merge classification,
test, specialist, review, approval, and readiness evidence are not committed:
GitHub stores them as immutable workflow artifacts or attestations keyed by
repository, head SHA, process revision, workflow run and attempt. Equivalent
platforms may use an external store with the same keys. Deployment evidence is
post-merge evidence and is retained separately from the readiness join.

`readiness` reads predicates from downloaded artifacts. Authenticated/trusted
status comes only from a verified transport index outside the checkout. It maps
each evidence content digest to repository, target revision, capability,
producer class, and platform identity. GitHub records also carry workflow,
run/attempt, and job identity. Repository-authored producer fields cannot elevate
evidence.

## Ordering, invalidation, and recovery

1. Resolve immutable base/head commits and classify their complete Git diff.
2. Publish classification before dependent jobs; every producer uses that exact
   head and locked process revision.
3. Collect all predicates and provenance, then run the readiness join.
4. Any new head is a different key and immediately invalidates prior readiness.
   Merge and post-merge release commits require their own evidence.

A rerun creates a new immutable attempt. Any failing or conflicting verdict in a
selected collection fails the join; success does not erase failure. Resolve a
contradiction with a clean run and an explicitly selected, auditable attempt. A
missing, expired, malformed, inaccessible, or unverifiable artifact fails closed:
restore/fetch it or rerun; never copy evidence to a new SHA. Retention follows
the platform policy and for Protected work should cover merge plus the audit
period. Expired evidence requires rerun.

Fork runs may create asserted diagnostics, but receive neither secrets nor trusted
status. Protected readiness runs in the base repository after authorization,
against the fork head SHA, with read-only source permissions. Human and agent
verdicts enter through authenticated reviews, protected workflow dispatch, or an
external service preserving actor/event audit identity; committed JSON remains
an assertion.

## Threat model

- Contributors can create, replace, and replay repository JSON, but cannot create
  authenticated/trusted provenance that way.
- Workflow authors can alter repository workflows. Protected trusted CI is
  restricted to approved workflow identities/refs and environment or ruleset;
  workflow changes themselves classify Protected.
- Platform administrators are inside the platform trust boundary. Audit logs and
  artifact attestations reduce replacement risk.
- Compromised credentials may impersonate their holder. Adapters require least
  privilege, OIDC issuer/audience checks, and short-lived credentials.
- Repository, exact SHA, process revision, content digest and run identity prevent
  replay. Wrong repository/workflow/job and unauthorized capability fail.

Lean v1 evidence remains proportionate and may be `asserted` where policy allows.
Standard and Protected progressively require authenticated/trusted provenance per
`policy/evidence/producer-authorization.yaml`. No self-declared v1 field is ever
upgraded to trusted status.

## Process upgrades and bootstrap trust

The executable revision changes only through `engineering-process upgrade`, which
updates the manifest, lock, generated workflow and snapshot together. Generated
and reusable workflows install the exact 40-character lock SHA and pass it back
to validation. Missing, floating, unavailable, or mismatched revisions fail.
The initial checkout, Git host, and action runner are bootstrap trust assumptions.
