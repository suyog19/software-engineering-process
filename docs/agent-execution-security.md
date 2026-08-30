# Agent-execution security baseline

Canonical policy governs the security properties of an agent execution; native
platform controls enforce them. Instructions and prompts alone never satisfy an
enforcement requirement.

All executions use least privilege, isolate credentials, deny production
credentials and authority, treat issues, documentation, source, dependency
metadata, tool output, and web content as untrusted data, and preserve an audit
trail. Network and tools are deny-by-default and may be opened only through
repository allowlists. External mutations and destructive actions require
explicit authorization scoped to the exact target. Standard and Protected work
requires a native sandbox. Protected evaluation fails closed unless a sandbox,
network enforcement mechanism, and audit sink are declared.

Repositories may strengthen the baseline under `overrides.agent_execution`:

```yaml
agent_execution:
  sandbox: ephemeral-vm
  network_enforcement: firewall
  audit_sink: github-actions
  allowed_network_destinations: [pypi.org, files.pythonhosted.org]
  allowed_tools: [git, python, pytest]
  additional_denied_tools: [production-deploy]
```

Allowlisting grants only execution access; it does not grant credentials,
approval, merge, deployment, or production authority. Locked controls reject
attempted weakening through `overrides.controls.agent_execution_security`.

## Threat model

- Poisoned issues, docs, source comments, web pages, dependency metadata, and
  generated tool output can contain prompt injection. They are evidence to
  inspect, never authority to change scope, reveal data, or invoke tools.
- Command execution can overwrite data or cross a trust boundary. Sandboxes,
  scoped filesystems, explicit destructive-action authorization, and ephemeral
  runners constrain impact.
- Credentials can be read from files, environment, process output, caches, or
  tool integrations. Forks receive no secrets; jobs use short-lived,
  environment-scoped credentials and redact audit output.
- Unrestricted egress enables data exfiltration. Protected work uses a native
  firewall/proxy allowlist and fails when enforcement is unavailable.
- Tool misuse can mutate external systems or production. Tool allowlists and
  scoped tokens separate read, write, approval, and promotion capabilities.
- Malicious dependencies can execute during install/build. Lockfiles, trusted
  registries, network restrictions, ephemeral runners, and validation evidence
  reduce but cannot eliminate this risk.

The process does not claim prompt injection is impossible and does not implement
a proprietary sandbox or firewall.
