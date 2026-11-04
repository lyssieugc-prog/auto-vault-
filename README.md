# Roblox AI Game Studio — Vault

A GitHub-backed vault that lets Claude Code build Roblox games from one prompt, in the owner's
house style, with reusable tested systems.

```
/make-game "Lava Pets" "hatch lava pets, steal eggs from other players' volcano bases"
```

| Start here | |
|---|---|
| `CLAUDE.md` | instructions Claude reads every session |
| `docs/integrations/STATUS.md` | what is connected right now + manual setup left |
| `docs/integrations/local-setup.md` | set up Blender / Studio / Figma on your computer |
| `.claude/skills/make-game` | the one-prompt game generator |
| `.claude/skills/vault-learn` | how corrections become permanent |
| `systems/README.md` | reusable Luau systems + test coverage |
| `docs/git-workflow.md` | branches, commits, recovery |

Validate everything: `scripts/validate.sh` (CI runs it on every push).

Safety: nothing is published to Roblox, no products are created and no Robux is spent without
the owner's explicit approval. No secrets in git (`scripts/check-secrets.sh`, pre-commit hook).
