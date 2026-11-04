# Games

One folder per game: `games/<slug>/`, developed on branch `game/<slug>`.
Create with `scripts/new-game.sh "Game Name" --branch` (the `/make-game` skill does this).
Each game is self-contained (vendored vault systems pinned in `vault.lock`) so later vault
changes never break an existing game. Start any session on a game by reading its `STATUS.md`.
