"""US-18 video stage constants (D-48)."""

AGENT_ID = "agent.video_generator"
VIDEO_BRANCH = "ai-draft"
LOGICAL_FILENAME = "scene_video.mp4"
STORYBOARD_FRAME_COUNT = 4
MIN_DURATION_SEC = 15.0
MAX_DURATION_SEC = 30.0
DEFAULT_DURATION_SEC = 20.0
DEFAULT_FPS = 24
# Quality upgrade: allow up to 720p so WAN i2v (832x480) and the cinematic
# slideshow (1280x720) outputs are not rejected/downscaled (supersedes 480p cap).
MAX_WIDTH = 1280
MAX_HEIGHT = 720
SOURCE_SLIDESHOW = "slideshow"
SOURCE_COMFYUI_I2V = "comfyui_i2v"
