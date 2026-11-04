# Genre: Building / Roleplay

**Loop**: earn via jobs/minigames → buy furniture → place on plot (grid build mode) → visitors rate.
**Systems**: Plots, Inventory (furniture), Currency, DataService (placed builds: serialize as
`{id, cframe components, color}` arrays), Monetization, Rewards, Tutorial, Guard (placement
validation: bounds, overlap, item ownership).
**Content v1**: 80–150 furniture items (Blender kit), 3 house shells, 1 neighbourhood.
**Pitfalls**: DataStore size (4MB per key — compress builds), unvalidated placements.
