Implement Drama Asset Pipeline including Character Bible, Scene Bible, Shot Graph and Storyboard systems.

Requirements:
- Persist workflow state
- Support edit/regenerate
- Integrate QA and Retry
- Reuse Jellyfish systems

Automation Switch:
- `execution_mode=automatic`: build character bible, scene bible, shot graph and storyboard state, then advance to Image Runtime.
- `execution_mode=manual`: persist asset/storyboard output, then stop for user confirmation or correction.
