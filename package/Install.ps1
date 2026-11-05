#Requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet('Install','Restore')][string]$Action = 'Install',
    [ValidateSet('ru','en')][string]$Language,
    [string]$Folder
)
$ErrorActionPreference = 'Stop'
function T([string]$Russian, [string]$English) {
    if ($Language -eq 'ru') { return $Russian }
    return $English
}
function Hash([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
$plans = @()
$applied = @()
$completed = $false
try {
    Add-Type -AssemblyName System.Windows.Forms
    if (-not $Language) {
        $form = New-Object System.Windows.Forms.Form
        $form.Text = 'Bellator Console - Language'
        $form.ClientSize = New-Object System.Drawing.Size(340,125)
        $form.StartPosition = 'CenterScreen'
        $form.FormBorderStyle = 'FixedDialog'
        $form.MaximizeBox = $false
        $form.MinimizeBox = $false
        $label = New-Object System.Windows.Forms.Label
        $label.Text = 'Выберите язык / Choose a language'
        $label.AutoSize = $true
        $label.Location = New-Object System.Drawing.Point(26,22)
        $form.Controls.Add($label)
        $ru = New-Object System.Windows.Forms.Button
        $ru.Text = 'Русский'
        $ru.Size = New-Object System.Drawing.Size(130,35)
        $ru.Location = New-Object System.Drawing.Point(26,65)
        $ru.Add_Click({ $form.Tag = 'ru'; $form.DialogResult = [System.Windows.Forms.DialogResult]::OK })
        $form.Controls.Add($ru)
        $en = New-Object System.Windows.Forms.Button
        $en.Text = 'English'
        $en.Size = New-Object System.Drawing.Size(130,35)
        $en.Location = New-Object System.Drawing.Point(184,65)
        $en.Add_Click({ $form.Tag = 'en'; $form.DialogResult = [System.Windows.Forms.DialogResult]::OK })
        $form.Controls.Add($en)
        $answer = $form.ShowDialog()
        $chosen = [string]$form.Tag
        $form.Dispose()
        if ($answer -ne [System.Windows.Forms.DialogResult]::OK) { exit 0 }
        $Language = $chosen
    }
    if (-not $Folder) {
        $picker = New-Object System.Windows.Forms.FolderBrowserDialog
        $picker.Description = T 'Выберите основную папку установленной Bellator Console' 'Select the main folder of the installed Bellator Console'
        $picker.ShowNewFolderButton = $false
        if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
            $picker.Dispose()
            exit 0
        }
        $Folder = $picker.SelectedPath
        $picker.Dispose()
    }
    $Folder = (Resolve-Path -LiteralPath $Folder).ProviderPath
    if (-not (Test-Path -LiteralPath (Join-Path $Folder '斗战者控制台.exe') -PathType Leaf)) {
        throw (T 'Выберите папку с 斗战者控制台.exe, а не папку ApplyIcc.' 'Select the folder containing 斗战者控制台.exe, not the ApplyIcc subfolder.')
    }
    foreach ($processName in @('斗战者控制台','ApplyIcc')) {
        if (@(Get-Process -Name $processName -ErrorAction SilentlyContinue).Count -gt 0) {
            throw (T 'Закройте Bellator Console (включая значок в трее) и окно калибровки.' 'Close Bellator Console (including its tray icon) and the calibration window.')
        }
    }
    $manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($d in $manifest.files) {
        # These are the only two allowed targets, regardless of manifest contents.
        if ($d.relative -notin @('斗战者控制台.dll','ApplyIcc/ApplyIcc.exe')) { throw 'Invalid manifest target.' }
        $relative = $d.relative.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
        $target = Join-Path $Folder $relative
        # Preserve compatibility with backups created by earlier RU installers.
        $backup = $target + '.before-russian'
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            throw ((T 'Файл не найден: ' 'File not found: ') + $relative)
        }
        $current = Hash $target
        $accepted = @($d.original, $d.ru, $d.en) + @($d.previous)
        if ($current -notin $accepted) {
            throw ((T 'Неизвестная сборка; файлы не изменены: ' 'Unknown build; files were not changed: ') + $relative)
        }
        if ($Action -eq 'Install') {
            $payload = Join-Path $PSScriptRoot ('payload/' + $Language + '/' + $relative)
            $expected = [string]$d.$Language
            if (-not (Test-Path -LiteralPath $payload -PathType Leaf) -or (Hash $payload) -ne $expected) {
                throw ((T 'Повреждён или отсутствует файл перевода: ' 'Missing or damaged language payload: ') + $relative)
            }
            if ($current -eq $expected) { continue }
            if (Test-Path -LiteralPath $backup) {
                if ((Hash $backup) -ne $d.original) {
                    throw ((T 'Резервная копия не совпадает с оригиналом: ' 'Backup does not match the original: ') + $relative)
                }
            } elseif ($current -ne $d.original) {
                throw ((T 'Для смены языка нужна оригинальная копия .before-russian: ' 'Switching languages requires the original .before-russian backup: ') + $relative)
            }
            $source = $payload
        } else {
            if ($current -eq $d.original) { continue }
            $source = $backup
            $expected = [string]$d.original
            if (-not (Test-Path -LiteralPath $backup -PathType Leaf) -or (Hash $backup) -ne $expected) {
                throw ((T 'Проверенная резервная копия не найдена: ' 'Verified original backup not found: ') + $relative)
            }
        }
        $plans += [pscustomobject]@{
            Source = $source; Target = $target; Backup = $backup;
            Expected = $expected; Original = $d.original; Temp = $null; Swap = $null
        }
    }
    if ($plans.Count -eq 0) {
        Write-Host (T 'Выбранная версия уже установлена.' 'The selected version is already installed.')
        exit 0
    }
    # Preflight of both targets finishes before backup or replacement starts.
    foreach ($job in $plans) {
        if ($Action -eq 'Install' -and -not (Test-Path -LiteralPath $job.Backup)) {
            [System.IO.File]::Copy($job.Target, $job.Backup, $false)
            if ((Hash $job.Backup) -ne $job.Original) { throw (T 'Ошибка проверки резервной копии.' 'Backup verification failed.') }
        }
        $job.Temp = $job.Target + '.localization-' + [Guid]::NewGuid().ToString('N') + '.tmp'
        $job.Swap = $job.Target + '.localization-swap-' + [Guid]::NewGuid().ToString('N') + '.bak'
        [System.IO.File]::Copy($job.Source, $job.Temp, $false)
        if ((Hash $job.Temp) -ne $job.Expected) { throw (T 'Ошибка проверки временной копии.' 'Temporary file verification failed.') }
    }
    foreach ($job in $plans) {
        [System.IO.File]::Replace($job.Temp, $job.Target, $job.Swap)
        $applied += $job
        if ((Hash $job.Target) -ne $job.Expected) { throw (T 'Ошибка проверки установленного файла.' 'Installed file verification failed.') }
    }
    $completed = $true
    if ($Action -eq 'Install') {
        Write-Host (T 'Русский язык установлен. Запустите программу обычным ярлыком.' 'English installed. Start the application using its normal shortcut.')
        Write-Host (T 'Для смены языка снова запустите Install.cmd. Для отката — Restore.cmd.' 'Run Install.cmd again to switch languages. Use Restore.cmd to restore the originals.')
    } else {
        Write-Host (T 'Оригинальные файлы восстановлены.' 'Original files restored.')
    }
} catch {
    Write-Host ((T 'Ошибка: ' 'Error: ') + $_.Exception.Message) -ForegroundColor Red
    for ($i = $applied.Count - 1; $i -ge 0; $i--) {
        $job = $applied[$i]
        try {
            $discard = $job.Target + '.localization-recovery-' + [Guid]::NewGuid().ToString('N') + '.bak'
            [System.IO.File]::Replace($job.Swap, $job.Target, $discard)
            Remove-Item -LiteralPath $discard -Force -ErrorAction SilentlyContinue
            Write-Host ((T 'Возвращено предыдущее состояние: ' 'Previous state restored: ') + $job.Target)
        } catch {
            Write-Host ((T 'Автооткат не удался. Копия предыдущего состояния: ' 'Automatic rollback failed. Previous-state copy: ') + $job.Swap) -ForegroundColor Red
        }
    }
    exit 1
} finally {
    foreach ($job in $plans) {
        if ($job.Temp -and (Test-Path -LiteralPath $job.Temp)) {
            Remove-Item -LiteralPath $job.Temp -Force -ErrorAction SilentlyContinue
        }
        if ($completed -and $job.Swap -and (Test-Path -LiteralPath $job.Swap)) {
            Remove-Item -LiteralPath $job.Swap -Force -ErrorAction SilentlyContinue
        }
    }
}
