---
category: convention
subject: git-hygiene
---

.gitattributes enforces LF line endings (eol=lf) — UMT exports LF, do not change. Baseline tags: v<version>-vanilla marks a clean UMT export (e.g. old v1.32-vanilla). Re-baseline workflow when a new vanilla export lands: rm -rf .git; git init; add+commit "vanilla <v>"; tag; then overwrite with mod files and commit "mod: initial state". Commit/push only when the user asks.
