---
category: convention
subject: install-and-deploy
---

GNX is applied to data.win by install_foundation.csx run as a G3M DATA patch (UMT scripting). The AUTHORITATIVE copy is E:\GNX_Work_folder\GNX\install_foundation.csx — after any change, deploy it to the G3M profile path (...\G3M\profiles\Default\<profile>\install_foundation.csx). GNX_assets/ must sit alongside the .csx in the same G3M DATA patch entry (its candidateDirs discovery). PNG filenames in GNX_assets/ must NOT carry a spr_ prefix (the .csx adds it). G3M context quirks: `Project` is unavailable (CS0103), ScriptMessage dialogs are suppressed (reports go to %LOCALAPPDATA%\goblin_nest\gnx_patch_timing.txt), sprite phase needs `using ImageMagick;`.
