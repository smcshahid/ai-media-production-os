# Runbook: ComfyUI Quality Upgrade (multi-engine stills + WAN 2.2 i2v)

This runbook covers the visual quality upgrade: a swappable high-quality storyboard
image engine (Flux.1-dev / Z-Image Turbo / RealVisXL / SDXL) and real WAN 2.2
image-to-video motion, both running on the Olares host's 24GB GPU via the hybrid
tunnel. The FFmpeg slideshow remains the always-on fallback (now cinematic: Ken
Burns + crossfades at 720p).

## What changed

| Area | Before | After |
|------|--------|-------|
| Image engine | base SDXL 1.0 only | swappable: Flux.1-dev (default), Z-Image Turbo, RealVisXL, SDXL |
| Storyboard resolution | 512x512 | 1344x768 (16:9) |
| Image params | hardcoded in JSON | per-engine JSON defaults + optional `.env` overrides |
| Worker env | `COMFYUI_WORKFLOW` / `VIDEO_I2V_*` never reached the container | passed through in compose (GPU path defaults to Flux + i2v) |
| Video | 480p hard-cut slideshow | WAN 2.2 i2v motion (per-frame clips, crossfaded) |
| Slideshow fallback | static, 480p | Ken Burns + crossfades, 720p |

New workflow files (all follow the convention `"2"`=positive prompt, `"5"`=primary
KSampler, `"4"`=latent, so they are interchangeable via `COMFYUI_WORKFLOW`):
- `configs/comfyui/workflows/flux_storyboard.json` — **Flux.1-dev fp8** (GPU default; non-commercial license)
- `configs/comfyui/workflows/zimage_storyboard.json` — **Z-Image Turbo** (8-step, fast, permissive license)
- `configs/comfyui/workflows/sdxl_realvis_storyboard.json` — **RealVisXL V5** (commercial-friendly photoreal)
- `configs/comfyui/workflows/sdxl_storyboard_v2.json` — base SDXL hi-res-fix (local-container default)
- `configs/comfyui/workflows/wan22_i2v.json` — WAN 2.2 14B I2V

## Storyboard image engine (A/B-validated on Olares 24GB)

Same prompts run through all four engines at 1344x768. base SDXL 1.0 (the original
pipeline) was clearly the weakest — waxy skin, weak faces, generic "AI look". Ranked:

| Engine | Quality | Speed | License | When to use |
|--------|---------|-------|---------|-------------|
| Flux.1-dev | best cinematic | ~26–42s | **non-commercial** | default; personal / non-commercial renders |
| Z-Image Turbo | excellent | **~16–30s (8 steps)** | permissive | fast + cheap (best for RunPod bursts), commercial |
| RealVisXL V5 | good photoreal | ~30–52s | OpenRAIL++ (commercial) | safe SDXL drop-in, commercial work |
| base SDXL 1.0 | weak | ~33s | OpenRAIL++ | reference only / minimal local container |

Switch engines with one env var (no code change), e.g. for commercial output:
`COMFYUI_WORKFLOW=zimage_storyboard.json`. Each engine's JSON carries its own correct
sampler params; the `COMFYUI_STEPS/CFG/SAMPLER/SCHEDULER` envs are *optional overrides*
(leave unset to use the engine's values).

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
- `models/checkpoints/flux1-dev-fp8.safetensors` (Flux storyboard engine — default)
- `models/checkpoints/RealVisXL_V5.0_fp16.safetensors` (commercial-friendly fallback)
- `models/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`
- `models/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`
- `models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- `models/vae/wan_2.1_vae.safetensors`
- (optional `-IncludeLightningLora`) `models/loras/Wan2.2-Lightning_I2V-A14B-4steps-lora_{HIGH,LOW}_fp16.safetensors`
- (optional `-IncludeZImage`) Z-Image Turbo trio: `diffusion_models/z_image_turbo_bf16.safetensors`, `text_encoders/qwen_3_4b.safetensors`, `vae/ae.safetensors`

> The shared Olares ComfyUI already had the Z-Image trio present; `-IncludeZImage`
> is for fresh hosts.

ComfyUI must be recent enough to ship native WAN 2.2 nodes (`WanImageToVideo`,
`CreateVideo`, `SaveVideo`, and the `wan` CLIP type). Restart ComfyUI after
downloading.

## Enabling i2v

Enabled by default when using `make up-dev` (worker `VIDEO_I2V_ENABLED=true` in `docker-compose.dev.yml`).

1. Provision models on Olares (above) and confirm ComfyUI loads them.
2. `make up-dev` (starts tunnels + stack).
3. Run the pipeline through VIDEO and confirm asset metadata shows
   `"source": "comfyui_i2v"`. On failure, metadata includes `"fallback_reason"`.

Manual compose equivalent:

```powershell
pwsh scripts/dev/ensure-olares-ai-tunnels.ps1
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env up -d --build worker
```

## Troubleshooting: "my run still used SDXL / fell back to slideshow"

1. **Use `make up-dev`** — it starts Olares tunnels and rebuilds the worker. A plain
   `docker compose up` without the dev overlay still defaults to in-compose (missing) AI hosts.
2. **Worker env check** (see [local-development.md](./local-development.md)) — must show
   `host.docker.internal:8190` and `flux_storyboard.json`.
3. Inspect VIDEO asset `metadata.fallback_reason` for the exact i2v failure.

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
| `COMFYUI_WORKFLOW` | `flux_storyboard.json` (GPU/hybrid) · `sdxl_storyboard_v2.json` (local) | image engine file |
| `COMFYUI_WIDTH` / `COMFYUI_HEIGHT` | 1344 / 768 | 16:9 latent (all engines) |
| `COMFYUI_STEPS` | _(unset)_ | optional override; engine JSON wins when unset |
| `COMFYUI_HIRES_STEPS` | _(unset)_ | optional override (SDXL hi-res pass) |
| `COMFYUI_CFG` | _(unset)_ | optional override (SDXL ~7, Flux/Z ~1) |
| `COMFYUI_SAMPLER` / `COMFYUI_SCHEDULER` | _(unset)_ | optional overrides |
| `COMFYUI_GENERATE_TIMEOUT_S` | 180 | per-frame image timeout |
| `VIDEO_I2V_ENABLED` | false | master switch for WAN i2v |
| `VIDEO_I2V_WIDTH` / `VIDEO_I2V_HEIGHT` | 832 / 480 | WAN clip size |
| `VIDEO_I2V_FRAMES` / `VIDEO_I2V_FPS` | 81 / 16 | ~5s per storyboard frame |
| `VIDEO_I2V_STEPS` | 20 | total steps (split high/low noise) |
| `VIDEO_I2V_TIMEOUT_S` | 600 | per-clip i2v timeout |
