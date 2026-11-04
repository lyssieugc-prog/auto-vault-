"""
Pet / creature template — v2 (rebuilt after owner rejected v1 as "horrible").

House rules this template must satisfy (style/house-style.md §4, lessons L-20261104-03):
- Chibi Roblox-pet proportions: HEAD is the biggest part (≈1.4x body height), short body,
  stubby legs. Cute + readable at 50 studs.
- Studs on the visible top surfaces as TEXTURE only (never stud geometry).
- A real FACE: big white eyes with pupils + sparkle highlights, blush, smiling mouth with teeth.
- 3+ hues: body, light belly/muzzle, dark trim (paws, ear tips, pattern) + one glow accent.
- Many chunky parts (target 50+ before join): stepped ears, toe pads, collar + tag, pattern
  spots, stepped tail with glowing tip, glow cracks.
- Rarity scales spectacle: more glow cracks, orbiting cubes, aura ring, crown (Mythic+).
- NEVER: few plain boxes, single flat colour, no face, Minecraft-mob look, smooth realistic animal.

Usage: blender -b -P creature.py -- <out_dir>     (or python with the bpy module)
Edit SPEC per pet; keep the structure.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import vault_blocky as vb  # noqa: E402

SPEC = {
    "name": "LavaPup",
    "rarity": "Legendary",
    "body": "#FF6A3D",  # main hue
    "light": "#FFD2A8",  # belly / muzzle / inner ear
    "dark": "#B8321A",  # paws, ear tips, pattern, tail segments
    "glow": "#FFD93B",  # emissive accent (cracks, tail flame, orbiters, tag)
    "eye_white": "#FFFFFF",
    "pupil": "#1A1A1A",
    "blush": "#FF8FB1",
    "collar": "#2590D1",
}

RARITY_LEVEL = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4, "Mythic": 5, "Secret": 6}


def build(spec=SPEC):
    vb.reset_scene()
    s = spec
    lvl = RARITY_LEVEL.get(s["rarity"], 2)
    P = []

    def add(obj):
        P.append(obj)
        return obj

    def box(name, size, loc, color, bevel=0.08, seg=2, emission=0.0):
        return add(vb.block(name, size, loc, color, bevel=bevel, segments=seg, emission=emission))

    # ---- Legs + toe pads (stubby, chunky) ----
    for i, (x, y) in enumerate([(-0.75, 0.55), (0.75, 0.55), (-0.75, -1.05), (0.75, -1.05)]):
        box(f"Leg{i}", (0.8, 0.8, 0.75), (x, y, 0), s["body"], bevel=0.18, seg=3)
        box(f"Paw{i}", (0.86, 0.9, 0.28), (x, y + 0.04, 0), s["dark"], bevel=0.1)
        for t, tx in enumerate((-0.22, 0.0, 0.22)):
            box(f"Toe{i}_{t}", (0.18, 0.12, 0.14), (x + tx, y + 0.48, 0.06), s["light"], bevel=0.04, seg=1)

    # ---- Body (short, rounded) + belly ----
    body = box("Body", (2.3, 2.5, 1.45), (0, -0.25, 0.6), s["body"], bevel=0.4, seg=3)
    box("Belly", (1.5, 0.22, 0.95), (0, 1.0, 0.75), s["light"], bevel=0.08)
    # Back studs (visible behind the head)
    vb.stud_surface(body, "top")  # studs are TEXTURE only (L-20261104-04)
    # Pattern spots on the sides
    for side in (-1, 1):
        box(f"SpotA{side}", (0.08, 0.55, 0.45), (side * 1.16, -0.6, 1.15), s["dark"], bevel=0.03, seg=1)
        box(f"SpotB{side}", (0.08, 0.35, 0.3), (side * 1.16, 0.15, 0.95), s["dark"], bevel=0.03, seg=1)

    # ---- Collar + glowing tag ----
    box("Collar", (2.5, 2.1, 0.32), (0, 0.85, 1.9), s["collar"], bevel=0.1)
    box("Tag", (0.42, 0.14, 0.42), (0, 1.95, 1.72), s["glow"], bevel=0.06, emission=2.5)

    # ---- Head (biggest part) ----
    hz, hy = 2.05, 0.95  # head bottom z, head center y
    hw, hd, hh = 3.1, 2.6, 2.4
    box("Head", (hw, hd, hh), (0, hy, hz), s["body"], bevel=0.5, seg=3)
    front = hy + hd / 2  # y of face plane
    top = hz + hh  # z of head top
    # Head studs (2x2) — the signature Roblox look
    vb.stud_surface(P[-1], "top")  # head top: texture studs
    back = hy - hd / 2  # y of the back of the head
    # Back-of-head stripes (no big blank faces anywhere — every side gets detail)
    for i, (w, z) in enumerate(((1.8, top - 0.6), (1.4, top - 1.1), (0.9, top - 1.55))):
        box(f"HeadStripe{i}", (w, 0.1, 0.22), (0, back - 0.02, z), s["dark"], bevel=0.03, seg=1)
    # Cheek tufts on the head sides (breaks up flat side walls + widens the silhouette)
    for side in (-1, 1):
        for j, (dy, dz, sz) in enumerate(((0.5, 0.55, 0.55), (0.0, 0.4, 0.45), (-0.5, 0.6, 0.38))):
            box(f"Cheek{side}_{j}", (0.3, sz, sz), (side * (hw / 2 + 0.08), hy + dy, hz + dz), s["light"],
                bevel=0.06)
        box(f"HeadSpot{side}", (0.08, 0.6, 0.5), (side * (hw / 2 + 0.01), hy - 0.4, hz + 1.5), s["dark"], bevel=0.03,
            seg=1)
    # Theme crest: stepped flame tuft on top-back of the head (strong silhouette)
    for i, (w, dz, col) in enumerate(((0.8, 0.0, "dark"), (0.6, 0.35, "body"), (0.42, 0.68, "glow"))):
        box(f"Crest{i}", (w, w, 0.4), (0, back + 0.55, top + dz), s[col], bevel=0.08,
            emission=3 if col == "glow" else 0)

    # ---- Face ----
    box("Muzzle", (1.5, 0.35, 0.8), (0, front + 0.05, hz + 0.3), s["light"], bevel=0.15, seg=2)
    box("Nose", (0.42, 0.18, 0.26), (0, front + 0.22, hz + 0.85), s["pupil"], bevel=0.06)
    box("Mouth", (0.62, 0.12, 0.12), (0, front + 0.2, hz + 0.45), s["pupil"], bevel=0.03, seg=1)
    for side in (-1, 1):
        box(f"Tooth{side}", (0.14, 0.08, 0.16), (side * 0.15, front + 0.25, hz + 0.32), s["eye_white"], bevel=0.02, seg=1)
        ex = side * 0.72
        box(f"Eye{side}", (0.78, 0.12, 0.92), (ex, front, hz + 1.1), s["eye_white"], bevel=0.12, seg=2)
        pupil_col = s["glow"] if lvl >= 5 else s["pupil"]
        box(f"Pupil{side}", (0.46, 0.1, 0.62), (ex + side * -0.08, front + 0.07, hz + 1.17), pupil_col,
            bevel=0.08, emission=3 if lvl >= 5 else 0)
        box(f"Sparkle{side}", (0.16, 0.06, 0.16), (ex + side * -0.2, front + 0.13, hz + 1.55), s["eye_white"],
            bevel=0.02, seg=1, emission=1.5)
        box(f"Blush{side}", (0.5, 0.08, 0.22), (side * 1.12, front, hz + 0.65), s["blush"], bevel=0.04, seg=1)

        # ---- Stepped ears ----
        ear_x = side * 1.05
        box(f"EarBase{side}", (0.8, 0.6, 0.6), (ear_x, hy - 0.2, top - 0.15), s["body"], bevel=0.12)
        box(f"EarTip{side}", (0.55, 0.45, 0.5), (ear_x + side * 0.08, hy - 0.2, top + 0.4), s["dark"], bevel=0.1)
        box(f"EarInner{side}", (0.4, 0.08, 0.55), (ear_x, hy + 0.1, top - 0.05), s["light"], bevel=0.03, seg=1)

    # ---- Stepped tail curling up into a flame ----
    tail = ((-1.6, 1.2), (-2.0, 1.45), (-2.3, 1.85), (-2.45, 2.3))
    for i, (ty, tz) in enumerate(tail):
        box(f"Tail{i}", (0.5, 0.48, 0.48), (0, ty, tz), s["dark"] if i % 2 else s["body"], bevel=0.1)
    for i, (sz, dz, col) in enumerate(((0.7, 0.0, "body"), (0.55, 0.45, "glow"), (0.32, 0.85, "eye_white"))):
        box(f"TailFlame{i}", (sz, sz, 0.5), (0, -2.45, 2.75 + dz), s[col], bevel=0.1,
            emission=0 if col == "body" else 4)

    # ---- Rarity spectacle ----
    for i in range(min(lvl, 4)):  # glow cracks on the body sides
        side = -1 if i % 2 else 1
        box(f"Crack{i}", (0.06, 0.12, 0.5), (side * 1.17, -1.05 + (i // 2) * 0.5, 0.85), s["glow"], bevel=0.0,
            seg=1, emission=3)
    n_orbit = max(0, lvl - 1) * 2  # Rare+ get orbiting cubes
    for i in range(n_orbit):
        a = 2 * math.pi * i / max(n_orbit, 1)
        box(f"Orbit{i}", (0.32, 0.32, 0.32), (math.cos(a) * 2.7, math.sin(a) * 2.7 + 0.2, 2.6 + (i % 2) * 0.6),
            s["glow"], bevel=0.06, emission=3)
    if lvl >= 4:  # Legendary+ aura ring on the ground
        for i in range(16):
            a = 2 * math.pi * i / 16
            box(f"Aura{i}", (0.45, 0.2, 0.08), (math.cos(a) * 2.4, math.sin(a) * 2.4 - 0.2, 0), s["glow"], bevel=0.02,
                seg=1, emission=2)
    if lvl >= 5:  # Mythic+ crown
        box("CrownBase", (1.3, 1.0, 0.3), (0, hy - 0.2, top + 0.25), s["glow"], bevel=0.05, emission=2)
        for i, cx in enumerate((-0.45, 0, 0.45)):
            box(f"CrownSpike{i}", (0.25, 0.25, 0.4), (cx, hy - 0.2, top + 0.55), s["glow"], bevel=0.04, emission=2)

    root = vb.group(s["name"], P)
    root["vault_rarity"] = s["rarity"]
    root["vault_template"] = "creature_v2"
    return root, P


def main(out_dir, spec=SPEC):
    _, parts = build(spec)
    report = vb.poly_report(parts)
    model = vb.join(spec["name"], parts)
    fbx = vb.export_fbx(os.path.join(out_dir, f"{spec['name']}.fbx"), [model])
    glb = vb.export_glb(os.path.join(out_dir, f"{spec['name']}.glb"), [model])
    return {"name": spec["name"], "fbx": fbx, "glb": glb, **report}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    print(main(argv[0] if argv else "out"))
