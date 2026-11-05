# Bellator Console 1.1.5 — Russian / English

Russian and English localization for **Bellator Console 1.1.5** (`斗战者控制台`), including the **ApplyIcc** color-calibration utility.

[Download RU / EN](https://github.com/dan-oasis/bellator-console-localization/raw/refs/heads/main/dist/BellatorConsole_1.1.5_RU_EN.zip) · [Русская инструкция](README.ru.md) · [SHA-256](https://github.com/dan-oasis/bellator-console-localization/blob/main/dist/SHA256SUMS)

## Features

- Translated dashboard, settings, performance modes, fan controls, lighting, dialogs and export labels.
- Translated color-calibration interface and messages.
- Russian or English selection during installation.
- Language switching, original-file backups and restoration.
- SHA-256 verification of payloads, installed files and backups.

## Requirements

Windows, PowerShell 5.1 or later, administrator privileges and the original Bellator Console 1.1.5 installation. The package contains localization files only; it does not include the original application installer or hardware drivers. Unknown application builds are rejected.

## Installation

1. Extract the entire ZIP into a folder.
2. Exit Bellator Console, including its tray icon, and close ApplyIcc.
3. Right-click **Install.cmd → Run as administrator**.
4. Choose **Русский** or **English**.
5. Select the application folder containing `斗战者控制台.exe`.
6. Start Bellator Console using its normal shortcut.

Run **Install.cmd** again to select another language. Original backups are required for language switching.

## Restoration

Close both applications and run **Restore.cmd** as administrator. Both original files are restored. The language selection controls the installer messages.

| Target | Backup |
| --- | --- |
| `斗战者控制台.dll` | `斗战者控制台.dll.before-russian` |
| `ApplyIcc/ApplyIcc.exe` | `ApplyIcc/ApplyIcc.exe.before-russian` |

Keep the backups. The `.before-russian` suffix is used for both languages. Backups and both target files are verified before replacement. If a replacement fails, the installer attempts to restore the state before that installation attempt.

## Scope

The package replaces the two files listed above. The main EXE, drivers, services, ICC profiles and application settings are not replaced. Manufacturer signatures are not retained on localized files. Some technical diagnostics and OS control names remain in their original language.

Automated checks cover binary structure, string references, **472 method bodies**, installation, language switching and restoration. Checks run on Windows and Linux. These tests do not validate GPU switching, fan behavior, color-calibration results or display layout on specific laptop models.

## Build and test

Python 3.10+; no third-party Python packages are required. Run from the repository root:

```sh
python src/build_english.py
python src/package.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

Windows installer tests:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\test-installer.ps1
```

The installer tests use temporary dummy files and do not launch the application. The translation dictionary is `locales/en.json`; binary verification results are in `docs/build-report.json`.

Command-line installation:

```powershell
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File .\Install.ps1 -Action Install -Language en -Folder 'C:\Path\To\Bellator Console'
```

Use `-Language ru` for Russian or `-Action Restore` to restore the original files. The CMD launchers do not change the machine-wide PowerShell execution policy.

## Ownership

Unofficial localization. The underlying application and third-party components belong to their respective owners.
