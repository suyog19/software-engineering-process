# Common Software Engineering Process with Repository Inheritance — Research-Backed Design (V4)

# 1. Purpose

> **Version 4 status.** This revision incorporates external evidence from software engineering standards, policy-as-code practice, software-supply-chain attestation standards, current coding-assistant capabilities, human-centred design guidance, and recent empirical research on coding and multi-agent systems. Mature standards and primary product documentation are used as architectural anchors; recent 2025–2026 research is treated as emerging evidence to motivate safeguards and measurement rather than as permanent doctrine. See Section 49.

This document defines the problem and proposed solution for establishing a **single, common software engineering process** that can be reused across multiple software repositories while still allowing each repository to adapt the process to its own needs.

The immediate motivation is the observed divergence between the current frontend and backend repositories. Both repositories follow disciplined software engineering practices, but they have evolved independently:

- the frontend uses a relatively lightweight, fixed-role agent workflow;
- the backend uses a more sophisticated, risk-adaptive process with explicit role invocation, approval boundaries, evidence requirements, builder/reviewer separation, and stronger assurance for sensitive changes.

The goal is not to force every repository to use the same detailed workflow. The goal is to establish **one common engineering process with explicit extension points**, so that frontend, backend, and future repositories inherit a shared engineering philosophy without duplicating or drifting away from it.

This direction is consistent with established software-engineering and control-framework practice. ISO/IEC/IEEE 12207:2026 defines a common software life-cycle process framework that can be applied across different organizational and project contexts, while NIST SSDF and NIST control-baseline/overlay guidance demonstrate the pattern of defining shared high-level practices or controls and tailoring them to specific environments rather than rewriting the full framework for every system.[^R1][^R2][^R3]

---

# 2. Problem Statement

## 2.1 Current state

At present, software engineering process is largely defined inside individual repositories through files such as:

- `AGENTS.md`
- `CLAUDE.md`
- `.codex/agents/*`
- `.codex/workflows/*`
- GitHub Actions
- repository-specific conventions and validation scripts

This has worked well while the number of repositories is small. However, it creates several structural problems as the engineering environment grows.

### Problem 1: Process duplication

Each repository independently defines concepts such as:

- issue-first development;
- branch and pull-request discipline;
- human approval boundaries;
- agent roles;
- review requirements;
- Definition of Done;
- production promotion;
- evidence requirements;
- security constraints;
- builder/reviewer separation.

Even when two repositories intend to follow the same principle, the rule is copied and maintained independently.

Over time, copied process definitions naturally diverge.

---

## 2.2 Frontend and backend have already diverged

The current frontend and backend repositories illustrate the issue.

The frontend process is relatively lightweight and uses a mostly fixed cast:

- Product Owner;
- Scrum Master / Orchestrator;
- Team Lead / Architect;
- Developer;
- QA / Reviewer;
- GitHub Actions.

The backend process has evolved further and introduces:

- delivery classification;
- Lean, Standard, and Protected profiles;
- conditional role invocation;
- Product Owner Assistant;
- Team Lead / Architect;
- Engineering Manager;
- Functional QA;
- Non-Functional QA;
- Independent Reviewer;
- explicit builder selection;
- exact-head evidence;
- durable approval records;
- stronger human approval boundaries;
- fail-closed handling of missing or stale evidence.

Neither model is inherently wrong.

The backend has greater operational, security, financial, authentication, infrastructure, and data risks, so it reasonably requires stronger assurance.

The frontend has lower average risk and should not inherit the entire backend ceremony for every change.

The problem is that these two processes currently evolve as **separate systems**, rather than as profiles of a shared software engineering model.

---

## 2.3 Missing process capabilities can lead to late correction

The frontend also illustrates another class of problem: some specialist capability may be absent from the formal process even though the product repeatedly needs it.

For example, user-facing pages may be technically correct but later require a separate UX improvement pass.

This means a specialist such as a **Senior UX Designer** should participate when the nature of a change requires that capability.

The important point is not merely to add another agent name.

The process should formally define:

- when UX expertise is required;
- what the UX role owns;
- what evidence it produces;
- whether UX approval is required before implementation;
- whether UX conformance is rechecked after implementation.

This is a general problem. Future projects may require other specialists:

- security architect;
- data architect;
- performance engineer;
- accessibility specialist;
- model risk reviewer;
- domain expert.

A repository-specific process should be able to add these roles without rewriting the entire engineering system.

---

## 2.4 New repositories have no clean inheritance mechanism

A future repository should not need to answer from scratch:

- What is our branch model?
- Are issues mandatory?
- Can the implementation agent review its own work?
- What is a Protected change?
- What evidence is required?
- Who may approve production?
- How do we record residual risk?
- Which roles exist?
- How are agent roles invoked?
- What constitutes merge readiness?

Copying `AGENTS.md` from an older repository is not a reliable solution.

It creates:

- version drift;
- accidental inheritance of irrelevant rules;
- stale agent assignments;
- inconsistent improvements across repositories;
- unclear ownership of engineering standards.

---

## 2.5 Repository-specific variation is necessary

A common process cannot mean identical workflow everywhere.

Different repositories legitimately differ in:

- technology stack;
- build system;
- test commands;
- deployment mechanism;
- infrastructure;
- branch names;
- security exposure;
- user-experience requirements;
- financial impact;
- data sensitivity;
- regulatory obligations;
- runtime environments;
- external providers;
- required specialist roles.

Therefore, the solution must support **inheritance plus controlled override**.

---

## 2.6 Process inheritance can create a token-cost problem

There is an additional constraint specific to agentic software engineering.

If every coding agent is required to read:

- the entire common process;
- the full frontend/backend profile;
- every agent role;
- every workflow;
- every approval policy;
- every repository-specific rule;

then the engineering process itself becomes an expensive context payload.

This creates several risks:

1. unnecessary token consumption;
2. slower agent startup;
3. important rules becoming harder to notice;
4. unrelated instructions influencing the task;
5. repeated context cost across multiple agent invocations.

Therefore, the solution must optimize not only for governance and reuse, but also for **context efficiency**.

---

## 2.7 Multi-agent participation can cause solution inflation

A further problem appears when several capable specialist agents participate in the same change.

Each specialist is naturally optimized to look for improvements within its own area:

- an Architect may identify a cleaner abstraction;
- UX may identify additional journey improvements;
- Functional QA may identify more edge cases;
- Non-Functional QA may recommend stronger operational protections;
- Security may recommend additional controls;
- Independent Review may identify maintainability improvements.

Individually, these observations may all be reasonable. Collectively, however, they can create a systematic bias toward **adding more**.

This can cause:

- scope expansion beyond the original problem;
- speculative abstraction and future-proofing;
- new configuration for hypothetical use cases;
- duplicate validation or assurance layers;
- implementation of every reviewer suggestion regardless of value;
- increased code size and cognitive load;
- longer delivery cycles;
- solutions that are technically sophisticated but disproportionate to the actual requirement.

The process therefore needs an explicit counterbalance.

Specialist feedback must be treated as **input to an engineering decision**, not as automatically additive requirements.

Someone other than the Product Owner should be responsible for asking:

> What is the smallest solution that fully satisfies the requirement, required quality controls, and material risk?

This capability is referred to in this document as **Solution Sufficiency / Complexity Stewardship**.

It may be performed by an Engineering Manager, Orchestrator, or a dedicated Solution Steward depending on the repository and change. It should not require a separate agent invocation for every small change.

---

## 2.8 Risk of duplicating coding-assistant competence

Modern coding assistants such as Codex and Claude Code already contain substantial software-engineering competence.

They can increasingly:

- inspect and understand repositories;
- plan implementation work;
- write and refactor code;
- run tests and linters;
- debug failures;
- use Git and worktrees;
- review code;
- operate tools and sandboxes;
- manage implementation context;
- use native subagents or parallel execution where supported.

These capabilities will continue to improve.

A common Software Engineering Process should therefore **not attempt to recreate or micromanage the native software-engineering competence of coding assistants**.

Doing so would create:

- duplicated instructions;
- increased token cost;
- unnecessary orchestration;
- conflict between repository policy and assistant-native behaviour;
- brittle coupling to current model capabilities;
- a process that becomes obsolete as coding assistants improve.

The common process should instead define information that coding assistants cannot infer merely by becoming better engineers:

- organizational intent;
- repository-specific constraints;
- approval authority;
- risk appetite;
- mandatory specialist perspectives;
- human boundaries;
- process inheritance;
- evidence requirements;
- definition of readiness;
- definition of sufficient scope;
- rules that must not be weakened locally.

This leads to a central design principle:

> **Do not encode generic engineering competence. Encode intent, constraints, authority, required perspectives, and evidence.**

---

## 2.9 Change classification can become a control-plane weakness

The architecture relies on change classification to determine whether the effective assurance profile is Lean, Standard, or Protected. That makes classification itself a **root-of-trust decision**.

If a payment, authentication, IAM, privacy, or production-control change is incorrectly classified as ordinary work, every downstream control may execute correctly while the wrong set of controls has been selected.

Recent large-scale evidence from 20,574 real-world coding-agent sessions identifies recurring misalignment in project understanding, developer intent, rule following, action boundaries, implementation/execution, and reporting. This does not prove that an agent will misclassify a Software Signal change, but it is strong evidence that semantic agent judgment should not be the sole protection for high-consequence routing decisions.[^R18]

Therefore classification must combine:

- issue declarations and acceptance criteria;
- repository-level protected characteristics and known sensitive paths;
- deterministic signals where available;
- agent semantic judgment for context that cannot be inferred mechanically;
- conservative fail-closed handling when a Protected characteristic is unknown, contradictory, or plausibly present.

Classification must itself produce durable evidence explaining why a change received its delivery profile.

# 3. Design Goals

The proposed system should satisfy the following goals.

## 3.1 One canonical process

