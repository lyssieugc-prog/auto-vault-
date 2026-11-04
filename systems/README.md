# Reusable Luau Systems

Layout in Roblox (`default.project.json`): `ReplicatedStorage.Vault.Shared`, `ReplicatedStorage.Vault.Client`,
`ServerScriptService.VaultServer`. Games vendor a pinned copy (`games/<slug>/vendor/vault`, see `vault.lock`).

**Shared modules are pure**: no Roblox APIs, dependencies injected (`now`, `rng`, `store`, other
system instances), so they're tested under Lune (`lune run systems/tests/run`). Mutating calls are
**server-only**; clients get snapshots.

| Module | Covers | Tests |
|---|---|---|
| `Shared/Currency` | wallets, spend/earn, stacked multipliers, passive income with fractional carry, change events | `specs/Currency` |
| `Shared/Rarity` | weighted rolls, luck, pity (“guaranteed in N”), mutations, odds strip data, weighted loot | `specs/Rarity` |
| `Shared/Inventory` | uid items, capacity, equip slots (+gamepass), trade locks, atomic transfer | `specs/Inventory` |
| `Shared/Plots` | base ownership + plot assignment | `specs/Plots` |
| `Shared/Stealing` | steal hold → grab → deliver, base lock with cooldown, shields, thief cooldown | `specs/Stealing` |
| `Shared/Tycoon` | purchase graph (requires, gamepass gates), income, progress, reset | `specs/Tycoon` |
| `Shared/Upgrades` | leveled curves + tier ladders (x2 → x1,250) | `specs/Upgrades` |
| `Shared/Rebirth` | cost curve, reset hooks, permanent multiplier, next-goal data | `specs/Rebirth` |
| `Shared/Trading` | request/accept, offers, anti-scam ready reset, confirm delay, re-validation, rollback | `specs/Trading` |
| `Shared/Rewards` | quests, 7-day daily streak, playtime rewards | `specs/Rewards` |
| `Shared/Tutorial` | onboarding step machine | `specs/Tutorial` |
| `Shared/Guard` | remote arg validation + token-bucket rate limiter | `specs/Guard` |
| `Shared/DataService` | profiles: template reconcile, migrations, session lock, retries, safe release | `specs/DataService` |
| `Shared/Monetization` | idempotent receipts, gamepass cache, 2x→100x repurchasable ladder | `specs/Monetization` |
| `Shared/Format` | 1.2K/3.4M abbreviations, commas, countdowns | `specs/Format` |
| `Server/DataStoreAdapter` | Roblox DataStore → DataService store interface (+ memory store) | Studio only |
| `Server/Net` | remotes folder, rate-limited + pcall-wrapped handlers | Studio only |
| `Server/MarketplaceAdapter` | ProcessReceipt → Monetization, save-before-grant | Studio only |
| `Client/UIAnim` | pop-open, stagger, hover/press, pulse, sunburst spin, countdown, number pops | Studio only |
| `Client/VFX` | camera shake, flash, particle bursts, bloom pulse, rarity reveal ladder, animation markers | Studio only |
| `Client/MobileUI` | touch detection, 44px targets, safe area, device scaling, tap binding | Studio only |

`specs/Integration` runs a full loop (load → earn → tycoon → hatch with pity → equip → rebirth →
save → reload) across several modules. The game template adds its own end-to-end tests
(`templates/game/tests/run.luau`).

“Studio only” modules are **built but not yet tested** until a Studio playtest exercises them
(`qa/playtest.md`). Update this table when that happens.

## Adding a system
1. Pure logic in `src/Shared/<Name>.luau` (`.new(config)`, injected deps, plain-table state).
2. `tests/specs/<Name>.luau` + register in `tests/run.luau`.
3. Thin Roblox glue in `src/Server` or `src/Client` only if needed.
4. Add a row here. `scripts/validate.sh` must pass.
