# Bellator Console 1.1.5 — Russian / English

Community localization for **Bellator Console 1.1.5** (`斗战者控制台`). Includes the main console and the **ApplyIcc color-calibration window**.

[**Download the RU / EN installer package**](dist/BellatorConsole_1.1.5_RU_EN.zip?raw=true) · [Русская инструкция](README.ru.md) · [SHA-256](dist/SHA256SUMS)

## Install or change language

1. Install the original manufacturer application first. This repository contains a localization patch, not the complete application or hardware drivers.
2. Download the ZIP above and **extract all files into a new folder**.
3. Exit Bellator Console, including its tray icon, and close ApplyIcc if it is open.
4. Right-click **Install.cmd → Run as administrator**.
5. Choose **Русский** or **English** in the language window.
6. Select the original application's main installation folder containing `斗战者控制台.exe`, then start it with its usual shortcut after installation completes.

To switch languages later, run **Install.cmd** again and select the other language. A prior Russian revision 1–5 can be upgraded if its original backups still exist.

To restore the manufacturer files, close both applications and run **Restore.cmd** as administrator. The language choice then controls installer messages; restoration always restores both original files.

PowerShell 5.1 or later on Windows is required. For unattended use with a known path:

```powershell
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File .\Install.ps1 -Action Install -Language en -Folder 'C:\Path\To\Bellator Console'
```

Use `-Language ru` for Russian or `-Action Restore` to restore the original files. The CMD launchers do not change the machine-wide PowerShell execution policy.

## Files and backups

Only these two files are replaced:

| Target | Purpose | Original backup |
| --- | --- | --- |
| `斗战者控制台.dll` | Main interface | `斗战者控制台.dll.before-russian` |
| `ApplyIcc/ApplyIcc.exe` | Color-calibration interface | `ApplyIcc/ApplyIcc.exe.before-russian` |

The historical `.before-russian` suffix is retained for compatibility, including English installations. **Keep these backups.** Their SHA-256 hashes are checked before a language change or restoration. Unknown builds are rejected before either target is changed. Both payloads and backups are prepared before replacement; if a later replacement fails, the script attempts to restore the exact state before that attempt.

The main EXE, drivers, services, ICC profiles and application settings are not part of this patch. Original manufacturer binaries and the original setup program are not redistributed here. Only translated application payloads are included. Manufacturer signatures cannot be retained on the modified payloads.

## Scope and verification

- Main dashboard, performance modes, graphics switches, keyboard settings, fan controls, confirmation dialogs, color picker, export labels and calibration messages.
- The main dashboard preserves the requested compact **Ghz**, **°C**, **CPU's**, **CPU/GPU**, and **system** labels. The CPU count remains dynamic and is centered inside the existing frame.
- English is built from the supplied Russian revision 5. The Russian payload is preserved byte-for-byte.
- English builds are structurally checked: PE bounds, .NET metadata, BAML records, deferred dictionary offsets, all `ldstr` references, and **472 method bodies**. Only string operands are allowed to differ inside method bodies.
- Exact OS window/control lookup strings used by ApplyIcc are preserved. This localization does not change the OEM calibration procedure or hardware support.
- Some technical OEM diagnostics and OS control names may remain in their original language. The unused original strings also remain embedded in metadata; this does not mean they are displayed.

**The new English UI and installer must still be checked on the target Windows laptop.** Static checks and installer fixture tests do not verify actual GPU switching, fan behavior or color calibration. Earlier Russian revisions were visually reviewed using user-provided screenshots; this is not an OEM release.

## Build and test

Python 3.10+ with no third-party packages:

```sh
python src/build_english.py
python src/package.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

The supplied Russian payload hashes are pinned by `src/build_english.py`. The English dictionary is in `locales/en.json`. Packaging produces a reproducible ZIP and SHA-256 lists.

On Windows, also run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\test-installer.ps1
```

That test uses temporary **dummy files** and does not modify or launch the installed Bellator application. It exercises EN installation, switching to RU, reinstallation, restoration, unknown-build rejection and rollback after a locked second file.

See [build-report.json](docs/build-report.json) for the binary verification counts.

## Ownership

This is an unofficial localization project. The underlying application and third-party components remain the property of their respective owners. No license or ownership of the manufacturer application is asserted by this repository.