There should be one authoritative place defining the common software engineering model. Repository-local process definitions should derive from it rather than duplicate it. This follows the same broad principle used by common software life-cycle frameworks and centrally governed control baselines.[^R1][^R3]

## 3.2 Backend and frontend should be profiles, not separate processes

The system should allow profiles such as:

- `generic`
- `frontend`
- `backend`

A profile extends the core process with domain-specific rules. Future profiles may include `mobile`, `data-platform`, `ml-system`, `library`, `infrastructure`, and `research-tool`.

## 3.3 Repositories may customize the process

A repository should be able to specify its local needs without copying the full process. Examples include UX triggers, repository-specific validation commands, infrastructure tooling, or device-matrix validation.

## 3.4 Overrides must not silently weaken critical controls

Some rules should be immutable or strengthen-only. A repository should not be able to casually override builder/reviewer separation, secret-handling rules, required human production approval, Protected fail-closed rules, mandatory traceability, or required approval boundaries. Repository customization must distinguish locked, extensible, and overridable settings.

## 3.5 Process should be risk-adaptive

The engineering process should be proportional to the change. A typo should not invoke the same assurance as payment logic, authentication, IAM, production deployment controls, or a major user journey. NIST's control-baseline and tailoring model provides mature precedent for applying controls according to context and risk rather than identically everywhere.[^R3]

## 3.6 Process should be tool-neutral

Roles should represent **engineering capabilities**, not model vendors. Runtime assignment may be Claude Code, Codex, another approved agent, or a human. The process should survive changes in the underlying AI tools.


## 3.6.1 Technology-stack independence

The canonical engineering process should be **technology-stack independent**. It must not depend on a repository's programming language, application framework, runtime, build system, test framework, deployment technology, or infrastructure provider. These are repository-local implementation concerns supplied through repository configuration and, where necessary, adapters.

A repository using a new or entirely different technology stack should therefore be able to inherit the same common process without changing the core simply because its stack is different. The repository supplies the local mechanisms needed to satisfy common obligations, such as build and test commands, revision identity, evidence generation, merge/release/deployment mechanisms, and available native enforcement controls.

Profiles should model **engineering characteristics and risk domains, not technology stacks**. For example, `frontend` should represent concerns such as user journeys, interaction, accessibility, browser/client behaviour, and related assurance needs; it should not mean React, JavaScript, or any specific frontend framework. Likewise, `backend` should represent concerns such as APIs, persistence, concurrency, authentication/authorization, IAM, operational behaviour, and related risks; it should not mean Python, Java, Go, .NET, or any particular backend framework.

A new technology stack should not require a new profile or a change to the canonical process unless it introduces a genuinely new class of engineering obligation or material risk. A new engineering domain, such as an ML system with model evaluation, data provenance, reproducibility, or model-risk requirements, may justify a new profile because the risk and assurance model is different—not because the implementation technology is different.

Platform-specific mechanisms are also treated as adapters rather than canonical policy. For example, GitHub rulesets, GitLab merge controls, Azure DevOps policies, or cloud deployment gates may provide different native ways to enforce the same common obligation. The canonical process owns the meaning of the rule; the applicable platform adapter maps that rule to the strongest available native enforcement mechanism.

A concise architectural rule follows:

> **New technology ≠ new profile. New engineering risk or assurance domain may justify a new profile.**

## 3.7 Process should be enforceable

The process should not exist only as prose. CI and supporting tooling should be able to validate process version, local overrides, forbidden weakening, classification, generated adapter freshness, evidence completeness, and process drift. Where a native platform can enforce a rule, the process should prefer that enforcement point over reminder text. GitHub, for example, can require status checks before merge and can protect deployments with required reviewers and self-review prevention.[^R12][^R13]

## 3.8 Process should minimize token overhead

Agents should receive only the process context relevant to the current task. The architecture should explicitly support progressive disclosure. Current Codex Skills and Claude Code Skills load detailed instructions only when relevant, providing a native mechanism for this design.[^R8][^R10]

## 3.9 Process should actively resist unnecessary complexity

The process should not merely collect specialist opinions. It should synthesize them into a **minimum sufficient solution** by preserving acceptance criteria, separating mandatory findings from optional improvements, challenging speculative abstractions, preferring existing patterns and reversible changes, and defining a stopping rule. Recent long-horizon coding-agent research reports increasing verbosity and structural erosion across iterative extensions, which provides emerging evidence for explicit complexity stewardship.[^R20]

## 3.10 Process should define WHAT, coding assistants should own HOW

The Software Engineering Process should define:

- what obligations apply;
- what constraints must be respected;
- what approvals are required;
- what specialist perspectives are mandatory;
- what evidence constitutes readiness.

The coding assistant should normally decide implementation approach inside approved boundaries, code structure, refactoring technique, test implementation, debugging approach, tool usage, and local task decomposition.

## 3.11 Prefer native coding-assistant capabilities over reimplementation

When a coding assistant provides a reliable native capability, the process should configure or consume it rather than rebuild it. Codex and Claude Code already provide repository exploration, editing, command execution, agent/skill extension mechanisms, and context-management facilities.[^R9][^R11]

## 3.12 Policy evaluation should produce obligations, not a competing orchestration runtime

The central platform should evaluate policy and produce an **Effective Obligation Set**: required capabilities, approvals, evidence, prohibited actions, and merge/deployment gates. It should not prescribe every implementation step or recreate an agent runtime. This follows the policy-as-code separation used by systems such as Open Policy Agent, where policy decisions are expressed declaratively and enforcement/execution occurs elsewhere.[^R4]

## 3.13 Classification must be a trusted policy decision

Because classification selects the assurance profile, it must be evidence-producing, conservative for Protected characteristics, and augmented by deterministic repository signals where practical. A sensitive change must not become Lean simply because an agent failed to notice a characteristic.

## 3.14 Evidence should be revision-bound

Critical evidence should be bound to the exact source revision it validates. The in-toto Statement model explicitly binds attestations to a subject digest, and SLSA Source provenance is built around evidence for specific immutable source revisions.[^R5][^R7]

## 3.15 Prefer the strongest native enforcement point

The canonical process owns the **meaning** of a rule. The strongest available native mechanism should normally enforce it: GitHub rulesets/status checks for merge gates, GitHub Environments for deployment approvals, CI for deterministic validation, attestations for revision-bound evidence, and agent Skills for procedural specialist guidance.[^R12][^R13]

# 4. Non-Goals

The system is not intended to:

- force all repositories into identical workflows;
- run every agent role on every change;
- eliminate repository-specific engineering decisions;
- eliminate human judgment;
- centralize all implementation knowledge;
- place application architecture in the common process repository;
- automatically approve production;
- automatically weaken Protected controls;
- make `AGENTS.md` itself the canonical process source;
- treat every specialist recommendation as mandatory implementation work;
- optimize for minimum code by weakening correctness, usability, security, operability, or required assurance;
- teach coding assistants generic software-engineering technique they already possess;
- reimplement coding-assistant-native execution, sandboxing, review, Git, planning, or subagent capabilities without a clear policy need;
- make the central process dependent on one coding-assistant vendor;
- become a general-purpose multi-agent orchestration runtime;
- rely on prompt text when a stronger native enforcement mechanism is available;
- allow semantic agent classification alone to weaken Protected assurance;
- require a different model vendor merely to claim independent review;
- introduce a heavyweight policy engine in V1 when YAML, schema validation, and a small semantic validator are sufficient.

---

# 5. Proposed Architecture

The proposed model separates **policy**, **policy evaluation**, **execution adapters**, and **native enforcement**.

```text
                 COMMON SOFTWARE ENGINEERING POLICY
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
          Frontend Profile              Backend Profile
                 │                           │
                 └─────────────┬─────────────┘
                               │
                   Repository Configuration
                               │
                   Change Characteristics
                               │
                      POLICY EVALUATION
                               │
                    Effective Obligation Set
                               │
       ┌───────────────────────┼────────────────────────┐
       │                       │                        │
 Required capabilities   Required evidence      Required gates /
 and approvals            and constraints        forbidden actions
       │                       │                        │
       └───────────────────────┼────────────────────────┘
                               │
                       Tool-specific adapters
                               │
                  Codex / Claude / Human / CI
                               │
                     Revision-bound evidence
                               │
                     Readiness verification
                               │
                       Merge / deployment
```

The effective policy for a given change is therefore:

```text
Core Policy
    +
Selected Profile
    +
Repository Manifest
    +
Issue / Change Characteristics
    =
Effective Obligation Set
```

**Inheritance decides what policy is available.**

**Classification decides which obligations apply to the specific change.**

**Adapters map obligations to native assistant/platform mechanisms.**

**Evidence proves that the obligations were satisfied for the exact revision.**

This boundary is deliberate:

```text
Software Signal Engineering
        owns WHAT must be true
                 ↓
Policy evaluator
        resolves obligations
                 ↓
Tool/platform adapters
        map obligations to native mechanisms
                 ↓
Codex / Claude Code / GitHub / CI / humans
        own HOW the work or enforcement happens
```

The process should therefore behave as an **engineering policy and assurance layer**, not as a competing coding-agent runtime. This separation closely matches mature policy-as-code architecture: policy is centrally expressed and evaluated, while enforcement occurs at appropriate system boundaries.[^R4]

# 6. Canonical Process Repository

Create a dedicated repository, for example:

```text
suyog19/software-engineering-process
```

A recommended V1 structure is:

