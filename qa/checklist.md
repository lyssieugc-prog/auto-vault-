# Release Checklist (run every build; paste results into the game report)

## Gameplay & data
- [ ] New player: spawn → tutorial → first reward in < 60s
- [ ] Core loop completes (earn → buy → upgrade → unlock) without errors in Output
- [ ] Rejoin restores currency, inventory, upgrades, rebirths, tutorial state
- [ ] Two-client test: plots assigned uniquely; trading/stealing (if used) behave per spec
- [ ] All remotes validate args (try invalid/negative/NaN/huge values) and are rate limited
- [ ] Purchases: receipt handler idempotent (test with Studio test purchases only)

## House style (style/house-style.md §9)
- [ ] Kid-showing-best-friend test: list the 3 most show-off-able things and the weakest thing
- [ ] Nothing static: every window pops, buttons react, timers tick, icons idle
- [ ] No BAD-list model (few plain boxes, flat single colour, smooth/realistic)
- [ ] 2x→100x ladder, Season 1 pass, daily + playtime rewards, index, rebirth all present
- [ ] UI themed to THIS game (frame decor, open animation)
- [ ] All custom geometry came from Blender (no Studio-built custom models)
- [ ] Every major asset passed the professional-asset review (`style-guides/3D_STYLE_BIBLE.md` §13) and is ORIGINAL to this game

## Mobile & performance
- [ ] Phone emulator (iPhone SE + mid Android): HUD readable, all buttons ≥ 44px, no overlap
- [ ] Budgets in `performance-budget.md` met

## Safety
- [ ] Not published; no products created; no Robux spent (unless owner approved in chat)
- [ ] `scripts/check-secrets.sh` clean
