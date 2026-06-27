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

function Get-SkillBase {
    param([string]$Plat)
    switch ($Plat) {
        "cursor"   { if ($Global) { Join-Path $env:USERPROFILE ".cursor\skills" } else { Join-Path $Target ".cursor\skills" } }
        "claude"   { if ($Global) { Join-Path $env:USERPROFILE ".claude\skills" } else { Join-Path $Target ".claude\skills" } }
        "codex"    { Join-Path $Target ".agents\skills" }
        "opencode" { Join-Path $Target ".opencode\skills" }
        "grok"     { Join-Path $Target ".factory\skills" }
    }
}

$Platforms = if ($Platform -eq "all") { @("cursor", "claude", "codex", "opencode", "grok") } else { @($Platform) }
$Skills = @("dream-eval-loop", "dream-tui")

foreach ($p in $Platforms) {
    foreach ($s in $Skills) {
        $src = Join-Path $BundleRoot (Join-Path $p (Join-Path "skills" $s))
        if (-not (Test-Path $src)) { continue }  # platform does not ship this skill
        $dst = Join-Path (Get-SkillBase $p) $s
        $tmp = "$dst.tmp.$PID"
        New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
        Copy-Item -Recurse -Force $src $tmp
        if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
        Rename-Item -Path $tmp -Destination $dst
        Write-Host "Installed $p/$s -> $dst"
    }
}

# Copy shared docs next to target for reference
$SharedDst = Join-Path $Target "docs\ops\dreaming\skills-bundle\shared"
$SharedTmp = "$SharedDst.tmp.$PID"
New-Item -ItemType Directory -Force -Path $SharedTmp | Out-Null
Copy-Item -Recurse -Force (Join-Path $BundleRoot "shared\*") $SharedTmp
if (Test-Path $SharedDst) { Remove-Item -Recurse -Force $SharedDst }
Rename-Item -Path $SharedTmp -Destination $SharedDst
Write-Host "Copied shared/ -> $SharedDst"

Write-Host "Done. Verify: node $PluginCli test --json"
