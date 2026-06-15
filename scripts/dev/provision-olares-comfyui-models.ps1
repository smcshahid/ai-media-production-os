<#
.SYNOPSIS
    Download the model weights required by the ComfyUI quality upgrade
    (upgraded SDXL stills + WAN 2.2 image-to-video) onto the Olares host that
    runs ComfyUI on the 24GB GPU.

.DESCRIPTION
    The compose `comfyui` service is SDXL-only and is the *dev* target. The real
    24GB GPU lives on the Olares host reached via the hybrid tunnel
    (COMFYUI_HOST=http://host.docker.internal:8190). WAN 2.2 weights must be
    placed in that host's ComfyUI `models/` tree.

    Run this ON THE OLARES HOST (or pass -ComfyUIRoot pointing at the mounted
    models directory). It is idempotent: existing files are skipped.

    Required ComfyUI version: recent enough to ship native WAN 2.2 nodes
    (UNETLoader 'wan' CLIP type, WanImageToVideo, CreateVideo/SaveVideo).

.PARAMETER ComfyUIRoot
    Path to the ComfyUI install root (the folder containing `models/`).

.PARAMETER IncludeLightningLora
    Also download the Wan2.2-Lightning 4-step LoRAs (faster, lower-step renders).

.EXAMPLE
    pwsh ./provision-olares-comfyui-models.ps1 -ComfyUIRoot /opt/comfyui
#>
[CmdletBinding()]
param(
    [string]$ComfyUIRoot = "/opt/comfyui",
    [switch]$IncludeLightningLora
)

$ErrorActionPreference = "Stop"

# repo = "<huggingface repo>"; path = "<file in repo>"; dest = "<models subdir>"
$models = @(
    # --- SDXL stills (base usually already present; refiner optional) ---
    @{ Name = "sdxl_base_1.0";           Repo = "stabilityai/stable-diffusion-xl-base-1.0";    Path = "sd_xl_base_1.0.safetensors";                                  Dest = "checkpoints";      File = "sdxl_base_1.0.safetensors" },

    # --- WAN 2.2 14B I2V (FP8-scaled fits 24GB; UMT5 offloads to system RAM) ---
    @{ Name = "wan22 i2v high noise";    Repo = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged";        Path = "split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"; Dest = "diffusion_models"; File = "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" },
    @{ Name = "wan22 i2v low noise";     Repo = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged";        Path = "split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors";  Dest = "diffusion_models"; File = "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" },
    @{ Name = "umt5 xxl fp8 (clip)";     Repo = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged";        Path = "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors";              Dest = "text_encoders";    File = "umt5_xxl_fp8_e4m3fn_scaled.safetensors" },
    @{ Name = "wan 2.1 vae";             Repo = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged";        Path = "split_files/vae/wan_2.1_vae.safetensors";                                       Dest = "vae";              File = "wan_2.1_vae.safetensors" }
)

if ($IncludeLightningLora) {
    $models += @(
        @{ Name = "wan22 lightning high"; Repo = "lightx2v/Wan2.2-Lightning"; Path = "Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors"; Dest = "loras"; File = "Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors" },
        @{ Name = "wan22 lightning low";  Repo = "lightx2v/Wan2.2-Lightning"; Path = "Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors";  Dest = "loras"; File = "Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors" }
    )
}

function Test-Tool($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

$hasHf = Test-Tool "huggingface-cli"
$hasWget = Test-Tool "wget"
if (-not $hasHf -and -not $hasWget) {
    throw "Need either 'huggingface-cli' (pip install -U 'huggingface_hub[cli]') or 'wget' on PATH."
}

foreach ($m in $models) {
    $destDir = Join-Path $ComfyUIRoot (Join-Path "models" $m.Dest)
    $destFile = Join-Path $destDir $m.File
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null

    if (Test-Path $destFile) {
        Write-Host "[skip] $($m.Name) already present -> $destFile"
        continue
    }

    Write-Host "[get ] $($m.Name) -> $destFile"
    if ($hasHf) {
        huggingface-cli download $m.Repo $m.Path --local-dir $destDir --local-dir-use-symlinks False
        $downloaded = Join-Path $destDir $m.Path
        if ((Test-Path $downloaded) -and ($downloaded -ne $destFile)) {
            Move-Item -Force $downloaded $destFile
        }
    }
    else {
        $url = "https://huggingface.co/$($m.Repo)/resolve/main/$($m.Path)?download=true"
        wget -O $destFile $url
    }
}

Write-Host ""
Write-Host "Done. Verify the files land under:"
Write-Host "  $ComfyUIRoot/models/checkpoints      (SDXL)"
Write-Host "  $ComfyUIRoot/models/diffusion_models (WAN high/low noise)"
Write-Host "  $ComfyUIRoot/models/text_encoders    (umt5)"
Write-Host "  $ComfyUIRoot/models/vae              (wan_2.1_vae)"
Write-Host ""
Write-Host "Then restart ComfyUI and set VIDEO_I2V_ENABLED=true in your .env."