```text
software-engineering-process/
│
├── policy/
│   ├── core.yaml
│   ├── profiles/
│   │   ├── generic.yaml
│   │   ├── frontend.yaml
│   │   └── backend.yaml
│   ├── classification/
│   │   ├── characteristics.yaml
│   │   └── delivery-profiles.yaml
│   └── evidence/
│       ├── evidence.schema.json
│       └── predicate-types.yaml
│
├── skills/
│   ├── senior-ux-review/
│   │   └── SKILL.md
│   ├── architecture-review/
│   │   └── SKILL.md
│   ├── functional-qa/
│   │   └── SKILL.md
│   ├── non-functional-qa/
│   │   └── SKILL.md
│   ├── independent-review/
│   │   └── SKILL.md
│   └── solution-sufficiency/
│       └── SKILL.md
│
├── adapters/
│   ├── codex/
│   ├── claude-code/
│   └── generic/
│
├── enforcement/
│   └── github/
│       ├── reusable-workflows/
│       └── ruleset-guidance/
│
├── schemas/
│   └── repository-process.schema.json
│
├── templates/
│   ├── AGENTS.md
│   ├── CLAUDE.md
│   └── process-validation.yml
│
└── tooling/
    ├── init
    ├── validate
    ├── classify
    ├── render
    └── explain
```

The exact layout can evolve. The important architectural separations are:

- **policy** — organizational obligations and override semantics;
- **classification** — trusted selection of applicable obligations;
- **skills** — portable specialist procedures loaded only when needed;
- **adapters** — mapping from tool-neutral obligations to Codex/Claude/native mechanisms;
- **enforcement** — platform-native controls such as GitHub status checks and deployment protection;
- **evidence** — revision-bound machine-readable readiness claims;
- **tooling** — initialization, validation, explanation, and rendering.

The Agent Skills open specification uses `SKILL.md` as a portable package for task-specific instructions and resources. Codex uses Skills with progressive disclosure, and Claude Code documents compatibility with the Agent Skills standard.[^R8][^R10][^R23]

# 7. Core Process

The core process contains engineering principles that apply broadly across repositories.

Examples include:

## 7.1 Traceability

Every implementation change should have durable traceability:

```text
Issue
  → branch
  → implementation
  → PR
  → validation
  → review
  → merge
  → deployment / release evidence
```

---

## 7.2 Issue-first development

Implementation should begin from a durable unit of work.

The issue records:

- problem;
- intended outcome;
- acceptance criteria;
- known constraints;
- relevant approvals.

---

## 7.3 Builder/reviewer separation

The agent or human who performs the implementation should not issue the final independent review verdict from the same implementation context. Final independent review should use a **fresh review context** with read-only access to the finished change and required evidence.

This is a core reliability control and should normally be locked. Mature separation-of-duty principles support the underlying independence requirement, while recent LLM-evaluation research reports self-preference and contextual/confirmation bias that can distort automated judgments.[^R14][^R21][^R22]

A different model or vendor may be used as an additional diversity mechanism, especially for Protected work, but vendor diversity is **not itself the locked requirement**. The locked requirement is independence of the final review context and verdict.

---

## 7.4 Proportional assurance

The process should select assurance based on risk and change characteristics rather than invoking every role by default.

---

## 7.5 Durable approval

Private prompts and temporary agent context are not sufficient evidence for critical approval boundaries.

Where approval is required, it should be recorded in durable project evidence.

---

## 7.6 Human production boundary

Production deployment and production-authority changes remain human controlled unless a future explicit policy changes that boundary.

---

## 7.7 Scope discipline

Agents work only on:

- the linked issue;
- explicitly approved follow-up;
- PR review feedback.

Drive-by refactoring should be avoided.

---

## 7.8 Security and privacy

The process must prohibit:

- committed credentials;
- secret exposure;
- accidental private-data disclosure;
- unapproved access expansion;
- bypassing review or deployment controls.

---

## 7.9 Evidence-bound readiness

A change is ready because required evidence exists, not because an agent claims that it is ready.

---

## 7.10 Do not encode generic engineering competence

The core process should avoid generic instructions such as:

- write clean code;
- use meaningful names;
- keep functions small;
- add appropriate tests;
- handle errors;
- refactor carefully;
- follow normal Git practices.

These are ordinary software-engineering competencies that modern coding assistants already possess and will continue to improve.

Such instructions should appear only when a repository has a **specific, non-obvious, organization-specific rule**.

For example:

```text
Do not introduce a framework in this static repository without explicit approval.
```

is useful because it is a repository-specific constraint.

By contrast:

```text
Write maintainable code.
```

adds little value.

The common process should concentrate context on what the assistant cannot safely infer.

---

## 7.11 Solution sufficiency and complexity stewardship

The common process should include an explicit capability responsible for preventing multi-agent engineering from becoming unnecessarily complicated.

Its governing principle is:

> **Prefer the simplest implementation that is sufficient for the present requirement and risk.**

This capability protects four things:

1. the original problem statement;
2. the agreed acceptance criteria;
3. mandatory engineering controls;
4. proportionality of the final solution.

It should challenge additions that are technically attractive but not necessary for the current change.

It must **not** override:

- locked process controls;
- genuine correctness defects;
- security or privacy requirements;
- required accessibility or UX acceptance;
- required Protected assurance;
- explicit Product Owner acceptance criteria.

Its purpose is therefore not to weaken engineering discipline. Its purpose is to prevent discipline from turning into indiscriminate accumulation of mechanisms, abstractions, and follow-up work inside the same change.

---

## 7.12 Classification integrity

Classification is part of the control plane and must be treated as evidence-bearing policy evaluation.

For Protected characteristics, the classifier should use a hybrid of deterministic repository signals and semantic analysis. Examples of deterministic signals include changes to configured authentication, IAM, payment, secrets, infrastructure, entitlement, or production-control paths. These signals are not sufficient by themselves, but they can prevent an obvious sensitive change from being silently routed to Lean assurance.

If a Protected characteristic cannot be confidently ruled out, the default should be to strengthen classification or require an explicit decision rather than weaken assurance.

# 8. Process Profiles

Profiles extend the common process for a class of repository.

They should add or strengthen rules without duplicating the core.

---

# 9. Frontend Profile

The frontend profile focuses on:

- user journeys;
- information architecture;
- interaction;
- accessibility;
- responsive design;
- browser behaviour;
- frontend API contracts;
- client-side security;
- visual consistency;
- discoverability;
- performance.

A critical addition should be a **Senior UX Designer** capability.

Example trigger model:

```yaml
senior_ux_designer:
  required_when:
    - new_user_journey
    - major_existing_journey_change
    - information_architecture_change
    - material_navigation_change
    - material_layout_change
    - user_facing_workflow_redesign
```

Possible pre-implementation responsibility:

- understand the user need;
- review information architecture;
- define interaction intent;
- identify usability risks;
- review accessibility implications;
- approve the UX direction when required.

Possible post-implementation responsibility:

- verify implementation against the intended UX;
- inspect responsive behaviour;
- verify journey clarity;
- identify unnecessary friction;
- record residual UX risks.

UX is therefore treated as an engineering capability, not merely a cosmetic finishing pass.

This lifecycle treatment is supported by ISO 9241-210, which specifies human-centred design principles and activities throughout the life cycle of interactive systems. W3C accessibility guidance likewise separates design/development from test/evaluation and provides testable accessibility criteria and evaluation methods.[^R15][^R16]

For material frontend changes, the profile should also support a **Solution Sufficiency** pass after UX/architecture input and again when review feedback is extensive. In a lightweight frontend repository this may be performed by the Orchestrator acting in a separate stewardship role rather than by invoking another permanent agent.

---

# 10. Backend Profile

The backend profile focuses on:

- API contracts;
- persistence;
- concurrency;
- retries;
- financial state;
- authentication;
- authorization;
- IAM;
- infrastructure;
- operational risk;
- privacy;
- secrets;
- data migration;
- production controls.

Example specialist triggers:

```text
Authentication
    → Team Lead
    → Functional QA
    → Non-Functional QA
    → Independent Review
    → Protected

Financially consequential behaviour
    → Team Lead
    → Engineering Manager when delivery risk is material
    → Functional QA
    → Non-Functional QA
    → required human approval
    → Independent Review
    → Protected

IAM / trust boundary
    → Team Lead
    → Non-Functional QA
    → human approval when required
    → Independent Review
```

The backend profile should continue to use stronger fail-closed behaviour for sensitive characteristics.

The backend Engineering Manager is a natural owner for **Solution Sufficiency / Complexity Stewardship** because it already reasons about scope, sequencing, operational risk, rollback, cost, capacity, and blast radius. This responsibility should explicitly include challenging unnecessary complexity and deciding which non-mandatory specialist recommendations belong in the current change.

---

# 11. Repository Manifest

Each repository should contain a small declarative process configuration rather than a complete independent process definition. It should also record the exact resolved process revision so policy evaluation is reproducible.

For example:

```text
.engineering/process.yaml
.engineering/process.lock
```

Frontend example:

```yaml
schema_version: 1

process:
  source: suyog19/software-engineering-process
  version: 1.3.0
  revision: <exact-git-sha>
  profile: frontend

repository:
  name: suyog19.github.io

overrides:
  technology:
    type: static-site
    build_system: none

  validation:
    commands:
      - node --test tests/*.test.js
      - python scripts/validate_image_performance.py

  classification:
    protected_path_hints:
      - "src/auth/**"
      - "src/payments/**"

  ux:
    senior_ux_designer:
      additional_required_when:
        - public_navigation_change
```

Backend example:

```yaml
schema_version: 1

process:
  source: suyog19/software-engineering-process
  version: 1.3.0
  revision: <exact-git-sha>
  profile: backend

repository:
  name: suyogjoshi-platform

overrides:
  technology:
    runtime: python3.12
    infrastructure: aws-sam

  validation:
    commands:
      - ruff check .
      - pytest
      - sam validate --template infra/template.yaml --lint
```

The repository configuration should be small enough that a maintainer can quickly understand how the repository differs from the shared process.

---

# 12. Override Model

Not every process setting should have the same override semantics.

The process should explicitly classify settings into three types.

## 12.1 Locked

A repository cannot weaken these rules.

Examples:

- implementation context cannot issue final independent review;
- secrets must not be committed;
- mandatory human approval boundaries;
- Protected fail-closed rules;
- production promotion restrictions;
- traceability requirements;
- stale evidence cannot satisfy readiness.

A repository may strengthen a locked rule, but not weaken it.

---

