# System Architecture

```text
User vibe prompt
   ↓ preserve raw prompt
Goal normalizer → goal.json → schema + workspace gate
   ↓
Orchestrator → append-only events → deterministic projections
   ↓                       ↘
Maker packet                PROJECT-STATUS / requirement graph
   ↓
Project candidate tree → changed-path boundary gate
   ↓
Sanitized verifier packet → independent evidence
   ↓
Fast gate → KG staging → comprehensive validation → atomic promotion
   ↓
Goal completion → requirement verification → eventual user project acceptance
```

The control plane and project share Git for auditable anchors but have separate ownership. A project goal cannot alter the control plane. A system-maintenance goal cannot implicitly alter the product.
