# Loop Engineering System v3.0
## Complete User-Project Execution, Vibe-Prompt Goals, Loop Autonomy, and Source Knowledge Graph Governance

**Purpose:** enable a coding agent to create and complete a real user project while every project change is governed by bounded loops, independent verification, workspace ownership, and source-linked knowledge artifacts.

---

## 0. System model

The system has two planes inside one Git workspace:

```text
CONTROL PLANE                           USER PROJECT PLANE
AGENTS.md                               framework-native application files
.agentic/protocol/**                    src/, app/, packages/, services/
.agentic/config/**                      tests/, e2e/, docs/, assets/
.agentic/policy/**                      package.json, pyproject.toml, etc.
.agentic/runtime/**
.agentic/knowledge/**
.agentic/scripts/**
.agentic/schemas/**
```

The control plane governs *how* work is performed. The user prompt and project specification define *what* is built. The control plane may never substitute its own product goals for the user's intent.

### Authority order

1. Git objects, exact exit codes, hashed evidence, append-only runtime events.
2. Human-authored user prompt, project specification, requirements, VISION constraints.
3. Derived STATE, VERSIONS, PROJECT-STATUS, KG views.
4. Agent plans, hypotheses, summaries, classifications.

### Roles

- **Human/User:** supplies product intent, vibe-coding prompts, constraint changes, and final project acceptance.
- **Orchestrator:** classifies prompts, opens goals, enforces budgets and path scopes, appends events.
- **Maker:** edits only authorized project paths and never declares completion.
- **Verifier:** independently evaluates completion conditions without maker narrative.
- **Validator:** performs deterministic system, scope, project, Git, and KG checks.
- **KG Builder:** extracts source-linked facts and stages generated knowledge artifacts.
- **Protocol Maintainer:** may edit control-plane files only under an explicit system-maintenance goal.

---

## 1. Workspace and ownership protocol

```text
WB-001 [W1] Every governed repository MUST contain `.agentic/config/workspace.json`.
WB-002 [W1] `workspace.json` is the machine authority for project roots, control root, path ownership, protected paths, generated paths, validation working directories, and KG exclusions.
WB-003 [W1] The first matching ownership rule classifies a path. Unclassified paths are non-writable.
WB-004 [W1] Ordinary project goals may write only PROJECT-owned paths explicitly listed in the goal's allowed_write_paths.
WB-005 [W1] Makers may never modify CONTROL_PLANE, RUNTIME_STATE, or KNOWLEDGE_GENERATED paths.
WB-006 [W1] A SYSTEM_MAINTENANCE goal must be explicitly requested by the user and set system_change_authorized=true.
WB-007 [W1] Protected paths remain denied even when a broad allowed pattern matches them.
WB-008 [W1] Before verification and before merge, compare the baseline and candidate Git trees and reject every changed path outside the goal scope.
WB-009 [W2] Project commands run from the declared project.command_cwd, not implicitly from the control-plane directory.
WB-010 [W2] KG extraction excludes control, runtime, generated, vendor, secret, and build-output paths by default.
```

The user application keeps its natural framework layout. The protocol does not force Next.js, Python, Go, monorepos, or any other project into a synthetic `project/` directory. Nested and multi-project layouts are declared through `projects[]`.

---

## 2. User prompt and goal-intake protocol

Each user coding message is preserved exactly and transformed into a typed goal contract.

### Goal kinds

- `PROJECT_CREATE`: initialize or scaffold a new user application.
- `PROJECT_TASK`: implement or fix a bounded product behavior.
- `PROJECT_MAINTENANCE`: refactor, dependency update, performance work, tests, documentation, or deployment work in the user project.
- `SYSTEM_MAINTENANCE`: modify Loop/KG/control-plane assets; never inferred from a normal coding request.

