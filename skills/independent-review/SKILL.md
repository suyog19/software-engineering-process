---
name: independent-review
description: Perform the final engineering review from a fresh context independent of implementation.
---
# Independent review

Start in a fresh review context with read-only access to the completed change, issue, resolved obligations, and evidence. Do not inherit implementation reasoning as trusted fact.

Use this reproducible basis:

1. Read the issue/product intent and every acceptance criterion.
2. Inspect the complete exact base-to-head diff, including renames and deletions.
3. Load every applicable repository-context source named by the manifest.
4. Examine the test-result evidence, commands, categories, skips/retries, and immutable logs; reproduce material checks when needed.
5. Seek concrete counterexamples and negative cases rather than only confirming the implementation narrative.
6. Record machine-readable findings (`severity`, `blocking`, location, rationale), residual risks, and every unverified area.
7. A blocking finding or unverified area prevents an unqualified pass.

The final reviewer is read-only. If the reviewer edits the change, the review ends without verdict; after the new commit, start a new fresh context and repeat the full review against the new SHA. Earlier-SHA review never carries forward.

The producer context ID must differ from the implementation context ID and `freshContext` must be true. A different vendor is optional diversity, not proof of independence. Emit exact-revision `independent-review/v2` evidence with issue, full-diff, context, validation, counterexample, unverified-area, finding, and residual-risk basis.
