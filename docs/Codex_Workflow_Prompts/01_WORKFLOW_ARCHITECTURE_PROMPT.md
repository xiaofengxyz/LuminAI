Implement workflow-first CineForge architecture integrated into Jellyfish.

Requirements:
- Persist workflow state
- Support edit/regenerate
- Integrate QA and Retry
- Reuse Jellyfish systems

Automation Switch:
- `execution_mode=automatic`: validate graph/state integrity, persist the ledger, then advance to Novel Engine.
- `execution_mode=manual`: persist architecture output, then stop for operator review before Novel Engine.
