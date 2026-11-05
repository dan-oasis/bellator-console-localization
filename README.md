# Bellator Console 1.1.5 — RU / EN

Unofficial Russian and English localization for Bellator Console 1.1.5 and the ApplyIcc color-calibration utility.

[Download package](https://github.com/dan-oasis/bellator-console-localization/raw/refs/heads/main/dist/BellatorConsole_1.1.5_RU_EN.zip) · [Русский](README.ru.md) · [SHA-256](https://github.com/dan-oasis/bellator-console-localization/blob/main/dist/SHA256SUMS)

## Features

- Translated dashboard, settings, performance modes, fan controls, lighting, dialogs and export labels.
- Translated color-calibration interface and messages.
- Russian or English selection during installation.
- Language switching, original-file backups and restoration.
- SHA-256 verification of application files and backups.

## Installation

Requires an installed Bellator Console 1.1.5, Windows, PowerShell 5.1 or later and administrator privileges.

1. Extract the ZIP and close Bellator Console, its tray icon and ApplyIcc.
2. Right-click **Install.cmd → Run as administrator**.
3. Choose **Русский** or **English**.
4. Select the folder containing `斗战者控制台.exe`.

Run **Install.cmd** again to switch languages. Run **Restore.cmd** with both applications closed to restore the original files.

Original backups are stored beside their files with the `.before-russian` suffix. Keep them: language switching and restoration require these backups. Unknown application builds are not supported.

## Package contents

The localization replaces `斗战者控制台.dll` and `ApplyIcc/ApplyIcc.exe`. The original application installer and hardware drivers are not included. Manufacturer signatures are not retained on localized files. Some technical messages remain in their original language.

Build and installer checks run on Windows and Linux. They do not validate hardware functions or interface layout on specific laptop models.

Dictionary: `locales/en.json`. Build scripts: `src/`. Tests: `tests/`. Report: `docs/build-report.json`.

The application and third-party components belong to their respective owners.
