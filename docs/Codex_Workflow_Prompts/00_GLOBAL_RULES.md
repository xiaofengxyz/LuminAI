THIS PROJECT IS A FORK OF JELLYFISH.
DO NOT CREATE A NEW PROJECT.
Extend existing architecture only.

Requirements:
- Persist workflow state
- Support edit/regenerate
- Integrate QA and Retry
- Reuse Jellyfish systems

Automation Switch:
- Every workflow module must expose `execution_mode`: `automatic` or `manual`.
- `automatic` means persist output, run QA/retry policy, then auto-advance to the next module.
- `manual` means persist output, then stop with `waiting_operator` until the user edits, approves, or regenerates.
