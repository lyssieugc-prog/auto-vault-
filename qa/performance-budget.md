# Performance Budget (mobile-first)

| Item | Budget |
|---|---|
| Triangles per MeshPart | ≤ 15k (Roblox hard cap 20k) |
| Visible scene triangles (typical view) | ≤ 400k |
| Unique MeshParts in map | ≤ 300 (join small props in Blender) |
| Real studs per surface | ≤ 400, else stud texture |
| Draw-call friendly materials | ≤ 12 colours per map chunk |
| ParticleEmitters active near player | ≤ 25, Rate ≤ 30 each |
| Textures | ≤ 1024px, UI icons 256–512px |
| Client memory (Studio stats, phone emulation) | ≤ 900 MB |
| Server heartbeat | ≥ 55 Hz with 8 players |
| Remote traffic | no per-frame remotes; batch updates ≤ 10/s per player |
| DataStore | save on leave + every 90s; profile < 100 KB |

Use StreamingEnabled for maps larger than ~1000 studs across.
