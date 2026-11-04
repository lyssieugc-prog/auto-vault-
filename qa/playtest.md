# Studio Playtest Procedure (via Roblox Studio MCP)

1. `rojo serve games/<slug>/default.project.json`, connect plugin (or confirm scripts synced).
2. Start Play (Server + 1 client; for multiplayer features Server + 2 clients).
3. Run scripted probes with `run_code` on the server, e.g.:
   ```lua
   local S = require(game.ServerScriptService.Game.Services)
   print(S.currency:get(game.Players:GetPlayers()[1].UserId, "Cash"))
   ```
4. Drive the loop: fire the same remotes the UI would, in order, and check state after each.
5. Capture Output; any error/warning = finding.
6. Stop, re-Play, verify persistence (DataStore needs API access in a private place, otherwise
   the template falls back to the in-memory adapter — note which one was used).
7. Write `games/<slug>/qa/playtest-<date>.md`: steps, expected, actual, pass/fail, screenshots.
