Implement Video Runtime Engine for Seedance, Kling, Veo and Wan2.1, Sora and so on.

Requirements:
- Persist workflow state
- Support edit/regenerate
- Integrate QA and Retry
- Reuse Jellyfish systems

Automation Switch:
- `execution_mode=automatic`: dispatch video requests through the runtime adapter, persist task links, then advance to QA/Retry Engine.
- `execution_mode=manual`: persist video task outputs, then stop for user review before QA/retry.
