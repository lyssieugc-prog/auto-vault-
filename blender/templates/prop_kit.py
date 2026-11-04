"""
Prop kit template — chunky blocky world props (tree, rock, lamp, chevron road tile, egg stand).
Each prop exports as its own FBX so Studio can bulk-import the folder.

Usage: blender -b -P prop_kit.py -- <out_dir>
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import vault_blocky as vb  # noqa: E402


def tree():
    parts = [vb.block("Trunk", (1.0, 1.0, 3.0), (0, 0, 0), "wood", bevel=0.1)]
    for i, (s, z) in enumerate([(4.0, 3.0), (3.0, 4.6), (1.8, 5.9)]):
        parts.append(vb.block(f"Leaves{i}", (s, s, 1.6), (0, 0, z), "green", bevel=0.25, segments=2))
    return parts


def rock():
    return [
        vb.block("RockA", (2.4, 2.0, 1.4), (0, 0, 0), "stone", bevel=0.3),
        vb.block("RockB", (1.4, 1.2, 1.0), (0.9, 0.6, 1.0), "stone", bevel=0.25),
    ]


def lamp():
    return [
        vb.block("Post", (0.4, 0.4, 4.0), (0, 0, 0), "navy", bevel=0.05),
        vb.block("Light", (0.9, 0.9, 0.9), (0, 0, 4.0), "gold", bevel=0.2, emission=5),
    ]


def chevron_tile():
    plate = vb.studded_plate("RoadTile", 4, 4, 0.4, (0, 0, 0), "yellow")
    arrows = [vb.wedge(f"Chevron{i}", (2.4, 0.6, 0.15), (0, -1 + i * 1.2, 0.4), "white") for i in range(2)]
    return [plate] + arrows


def egg_stand():
    base = vb.studded_plate("StandBase", 6, 6, 1.0, (0, 0, 0), "purple")
    pillar = vb.cylinder("Pillar", 1.2, 2.0, (0, 0, 1.0), "navy", sides=10)
    egg = vb.block("EggPreview", (2.0, 2.0, 2.6), (0, 0, 3.0), "pink", bevel=0.8, segments=3, emission=1.5)
    return [base, pillar, egg]


KIT = {"Tree": tree, "Rock": rock, "Lamp": lamp, "RoadTile": chevron_tile, "EggStand": egg_stand}


def main(out_dir):
    results = []
    for name, fn in KIT.items():
        vb.reset_scene()
        parts = fn()
        report = vb.poly_report(parts)
        model = vb.join(name, parts)
        fbx = vb.export_fbx(os.path.join(out_dir, f"{name}.fbx"), [model])
        results.append({"name": name, "fbx": fbx, **report})
    return results


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    for r in main(argv[0] if argv else "out"):
        print(r)
