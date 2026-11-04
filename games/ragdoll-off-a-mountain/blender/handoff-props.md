# Model Handoff — Props (Launch Cannons ×5 + Bone Zone hub props ×7)

Game: `ragdoll-off-a-mountain` · Profile: `simulator` (+ brainrot tags) · Rarity: cannon tiers 1–5 (rarer = more glow)
Template: `prop_kit` (SOLID language) · Scripts: `blender/cannons.py`, `blender/hub_props.py`
Status: PENDING owner approval (nothing here is approved until the owner says so).

## Style rules that apply (house-style §0/§3/§4, bible ★ §0 §3 §3b §13, simulator profile)
- SOLID language: few big chunky readable masses + many small chunky trim/detail parts; texture studs
  (0.5-stud, world-space) on ALL sides except glass / neon / Screen faces. Never stud geometry.
- ≥ 2 shades per material (`vault_kit.shades`), 1 main hue + 1 secondary + 1 accent + neutrals.
- Physical geometry for trims, rivets, hoops, signs, icons. ≥ 3 depth layers on any face > 6×6.
- Glow accents ≤ ~10 % visible area; rarer cannon = more glow (Popper: 2 bulbs → Meteor: coils + core).
- Detail must make sense: cardboard tube gets confetti/paper/string (no rivets); barrel gets staves +
  iron hoops + wheels; rocket gets fins/tanks/hazard; mortar gets gears/gauges/bolts; rail gun gets coils/vents/crystal.
- NEVER: few plain boxes, single flat colour, smooth realistic, generic AI look, scary skeleton.
- Originality: designed for THIS game (cliff-launch + bones theme); nothing copied from the test collection.

## Shared conventions
- 1 unit = 1 stud, Z up, FRONT faces +Y, pivot bottom-centre (0,0,0).
- Cannons: base footprint fits the **8-stud mount ring** (`CannonMountN`), barrel axis tilted **25°** up
  toward +Y, barrel **inner opening ≥ 4.0 studs** diameter (5-stud R6 climbs in feet-first).
  Each tier larger: overall height ≈ 7.5 / 9 / 11 / 12 / 14 studs.
- Attachments (empties, exported with the FBX): `Muzzle` (barrel mouth centre, launch point),
  `Seat` (inside the barrel where the player sits), `Pivot` (barrel tilt pivot).
- Export meshes per model ≤ 3: `<Name>_Body`, `<Name>_Neon`, and one special: `Screen` (boards) /
  `Accent` (egg stand, material named `Accent`) / `<Name>_Glass`.

## Palette (game theme + per-asset accents)
| Role | Hex |
|---|---|
| Stone | `#8E96A3` / `#6E7683` |
| Bone cream (game accent) | `#FFF1CF` |
| SNAP orange (glow) | `#FF8A1F` |
| Cash gold | `#FFD93B` |
| Party Popper | kraft `#D99A55`, confetti pink `#FF5FA2`, teal `#22C3A6`, yellow `#FFD93B`, purple `#B678EA` |
| Barrel Blaster | oak `#B5733A`/`#8A5530`, iron `#4A5260`, rope `#D9B77A`, fuse glow `#FF8A1F` |
| Rocket Rig | hull white `#F2F5FA`, red `#E13A2A`, hazard `#FFC21A`+`#1A1A1A`, steel `#5B6B82`, thruster neon `#3EF0FF` |
| Mega Mortar | gunmetal `#5B6B82`/`#3B4554`, brass `#E0A93A`, stone `#8E96A3`, gauge glow `#A8F03C` |
| Meteor Launcher | navy armour `#2A2F5A`, white `#E8ECFF`, purple `#B678EA`, neon cyan `#3EF0FF`, crystal `#C45BFF` |
| Hub: shop wood `#C98A4B`, awning SNAP orange/cream, sign navy `#1E1B33`, egg-stand Accent default `#4CC24A` |

## Part lists (pieces before join, approximate)
| Asset | Main masses | Detail layers | Glow | Silhouette feature |
|---|---|---|---|---|
| Cannon1 PartyPopper | gift-box base + ribbon cradle, flared cardboard cone tube | 5 confetti stripe bands, confetti chips, gold mouth rim, paper fringe + curly streamers, pull-string + ring tab, bow | 2 bulbs + streamer tips | flared cone + streamers bursting out |
| Cannon2 BarrelBlaster | 4-wheel cart, bulging stave barrel | 16 staves in 3 shades, 4 iron hoops + rivets, spoked wheels, axle caps, trail handle, fuse coil | fuse spark | barrel on big wheels + fuse |
| Cannon3 RocketRig | tripod + turntable, rocket launch tube | 4 fins, 2 fuel tanks + straps + pipes, hazard band, nose collar, control box, rivets, warning lights | thruster ring, 2 beacons | finned tube on 3 splayed legs |
| Cannon4 MegaMortar | stone+steel turntable, stubby fat barrel | 3 gears with teeth, 2 pressure gauges, pipes + valve wheel, bolt rings, trunnions, stone base blocks, cannonball rack | gauge needles, base lights | huge squat muzzle |
| Cannon5 MeteorLauncher | hover pedestal, rail barrel | 2 rails, 6 neon coils, cooling vent fins, crystal core in cradle, armour plates, cables | coils, core, base ring, muzzle ring | long double-rail + glowing crystal |
| RebirthStatue | stepped studded plinth, skeleton (~19 tall) | ribs, spine, pelvis, bone limbs with knob ends, big skull w/ grin + teeth, bandage, gold medal, trophy w/ gem, plaque, rebirth arrows icon | rebirth ring, trophy gem | arm raised with trophy |
| EggStand | studded platform, display pedestal + ring, two posts + roof sign | egg icon on sign, awning, rope posts, steps, lamps | ring glow, lamps | arched sign + ring |
| CannonShop | wooden booth, counter, slanted roof | striped awning + scallops, sign w/ cannon icon, rooftop cannon, cannonball pyramid, crates, poster | sign bulbs | rooftop cannon |
| UpgradeStand | rounded kiosk, counter, tower sign | bone+arrow icon, shelves w/ bottles + bones, awning, gear deco | arrow glow | tall arrow sign |
| SeasonBoard | 2 posts, framed board | snow cap drips, snowflake crest, lamps, rope + carabiner, kick plates | crest + lamps | snowy crest on wide board |
| Leaderboard | 1-2-3 podium + framed board | gold/silver/bronze steps, number plates, trophy topper, bone crest | trophy gem, rim lights | podium + trophy |
| DailyChest | chest body + curved lid | planks, gold corner caps + bands, bone lock, rivets, feet, gems | lid seam glow | domed lid + bone lock |

## Silhouette check
Cannons read as five different black shapes (cone / barrel-on-wheels / finned tube on tripod /
squat mortar on turntable / long twin-rail gun). Statue reads as a skeleton holding a trophy high.

## Studio-side extras (added in Studio, not modelled)
Cannons: ParticleEmitter confetti / smoke / sparks at `Muzzle`, fuse sparks (Barrel), thruster flame
(Rocket), steam (Mortar), crystal pulse + coil beam (Meteor); ProximityPrompt at `Seat`.
Statue: slow rebirth-ring rotation, sparkle particles. Egg stand: egg model spins over the ring;
Accent recoloured per peak. Boards: SurfaceGui on `Screen`. Chest: bob + glow pulse, ProximityPrompt.

## Budget
Target tris: cannons 3–9k, statue ≤ 12k, booths ≤ 8k, boards ≤ 4k (each ≤ 15k per mesh).
Parts before join: 60–250 per model.
