"""
My Vet Office — Golden Retriever (hero patient), RIGGED for Roblox Motor6D procedural animation.

Original asset (not from the calibration sample). Chunky-stylized simulator look with believable dog
anatomy: deep chest + cream bib, tucked loin, angled hind legs (stifle forward, hock back), feathered
legs + "pants", plumed tail, domed head with stop + cream muzzle, floppy ears, big brown eyes with
sparkles and SEPARATE eyelids, opening jaw with tongue, red collar + glowing vet ID tag.

Every piece belongs to exactly one bone; pieces of a bone are joined into `<Bone>_Geo`, skinned 100 %
to that bone. Joints are hidden by overlapping rounded caps on the child segment.
Studs: world-space TEXTURE at vb.STUD_PITCH (0.5) on every piece except face pieces (eyes, nose,
mouth/tongue) and neon.

Usage (repo root, bpy python):
    python games/my-vet-office/blender/golden_retriever.py            # build + check + export
    python games/my-vet-office/blender/golden_retriever.py --render   # + previews (front/side/back/3-4/sit/lie)
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vet_common as vc  # noqa: E402
from vet_common import box, dome, orb, ring, seg, taper, tube, vb, vk  # noqa: E402

NAME = "GoldenRetriever"
FILE = "golden_retriever"
MAX_TRIS = 12000  # hero pet budget (see handoff.md)

COAT = vk.shades("#E9A23B")  # light / base / dark / deep
C = {
    "coat": COAT["base"], "coat_l": COAT["light"], "coat_d": COAT["dark"], "coat_dd": COAT["deep"],
    "cream": "#FFD996", "cream_l": "#FFEAC0",
    "nose": "#2B1D19", "nostril": "#120C0A", "nose_hi": "#8A7A76", "claw": "#4A3426",
    "white": "#FFFFFF", "iris": "#6B3A1A", "iris_l": "#A0612C", "pupil": "#141010", "lash": "#5A3410",
    "tongue": "#FF6F91", "tongue_d": "#E04F78", "mouth": "#5A1E2A",
    "collar": "#E8403A", "collar_d": "#B8261F", "steel": "#D7DEE8", "tag": "#3EE6FF",
}

# Bone table: (name, parent, pivot). L = dog's left = -X. Single source of truth for the rig.
X_F, X_B = 0.38, 0.40
HY, HZ = 1.56, 2.80  # skull centre (y, z)
FACE = HY + 0.49  # skull front plane y
BONES = [
    ("Root", None, (0, 0, 0)),
    ("Pelvis", "Root", (0, -0.95, 1.74)),
    ("SpineLow", "Pelvis", (0, -0.50, 1.80)),
    ("SpineMid", "SpineLow", (0, 0.0, 1.84)),
    ("Chest", "SpineMid", (0, 0.50, 1.86)),
    ("Neck", "Chest", (0, 0.95, 2.02)),
    ("Head", "Neck", (0, 1.30, 2.56)),
    ("Jaw", "Head", (0, FACE - 0.30, 2.42)),
    ("EarL", "Head", (-0.50, HY - 0.08, HZ + 0.26)),
    ("EarR", "Head", (0.50, HY - 0.08, HZ + 0.26)),
    ("LidL", "Head", (-0.28, FACE - 0.07, HZ + 0.07)),
    ("LidR", "Head", (0.28, FACE - 0.07, HZ + 0.07)),
    ("EyeL", "Head", (-0.28, FACE - 0.07, HZ + 0.07)),
    ("EyeR", "Head", (0.28, FACE - 0.07, HZ + 0.07)),
    ("Tail1", "Pelvis", (0, -1.36, 1.98)),
    ("Tail2", "Tail1", (0, -1.62, 2.14)),
    ("Tail3", "Tail2", (0, -1.86, 2.27)),
    ("Tail4", "Tail3", (0, -2.09, 2.33)),
    ("ShoulderL", "Chest", (-X_F, 0.74, 1.62)),
    ("ElbowL", "ShoulderL", (-X_F, 0.56, 1.00)),
    ("WristL", "ElbowL", (-X_F, 0.66, 0.32)),
    ("PawFL", "WristL", (-X_F, 0.72, 0.13)),
    ("ShoulderR", "Chest", (X_F, 0.74, 1.62)),
    ("ElbowR", "ShoulderR", (X_F, 0.56, 1.00)),
    ("WristR", "ElbowR", (X_F, 0.66, 0.32)),
    ("PawFR", "WristR", (X_F, 0.72, 0.13)),
    ("HipL", "Pelvis", (-X_B, -0.98, 1.62)),
    ("KneeL", "HipL", (-X_B, -0.74, 0.98)),
    ("HockL", "KneeL", (-X_B, -1.17, 0.46)),
    ("PawBL", "HockL", (-X_B, -1.10, 0.13)),
    ("HipR", "Pelvis", (X_B, -0.98, 1.62)),
    ("KneeR", "HipR", (X_B, -0.74, 0.98)),
    ("HockR", "KneeR", (X_B, -1.17, 0.46)),
    ("PawBR", "HockR", (X_B, -1.10, 0.13)),
]
REQUIRED_BONES = [b[0] for b in BONES]
PIV = {b[0]: b[2] for b in BONES}

# Poses for the posed tests (degrees, bone-local == world axes at rest; +X rot = swing forward/up).
POSES = {
    "sit": {
        "Pelvis": {"rot": (38, 0, 0), "loc": (0, 0.1, -1.03)},
        "Neck": (-14, 0, 0), "Head": (-14, 0, 0),
        "ShoulderL": (-28, 0, 0), "ShoulderR": (-28, 0, 0),
        "ElbowL": (-8, 0, 0), "ElbowR": (-8, 0, 0),
        "WristL": (2, 0, 0), "WristR": (2, 0, 0),
        "HipL": (52, 0, -6), "HipR": (52, 0, 6),
        "KneeL": (-112, 0, 0), "KneeR": (-112, 0, 0),
        "HockL": (24, 0, 0), "HockR": (24, 0, 0),
        "Tail1": (-52, 0, 18), "Tail2": (-14, 0, 14), "Tail3": (-6, 0, 10), "Tail4": (0, 0, 6),
        "Jaw": (-8, 0, 0), "EarL": (0, -6, 0), "EarR": (0, 6, 0),
    },
    "lie": {
        "Pelvis": {"rot": (0, 0, 0), "loc": (0, 0, -0.87)},
        "Neck": (-4, 0, 0), "Head": (-6, 0, 8),
        "ShoulderL": (70, 0, 0), "ShoulderR": (70, 0, 0),
        "ElbowL": (10, 0, 0), "ElbowR": (10, 0, 0),
        "PawFL": (-80, 0, 0), "PawFR": (-80, 0, 0),
        "HipL": (45, 0, -14), "HipR": (45, 0, 14),
        "KneeL": (-80, 0, 0), "KneeR": (-80, 0, 0),
        "HockL": (108, 0, 0), "HockR": (108, 0, 0),
        "PawBL": (-73, 0, 0), "PawBR": (-73, 0, 0),
        "Tail1": (-30, 0, 24), "Tail2": (-6, 0, 18), "Tail3": (0, 0, 14), "Tail4": (0, 0, 10),
        "LidL": (-24, 0, 0), "LidR": (-24, 0, 0), "EarL": (0, -4, 0), "EarR": (0, 4, 0),
    },
}



def build():
    vb.reset_scene()
    P = {b: [] for b in REQUIRED_BONES}

    def add(bone, *objs):
        P[bone].extend(objs)
        return objs[0] if objs else None

    # ------------------------------------------------------------------ torso: 4 overlapping rounded masses
    # (shorter + deeper than v1; one narrow darker back stripe instead of plank-like saddle plates)
    torso = (("Pelvis", "Rump", (1.12, 0.9, 0.92), (0, -0.98, 1.70)),
             ("SpineLow", "Loin", (1.06, 0.62, 0.82), (0, -0.48, 1.75)),
             ("SpineMid", "Ribs", (1.2, 0.62, 1.04), (0, 0.02, 1.62)),
             ("Chest", "Barrel", (1.24, 0.72, 1.16), (0, 0.5, 1.6)))
    for bone, nm, size, c in torso:
        # rounded only along Y: neighbouring masses butt like one continuous chunky body (no bead bands)
        add(bone, box(nm, size, c, C["coat"], r=0.3, seg=2, bevel_axis=1))
    # darker back saddle: 4 butting pieces at one common height (no steps / coplanar overlaps)
    for bone, (y0, y1) in (("Pelvis", (-1.32, -0.74)), ("SpineLow", (-0.74, -0.24)), ("SpineMid", (-0.24, 0.26)),
                           ("Chest", (0.26, 0.78))):
        add(bone, box(f"Saddle{bone}", (0.52, y1 - y0, 0.16), (0, (y0 + y1) / 2, 2.12), C["coat_d"], r=0.07,
                      bevel_axis=1))
    add("Pelvis", box("RumpEnd", (1.08, 0.42, 0.9), (0, -1.38, 1.71), C["coat"], r=0.22, seg=2),
        box("RumpPatch", (0.56, 0.12, 0.42), (0, -1.6, 1.62), C["coat_l"], r=0.05),
        box("SaddleEnd", (0.5, 0.24, 0.14), (0, -1.42, 2.1), C["coat_d"], r=0.06))
    add("Chest", box("BarrelFront", (1.18, 0.36, 1.08), (0, 0.84, 1.62), C["coat"], r=0.24, seg=2))
    add("Pelvis",
        taper("BritchesL", (0.32, 0.26, 0.5), (-0.27, -1.55, 1.48), C["cream"], top=(0.7, 0.7), r=0.09,
              rot=(205, 0, -10)),
        taper("BritchesR", (0.32, 0.26, 0.5), (0.27, -1.55, 1.48), C["cream"], top=(0.7, 0.7), r=0.09,
              rot=(205, 0, 10)),
        box("RumpUnder", (0.5, 0.3, 0.3), (0, -1.36, 1.36), C["coat_l"], r=0.1, seg=2),
        taper("CroupTuft", (0.42, 0.3, 0.16), (0, -1.36, 2.06), C["coat_l"], top=(0.6, 0.7), r=0.06, rot=(-30, 0, 0)))
    add("SpineLow", box("LoinBelly", (0.62, 0.56, 0.16), (0, -0.45, 1.38), C["cream"], r=0.07))
    for i, (y, h) in enumerate(((-0.22, 0.22), (0.04, 0.26))):  # belly feathering
        add("SpineMid", taper(f"BellyFringe{i}", (0.72, 0.36, h), (0, y, 1.12 - h / 2 + 0.07), C["cream"],
                              top=(0.86, 0.8), r=0.08, rot=(180 - 6 * i, 0, 0)))
    # cream bib / chest ruff: 3 staggered rows of chunky tufts, pointing down
    for row, (z, w, n, yb, h) in enumerate(((1.84, 0.8, 2, 0.95, 0.56), (1.5, 0.9, 3, 0.98, 0.5),
                                            (1.2, 0.66, 2, 0.94, 0.4))):
        for k in range(n):
            x = (k - (n - 1) / 2) * (w / n)
            tone = C["cream_l"] if (k + row) % 2 == 0 else C["cream"]
            add("Chest", taper(f"Ruff{row}_{k}", (w / n + 0.12, 0.28, h), (x, yb + 0.03 * (k % 2), z),
                               tone, top=(1.15, 1.1), r=0.11, seg=2, rot=(188, 0, (k - (n - 1) / 2) * -10)))
    add("Chest", taper("BrisketTuft", (0.56, 0.46, 0.22), (0, 0.6, 1.0), C["cream"], top=(1.15, 1.15), r=0.08,
                       rot=(180, 0, 0)))

    # ------------------------------------------------------------------ neck + collar + vet ID tag
    nrot = (-32, 0, 0)
    add("Neck",
        taper("NeckMass", (0.84, 0.78, 1.0), (0, 1.1, 2.3), C["coat"], top=(0.92, 0.9), r=0.24, seg=2, rot=nrot),
        taper("NeckRuff", (0.7, 0.36, 0.66), (0, 1.38, 2.06), C["cream"], top=(0.8, 0.8), r=0.12, rot=(-24, 0, 0)),
        taper("Scruff", (0.6, 0.34, 0.3), (0, 0.92, 2.5), C["coat_d"], top=(0.7, 0.8), r=0.1, rot=(-40, 0, 0)))
    for s in (-1, 1):
        add("Neck", taper(f"NeckSideFluff{s}", (0.16, 0.5, 0.56), (s * 0.42, 1.12, 2.2), C["coat_l"],
                          top=(0.6, 0.7), r=0.06, rot=(-30, 0, s * 4)))
    cc = (0, 1.13, 2.27)
    add("Neck",
        ring("Collar", 0.45, 0.1, 0.17, cc, C["collar"], sides=14, rot=nrot, scale=(1.08, 1.0)),
        ring("CollarStitchTop", 0.5, 0.03, 0.03, _off(cc, nrot, (0, 0, 0.065)), C["collar_d"], sides=12, rot=nrot,
             scale=(1.08, 1.0)),
        ring("CollarStitchBot", 0.5, 0.03, 0.03, _off(cc, nrot, (0, 0, -0.065)), C["collar_d"], sides=12, rot=nrot,
             scale=(1.08, 1.0)))
    for s in (-1, 1):  # rivets along the band
        for k in range(2):
            a = math.radians(40 + k * 34)
            p = _off(cc, nrot, (s * math.sin(a) * 0.53, math.cos(a) * 0.5, 0))
            add("Neck", box(f"Rivet{s}_{k}", (0.07, 0.07, 0.07), p, C["steel"], r=0.02, rot=nrot, roughness=0.3))
    buckle = _off(cc, nrot, (-0.5, -0.08, 0))
    add("Neck", box("Buckle", (0.08, 0.2, 0.22), buckle, C["steel"], r=0.03, rot=nrot, roughness=0.3),
        box("BucklePin", (0.05, 0.05, 0.16), _off(buckle, nrot, (-0.04, 0, 0)), C["collar_d"], r=0.01, rot=nrot))
    ringp = _off(cc, nrot, (0, 0.5, -0.06))
    tagp = _off(cc, nrot, (0, 0.53, -0.24))
    add("Neck",
        ring("TagRing", 0.06, 0.03, 0.03, ringp, C["steel"], sides=8, rot=(nrot[0] + 90, 0, 90)),
        tube("Tag", 0.13, 0.05, tagp, C["tag"], sides=10, rot=(nrot[0] - 90, 0, 0), emission=2.5),
        tube("TagRim", 0.15, 0.04, _off(tagp, nrot, (0, -0.02, 0)), C["steel"], sides=10, rot=(nrot[0] - 90, 0, 0),
             roughness=0.3),
        box("TagCrossV", (0.04, 0.03, 0.15), _off(tagp, nrot, (0, 0.035, 0)), C["white"], r=0.005, rot=nrot,
            studs=False),
        box("TagCrossH", (0.15, 0.03, 0.04), _off(tagp, nrot, (0, 0.035, 0)), C["white"], r=0.005, rot=nrot,
            studs=False))

    # ------------------------------------------------------------------ head (domed skull, stop, cream muzzle)
    F = FACE
    add("Head",
        box("Skull", (1.14, 0.98, 0.84), (0, HY, HZ), C["coat"], r=0.26, seg=2),
        taper("Crown", (0.86, 0.66, 0.16), (0, HY - 0.06, HZ + 0.44), C["coat_l"], top=(0.8, 0.8), r=0.07),
        taper("Occiput", (0.72, 0.2, 0.46), (0, HY - 0.5, HZ + 0.04), C["coat_d"], top=(0.8, 1.0), r=0.08,
              rot=(-90, 0, 0)),
        taper("Muzzle", (0.64, 0.6, 0.42), (0, F + 0.12, HZ - 0.24), C["cream"], top=(0.86, 0.92), r=0.15, seg=2),
        taper("NoseBridge", (0.32, 0.52, 0.12), (0, F + 0.08, HZ - 0.02), C["coat"], top=(0.72, 1.0), r=0.05),
        box("Stop", (0.46, 0.14, 0.16), (0, F - 0.04, HZ - 0.06), C["coat_d"], r=0.06),
        box("Nose", (0.32, 0.18, 0.2), (0, F + 0.43, HZ - 0.1), C["nose"], r=0.08, seg=2, studs=False,
            roughness=0.25),
        box("NoseShine", (0.12, 0.04, 0.05), (-0.05, F + 0.51, HZ - 0.03), C["nose_hi"], r=0.015, studs=False,
            roughness=0.2),
        box("UpperLip", (0.54, 0.36, 0.05), (0, F + 0.14, HZ - 0.415), C["mouth"], r=0.02, studs=False))
    for s in (-1, 1):
        add("Head",
            box(f"Nostril{s}", (0.07, 0.04, 0.05), (s * 0.075, F + 0.515, HZ - 0.12), C["nostril"], r=0.015,
                studs=False),
            box(f"Flew{s}", (0.25, 0.48, 0.3), (s * 0.25, F + 0.06, HZ - 0.33), C["cream_l"], r=0.1, seg=2,
                rot=(0, s * 6, 0)),
            box(f"Whisker{s}0", (0.045, 0.045, 0.045), (s * 0.31, F + 0.26, HZ - 0.24), C["coat_d"], r=0.0),
            box(f"Whisker{s}1", (0.045, 0.045, 0.045), (s * 0.25, F + 0.33, HZ - 0.2), C["coat_d"], r=0.0),
            box(f"Whisker{s}2", (0.045, 0.045, 0.045), (s * 0.33, F + 0.2, HZ - 0.18), C["coat_d"], r=0.0),
            taper(f"Brow{s}", (0.28, 0.14, 0.11), (s * 0.29, F + 0.0, HZ + 0.3), C["coat_l"], top=(0.7, 0.8),
                  r=0.035, rot=(0, 0, s * -10)),
            taper(f"Cheek{s}", (0.18, 0.5, 0.42), (s * 0.58, HY + 0.12, HZ - 0.25), C["cream"], top=(0.6, 0.8),
                  r=0.07, rot=(0, s * -8, 0)),
            box(f"TempleTuft{s}", (0.1, 0.34, 0.2), (s * 0.565, HY + 0.24, HZ + 0.12), C["coat_d"], r=0.04))

    # ------------------------------------------------------------------ jaw + tongue (Jaw bone)
    add("Jaw",
        taper("LowerJaw", (0.5, 0.56, 0.18), (0, F + 0.01, HZ - 0.5), C["cream"], top=(1.06, 1.0), r=0.08, seg=2),
        box("MouthInside", (0.44, 0.48, 0.05), (0, F + 0.03, HZ - 0.415), C["mouth"], r=0.02, studs=False),
        taper("Chin", (0.34, 0.24, 0.12), (0, F + 0.1, HZ - 0.62), C["cream_l"], top=(1.2, 1.2), r=0.05,
              rot=(180, 0, 0)),
        taper("Tongue", (0.26, 0.4, 0.08), (0, F + 0.33, HZ - 0.56), C["tongue"], top=(1.0, 1.0), r=0.035, seg=2,
              rot=(-38, 0, 0), studs=False),
        box("TongueLine", (0.03, 0.28, 0.02), (0, F + 0.345, HZ - 0.53), C["tongue_d"], r=0.005, rot=(-38, 0, 0),
            studs=False),
        box("ToothL", (0.05, 0.05, 0.07), (-0.17, F + 0.26, HZ - 0.39), C["white"], r=0.01, studs=False),
        box("ToothR", (0.05, 0.05, 0.07), (0.17, F + 0.26, HZ - 0.39), C["white"], r=0.01, studs=False))

    # ------------------------------------------------------------------ eyes (Eye bones) + lids (Lid bones)
    for side, s in (("L", -1), ("R", 1)):
        ex, ey, ez = PIV[f"Eye{side}"]
        add(f"Eye{side}",
            orb(f"Sclera{side}", (0.18, 0.12, 0.18), (ex, ey, ez), C["white"], segs=12, rings=8, studs=False,
                smooth=True),
            orb(f"Iris{side}", (0.135, 0.05, 0.145), (ex - s * 0.01, ey + 0.095, ez - 0.01), C["iris"], segs=10,
                rings=6, studs=False, smooth=True),
            orb(f"IrisRim{side}", (0.095, 0.03, 0.1), (ex - s * 0.01, ey + 0.117, ez - 0.035), C["iris_l"], segs=10,
                rings=5, studs=False, smooth=True),
            orb(f"Pupil{side}", (0.08, 0.03, 0.09), (ex - s * 0.01, ey + 0.132, ez), C["pupil"], segs=10, rings=5,
                studs=False, smooth=True),
            orb(f"Sparkle{side}", (0.048, 0.02, 0.048), (ex + s * 0.04, ey + 0.155, ez + 0.055), C["white"], segs=8,
                rings=4, studs=False, emission=1.5),
            orb(f"Sparkle2{side}", (0.024, 0.012, 0.024), (ex - s * 0.05, ey + 0.148, ez - 0.055), C["white"],
                segs=6, rings=4, studs=False, emission=1.5))
        lid_rot = (38, 0, 0)  # rest: relaxed open (rotate -X to blink)
        add(f"Lid{side}",
            dome(f"Lid{side}Shell", (0.2, 0.145, 0.2), (ex, ey, ez), C["coat"], segs=12, rings=8, rot=lid_rot),
            ring(f"Lid{side}Lash", 0.18, 0.035, 0.03, (ex, ey, ez), C["lash"], sides=12, rot=(lid_rot[0] - 90, 0, 0),
                 scale=(1.1, 0.85), studs=False))

    # ------------------------------------------------------------------ ears: hang from the skull side (no top bumps)
    for side, s in (("L", -1), ("R", 1)):
        px, py, pz = PIV[f"Ear{side}"]
        b = f"Ear{side}"
        tilt = (0, -s * 8, 0)
        add(b,
            box(f"EarFold{side}", (0.2, 0.44, 0.24), (px + s * 0.08, py, pz - 0.05), C["coat_d"], r=0.09, seg=2),
            taper(f"EarFlap{side}", (0.18, 0.54, 0.74), (px + s * 0.13, py + 0.02, pz - 0.42), C["coat_d"],
                  top=(0.9, 0.62), r=0.08, seg=2, rot=tilt),
            taper(f"EarPanel{side}", (0.06, 0.38, 0.5), (px + s * 0.235, py + 0.02, pz - 0.44), C["coat"],
                  top=(0.9, 0.6), r=0.025, rot=tilt))
        for k, (dy, h) in enumerate(((-0.16, 0.2), (0.02, 0.26), (0.19, 0.18))):
            add(b, taper(f"EarFringe{side}{k}", (0.17, 0.2, h), (px + s * 0.18, py + 0.02 + dy, pz - 0.8 - h / 3),
                         C["coat"] if k != 1 else C["coat_l"], top=(0.62, 0.7), r=0.05,
                         rot=(180 + (k - 1) * 10, s * 8, 0)))

    # ------------------------------------------------------------------ tail: happy upward curve + plume
    tail_pts = [PIV["Tail1"], PIV["Tail2"], PIV["Tail3"], PIV["Tail4"], (0, -2.33, 2.3)]
    for i in range(4):
        b = f"Tail{i + 1}"
        a, e = tail_pts[i], tail_pts[i + 1]
        th = 0.28 - i * 0.03
        add(b, seg(f"TailCore{i}", a, e, (th, th), C["coat"], r=0.08, segs=2, overlap=0.06),
            orb(f"TailJoint{i}", (th * 0.6,) * 3, a, C["coat"], segs=8, rings=5))
        mid = [(a[k] + e[k]) / 2 for k in range(3)]
        plume = (0.26, 0.36, 0.4, 0.3)[i]
        add(b, taper(f"Plume{i}", (0.22 - i * 0.02, 0.26, plume), (0, mid[1] + 0.02, mid[2] - plume / 2 + 0.02),
                     C["cream"] if i % 2 == 0 else C["cream_l"], top=(0.6, 0.75), r=0.06, rot=(180 + 24, 0, 0)),
            taper(f"TailTop{i}", (0.16 - i * 0.02, 0.24, 0.1), (0, mid[1], mid[2] + th / 2), C["coat_d"],
                  top=(0.6, 0.8), r=0.03))
    add("Tail4", taper("TailTip", (0.2, 0.22, 0.28), (0, -2.4, 2.28), C["cream_l"], top=(0.45, 0.5), r=0.06,
                       rot=(105, 0, 0)))

    # ------------------------------------------------------------------ legs (thicker than v1; flat feathering)
    def paw(bone, x, y):
        add(bone, box(f"{bone}Base", (0.44, 0.5, 0.17), (x, y, 0.09), C["coat_l"], r=0.06, seg=1))
        for k, dx in enumerate((-0.15, -0.05, 0.05, 0.15)):
            ty = y + 0.22 + (0.025 if k in (1, 2) else 0)
            add(bone, box(f"{bone}Toe{k}", (0.11, 0.15, 0.14), (dx + x, ty, 0.075), C["cream"] if k % 3 == 0
                          else C["coat_l"], r=0.045),
                box(f"{bone}Claw{k}", (0.05, 0.06, 0.045), (dx + x, ty + 0.09, 0.03), C["claw"], r=0.0,
                    studs=False))
        add(bone, taper(f"{bone}Fluff", (0.32, 0.2, 0.12), (x, y - 0.14, 0.2), C["cream"], top=(0.6, 0.8), r=0.04))

    for side, s in (("L", -1), ("R", 1)):
        x = s * X_F
        sh, el, wr, pw = PIV[f"Shoulder{side}"], PIV[f"Elbow{side}"], PIV[f"Wrist{side}"], PIV[f"PawF{side}"]
        add(f"Shoulder{side}",
            seg(f"UpperArm{side}", (x, sh[1] + 0.06, sh[2] + 0.2), el, (0.46, 0.56), C["coat"], r=0.15, segs=2,
                top=(0.82, 0.78), overlap=0.06),
            box(f"ShoulderMuscle{side}", (0.2, 0.5, 0.56), (x + s * 0.17, sh[1] + 0.02, sh[2] - 0.0),
                C["coat_l"], r=0.09, seg=2, rot=(14, 0, 0)))
        add(f"Elbow{side}",
            orb(f"ElbowCap{side}", (0.21, 0.22, 0.2), el, C["coat"], segs=10, rings=7),
            seg(f"Forearm{side}", el, wr, (0.35, 0.37), C["coat"], r=0.11, segs=2, top=(0.9, 0.9), overlap=0.04))
        for k, (t, ln) in enumerate(((0.25, 0.36), (0.6, 0.3))):  # feathering on the back of the foreleg
            p = [el[j] + (wr[j] - el[j]) * t for j in range(3)]
            add(f"Elbow{side}", taper(f"ForeFeather{side}{k}", (0.28, 0.16, ln), (x, p[1] - 0.2, p[2] - 0.05),
                                      C["cream"] if k == 0 else C["coat_l"], top=(0.65, 0.6), r=0.05,
                                      rot=(180 - 36, 0, 0)))
        add(f"Wrist{side}",
            orb(f"WristCap{side}", (0.175, 0.18, 0.15), wr, C["coat"], segs=10, rings=6),
            seg(f"Pastern{side}", wr, (x, pw[1] + 0.02, pw[2] - 0.02), (0.31, 0.32), C["coat_l"], r=0.09,
                overlap=0.04))
        paw(f"PawF{side}", x, pw[1] + 0.08)

        xb = s * X_B
        hp, kn, hk, pb = PIV[f"Hip{side}"], PIV[f"Knee{side}"], PIV[f"Hock{side}"], PIV[f"PawB{side}"]
        add(f"Hip{side}",
            seg(f"Thigh{side}", (xb, hp[1] - 0.04, hp[2] + 0.16), kn, (0.52, 0.8), C["coat"], r=0.2, segs=2,
                top=(0.78, 0.6), overlap=0.06),
            box(f"HaunchMuscle{side}", (0.2, 0.56, 0.5), (xb + s * 0.2, hp[1] + 0.02, hp[2] - 0.12), C["coat_l"],
                r=0.09, seg=2, rot=(-22, 0, 0)))
        for k, (dz, ln) in enumerate(((0.0, 0.4), (-0.3, 0.36))):  # "pants" feathering
            add(f"Hip{side}", taper(f"Pants{side}{k}", (0.36 - k * 0.04, 0.2, ln),
                                    (xb, hp[1] - 0.42 + k * 0.06, hp[2] - 0.12 + dz),
                                    C["cream"] if k == 0 else C["cream_l"], top=(0.65, 0.6), r=0.06,
                                    rot=(180 - 32, 0, 0)))
        add(f"Knee{side}",
            orb(f"KneeCap{side}", (0.23, 0.24, 0.22), kn, C["coat"], segs=10, rings=7),
            seg(f"Shin{side}", kn, hk, (0.35, 0.4), C["coat"], r=0.11, segs=2, top=(0.85, 0.85), overlap=0.04))
        add(f"Hock{side}",
            orb(f"HockCap{side}", (0.17, 0.19, 0.17), hk, C["coat"], segs=10, rings=6),
            seg(f"Metatarsus{side}", hk, (xb, pb[1] + 0.02, pb[2] - 0.02), (0.29, 0.31), C["coat_l"], r=0.09,
                overlap=0.04),
            taper(f"HockFeather{side}", (0.22, 0.14, 0.28), (xb, hk[1] - 0.16, hk[2] - 0.08), C["cream"],
                  top=(0.65, 0.6), r=0.05, rot=(180 - 40, 0, 0)))
        paw(f"PawB{side}", xb, pb[1] + 0.12)

    parts_before_join = sum(len(v) for v in P.values())
    arm, meshes = vc.build_rig(NAME, BONES, P, root_geo_size=(1.1, 3.0, 0.1))
    arm["vault_parts_before_join"] = parts_before_join
    arm["vault_asset"] = FILE
    return arm, meshes, parts_before_join


def _off(center, rot_deg, local):
    """center + R(rot) @ local — place pieces on rotated parents (collar hardware)."""
    from mathutils import Euler, Vector

    r = Euler(tuple(math.radians(a) for a in rot_deg)).to_matrix()
    return tuple(Vector(center) + r @ Vector(local))


def check(arm, meshes):
    rep = vc.check_rig(arm, meshes, REQUIRED_BONES, MAX_TRIS)
    # paws flat at rest: lowest point of every paw within 0.02 of the ground, nothing below ground
    for b in ("PawFL", "PawFR", "PawBL", "PawBR"):
        lo, _ = vc.world_bbox([meshes[b]])
        assert abs(lo.z) < 0.03, f"{b} not on ground (min z {lo.z:.3f})"
    body = [m for b, m in meshes.items() if b != "Root"]
    for name, pose in POSES.items():  # posed tests: nothing sinks into the floor, body rests near it
        vc.set_pose(arm, pose)
        lo, _ = vc.world_bbox(body)
        rep[f"pose_{name}_min_z"] = round(lo.z, 3)
        assert lo.z > -0.08, f"pose {name} sinks below ground ({lo.z:.3f})"
    vc.set_pose(arm, {})
    lo, hi = vc.world_bbox(body)
    rep["size_studs"] = tuple(round(v, 2) for v in (hi - lo))
    rep["head_top"] = round(hi.z, 2)
    return rep


def render(arm, meshes, out_dir=vc.PREVIEW_DIR, samples=24, which=("front", "side", "back", "34", "sit", "lie")):
    os.makedirs(out_dir, exist_ok=True)
    vc.setup_render(samples=samples)
    tgt = (0, 0.0, 1.55)
    shots = {
        "front": (0, 8), "side": (90, 6), "back": (180, 8), "34": (38, 12),
    }
    out = []
    for key in which:
        if key in shots:
            vc.set_pose(arm, {})
            yaw, pitch = shots[key]
            out.append(vc.shoot(os.path.join(out_dir, f"{FILE}_{key}.png"), vc.orbit(tgt, 11.5, yaw, pitch), tgt, lens=50))
        elif key in POSES:
            vc.set_pose(arm, POSES[key])
            out.append(vc.shoot(os.path.join(out_dir, f"{FILE}_{key}.png"), vc.orbit((0, 0, 1.3), 11, 62, 10),
                                (0, 0, 1.3), lens=50))
            out.append(vc.shoot(os.path.join(out_dir, f"{FILE}_{key}_side.png"), vc.orbit((0, 0, 1.3), 11, 90, 4),
                                (0, 0, 1.3), lens=50))
    vc.set_pose(arm, {})
    return out


def main(argv):
    arm, meshes, n = build()
    rep = check(arm, meshes)
    rep["parts_before_join"] = n
    fbx, glb = vc.export_rig(arm, os.path.join(vc.EXPORT_DIR, FILE))
    rep["fbx"], rep["glb"] = fbx, glb
    if "--render" in argv:
        only = [a.split("=", 1)[1] for a in argv if a.startswith("--only=")]
        rep["renders"] = render(arm, meshes, which=only[0].split(",") if only else
                                ("front", "side", "back", "34", "sit", "lie"))
    per = rep.pop("tris_per_part")
    print({k: v for k, v in rep.items()})
    print("tris per part:", per)
    return rep


if __name__ == "__main__":
    main(sys.argv[1:])
