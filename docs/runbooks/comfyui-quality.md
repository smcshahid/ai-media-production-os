# Runbook: ComfyUI Quality Upgrade (SDXL hi-res + WAN 2.2 i2v)

This runbook covers the visual quality upgrade: high-resolution 16:9 SDXL
storyboards and real WAN 2.2 image-to-video motion, both running on the Olares
host's 24GB GPU via the hybrid tunnel. The FFmpeg slideshow remains the always-on
fallback (now cinematic: Ken Burns + crossfades at 720p).

## What changed

| Area | Before | After |
|------|--------|-------|
| Storyboard resolution | 512x512 | 1344x768 (16:9) + 1.5x hi-res-fix pass |
| Sampler / steps | euler / normal, 15 steps | dpmpp_2m_sde / karras, 28 + 12 steps |
| Image params | hardcoded in JSON | tunable via `Settings` / `.env` |
| Video | 480p hard-cut slideshow | WAN 2.2 i2v motion (per-frame clips, crossfaded) |
| Slideshow fallback | static, 480p | Ken Burns + crossfades, 720p |

New workflow files:
- `configs/comfyui/workflows/sdxl_storyboard_v2.json` (default image workflow)
- `configs/comfyui/workflows/wan22_i2v.json` (WAN 2.2 14B I2V)

The legacy `sdxl_storyboard_production.json` is kept; switch back by setting
`COMFYUI_WORKFLOW=sdxl_storyboard_production.json`.

## Verified live on Olares (RTX 5090 Laptop, 24GB)

Both paths were validated against the shared Olares ComfyUI (v0.24.0, all native WAN
nodes present):

- SDXL v2 image: 1344x768 base + 1.5x hi-res-fix -> 2016x1152 PNG in ~28s.
- WAN 2.2 i2v: the I2V weights (~14.3GB x2) were downloaded into the pod's
  `/root/ComfyUI/models/diffusion_models/`; one 81-frame 832x480 clip rendered in
  ~12 min, peaking ~20GB VRAM (fits 24GB), output h264 mp4 5.06s @ 16fps with clear
  motion. Note: the box initially had only the WAN 2.2 *T2V* weights; i2v needs the
  *I2V* weights.

Render time caveat: ~12 min/clip x 4 clips is heavy on a laptop GPU. Cut it with
`VIDEO_I2V_STEPS` (lower), fewer `VIDEO_I2V_FRAMES`, the Lightning 4-step LoRA, or the
TI2V-5B model.

## VRAM budget (24GB)

- SDXL base + hi-res-fix at 1344x768 -> ~2016x1152: comfortable on 24GB.
- WAN 2.2 14B I2V FP8 (~24GB) + UMT5-XXL text encoder (~9GB): tight. The text
  encoder is offloaded to system RAM by ComfyUI's native offloading (needs
  >= 24GB system RAM). If you hit OOM:
  - Use the Wan2.2-Lightning 4-step LoRAs (`-IncludeLightningLora`) and set
    `VIDEO_I2V_STEPS=8` (or lower) to cut compute.
  - Or switch to the `Wan2.2-TI2V-5B` model (fits comfortably) by pointing
    `wan22_i2v.json` at the 5B checkpoint.
  - Or use GGUF Q5 quantized WAN weights.
- Ollama is unloaded before i2v (`unload_ollama_before_comfyui`, D-08) so the LLM
  and WAN never contend for VRAM.

## Provisioning models on the Olares host

The compose `comfyui` service is SDXL-only and is the dev target. The real GPU is
on Olares. Run on the Olares host (or against its mounted models dir):

```powershell
pwsh scripts/dev/provision-olares-comfyui-models.ps1 -ComfyUIRoot /opt/comfyui -IncludeLightningLora
```

This downloads (idempotently):
- `models/checkpoints/sdxl_base_1.0.safetensors`
- `models/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`
- `models/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`
- `models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- `models/vae/wan_2.1_vae.safetensors`
- (optional) `models/loras/Wan2.2-Lightning_I2V-A14B-4steps-lora_{HIGH,LOW}_fp16.safetensors`

ComfyUI must be recent enough to ship native WAN 2.2 nodes (`WanImageToVideo`,
`CreateVideo`, `SaveVideo`, and the `wan` CLIP type). Restart ComfyUI after
downloading.

## Enabling i2v

1. Provision models (above) and confirm ComfyUI loads them.
2. In `.env`: set `VIDEO_I2V_ENABLED=true`.
3. Start the hybrid stack (tunnels first):

```powershell
pwsh scripts/dev/start-olares-tunnels.ps1
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml -f deploy/compose/docker-compose.olares-hybrid.yml --env-file .env up -d
```

4. Run the pipeline through the VIDEO stage and confirm asset metadata shows
   `"source": "comfyui_i2v"`. If anything fails (model missing, OOM, timeout),
   the stage logs `video_i2v_failed` and falls back to the cinematic slideshow
   with `"source": "slideshow"` and `"fallback_reason"` populated.

## Validating a generated WAN workflow

`wan22_i2v.json` is authored in ComfyUI API (`/prompt`) format. If your ComfyUI
build's WAN nodes differ, export a known-good graph from the UI:

1. ComfyUI -> Workflow -> Browse Templates -> Video -> "Wan2.2 14B I2V".
2. Wire your start image, set 832x480 and length 81.
3. Save (API Format) and replace `configs/comfyui/workflows/wan22_i2v.json`,
   keeping the node class types the patcher expects: `LoadImage`,
   `WanImageToVideo`, `KSamplerAdvanced` (x2), `CreateVideo`.

## Tuning knobs (.env)

| Var | Default | Notes |
|-----|---------|-------|
| `COMFYUI_WORKFLOW` | `sdxl_storyboard_v2.json` | image workflow file |
| `COMFYUI_WIDTH` / `COMFYUI_HEIGHT` | 1344 / 768 | SDXL 16:9 base latent |
| `COMFYUI_STEPS` | 28 | base sampler steps |
| `COMFYUI_HIRES_STEPS` | 12 | hi-res-fix pass steps |
| `COMFYUI_CFG` | 7.0 | SDXL guidance |
| `COMFYUI_SAMPLER` / `COMFYUI_SCHEDULER` | dpmpp_2m_sde / karras | |
| `COMFYUI_GENERATE_TIMEOUT_S` | 180 | per-frame image timeout |
| `VIDEO_I2V_ENABLED` | false | master switch for WAN i2v |
| `VIDEO_I2V_WIDTH` / `VIDEO_I2V_HEIGHT` | 832 / 480 | WAN clip size |
| `VIDEO_I2V_FRAMES` / `VIDEO_I2V_FPS` | 81 / 16 | ~5s per storyboard frame |
| `VIDEO_I2V_STEPS` | 20 | total steps (split high/low noise) |
| `VIDEO_I2V_TIMEOUT_S` | 600 | per-clip i2v timeout |
