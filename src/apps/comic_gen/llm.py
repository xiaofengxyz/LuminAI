"""Default prompt templates for the comic generation pipeline.

Templates live outside runtime adapters so prompts can be compiled and
versioned without coupling the film core to a provider.
"""

DEFAULT_STORYBOARD_POLISH_PROMPT = (
    "Polish the storyboard into cinematic panels while preserving character, "
    "outfit, scene, and timeline continuity."
)
DEFAULT_VIDEO_POLISH_PROMPT = (
    "Convert the shot plan into a controllable video prompt with clear camera "
    "movement, pacing, lighting, and reference-image constraints."
)
DEFAULT_R2V_POLISH_PROMPT = (
    "Repair the reference-to-video prompt by keeping the existing composition, "
    "character identity, and continuity-critical visual details stable."
)

DEFAULT_PROMPTS = {
    "storyboard_polish": DEFAULT_STORYBOARD_POLISH_PROMPT,
    "video_polish": DEFAULT_VIDEO_POLISH_PROMPT,
    "r2v_polish": DEFAULT_R2V_POLISH_PROMPT,
}
