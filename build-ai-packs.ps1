param(
  [int]$MaxBytes = 150000
)

$Root = (Get-Location).Path
$OutDir = Join-Path $Root "AI_Packs"
$IncludeExt = @(
  ".py",".js",".ts",".tsx",".jsx",".json",".yml",".yaml",
  ".toml",".ini",".md",".html",".css",".scss",".env.example",
  ".txt",".sql",".ps1",".bat",".sh"
)
$SkipDirs = @("node_modules",".git","dist","build",".next",".vercel","coverage","venv",".venv","__pycache__",".turbo",".cache",".pytest_cache")

function Should-SkipDir($path) {
  foreach ($d in $SkipDirs) { if ($path -like "*\$d\*") { return $true } }
  return $false
}

# Prep output
Remove-Item $OutDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $OutDir | Out-Null

# Inventory
$inventory = @()
Get-ChildItem -Path $Root -Recurse -File | ForEach-Object {
  if (Should-SkipDir $_.FullName) { return }
  if ($IncludeExt -contains $_.Extension.ToLower()) {
    $lines = 0
    try { $lines = (Get-Content -Path $_.FullName -ErrorAction Stop).Count } catch {}
    $inventory += [PSCustomObject]@{
      Path  = $_.FullName.Substring($Root.Length+1)
      Bytes = $_.Length
      Lines = $lines
      Ext   = $_.Extension.ToLower()
    }
  }
}

$invPath = Join-Path $OutDir "RepoInventory.csv"
$inventory | Sort-Object Path | Export-Csv -Path $invPath -NoTypeInformation -Encoding UTF8

# Pack builder
$files = $inventory | Sort-Object Path
$packNum = 1
$bytesInPack = 0
$packFiles = @()
$packList = @()

function Flush-Pack {
  param($packNumRef, $packFilesRef, $OutDir, $Root)
  if ($packFilesRef.Count -eq 0) { return $null }
  $packName = "pack_$('{0:D3}' -f $packNumRef).txt"
  $packPath = Join-Path $OutDir $packName

  "# AI Review Pack $packNumRef`r`n" | Out-File -FilePath $packPath -Encoding UTF8
  "Note: Paths are relative to repo root.`r`n" | Out-File -FilePath $packPath -Append -Encoding UTF8

  foreach ($f in $packFilesRef) {
    "`r`n===== FILE: $($f.Path) =====`r`n" | Out-File -FilePath $packPath -Append -Encoding UTF8
    try {
      Get-Content -Path (Join-Path $Root $f.Path) -Raw -ErrorAction Stop | Out-File -FilePath $packPath -Append -Encoding UTF8
    } catch {
      "# [READ ERROR] $($f.Path) $_" | Out-File -FilePath $packPath -Append -Encoding UTF8
    }
  }
  return $packName
}

foreach ($f in $files) {
  if (($bytesInPack + $f.Bytes) -gt $MaxBytes -and $packFiles.Count -gt 0) {
    $pname = Flush-Pack -packNumRef $packNum -packFilesRef $packFiles -OutDir $OutDir -Root $Root
    if ($pname) { $packList += $pname }
    $packNum++
    $bytesInPack = 0
    $packFiles = @()
  }
  $packFiles += $f
  $bytesInPack += [int64]$f.Bytes
}

if ($packFiles.Count -gt 0) {
  $pname = Flush-Pack -packNumRef $packNum -packFilesRef $packFiles -OutDir $OutDir -Root $Root
  if ($pname) { $packList += $pname }
}

# Index
$indexPath = Join-Path $OutDir "PACK_INDEX.md"
@"
# AI Review Bundle

**How to use**
1) Read this file first.
2) I’ll provide numbered packs on request.
3) Review packs in order to avoid timeouts/freezes.

## Repo Summary
- Root: `$(Split-Path -Leaf $Root)`
- Inventory: `RepoInventory.csv` (path, bytes, lines, ext)
- Total files included: $($files.Count)
- Pack size target: $MaxBytes bytes

## Packs (in order)
$(($packList | ForEach-Object { "- $_" }) -join "`r`n")

## Suggested Review Order
1. Backend config & routers (e.g., `app/main.py`, `app/routes/*`)
2. Frontend entrypoints (`index.html`, `src/main.tsx`, `src/App.*`)
3. API clients/SDK calls (`src/lib/*`)
4. Auth & payments (`auth*`, `stripe*`, `paypal*`)
5. Transcribe/translate features
6. UI components & state management
7. Tests & scripts

## Key Manifests
- Python: `pyproject.toml` / `requirements.txt`
- Node: `package.json`, `vite.config.*`, `tsconfig.*`
- FastAPI: `app/main.py` (CORS/origins), server cmd/env
- Netlify: `netlify.toml` / `_redirects`
- Docker/CI: `Dockerfile`, `.github/workflows/*`
"@ | Out-File -FilePath $indexPath -Encoding UTF8

Write-Host "`nDone. Open '$OutDir\PACK_INDEX.md'." -ForegroundColor Green
