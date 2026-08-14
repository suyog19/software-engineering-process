# Repository adoption

1. Install a released package or run from an immutable process checkout.
2. Run `engineering-process --root <repo> init --profile generic|frontend|backend`.
3. Add only local differences to `.engineering/process.yaml`.
4. Commit the manifest, lock, adapters, workflow, and materialized Skills.
5. Configure GitHub rulesets/environments using `enforcement/github/README.md`.
6. For each change, classify, evaluate, execute with selected Skills, emit exact-SHA evidence, and run readiness.

Repository-local technology is deliberately opaque to policy. Put commands under `overrides.validation.commands`; add sensitive paths/characteristics and domain triggers when they strengthen classification. Never copy the canonical policy into the manifest.

For upgrades, run `engineering-process upgrade --version X --revision SHA --dry-run`, review inherited/profile/generated-file changes and conflicts, then apply from the reviewed target process checkout. A central update never mutates an active repository automatically.

