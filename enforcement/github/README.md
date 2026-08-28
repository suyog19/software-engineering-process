# GitHub-native enforcement

The process reports policy meaning; configure GitHub for the stronger enforcement point:

| Obligation | GitHub mechanism |
|---|---|
| CI/process readiness before merge | Ruleset required status checks (`engineering-process`, tests) |
| Review and protected branch | Branch ruleset; require pull request and status checks; require human approvals when repository governance calls for them |
| Production human authorization | Manual owner/authorized-maintainer merge or promotion; optionally a protected Environment required reviewer |
| No autonomous production | Do not grant agents or automation production approval or merge authority |
| Minimal token bootstrap | Generated assistant files, not branch prose |

The reusable workflow in `reusable-workflows/process-readiness.yml` validates the repository and joins evidence. Repository administrators must configure rulesets and Environments because permissions, plans, and collaborator topology differ; prompt instructions are not a substitute. A required Environment reviewer plus self-review prevention is a valid stronger control when a distinct authorized human exists. It is not the canonical meaning of the human production boundary and is not mandatory for an owner-controlled repository.
