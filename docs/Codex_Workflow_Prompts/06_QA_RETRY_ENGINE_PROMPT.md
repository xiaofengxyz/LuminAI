Implement QA and Retry Engine for all workflow stages.

Requirements:
- Persist workflow state
- Support edit/regenerate
- Integrate QA and Retry
- Reuse Jellyfish systems

Automation Switch:
- `execution_mode=automatic`: score continuity/identity/motion, queue targeted retries, then advance to Studio UI/final packaging gates.
- `execution_mode=manual`: persist QA findings and retry candidates, then stop for user decision.
