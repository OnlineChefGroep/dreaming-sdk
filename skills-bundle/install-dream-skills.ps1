# Install dream-eval-loop skills for multiple agent platforms.
# Usage: .\install-dream-skills.ps1 -Platform codex -Target C:\path\to\repo
#        .\install-dream-skills.ps1 -Platform all -Global

param(
    [ValidateSet("cursor", "claude", "codex", "opencode", "grok", "all")]
    [string]$Platform = "all",
    [string]$Target = (Get-Location).Path,
    [switch]$Global
)

$ErrorActionPreference = "Stop"
$BundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginCli = Join-Path $env:USERPROFILE ".cursor\plugins\local\dreaming\cli\dream.mjs"

if (-not (Test-Path $PluginCli)) {
    Write-Warning "Dreaming plugin not found at $PluginCli — install plugin before running eval."
}

$Map = @{
    cursor   = @{ Src = "cursor\skills\dream-eval-loop"; Dst = if ($Global) { Join-Path $env:USERPROFILE ".cursor\skills\dream-eval-loop" } else { Join-Path $Target ".cursor\skills\dream-eval-loop" } }
    claude   = @{ Src = "claude\skills\dream-eval-loop"; Dst = if ($Global) { Join-Path $env:USERPROFILE ".claude\skills\dream-eval-loop" } else { Join-Path $Target ".claude\skills\dream-eval-loop" } }
    codex    = @{ Src = "codex\skills\dream-eval-loop";  Dst = Join-Path $Target ".agents\skills\dream-eval-loop" }
    opencode = @{ Src = "opencode\skills\dream-eval-loop"; Dst = Join-Path $Target ".opencode\skills\dream-eval-loop" }
    grok     = @{ Src = "grok\skills\dream-eval-loop";   Dst = Join-Path $Target ".factory\skills\dream-eval-loop" }
}

$Platforms = if ($Platform -eq "all") { @("cursor", "claude", "codex", "opencode", "grok") } else { @($Platform) }

foreach ($p in $Platforms) {
    $entry = $Map[$p]
    $src = Join-Path $BundleRoot $entry.Src
    $dst = $entry.Dst
    if (-not (Test-Path $src)) {
        Write-Error "Bundle source missing: $src"
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
    Copy-Item -Recurse -Force $src $dst
    Write-Host "Installed $p -> $dst"
}

# Copy shared docs next to target for reference
$SharedDst = Join-Path $Target "docs\ops\dreaming\skills-bundle\shared"
if (-not (Test-Path $SharedDst)) {
    New-Item -ItemType Directory -Force -Path $SharedDst | Out-Null
    Copy-Item -Recurse -Force (Join-Path $BundleRoot "shared\*") $SharedDst
    Write-Host "Copied shared/ -> $SharedDst"
}

Write-Host "Done. Verify: node $PluginCli test --json"
