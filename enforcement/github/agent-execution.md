# GitHub agent-execution mapping

| Canonical requirement | GitHub enforcement |
|---|---|
| Least privilege | Set workflow/job `permissions: contents: read`; grant individual write scopes only to a separately authorized job. |
| Credential isolation | Withhold secrets from forks and pull-request code; use OIDC and protected Environment secrets with short lifetimes. |
| Sandbox | Use ephemeral GitHub-hosted runners or isolated, single-use self-hosted runners; never a persistent production runner. |
| Network deny/allowlist | Enforce egress on a runner firewall/proxy. GitHub YAML and instructions alone do not satisfy Protected isolation. |
| Tool allowlist | Preinstall/allow approved actions and commands; pin third-party actions to immutable SHAs for Protected use. |
| Untrusted content | Do not interpolate issue, PR, branch, file, or tool-output text into shell commands. Fork code runs without secrets. |
| External mutation | Separate read-only validation from mutation jobs; require Environment/ruleset approval and scoped tokens. |
| Auditability | Retain workflow/job logs, artifact digests, run attempt, actor, workflow ref, and environment decisions. |
| Production separation | Environment approval and manual human promotion remain mandatory; agents and automation cannot approve or promote. |

Untrusted-fork workflows require maintainer approval and run with read-only
permissions. Protected repositories must configure an egress-enforced runner and
declare its mechanism in the manifest; otherwise policy evaluation fails closed.
