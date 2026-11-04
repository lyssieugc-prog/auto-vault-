"""
Map layout template — house-style hub-and-spoke world:
central studded spawn plaza -> radiating chevron paths -> N zone islands (each its own sub-palette)
+ water ring + ring of player plots. Each region exports as a separate FBX chunk (streaming
friendly, under the per-mesh triangle budget). Positions are written to layout.json so the Studio
integration step can place spawn/zone triggers/plot markers exactly.

Usage: blender -b -P map_layout.py -- <out_dir>
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import vault_blocky as vb  # noqa: E402

LAYOUT = {
    "plaza_size": 60,
    "zone_radius": 150,
    "zone_size": 80,
    "zones": [
        {"name": "Meadow", "color": "#7ADE43"},
        {"name": "Desert", "color": "#E2C608"},
        {"name": "Frost", "color": "#A7D8FF"},
        {"name": "Lava", "color": "#E13A2A"},
        {"name": "Candy", "color": "#DD70E1"},
    ],
    "plots": 8,
    "plot_radius": 70,
    "plot_size": 24,
}


def build(layout=LAYOUT):
    vb.reset_scene()
    chunks = {}
    markers = {"spawn": [0, 0, 1], "zones": [], "plots": []}

    plaza = vb.studded_plate("Plaza", layout["plaza_size"], layout["plaza_size"], 2, (0, 0, -2), "white", spacing=4)
    chunks["Plaza"] = [plaza]

    water = vb.cylinder("WaterRing", layout["zone_radius"] - layout["zone_size"] / 2 - 4, 0.5, (0, 0, -1.5),
                        "water", sides=48)
    chunks["Water"] = [water]

    plots = []
    for i, (pos, angle) in enumerate(vb.ring_positions(layout["plots"], layout["plot_radius"], -1.5)):
        p = vb.studded_plate(f"Plot{i + 1}", layout["plot_size"], layout["plot_size"], 1.5, pos, "blue", spacing=4)
        plots.append(p)
        markers["plots"].append({"index": i + 1, "position": list(pos), "facing": math.degrees(angle) + 180})
    chunks["Plots"] = plots

    for i, ((x, y, _), angle) in enumerate(vb.ring_positions(len(layout["zones"]), layout["zone_radius"])):
        zone = layout["zones"][i]
        name = zone["name"]
        island = vb.studded_plate(f"Zone_{name}", layout["zone_size"], layout["zone_size"], 4, (x, y, -4),
                                  zone["color"], spacing=4)
        terrace = vb.block(f"Zone_{name}_Terrace", (layout["zone_size"] * 0.4, layout["zone_size"] * 0.4, 6),
                           (x, y, 0), zone["color"], bevel=0.5)
        # Chevron path from plaza edge to the island
        length = layout["zone_radius"] - layout["zone_size"] / 2 - layout["plaza_size"] / 2
        mid = layout["plaza_size"] / 2 + length / 2
        # Path top sits 0.2 above plaza/plot tops so it never z-fights where it crosses a plot.
        path = vb.block(f"Path_{name}", (8, length, 0.6), (math.cos(angle) * mid, math.sin(angle) * mid, -0.4),
                        "yellow", bevel=0.1)
        path.rotation_euler[2] = angle - math.pi / 2
        gate = vb.block(f"Gate_{name}", (12, 2, 10), (x - math.cos(angle) * 36, y - math.sin(angle) * 36, 0),
                        "navy", bevel=0.4)
        gate.rotation_euler[2] = angle - math.pi / 2
        chunks[f"Zone_{name}"] = [island, terrace, path, gate]
        markers["zones"].append({"name": name, "order": i + 1, "center": [x, y, 0], "gate":
                                 [x - math.cos(angle) * 36, y - math.sin(angle) * 36, 0]})
    return chunks, markers


def main(out_dir, layout=LAYOUT):
    chunks, markers = build(layout)
    results = []
    for name, objs in chunks.items():
        report = vb.poly_report(objs)
        merged = vb.join(f"Map_{name}", objs) if len(objs) > 1 else objs[0]
        fbx = vb.export_fbx(os.path.join(out_dir, f"Map_{name}.fbx"), [merged])
        results.append({"name": f"Map_{name}", "fbx": fbx, **report})
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "layout.json"), "w", encoding="utf-8") as f:
        json.dump(markers, f, indent=2)
    return results


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    for r in main(argv[0] if argv else "out"):
        print(r)
