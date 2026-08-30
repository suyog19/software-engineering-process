# Repository adoption

1. Install a released package or run from an immutable process checkout.
2. Run `engineering-process --root <repo> init --profile generic|frontend|backend`.
3. Add only local differences to `.engineering/process.yaml`.
4. Commit the manifest, lock, adapters, workflow, and materialized Skills.
5. Configure GitHub rulesets/environments using `enforcement/github/README.md`.
6. For each change, classify, evaluate, execute with selected Skills, emit exact-SHA evidence, and run readiness.

Repository-local technology is deliberately opaque to policy. Put commands under `overrides.validation.commands`; add sensitive paths/characteristics and domain triggers when they strengthen classification. Never copy the canonical policy into the manifest.

## Locked process upgrades

CI executes the immutable Git SHA in `.engineering/process.lock`, never a floating
package, tag, or branch. Change it only through a reviewed
`engineering-process upgrade --version VERSION --revision 40_HEX_SHA`. The
upgrade refreshes the manifest, lock, generated workflow, and policy snapshot
together. Missing, unavailable, floating, or inconsistent revisions fail closed.
The initial checkout and runner are the bootstrap trust boundary. Evidence
transport and v1 compatibility are defined in the [exact-revision evidence
lifecycle](evidence-lifecycle.md).

### Schema v2 and adapters

Process 1.3.0 upgrades schema-v1 manifests to strict schema v2. Legacy
`overrides.technology` moves to the explicit versioned `legacy/technology`
extension; platform mechanics move from `overrides.native_enforcement` to
`adapters.github`. Unknown v2 fields are rejected. Canonical policy now expresses
semantic readiness, protected-branch, and production-boundary obligations while
the versioned GitHub adapter selects status names, branches, environments, and
runner labels. Stronger local controls remain valid; locked-control weakening is
still rejected.

Optional `adapters.github_copilot.scoped_instructions` generate compact
path-scoped `.github/instructions/*.instructions.md` files from canonical process
identity and declared local-context paths. They are hash-locked and non-canonical.
Remove adapter configuration during a reviewed upgrade to remove only unchanged
generated files; modified or repository-owned files are refused.

### Phase 2 evidence migration

Process 1.1.0 obligation sets require `test-result/v2` and `independent-review/v2`.
`test-result/v1` and `independent-review/v1` remain schema-valid only for stored
historical obligations that explicitly require v1; they do not satisfy v2.
Configure validation commands with `focused`, `integration`, `negative`, or
`security` categories and use `run-validation` in trusted CI. Use the protected
`review-attest` workflow after reviewing the exact diff and v2 test evidence. A
process upgrade changes obligations only with the new locked process revision.

Validation commands are executable argument strings, not shell programs; pipes,
redirection, interpolation, and compound shell expressions are intentionally not
supported. Put complex validation in a reviewed repository script and configure
that script as the command.

Standard/Protected agent execution requires a native sandbox; Protected also
requires declared network enforcement and an audit sink. See the [security
baseline](agent-execution-security.md) and [GitHub
mapping](../enforcement/github/agent-execution.md).

## Production authority and independent review

The human production boundary and independent review are separate controls. Every change still requires fresh-context, implementation-independent review evidence. Production authorization and promotion remain manual human actions, and automation or agents may not perform them. For an owner-controlled repository, the owner's explicit authorization and manual merge or promotion satisfy the human boundary; a second human GitHub reviewer is not implicitly required. Repositories with multiple authorized maintainers may configure a stronger branch or Environment reviewer gate.

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
