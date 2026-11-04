# Profile: Obby

**Palette**: one strong hue per stage band (every 10 stages), kill parts always neon red
`#FF2A2A` with glow, checkpoints always lime with stud tops, safe platforms high contrast vs void.
**Shapes & studs**: studded platforms, chunky obstacles (spinners, crushers, conveyors) with
telegraphed motion. Silhouettes must read against the skybox.
**Lighting**: bright; fog only for depth cueing, never to hide the next jump.
**UI deltas**: stage counter, skip-stage product button, checkpoint flash, timer for speedruns.
**Map deltas**: linear or tower; every 10 stages a themed "world" with a landmark reward room.
**Model deltas**: obstacle kit authored in Blender as modular pieces (follow the
`blender/templates/prop_kit.py` pattern: one function per piece, one FBX each).
**Systems**: Currency (coins), Quests/Rewards, Monetization (skip stage, gravity coil), Tutorial,
DataStore (stage).
**Never**: invisible kill bricks, jumps that need pixel-precision on mobile, same color for safe
and deadly surfaces.
