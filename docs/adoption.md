# Repository adoption

1. Install a released package or run from an immutable process checkout.
2. Run `engineering-process --root <repo> init --profile generic|frontend|backend`.
3. Add only local differences to `.engineering/process.yaml`.
4. Commit the manifest, lock, adapters, workflow, and materialized Skills.
5. Configure GitHub rulesets/environments using `enforcement/github/README.md`.
6. For each change, classify, evaluate, execute with selected Skills, emit exact-SHA evidence, and run readiness.

Repository-local technology is deliberately opaque to policy. Put commands under `overrides.validation.commands`; add sensitive paths/characteristics and domain triggers when they strengthen classification. Never copy the canonical policy into the manifest.

## Mature repository migration

Initialization is non-destructive. If `AGENTS.md`, `CLAUDE.md`, or the process validation workflow is repository-owned, normal `init` stops before creating `.engineering/process.yaml`. Do not use `--force` to bypass this boundary.

Use this reviewed workflow:

1. Inventory existing assistant, architecture, branch/release, validation, security, product/UX, and deployment guidance. Identify copied generic policy versus genuine repository-specific context.
2. Keep canonical requirements in this process. Keep local mechanics and stronger constraints in repository-owned documents. Existing `overrides` remain the only mechanism for validation commands, classification additions, UX triggers, controls, and native enforcement.
3. Commit or otherwise preserve a baseline so the migration can be reviewed.
4. Run `engineering-process --root <repo> init --profile frontend --adopt-existing-context`. The command moves existing `AGENTS.md` and/or `CLAUDE.md` verbatim into `docs/engineering/local-context/`, declares them in `local_context`, and writes compact generated bootstraps. It refuses to replace a repository-owned workflow.
5. Split or rename the preserved documents as useful, then update `local_context`. Each entry has a category, repository-relative path, and optional contextual `load_when` instruction:

   ```yaml
   local_context:
     - category: operating_contract
       path: docs/engineering/operating-contract.md
       load_when: load before branch, issue, or release workflow changes
     - category: architecture
       path: docs/architecture/
       load_when: load for changes affecting component boundaries
     - category: ux_product_design
       path: docs/ux/ux-gates.md
       load_when: load for user-visible changes
   ```

6. Review the full diff. Confirm branch responsibilities, issue-first workflow, agent roles, architecture/deployment rules, Senior UX Designer responsibilities, UX Gates A-D, and local implementation/review conventions remain referenced and readable.
7. Run `engineering-process validate`. Missing paths, invalid context structure, stale generated bootstraps, modified generated files, and locked-control override attempts fail validation.

Local-context documents add detail and mechanics; they do not override the Effective Obligation Set. Progressive `load_when` hints keep the bootstraps compact and avoid loading every document for every change.

For upgrades, run `engineering-process upgrade --version X --revision SHA --dry-run`, review inherited/profile/generated-file changes, preserved local-context paths, and conflicts, then apply from the reviewed target process checkout. Upgrade verifies generated-file hashes before replacement and refuses modified or repository-owned targets. It never rewrites files referenced by `local_context`. A central update never mutates an active repository automatically.
