# Deployment Guide

## Existing project

```bash
python3 -m pip install -r system/scripts/requirements.txt
python3 install.py /absolute/path/to/project
cd /absolute/path/to/project
git add AGENTS.md .agentic
# Review before committing.
git commit -m "chore: install Loop Engineering v3.0 control plane"
python3 .agentic/scripts/agenticctl.py --root . validate
```

## New project

```bash
mkdir my-project
python3 install.py my-project --init-git
```

Then define the product in `.agentic/policy/PROJECT-SPEC.md` and replace the placeholder requirement ledger. The first coding goal should use `PROJECT_CREATE` and authorize only the scaffold target paths.

## Required coding-agent integration

The agent must automatically read root `AGENTS.md`. For tools that use another entrypoint, copy or reference its contents from `CLAUDE.md`, `.github/copilot-instructions.md`, or the relevant IDE rule file without creating a second conflicting protocol.

## Operational storage

`.agentic/runtime/**` is ignored from Git by default because it is mutable execution state. Back it up through your CI artifact store or observability system when durable audit retention is required. Promoted KG releases may be stored locally, committed selectively, or uploaded to artifact storage; their manifests and hashes remain the integrity boundary.
