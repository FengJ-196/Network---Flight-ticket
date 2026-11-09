param([switch]$Offline)
$ErrorActionPreference = 'Stop'
$reportRoot = $PSScriptRoot
$portableCompiler = Join-Path $reportRoot '..\.build-tools\tectonic\tectonic.exe'
$systemCompiler = Get-Command tectonic -ErrorAction SilentlyContinue
if (Test-Path -LiteralPath $portableCompiler) {
    $compiler = (Resolve-Path -LiteralPath $portableCompiler).Path
} elseif ($systemCompiler) {
    $compiler = $systemCompiler.Source
} else {
    throw 'Tectonic is unavailable. Install Tectonic, or compile the .tex with a complete TeX distribution.'
}
$env:TECTONIC_CACHE_DIR = [System.IO.Path]::GetFullPath((Join-Path $reportRoot '..\.build-tools\latex-cache'))
New-Item -ItemType Directory -Path $env:TECTONIC_CACHE_DIR -Force | Out-Null
$fontConfigRoot = [System.IO.Path]::GetFullPath((Join-Path $reportRoot '..\.build-tools\fontconfig'))
$fontCacheRoot = Join-Path $fontConfigRoot 'cache'
New-Item -ItemType Directory -Path $fontCacheRoot -Force | Out-Null
$windowsFontRoot = [System.Security.SecurityElement]::Escape((Join-Path $env:WINDIR 'Fonts').Replace('\','/'))
$fontCacheXml = [System.Security.SecurityElement]::Escape($fontCacheRoot.Replace('\','/'))
$fontConfigXml = '<?xml version="1.0"?><fontconfig><dir>' + $windowsFontRoot + '</dir><cachedir>' + $fontCacheXml + '</cachedir></fontconfig>'
$env:FONTCONFIG_FILE = Join-Path $fontConfigRoot 'fonts.conf'
[System.IO.File]::WriteAllText($env:FONTCONFIG_FILE, $fontConfigXml, [System.Text.UTF8Encoding]::new($false))
$compileArgs = @('--keep-logs', '--untrusted')
if ($Offline) { $compileArgs += '--only-cached' }
$compileArgs += 'flight-ticket-design.tex'
Push-Location -LiteralPath $reportRoot
try {
    & $compiler @compileArgs
    if ($LASTEXITCODE -ne 0) { throw "LaTeX compilation failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