## 12.2 Extensible

Repositories may add additional requirements.

Example:

Core:

```text
Functional QA required for observable behaviour.
```

Frontend:

```text
For major user journeys, UX conformance review is additionally required.
```

Backend:

```text
For retry or concurrency changes, NFQA is additionally required.
```

---

## 12.3 Overridable

These are intentionally repository-specific.

Examples:

- build commands;
- test commands;
- repository paths;
- deployment commands;
- branch names;
- framework;
- runtime;
- local validation scripts;
- environment naming;
- documentation paths.

---

# 13. Agent Roles as Capabilities

Roles should exist only where they contribute a distinct decision authority, specialist perspective, risk ownership, independent assurance function, or separation-of-duties boundary.

The process should **not recreate a traditional human team merely by assigning an AI agent to every job title**.

A role is a policy-level capability definition. Its procedural guidance should normally be packaged as a portable Skill when such guidance is needed. Runtime assignment remains separate.

For example:

```text
Functional QA capability
    policy responsibility:
      - acceptance criteria
      - user-visible behaviour
      - errors
      - state transitions
      - edge cases

Functional QA Skill
    procedure:
      - how to inspect the finished change
      - required inputs
      - required output schema
      - escalation rules

Runtime assignment
    preferred: codex | claude-code | human
```

This distinction allows policy to remain stable even when model capabilities or vendor choices change. Agent Skills provide a current cross-tool packaging convention for such on-demand procedural capability.[^R23]

A recommended core capability model is:

| Capability | Why it exists |
|---|---|
| Product Owner | Product intent, priority, acceptance, and material product decisions |
| Orchestrator | Classification coordination, required-capability selection, handoffs, and evidence tracking |
| Senior UX Designer | Independent user, interaction, information-architecture, and accessibility perspective |
| Architect / Team Lead | Material architectural decisions and technical boundaries |
| Engineering Manager | Delivery risk, scope, operational realism, and complexity control |
| Software Developer | Implementation using native coding-assistant engineering judgment |
| Functional QA | Independent behavioural and acceptance verification |
| Non-Functional QA | Relevant security, reliability, performance, privacy, infrastructure, and operational assurance |
| Independent Reviewer | Fresh-context final engineering review |
| Solution Steward | Minimum-sufficient solution and non-mandatory feedback triage |
| CI / Automation | Objective automated evidence and policy enforcement |

Not every capability participates in every change.

## 13.1 Software Developer should be deliberately thin

The Software Developer role should primarily provide the accepted requirement, repository-specific constraints, approved design decisions, required validation commands, and applicable policy boundaries.

A useful developer contract remains:

> Implement the approved change using your engineering judgment, within the stated constraints, and produce the required validation evidence.

## 13.2 Orchestrator should be deliberately thin

The Orchestrator should primarily:

```text
Understand the issue
    ↓
Coordinate trusted classification
    ↓
Select only required capabilities
    ↓
Coordinate required handoffs
    ↓
Track required evidence
    ↓
Stop when solution sufficiency and readiness are achieved
```

The Orchestrator should not micromanage coding style, implementation decomposition, debugging technique, tool selection, or native assistant subagent strategy.

## 13.3 Solution Steward is a capability, not necessarily another permanent agent

The Solution Steward synthesizes specialist input and protects solution proportionality. A repository may map the capability to Engineering Manager, Orchestrator, Team Lead where separation remains acceptable, a dedicated fresh agent for contentious changes, or a human engineering lead.

The default should **not** be to add another agent invocation to every change.

Typical triggers include:

- three or more specialist roles contribute material recommendations;
- reviewers propose substantial additional scope;
- a design introduces a new framework, service, abstraction, or configuration layer;
- proposed implementation materially exceeds the issue scope;
- specialists disagree on whether a recommendation is required;
- a review/fix loop exceeds a configured threshold;
- implementation complexity grows unexpectedly relative to the problem.

## 13.4 Assurance roles exist for independence, not because the assistant lacks competence

Functional QA, Non-Functional QA, and Independent Review should not repeat generic engineering advice. Their value is **independent perspective and assurance**.

The existence of these roles does not imply that the implementation assistant cannot test or review its own work. Their purpose is to reduce correlated assumptions, preserve separation of duties, and provide fresh-context verification. NIST separation-of-duty guidance provides the mature control principle; recent LLM research gives additional reason not to rely on a generator's own evaluative context as the sole final verdict.[^R14][^R21]

# 14. Example Capability Policy and Skill

Policy and procedure should be separated. The policy definition answers **when the capability is required and what evidence it must produce**; the Skill answers **how an invoked agent should perform that specialist procedure**.

Example policy definition:

```yaml
capability: functional-qa

invoke_when:
  - observable_behavior_change
  - user_journey_change
  - state_transition_change
  - validation_or_error_change

obligations:
  - verify_acceptance_criteria
  - verify_happy_path
  - verify_edge_cases
  - verify_errors
  - identify_residual_functional_risk

constraints:
  - final_verdict_must_not_use_implementation_context

evidence:
  predicate_type: functional-qa-verdict/v1
  bind_to_exact_revision: true
```

Example Skill package:

```text
skills/functional-qa/
├── SKILL.md
└── references/
    └── evidence-schema.md
```

The Skill should remain concise: purpose, required inputs, verification perspective, escalation rules, and the required machine-readable output. Codex and Claude Code both support `SKILL.md`-based on-demand capability loading, while the Agent Skills specification defines a portable directory format.[^R8][^R10][^R23]

# 15. Solution Sufficiency and Complexity Stewardship

The common process should formalize a **Solution Sufficiency / Complexity Stewardship** capability.

This is the process-level answer to the tendency of multi-agent teams to over-engineer.

The concern is not purely theoretical. MAST identifies specification/system-design, inter-agent alignment, and verification/termination failures across multi-agent systems, while SlopCodeBench reports increasing verbosity and structural erosion during repeated coding-agent extensions. These are emerging research results rather than mature standards, but they justify an explicit proportionality and stopping mechanism that we can measure in our own repositories.[^R17][^R20]

## 15.1 Mandate

The mandate is:

> **Deliver the smallest solution that fully satisfies the requirement, acceptance criteria, required engineering controls, and material risk.**

The steward should optimize for:

- sufficiency rather than maximal sophistication;
- current requirements rather than speculative future requirements;
- understandable implementation rather than abstraction for its own sake;
- existing patterns rather than new machinery where both are adequate;
- reversible local changes rather than broad structural changes;
- explicit deferral rather than quietly expanding scope.

The steward is not a cost cutter and is not authorized to suppress valid defects.

---

## 15.2 Inputs

The steward consumes:

- issue problem statement;
- acceptance criteria;
- Product Owner decisions;
- UX recommendations;
- architecture decisions;
- Engineering Manager concerns;
- Functional QA findings;
- Non-Functional QA findings;
- security/privacy findings;
- Independent Review findings;
- implementation diff and complexity;
- CI/test evidence;
- known residual risks.

The steward does not replace any of these roles.

It synthesizes them.

---

## 15.3 Feedback triage

Every non-mandatory specialist recommendation should be classified into one of four outcomes.

### Must address

Required because leaving it unresolved would:

- fail an acceptance criterion;
- create a correctness defect;
- violate a locked engineering control;
- create material security/privacy risk;
- create unacceptable operational risk;
- violate an approved architecture or public contract;
- leave a blocking review finding.

These cannot be dismissed by the Solution Steward.

### Worth addressing now

Not strictly mandatory, but:

- clearly within current scope;
- materially improves the solution;
- introduces little additional complexity;
- is easier and safer to address now than later.

This should remain a deliberately small category.

### Defer

A valid observation that:

- is not required for the current outcome;
- adds meaningful scope or complexity;
- addresses a future scenario;
- belongs to another improvement;
- can safely be handled separately.

A follow-up issue should be created only when the improvement is genuinely worth tracking. Deferral should not automatically create backlog noise.

### Reject

A recommendation that is:

- unnecessary;
- based on an invalid assumption;
- redundant with an existing control;
- inconsistent with current scope;
- disproportionate to the risk;
- speculative without sufficient evidence.

The reason should be recorded when the rejected recommendation was material.

---

## 15.4 Sufficiency test

For a proposed addition, the process should ask:

> If this is removed, does the solution fail an acceptance criterion, violate a required engineering control, create material risk, or become materially harder to maintain?

If the answer is **no**, the default is not to add it to the current change.

This is a heuristic, not an absolute rule, but it creates the desired engineering bias.

---

## 15.5 Complexity guardrails

The steward should prefer:

```yaml
prefer:
  - existing_patterns
  - local_changes
  - reversible_changes
  - fewer_components
  - fewer_new_abstractions
  - fewer_configuration_dimensions
  - explicit_code_over_generic_frameworks_for_single_use
```

The steward should challenge:

```yaml
challenge:
  - new_frameworks
  - new_managed_services
  - new_dependencies
  - generic_abstractions_for_one_use_case
  - speculative_future_requirements
  - configuration_for_hypothetical_variants
  - duplicate_validation_layers
  - duplicate_assurance
  - recommendations_outside_acceptance_scope
  - large_refactors_hidden_inside_feature_work
```

These are not automatic prohibitions.

They are prompts to establish that the added complexity earns its place.

---

## 15.6 Pre-implementation stewardship

For changes with substantial specialist input, the Solution Steward should operate before implementation.

Conceptually:

```text
Problem / Acceptance Criteria
        ↓
Selected Specialist Inputs
        ↓
Solution Sufficiency Pass
        ↓
Minimum Sufficient Design
        ↓
Implementation
```

The output should identify:

- what will be implemented now;
- what is explicitly out of scope;
- which recommendations were deferred or rejected;
- why the resulting design is sufficient.

This gives the design process an explicit stopping point.

---

## 15.7 Post-review stewardship

A second stewardship pass may be needed when multiple reviewers produce findings.

Conceptually:

