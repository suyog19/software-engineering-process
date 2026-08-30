# Contributing

Material policy, schema, workflow, adapter, or release changes must review and update `docs/capability-status.md`. If status does not change, state why in the pull request. Schema changes require compatibility/upgrade notes and tests.

Open an issue before implementation. Keep policy technology-neutral and encode obligations rather than generic engineering advice. Add tests for inheritance, classification, evidence, adapters, and migration impact. Run `pytest`, build/install the wheel, and exercise the CLI outside the checkout. Pull requests must explain why new machinery is necessary and identify native alternatives considered.
