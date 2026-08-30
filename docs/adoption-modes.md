# Progressive adoption modes

Modes describe operational maturity, never delivery risk and never alternate meanings of locked controls.

| Mode | Target users | Prerequisites | Guarantees | Limitations |
|---|---|---|---|---|
| Foundation | New/small repositories | Manifest, lock, generated bootstrap, validation workflow | Locked policy/version drift checks | No claim of authenticated end-to-end evidence |
| Assured | Mature or solo repositories | Foundation + categorized validation, trusted CI/review workflow allowlists, GitHub adapter | Automated Lean evidence and authenticated review/readiness | No claim of Protected agent isolation |
| Protected | Sensitive repositories | Assured + sandbox, network enforcement, audit sink | Protected execution fails closed and human production boundary remains | Native controls must be operated by repository owner |
| Governed | Multi-maintainer/process-improvement programs | Protected + optional metrics enabled + maintained critical context | Aggregated outcome feedback and explicit truth ownership | Metrics cannot rank individuals |

Run `engineering-process adoption-report`. A configured target above achieved prerequisites is diagnostic and makes `validate` fail. Transitions are incremental reviewed manifest/lock upgrades; optional metrics/adapters can be removed in a reviewed upgrade. Locked controls never weaken. A solo owner can manually authorize/promote production while independent review remains a separate fresh-context procedure.

Examples: a new repository begins Foundation; a mature repository maps existing CI into Assured; a solo maintainer uses Assured/Protected with owner-controlled production; a multi-maintainer repository may reach Governed. Lean work in Assured uses trusted diff, automatic CI test evidence, one authenticated independent review, and readiness—no hand-authored routine test JSON.