```text
Implementation
      ↓
QA / UX / NFQA / Independent Review
      ↓
Mandatory findings separated from improvement ideas
      ↓
Solution Steward triage
      ↓
Required fixes
      +
small worthwhile fixes
      +
explicit deferrals/rejections
      ↓
Done
```

Mandatory review findings still block readiness according to their governing policy.

The steward controls **scope inflation from non-blocking recommendations**, not the validity of required controls.

---

## 15.8 Stopping rule

Agentic engineering needs an explicit stopping condition.

A change is sufficient when:

- acceptance criteria are satisfied;
- mandatory engineering controls are satisfied;
- required tests and CI are complete;
- required specialist reviews are complete;
- no blocking findings remain;
- material residual risks are understood and recorded;
- further proposed improvements are nonessential to the current outcome.

The stopping condition is **not**:

> No participant can think of any further improvement.

That condition is effectively unbounded.

Once sufficiency is established, further improvements belong to another issue or are intentionally discarded.

---

## 15.9 Relationship to Engineering Manager

In backend and other operationally significant systems, Engineering Manager is the preferred owner for this capability.

The Engineering Manager already evaluates:

- scope;
- sequencing;
- rollback;
- cost;
- capacity;
- operations;
- blast radius.

The role should explicitly add:

- complexity control;
- solution proportionality;
- synthesis of specialist recommendations;
- current-scope versus future-scope decisions.

---

## 15.10 Relationship to Orchestrator

In lighter repositories, invoking a separate Engineering Manager for every Standard change would itself be process overhead.

The Orchestrator may therefore perform a bounded **Solution Steward pass**, provided:

- it is not overriding a specialist's mandatory control;
- role responsibilities are clearly separated;
- the pass is focused on synthesis rather than another full review.

This allows the capability to exist without creating a permanent extra participant.

---

## 15.11 Relationship to Product Owner

The Product Owner remains the authority for:

- product intent;
- priorities;
- acceptance criteria;
- material product trade-offs;
- explicit human approvals.

The Solution Steward does not replace Product Owner judgment.

Its purpose is to keep routine engineering proportional **without requiring the Product Owner to personally arbitrate every technical recommendation**.

---

## 15.12 Evidence output

For material changes, a concise stewardship record may contain:

```yaml
solution_sufficiency:
  verdict: sufficient
  must_address:
    - finding-1
    - finding-2
  worth_addressing_now:
    - improvement-1
  deferred:
    - improvement-2
  rejected:
    - improvement-3
  complexity_added:
    - none
  rationale: >
    Current design satisfies acceptance criteria and required controls
    without introducing a new abstraction or service.
```

This evidence should remain concise.

The stewardship mechanism should reduce process noise, not create another essay-producing role.

---

# 16. Change Classification

Every issue or change must be classified because classification selects the effective obligation set. Classification is therefore a **trusted policy decision**, not merely an orchestration convenience.

The classification may use characteristics such as:

```text
observable behaviour
public contract
user journey
information architecture
architecture
cross-service
financial consequence
payment-provider trust
authentication / authorization
IAM / privilege / trust
secrets
sensitive data
production controls
irreversible data
infrastructure
performance
retry
concurrency
shared test infrastructure
```

The resulting delivery profile may be Lean, Standard, or Protected.

## 16.1 Classification inputs

Classification should combine four input classes:

1. **Declared intent** — issue description, acceptance criteria, Product Owner decisions.
2. **Repository policy** — profile, protected characteristics, sensitive path hints, known trust boundaries.
3. **Deterministic evidence** — changed paths, configuration changes, infrastructure files, permission/IAM changes, deployment files, dependency or secret-policy signals where available.
4. **Semantic judgment** — agent or human interpretation for characteristics that cannot be reliably derived mechanically.

No single input is universally sufficient. Deterministic checks reduce obvious routing mistakes; semantic judgment covers changes whose consequences are not visible from paths alone.

## 16.2 Protected fail-closed rule

A change must not be classified Lean or Standard merely because a classifier failed to recognize a Protected characteristic.

If a configured Protected signal is present, contradicted, or cannot be confidently resolved, the process should:

- strengthen the classification automatically; or
- require an explicit authorized decision before weaker assurance is accepted.

## 16.3 Classification evidence

Classification should produce concise durable evidence, for example:

```yaml
classification:
  revision: <git-sha>
  profile: backend
  delivery_profile: Protected
  characteristics:
    authentication: true
    observable_behavior: true
  deterministic_signals:
    - path: src/auth/token_service.py
      matched_rule: protected.auth_path
  semantic_rationale: >
    The change modifies token validation semantics and therefore affects
    authentication behaviour.
  policy_version: 1.3.0
  policy_revision: <process-sha>
```

The classification evidence becomes an input to readiness verification.

The need for this safeguard is strengthened by empirical evidence that real coding-agent sessions still exhibit recurring misalignment around intent, rules, project understanding, action boundaries, and reporting.[^R18]

# 17. Lean Changes

Typical examples:

- typo;
- documentation;
- metadata;
- sitemap update;
- small established-pattern CSS change;
- test-only mechanical update;
- minor internal refactor with no observable consequence.

Typical workflow:

```text
Issue
  → Developer
  → focused validation
  → lightweight Independent Review
  → merge readiness
```

No UX Designer, Engineering Manager, or NFQA should be invoked merely to keep roles active.

---

# 18. Standard Changes

Typical frontend examples:

- new page;
- new interaction;
- user journey improvement;
- navigation change;
- API response handling;
- responsive component.

Typical backend examples:

- ordinary endpoint;
- validation;
- bounded state transition;
- accepted-pattern infrastructure behaviour.

Possible frontend workflow:

```text
Issue
  → UX Designer if triggered
  → Architect if triggered
  → Solution Sufficiency pass when specialist input is material
  → Developer
  → Functional QA
  → UX conformance if triggered
  → Independent Review
  → merge readiness
```

---

# 19. Protected Changes

Typical examples:

- payment behaviour;
- refunds;
- authentication;
- authorization;
- IAM;
- secrets;
- private data exposure;
- production deployment authority;
- irreversible migration;
- high-risk learner entitlement;
- frontend cancellation/refund workflow;
- security-sensitive admin actions.

Typical workflow:

```text
Issue
  → trusted classification + classification evidence
  → Effective Obligation Set
  → required specialist design
  → Solution Sufficiency synthesis
  → human approval where required
  → implementation
  → CI/tests
  → Functional QA
  → Non-Functional QA
  → UX review where user-facing
  → fresh Independent Review
  → Solution Sufficiency triage for non-blocking additional recommendations
  → exact-head evidence join
  → human merge
  → controlled production promotion
```

Protected workflow should fail closed when required evidence is:

- absent;
- malformed;
- stale;
- contradictory;
- bound to the wrong commit;
- produced by an invalid reviewer context.

---

# 20. Generated Assistant Entry Points

`AGENTS.md`, `CLAUDE.md`, and similar assistant-specific files should not be canonical process sources. They are **small repository-local adapter outputs** generated from the canonical policy, profile, and repository manifest.

Example header:

```text
THIS FILE IS GENERATED.

Process source: suyog19/software-engineering-process
Process version: 1.3.0
Process revision: <exact process SHA>
Profile: frontend
Repository configuration: .engineering/process.yaml

Do not edit this file directly.
```

These files should contain only the always-needed bootstrap contract:

- process identity and pinned revision;
- non-negotiable controls;
- classification requirement;
- repository-specific essentials;
- how to discover the current Effective Obligation Set;
- where compatible Skills are installed or materialized;
- how to produce required evidence.

Detailed specialist procedure should not be duplicated into these files. Current Codex and Claude Code capability models support loading Skills only when needed.[^R8][^R10]

# 21. Important Token-Efficiency Constraint

A naive implementation would materialize every process rule, profile rule, role, workflow, and approval policy into each assistant's startup instructions. That should be avoided.

The preferred model is **shallow progressive disclosure**:

```text
small always-loaded contract
        ↓
trusted classification / obligation resolution
        ↓
direct activation of relevant Skills and evidence schemas
```

Codex documents progressive disclosure for Skills, and Claude Code supports the same `SKILL.md`-oriented pattern.[^R8][^R10]

A July 2026 controlled study found that one-level progressive disclosure became useful as the information corpus scaled, while a deeper routing level did not improve results and sometimes hurt accuracy. This is emerging evidence, but it argues against building a deeply nested context-routing hierarchy before measurements justify it.[^R19]

# 22. Evidence Architecture and Attestation Model

Readiness evidence should be machine-readable and bound to the **exact revision** it validates.

The design should borrow the proven attestation pattern rather than inventing unrelated evidence structures. The in-toto Statement specification binds an attestation to a subject digest and identifies a predicate type. SLSA Source provenance similarly treats evidence as belonging to an immutable source revision, and in-toto defines a test-result predicate specifically for proving that required tests were executed and passed.[^R5][^R6][^R7]

Software Signal Engineering does not need full SLSA adoption in V1. It should reuse the model:

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [{
    "name": "suyogjoshi-platform",
    "digest": {
      "gitCommit": "<exact-sha>"
    }
  }],
  "predicateType": "https://suyogjoshi.com/software-signal/engineering/independent-review/v1",
  "predicate": {
    "processVersion": "1.3.0",
    "processRevision": "<process-sha>",
    "classification": "Protected",
    "capability": "independent-review",
    "verdict": "pass",
    "findings": [],
    "residualRisk": []
  }
}
```

V1 evidence may be unsigned, schema-validated JSON produced by trusted jobs or approved roles. Protected workflows may later add cryptographic signing or trusted attestation storage if the threat model justifies it.

Required evidence types may include:

- classification verdict;
- UX design/conformance verdict;
- architecture decision where required;
- validation/test result;
- Functional QA verdict;
- Non-Functional QA verdict;
- Independent Review verdict;
- Solution Sufficiency record when triggered;
- human approval record;
- deployment/release evidence.

Evidence joins must fail when required evidence is absent, stale, contradictory, bound to another revision, or produced from an invalid review context.

# 23. Small Always-Loaded Contract

`AGENTS.md` should contain only what every coding session must know:

- process identity/version;
- repository profile;
- non-negotiable controls;
- branch/issue fundamentals;
- classification requirement;
- how to discover additional role/workflow instructions;
- repository-specific implementation essentials.

The target should be a compact document rather than a process encyclopedia.

---

# 24. Conditional Context Loading

After trusted classification and policy evaluation, only the Skills and references required by the Effective Obligation Set should be exposed to the agent.

Example:

```text
Typo fix
  → Lean obligations
  → core bootstrap + lightweight-review Skill

