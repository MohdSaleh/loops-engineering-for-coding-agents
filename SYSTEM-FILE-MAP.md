# System Files vs User Project Files

## Discovery rule

`AGENTS.md` is the only required root-level system entrypoint. It directs the coding agent to `.agentic/config/workspace.json`, which is the machine authority for every path classification.

## Control plane

```text
AGENTS.md
.agentic/protocol/**
.agentic/config/**
.agentic/policy/**
.agentic/scripts/**
.agentic/schemas/**
```

These files govern execution and are not writable by an ordinary project maker.

## Runtime and generated system data

```text
.agentic/runtime/**
.agentic/knowledge/**
```

Only the orchestrator, validator, and KG builder may write these locations.

## User project

The user application remains in its native structure, for example:

```text
src/  app/  packages/  services/  tests/  e2e/  docs/  public/
package.json  pyproject.toml  go.mod  Cargo.toml  Dockerfile
```

The exact project roots and command working directories are declared in `workspace.json`. The system never assumes that all projects use `src/`, and it supports nested and multi-project workspaces through `projects[]`.

## Enforcement

The active goal contains `allowed_write_paths` and `denied_write_paths`. Before verification, the system compares the baseline and candidate Git trees and rejects:

- protected paths;
- denied paths;
- paths outside the goal scope;
- control/runtime/KG paths changed by a project goal;
- uncommitted user-project changes.
