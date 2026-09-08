---
category: convention
subject: git-hygiene
---

No `.gitattributes` in this repo (the old CLAUDE.md claim of LF enforcement was stale from the `Code/` era). `core.autocrlf=true` globally. Tracked `GNX/diffs/*.patch` are UTF-16 LE with CRLF (as UMT/G3M exports them) — leave them. Graphene `.md` files trigger CRLF warnings on commit; harmless, they store fine. Baseline tags: `v<version>-vanilla` for a clean UMT export. Commit/push only when the user asks. Prefer a new commit over amending.
