# Loop Engineering v3.0 — Complete Project Execution System

This package installs a governed coding-agent control plane into an existing or new Git project. It resolves the core boundary problem:

- **User project files** remain in their normal framework-native layout.
- **Loop/KG system files** live under `.agentic/`.
- Root `AGENTS.md` is a thin discovery and boot instruction.
- `.agentic/config/workspace.json` machine-classifies ownership, roles, protected paths, project roots, validation working directories, and KG exclusions.
- Ordinary vibe-coding prompts become bounded project goals; they do not authorize changes to the system that judges them.

## Install

```bash
python3 -m pip install -r system/scripts/requirements.txt
python3 install.py /path/to/user-project
cd /path/to/user-project
python3 .agentic/scripts/agenticctl.py --root . validate
```

For a new empty directory:

```bash
python3 install.py ./my-new-project --init-git
```

Then complete:

- `.agentic/policy/PROJECT-SPEC.md`
- `.agentic/policy/REQUIREMENTS.json`
- `.agentic/policy/VISION.md`
- `.agentic/config/workspace.json`
- `.agentic/config/loop-validation.json`

## Register a user goal

The coding agent converts the user's exact prompt into a JSON goal contract matching `.agentic/schemas/goal.schema.json`.

```bash
python3 .agentic/scripts/agenticctl.py --root . register-goal --goal-file /tmp/goal.json
python3 .agentic/scripts/agenticctl.py --root . maker-packet --goal-id G001
```

Before verification:

```bash
python3 .agentic/scripts/agenticctl.py --root . verify-scope --goal-id G001
python3 .agentic/scripts/agenticctl.py --root . verifier-packet --goal-id G001
```

## What is executable now

- installation and layout detection;
- workspace/path ownership validation;
- exact user-goal contracts;
- append-only hash-chained events;
- deterministic STATE/VERSIONS/PROJECT-STATUS rebuilding;
- prior-goal sequencing;
- maker/verifier packet separation;
- candidate diff scope enforcement;
- project commands executed from declared project roots;
- requirement-level versus project-level completion;
- source-KG protocol and transaction contract.

Language-specific AST/LSP/runtime extractors remain adapters because they depend on the target repository's languages and build system. They must emit the v3 provenance contract and are governed by the same staging/promotion rules.

## Test this package

```bash
python3 tests/test_install_and_boundary.py
python3 tests/test_goal_lifecycle.py
python3 tests/test_full_cycle.py
```


## Canonical execution sequence

```bash
# 1. Register the normalized user vibe-coding goal.
python3 .agentic/scripts/agenticctl.py --root . register-goal --goal-file /tmp/goal.json

# 2. Generate the constrained maker packet and implement in authorized project paths.
python3 .agentic/scripts/agenticctl.py --root . maker-packet --goal-id G001
python3 .agentic/scripts/agenticctl.py --root . record-attempt \
  --goal-id G001 --task-id T001 --result PASS --files-json '["src/example.py"]'

# 3. Independently verify all goal conditions and run the fast stop gate.
python3 .agentic/scripts/agenticctl.py --root . verifier-packet --goal-id G001
python3 .agentic/scripts/agenticctl.py --root . verify --goal-id G001
python3 .agentic/scripts/agenticctl.py --root . stop-gate --goal-id G001

# 4. Build the KG from the approved Git tree, validate, and promote it.
python3 .agentic/scripts/agenticctl.py --root . kg-build --goal-id G001
python3 .agentic/scripts/agenticctl.py --root . kg-promote --goal-id G001

# 5. Run the comprehensive gate and complete the bounded goal.
python3 .agentic/scripts/agenticctl.py --root . complete-goal \
  --goal-id G001 --outcome "Goal implemented and independently verified"

# 6. Only after every MUST requirement is verified, record user project acceptance.
python3 .agentic/scripts/agenticctl.py --root . accept-project
```

## Documentation map

- `SYSTEM-FILE-MAP.md` — precise system/project ownership boundary.
- `SYSTEM-ARCHITECTURE.md` — component and data flow.
- `DEPLOYMENT-GUIDE.md` — installation and coding-agent integration.
- `MIGRATION-v2.1-to-v3.0.md` — upgrade procedure.
- `system/protocol/LOOP-ENGINEERING-v3.0.md` — complete normative protocol.
- `VALIDATION-REPORT.md` — executed evidence and known boundaries.
