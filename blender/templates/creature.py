"""
Creature / pet template — house-style GOOD list: many chunky parts, 1–2 hue body + glow accent,
glowing eyes, spikes, distinct silhouette. Copy into games/<slug>/blender/ and edit SPEC.

Usage: blender -b -P creature.py -- <out_dir>
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import vault_blocky as vb  # noqa: E402

SPEC = {
    "name": "LavaPup",
    "body": "#E13A2A",
    "accent": "#FF8A1F",
    "glow": "#FFD93B",
    "rarity": "Epic",  # rarer => more glow parts / spikes (see style/house-style.md §4)
}

GLOW_BY_RARITY = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4, "Mythic": 6, "Secret": 8}


def build(spec=SPEC):
    vb.reset_scene()
    parts = []
    body, accent, glow = spec["body"], spec["accent"], spec["glow"]
    # Body + belly + head (oversized head = readable silhouette)
    parts.append(vb.block("Body", (2.2, 3.0, 1.8), (0, 0, 0.9), body, bevel=0.25, segments=2))
    parts.append(vb.block("Belly", (1.6, 2.2, 0.3), (0, 0, 0.75), accent, bevel=0.1))
    parts.append(vb.block("Head", (2.4, 2.2, 2.0), (0, 1.9, 2.0), body, bevel=0.3, segments=2))
    parts.append(vb.block("Snout", (1.4, 0.9, 0.8), (0, 3.15, 2.1), accent, bevel=0.15))
    # Glowing eyes = focal point
    for side in (-1, 1):
        parts.append(vb.block(f"Eye{side}", (0.5, 0.2, 0.6), (side * 0.6, 3.0, 2.95), glow, bevel=0.05, emission=4))
        parts.append(vb.block(f"Ear{side}", (0.5, 0.4, 0.9), (side * 0.85, 1.6, 4.0), accent, bevel=0.1))
    # Legs
    for i, (x, y) in enumerate([(-0.8, 1.0), (0.8, 1.0), (-0.8, -1.0), (0.8, -1.0)]):
        parts.append(vb.block(f"Leg{i}", (0.7, 0.7, 0.9), (x, y, 0), accent, bevel=0.12))
    # Tail
    parts.append(vb.block("Tail", (0.5, 1.4, 0.5), (0, -2.0, 1.6), body, bevel=0.12))
    # Spikes / emissive cracks scale with rarity
    n = GLOW_BY_RARITY.get(spec["rarity"], 2)
    for i in range(n + 2):
        y = 1.2 - i * (2.6 / max(n + 1, 1))
        parts.append(vb.block(f"Spike{i}", (0.4, 0.4, 0.6), (0, y, 2.65), glow if i < n else accent, bevel=0.06,
                              emission=2 if i < n else 0))
    root = vb.group(spec["name"], parts)
    root["vault_rarity"] = spec["rarity"]
    return root, parts


def main(out_dir, spec=SPEC):
    root, parts = build(spec)
    report = vb.poly_report(parts)
    model = vb.join(spec["name"], parts)
    fbx = vb.export_fbx(os.path.join(out_dir, f"{spec['name']}.fbx"), [model])
    glb = vb.export_glb(os.path.join(out_dir, f"{spec['name']}.glb"), [model])
    return {"name": spec["name"], "fbx": fbx, "glb": glb, **report}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    print(main(argv[0] if argv else "out"))
