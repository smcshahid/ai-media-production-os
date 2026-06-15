"""Cinematography agent constants (US-16)."""

AGENT_ID = "agent.cinematography"
PROMPT_VERSION = "v1"
STORYBOARD_BRANCH = "ai-draft"
WORKFLOW_NAME = "sdxl_storyboard_production_v1"
# D-45: exactly 4 frames per generation.
STORYBOARD_FRAME_COUNT = 4
BASE_SEED = 42

# Quality scaffold appended to every per-shot SDXL prompt so the diffusion model
# consistently produces sharp, cinematic stills regardless of the LLM wording.
QUALITY_SUFFIX = (
    "cinematic film still, sharp focus, professional color grading, "
    "volumetric lighting, highly detailed, depth of field, 35mm photograph"
)


def apply_quality_suffix(prompt: str) -> str:
    """Append the cinematic quality scaffold to a per-shot prompt."""
    base = (prompt or "").strip().rstrip(",")
    if not base:
        return QUALITY_SUFFIX
    return f"{base}, {QUALITY_SUFFIX}"
