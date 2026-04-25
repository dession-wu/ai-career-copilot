# gstack setup for Windows PowerShell
# Build browser binary + register all skills with Claude Code

$GSTACK_DIR = $PSScriptRoot
$SKILLS_DIR = Split-Path -Parent $GSTACK_DIR
$BROWSE_BIN = "$GSTACK_DIR\browse\dist\browse.exe"

Write-Host "Setting up gstack..."
Write-Host "GSTACK_DIR: $GSTACK_DIR"
Write-Host "SKILLS_DIR: $SKILLS_DIR"

# 1. Build browse binary if needed
$NEEDS_BUILD = $false
if (-not (Test-Path $BROWSE_BIN)) {
    $NEEDS_BUILD = $true
    Write-Host "Browse binary not found, need to build"
} else {
    # Check if sources are newer than binary
    $srcFiles = Get-ChildItem -Path "$GSTACK_DIR\browse\src" -Recurse -File -ErrorAction SilentlyContinue
    $binaryTime = (Get-Item $BROWSE_BIN).LastWriteTime
    foreach ($file in $srcFiles) {
        if ($file.LastWriteTime -gt $binaryTime) {
            $NEEDS_BUILD = $true
            Write-Host "Source file $($file.Name) is newer than binary"
            break
        }
    }
    
    # Check package.json
    if (-not $NEEDS_BUILD) {
        $pkgJson = "$GSTACK_DIR\package.json"
        if (Test-Path $pkgJson) {
            if ((Get-Item $pkgJson).LastWriteTime -gt $binaryTime) {
                $NEEDS_BUILD = $true
                Write-Host "package.json is newer than binary"
            }
        }
    }
}

if ($NEEDS_BUILD) {
    Write-Host "Building browse binary..."
    Set-Location $GSTACK_DIR
    
    Write-Host "Running bun install..."
    bun install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "bun install failed"
        exit 1
    }
    
    Write-Host "Running bun run build..."
    bun run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "bun run build failed"
        exit 1
    }
    
    # Write version file
    $versionFile = "$GSTACK_DIR\browse\dist\.version"
    git -C $GSTACK_DIR rev-parse HEAD 2>$null | Out-File -FilePath $versionFile -ErrorAction SilentlyContinue
}

if (-not (Test-Path $BROWSE_BIN)) {
    Write-Error "gstack setup failed: browse binary missing at $BROWSE_BIN"
    exit 1
}

# 2. Ensure Playwright's Chromium is available
Write-Host "Checking Playwright Chromium..."
try {
    $testScript = 'import { chromium } from "playwright"; const browser = await chromium.launch(); await browser.close();'
    bun --eval $testScript 2>$null
    Write-Host "Playwright Chromium is available"
} catch {
    Write-Host "Installing Playwright Chromium..."
    Set-Location $GSTACK_DIR
    bunx playwright install chromium
}

# 3. Ensure ~/.gstack global state directory exists
$GSTACK_HOME = "$env:USERPROFILE\.gstack"
$GSTACK_PROJECTS = "$GSTACK_HOME\projects"
if (-not (Test-Path $GSTACK_PROJECTS)) {
    New-Item -ItemType Directory -Path $GSTACK_PROJECTS -Force | Out-Null
    Write-Host "Created $GSTACK_PROJECTS"
}

# 4. Create skill symlinks if we're inside a .claude/skills directory
$SKILLS_BASENAME = Split-Path -Leaf $SKILLS_DIR
if ($SKILLS_BASENAME -eq "skills") {
    $linked = @()
    $skillDirs = Get-ChildItem -Path $GSTACK_DIR -Directory -ErrorAction SilentlyContinue
    
    foreach ($skillDir in $skillDirs) {
        $skillMd = "$($skillDir.FullName)\SKILL.md"
        if (Test-Path $skillMd) {
            $skillName = $skillDir.Name
            # Skip node_modules
            if ($skillName -eq "node_modules") { continue }
            
            $target = "$SKILLS_DIR\$skillName"
            $source = "gstack\$skillName"
            
            # Create junction/symlink
            if ((Test-Path $target) -and (Get-Item $target).PSIsContainer) {
                # Already exists as directory, skip
                Write-Host "Skill $skillName already exists at $target"
            } else {
                # Create symlink
                $targetParent = Split-Path -Parent $target
                if (-not (Test-Path $targetParent)) {
                    New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
                }
                
                # Remove existing symlink if any
                if (Test-Path $target) {
                    Remove-Item $target -Force -ErrorAction SilentlyContinue
                }
                
                # Create junction (directory symlink)
                $sourceFull = "$GSTACK_DIR\$skillName"
                cmd /c mklink /J "$target" "$sourceFull" 2>$null | Out-Null
                $linked += $skillName
                Write-Host "Linked skill: $skillName"
            }
        }
    }
    
    Write-Host "`ngstack ready."
    Write-Host "  browse: $BROWSE_BIN"
    if ($linked.Count -gt 0) {
        Write-Host "  linked skills: $($linked -join ' ')"
    }
} else {
    Write-Host "`ngstack ready."
    Write-Host "  browse: $BROWSE_BIN"
    Write-Host "  (skipped skill symlinks — not inside .claude/skills/)"
}

# 4. First-time welcome + legacy cleanup
if (-not (Test-Path $GSTACK_HOME)) {
    New-Item -ItemType Directory -Path $GSTACK_HOME -Force | Out-Null
    Write-Host "  Welcome! Run /gstack-upgrade anytime to stay current."
}

# Remove legacy temp file
$legacyFile = "C:\tmp\gstack-latest-version"
if (Test-Path $legacyFile) {
    Remove-Item $legacyFile -Force -ErrorAction SilentlyContinue
}

Write-Host "`nSetup complete!"
