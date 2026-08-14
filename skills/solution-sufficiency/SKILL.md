---
name: solution-sufficiency
description: Triage specialist feedback and establish the smallest solution sufficient for requirements, controls, and material risk.
---
# Solution Sufficiency

Classify each recommendation as `must_address`, `worth_addressing_now`, `defer`, or `reject`. You cannot defer or reject correctness defects, locked controls, security/privacy requirements, mandatory accessibility/UX, Protected assurance, blocking findings, approved contracts, or Product Owner acceptance criteria.

Ask whether removing an addition would fail acceptance, violate a control, create material risk, or materially harm maintainability. If not, default to defer/reject. Stop when acceptance, mandatory controls/tests/reviews, blocking findings, and residual-risk recording are complete—even if optional improvements remain. Emit concise exact-revision `solution-sufficiency/v1` evidence.