```text
GI-001 [W1] Preserve the user's raw prompt verbatim with a prompt_id before normalization.
GI-002 [W1] Default an ordinary vibe-coding request to PROJECT_TASK for default_project_id.
GI-003 [W1] A goal contract must state project_id, intent summary, affected requirements, allowed and denied write paths, assumptions, and completion conditions.
GI-004 [W1] Every completion condition is TYPE A exit code, TYPE B repository/file state, TYPE C numeric threshold, or pre-approved TYPE D judgment.
GI-005 [W1] Runtime-invented TYPE D conditions are forbidden.
GI-006 [W2] When a detail is missing but a safe reversible default exists, record the assumption and continue. When ambiguity can materially change architecture, data safety, cost, or product meaning, block or request human direction.
GI-007 [W1] The prior-goal gate runs before allocating a new goal ID. IN_PROGRESS resumes; ESCALATED blocks; COMPLETED or ABANDONED permits a new goal.
GI-008 [W1] Capture git_sha_before and git_tree_before in GOAL_CREATED before any project write.
```

---

## 3. Project creation lifecycle

A greenfield project is not treated as one unrestricted edit. It follows this lifecycle:

```text
PROJECT INTAKE
→ PRODUCT SPECIFICATION
→ REQUIREMENT LEDGER
→ STACK/ARCHITECTURE DECISION
→ WORKSPACE MANIFEST
→ REVERSIBLE SCAFFOLD
→ BASELINE BUILD/TEST
→ BASELINE SOURCE KG
→ MILESTONE GOALS
→ USER VIBE-PROMPT LOOPS
→ PROJECT ACCEPTANCE
```

```text
PC-001 [W1] Before scaffolding, declare the target project_id and root in workspace.json.
PC-002 [W1] Scaffolding may not overwrite non-empty project paths unless the user explicitly authorizes migration or replacement.
PC-003 [W2] Record stack decisions and their user constraints in PROJECT-SPEC.md.
PC-004 [W1] Create machine-readable MUST/SHOULD/COULD requirements with acceptance conditions.
PC-005 [W1] Baseline validation must pass or its failures must be recorded as pre-existing before feature work begins.
PC-006 [W2] Build the initial source KG from the scaffolded repository after baseline validation.
PC-007 [W1] Project creation completes only through the project-completion protocol, not when scaffolding finishes.
```

---

## 4. Product specification and requirement graph

`PROJECT-SPEC.md` describes the complete desired product. `REQUIREMENTS.json` is its machine-readable acceptance ledger.

Requirement states:

```text
OPEN → IN_PROGRESS → IMPLEMENTED → VERIFIED
  ↘ BLOCKED
  ↘ DEFERRED
```

```text
RQ-001 [W1] A goal must link every requirement it intends to satisfy.
RQ-002 [W1] A maker may mark work implemented only through an event; only independent evidence can move a requirement to VERIFIED.
RQ-003 [W1] Requirement evidence must identify the goal, candidate Git tree, verification item, and evidence hash.
RQ-004 [W2] Newly discovered product requirements are proposed, not silently added as mandatory scope.
RQ-005 [W1] A task goal completing does not imply project completion.
```

The resulting knowledge relationship is:

```text
Requirement → SATISFIED_BY → Goal → IMPLEMENTED_BY → Commit/Tree
Requirement → VERIFIED_BY → Test/Evidence
Commit/Tree → CHANGES → File/Symbol
```

---

## 5. Canonical goal loop