Major frontend journey
  → Standard obligations
  → UX Skill + Functional QA Skill + Independent Review Skill

Payment backend change
  → Protected obligations
  → architecture + EM/sufficiency + FQA + NFQA + Independent Review
```

The process platform should avoid adding another multi-level router above native Skill discovery unless measurements show that it is necessary. Current Codex/Claude implementations already provide on-demand Skill loading, and controlled 2026 research suggests that a single disclosure level can outperform deeper routing for larger information sets.[^R8][^R10][^R19]

# 25. Token Budget as a First-Class Engineering Requirement

The common process should include a design requirement:

> Process inheritance must support progressive disclosure. The complete engineering process must not be materialized into every agent context.

This should be considered as important as:

- maintainability;
- correctness;
- security;
- traceability.

The process itself is part of the agent runtime environment, so its context footprint matters.

---

# 26. Avoid Repeating Process History

Repository instructions should contain current rules, not long historical explanations.

Reasoning and design history should live in:

- ADRs;
- issues;
- process design documents.

Agent runtime instructions should contain only information needed to execute correctly.

This further reduces token overhead.

---

# 27. Local Process Layout

A participating repository should remain small and understandable:

```text
AGENTS.md                  # small generated Codex entrypoint when used
CLAUDE.md                  # small generated Claude entrypoint when used

.engineering/
├── process.yaml           # repository differences and profile selection
├── process.lock           # exact resolved central process revision
└── generated/             # optional adapter/evidence metadata

<assistant-native skill location>/
└── ...                    # selected/materialized compatible Skills
```

The canonical Skill source remains in the process repository. Adapters may materialize or synchronize it into the assistant's expected repository-local location. This avoids making the policy model depend on a vendor-specific directory convention while still consuming native Skill support.

Agents load only Skills selected by the effective obligation set or natively discovered as relevant.

# 28. Process Versioning

Every repository should pin a process version.

Example:

```yaml
process:
  source: suyog19/software-engineering-process
  version: 1.3.0
  revision: <exact-git-sha>
