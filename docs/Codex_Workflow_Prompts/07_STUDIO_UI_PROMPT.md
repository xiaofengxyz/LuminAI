Transform Jellyfish frontend into CineForge Studio workflow UI.

Requirements:
- Persist workflow state
- Support edit/regenerate
- Integrate QA and Retry
- Reuse Jellyfish systems

Automation Switch:
- `execution_mode=automatic`: expose current state and task outcomes without requiring user edits, then advance when upstream stages are complete.
- `execution_mode=manual`: keep the operator surface in `waiting_operator` until the user approves, edits, or regenerates.
