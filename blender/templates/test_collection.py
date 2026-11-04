"""
Style test collection v3 (style-guides/3D_STYLE_BIBLE.md — DRAFT until the owner approves).

Owner feedback applied (L-20261104-04):
- Studs are part of the TEXTURE (UV stud tile + bump/normal), never physical geometry.
- Props/buildings are clean chunky SOLIDS with crisp edges — no stacked-brick seams (v2 "absolute no").
- The brainrot is chunky MERGED blocks (coarse voxels, no colour noise) with a real cartoon face.

Five ORIGINAL models (nothing copied from the references):
  1. Tree — cube-cluster canopy with slightly rotated clumps, tapered trunk with branches
  2. Rock — offset stone masses, moss cap, pebbles
  3. Building — "Smoothie Shack": framed two-floor shop, big glass, lit interior, awning, roof sign
  4. Conveyor machine — legs, steel frame, hazard guards, belt + rollers, hopper, processing box
  5. Brainrot collectible — "Frappo Froggini": smug frog bursting out of an iced-coffee cup, sneakers
Plus a 5-stud R6 dummy for scale and a studded (texture) baseplate.

Usage: python blender/templates/test_collection.py <out_dir>   (bpy module)
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import vault_blocky as vb  # noqa: E402

C = {
    "leaf": "#4CC24A", "leaf_dark": "#2E9A3E", "leaf_light": "#86E05A",
    "bark": "#8A5530", "bark_dark": "#6B3F22",
    "stone": "#8E96A3", "stone_dark": "#6E7683", "moss": "#5FC24A",
    "wall": "#FFF6EA", "frame": "#22C3A6", "frame_dark": "#159C85", "accent": "#FF6B6B",
    "glass": "#9BE1FF", "door": "#8A5A34", "sign": "#FFD93B", "light": "#FFE7B0",
    "steel": "#5B6B82", "steel_dark": "#3E4A5C", "belt": "#2B2F36", "belt_line": "#1E2126",
    "hazard": "#FFC21A", "black": "#1A1A1A", "machine": "#FF8A1F", "scan": "#3EF0FF",
    "ground": "#4FC33A", "pedestal": "#9AA3AF", "pad": "#36E05A",
}


def offset(objs, dx, dy, dz=0.0):
    for o in objs:
        if o.parent is None:
            o.location = (o.location[0] + dx, o.location[1] + dy, o.location[2] + dz)
    return objs


def S(*a, **k):
    return vb.solid(*a, **k)


# 1. Tree -------------------------------------------------------------------------------------
def tree():
    rnd = random.Random(11)
    P = [
        S("TrunkLow", (1.8, 1.8, 3.0), (0, 0, 0), C["bark"]),
        S("TrunkHigh", (1.3, 1.3, 4.6), (0.25, 0.1, 3.0), C["bark"]),
        S("RootA", (1.0, 0.8, 0.7), (1.2, 0.3, 0), C["bark_dark"]),
        S("RootB", (0.8, 1.0, 0.6), (-0.6, -1.2, 0), C["bark_dark"]),
        S("BranchA", (0.7, 0.7, 2.6), (1.3, 0.1, 4.6), C["bark"], rot=(0, math.radians(38), 0)),
        S("BranchB", (0.6, 0.6, 2.2), (-1.0, -0.3, 5.0), C["bark_dark"], rot=(math.radians(-15), math.radians(-35), 0)),
    ]
    clumps = (  # (x, y, z, size, colour) — a puffy cluster of cubes, rotated a little
        (0, 0, 7.0, 4.4, "leaf"), (2.6, 0.6, 6.6, 3.4, "leaf_dark"), (-2.5, -0.4, 7.0, 3.4, "leaf"),
        (0.4, 2.5, 6.8, 3.2, "leaf_dark"), (-0.3, -2.5, 6.9, 3.0, "leaf"), (1.2, 0.8, 9.6, 3.4, "leaf_light"),
        (-1.4, -0.6, 9.4, 3.0, "leaf"), (2.9, -1.9, 8.6, 2.4, "leaf_light"), (-2.6, 2.0, 8.4, 2.4, "leaf_light"),
        (0.1, 0.0, 11.6, 2.4, "leaf_light"), (3.6, 1.8, 5.8, 1.8, "leaf"), (-3.4, -2.2, 6.2, 1.8, "leaf_dark"),
    )
    for i, (x, y, z, s, col) in enumerate(clumps):
        rot = (math.radians(rnd.uniform(-8, 8)), math.radians(rnd.uniform(-8, 8)), math.radians(rnd.uniform(-20, 20)))
        P.append(S(f"Leaves{i}", (s, s, s * 0.85), (x, y, z), C[col], bevel=0.06, rot=rot))
    for i, (x, y, z) in enumerate(((3.9, -0.6, 7.4), (-3.2, 2.6, 7.6), (1.8, -3.0, 8.0))):
        P.append(vb.block(f"Fruit{i}", (0.7, 0.7, 0.7), (x, y, z), "#FF4D4D", bevel=0.18, segments=2))
    return P


# 2. Rock -------------------------------------------------------------------------------------
def rock():
    return [
        S("RockBase", (6, 4, 1.4), (0, 0, 0), C["stone_dark"]),
        S("RockMid", (4, 3, 1.3), (-0.5, 0.4, 1.4), C["stone"]),
        S("RockSide", (2.2, 2, 1.1), (2.1, -0.4, 1.4), C["stone_dark"]),
        S("RockTop", (2.2, 2, 1.1), (-0.9, 0.5, 2.7), C["stone"]),
        S("RockChunk", (1.8, 1.4, 1.0), (3.6, 1.4, 0), C["stone"]),
        S("Moss", (2.4, 2.2, 0.35), (-0.9, 0.5, 3.8), C["moss"]),
        S("MossLow", (2.0, 1.4, 0.3), (2.1, -0.4, 2.5), C["moss"]),
        S("Pebble0", (0.9, 0.9, 0.5), (-3.8, -1.5, 0), C["stone"]),
        S("Pebble1", (0.8, 0.8, 0.4), (4.4, -1.8, 0), C["stone_dark"]),
    ]


# 3. Building — "Smoothie Shack" --------------------------------------------------------------
def building():
    W, D, H1, H2 = 14, 10, 7.0, 6.0
    fy = D / 2  # front face
    P = [S("Plinth", (W + 3, D + 3, 0.6), (0, 0, 0), C["stone"])]
    z0 = 0.6
    # ground floor: solid wall panels around a big shop window + door
    P += [
        S("Back1", (W, 0.8, H1), (0, -D / 2 + 0.4, z0), C["wall"]),
        S("Left1", (0.8, D - 1.6, H1), (-W / 2 + 0.4, 0, z0), C["wall"]),
        S("Right1", (0.8, D - 1.6, H1), (W / 2 - 0.4, 0, z0), C["wall"]),
        S("FrontSill", (8.0, 0.8, 1.4), (-1.5, fy - 0.4, z0), C["wall"]),
        S("FrontLintel", (W, 0.8, 1.4), (0, fy - 0.4, z0 + H1 - 1.4), C["wall"]),
        S("FrontPierL", (1.5, 0.8, H1 - 1.4), (-W / 2 + 0.75, fy - 0.4, z0), C["wall"]),
        S("FrontPierM", (1.0, 0.8, H1 - 1.4), (3.0, fy - 0.4, z0), C["wall"]),
        S("FrontPierR", (1.0, 0.8, H1 - 1.4), (W / 2 - 0.5, fy - 0.4, z0), C["wall"]),
        S("ShopGlass", (8.0, 0.15, H1 - 2.8), (-1.5, fy - 0.45, z0 + 1.4), C["glass"], studs="none", bevel=0.01),
        S("Door", (2.5, 0.25, 4.6), (4.75, fy - 0.5, z0), C["door"]),
        S("DoorWindow", (1.4, 0.1, 1.2), (4.75, fy - 0.35, z0 + 2.9), C["glass"], studs="none", bevel=0.01),
        S("CounterLedge", (8.6, 1.4, 0.35), (-1.5, fy + 0.3, z0 + 1.4), C["frame"]),
    ]
    P.append(vb.block("InteriorLight1", (11, 7, 0.15), (0, 0, z0 + H1 - 0.3), C["light"], bevel=0.0, emission=3.5))
    # awning over the shop window (alternating stripes, tilted)
    for i in range(8):
        a = S(f"Awning{i}", (1.08, 2.4, 0.22), (-5.6 + i * 1.1, fy + 1.0, z0 + H1 - 1.6),
              C["accent"] if i % 2 == 0 else "#FFFFFF", bevel=0.02, rot=(math.radians(-22), 0, 0))
        P.append(a)
    # chunky frame: corner pillars + floor beam band
    for i, (x, y) in enumerate(((-W / 2, fy), (W / 2, fy), (-W / 2, -D / 2), (W / 2, -D / 2))):
        P.append(S(f"Pillar{i}", (1.6, 1.6, H1 + H2 + 1.0), (x, y, z0), C["frame"]))
    P += [
        S("BeamFront", (W, 1.4, 1.0), (0, fy, z0 + H1), C["frame"]),
        S("BeamBack", (W, 1.4, 1.0), (0, -D / 2, z0 + H1), C["frame"]),
        S("BeamL", (1.4, D, 1.0), (-W / 2, 0, z0 + H1), C["frame"]),
        S("BeamR", (1.4, D, 1.0), (W / 2, 0, z0 + H1), C["frame"]),
    ]
    # upper floor
    z1 = z0 + H1 + 1.0
    P += [
        S("Back2", (W, 0.8, H2), (0, -D / 2 + 0.4, z1), C["wall"]),
        S("Left2", (0.8, D - 1.6, H2), (-W / 2 + 0.4, 0, z1), C["wall"]),
        S("Right2", (0.8, D - 1.6, H2), (W / 2 - 0.4, 0, z1), C["wall"]),
        S("Front2Low", (W, 0.8, 1.2), (0, fy - 0.4, z1), C["wall"]),
        S("Front2High", (W, 0.8, 1.2), (0, fy - 0.4, z1 + H2 - 1.2), C["wall"]),
        S("Front2L", (3.0, 0.8, H2 - 2.4), (-W / 2 + 1.5, fy - 0.4, z1 + 1.2), C["wall"]),
        S("Front2R", (3.0, 0.8, H2 - 2.4), (W / 2 - 1.5, fy - 0.4, z1 + 1.2), C["wall"]),
        S("UpperGlass", (8.0, 0.15, H2 - 2.4), (0, fy - 0.45, z1 + 1.2), C["glass"], studs="none", bevel=0.01),
        S("UpperSill", (8.8, 1.2, 0.3), (0, fy + 0.1, z1 + 1.2), C["frame_dark"]),
        S("Mullion", (0.3, 0.2, H2 - 2.4), (0, fy - 0.3, z1 + 1.2), "#FFFFFF"),
    ]
    P.append(vb.block("InteriorLight2", (11, 7, 0.15), (0, 0, z1 + H2 - 0.3), C["light"], bevel=0.0, emission=3.0))
    # roof + sign + rooftop cup
    zr = z1 + H2
    P += [
        S("Roof", (W + 2.6, D + 2.6, 0.9), (0, 0, zr), C["accent"]),
        S("RoofTrim", (W + 3.0, D + 3.0, 0.3), (0, 0, zr - 0.3), "#FFFFFF"),
        S("SignBack", (10, 0.6, 2.6), (0, fy + 0.6, zr + 0.9), C["accent"]),
        S("SignFace", (9.2, 0.15, 2.0), (0, fy + 0.95, zr + 1.2), C["sign"], bevel=0.01),
        S("CupBody", (2.6, 2.6, 3.0), (-3.8, -1.5, zr + 0.9), "#FF6FAE", bevel=0.1),
        S("CupBand", (2.8, 2.8, 0.7), (-3.8, -1.5, zr + 2.0), "#FFFFFF"),
        S("CupLid", (3.2, 3.2, 0.5), (-3.8, -1.5, zr + 3.9), "#FFFFFF"),
        S("CupDome", (2.0, 2.0, 0.6), (-3.8, -1.5, zr + 4.4), "#FFFFFF", bevel=0.2),
        S("Straw", (0.5, 0.5, 2.8), (-3.4, -1.3, zr + 4.6), C["accent"], rot=(0, math.radians(18), 0)),
    ]
    # planters by the door
    for i, x in enumerate((2.0, 7.6)):
        P.append(S(f"Planter{i}", (1.2, 1.2, 0.9), (x, fy + 1.4, z0), C["frame_dark"]))
        P.append(S(f"Bush{i}", (1.1, 1.1, 1.0), (x, fy + 1.4, z0 + 0.9), C["leaf"], rot=(0, 0, math.radians(20))))
    return P


# 4. Conveyor machine --------------------------------------------------------------------------
def conveyor():
    L, Wd, zt = 14, 3.4, 2.6
    P = []
    for i, x in enumerate((-6.2, -1.5, 3.0)):
        for j, y in enumerate((-1.3, 1.3)):
            P.append(S(f"Leg{i}{j}", (0.7, 0.7, zt - 0.8), (x, y, 0), C["steel_dark"]))
        P.append(S(f"Brace{i}", (0.4, 2.6, 0.4), (x, 0, 0.6), C["steel_dark"]))
    P.append(S("Frame", (L, Wd, 0.8), (0, 0, zt - 0.8), C["steel"]))
    P.append(S("Belt", (L - 0.4, Wd - 0.9, 0.2), (0, 0, zt), C["belt"], bevel=0.01))
    for i in range(13):
        P.append(vb.block(f"BeltLine{i}", (0.08, Wd - 0.95, 0.02), (-6.0 + i * 1.0, 0, zt + 0.2), C["belt_line"], bevel=0.0))
    for side in (-1, 1):
        P.append(S(f"Guard{side}", (L, 0.35, 0.8), (0, side * (Wd / 2 - 0.1), zt), C["hazard"]))
        for i in range(7):  # diagonal hazard stripes on the guard face
            P.append(vb.block(f"Stripe{side}_{i}", (0.35, 0.05, 1.0), (-6.0 + i * 2.0, side * (Wd / 2 + 0.08), zt - 0.1),
                              C["black"], bevel=0.0))
            P[-1].rotation_euler = (0, math.radians(35), 0)
    for i, x in enumerate((-L / 2, L / 2 - 4.2)):
        r = vb.cylinder(f"Roller{i}", 0.45, Wd - 0.6, (x, (Wd - 0.6) / 2, zt - 0.35), C["steel_dark"], sides=14)
        r.rotation_euler[0] = math.pi / 2
        P.append(r)
    # hopper at the start
    P.append(S("HopperLow", (2.4, 2.4, 1.0), (-5.6, 0, zt + 0.2), C["machine"]))
    P.append(S("HopperTop", (3.4, 3.4, 1.0), (-5.6, 0, zt + 1.2), C["machine"]))
    P.append(vb.block("HopperHole", (2.6, 2.6, 0.05), (-5.6, 0, zt + 2.2), C["black"], bevel=0.0))
    # processing box at the end
    bx = L / 2 - 2.1
    P += [
        S("Machine", (4.2, Wd + 1.2, 3.8), (bx, 0, zt - 0.8), C["machine"]),
        S("MachineTop", (3.4, Wd + 0.4, 0.6), (bx, 0, zt + 3.0), C["steel"]),
        S("Tunnel", (0.2, Wd - 1.0, 1.4), (bx - 2.12, 0, zt), C["black"], bevel=0.0),
        S("Pipe0", (0.6, 0.6, 1.6), (bx + 0.8, -1.0, zt + 3.6), C["steel_dark"]),
        S("Pipe1", (0.6, 0.6, 1.1), (bx - 0.5, 1.1, zt + 3.6), C["steel_dark"]),
    ]
    P.append(vb.block("MachineWindow", (2.4, 0.1, 1.4), (bx, Wd / 2 + 0.65, zt + 0.9), C["scan"], bevel=0.0, emission=4))
    P.append(vb.block("WarnLight", (0.7, 0.7, 0.5), (bx + 1.2, 1.2, zt + 3.6), "#FF3B3B", bevel=0.15, segments=2, emission=5))
    # crates riding the belt
    for i, (x, col) in enumerate(((-2.8, "#B678EA"), (0.8, "#2590D1"))):
        P.append(S(f"Crate{i}", (1.3, 1.3, 1.3), (x, 0, zt + 0.2), col))
    return P


# 5. Brainrot collectible — "Frappo Froggini" v3 ------------------------------------------------
def frappo():
    """Chunky MERGED blocks (fine design -> downsampled to 0.5-stud blocks, no colour noise)
    plus a clean cartoon face built from crisp pieces on the head front."""
    V = vb.VoxelCanvas()
    G, GL = "#4FD13A", "#B8F07A"
    CUP, SLEEVE, LID = "#F7F4EC", "#B5743A", "#4A2E1A"
    WHITE, RED, SOLE = "#FFFFFF", "#FF3B3B", "#2E3440"
    for sx in (-1, 1):  # sneakers
        x0, x1 = (2, 7) if sx > 0 else (-8, -3)
        V.box(x0, x1, -3, 5, 0, 1, SOLE)
        V.box(x0, x1, -3, 5, 2, 3, WHITE)
        V.box(x0, x1, 4, 5, 2, 3, RED)
        V.box(x0 + 1, x1 - 1, -1, 1, 4, 5, G)
    V.cylinder(0, 0, 6, 17, 5.5, 6.5, CUP)
    V.paint(lambda x, y, z: 10 <= z <= 13, SLEEVE)
    V.cylinder(0, 0, 18, 19, 7.0, 7.0, LID)
    V.ellipsoid(0, 0.5, 26.5, 11, 8.5, 8.0, G)
    V.paint(lambda x, y, z: z <= 23 and y >= 2 and V.v.get((x, y, z)) == G, GL)
    for sx in (-1, 1):
        V.ellipsoid(sx * 5, 1.5, 33, 3.8, 3.4, 3.6, G)
    for i in range(24):  # thick striped straw
        x, y, z = 6 + i // 6, -6, 18 + i
        for dx in (0, 1):
            for dy in (0, 1):
                V.v[(x + dx, y + dy, z)] = RED if (i // 4) % 2 == 0 else WHITE
    V.box(7, 9, -1, 1, 11, 14, G)  # thumbs-up arm
    V.box(8, 10, -1, 1, 15, 18, G)
    V.box(8, 11, -1, 1, 19, 21, GL)
    V.box(10, 11, -1, 0, 22, 24, GL)
    V.box(-9, -7, -1, 1, 11, 14, G)  # resting arm
    V.box(-10, -7, 0, 3, 10, 11, GL)
    coarse = V.downsample(2, min_fill=3)
    vs = 0.5
    body = vb.voxel_mesh("Frappo_Body", coarse.v, voxel=vs, jitter=0.0, seed=3)
    P = [body]

    def face_y(x_studs, z_studs, half_w=0.0):
        """Front surface (studs) of the merged head at an x/z, max across the feature width."""
        best = None
        for xx in (x_studs - half_w, x_studs, x_studs + half_w):
            fy = coarse.front_y(int(math.floor(xx / vs)), int(math.floor(z_studs / vs)))
            if fy is not None:
                best = max(best, (fy + 1) * vs) if best is not None else (fy + 1) * vs
        return best if best is not None else 2.0

    def feat(name, size, x, z, col, dy=0.0, emission=0.0, rot=None):
        y = face_y(x, z + size[2] / 2, size[0] / 2) + size[1] / 2 - 0.02 + dy
        o = vb.block(name, size, (x, y, z), col, bevel=0.03, segments=1, emission=emission)
        if rot:
            o.rotation_euler = rot
        P.append(o)
        return o

    for sx, side in ((-1, "L"), (1, "R")):  # big eyes on the eye domes, smug half-lids
        ex = sx * 1.25
        feat(f"Eye{side}", (1.5, 0.16, 1.5), ex, 7.55, WHITE)
        feat(f"Pupil{side}", (0.62, 0.14, 0.8), ex - sx * 0.25, 7.7, "#141414", dy=0.08)
        feat(f"Sparkle{side}", (0.24, 0.1, 0.24), ex - sx * 0.05, 8.25, WHITE, dy=0.16, emission=1.0)
        feat(f"Lid{side}", (1.62, 0.2, 0.5), ex, 8.6, "#2F9A22", dy=0.1, rot=(0, math.radians(sx * -8), 0))
        feat(f"Blush{side}", (0.7, 0.12, 0.32), sx * 2.15, 6.05, "#FF8FB1")
    feat("Mouth", (3.0, 0.16, 0.9), 0.2, 4.95, "#141414", rot=(0, math.radians(-6), 0))  # open smirk
    feat("Tongue", (1.3, 0.14, 0.42), -0.2, 5.0, "#FF6F9B", dy=0.06)
    feat("Emblem", (0.7, 0.12, 0.7), 0.0, 2.75, G)  # leaf logo on the cup sleeve
    for i in range(6):  # glow sparkles
        a = 2 * math.pi * i / 6
        P.append(vb.block(f"Glow{i}", (0.35, 0.35, 0.35), (math.cos(a) * 3.8, math.sin(a) * 3.8, 2.0 + (i % 3) * 1.5),
                          "#FFD93B", bevel=0.0, emission=4))
    return P


def pedestal():
    return [
        S("Pedestal", (6, 6, 1.0), (0, 0, 0), C["pedestal"]),
        S("PedestalTop", (5.2, 5.2, 0.4), (0, 0, 1.0), C["pedestal"]),
        vb.block("CollectPad", (6.4, 1.2, 0.12), (0, 3.8, 0), C["pad"], bevel=0.0, emission=1.2),
    ]


def r6_dummy():
    g, gd = "#C8CCD2", "#A3A9B1"
    return [
        vb.block("Dummy_LegL", (1, 1, 2), (-0.5, 0, 0), gd, bevel=0.05),
        vb.block("Dummy_LegR", (1, 1, 2), (0.5, 0, 0), gd, bevel=0.05),
        vb.block("Dummy_Torso", (2, 1, 2), (0, 0, 2), g, bevel=0.05),
        vb.block("Dummy_ArmL", (1, 1, 2), (-1.5, 0, 2), gd, bevel=0.05),
        vb.block("Dummy_ArmR", (1, 1, 2), (1.5, 0, 2), gd, bevel=0.05),
        vb.block("Dummy_Head", (1.2, 1.2, 1.0), (0, 0, 4), g, bevel=0.2, segments=2),
    ]  # 5 studs tall = Roblox R6 character


def build_all():
    vb.reset_scene()
    vb.ensure_stud_textures()
    fr = frappo()
    for o in fr:  # stand on the pedestal top
        o.location = (o.location[0], o.location[1], o.location[2] + 1.4)
    groups = {  # every model's FRONT faces +y; review cameras look from +y
        "Tree": offset(tree(), -13, -5),
        "Rock": offset(rock(), -12, 8),
        "Building": offset(building(), 5, -9),
        "Conveyor": offset(conveyor(), 5, 7),
        "Brainrot": offset(pedestal() + fr, 20, 2),
        "Dummy": offset(r6_dummy(), -4, 3),
    }
    ground = vb.block("Baseplate", (56, 36, 1), (3, 0, -1), C["ground"], bevel=0.0)
    vb.stud_surface(ground, "all")
    return groups, [ground]


def main(out_dir):
    groups, _ = build_all()
    os.makedirs(out_dir, exist_ok=True)
    return {name: vb.poly_report(objs) for name, objs in groups.items()}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    for k, v in main(argv[0] if argv else "out").items():
        print(k, v)
