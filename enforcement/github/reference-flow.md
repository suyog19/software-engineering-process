# Reference assurance flow

`reusable-workflows/reference-assurance.yml` demonstrates the complete
`trusted diff → classify → evaluate → objective validation → authenticated
independent review → readiness` lifecycle. Every job checks out the exact head,
installs the lock SHA, and exchanges exact-SHA evidence as short-retention
artifacts outside the source tree. A changed head has a different artifact name
and reruns every job, so earlier readiness cannot carry forward.

The Lean path requires only configured focused validation and one authenticated
fresh-context review artifact. Standard additionally requires integration
validation and functional QA evidence. Protected requires focused, integration,
negative, and security validation, the remaining policy predicates, an
egress-enforced sandbox/audit sink, and manual owner production authorization.
The reference workflow never merges or deploys.

Declare exact repository-relative YAML paths below `.github/workflows/` in
`repository.trusted_ci_workflows` and `repository.authorized_review_workflows`.
The adapter parses `GITHUB_WORKFLOW_REF` as `owner/repository/path@ref`, requires
the manifest repository, and compares normalized paths for equality. Display
names, fragments, traversal, other repositories, and feature refs fail closed.

A ref is trusted only when it is an immutable 40-character commit SHA, or the
configured protected/default branch with `GITHUB_REF_PROTECTED=true`. A workflow
SHA equal to the assessed target cannot bootstrap its own authorization; a
reviewed authorization change affects later runs. `pull_request` is diagnostic
only. `pull_request_target` and `workflow_dispatch` must use the protected base
definition. `workflow_call` also requires `GITHUB_CALLER_WORKFLOW_REF`, with both
caller and callee allowlisted. Fork review runs in the authorized base repository.
Reruns bind both run ID and attempt.

An independent reviewer runs `review-attest` from a protected review workflow
after inspecting the objective artifact, then uploads
`process-independent-review-<SHA>`. If the reviewer edits, they emit no verdict;
the new SHA repeats the entire flow.

For local reproduction, use exact commits:

```bash
engineering-process evaluate --base "$BASE_SHA" --head "$HEAD_SHA"
engineering-process explain --base "$BASE_SHA" --head "$HEAD_SHA"
```

Trusted `run-validation` and `review-attest` intentionally require GitHub Actions;
local runs may reproduce commands but cannot mint trusted provenance.

Forks do not receive secrets. A maintainer must approve the base-repository
review workflow, and the target fork SHA must remain fetchable. Artifact download
across runs needs `actions: read`; private forks may require an explicitly scoped
token. Missing permissions, artifacts, provenance, or retained logs fail
readiness rather than falling back to committed JSON.
