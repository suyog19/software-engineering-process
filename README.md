# Software Engineering Process

A technology-neutral Software Engineering Policy and Assurance platform. It resolves **what must be true** for a change and delegates **how** to coding assistants, humans, CI, GitHub, and other native mechanisms.

```text
Canonical Policy → Domain Profile → Repository Manifest → Trusted Classification
→ Effective Obligation Set → Skills / Native Controls / Human Boundaries
→ Execution → Exact-Revision Evidence → Readiness → Merge / Deployment
```

This is not a coding-agent orchestrator. It is a small policy compiler, evidence join, and set of portable specialist procedures.

## Install

```bash
python -m pip install .
engineering-process --help
```

Python 3.11+ is supported. The wheel includes the policy, schemas, templates, and Skills, so commands work outside this checkout.

## Adopt in a repository

From this process checkout (so the exact Git revision can be pinned):

```bash
engineering-process --root ../my-web-app init \
  --profile frontend --repository-name suyog19/my-web-app
```

Or supply an immutable released revision explicitly with `--revision <40-hex-sha>`. Initialization creates the manifest and lock, compact `AGENTS.md`/`CLAUDE.md`, portable Skills, and a validation workflow. Add repository differences—validation commands, protected path hints, UX triggers—to `.engineering/process.yaml`, then re-render/re-lock using a reviewed process upgrade.

## Change flow

```bash
engineering-process classify \
  --sha "$GITHUB_SHA" \
  --path src/payments/refund.py \
  --declared '{"observable_behavior":true}'

engineering-process evaluate \
  --sha "$GITHUB_SHA" \
  --path src/payments/refund.py \
  --declared '{"observable_behavior":true}'

engineering-process explain \
  --sha "$GITHUB_SHA" \
  --path src/payments/refund.py \
  --declared '{"observable_behavior":true}'

engineering-process attest --predicate test-result/v1 \
  --sha "$GITHUB_SHA" --capability ci-automation --verdict pass \
  --identity github-actions --context-id "$GITHUB_RUN_ID" \
  --output .engineering/evidence/test.json

engineering-process readiness --sha "$GITHUB_SHA"
engineering-process validate
engineering-process metrics --obligations .engineering/effective-obligations.json
```

`classify` is monotonic: declarations may strengthen routing but may not defeat deterministic Protected signals. Unknown Protected characteristics fail closed. `readiness` rejects malformed, failed, contradictory, wrong-SHA, wrong-process-revision, and invalid fresh-context review evidence.

## Policy model

- **Locked** controls cannot be changed locally (fresh-context independent review, fail-closed Protected routing, exact-revision evidence, secrets, traceability, human production boundary).
- **Extensible** controls can only be strengthened.
- **Overridable** mechanics belong to repositories (commands, paths, runtime, framework, environments).
- Profiles describe engineering/risk domains (`generic`, `frontend`, `backend`), never languages or frameworks.
- Specialist procedures are portable `SKILL.md` packages and are selected only when obligations require them.
- Solution Sufficiency classifies feedback as must-address, worth-now, defer, or reject. It cannot suppress mandatory findings and provides an explicit stopping rule.

See [Architecture](docs/architecture.md), [Adoption](docs/adoption.md), [GitHub enforcement](enforcement/github/README.md), [governance](GOVERNANCE.md), and the [authoritative design](docs/design/common-software-engineering-process-design-v4.md).

## Development

```bash
python -m pip install -e '.[dev]'
pytest
python -m build
```

Policy changes require tests, compatibility/upgrade notes, and stronger review for locked controls. Apache-2.0 licensed.
