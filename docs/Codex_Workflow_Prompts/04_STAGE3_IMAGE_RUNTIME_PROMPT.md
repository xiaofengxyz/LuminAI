Implement Image Runtime pipeline using FLUX, SDXL, StoryDiffusion and ComfyUI adapters.

Requirements:
- Persist workflow state
- Support edit/regenerate
- Integrate QA and Retry
- Reuse Jellyfish systems

Automation Switch:
- `execution_mode=automatic`: dispatch image requests through the runtime adapter, run reference QA, then advance to Video Runtime.
- `execution_mode=manual`: persist image runtime outputs and QA notes, then stop for user selection/regeneration.
