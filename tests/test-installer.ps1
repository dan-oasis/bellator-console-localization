#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$script = Join-Path $root 'package/Install.ps1'
# Parse the installer independently of execution.
$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile($script, [ref]$tokens, [ref]$parseErrors) | Out-Null
if ($parseErrors.Count) { throw ($parseErrors | Out-String) }
$fixture = Join-Path ([System.IO.Path]::GetTempPath()) ('BellatorLocalizationTest-' + [Guid]::NewGuid().ToString('N'))
$package = Join-Path $fixture 'package'
$app = Join-Path $fixture 'application'
$relatives = @('斗战者控制台.dll','ApplyIcc/ApplyIcc.exe')
function Put([string]$Path, [string]$Content) {
    [System.IO.Directory]::CreateDirectory((Split-Path $Path -Parent)) | Out-Null
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.Encoding]::UTF8)
}
function Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Assert([bool]$Value, [string]$Message) { if (-not $Value) { throw $Message } }
function Invoke-Install([string]$Action, [string]$Language, [bool]$ShouldSucceed) {
    & powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File (Join-Path $package 'Install.ps1') -Action $Action -Language $Language -Folder $app
    Assert (($LASTEXITCODE -eq 0) -eq $ShouldSucceed) "Unexpected installer exit code: $LASTEXITCODE"
}
function Assert-Language([string]$Language) {
    foreach ($d in $definitions) {
        $actual = Hash (Join-Path $app $d.relative)
        Assert ($actual -eq $d[$Language]) ('Wrong target: ' + $d.relative)
    }
}
$lock = $null
try {
    [System.IO.Directory]::CreateDirectory($package) | Out-Null
    Copy-Item -LiteralPath $script -Destination (Join-Path $package 'Install.ps1')
    Put (Join-Path $app '斗战者控制台.exe') 'dummy main executable: NEVER LAUNCHED'
    $definitions = @()
    foreach ($relative in $relatives) {
        $target = Join-Path $app $relative
        Put $target ('original fixture: ' + $relative)
        $row = @{ relative = $relative; original = (Hash $target); previous = @() }
        foreach ($language in @('ru','en')) {
            $payload = Join-Path $package ('payload/' + $language + '/' + $relative)
            Put $payload ($language + ' fixture: ' + $relative)
            $row[$language] = Hash $payload
        }
        $definitions += $row
    }
    @{ files = $definitions } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $package 'manifest.json') -Encoding UTF8
    Invoke-Install 'Install' 'en' $true
    Assert-Language 'en'
    foreach ($d in $definitions) { Assert ((Hash ((Join-Path $app $d.relative) + '.before-russian')) -eq $d.original) 'Original backup not preserved' }
    Invoke-Install 'Install' 'ru' $true
    Assert-Language 'ru'
    Invoke-Install 'Install' 'ru' $true
    Assert-Language 'ru'
    Invoke-Install 'Restore' 'en' $true
    Assert-Language 'original'
    # Reject an unknown second file before the first target is replaced.
    $second = Join-Path $app $relatives[1]
    Put $second 'unknown fixture'
    $unknown = Hash $second
    Invoke-Install 'Install' 'en' $false
    Assert ((Hash (Join-Path $app $relatives[0])) -eq $definitions[0].original) 'Preflight changed first target'
    Assert ((Hash $second) -eq $unknown) 'Preflight changed unknown target'
    Copy-Item -LiteralPath ($second + '.before-russian') -Destination $second -Force
    # Corrupted selected-language payload must also abort before replacement.
    $payload = Join-Path $package ('payload/en/' + $relatives[1])
    $good = [System.IO.File]::ReadAllBytes($payload)
    Put $payload 'damaged payload'
    Invoke-Install 'Install' 'en' $false
    Assert-Language 'original'
    [System.IO.File]::WriteAllBytes($payload,$good)
    # Lock the second target against deletion/replacement. The first replacement
    # should be rolled back when replacing the second one fails.
    $lock = [System.IO.File]::Open($second,[System.IO.FileMode]::Open,[System.IO.FileAccess]::Read,[System.IO.FileShare]::Read)
    Invoke-Install 'Install' 'en' $false
    Assert-Language 'original'
    $lock.Dispose()
    $lock = $null
    # Existing historical original backups must survive all transitions.
    foreach ($d in $definitions) { Assert ((Hash ((Join-Path $app $d.relative) + '.before-russian')) -eq $d.original) 'Backup changed' }
    Write-Host 'Windows installer fixture tests passed.'
} finally {
    if ($lock) { $lock.Dispose() }
    Remove-Item -LiteralPath $fixture -Recurse -Force -ErrorAction SilentlyContinue
}

# The final negative case intentionally returns 1; do not propagate it to CI.
exit 0