```text
PHASE 0  BOOT
  Read AGENTS, workspace, protocol, project spec, requirements, VISION.
  Validate event chain and rebuild projections.
  Observe VISION hash without overwriting the accepted hash.

PHASE 1  PROMPT GATE
  Preserve raw user prompt.
  Classify goal kind and project.
  Check prior goal and human blockers.
  Build and validate goal contract.
  Capture baseline Git commit/tree and append GOAL_CREATED.

PHASE 2  PLAN
  Build tasks, dependencies, budgets, allowed write paths, checks, and rollback boundary.
  Load current source KG and only relevant skills/context.

PHASE 3  IMPLEMENT LOOP
  Select one task.
  Build a maker packet.
  Maker edits authorized project paths only.
  Run cheap local checks.
  Record attempt, strategy, files, exit codes, evidence, and plain-language summary.
  On failure: falsify the strategy, select a materially different next strategy, and retry within limits.

PHASE 4  SCOPE GATE
  Commit or identify the candidate tree.
  Compare baseline to candidate.
  Reject protected, denied, control-plane, runtime, generated, and out-of-scope changes.

PHASE 5  INDEPENDENT VERIFICATION
  Build a sanitized verifier packet.
  Verifier receives goal conditions, baseline/candidate anchors, and repository access.
  Verifier does not receive maker packet, maker log, maker confidence, or maker summary.
  Record evidence per condition. Any failed condition returns to Phase 3.

PHASE 6  FAST STOP GATE
  Run fast deterministic project checks and state-presence checks.
  Three unchanged-code failures escalate as an environment/control failure.

PHASE 7  KG TRANSACTION
  Extract only declared project paths from the verifier-approved tree.
  Write nodes, edges, provenance, and views to staging.
  Validate schemas, hashes, source spans, edge references, tree binding, and exclusions.
  Atomically promote the staged release. Never edit a promoted release.

PHASE 8  COMPREHENSIVE VALIDATION
  Validate control plane, event chain, projections, path scope, project commands, Git anchors, KG release, and requirement evidence.

PHASE 9  COMPLETE
  Append GOAL_COMPLETED only after verifier pass, scope pass, KG promotion, and comprehensive validation.
  Update requirement projections and emit the human summary.

PHASE 10 ESCALATE
  Stop active agents, append GOAL_ESCALATED, preserve exact evidence and attempted strategies, and wait for human resolution.
```

---

## 6. Loop autonomy and strategy rules

```text
LA-001 [W1] Autonomy is bounded by goal, path scope, budgets, constraints, and deterministic completion conditions.
LA-002 [W1] The loop may change implementation strategy but not the user's product meaning.
LA-003 [W1] Retrying the same failed strategy without new evidence is forbidden.
LA-004 [W1] Retry limits are finite: default 3 simple and 7 complex attempts; budget may end earlier.
LA-005 [W2] Each failed attempt records hypothesis, evidence, falsification result, rejected path, next strategy, token cost, and changed files.
LA-006 [W1] A loop may not weaken, delete, skip, or rewrite a failing test/validator unless the user goal explicitly changes that requirement and independent evidence validates the replacement.
LA-007 [W1] A loop may not edit the control plane to make a project goal pass.
LA-008 [W2] Parallel agents require isolated worktrees and a serial orchestrator-owned merge queue.
```

---

## 7. Agent packet isolation

Maker packet contains user goal, current task, project root, allowed/denied paths, baseline anchors, completion conditions, and relevant context files.

Verifier packet contains completion conditions, project root, allowed/denied paths, baseline and candidate anchors, and explicit forbidden context.

```text
AP-001 [W1] Verifier access to maker narrative or session logs is prohibited.
AP-002 [W1] The verifier independently executes every check and binds every PASS to the candidate tree.
AP-003 [W1] The verifier cannot modify project or control-plane files.
AP-004 [W2] Security, payments, destructive migrations, identity, or safety-critical work requires a second independent check or human gate declared in VISION.
```

---

## 8. Runtime authority and projections

The append-only `.agentic/runtime/LOOP-EVENTS.jsonl` is execution authority. STATE, VERSIONS, and PROJECT-STATUS are deterministic projections and must never be manually reconciled.

```text
EV-001 [W1] Events are contiguous, hash chained, append-only, and orchestrator serialized.
EV-002 [W1] Corrections use compensating events, never event mutation.
EV-003 [W1] Projections are rebuilt before every run and must match the reducer exactly.
EV-004 [W1] Raw user prompts, goal creation, maker attempts, verification items, KG promotion, requirement transitions, completion, escalation, abandonment, and human resolution are evented.
EV-005 [W2] Evidence files are content hashed and referenced from events.
```

---

## 9. Source knowledge graph

Markdown architecture documents are generated views, not graph authority.

Minimum node types: Project, Module, File, Symbol, Class, Function, Method, Type, Endpoint, Table, Config, Test, Requirement, Goal, Commit, RuntimeEvent, Issue.

Minimum edge types: CONTAINS, DEFINES, IMPORTS, CALLS, INHERITS, IMPLEMENTS, READS, WRITES, EXPOSES, TESTED_BY, SATISFIES, CHANGED_BY, VERIFIED_BY, OBSERVED_IN, SUPERSEDES.

