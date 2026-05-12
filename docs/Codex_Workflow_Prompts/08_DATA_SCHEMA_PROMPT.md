Implement production-grade schemas for workflow assets, QA, runtime and retry systems.

Requirements:
- Persist workflow state
- Support edit/regenerate
- Integrate QA and Retry
- Reuse Jellyfish systems

Automation Switch:
- `execution_mode=automatic`: validate schema compatibility and persist migration-safe state, then advance to Final Integration.
- `execution_mode=manual`: persist schema validation output, then stop for user/operator review.
