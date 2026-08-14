# GitHub-native enforcement

The process reports policy meaning; configure GitHub for the stronger enforcement point:

| Obligation | GitHub mechanism |
|---|---|
| CI/process readiness before merge | Ruleset required status checks (`engineering-process`, tests) |
| Review and protected branch | Branch ruleset; require pull request and approvals |
| Production human approval | Protected Environment required reviewer |
| No deployment self-approval | Environment “prevent self-review” |
| Minimal token bootstrap | Generated assistant files, not branch prose |

The reusable workflow in `reusable-workflows/process-readiness.yml` validates the repository and joins evidence. Repository administrators must configure rulesets and Environments because permissions/plans differ; prompt instructions are not a substitute.