Every source-derived node or edge records extractor name/version, source path/span, file hash, Git commit/tree, confidence, and generation timestamp.

```text
KG-001 [W1] Extract only from the verifier-approved Git tree.
KG-002 [W1] Exclude every workspace.kg_exclude path.
KG-003 [W1] No source fact without provenance.
KG-004 [W1] Stage → validate → atomically promote.
KG-005 [W1] A promoted release is immutable and bound to one Git tree.
KG-006 [W2] Incremental invalidation uses changed file hashes and reverse dependency edges.
KG-007 [W2] Runtime observations never overwrite static facts; they are separate OBSERVED_IN evidence.
KG-008 [W1] Escalated or abandoned goals do not receive a promoted post-goal KG version.
```

---

## 10. Deterministic validation groups

```text
A. Control-plane integrity
   Required files, JSON schemas, workspace semantics, path classes, no unsafe overlaps.

B. Runtime integrity
   Event hash chain, event transition invariants, exact projection rebuild.

C. Goal and scope integrity
   Goal schema, prior-goal gate, baseline anchors, candidate changed-path authorization.

D. Project quality
   Project-profile commands executed from declared cwd; success determined by exit code and explicit assertions.

E. Independent verification
   Every condition has evidence bound to the candidate tree; verifier packet contains no forbidden maker context.

F. Knowledge graph
   Staging/promoted manifest, artifact hashes, source provenance, valid edges, tree binding, exclusion compliance.

G. Requirement/project completion
   Requirement evidence and mandatory coverage; project acceptance gate.
```

A missing tool is a failed required check, not a pass or silent skip.

---

## 11. Task completion versus project completion

A goal is complete when its bounded conditions pass. The whole project is complete only when:

1. Every `MUST` requirement is `VERIFIED` with immutable evidence.
2. Project-wide acceptance checks pass on the final Git tree.
3. No P0/P1 or explicitly blocking issue remains.
4. Deployment/release checks required by PROJECT-SPEC pass.
5. The final KG release matches the accepted project tree.
6. The user explicitly accepts the result.

```text
PJ-001 [W1] Only a human acceptance action can append PROJECT_COMPLETED.
PJ-002 [W1] PROJECT_COMPLETED is rejected unless PROJECT-STATUS is READY_FOR_ACCEPTANCE.
PJ-003 [W1] Later work reopens project status when it changes a verified requirement or accepted tree.
PJ-004 [W2] Produce a final requirement-to-goal-to-commit-to-test evidence report.
```

---

## 12. System maintenance separation

```text
SM-001 [W1] A normal user coding prompt never authorizes changes to AGENTS.md or `.agentic/**`.
SM-002 [W1] System maintenance uses a separate goal kind, explicit authorization, protocol-maintainer role, and system-specific validation profile.
SM-003 [W1] System maintenance cannot modify the user project unless those project paths are separately authorized.
SM-004 [W1] A system validator cannot approve its own changed implementation; use the prior trusted validator or an external/human gate.
SM-005 [W2] Protocol version upgrades are migrations with backups, schema transitions, and rollback instructions.
```

---

## 13. Escalation conditions

Escalate on exhausted attempts or budget, protected-path request, goal contract change after implementation, verifier BLOCKED, repeated unchanged-code gate failure, missing authority file, event/projection corruption, KG transaction failure, ambiguous destructive operation, unsafe rollback, or required-tool absence.

Every escalation includes exact code, goal/task IDs, baseline/candidate anchors, actionable error excerpt, full evidence reference, attempted strategies, best root-cause hypothesis, and a specific human resolution request.

---

## 14. Golden rules

```text
The user defines the product.
The workspace manifest defines ownership.
The goal contract defines the bounded change.
The maker implements but cannot approve.
The verifier proves but cannot modify.
The validator trusts exit codes, hashes, schemas, and Git trees.
The KG describes the accepted project tree with provenance.
A completed task is not automatically a completed project.
No project goal may rewrite the system that judges it.
```