```

This provides:

- reproducibility;
- controlled upgrades;
- rollback;
- process-change review;
- avoidance of surprise changes.

A central process update should not silently alter every active repository.

---

# 29. Process Upgrade Workflow

A process upgrade could create a repository PR such as:

```text
Upgrade engineering process 1.3.0 → 1.4.0
```

The PR should show:

- changed inherited rules;
- changed generated files;
- local override conflicts;
- newly required roles;
- newly locked rules;
- validation result.

This makes process evolution reviewable like any other software dependency.

---

# 30. Process Validation and Native Enforcement

Each participating repository should run policy validation in CI:

```bash
engineering-process validate
```

Validation should check:

- manifest schema;
- process source/version/revision;
- profile existence;
- override legality;
- generated assistant entrypoint freshness;
- Skill references;
- forbidden weakening of locked rules;
- classification evidence;
- exact-revision evidence binding;
- evidence completeness for the selected obligation set.

However, the validator should not recreate controls that the hosting platform can enforce more strongly.

Recommended enforcement mapping:

| Policy meaning | Preferred enforcement point |
|---|---|
| Required CI/test verdict | GitHub required status check |
| Protected branch/merge rule | GitHub ruleset / protected branch |
| Human production approval | GitHub Environment required reviewer where available |
| Prevent deployment self-approval | GitHub Environment self-review prevention |
| Process/manifest legality | engineering-process validator |
| Protected classification | classification policy + deterministic CI signals |
| Exact revision evidence | attestation/evidence join |
| Specialist procedure | Agent Skill / human procedure |

GitHub documents required status checks that block merge until required checks pass, and protected environments can require reviewers and prevent the deployment initiator from approving their own deployment.[^R12][^R13]

The canonical process owns the rule's semantics; native platforms enforce it when they have a reliable mechanism.

# 31. Policy Evaluation and Adapter Materialization

The core operation is policy evaluation, not workflow orchestration.

Conceptually:

```text
load core policy
load selected profile
apply valid repository overrides
collect issue/change characteristics
combine deterministic and semantic classification evidence
resolve delivery profile
compute Effective Obligation Set
map obligations to native enforcement / Skills / human approvals
generate compact assistant-specific bootstrap files
verify required evidence schemas
```

The output should answer:

- which capabilities are required;
- which approvals are required;
- which evidence predicates must exist;
- which actions are forbidden;
- which native platform gates must pass;
- which assistant Skills are relevant.

Before generating new machinery, the adapter applies a **native capability first** rule:

> If the target coding assistant or platform already provides a reliable mechanism that satisfies the policy requirement, configure or invoke that mechanism rather than recreating it.

This prevents Software Signal Engineering from becoming an unnecessary orchestration/runtime layer. OPA provides strong precedent for separating declarative policy decisions from enforcement, but V1 should remain simpler: YAML + JSON Schema + a small deterministic semantic validator are sufficient until policy complexity demonstrates a need for a dedicated policy engine.[^R4]

# 32. New Repository Bootstrap

New repositories should inherit the process through an initialization command.

```bash
engineering-process init --profile frontend
```

or:

```bash
engineering-process init --profile backend
```

This may create:

```text
.engineering/process.yaml
.engineering/process.lock
AGENTS.md                   # when Codex adapter is enabled
CLAUDE.md                   # when Claude adapter is enabled
.github/workflows/process-validation.yml
<assistant-native skill locations>/*
```

The bootstrap should also report which GitHub-native protections are recommended or required but cannot be created automatically under the current repository/plan/permission context.

A new repository therefore begins with a pinned policy baseline, explicit local differences, compatible Skill materialization, validation, and clear native-enforcement expectations.

# 33. Repository Override Example: Frontend

Suppose a frontend repository is a public web application.

It may add:

```yaml
overrides:
  ux:
    senior_ux_designer:
      additional_required_when:
        - checkout_journey
        - learner_dashboard
        - admin_workflow

  accessibility:
    required_for:
      - public_ui_change

  validation:
    commands:
      - node --test tests/*.test.js
      - npm run accessibility-check
```

The repository strengthens the common frontend process but does not redefine it.

---

# 34. Repository Override Example: Backend

Suppose a backend repository has particularly strict payment requirements.

It may add:

```yaml
overrides:
  protected:
    additional_characteristics:
      - learner_entitlement
      - commercial_deadline

  validation:
    commands:
      - ruff check .
      - pytest
      - sam validate --template infra/template.yaml --lint
```

Again, the repository extends the process without duplicating the process definition.

---

# 35. Cross-Repository Projects

Some future systems may contain multiple repositories.

For example:

```text
System X
├── frontend repository
├── backend repository
└── infrastructure repository
```

Each repository can inherit the appropriate profile while sharing the same core.

A higher-level project manifest may eventually coordinate cross-repository workflow, but this is not required for the first version.

---

# 36. Handling Full-Stack Repositories

A future repository may contain both frontend and backend code.

Two options should be supported.

### Option A: Composite profile

```yaml
profile:
  - frontend
  - backend
```

### Option B: Full-stack profile

```yaml
profile: fullstack
```

A full-stack profile could compose frontend and backend rules while resolving duplicate core behaviour.

This should be designed only when a real repository requires it.

---

# 37. Governance of the Common Process

Changes to the common process can have a large blast radius.

Therefore, the common process repository itself should follow a strong engineering workflow.

Changes should include:

- issue;
- rationale;
- impact analysis;
- compatibility considerations;
- schema changes;
- test coverage;
- migration strategy;
- affected profiles;
- sample repository validation.

Changes to locked controls should receive especially strong review.

---

# 38. Process Tests

The common process should have its own tests. Examples:

- frontend journey change selects UX capability;
- typo remains Lean;
- IAM change selects Protected;
- payment behaviour cannot be classified Lean;
- configured Protected path signal cannot silently downgrade assurance;
- unresolved Protected characteristic fails closed;
- classification evidence is bound to the tested revision;
- repository cannot disable fresh-context independent review where locked;
- repository may add UX requirement;
- invalid process version/revision fails;
- unknown profile fails;
- generated assistant entrypoints match source policy;
- stale generated files fail validation;
- self-review configuration fails;
- exact-revision evidence from another SHA fails readiness;
- missing mandatory evidence predicate fails readiness;
- token-loading plan selects only required Skills;
- specialist suggestions are not automatically converted into mandatory scope;
- Solution Steward cannot dismiss locked or blocking findings;
- unnecessary new abstraction can be classified as defer/reject;
- sufficiency stopping rule can close a review loop with nonessential improvements remaining;
- generic coding competence is not unnecessarily emitted into adapter output;
- assistant-native capability is preferred when it satisfies a policy requirement;
- Codex and Claude adapters preserve the same organizational obligation semantics;
- Developer role output contains constraints and obligations rather than implementation micromanagement;
- GitHub-native enforcement requirements are surfaced rather than duplicated as prompt-only reminders.

This makes the engineering process itself testable.

# 39. Explainability

The tooling should support an explanation command such as:

```bash
engineering-process explain issue-123
```

Example output:

```text
Repository profile: frontend
Delivery profile: Standard
Process: 1.3.0 @ <process-sha>
Target revision: <repo-sha>

Classification evidence:
- user_journey_change = true (issue + changed route)
- observable_behavior_change = true
- no Protected deterministic signal matched
- no payment/auth/IAM/production-control consequence identified

Effective obligations:
- Senior UX Designer
- Developer
- Functional QA
- Independent Review (fresh context)

Required evidence:
- ux-direction/v1
- functional-qa-verdict/v1
- independent-review/v1
- ci-test-result/v1

Native enforcement:
- required CI status check

Not required:
- Engineering Manager
- Non-Functional QA
- dedicated Solution Steward

Execution boundary:
- implementation technique delegated to coding assistant
- relevant Skills loaded on demand
```

This is important for both humans and agents. The process should not behave like an opaque policy engine.

# 40. Why This Model Is Preferable to Shared AGENTS.md

A single shared `AGENTS.md` template would solve only the most superficial duplication problem.

It would not adequately solve:

- domain profiles;
- selective specialist invocation;
- repository overrides;
- locked vs overridable rules;
- versioning;
- process testing;
- token-efficient loading;
- process compilation;
- explainability.

Therefore:

> `AGENTS.md` should be an output of the process system, not the process system itself.

---

# 41. Relationship to Process-as-Code

This design is a practical form of Process-as-Code.

The software engineering process becomes:

- version controlled;
- declarative;
- validated;
- inherited;
- testable;
- reviewable;
- reproducible;
- machine consumable;
- agent consumable;
- enforceable at native platform boundaries;
- capable of producing revision-bound evidence.

Open Policy Agent is useful architectural precedent: it treats policy as declarative data/code evaluated separately from the application or infrastructure enforcing the decision, and it supports policy checks in CI/CD.[^R4]

That precedent does **not** mean Software Signal should adopt OPA/Rego immediately. For V1, YAML, JSON Schema, and a small validator keep the solution sufficient and understandable. A dedicated policy engine should be introduced only when real policy composition or expression complexity earns the additional machinery.

# 42. Relationship to Agentic Software Engineering

The design deliberately follows this boundary:

> **Software Signal Engineering owns organizational engineering policy and assurance. Coding assistants own native engineering execution.**

Software Signal Engineering should become better when Codex, Claude Code, or future coding assistants become better rather than competing with their improvements.

The design separates:

```text
Engineering policy
        ↓
Required capability / obligation
        ↓
Portable procedure (Skill) where needed
        ↓
Runtime/model/native platform mechanism
```

Current product architecture supports this direction. Codex exposes repository instructions, Skills and progressive disclosure; Claude Code supports Skills, subagents, codebase reading/editing and command execution. The portable Agent Skills format reduces the need to invent a second procedure-packaging convention.[^R8][^R9][^R10][^R11][^R23]

Multi-agent participation should remain selective. MAST identifies failure modes in specification/system design, inter-agent alignment, and task verification/termination; adding more agents is therefore not automatically a reliability improvement.[^R17]

# 43. Proposed Effective Obligation and Workflow Example

Consider a future frontend issue:

> Improve the My Learning cancellation journey.

Initial characteristics:

```text
frontend
observable behaviour = true
user journey = true
financial consequence = possibly true
```

The process first performs trusted classification. If cancellation affects payment, refund, entitlement, or another Protected characteristic, the change cannot remain Standard merely because it originated in the frontend.

Conceptually:

```text
Issue / acceptance criteria
        ↓
Trusted classification
  + deterministic repository signals
  + semantic assessment
        ↓
Effective Obligation Set
        ↓
Senior UX Designer
        ↓
Frontend Architect if triggered
        ↓
Solution Sufficiency synthesis
        ↓
Human approval if Protected policy requires it
        ↓
Developer using native coding-assistant capability
        ↓
CI / exact-revision test evidence
        ↓
Functional QA
        ↓
UX conformance review
        ↓
NFQA if payment/security/operational implications exist
        ↓
Fresh-context Independent Review
        ↓
Solution Sufficiency triage of non-blocking additions
        ↓
Exact-revision evidence join
        ↓
GitHub/native merge and deployment gates
```

By contrast:

> Correct a typo on the About page.

would select:

```text
Lean obligations
    ↓
Developer
    ↓
focused validation
    ↓
lightweight fresh-context review
```

The same repository therefore supports both speed and rigor without requiring a custom orchestration runtime for either case.

# 44. Recommended Initial Scope

The first implementation should remain intentionally small.

## Phase 1 — Define policy and evidence contracts

Create the central repository with:

- core policy;
- frontend and backend profiles;
- locked/extensible/overridable semantics;
- trusted classification model;
- Effective Obligation Set schema;
- evidence/attestation schema inspired by in-toto;
- coding-assistant responsibility boundary;
- Solution Sufficiency capability;
- minimal repository schema.

Use YAML + JSON Schema + a small semantic validator. Do **not** introduce OPA/Rego unless V1 policy complexity requires it.

## Phase 2 — Package specialist capabilities as Skills

Create concise portable Skills for the procedures that genuinely need specialist framing:

- Senior UX review;
- Functional QA;
- Non-Functional QA;
- Independent Review;
- Solution Sufficiency;
- architecture review only where distinct procedure is useful.

Keep Developer and Orchestrator contracts thin.

## Phase 3 — Adopt in current repositories

Convert:

- `suyog19.github.io`;
- `suyogjoshi-platform`;

to manifests that reference a pinned common process version/revision. Generate small Codex and Claude bootstrap files and materialize compatible Skills where required.

Verify that no important existing control is lost.

## Phase 4 — Add validation, evidence joins, and native GitHub enforcement

Introduce:

- schema validation;
- locked-rule validation;
- process-version/revision validation;
- protected-classification checks;
- generated-file drift detection;
- exact-revision evidence joins;
- required GitHub status checks/ruleset guidance;
- GitHub Environment approval where available and required.

## Phase 5 — Measure context and process effectiveness

Measure:

- average always-loaded process tokens;
- number of activated Skills;
- unnecessary capability invocations;
- classification corrections or escalations;
- stale/wrong-revision evidence caught;
- specialist recommendations implemented, deferred, and rejected;
- review/fix expansion caused by non-mandatory feedback;
- instances where stewardship prevented unnecessary abstractions/services/scope;
- false-positive and false-negative Protected classifications;
- situations where a native assistant/platform feature allowed custom process machinery to be removed.

Only after these measurements should deeper routing, a dedicated policy engine, cryptographic attestations, or more elaborate orchestration be considered.

# 45. Success Criteria

The design is successful if:

1. frontend and backend share one core engineering policy;
2. differences are explicitly represented as profiles;
3. repository-specific rules are small and clear;
4. critical controls cannot be weakened accidentally;
5. new repositories can inherit the process without copy/paste;
6. trusted classification determines the Effective Obligation Set;
7. sensitive deterministic signals cannot silently route a Protected change to Lean;
8. Senior UX Designer participates automatically when frontend UX work requires it;
9. Protected backend controls remain intact;
10. `AGENTS.md` / `CLAUDE.md` are small generated adapter outputs rather than canonical policy;
11. specialist procedures use portable Skills where appropriate;
12. CI detects process drift and illegal overrides;
13. agents do not need the entire process for every task;
14. process-related token overhead remains small;
15. process policy remains tool-neutral;
16. process changes are versioned and reviewable;
17. specialist recommendations do not automatically become implementation scope;
18. material multi-agent changes have a clear minimum-sufficient design decision;
19. nonessential review feedback can be explicitly deferred or rejected;
20. the process has a usable stopping rule;
21. generic coding competence is not recreated in central policy;
22. Developer and Orchestrator roles remain thin;
23. Codex, Claude Code, and future assistants can map the same obligation semantics to their native mechanisms;
24. independent final review uses fresh context rather than relying on model/vendor naming as a proxy for independence;
25. critical evidence is bound to the exact repository revision;
26. stale or wrong-revision evidence cannot satisfy readiness;
27. platform-native enforcement is preferred over prompt-only reminders;
28. improvements in assistant-native capabilities can remove custom machinery without redesigning core policy;
29. V1 remains simple enough to understand and operate without a heavyweight policy engine.

# 46. Key Architectural Decisions

### Decision 1
There is **one software engineering policy/process model**. Frontend and backend are profiles of it.

### Decision 2
Repositories inherit a pinned version **and exact revision** of the process.

### Decision 3
Repositories express only local differences.

### Decision 4
Overrides are governed by locked, extensible, and overridable semantics.

### Decision 5
Agent roles represent capabilities, not model vendors.

### Decision 6
Change classification is a trusted control-plane decision and produces durable evidence.

### Decision 7
Classification combines declared intent, repository policy, deterministic signals, and semantic judgment; Protected ambiguity fails closed.

### Decision 8
Policy evaluation produces an **Effective Obligation Set**, not a detailed custom agent execution plan.

### Decision 9
The common process defines **WHAT must be true**; coding assistants and native platforms normally own **HOW**.

### Decision 10
`AGENTS.md`, `CLAUDE.md`, and similar files are small generated adapter outputs, not canonical process sources.

### Decision 11
Specialist procedures should use the portable Agent Skills format where it fits rather than an invented role-instruction format.

### Decision 12
Progressive disclosure should remain shallow: small bootstrap → resolved obligations → directly relevant Skills/references.

### Decision 13
Critical readiness depends on durable evidence rather than ephemeral agent context.

### Decision 14
Critical evidence is bound to the exact source revision using an attestation-style model.

### Decision 15
Independent final review requires a **fresh review context**. A different vendor/model is optional diversity, not the definition of independence.

### Decision 16
Solution Sufficiency / Complexity Stewardship is a core engineering capability but not necessarily a separate agent invocation.

### Decision 17
Specialist recommendations are not automatically additive requirements. Mandatory controls remain mandatory; nonessential recommendations are triaged.

### Decision 18
Generic coding competence is not part of central policy unless an organization/repository has a specific non-obvious requirement.

### Decision 19
The strongest reliable native enforcement point should be used: GitHub/CI for gates, Skills for procedure, attestations for revision-bound evidence.

### Decision 20
The process itself is versioned, validated, tested, and treated as software.

### Decision 21
V1 uses YAML + JSON Schema + a small semantic validator. OPA/Rego or another policy engine is deferred until real policy complexity justifies it.

### Decision 22
Software Signal Engineering should prefer reliable native coding-assistant/platform capabilities over reimplementing runtime functionality.

# 47. Open Design Questions

The following decisions remain appropriate for detailed design or implementation experiments:

1. What exact YAML schema best represents characteristics, obligations, locked rules, and evidence predicates?
2. Should `process.lock` pin both semantic version and commit SHA, or treat the SHA as authoritative and version as human-readable metadata?
3. How should the central process revision be retrieved and cached for offline/local work?
4. Which existing backend controls belong in core versus the backend profile?
5. Which frontend UX triggers should initially be mandatory?
6. What maximum always-loaded process token budget should V1 target?
7. How should token usage be measured consistently across Codex and Claude Code?
8. Which deterministic path/configuration signals should automatically strengthen classification in each current repository?
9. How should conflicting deterministic and semantic classification evidence be resolved?
10. Which human approvals require GitHub Environment enforcement versus durable evidence only?
11. What is the minimal common adapter contract for Codex and Claude Code?
12. Which Skills should be shared identically across assistants, and which require thin adapter-specific wrappers?
13. Should evidence objects be committed to the repository, stored as CI artifacts, attached to GitHub checks, or use another durable store?
14. At what risk level would signed attestations become worthwhile?
15. Should model/vendor diversity be recommended for particular Protected reviews, and how should its value be measured?
16. What review/fix-loop threshold should trigger explicit Solution Sufficiency stewardship?
17. Should complexity telemetry such as changed files/LOC/components remain informational or ever become a policy trigger?
18. How should assistant-native feature evolution be detected so obsolete custom adapters or instructions can be removed?
19. How should cross-repository classification and evidence work when a single change spans frontend, backend, and infrastructure repositories?
20. Which measurements will tell us that the process is improving reliability without adding disproportionate ceremony?

These questions do not block the architecture. They are implementation decisions to resolve through current-repository adoption and measurement.

# 48. Final Recommendation

Build a **versioned Software Engineering Policy and Assurance platform** rather than maintain independent repository-specific agent instructions or create a competing multi-agent runtime.

The conceptual model is:

```text
Canonical Engineering Policy
          ↓
      Domain Profile
          ↓
 Repository Configuration
          ↓
 Trusted Change Classification
          ↓
 Effective Obligation Set
          ↓
 Selected Skills + Native Controls + Human Boundaries
          ↓
 Coding / Review Execution
          ↓
 Exact-Revision Evidence
          ↓
 Readiness Verification
          ↓
 Merge / Deployment
```

The system should preserve a common engineering philosophy while allowing frontend, backend, and future repositories to apply the amount and type of assurance appropriate to their domain.

It should deliberately avoid competing with Codex, Claude Code, GitHub, CI systems, or future tools on capabilities they already provide reliably. Software Signal Engineering defines organizational obligations, decision authority, required perspectives, evidence, readiness, and limits on local weakening; native tools fulfil or enforce those obligations wherever possible.

Classification must be treated as part of the trusted control plane because it determines which obligations are selected. Critical evidence must be bound to the exact revision because readiness claims without revision identity are vulnerable to staleness and mismatch.

The process should be inherited, but not blindly copied.

It should be customizable, but not casually weakened.

It should be enforceable, but not orchestration-heavy.

It should be comprehensive, but not loaded into every agent context.

It should use specialist agents when independent perspective materially improves assurance, but should not assume that more agents automatically mean better engineering.

And it should remain simple enough that its own implementation obeys its governing principle: **the smallest system sufficient to preserve intent, required quality, authority, evidence, and material risk.**

# 49. Evidence Basis and External References

This design deliberately distinguishes **mature architectural anchors** from **emerging agent research**. Standards and primary product/platform documentation justify durable structural choices. Recent research papers identify failure modes and design hypotheses that should be measured in Software Signal repositories before being promoted into permanent locked policy.

## 49.1 Mature standards and primary technical references

[^R1]: ISO/IEC/IEEE 12207:2026, *Systems and software engineering — Software life cycle processes*. Establishes a common framework for software life-cycle processes and permits application across different organizational/project approaches. https://www.iso.org/standard/90219.html

[^R2]: NIST SP 800-218, *Secure Software Development Framework (SSDF) Version 1.1*. Defines a core set of high-level secure software-development practices intended to be integrated into SDLC implementations. https://csrc.nist.gov/pubs/sp/800/218/final

[^R3]: NIST SP 800-53B, *Control Baselines for Information Systems and Organizations*, including tailoring guidance and overlays for contextual customization of control baselines. https://csrc.nist.gov/pubs/sp/800/53/b/upd1/final

[^R4]: Open Policy Agent documentation. OPA demonstrates declarative policy-as-code and separation of policy decision-making from application/enforcement logic, including CI/CD guardrails. https://openpolicyagent.org/docs

[^R5]: in-toto Attestation Framework, *Statement v1*. The Statement binds a predicate to a particular subject and its digest. https://in-toto.io/Statement/v1

[^R6]: in-toto Attestation Framework, *Test Result Predicate*. Defines attestations for expressing whether required tests ran and passed. https://in-toto.io/attestation/test-result/

[^R7]: SLSA v1.2, *Source Requirements*. Describes provenance attestations associated with immutable source revisions and the controls used to produce them. https://slsa.dev/spec/v1.2/source-requirements

[^R8]: OpenAI Codex documentation, *Build skills*. Documents `SKILL.md`-based Skills and progressive disclosure, where metadata is loaded first and full instructions only when the Skill is used. https://developers.openai.com/codex/build-skills

[^R9]: OpenAI Codex documentation, *Customization*. Documents repository/global instructions, Skills, and progressive-disclosure customization mechanisms. https://developers.openai.com/codex/customization/overview

[^R10]: Anthropic Claude Code documentation, *Extend Claude with skills*. Documents Claude Code Skills and states that they follow the Agent Skills open standard. https://docs.anthropic.com/en/docs/claude-code/skills

[^R11]: Anthropic Claude Code documentation, *Overview*. Documents codebase reading, file editing, command execution, and development-tool integration as native capabilities. https://docs.anthropic.com/en/docs/claude-code/overview

[^R12]: GitHub documentation, *Available rules for rulesets*. Required status checks can require CI checks to pass before merge. https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets

[^R13]: GitHub documentation, *Deployments and environments*. Protected environments can require reviewers and prevent deployment self-review. https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

[^R14]: NIST CSRC Glossary, *Separation of Duty*. Defines the security principle that one actor should not have sufficient privileges to misuse a system alone. https://csrc.nist.gov/glossary/term/separation_of_duty

[^R15]: ISO 9241-210, *Human-centred design for interactive systems*. Defines human-centred design principles and activities throughout the life cycle of interactive systems. https://www.iso.org/standard/77520.html

[^R16]: W3C Web Accessibility Initiative, *WCAG 2 Overview*. Provides accessibility guidance, success criteria, and related design/development and test/evaluation resources. https://www.w3.org/WAI/standards-guidelines/wcag/

[^R23]: Agent Skills, *Specification*. Defines the open `SKILL.md` directory format, optional scripts/references/assets, and progressive-disclosure model for portable agent capabilities. https://agentskills.io/specification

## 49.2 Emerging empirical evidence for agent-specific safeguards

[^R17]: Cemri et al. (2025), *Why Do Multi-Agent LLM Systems Fail?* Introduces MAST, an empirical taxonomy of multi-agent failures grouped around specification/system design, inter-agent misalignment, and task verification/termination. arXiv:2503.13657. https://arxiv.org/abs/2503.13657

[^R18]: Tang et al. (2026), *How Coding Agents Fail Their Users: A Large-Scale Analysis of Developer-Agent Misalignment in 20,574 Real-World Sessions*. Reports recurring misalignment across project understanding, intent, constraints/rules, action boundaries, execution, and reporting in 1,639 repositories. arXiv:2605.29442. https://arxiv.org/abs/2605.29442

[^R19]: He et al. (2026), *Is Progressive Disclosure All You Need for Long-Context Agents?* Finds that one-level progressive disclosure can help as the corpus scales, while a deeper routing level did not improve the tested settings and sometimes harmed accuracy. arXiv:2607.17598. https://arxiv.org/abs/2607.17598

[^R20]: Orlanski et al. (2026), *SlopCodeBench: Benchmarking How Coding Agents Degrade Over Long-Horizon Iterative Tasks*. Reports increasing verbosity and structural erosion across iterative coding-agent trajectories, motivating measurement of complexity growth and minimum-sufficient design. arXiv:2603.24755. https://arxiv.org/abs/2603.24755

[^R21]: Pombal, Rei, and Martins (2026), *Self-Preference Bias in Rubric-Based Evaluation of Large Language Models*. Reports self-preference effects in LLM evaluation, supporting fresh-context independent assurance rather than sole reliance on a generator's own evaluative judgment. arXiv:2604.06996. https://arxiv.org/abs/2604.06996

[^R22]: Mitropoulos et al. (2026), *Measuring and Exploiting Confirmation Bias in LLM-Assisted Security Code Review*. Reports that framing can materially affect LLM vulnerability detection and demonstrates practical attacks against LLM-assisted code review, supporting evidence-focused and context-independent review practices. arXiv:2603.18740. https://arxiv.org/abs/2603.18740

## 49.3 Evidence-use rule for future process changes

A proposed locked process rule should preferably be justified by one or more of:

1. established software-engineering/security/control principles;
2. authoritative platform capability or enforcement constraints;
3. repeated observed failures in Software Signal repositories;
4. replicated or sufficiently strong empirical research relevant to the actual failure being controlled.

A single recent preprint should normally motivate an experiment, telemetry, or conservative safeguard—not by itself create irreversible process ceremony.
