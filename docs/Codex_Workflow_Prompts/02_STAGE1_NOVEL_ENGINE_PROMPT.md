Implement Novel Engine with world bible, relationship graph, chapter outline, cliffhanger engine and editable workflow.

Requirements:
- Persist workflow state
- Support edit/regenerate
- Integrate QA and Retry
- Reuse Jellyfish systems

Automation Switch:
- `execution_mode=automatic`: generate or update the world bible, relationship graph, chapter outline and cliffhanger plan, then advance to Asset Pipeline.
- `execution_mode=manual`: persist Novel Engine output, then stop for user edit/approval.
