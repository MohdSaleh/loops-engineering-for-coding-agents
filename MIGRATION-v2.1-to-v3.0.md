# Migration from v2.1 to v3.0

v3.0 changes the repository layout from root-level Loop/KG files to an isolated `.agentic/` control plane.

## Procedure

1. Commit or back up the repository.
2. Preserve v2.1 artifacts under `.agentic/migrations/v2.1-backup/`:
   - `LOOP-ENGINEERING-v2.1.md`
   - `LOOP-EVENTS.jsonl`
   - `LOOP-STATE.json`
   - `LOOP-VERSIONS.json`
   - `knowledge/`, `schemas/`, and Loop scripts.
3. Run the v3 installer.
4. Move the active product goal and constraints into `.agentic/policy/VISION.md`.
5. Convert the complete product destination into `PROJECT-SPEC.md` and `REQUIREMENTS.json`.
6. Review generated `.agentic/config/workspace.json`; declare every project root and validation working directory.
7. Do not append v2.1 events directly to the v3.0 log. Preserve them as historical evidence. Start a new v3 event chain and record the previous final Git SHA/KG version in a migration note.
8. Run all v3 tests and the comprehensive validator before allowing autonomous project changes.

## Breaking changes

- Project and system files are explicitly separated.
- Runtime files move under `.agentic/runtime/`.
- KG artifacts move under `.agentic/knowledge/`.
- Goal contracts require project ID and path authorization.
- Project completion is distinct from goal completion.
- Ordinary project goals cannot write the Loop/KG control plane.
