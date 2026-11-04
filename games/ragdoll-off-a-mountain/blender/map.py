"""
Ragdoll Off a Mountain — full MAP (Bone Zone valley + 5-peak stepped massif + base rim).

    python3 games/ragdoll-off-a-mountain/blender/map.py [out_dir]
        default out_dir = games/ragdoll-off-a-mountain/assets/export/map

World axes (Blender): X east, Y north, Z up, 1 unit = 1 stud. Mountain to the north, valley around (0,-60),
base camps on the south rim facing +Y. Roblox: (X, Y, Z)_roblox = (x, z, -y) (verify on first import).

Built ONLY from vault_blocky / vault_kit techniques (solid, rounded, cyl, ball, canopy, path_network, vignettes,
shades). Everything here is an original design for this game (handoff: blender/handoff-map.md).
Export: one mesh per colour group per chunk (= one MeshPart per colour in Roblox), split so every mesh
stays <= 14k tris. layout.json carries every gameplay marker.
"""

from __future__ import annotations

import bisect
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path[:0] = [os.path.join(ROOT, "blender", "lib")]

import bpy  # noqa: E402  (bpy must load before bmesh)
import bmesh  # noqa: E402

import vault_blocky as vb  # noqa: E402
import vault_kit as kit  # noqa: E402

# ------------------------------------------------------------------------------------------------
# Palette (handoff-map.md). Neon colours are NEVER reused as non-neon (materials are cached by hex).
# ------------------------------------------------------------------------------------------------
GRASS, GRASS_D, GRASS_L = "#4CC24A", "#2E9A3E", "#86E05A"
STONE, STONE_D, STONE_L = "#8E96A3", "#6E7683", "#B3BAC4"
DIRT, DIRT_D = "#9A6B45", "#7A5236"
SNOW, SNOW_D = "#F4FBFF", "#D9ECF7"
CREAM, GOLD, HAZ, BLACK = "#FFF1CF", "#FFD93B", "#FFC21A", "#1A1A1A"
ORANGE = "#F57C1F"  # non-neon SNAP orange (paint)
WOOD, WOOD_D, WOOD_L = "#B5733A", "#8A5530", "#CD8C52"
WATER, WATER_D = "#3EC6FF", "#2A9BE0"
NAVY, WHITE, RED, RED_D = "#1E1B33", "#F5F5F5", "#E13A2A", "#B6261D"
BLUE, BLUE_D, TEAL, PINK = "#2590D1", "#1C6FA8", "#22C3A6", "#FF5FA2"
PINE, PINE_L = "#1F7A3A", "#2E9A3E"
ICE, ICE_D, ICE_GLASS = "#8FE3FF", "#5CC8F0", "#C4F4FF"
BSTONE, BSTONE_D, BSTONE_L = "#7E9CB8", "#6A86A3", "#9BB6CE"  # frost blue stone
BASALT, BASALT_D, BASALT_L, ASH = "#3B3540", "#2A2530", "#544B5C", "#6A5F6E"
SLATE, SLATE_D, SLATE_L, LAVSNOW = "#5A5478", "#433E5E", "#7A73A0", "#EEE8FF"
CRYSTAL, CRYSTAL_D, CRYSTAL_L = "#B678EA", "#8E4FE0", "#D9B3FF"
CLOUD, CLOUD_D = "#FFFFFF", "#E3E8F5"
HAY, HAY_D = "#F2C94C", "#D9A930"
STEEL, STEEL_D = "#5B6B82", "#3B4554"
# neon (emissive) — only ever used with emission
N_ORANGE, N_LAVA, N_LAVAY, N_CYAN, N_LAMP, N_GOLD = "#FF8A1F", "#FF5A14", "#FFC83A", "#3EF0FF", "#FFE7A8", "#FFE45C"

FOOT_Y = 100.0  # mountain foot line
CH_HW = 18.0  # half width of each fall-line channel
HUB = (0.0, -92.0)
R_PLAZA, R_MOAT, R_PROM = 48.0, 60.0, 78.0
STREAM_X0, STREAM_X1 = 40.0, 50.0
BASES = [(-200, -185), (-120, -204), (-40, -216), (40, -216), (120, -204), (200, -185)]
BASE_TOP = 5.0
RIM_Z = 4.0

PEAKS = [
    dict(n=1, name="PebbleHill", x=-160.0, z=120.0, riser=(1.5, 3.4), slope=(48, 62), every=(4, 6), ledge=(5, 7.5),
         accent=GOLD, flag=GOLD, dom=(-290.0, -120.0)),
    dict(n=2, name="PineRidge", x=-80.0, z=260.0, riser=(2.0, 4.6), slope=(48, 62), every=(4, 6), ledge=(5.5, 8),
         accent=PINE_L, flag=GRASS_D, dom=(-120.0, -40.0)),
    dict(n=3, name="FrostbiteCliffs", x=0.0, z=420.0, riser=(2.5, 5.5), slope=(50, 64), every=(4, 7), ledge=(6, 9),
         accent=ICE_D, flag=ICE_D, dom=(-40.0, 40.0)),
    dict(n=4, name="MagmaSpire", x=80.0, z=620.0, riser=(3.0, 6.0), slope=(52, 64), every=(4, 7), ledge=(6, 9),
         accent=ORANGE, flag=RED, dom=(40.0, 120.0)),
    dict(n=5, name="StormcrownSummit", x=160.0, z=880.0, riser=(3.0, 6.0), slope=(52, 64), every=(4, 7), ledge=(6, 9.5),
         accent=CRYSTAL_D, flag=CRYSTAL_D, dom=(120.0, 300.0)),
]

# ------------------------------------------------------------------------------------------------
# Registry + primitive wrappers
# ------------------------------------------------------------------------------------------------
CH: dict[str, list] = {}
CUR = ["Map_BoneZone"]
MARK: list[dict] = []
_N = [0]


def nm(p):
    _N[0] += 1
    return f"{p}_{_N[0]}"


def chunk(name):
    CUR[0] = name
    CH.setdefault(name, [])


def reg(o):
    if isinstance(o, (list, tuple)):
        CH[CUR[0]].extend(o)
        return list(o)
    CH[CUR[0]].append(o)
    return o


def S(p, size, loc, col, bevel=0.04, studs="all", em=0.0, rot=None):
    return reg(vb.solid(nm(p), size, loc, col, bevel=bevel, studs=studs, emission=em, rot=rot))


def R(p, size, loc, col, radius=0.3, studs="all", em=0.0, rot=None):
    return reg(vb.rounded(nm(p), size, loc, col, radius=radius, studs=studs, emission=em, rot=rot))


def C(p, r1, r2, h, loc, col, sides=12, studs="all", rot=None, em=0.0):
    return reg(vb.cyl(nm(p), r1, r2, h, loc, col, sides=sides, studs=studs, rot=rot, emission=em))


def B(p, radii, c, col, seg=10, rings=6, studs="all", em=0.0, rot=None):
    return reg(vb.ball(nm(p), radii, c, col, segments=seg, rings=rings, studs=studs, emission=em, rot=rot))


def SPAN(p, x0, x1, y0, y1, z0, z1, col, **kw):
    return S(p, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, z0), col, **kw)


def RING(p, r_in, r_out, h, loc, col, sides=24, studs="all", em=0.0, a0=0.0, a1=2 * math.pi):
    """Annulus prism (bottom at loc z). Partial arcs get end caps."""
    bm = bmesh.new()
    full = abs(a1 - a0 - 2 * math.pi) < 1e-6
    n = sides
    cols = []
    for k in range(n + (0 if full else 1)):
        a = a0 + (a1 - a0) * k / n
        c, s = math.cos(a), math.sin(a)
        cols.append([bm.verts.new((r_in * c, r_in * s, 0)), bm.verts.new((r_out * c, r_out * s, 0)),
                     bm.verts.new((r_out * c, r_out * s, h)), bm.verts.new((r_in * c, r_in * s, h))])
    m = len(cols)
    for k in range(n):
        a, b = cols[k], cols[(k + 1) % m]
        bm.faces.new((a[3], a[2], b[2], b[3]))  # top
        bm.faces.new((a[0], b[0], b[1], a[1]))  # bottom
        bm.faces.new((a[1], b[1], b[2], a[2]))  # outer
        bm.faces.new((a[0], a[3], b[3], b[0]))  # inner
    if not full:
        a, b = cols[0], cols[-1]
        bm.faces.new((a[0], a[1], a[2], a[3]))
        bm.faces.new((b[3], b[2], b[1], b[0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = vb._new_mesh_object(nm(p), bm)
    obj.location = loc
    return reg(vb._finish(obj, col, em, studs, None))


def BAR(p, a, b, th, col, studs="all", em=0.0, th2=None):
    """Square-section beam from point a to point b (logs, rails, poles, crutches)."""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    L = math.sqrt(dx * dx + dy * dy + dz * dz)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    t2 = th2 or th
    for v in bm.verts:
        v.co.x *= L
        v.co.y *= th
        v.co.z *= t2
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(0.04, th * 0.2), segments=1, affect="EDGES")
    obj = vb._new_mesh_object(nm(p), bm)
    obj.location = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(dz, math.hypot(dx, dy))
    return reg(vb._finish(obj, col, em, studs, (0, -pitch, yaw)))


def mark(name, pos, rot=0.0, size=None, **extra):
    m = {"name": name, "position": [round(pos[0], 2), round(pos[1], 2), round(pos[2], 2)], "rotationY": round(rot, 1)}
    if size:
        m["size"] = [round(s, 2) for s in size]
    m.update(extra)
    MARK.append(m)


# ------------------------------------------------------------------------------------------------
# Block-pixel lettering (physical sign geometry, bible §0.9)
# ------------------------------------------------------------------------------------------------
GLYPH = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "001", "010", "010"],
    "8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
    "B": ["110", "101", "110", "101", "110"], "O": ["111", "101", "101", "101", "111"],
    "N": ["1001", "1101", "1011", "1001", "1001"], "E": ["111", "100", "110", "100", "111"],
    "Z": ["111", "001", "010", "100", "111"], "L": ["100", "100", "100", "100", "111"],
    "I": ["111", "010", "010", "010", "111"], "F": ["111", "100", "110", "100", "100"],
    "T": ["111", "010", "010", "010", "010"], "P": ["110", "101", "110", "100", "100"],
    "K": ["101", "101", "110", "101", "101"], "A": ["010", "101", "111", "101", "101"],
    "H": ["101", "101", "111", "101", "101"], "G": ["111", "100", "101", "101", "111"],
    "S": ["111", "100", "111", "001", "111"], "!": ["1", "1", "1", "0", "1"], " ": ["00", "00", "00", "00", "00"],
    "^": ["010", "111", "101", "000", "000"], "Y": ["101", "101", "010", "010", "010"],
    "$": ["011", "110", "111", "011", "110"], "+": ["000", "010", "111", "010", "000"],
}


def text_width(s, px):
    return sum((len(GLYPH[c][0]) + 1) * px for c in s) - px


def pixtext(p, s, x, y, z, px, col, face="-y", depth=0.3, em=0.0):
    """Chunky block letters centred on x, bottom at z, protruding from a sign face at y (facing -y or +y)."""
    w = text_width(s, px)
    sgn = -1 if face == "-y" else 1
    cx = x - w / 2 if face == "-y" else x + w / 2
    out = []
    for c in s:
        g = GLYPH[c]
        gw = len(g[0])
        for r, row in enumerate(g):
            k = 0
            while k < gw:
                if row[k] == "1":
                    j = k
                    while j + 1 < gw and row[j + 1] == "1":
                        j += 1
                    run = (j - k + 1) * px
                    gx = cx + sgn * -1 * 0 + (k * px + run / 2) * (1 if face == "-y" else -1)
                    out.append(S(p, (run, depth, px), (gx, y + sgn * depth / 2, z + (4 - r) * px), col, bevel=0.03,
                                 em=em, studs="none" if em else "all"))
                    k = j + 1
                else:
                    k += 1
        cx += (gw + 1) * px * (1 if face == "-y" else -1)
    return out


def sign_board(p, x, y, z, w, h, board, frame, text=None, tcol=NAVY, px=0.5, face="-y", posts=2, post_col=WOOD_D,
               lift=1.4):
    """Post-mounted board with a raised frame and block text; front faces `face`."""
    sgn = -1 if face == "-y" else 1
    if posts == 2:
        for dx in (-w / 2 + 0.6, w / 2 - 0.6):
            S(p + "Post", (0.7, 0.7, lift + h + 0.4), (x + dx, y - sgn * 0.6, z), post_col)
    elif posts == 1:
        S(p + "Post", (0.8, 0.8, lift + h + 0.6), (x, y - sgn * 0.6, z), post_col)
    bz = z + (lift if posts else 0.0)
    S(p + "Board", (w, 0.5, h), (x, y, bz), board)
    S(p + "FrameT", (w + 0.5, 0.7, 0.4), (x, y, bz + h), frame)
    S(p + "FrameB", (w + 0.5, 0.7, 0.4), (x, y, bz - 0.4), frame)
    S(p + "FrameL", (0.4, 0.7, h), (x - w / 2 - 0.05, y, bz), frame)
    S(p + "FrameR", (0.4, 0.7, h), (x + w / 2 + 0.05, y, bz), frame)
    if text:
        th = 5 * px
        pixtext(p + "Txt", text, x, y + sgn * 0.25, bz + (h - th) / 2, px, tcol, face=face)


# ------------------------------------------------------------------------------------------------
# Reusable organic pieces (originals for this map; built with kit techniques)
# ------------------------------------------------------------------------------------------------
def rock_cluster(p, x, y, z, s, cols, rnd, n=3, cap=None):
    out = []
    for i in range(n):
        k = 1.0 if i == 0 else rnd.uniform(0.45, 0.7)
        ox = 0 if i == 0 else rnd.uniform(-0.9, 0.9) * s
        oy = 0 if i == 0 else rnd.uniform(-0.6, 0.6) * s
        sz = (s * k * rnd.uniform(1.0, 1.3), s * k * rnd.uniform(0.8, 1.1), s * k * rnd.uniform(0.65, 0.9))
        out.append(S(p + "Rock", sz, (x + ox, y + oy, z - 0.2), cols[i % len(cols)], bevel=0.12,
                     rot=(math.radians(rnd.uniform(-8, 8)), math.radians(rnd.uniform(-8, 8)), rnd.uniform(0, 1.5))))
        if cap and i == 0:
            out.append(S(p + "RockCap", (sz[0] * 0.75, sz[1] * 0.7, 0.35), (x + ox, y + oy, z - 0.2 + sz[2] - 0.05),
                         cap, bevel=0.08, rot=(0, 0, rnd.uniform(0, 1.5))))
    return out


def pine(p, x, y, z, h, rnd, snow=False, hero=False, leaf=PINE):
    """Angular-cluster pine: trunk + stacked tiers. hero=True uses kit.canopy clusters per tier."""
    out = [S(p + "Trunk", (h * 0.09, h * 0.09, h * 0.32), (x, y, z), WOOD_D, bevel=0.06)]
    tiers = 3 if hero else 4
    for t in range(tiers):
        f = 1 - t / (tiers + 0.6)
        tz = z + h * (0.2 + 0.2 * t)
        if hero:
            out += reg(kit.canopy(nm(p + "Can"), (x, y, tz), radius=h * 0.3 * f, height=h * 0.2, clusters=4, leaf=leaf,
                                  rnd=rnd))
        else:
            s = h * 0.58 * f
            out.append(S(p + "Tier", (s, s, h * 0.2), (x + rnd.uniform(-0.2, 0.2), y + rnd.uniform(-0.2, 0.2), tz),
                         leaf if t % 2 == 0 else PINE_L, bevel=0.1,
                         rot=(math.radians(rnd.uniform(-6, 6)), math.radians(rnd.uniform(-6, 6)), rnd.uniform(0, 1.5))))
            if snow:
                out.append(S(p + "Snow", (s * 0.62, s * 0.62, 0.45), (x, y, tz + h * 0.2 - 0.05), SNOW, bevel=0.1,
                             rot=(0, 0, rnd.uniform(0, 1.5))))
    out.append(S(p + "Tip", (h * 0.13, h * 0.13, h * 0.16), (x, y, z + h * (0.2 + 0.2 * tiers) - 0.1),
                 SNOW if snow else PINE_L, bevel=0.08, rot=(0, 0, 0.7)))
    return out


def round_tree(p, x, y, z, h, rnd, leaf=GRASS, fruit=None):
    out = [S(p + "Trunk", (1.3, 1.3, h * 0.45), (x, y, z), WOOD_D, bevel=0.08),
           S(p + "Root", (2.2, 1.0, 0.6), (x, y, z), WOOD_D, rot=(0, 0, rnd.uniform(0, 3)))]
    out += reg(kit.canopy(nm(p + "Can"), (x, y, z + h * 0.42), radius=h * 0.36, height=h * 0.42, clusters=10, leaf=leaf,
                          rnd=rnd, fruit=fruit))
    return out


def flower_patch(p, x, y, z, rnd, cols=(GOLD, WHITE), n=6, r=1.6):
    out = [S(p + "Tuft", (r * 1.6, r * 1.3, 0.4), (x, y, z - 0.1), GRASS_L, bevel=0.1, rot=(0, 0, rnd.uniform(0, 2)))]
    for i in range(n):
        a = rnd.uniform(0, 6.28)
        rr = rnd.uniform(0.2, r * 0.8)
        fx, fy = x + math.cos(a) * rr, y + math.sin(a) * rr
        hh = rnd.uniform(0.5, 1.0)
        out.append(S(p + "Stem", (0.16, 0.16, hh), (fx, fy, z + 0.25), GRASS_D, bevel=0.02))
        out.append(S(p + "Bloom", (0.55, 0.55, 0.36), (fx, fy, z + 0.25 + hh), cols[i % len(cols)], bevel=0.08,
                     rot=(0, 0, rnd.uniform(0, 0.8))))
    return out


def fence_run(p, x0, x1, y, z, col=WOOD, post=WOOD_D, h=2.6, step=3.0):
    out = []
    n = max(1, int(round(abs(x1 - x0) / step)))
    for i in range(n + 1):
        px = x0 + (x1 - x0) * i / n
        out.append(S(p + "Post", (0.55, 0.55, h), (px, y, z), post))
        out.append(S(p + "PostCap", (0.75, 0.75, 0.25), (px, y, z + h), post))
    L = abs(x1 - x0)
    out.append(S(p + "RailT", (L, 0.3, 0.45), ((x0 + x1) / 2, y + 0.05, z + h * 0.72), col))
    out.append(S(p + "RailB", (L, 0.3, 0.45), ((x0 + x1) / 2, y + 0.05, z + h * 0.32), col))
    return out


def fence_run_y(p, x, y0, y1, z, col=WOOD, post=WOOD_D, h=2.6, step=3.0):
    out = []
    n = max(1, int(round(abs(y1 - y0) / step)))
    for i in range(n + 1):
        py = y0 + (y1 - y0) * i / n
        out.append(S(p + "Post", (0.55, 0.55, h), (x, py, z), post))
        out.append(S(p + "PostCap", (0.75, 0.75, 0.25), (x, py, z + h), post))
    L = abs(y1 - y0)
    out.append(S(p + "RailT", (0.3, L, 0.45), (x + 0.05, (y0 + y1) / 2, z + h * 0.72), col))
    out.append(S(p + "RailB", (0.3, L, 0.45), (x + 0.05, (y0 + y1) / 2, z + h * 0.32), col))
    return out


def warn_sign(p, x, y, z, col=HAZ, icon=BLACK):
    """Yellow diamond on a post with a block '!' — faces south (-y)."""
    out = [S(p + "Post", (0.5, 0.5, 4.2), (x, y + 0.4, z), STEEL_D)]
    out.append(S(p + "Diamond", (2.6, 0.35, 2.6), (x, y, z + 3.0), col, rot=(0, math.radians(45), 0)))
    out.append(S(p + "Rim", (3.0, 0.25, 3.0), (x, y + 0.25, z + 2.85), BLACK, rot=(0, math.radians(45), 0)))
    out.append(S(p + "Bang", (0.4, 0.2, 1.1), (x, y - 0.25, z + 4.25), icon, bevel=0.02))
    out.append(S(p + "Dot", (0.4, 0.2, 0.4), (x, y - 0.25, z + 3.65), icon, bevel=0.02))
    return out


def slalom_pole(p, x, y, z, col, h=5.5):
    return [S(p + "PoleA", (0.55, 0.55, h * 0.5), (x, y, z), col, bevel=0.05),
            S(p + "PoleB", (0.55, 0.55, h * 0.5), (x, y, z + h * 0.5), WHITE, bevel=0.05),
            S(p + "PoleTip", (0.8, 0.8, 0.6), (x, y, z + h), col, bevel=0.1),
            S(p + "PoleFoot", (1.1, 1.1, 0.35), (x, y, z), STEEL_D)]


def bumper(p, x, y, z, s, body, band, cap, sides=8):
    """Pinball-style bumper rock: tapered prism core + fat coloured band + cap."""
    out = [C(p + "Core", s, s * 0.78, s * 1.25, (x, y, z - 0.2), body, sides=sides),
           RING(p + "Band", s * 0.86, s + 0.55, s * 0.32, (x, y, z + s * 0.38), band, sides=sides)]
    out.append(C(p + "Cap", s * 0.8, s * 0.45, s * 0.45, (x, y, z + s * 1.05 - 0.2), cap, sides=sides))
    return out


# ------------------------------------------------------------------------------------------------
# Biome tables (colours by altitude)
# ------------------------------------------------------------------------------------------------
def biome(pk, z):
    n = pk["n"]
    if z < 55:
        return dict(body=(STONE_L, STONE, STONE_D), cap=(GRASS, GRASS_L), lip=GRASS_D)
    if n == 1:
        return dict(body=(STONE_L, STONE, STONE_D), cap=(GRASS, GRASS_L), lip=GRASS_D)
    if n == 2:
        if z < 150:
            return dict(body=(STONE_L, STONE, STONE_D), cap=(GRASS_D, GRASS), lip=PINE)
        return dict(body=(STONE_L, STONE, STONE_D), cap=(SNOW, GRASS_D), lip=PINE)
    if n == 3:
        if z < 170:
            return dict(body=(STONE_L, STONE, STONE_D), cap=(SNOW, SNOW_D), lip=STONE_D)
        return dict(body=(BSTONE_L, BSTONE, BSTONE_D), cap=(SNOW, ICE), lip=ICE_D)
    if n == 4:
        if z < 190:
            return dict(body=(STONE_L, STONE, STONE_D), cap=(ASH, STONE_L), lip=STONE_D)
        return dict(body=(BASALT_L, BASALT, BASALT_D), cap=(ASH, BASALT_L), lip=BASALT_D)
    if z < 380:
        return dict(body=(STONE_L, STONE, STONE_D), cap=(SNOW, SNOW_D), lip=STONE_D)
    return dict(body=(SLATE_L, SLATE, SLATE_D), cap=(LAVSNOW, SLATE_L), lip=SLATE_D)


# ------------------------------------------------------------------------------------------------
# Mountain: fall-line faces
# ------------------------------------------------------------------------------------------------
def gen_face(pk, rnd):
    steps = []
    y, z = FOOT_Y, 0.0
    nxt = rnd.randint(*pk["every"])
    while z < pk["z"] - 1e-6:
        r = rnd.uniform(*pk["riser"])
        if pk["z"] - (z + r) < 1.5:
            r = pk["z"] - z
        z += r
        ledge = False
        nxt -= 1
        if nxt <= 0 and z < pk["z"] - 3:
            ledge = True
            nxt = rnd.randint(*pk["every"])
            tread = rnd.uniform(*pk["ledge"])
        else:
            tread = r / math.tan(math.radians(rnd.uniform(*pk["slope"])))
            tread = max(1.3, tread)
        steps.append(dict(y=y, z=z, r=r, t=tread, ledge=ledge, hw=CH_HW + rnd.uniform(-1.6, 1.6),
                          xo=rnd.uniform(-1.4, 1.4)))
        y += tread
    steps[-1]["top"] = True
    return steps


def face_fn(steps):
    zs = [s["z"] for s in steps]
    ys = [s["y"] for s in steps]

    def f(z):
        if z <= 0:
            return FOOT_Y
        i = bisect.bisect_left(zs, z)
        if i >= len(steps):
            return ys[-1] + 24 + (z - zs[-1]) * 0.7
        return ys[i]

    return f


def build_face(pk, steps, rnd):
    px = pk["x"]
    for i, s in enumerate(steps):
        if s.get("top"):
            continue
        b = biome(pk, s["z"])
        band = int((s["z"] + 7) / 13) % 3
        body = b["body"][band]
        x = px + s["xo"]
        z, r, t, y = s["z"], s["r"], s["t"], s["y"]
        bot = max(-0.5, z - r - 20)
        split = (not s["ledge"]) and r > 2.4 and rnd.random() < 0.22 and i + 1 < len(steps) and steps[i + 1]["r"] > 3.0
        if split:  # two half-steps at different heights break the staircase rhythm
            cut = x + rnd.uniform(-6, 6)
            hi = rnd.choice((-1, 1))
            for side in (-1, 1):
                x0, x1 = (x - s["hw"], cut) if side < 0 else (cut, x + s["hw"])
                zz = z + (1.2 if side == hi else 0.0)
                SPAN("FaceBody", x0, x1, y, y + t + 16, bot, zz - 0.62, body, bevel=0.15)
                SPAN("FaceCap", x0 - 0.25, x1 + 0.25, y - 0.25, y + t + 0.3, zz - 0.62, zz, b["cap"][i % 2], bevel=0.1)
        else:
            SPAN("FaceBody", x - s["hw"], x + s["hw"], y, y + t + 16, bot, z - 0.62, body, bevel=0.15)
            SPAN("FaceCap", x - s["hw"] - 0.25, x + s["hw"] + 0.25, y - 0.25, y + t + 0.3, z - 0.62, z,
                 b["cap"][i % 2], bevel=0.1)
        if s["ledge"]:
            SPAN("FaceLip", x - s["hw"] - 0.45, x + s["hw"] + 0.45, y - 0.5, y + 0.6, z - 1.05, z - 0.64, b["lip"], bevel=0.06)
        # strata band on tall risers: a darker protruding seam (3rd depth layer)
        if r >= 4.2 and i % 2 == 0:
            SPAN("FaceSeam", x - s["hw"] + 1, x + s["hw"] - 1, y - 0.35, y + 0.5, z - r * 0.62, z - r * 0.62 + 0.7,
                 b["body"][(band + 2) % 3], bevel=0.06)


def face_props(pk, steps, rnd, poles_col):
    """Impact features on ledges + slalom poles marking the fall line + height markers."""
    px, n = pk["x"], pk["n"]
    side = 1
    last_marker = 0
    for i, s in enumerate(steps):
        if s.get("top"):
            continue
        x0 = px + s["xo"]
        z, y, t = s["z"], s["y"], s["t"]
        ty = y + min(t, 6) * 0.5  # tread centre
        if i % 5 == 2:  # slalom poles both edges = readable fall line
            for sx in (-1, 1):
                slalom_pole("Pole", x0 + sx * (s["hw"] - 1.0), y + 0.8, z, poles_col if sx < 0 else RED,
                            h=5.0 if n < 3 else 6.5)
        if z - last_marker >= 100 and z < pk["z"] - 20:
            last_marker = int(z // 100) * 100
            sx = -side
            sign_board("HMark", x0 + sx * (s["hw"] - 4.5), y + 1.2, z, 6.4, 3.0, CREAM, pk["accent"],
                       text=str(last_marker), px=0.42)
        if not s["ledge"]:
            # sparse risers decoration: lava cracks / icicles under higher steps
            if n == 4 and s["z"] > 190 and i % 3 == 0:
                for k in range(2):
                    cx = x0 + rnd.uniform(-s["hw"] + 3, s["hw"] - 3)
                    S("LavaCrack", (rnd.uniform(3, 7), 0.3, 0.45), (cx, y - 0.12, z - s["r"] * rnd.uniform(0.3, 0.7)),
                      N_LAVA, em=4, studs="none", bevel=0.02)
                    S("LavaCrackT", (0.45, rnd.uniform(2, 4), 0.25), (cx + rnd.uniform(-2, 2), y + 1.4, z - 0.02),
                      N_LAVA, em=4, studs="none", bevel=0.02)
            if n == 3 and s["z"] > 120 and i % 4 == 1:
                for k in range(rnd.randint(3, 6)):
                    cx = x0 + rnd.uniform(-s["hw"] + 1, s["hw"] - 1)
                    L = rnd.uniform(1.2, 3.2)
                    C("Icicle", 0.05, 0.42, L, (cx, y - 0.55, z - 0.62 - L), ICE_GLASS, sides=4, studs="none")
            continue
        side = -side
        fx = x0 + side * rnd.uniform(4, s["hw"] - 5)
        gx = x0 - side * rnd.uniform(2, s["hw"] - 6)
        biome_ledge(pk, s, fx, gx, ty, rnd, i)


def biome_ledge(pk, s, fx, gx, ty, rnd, i):
    n, z, y, t = pk["n"], s["z"], s["y"], s["t"]
    k = i % 4
    if n == 1:
        if k in (0, 2):
            bumper("Bumper", fx, ty, z, rnd.uniform(1.8, 2.4), STONE, GOLD, GRASS_L)
        else:
            rock_cluster("Pebble", fx, ty, z, rnd.uniform(2.0, 3.2), (STONE, STONE_L, STONE_D), rnd, cap=GRASS_L)
        flower_patch("Gold", gx, ty, z, rnd, cols=(GOLD, WHITE, GOLD))
        if k == 1:
            fence_run("Fence", gx - 4, gx + 4, y + t - 0.8, z)
        if k == 3:
            S("Outcrop", (rnd.uniform(7, 11), 3.5, 2.4), (gx, y - 0.6, z - 0.3), STONE_L, bevel=0.15)
            S("OutcropMoss", (rnd.uniform(5, 7), 2.6, 0.4), (gx, y - 0.4, z + 2.05), GRASS, bevel=0.1)
    elif n == 2:
        hi = z > 150
        if k in (0, 2):
            pine("Pine", fx, ty + 0.5, z, rnd.uniform(9, 13), rnd, snow=hi)
        else:
            # log ramp kicker: two logs on a chock, sloping up toward the front
            BAR("LogRamp", (fx - 1.0, ty + 2.5, z + 0.2), (fx - 1.0, y + 0.3, z + 2.6), 1.3, WOOD)
            BAR("LogRamp", (fx + 1.2, ty + 2.5, z + 0.2), (fx + 1.2, y + 0.3, z + 2.6), 1.3, WOOD_L)
            S("LogChock", (4.2, 1.2, 1.6), (fx, y + 0.6, z), WOOD_D)
            S("LogEnd", (0.2, 0.9, 0.9), (fx - 1.0 - 0.65, y + 0.3, z + 2.15), CREAM, bevel=0.02)
        if k == 1:
            for j in range(3):  # log pile
                BAR("LogPile", (gx - 2.5, ty - 1 + j * 0.0, z + 0.5 + j * 0.95), (gx + 2.5, ty - 1, z + 0.5 + j * 0.95), 0.95,
                    WOOD if j % 2 else WOOD_D)
        elif k == 3:
            S("Stump", (1.6, 1.6, 1.2), (gx, ty, z), WOOD_D)
            S("StumpTop", (1.3, 1.3, 0.2), (gx, ty, z + 1.2), CREAM, bevel=0.04)
            if hi:
                R("SnowPile", (3.4, 2.6, 1.0), (gx + 2.5, ty, z - 0.1), SNOW, radius=0.4)
        else:
            rock_cluster("Rock", gx, ty, z, 2.2, (STONE, STONE_D), rnd, n=2, cap=SNOW if hi else GRASS_L)
    elif n == 3:
        if k in (0, 2):
            bumper("IceBumper", fx, ty, z, rnd.uniform(2.0, 2.6), ICE, WHITE, SNOW)
        else:
            # ice shelf overhanging the ledge + icicle curtain under it
            w = rnd.uniform(8, 12)
            S("IceShelf", (w, 3.6, 0.9), (fx, y - 1.0, z + 0.0), ICE, bevel=0.08)
            S("IceShelfSnow", (w - 1.2, 2.6, 0.4), (fx, y - 0.8, z + 0.9), SNOW, bevel=0.06)
            for j in range(int(w / 1.3)):
                L = rnd.uniform(1.0, 3.4)
                C("Icicle", 0.05, 0.4, L, (fx - w / 2 + 0.7 + j * 1.3, y - 2.4, z - L + 0.05), ICE_GLASS, sides=4,
                  studs="none")
        if k == 1:
            # snowman — a friendly impact target
            B("SnowmanB", (1.6, 1.6, 1.4), (gx, ty, z + 1.3), SNOW, seg=8, rings=5)
            B("SnowmanH", (1.1, 1.1, 1.0), (gx, ty, z + 3.4), SNOW, seg=8, rings=5)
            C("SnowmanNose", 0.25, 0.04, 1.0, (gx, ty - 1.0, z + 3.45), ORANGE, sides=6, rot=(math.radians(90), 0, 0))
            S("SnowmanEyeL", (0.25, 0.2, 0.25), (gx - 0.4, ty - 0.98, z + 3.7), BLACK, studs="none", bevel=0.02)
            S("SnowmanEyeR", (0.25, 0.2, 0.25), (gx + 0.4, ty - 0.98, z + 3.7), BLACK, studs="none", bevel=0.02)
            S("SnowmanScarf", (2.0, 2.0, 0.45), (gx, ty, z + 2.55), RED, bevel=0.1)
            S("SnowmanHat", (1.2, 1.2, 1.0), (gx, ty, z + 4.25), NAVY, bevel=0.05)
        elif k == 3:
            for j in range(3):
                C("IceSpike", rnd.uniform(0.7, 1.1), 0.1, rnd.uniform(2.5, 4.5), (gx + j * 1.4 - 1.4, ty + rnd.uniform(-1, 1), z),
                  ICE_D if j % 2 else ICE, sides=4, rot=(math.radians(rnd.uniform(-10, 10)), math.radians(rnd.uniform(-12, 12)), 0))
        else:
            R("SnowDrift", (5, 3, 1.2), (gx, ty, z - 0.1), SNOW_D, radius=0.4)
    elif n == 4:
        hot = z > 190
        if k in (0, 2):
            # basalt hex column cluster with a glowing lava band
            for j, (dx, dy, hh) in enumerate(((0, 0, 4.2), (1.9, 0.6, 3.0), (-1.7, 0.9, 2.4), (0.6, -1.5, 1.8))):
                C("Basalt", 1.05, 1.05, hh, (fx + dx, ty + dy, z - 0.1), (BASALT_L, BASALT, BASALT_D, BASALT_L)[j], sides=6)
            if hot:
                RING("LavaBand", 0.9, 1.2, 0.35, (fx, ty, z + 2.2), N_LAVA, sides=6, em=5, studs="none")
        else:
            # lava pool inset in a basalt rim
            S("PoolRim", (6.5, 4.4, 0.8), (fx, ty, z - 0.1), BASALT_D)
            S("Lava", (5.2, 3.1, 0.3), (fx, ty, z + 0.55), N_LAVA if hot else N_LAVAY, em=5, studs="none", bevel=0.02)
            S("LavaHot", (2.0, 1.2, 0.3), (fx + 0.8, ty, z + 0.62), N_LAVAY, em=6, studs="none", bevel=0.02)
        if k == 1:
            # steam vent: grated stack + puff
            S("VentBase", (3.0, 3.0, 1.4), (gx, ty, z - 0.1), STEEL_D)
            S("VentStack", (2.0, 2.0, 1.2), (gx, ty, z + 1.3), STEEL)
            for g in range(3):
                S("VentGrate", (1.8, 0.25, 0.2), (gx, ty - 0.6 + g * 0.6, z + 2.5), BLACK, studs="none", bevel=0.02)
            for j in range(3):
                R("Steam", (1.6 - j * 0.3, 1.6 - j * 0.3, 1.2), (gx + j * 0.3, ty, z + 3.0 + j * 1.3), CLOUD_D, radius=0.4)
        elif k == 3:
            warn_sign("Hot", gx, ty, z, col=ORANGE, icon=BLACK)
        else:
            rock_cluster("Obsidian", gx, ty, z, 2.0, (BASALT_D, BASALT), rnd, n=2)
            if hot:
                S("ObsidianGlow", (0.3, 2.2, 0.3), (gx, ty - 0.2, z + 1.3), N_LAVA, em=4, studs="none", bevel=0.02)
    else:
        storm = z > 380
        if k in (0, 2):
            crystal_cluster("Crystal", fx, ty, z, rnd, big=storm)
        else:
            # lightning rod: steel mast + coil rings + glowing tip
            S("RodBase", (2.2, 2.2, 0.8), (fx, ty, z - 0.1), STEEL_D)
            C("RodMast", 0.32, 0.25, 7.5, (fx, ty, z + 0.7), STEEL, sides=6)
            for j in range(3):
                RING("RodCoil", 0.3, 0.75, 0.3, (fx, ty, z + 3.2 + j * 1.2), GOLD, sides=8)
            B("RodTip", (0.55, 0.55, 0.7), (fx, ty, z + 8.6), N_CYAN, em=6, studs="none")
        if k == 1 and storm:
            # floating cloud step out in front of the ledge
            cy = y - rnd.uniform(4, 6)
            for j, (dx, dz, s2) in enumerate(((0, 0, 2.6), (2.4, 0.3, 2.0), (-2.4, 0.2, 2.1), (0.8, 1.1, 1.8))):
                R("CloudStep", (s2 * 1.5, s2 * 1.2, s2 * 0.8), (gx + dx, cy, z + 1.5 + dz), CLOUD if j % 2 == 0 else CLOUD_D,
                  radius=0.5)
        elif k == 3:
            rock_cluster("Slate", gx, ty, z, 2.4, (SLATE, SLATE_D) if storm else (STONE, STONE_D), rnd, n=2,
                         cap=LAVSNOW if storm else SNOW)
        else:
            R("Drift", (4.5, 2.8, 1.0), (gx, ty, z - 0.1), LAVSNOW if storm else SNOW, radius=0.4)


def axis_offset(rot, L):
    from mathutils import Euler, Vector

    v = Euler(rot, "XYZ").to_matrix() @ Vector((0, 0, L))
    return v.x, v.y, v.z


def crystal_cluster(p, x, y, z, rnd, big=False):
    out = []
    k = 1.4 if big else 1.0
    spec = ((0, 0, 1.0, 0), (1.5, 0.5, 0.7, 14), (-1.4, 0.7, 0.65, -16), (0.4, -1.3, 0.55, 8), (-0.6, 1.4, 0.45, -6))
    for j, (dx, dy, f, tilt) in enumerate(spec):
        h = 5.5 * f * k
        r = 1.0 * f * k + 0.3
        col = (CRYSTAL, CRYSTAL_D, CRYSTAL_L, CRYSTAL_D, CRYSTAL)[j]
        rot = (math.radians(tilt), math.radians(-tilt * 0.7), rnd.uniform(0, 1))
        out.append(C(p + "Prism", r, r * 0.92, h * 0.72, (x + dx, y + dy, z - 0.2), col, sides=6, rot=rot))
        # pointed tip sits on the prism (same rotation, offset along the tilted axis)
        o = axis_offset(rot, h * 0.72 - 0.02)
        out.append(C(p + "Tip", r * 0.92, 0.08, h * 0.32, (x + dx + o[0], y + dy + o[1], z - 0.2 + o[2]),
                     CRYSTAL_L if j != 2 else CRYSTAL, sides=6, rot=rot))
    out.append(S(p + "Base", (3.6 * k, 3.0 * k, 0.7), (x, y, z - 0.1), SLATE_D, bevel=0.1))
    return out


# ------------------------------------------------------------------------------------------------
# Mountain: massif (flank tiers), backdrop, launch pads, summits, waterfall
# ------------------------------------------------------------------------------------------------
def flank_tiers(pk, yface, ylast, rnd):
    px, pz = pk["x"], pk["z"]
    xl, xr = pk["dom"]
    for sgn in (-1, 1):
        edge = px + sgn * (CH_HW - 3.0)
        bound = xl if sgn < 0 else xr
        outer = (pk["n"] == 1 and sgn < 0) or (pk["n"] == 5 and sgn > 0)
        x = edge
        while (x - bound) * sgn < -0.5:
            w = rnd.uniform(9, 15) if not outer else rnd.uniform(14, 24)
            x2 = x + sgn * w
            if (x2 - bound) * sgn > -6:
                x2 = bound
            d = abs((x + x2) / 2 - px) - CH_HW
            fall = 2.4 if not outer else 3.2
            hmax = pz + rnd.uniform(-6, 6) - max(0, d) * fall
            if hmax < 6:
                break
            recess = 2.5 + 0.5 * max(0, d) + rnd.uniform(0, 3)
            z0 = -0.5
            z = rnd.uniform(10, 20)
            lvl = 0
            while True:
                last = z >= hmax - 6
                if last:
                    z = hmax
                f = yface(min(z, pz)) + recess + rnd.uniform(-2, 3)
                back = ylast + 30 + (pz - z) * 0.85 + rnd.uniform(0, 10)
                xa, xb = min(x, x2), max(x, x2)
                b = biome(pk, z)
                body = b["body"][(lvl + int(d / 10)) % 3]
                SPAN("Tier", xa, xb, f, back, z0, z - 0.75, body, bevel=0.25)
                SPAN("TierCap", xa - 0.3, xb + 0.3, f - 0.3, back + 0.3, z - 0.75, z, b["cap"][lvl % 2], bevel=0.15)
                if z - z0 > 14:
                    SPAN("TierBand", xa - 0.35, xb + 0.35, f - 0.6, f + 1.0, z0 + (z - z0) * 0.45, z0 + (z - z0) * 0.45 + 1.4,
                         b["lip"], bevel=0.1)
                # occasional prop on the tread in front of the next tier
                if rnd.random() < 0.33 and not last:
                    flank_prop(pk, (xa + xb) / 2 + rnd.uniform(-2, 2), f + rnd.uniform(2, 5), z, rnd)
                if last:
                    break
                z0 = z - 2.5
                z += rnd.uniform(16, 28)
                lvl += 1
            x = x2


def flank_prop(pk, x, y, z, rnd):
    n = pk["n"]
    if z < 55 or n == 1:
        if rnd.random() < 0.5:
            round_tree("FTree", x, y, z, rnd.uniform(9, 12), rnd, leaf=GRASS)
        else:
            rock_cluster("FRock", x, y, z, 2.4, (STONE, STONE_D), rnd, n=2, cap=GRASS_L)
    elif n == 2:
        pine("FPine", x, y, z, rnd.uniform(9, 14), rnd, snow=z > 150)
    elif n == 3:
        if z < 170:
            pine("FPine", x, y, z, rnd.uniform(9, 12), rnd, snow=True)
        else:
            for j in range(2):
                C("FIce", 1.0, 0.1, rnd.uniform(3, 5), (x + j * 1.6, y, z), ICE if j else ICE_D, sides=4)
    elif n == 4:
        if z > 190:
            C("FBasalt", 1.2, 1.2, rnd.uniform(3, 5), (x, y, z), BASALT_L, sides=6)
            S("FLava", (0.3, 3.0, 0.25), (x + 2.0, y, z + 0.02), N_LAVA, em=4, studs="none", bevel=0.02)
        else:
            rock_cluster("FRock", x, y, z, 2.2, (STONE, STONE_D), rnd, n=2)
    else:
        if z > 380:
            crystal_cluster("FCrystal", x, y, z, rnd)
        else:
            pine("FPine", x, y, z, rnd.uniform(9, 12), rnd, snow=True)


def backdrop(pk, nxt, ylast, rnd):
    """Higher range behind a lower peak: tall stepped columns rising north toward the next peak."""
    xl, xr = pk["dom"]
    if pk["n"] == 1:
        xl = -290
    pz = pk["z"]
    hb = pz + 0.55 * (nxt["z"] - pz)
    x = xl
    while x < xr - 1:
        w = min(rnd.uniform(22, 36), xr - x)
        y = ylast + 34 + rnd.uniform(0, 10)
        row = 0
        while row < 6:
            dpt = rnd.uniform(24, 34)
            h = pz * 0.75 + (hb - pz * 0.75) * min(1.0, (row + 1) / 3.5) + rnd.uniform(-14, 14)
            b = biome(nxt if h > pz else pk, h)
            SPAN("Back", x, x + w, y, y + dpt, -0.5, h - 1.0, b["body"][(row + int(x)) % 3], bevel=0.3)
            SPAN("BackCap", x - 0.4, x + w + 0.4, y - 0.4, y + dpt + 0.4, h - 1.0, h, b["cap"][row % 2], bevel=0.2)
            for band in range(1, int(h / 45)):
                bz = band * 45 + rnd.uniform(-4, 4)
                if bz < h - 8:
                    SPAN("BackBand", x - 0.5, x + w + 0.5, y - 0.5, y + 1.5, bz, bz + 2.0, b["lip"], bevel=0.12)
            y += dpt
            row += 1
        x += w


def launch_pad(pk, ylip, rnd):
    """Deck + hazard lip + rails + flag + height sign + cannon ring + zone gate + arrival pad + summit."""
    px, pz, n = pk["x"], pk["z"], pk["n"]
    acc = pk["accent"]
    b = biome(pk, pz)
    D = 24.0
    # summit plateau under deck/gate/arrival pad
    SPAN("Plateau", px - 20, px + 20, ylip - 0.2, ylip + 56, pz - 28, pz - 0.3, b["body"][1], bevel=0.3)
    SPAN("PlateauCap", px - 20.4, px + 20.4, ylip - 0.5, ylip + 56.4, pz - 0.3, pz + 0.3, b["cap"][0], bevel=0.15)
    dz = pz + 0.3
    # deck frame + planks
    SPAN("DeckFrame", px - 16.5, px + 16.5, ylip - 0.3, ylip + D, dz, dz + 1.0, STONE_D if n != 4 else BASALT_D)
    for k in range(7):
        y0 = ylip + 1.6 + k * 3.2
        SPAN("Plank", px - 15.5, px + 15.5, y0 + 0.08, y0 + 3.12, dz + 1.0, dz + 1.45, WOOD if k % 2 else WOOD_L, bevel=0.06)
    top = dz + 1.45
    # hazard lip (top) + hazard fascia (front face)
    for k in range(13):
        x0 = px - 15.6 + k * 2.4
        SPAN("Hazard", x0 + 0.04, x0 + 2.36, ylip - 0.2, ylip + 1.5, dz + 1.0, top + 0.06, HAZ if k % 2 == 0 else BLACK,
             bevel=0.05)
        SPAN("HazardF", x0 + 0.04, x0 + 2.36, ylip - 0.75, ylip - 0.3, dz - 1.6, dz + 1.0, BLACK if k % 2 == 0 else HAZ,
             bevel=0.05)
    # side rails (posts + 2 rails), front left open for the launch
    for sx in (-1, 1):
        xr = px + sx * 16.0
        for k in range(7):
            S("RailPost", (0.7, 0.7, 3.4), (xr, ylip + 3 + k * 3.4, top), WOOD_D)
        S("RailTop", (0.5, 20.4, 0.5), (xr, ylip + 3 + 10.2, top + 3.0), acc)
        S("RailMid", (0.4, 20.4, 0.4), (xr, ylip + 3 + 10.2, top + 1.6), WOOD)
    # flag (front-left) with peak number
    fx, fy = px - 14.0, ylip + 2.4
    S("FlagFoot", (1.8, 1.8, 0.8), (fx, fy, top), STONE_D)
    C("FlagPole", 0.32, 0.26, 15, (fx, fy, top + 0.8), WHITE, sides=8)
    B("FlagBall", (0.6, 0.6, 0.6), (fx, fy, top + 16.1), GOLD, seg=8, rings=5)
    for k in range(3):
        S("Flag", (2.2, 0.3, 4.2), (fx + 1.3 + k * 2.2, fy + (0.25 if k % 2 else 0), top + 11.0 - k * 0.3), pk["flag"], bevel=0.05,
          rot=(0, 0, math.radians(8 if k % 2 else -8)))
    pixtext("FlagNum", str(n), fx + 3.5, fy - 0.15, top + 11.6, 0.55, WHITE)
    # height sign (front-right) — "<height>" + up arrow
    sign_board("HSign", px + 11.0, ylip + 2.6, top, 9.0, 4.0, CREAM, acc, text=f"^{int(pz)}", px=0.5, lift=1.0)
    # cannon mount ring (Ø 9.2) + bolts + aim chevrons
    cy = ylip + 9.5
    RING("MountRing", 3.4, 4.6, 0.55, (px, cy, top - 0.05), STEEL, sides=20)
    C("MountDisc", 3.45, 3.45, 0.35, (px, cy, top - 0.05), STEEL_D, sides=20)
    for k in range(8):
        a = k * math.pi / 4
        C("Bolt", 0.28, 0.28, 0.3, (px + math.cos(a) * 4.0, cy + math.sin(a) * 4.0, top + 0.5), GOLD, sides=6)
    RING("MountGlow", 4.7, 5.1, 0.15, (px, cy, top - 0.05), N_ORANGE, sides=20, em=3, studs="none")
    for k in range(2):  # chevrons pointing down the fall line (-y)
        for sx in (-1, 1):
            S("AimChev", (3.0, 0.7, 0.12), (px + sx * 1.1, ylip + 2.3 + 1.5 * k, top), ORANGE, bevel=0.03,
              rot=(0, 0, math.radians(sx * -35)))
    mark(f"Peak{n}Pad", (px, ylip + D / 2, top), 180.0, (30, 24, 0), peak=pk["name"], launchLipY=round(ylip, 2))
    mark(f"CannonMount{n}", (px, cy, top), 180.0, (9.2, 9.2, 0))
    # zone gate arch at the back of the deck (facing the deck, -y)
    gy = ylip + D + 2.0
    gcol = b["body"][0] if n != 4 else BASALT_L
    for sx in (-1, 1):
        gx = px + sx * 9.5
        S("GatePlinth", (4.6, 4.6, 1.4), (gx, gy, dz), b["body"][2])
        S("GatePillar", (3.4, 3.4, 15.0), (gx, gy, dz + 1.4), gcol)
        for band in (4.0, 9.0):
            S("GateBand", (3.8, 3.8, 0.7), (gx, gy, dz + 1.4 + band), acc)
        S("GateCap", (4.4, 4.4, 1.0), (gx, gy, dz + 16.4), b["body"][2])
        gate_ornament(pk, gx, gy, dz + 17.4, rnd)
    S("GateBeam", (23.0, 3.2, 2.8), (px, gy, dz + 13.6), gcol)
    S("GateBeamTrim", (23.6, 3.6, 0.6), (px, gy, dz + 13.0), acc)
    S("GateKey", (8.0, 3.6, 2.4), (px, gy, dz + 16.4), acc)
    S("GateKeyTop", (5.0, 3.2, 1.4), (px, gy, dz + 18.8), b["body"][2])
    pixtext("GateNum", str(n), px, gy - 1.8, dz + 16.6, 0.4, WHITE)
    # hanging lock sign (+ price plate). Peak 1 is free: open green lock.
    lock_col = GRASS if n == 1 else GOLD
    for sx in (-1, 1):
        S("Chain", (0.25, 0.25, 2.2), (px + sx * 1.6, gy - 0.6, dz + 11.4), STEEL_D, bevel=0.02)
    S("LockBody", (4.0, 1.0, 3.2), (px, gy - 0.6, dz + 8.2), lock_col, bevel=0.12)
    S("LockHole", (0.7, 0.2, 1.2), (px, gy - 1.15, dz + 9.0), BLACK, studs="none", bevel=0.03)
    shy = 0.9 if n == 1 else 0.0  # open shackle lifted on peak 1
    for sx in (-1, 1):
        S("Shackle", (0.6, 0.6, 1.6), (px + sx * 1.25, gy - 0.6, dz + 11.4 + shy - 0.1 - 0.0), STEEL, bevel=0.05)
    S("ShackleTop", (3.1, 0.6, 0.6), (px, gy - 0.6, dz + 12.9 + shy - 0.1), STEEL, bevel=0.05)
    S("PricePlate", (9.0, 0.5, 1.8), (px, gy - 0.6, dz + 5.8), NAVY)
    S("PricePlateRim", (9.6, 0.4, 0.3), (px, gy - 0.45, dz + 7.6), GOLD)
    mark(f"Peak{n}Gate", (px, gy, dz), 180.0, (16, 3.2, 16), priceSurface="PricePlate", free=(n == 1))
    # arrival teleport pad behind the gate
    ay = gy + 13.0
    C("ArrivalBase", 8.0, 8.0, 1.0, (px, ay, dz), b["body"][2], sides=12)
    C("ArrivalTop", 7.2, 7.2, 0.6, (px, ay, dz + 1.0), STONE_L if n != 4 else ASH, sides=12)
    RING("ArrivalGlow", 5.4, 6.2, 0.16, (px, ay, dz + 1.6), N_CYAN, sides=12, em=4, studs="none")
    S("ArrivalStep", (6.0, 2.0, 0.55), (px, ay - 8.4, dz), STONE_L if n != 4 else ASH)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        lx, ly = px + math.cos(a) * 8.6, ay + math.sin(a) * 8.6
        S("LanternPost", (0.8, 0.8, 5.0), (lx, ly, dz), WOOD_D)
        S("LanternBox", (1.4, 1.4, 1.4), (lx, ly, dz + 5.0), STEEL_D)
        S("LanternGlow", (0.9, 0.9, 0.9), (lx, ly, dz + 5.25), N_LAMP, em=5, studs="none")
        S("LanternRoof", (1.8, 1.8, 0.4), (lx, ly, dz + 6.4), acc)
    summit(pk, px, ylip + 58, pz, rnd)
    pad_theme_props(pk, px, ylip, top, rnd)
    return top


def gate_ornament(pk, x, y, z, rnd):
    n = pk["n"]
    if n == 1:
        B("OrnBall", (1.3, 1.3, 1.3), (x, y, z + 1.2), GOLD, seg=10, rings=6)
    elif n == 2:
        pine("OrnPine", x, y, z, 5.5, rnd, snow=True)
    elif n == 3:
        C("OrnIce", 1.4, 0.1, 4.0, (x, y, z), ICE, sides=4)
    elif n == 4:
        C("OrnBowl", 1.3, 1.8, 1.0, (x, y, z), BASALT_D, sides=6)
        B("OrnFlame", (1.0, 1.0, 1.4), (x, y, z + 1.6), N_LAVA, em=5, studs="none", seg=8, rings=5)
    else:
        C("OrnCrystal", 1.0, 0.1, 4.5, (x, y, z), CRYSTAL_L, sides=6)
        B("OrnSpark", (0.4, 0.4, 0.4), (x, y, z + 4.8), N_CYAN, em=6, studs="none", seg=8, rings=5)


def summit(pk, px, y0, pz, rnd):
    """Peak crown behind the launch area — each one a different silhouette."""
    n = pk["n"]
    b = biome(pk, pz + 10)
    if n == 1:  # grassy rock knob + gold flower meadow + bench lookout
        S("Knob", (30, 24, 10), (px, y0 + 10, pz - 1), STONE, bevel=0.3)
        S("KnobCap", (30.6, 24.6, 0.8), (px, y0 + 10, pz + 9), GRASS, bevel=0.15)
        S("Knob2", (16, 14, 8), (px + 3, y0 + 13, pz + 9.8), STONE_L, bevel=0.3)
        S("Knob2Cap", (16.6, 14.6, 0.8), (px + 3, y0 + 13, pz + 17.8), GRASS_L, bevel=0.15)
        rock_cluster("Boulder", px - 6, y0 + 8, pz + 9.8, 4.2, (STONE_L, STONE, STONE_D), rnd, cap=GRASS_L)
        round_tree("SummitTree", px + 6, y0 + 14, pz + 18.6, 12, rnd, leaf=GRASS, fruit=GOLD)
        for k in range(4):
            flower_patch("SumFlower", px - 10 + k * 6, y0 + 2 + (k % 2) * 3, pz + 9.8, rnd, cols=(GOLD, WHITE))
    elif n == 2:  # rocky crown + hero pines
        for k, (dx, dy, h) in enumerate(((-7, 6, 14), (6, 9, 22), (0, 18, 30), (-12, 16, 18), (12, 18, 16))):
            S("Crown", (14, 12, h), (px + dx, y0 + dy, pz - 1), (STONE, STONE_L, STONE_D)[k % 3], bevel=0.3)
            S("CrownCap", (14.5, 12.5, 0.8), (px + dx, y0 + dy, pz - 1 + h), SNOW if h > 16 else GRASS_D, bevel=0.15)
        for k, (dx, dy, h) in enumerate(((-7, 4, 13), (6, 8, 21), (-12, 14, 17))):
            pine("SummitPine", px + dx + 2, y0 + dy + 1, pz - 1 + h + 0.8, 11 + k * 2, rnd, snow=True, hero=True)
    elif n == 3:  # ice fang spires
        for k, (dx, dy, h, r) in enumerate(((0, 14, 46, 9), (-10, 8, 28, 6), (11, 10, 34, 6.5), (4, 22, 30, 7))):
            C("Fang", r, r * 0.35, h, (px + dx, y0 + dy, pz - 1), (BSTONE, BSTONE_L, BSTONE_D, BSTONE)[k], sides=4,
              rot=(0, 0, math.radians(45 + k * 10)))
            C("FangSnow", r * 0.5, 0.2, h * 0.28, (px + dx, y0 + dy, pz - 1 + h * 0.72), SNOW, sides=4,
              rot=(0, 0, math.radians(45 + k * 10)))
        for k in range(6):
            C("FangIce", 1.2, 0.1, rnd.uniform(4, 8), (px - 14 + k * 5.5, y0 + 1, pz - 0.2), ICE if k % 2 else ICE_D, sides=4)
    elif n == 4:  # volcano spire with glowing crater
        lv = [(30, 26, 14), (24, 20, 12), (18, 15, 10)]
        zz = pz - 1
        for k, (w, d, h) in enumerate(lv):
            S("Cone", (w, d, h), (px, y0 + 14, zz), (BASALT, BASALT_L, BASALT_D)[k], bevel=0.3)
            for j in range(3):
                S("ConeCrack", (0.4, 0.3, h * 0.8), (px - w / 2 + 4 + j * (w - 8) / 2, y0 + 14 - d / 2 - 0.1, zz + h * 0.1), N_LAVA,
                  em=4, studs="none", bevel=0.02)
            zz += h
        RING("CraterRim", 5.0, 8.0, 2.4, (px, y0 + 14, zz), BASALT_D, sides=8)
        C("CraterLava", 5.1, 5.1, 1.8, (px, y0 + 14, zz), N_LAVA, sides=8, em=5, studs="none")
        for j in range(4):
            R("Smoke", (5 - j, 5 - j, 3), (px + j * 1.5, y0 + 14 + j, zz + 3 + j * 3.2), CLOUD_D, radius=0.8)
    else:  # Stormcrown: slate summit + purple crystal crown + lightning rods
        S("Crown", (36, 30, 22), (px, y0 + 14, pz - 1), SLATE, bevel=0.3)
        S("CrownCap", (36.6, 30.6, 0.8), (px, y0 + 14, pz + 21), LAVSNOW, bevel=0.15)
        S("Crown2", (24, 20, 14), (px, y0 + 16, pz + 21.8), SLATE_L, bevel=0.3)
        S("Crown2Cap", (24.6, 20.6, 0.8), (px, y0 + 16, pz + 35.8), LAVSNOW, bevel=0.15)
        ring_r = 12
        for k in range(9):
            a = k * 2 * math.pi / 9
            h = 18 + (k % 3) * 6
            cx, cy = px + math.cos(a) * ring_r, y0 + 16 + math.sin(a) * ring_r * 0.8
            tilt = math.radians(14)
            rot = (-math.sin(a) * tilt, math.cos(a) * tilt, a)
            rot = (math.sin(a) * -tilt, math.cos(a) * tilt, 0.0)
            C("CrownPrism", 2.6, 2.4, h, (cx, cy, pz + 35), (CRYSTAL, CRYSTAL_D, CRYSTAL_L)[k % 3], sides=6, rot=rot)
            o = axis_offset(rot, h - 0.05)
            C("CrownTip", 2.4, 0.15, 5.5, (cx + o[0], cy + o[1], pz + 35 + o[2]), CRYSTAL_L, sides=6, rot=rot)
        C("CrownHeart", 4.0, 0.3, 26, (px, y0 + 16, pz + 35), CRYSTAL_L, sides=6)
        for k in range(3):
            a = math.pi * (0.25 + 0.75 * k)
            rx, ry = px + math.cos(a) * 15, y0 + 8 + math.sin(a) * 6
            C("StormRod", 0.45, 0.3, 24, (rx, ry, pz + 21.8), STEEL, sides=6)
            for j in range(4):
                RING("StormCoil", 0.4, 1.0, 0.4, (rx, ry, pz + 30 + j * 2.4), GOLD, sides=8)
            B("StormTip", (1.0, 1.0, 1.2), (rx, ry, pz + 46.5), N_CYAN, em=7, studs="none", seg=8, rings=5)


def pad_theme_props(pk, px, ylip, top, rnd):
    n = pk["n"]
    yb = ylip + 18
    if n == 1:
        for sx in (-1, 1):
            S("FlowerBox", (4.4, 1.6, 1.0), (px + sx * 13.5, yb, top), WOOD_D)
            flower_patch("PadFlowers", px + sx * 13.5, yb, top + 1.0, rnd, cols=(GOLD, PINK, WHITE), n=5, r=1.4)
    elif n == 2:
        for k in range(3):
            BAR("PadLog", (px - 15, yb - 1 + k * 0.0, top + 0.5 + k * 0.95), (px - 10, yb - 1, top + 0.5 + k * 0.95), 0.95, WOOD_D)
        S("Axe", (0.3, 0.3, 2.2), (px - 12.5, yb + 1.5, top + 3.3), WOOD, rot=(0.3, 0, 0))
        S("AxeHead", (1.0, 0.3, 0.6), (px - 12.5, yb + 1.9, top + 5.0), STEEL, rot=(0.3, 0, 0))
        R("PadSnow", (4.0, 3.0, 0.8), (px + 13, yb, top), SNOW, radius=0.35)
    elif n == 3:
        for sx in (-1, 1):
            R("PadSnow", (4.6, 3.0, 1.0), (px + sx * 13, yb, top), SNOW, radius=0.4)
            C("PadIce", 0.9, 0.1, 3.2, (px + sx * 13.5, yb + 0.5, top + 0.8), ICE, sides=4)
    elif n == 4:
        for sx in (-1, 1):
            S("PadBrazier", (2.0, 2.0, 1.6), (px + sx * 13.5, yb, top), BASALT_D)
            B("PadFlame", (0.9, 0.9, 1.3), (px + sx * 13.5, yb, top + 2.3), N_LAVA, em=5, studs="none", seg=8, rings=5)
    else:
        for sx in (-1, 1):
            crystal_cluster("PadCrystal", px + sx * 13, yb, top, rnd)


def waterfall(f3, f4, rnd):
    """Stepped cascade on the Peak 3 / Peak 4 seam: frozen top (icicles) → liquid falls → foot pool."""
    xc, w = 45.0, 10.0
    steps = []
    z, top = 0.0, 372.0
    while z < top:
        z = min(top, z + rnd.uniform(8, 15))
        steps.append(z)
    prev_z, prev_y = 0.0, FOOT_Y - 6
    fronts = []
    for zt in steps:
        fy = min(f3(zt), f4(zt)) - 5.0
        fy = max(fy, prev_y + 3.0)
        fronts.append((zt, fy))
        prev_y = fy
    prev_z = 0.0
    for i, (zt, fy) in enumerate(fronts):
        frozen = zt > 250
        rock = (BSTONE, BSTONE_D) if zt > 170 else (STONE, STONE_D)
        nxt_y = fronts[i + 1][1] if i + 1 < len(fronts) else fy + 20
        SPAN("FallRock", xc - w / 2 - 4, xc + w / 2 + 4, fy, nxt_y + 16, max(-0.5, prev_z - 20), zt - 0.6, rock[i % 2], bevel=0.25)
        SPAN("FallCap", xc - w / 2 - 4.3, xc + w / 2 + 4.3, fy - 0.3, nxt_y + 0.3, zt - 0.6, zt, SNOW if zt > 150 else GRASS_D,
             bevel=0.12)
        sheet = ICE_GLASS if frozen else WATER
        # falling sheet on the riser + pool on the tread below
        SPAN("FallSheet", xc - w / 2, xc + w / 2, fy - 0.9, fy - 0.2, prev_z + 0.02, zt + 0.25, sheet, studs="none", bevel=0.05)
        SPAN("FallPool", xc - w / 2, xc + w / 2, fy - 0.4, nxt_y - 0.3, zt + 0.02, zt + 0.3, sheet, studs="none", bevel=0.05)
        for sx in (-1, 1):  # side boulders frame the falls
            rock_cluster("FallSide", xc + sx * (w / 2 + 2.6), fy + 2.5, zt, rnd.uniform(2.2, 3.0), rock, rnd, n=2,
                         cap=SNOW if zt > 150 else GRASS_L)
        if frozen:
            for j in range(6):
                L = rnd.uniform(1.5, 4.0)
                C("FallIcicle", 0.05, 0.4, L, (xc - w / 2 + 0.8 + j * 1.7, fy - 1.3, zt + 0.25 - L), ICE_GLASS, sides=4, studs="none")
        elif i % 2 == 0:
            for j in range(3):  # foam blocks where the water lands
                R("Foam", (2.0, 1.4, 0.7), (xc - 3 + j * 3, fy - 1.6, prev_z + 0.1), CLOUD, radius=0.3)
        prev_z = zt
    zt, fy = fronts[-1]
    # ice-cave spring at the top
    S("SpringArchL", (3, 4, 9), (xc - 6.5, fy + 2, zt), BSTONE_L)
    S("SpringArchR", (3, 4, 9), (xc + 6.5, fy + 2, zt), BSTONE_L)
    S("SpringArchT", (16, 4, 3), (xc, fy + 2, zt + 9), BSTONE)
    S("SpringDark", (10, 0.5, 9), (xc, fy + 3.8, zt), NAVY, studs="none")
    S("SpringSnow", (17, 4.6, 1.0), (xc, fy + 2, zt + 12), SNOW, bevel=0.2)
    # foot pool (feeds the stream)
    S("PoolRim", (24, 18, 1.2), (xc, FOOT_Y - 4, -0.6), STONE_D, bevel=0.15)
    S("PoolWater", (21, 15, 0.3), (xc, FOOT_Y - 4, 0.35), WATER, studs="none", bevel=0.05)
    for j in range(5):
        R("PoolFoam", (2.4, 1.6, 0.6), (xc - 6 + j * 3, FOOT_Y - 8 + (j % 2), 0.45), CLOUD, radius=0.3)


def build_mountain(seed=11):
    faces = {}
    for pk in PEAKS:
        rnd = random.Random(seed + pk["n"] * 101)
        steps = gen_face(pk, rnd)
        faces[pk["n"]] = (steps, face_fn(steps))
    chunk("Map_Peak1")
    SPAN("MountainFloor", -292, 302, 104, 1000, -3.0, -0.8, DIRT_D, bevel=0.2)
    SPAN("MountainFloorTurf", -292, 302, 104, 1000, -0.8, -0.2, GRASS_D, bevel=0.2)
    frnd = random.Random(seed + 5)
    for k in range(16):  # foothill pine wood west of Pebble Hill
        x, y = frnd.uniform(-284, -222), frnd.uniform(116, 236)
        pine("FootPine", x, y, -0.2, frnd.uniform(11, 16), frnd) if k % 3 else round_tree("FootTree", x, y, -0.2, 11, frnd)
    for k in range(5):
        rock_cluster("FootRock", frnd.uniform(-280, -225), frnd.uniform(118, 230), -0.2, frnd.uniform(2.5, 4), (STONE, STONE_L, STONE_D),
                     frnd, cap=GRASS_L)
    for i, pk in enumerate(PEAKS):
        chunk(f"Map_Peak{pk['n']}")
        rnd = random.Random(seed + pk["n"] * 7)
        steps, yf = faces[pk["n"]]
        ylast = steps[-1]["y"]
        build_face(pk, steps, rnd)
        face_props(pk, steps, rnd, pk["accent"])
        flank_tiers(pk, yf, ylast, rnd)
        if i + 1 < len(PEAKS):
            backdrop(pk, PEAKS[i + 1], ylast, rnd)
        launch_pad(pk, ylast, rnd)
        avg = math.degrees(math.atan2(pk["z"], ylast - FOOT_Y))
        pk["ylast"], pk["avg_slope"], pk["steps"] = ylast, avg, len(steps)
    chunk("Map_Peak3")
    waterfall(faces[3][1], faces[4][1], random.Random(seed + 77))
    return faces


# ------------------------------------------------------------------------------------------------
# Valley terrain
# ------------------------------------------------------------------------------------------------
TERR = [  # designed turf terraces (x0, x1, y0, y1, h)
    (-210, -110, -132, -36, 1.5), (-195, -140, -118, -58, 3.0),  # west meadow (picnic + rock garden)
    (110, 210, -132, -36, 1.5), (135, 195, -120, -60, 3.0),  # east first-aid terrace
    (-130, -70, -30, 2, 1.5), (70, 130, -30, 2, 1.5),  # flower terraces flanking the lift plaza
    (-250, -215, -40, 60, 3.0), (215, 250, -40, 60, 3.0),
]
CELL = 10.0
GX0, GX1, GY0, GY1 = -290.0, 300.0, -280.0, 110.0


def rim_edge(x):
    for bx, by in BASES:
        if abs(x - bx) <= 40:
            return math.floor((by + 26) / CELL) * CELL
    return -170.0


def vh(x, y):
    """Valley height at a cell centre (stepped, designed)."""
    if STREAM_X0 < x < STREAM_X1 and -40 < y < 104:
        return -2.6
    if y < -258:
        return 15.0
    if y < -246:
        return 9.0
    if y < rim_edge(x):
        return RIM_Z
    ax = abs(x)
    wob = 6 * math.sin(y * 0.045)
    if ax > 268 + wob:
        return 12.0
    if ax > 252 + wob:
        return 7.5 if y > -200 else 9.0
    for x0, x1, y0, y1, h in reversed(TERR):
        if x0 <= x <= x1 and y0 <= y <= y1:
            return h
    if ax > 232 + wob:
        return 3.0
    return 0.0


def valley_ground():
    chunk("Map_BoneZone")
    srnd = random.Random(42)
    nx, ny = int((GX1 - GX0) / CELL), int((GY1 - GY0) / CELL)
    hx, hy = HUB

    def skip(cx, cy):
        # nearest point of the cell to the hub centre
        qx = min(max(hx, cx - CELL / 2), cx + CELL / 2)
        qy = min(max(hy, cy - CELL / 2), cy + CELL / 2)
        return math.hypot(qx - hx, qy - hy) < R_MOAT + 1.0

    def tone(cx, cy, h):
        if h == RIM_Z:
            return GRASS_D if int(cx // 30 + cy // 20) % 3 == 0 else GRASS
        k = math.sin(cx * 0.031) + math.cos(cy * 0.027 + cx * 0.012) * 1.2 + 0.5 * math.sin((cx - cy) * 0.05)
        return (GRASS_D, GRASS, GRASS, GRASS_L)[max(0, min(3, int(k + 1.6)))]

    for j in range(ny):
        cy = GY0 + (j + 0.5) * CELL
        i = 0
        while i < nx:
            cx0 = GX0 + i * CELL
            h = vh(cx0 + CELL / 2, cy)
            sk = skip(cx0 + CELL / 2, cy)
            t = tone(cx0 + CELL / 2, cy, h)
            k = i
            while k + 1 < nx:
                c2 = GX0 + (k + 1.5) * CELL
                if vh(c2, cy) != h or skip(c2, cy) != sk or tone(c2, cy, h) != t:
                    break
                k += 1
            if not sk:
                x0, x1 = cx0, GX0 + (k + 1) * CELL
                y0, y1 = cy - CELL / 2, cy + CELL / 2
                bodyc = DIRT if (i + j) % 2 else DIRT_D
                if h < 0:
                    SPAN("Bed", x0, x1, y0, y1, -6, h, STONE_D, bevel=0.1)
                else:
                    SPAN("Ground", x0, x1, y0, y1, -6, h - 0.6, bodyc if h > 0.5 else DIRT, bevel=0.12)
                    SPAN("Turf", x0, x1, y0, y1, h - 0.6, h, t, bevel=0.08)
                    if h >= 1.5:  # lip trim + exposed stones on terrace edges
                        for (ex, ey, ok) in ((x0, cy, vh(x0 - 1, cy) < h), (x1, cy, vh(x1 + 1, cy) < h),
                                             ((x0 + x1) / 2, y0, vh((x0 + x1) / 2, y0 - 1) < h),
                                             ((x0 + x1) / 2, y1, vh((x0 + x1) / 2, y1 + 1) < h)):
                            if ok:
                                horiz = ey in (y0, y1)
                                L = (x1 - x0) if horiz else CELL
                                S("TerrLip", (L + 0.3, 0.6, 0.3) if horiz else (0.6, L + 0.3, 0.3),
                                  (ex, ey, h - 0.9), GRASS_D, bevel=0.04)
                                if srnd.random() < 0.45 and h - 0.9 > 0.8:
                                    st = srnd.uniform(0.9, 1.5)
                                    ox = srnd.uniform(-L / 2 + 1, L / 2 - 1)
                                    R("CliffStone", (st * 1.3, st, min(st, h - 1.0)),
                                      (ex + (ox if horiz else 0), ey + (0 if horiz else ox), max(-0.1, (h - 1.0) * 0.2)),
                                      STONE if srnd.random() < 0.5 else STONE_D, radius=0.15)
            i = k + 1


def terrace_stones(rnd):
    """Exposed stones on terrace risers (kit terrace_field technique), placed by hand along each riser."""
    for x0, x1, y0, y1, h in TERR:
        for edge in range(int((x1 - x0) / 9)):
            x = x0 + 4 + edge * 9 + rnd.uniform(-2, 2)
            for y in (y0, y1):
                if rnd.random() < 0.5:
                    s = rnd.uniform(0.9, 1.6)
                    R("CliffStone", (s * 1.3, s, min(s, h - 0.4)), (x, y, max(-0.1, h * 0.15)), rnd.choice((STONE, STONE_D)),
                      radius=0.15)


# ------------------------------------------------------------------------------------------------
# Hub: plaza, moat, promenade, bridges, shops-ring pads (markers only)
# ------------------------------------------------------------------------------------------------
def hub(rnd):
    chunk("Map_Lake")
    hx, hy = HUB
    RING("MoatBed", R_PLAZA - 1, R_MOAT + 1, 3.0, (hx, hy, -6.0), STONE_D, sides=32)
    RING("MoatWater", R_PLAZA - 0.6, R_MOAT + 0.6, 0.35, (hx, hy, -1.05), WATER, sides=32, studs="none")
    RING("MoatDeep", R_PLAZA + 3, R_MOAT - 3, 0.1, (hx, hy, -0.72), WATER_D, sides=32, studs="none")
    RING("Promenade", R_MOAT, R_PROM, 6.35, (hx, hy, -6.0), STONE_L, sides=32)
    RING("PromEdge", R_MOAT - 0.4, R_MOAT + 1.6, 0.35, (hx, hy, 0.35), CREAM, sides=32)
    RING("PromOuter", R_PROM - 1.2, R_PROM + 0.3, 0.3, (hx, hy, 0.35), STONE, sides=32)
    # lily pads + stepping rocks in the moat
    for k in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        if min(abs(math.sin(a)), abs(math.cos(a))) < 0.2:
            continue
        r = rnd.uniform(R_PLAZA + 3, R_MOAT - 3)
        C("LilyPad", 1.4, 1.4, 0.15, (hx + math.cos(a) * r, hy + math.sin(a) * r, -0.68), GRASS, sides=8)
        if k % 3 == 0:
            B("LilyFlower", (0.5, 0.5, 0.4), (hx + math.cos(a) * r + 0.5, hy + math.sin(a) * r, -0.45), PINK, seg=8, rings=4)
    chunk("Map_BoneZone")
    # plaza: body + concentric studded rings
    C("PlazaBody", R_PLAZA, R_PLAZA, 6.8, (hx, hy, -6.0), STONE, sides=32)
    RING("PlazaTrim", R_PLAZA - 0.3, R_PLAZA + 0.5, 0.5, (hx, hy, 0.25), CREAM, sides=32)
    C("PlazaCore", 14, 14, 0.25, (hx, hy, 0.78), CREAM, sides=16)
    RING("PlazaRingA", 14, 28, 0.25, (hx, hy, 0.78), STONE_L, sides=32)
    RING("PlazaRingB", 28, R_PLAZA - 0.3, 0.25, (hx, hy, 0.78), CREAM, sides=32)
    ztop = 1.03
    # radial paving spokes on ring A (orange chevrons pointing outward to the bridges)
    for k in range(4):
        a = k * math.pi / 2
        for j in range(3):
            r = 17 + j * 3.6
            for sx in (-1, 1):
                S("SpokeChev", (3.2, 0.8, 0.12), (hx + math.cos(a) * r + math.cos(a + sx * 2.2) * 0.9,
                                                  hy + math.sin(a) * r + math.sin(a + sx * 2.2) * 0.9, ztop),
                  ORANGE, bevel=0.03, rot=(0, 0, a + sx * math.radians(55) + math.pi / 2))
    # balustrade around the plaza edge (gaps at the 4 bridges)
    for k in range(32):
        a = (k + 0.5) * 2 * math.pi / 32
        if min(abs(math.sin(a)), abs(math.cos(a))) < 0.16:
            continue
        r = R_PLAZA - 1.2
        S("Baluster", (1.0, 1.0, 2.2), (hx + math.cos(a) * r, hy + math.sin(a) * r, ztop), CREAM, rot=(0, 0, a))
        S("BalusterCap", (1.4, 1.4, 0.4), (hx + math.cos(a) * r, hy + math.sin(a) * r, ztop + 2.2), STONE_D, rot=(0, 0, a))
        if k % 4 == 1:
            kit_lamp(hx + math.cos(a) * (r - 2.0), hy + math.sin(a) * (r - 2.0), ztop)
    # bridges N/E/S/W
    for k in range(4):
        bridge(k * math.pi / 2, rnd)
    shops_ring(ztop)


def kit_lamp(x, y, z):
    reg(kit.lamp_post(nm("Lamp"), (x, y), z=z, light=N_LAMP))


def bridge(a, rnd):
    hx, hy = HUB
    r0, r1 = R_PLAZA - 3, R_MOAT + 3
    L = r1 - r0
    rc = (r0 + r1) / 2
    cx, cy = hx + math.cos(a) * rc, hy + math.sin(a) * rc
    rot = (0, 0, a)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    # arched deck: 3 sections (ramp up, flat crown, ramp down)
    for j, (off, lz, ln, pitch) in enumerate(((-L / 3, 0.75, L / 3 + 0.6, 6), (0, 1.55, L / 3, 0), (L / 3, 0.75, L / 3 + 0.6, -6))):
        S("BridgeDeck", (ln, 8.0, 0.7), (cx + ux * off, cy + uy * off, lz), WOOD if j != 1 else WOOD_L, bevel=0.08,
          rot=(0, math.radians(-pitch), a))
    S("BridgeBeam", (L, 7.0, 1.0), (cx, cy, -1.0), WOOD_D, rot=rot)
    for side in (-1, 1):
        for j in range(5):
            t = -L / 2 + 1.5 + j * (L - 3) / 4
            px, py = cx + ux * t + vx * side * 3.7, cy + uy * t + vy * side * 3.7
            zb = 1.0 + (0.9 if abs(t) < L / 6 else 0.4)
            S("BridgePost", (0.8, 0.8, 3.0), (px, py, zb), WOOD_D, rot=rot)
            S("BridgeKnob", (1.1, 1.1, 0.5), (px, py, zb + 3.0), ORANGE, rot=rot)
        S("BridgeRail", (L - 2, 0.5, 0.5), (cx + vx * side * 3.7, cy + vy * side * 3.7, 3.8), WOOD, rot=rot)
    for end in (-1, 1):  # stone abutments
        S("Abutment", (3.0, 9.4, 1.2), (cx + ux * end * (L / 2 - 1.5), cy + uy * end * (L / 2 - 1.5), -0.2), STONE_D, rot=rot)


def plaza_pad(name, a, r, w, d, col, ztop, face_center=True, kind="pad"):
    hx, hy = HUB
    x, y = hx + math.cos(a) * r, hy + math.sin(a) * r
    yaw = a + math.pi / 2 if face_center else a - math.pi / 2  # local +Y toward the centre
    # local +Y must point at the centre: direction (-cos a, -sin a) => yaw = a + 90deg
    S(name + "Pad", (w, d, 0.5), (x, y, ztop), STONE_L, rot=(0, 0, yaw))
    S(name + "PadTrim", (w + 0.8, d + 0.8, 0.3), (x, y, ztop), col, rot=(0, 0, yaw))
    # corner studs (bollards) mark the build footprint
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * (w / 2 + 0.1), sy * (d / 2 + 0.1)
            wx = x + lx * math.cos(yaw) - ly * math.sin(yaw)
            wy = y + lx * math.sin(yaw) + ly * math.cos(yaw)
            C(name + "Bollard", 0.45, 0.45, 1.0, (wx, wy, ztop), col, sides=8)
    # Roblox rotationY: yaw measured from +Y (front) — convert Blender yaw (front=+Y rotated by yaw)
    mark(name, (x, y, ztop + 0.5), math.degrees(yaw) % 360, (w, d, 0), kind=kind)


def shops_ring(ztop):
    rad = math.radians
    eggcols = [GOLD, PINE_L, ICE_D, ORANGE, CRYSTAL_D]
    for k, ang in enumerate((20, 45, 70, 110, 135)):
        plaza_pad(f"EggStand{k + 1}", rad(ang), 35, 11, 11, eggcols[k], ztop, kind="egg")
    plaza_pad("CannonShop", rad(200), 36, 18, 14, ORANGE, ztop, kind="shop")
    plaza_pad("UpgradeStand", rad(340), 36, 14, 12, TEAL, ztop, kind="shop")
    plaza_pad("SeasonBoard", rad(232), 38, 12, 5, ICE_D, ztop, kind="board")
    plaza_pad("DailyChest", rad(252), 38, 7, 7, GOLD, ztop, kind="chest")
    plaza_pad("LeaderboardBones", rad(288), 38, 11, 5, CREAM, ztop, kind="board")
    plaza_pad("LeaderboardRun", rad(308), 38, 11, 5, GOLD, ztop, kind="board")
    hx, hy = HUB
    C("StatueStep1", 10, 10, 0.6, (hx, hy, ztop), STONE, sides=16)
    C("StatueStep2", 8, 8, 0.6, (hx, hy, ztop + 0.6), CREAM, sides=16)
    RING("StatueGoldRing", 8.0, 8.6, 0.35, (hx, hy, ztop + 0.6), GOLD, sides=16)
    mark("RebirthStatue", (hx, hy, ztop + 1.2), 180.0, (16, 16, 0), kind="statue")
    mark("SpawnFallback", (hx, hy - 30, ztop + 3), 0.0)


# ------------------------------------------------------------------------------------------------
# Lift plaza, paths, landing features, vignettes
# ------------------------------------------------------------------------------------------------
def lift_plaza(rnd):
    chunk("Map_BoneZone")
    x, y = 0.0, 0.0
    SPAN("LiftPlaza", -22, 22, -13, 13, -0.4, 0.6, STONE_L, bevel=0.15)
    SPAN("LiftPlazaTrim", -22.6, 22.6, -13.6, 13.6, -0.4, 0.35, STONE_D, bevel=0.1)
    C("LiftPadBase", 7.5, 7.5, 0.8, (x, 4, 0.6), STONE, sides=6)
    C("LiftPadTop", 6.4, 6.4, 0.4, (x, 4, 1.4), CREAM, sides=6)
    RING("LiftPadGlow", 4.6, 5.6, 0.14, (x, 4, 1.8), N_CYAN, sides=6, em=4, studs="none")
    C("LiftPadCore", 1.8, 1.8, 0.12, (x, 4, 1.8), N_CYAN, sides=6, em=3, studs="none")
    mark("LiftPad", (x, 4, 1.8), 0.0, (12.8, 12.8, 0))
    # lift arch + "LIFT" sign (faces south toward the hub)
    for sx in (-1, 1):
        S("LiftPylon", (2.4, 2.4, 13), (x + sx * 9, 8, 0.6), STEEL)
        S("LiftPylonFoot", (3.4, 3.4, 1.0), (x + sx * 9, 8, 0.6), STEEL_D)
        for j in range(3):
            S("LiftBrace", (2.8, 2.8, 0.5), (x + sx * 9, 8, 3.6 + j * 3.4), CYAN_PAINT)
    S("LiftBeam", (21.5, 2.8, 2.6), (x, 8, 13.6), STEEL_D)
    S("LiftBoard", (14.0, 0.6, 4.4), (x, 6.4, 14.8), NAVY)
    S("LiftBoardRim", (14.8, 0.5, 0.5), (x, 6.3, 19.2), CYAN_PAINT)
    pixtext("LiftTxt", "LIFT", x, 6.1, 15.6, 0.6, WHITE)
    pixtext("LiftUp", "^", x + 6.0, 6.1, 15.9, 0.45, GOLD)
    C("BullWheel", 3.0, 3.0, 0.8, (x, 9.5, 16.5), STEEL, sides=12, rot=(math.radians(90), 0, 0))
    C("BullHub", 0.9, 0.9, 1.0, (x, 9.6, 16.5), GOLD, sides=8, rot=(math.radians(90), 0, 0))
    # waiting gondola chair parked beside the pad (lift theme)
    S("ChairSeat", (5.0, 2.0, 0.6), (x - 15, 6, 2.8), ORANGE)
    S("ChairBack", (5.0, 0.5, 2.4), (x - 15, 6.9, 3.4), ORANGE)
    S("ChairBar", (0.4, 0.4, 6.0), (x - 15, 6.2, 3.4), STEEL_D)
    S("ChairStand", (1.4, 1.4, 2.2), (x - 15, 6, 0.6), STEEL_D)
    for sx in (-1, 1):
        kit_lamp(x + sx * 19, -10, 0.6)
    for k in range(4):  # chevrons from the hub to the pad
        for sx in (-1, 1):
            S("LiftChev", (3.4, 0.9, 0.12), (x + sx * 1.15, -11 + k * 3.0, 0.6), ORANGE, bevel=0.03,
              rot=(0, 0, math.radians(sx * 35)))


CYAN_PAINT = "#2FBFD8"


def follow_ground(objs, lift=0.03):
    for o in objs:
        h = vh(o.location.x, o.location.y)
        o.location.z = max(h, 0.0) + lift + o.location.z
    vb.restud(objs)
    return objs


def paths(rnd):
    chunk("Map_BoneZone")
    lines = []
    # rim road in front of the base rim (collector) + spurs to each base's stairs
    road = [(-200, -150), (-150, -158), (-120, -168), (-80, -176), (-40, -180), (0, -180), (40, -180),
            (80, -176), (120, -168), (150, -158), (200, -150)]
    lines.append(road)
    lines.append([(0, -180), (0, -171)])
    # hub E/W exits to the terraces
    lines.append([(R_PROM + 1, HUB[1]), (104, HUB[1])])
    lines.append([(-R_PROM - 1, HUB[1]), (-104, HUB[1])])
    # landing trail along the south edge of the catch area (to the lift)
    lines.append([(-196, 14), (-120, 14), (-60, 16), (-24, 16)])
    lines.append([(24, 16), (60, 16), (120, 14), (196, 14)])
    tiles = kit.path_network(lines, tile=6.6, step=7.6, colors=(CREAM, "#E8D9AE"), rnd=rnd, edge=STONE_D)
    keep = []
    for o in tiles:
        if STREAM_X0 - 4 < o.location.x < STREAM_X1 + 4 and o.location.y > -30:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        o.name = nm(o.name)
        keep.append(o)
    tiles = keep
    reg(tiles)
    follow_ground(tiles)
    # chevrons along the road (pointing toward the hub / lift)
    def chev_line(line, every=3, toward=None):
        for si in range(len(line) - 1):
            (ax, ay), (bx, by) = line[si], line[si + 1]
            n = max(1, int(math.hypot(bx - ax, by - ay) / 7.6))
            ang = math.atan2(by - ay, bx - ax)
            for k in range(1, n + 1):
                if k % every:
                    continue
                t = k / n
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                d = ang
                if toward is not None:
                    tx, ty = toward
                    if (tx - x) * math.cos(ang) + (ty - y) * math.sin(ang) < 0:
                        d = ang + math.pi
                z = max(vh(x, y), 0) + 0.3
                for sx in (-1, 1):
                    S("Chevron", (3.0, 0.8, 0.14), (x - math.cos(d) * 0.6 + math.cos(d + sx * 1.57) * 0.95,
                                                    y - math.sin(d) * 0.6 + math.sin(d + sx * 1.57) * 0.95, z),
                      ORANGE, bevel=0.03, rot=(0, 0, d + sx * math.radians(-55) + 0))
    chev_line(road, toward=(0, -180))
    chev_line(lines[4], toward=(0, 14))
    chev_line(lines[5], toward=(0, 14))
    chev_line([(0, -180), (0, -171)], every=1)


def stream():
    chunk("Map_Lake")
    xc = (STREAM_X0 + STREAM_X1) / 2
    S("StreamWater", (STREAM_X1 - STREAM_X0 - 0.1, 132, 0.3), (xc, 38, -0.95), WATER, studs="none", bevel=0.03)
    for j in range(8):  # pebbles + reeds along the banks
        y = -20 + j * 15
        for sx in (-1, 1):
            R("StreamPebble", (1.4, 1.1, 0.8), (xc + sx * 3.8, y + sx * 3, -0.9), STONE if j % 2 else STONE_L, radius=0.2)
        S("Reed", (0.25, 0.25, 2.4), (xc - 4.2, y + 6, -0.8), GRASS_D, bevel=0.02)
        S("ReedTop", (0.4, 0.4, 0.7), (xc - 4.2, y + 6, 1.6), DIRT_D, bevel=0.05)
    # culvert arch where the stream slips under the promenade into the moat
    cy = HUB[1] + math.sqrt(R_PROM ** 2 - xc ** 2) + 0.6
    S("CulvertL", (2.0, 2.0, 4.2), (xc - 6.0, cy, -1.0), STONE_D)
    S("CulvertR", (2.0, 2.0, 4.2), (xc + 6.0, cy, -1.0), STONE_D)
    S("CulvertTop", (14.0, 2.2, 1.6), (xc, cy, 2.4), STONE)
    S("CulvertDark", (10.0, 0.4, 3.2), (xc, cy - 0.6, -1.0), NAVY, studs="none")
    # footbridges where the landing trail crosses
    for by in (15.0,):
        S("FootBridge", (14.0, 6.0, 0.6), (xc, by, 0.6), WOOD_L, bevel=0.06)
        S("FootBeam", (14.0, 1.0, 1.2), (xc, by - 2.4, -0.6), WOOD_D)
        S("FootBeam", (14.0, 1.0, 1.2), (xc, by + 2.4, -0.6), WOOD_D)
        for sy in (-1, 1):
            S("FootRail", (14.0, 0.4, 0.4), (xc, by + sy * 2.8, 2.6), WOOD)
            for k in range(3):
                S("FootPost", (0.6, 0.6, 2.4), (xc - 6 + k * 6, by + sy * 2.8, 1.2), WOOD_D)


def hay_heap(x, y, rnd):
    """Peak 1 catch: giant square-bale pyramid + round bales + loose straw."""
    for lvl, (n, w) in enumerate(((5, 6.0), (4, 6.0), (2, 6.0))):
        for k in range(n):
            bx = x - (n - 1) * w / 2 + k * w + rnd.uniform(-0.3, 0.3)
            for row in range(2 if lvl < 2 else 1):
                by = y - 2.0 + row * 4.2 + lvl * 1.2
                S("Bale", (5.8, 4.0, 3.2), (bx, by, lvl * 3.2), HAY if (k + lvl + row) % 2 else HAY_D, bevel=0.2,
                  rot=(0, 0, math.radians(rnd.uniform(-4, 4))))
                S("BaleTwine", (0.3, 4.1, 3.3), (bx - 1.4, by, lvl * 3.2 - 0.02), WOOD_D, bevel=0.05)
                S("BaleTwine", (0.3, 4.1, 3.3), (bx + 1.4, by, lvl * 3.2 - 0.02), WOOD_D, bevel=0.05)
    for k, (dx, dy) in enumerate(((-19, -6), (19, -4), (-14, -12), (15, -12))):
        C("RoundBale", 3.2, 3.2, 4.4, (x + dx, y + dy, 3.2), HAY_D if k % 2 else HAY, sides=12,
          rot=(0, math.radians(90), rnd.uniform(-0.4, 0.4)))
    for k in range(14):
        S("Straw", (rnd.uniform(1, 2.2), 0.2, 0.2), (x + rnd.uniform(-20, 20), y + rnd.uniform(-15, 6), 0.02), HAY,
          bevel=0.02, rot=(0, 0, rnd.uniform(0, 3)))
    sign_board("HaySign", x + 20, y - 14, 0, 8, 2.8, CREAM, GOLD, text="HAY", px=0.42)


def trampoline(x, y, r, mat=BLUE):
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        S("TrampLeg", (0.7, 0.7, 2.6), (x + math.cos(a) * (r - 0.4), y + math.sin(a) * (r - 0.4), 0), STEEL_D)
    n = 16
    for k in range(n):  # striped skirt
        a = (k + 0.5) * 2 * math.pi / n
        S("TrampSkirt", (2 * r * math.sin(math.pi / n) + 0.05, 0.4, 1.4),
          (x + math.cos(a) * (r + 0.1), y + math.sin(a) * (r + 0.1), 1.4), RED if k % 2 else WHITE, rot=(0, 0, a + math.pi / 2))
    RING("TrampFrame", r - 0.9, r + 0.4, 0.6, (x, y, 2.8), BLUE_D, sides=16)
    C("TrampMat", r - 0.9, r - 0.9, 0.3, (x, y, 2.85), NAVY, sides=16)
    RING("TrampTarget", r * 0.25, r * 0.45, 0.08, (x, y, 3.15), GOLD, sides=16)
    C("TrampDot", r * 0.15, r * 0.15, 0.08, (x, y, 3.15), RED, sides=12)
    for k in range(12):  # springs
        a = k * math.pi / 6
        S("TrampSpring", (1.0, 0.3, 0.25), (x + math.cos(a) * (r - 0.6), y + math.sin(a) * (r - 0.6), 3.05), STEEL,
          rot=(0, 0, a))


def crash_mat(x, y, w, d, emblem=None):
    """Padded crash mat with a concentric target — reads from 100 studs."""
    S("MatBase", (w, d, 2.2), (x, y, 0), BLUE, bevel=0.5)
    S("MatBand", (w + 0.3, d + 0.3, 0.6), (x, y, 0.8), BLUE_D, bevel=0.2)
    S("MatTop", (w - 1.0, d - 1.0, 0.8), (x, y, 2.2), BLUE, bevel=0.35)
    zt = 3.0
    rr = min(w, d) * 0.45
    for k, (a, b2, col) in enumerate(((0.8, 1.0, WHITE), (0.6, 0.8, RED), (0.4, 0.6, WHITE), (0.2, 0.4, RED))):
        RING("MatRing", rr * a, rr * b2, 0.1, (x, y, zt - 0.02 + k * 0.0), col, sides=24)
    C("MatBull", rr * 0.2, rr * 0.2, 0.12, (x, y, zt - 0.02), GOLD, sides=16)
    for sx in (-1, 1):  # carry handles
        for sy in (-1, 1):
            S("MatHandle", (3.0, 0.4, 0.8), (x + sx * w * 0.3, y + sy * (d / 2 + 0.2), 1.0), BLACK, studs="none", bevel=0.1)
    for sx in (-1, 1):  # corner flags
        S("MatFlagPole", (0.3, 0.3, 6), (x + sx * (w / 2 + 1), y - d / 2 - 1, 0), WHITE)
        S("MatFlag", (2.0, 0.2, 1.4), (x + sx * (w / 2 + 1) + 1.0, y - d / 2 - 1, 4.5), ORANGE)
    if emblem == "bolt":
        for k, (dx, dz) in enumerate(((0.0, 0.0),)):
            S("BoltA", (1.0, 3.2, 0.12), (x + 0.4, y + 0.9, zt + 0.08), N_CYAN, em=3, studs="none", rot=(0, 0, 0.5))
            S("BoltB", (1.0, 3.2, 0.12), (x - 0.4, y - 0.9, zt + 0.08), N_CYAN, em=3, studs="none", rot=(0, 0, 0.5))


def bounce_cushions(x, y, rnd):
    """Peak 4 catch: chunky inflatable cushions in hot stripes (kid friendly lava-safe zone)."""
    for k, (dx, dy, w, d, h) in enumerate(((0, 0, 16, 12, 4.5), (-13, -3, 10, 9, 3.4), (13, -2, 11, 9, 3.6), (0, -12, 12, 7, 2.6))):
        R("Cushion", (w, d, h), (x + dx, y + dy, 0), ORANGE if k % 2 == 0 else HAZ, radius=1.0)
        for j in range(int(w / 3.2)):
            S("CushionStripe", (1.0, d + 0.1, 0.25), (x + dx - w / 2 + 2 + j * 3.2, y + dy, h - 0.18), RED, bevel=0.08)
    sign_board("CushSign", x + 20, y - 10, 0, 7, 2.6, CREAM, ORANGE, text="SOFT", px=0.36)


def landing(rnd):
    chunk("Map_Landing")
    p = {pk["n"]: pk for pk in PEAKS}
    hay_heap(p[1]["x"], 70, rnd)
    for dx, dy, r in ((-10, 74, 8.0), (10, 64, 7.0), (-4, 52, 6.0), (14, 82, 6.0)):
        trampoline(p[2]["x"] + dx, dy, r)
    crash_mat(p[3]["x"], 66, 34, 26)
    crash_mat(p[3]["x"] - 4, 38, 18, 14)
    bounce_cushions(p[4]["x"], 68, rnd)
    crash_mat(p[5]["x"], 66, 38, 28, emblem="bolt")
    for dx in (-26, 26):
        trampoline(p[5]["x"] + dx, 46, 6.0)
    # "BONE ZONE" landing arch billboard (faces south) between the P2/P3 catch areas
    bx, by = -40.0, 88.0
    for sx in (-1, 1):
        S("BZPost", (2.2, 2.2, 16), (bx + sx * 15, by, 0), WOOD_D)
    S("BZBoard", (30.0, 1.0, 7.0), (bx, by, 14.0), NAVY)
    S("BZRim", (31.0, 1.2, 0.6), (bx, by, 21.0), ORANGE)
    S("BZRimB", (31.0, 1.2, 0.6), (bx, by, 13.4), ORANGE)
    pixtext("BZTxt", "BONE ZONE", bx, by - 0.5, 15.2, 0.52, CREAM)
    mark("LandingZone", (0, 62, 20), 0.0, (440, 96, 44), kind="trigger")
    first_aid(-120, 30, rnd, face=1)
    first_aid(122, 30, rnd, face=1)


def first_aid(x, y, rnd, face=1):
    """First-aid station: canopy tent, plus-sign board, stretcher, crutches, bandage rolls, kit box, bench."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            S("AidPole", (0.5, 0.5, 6.0), (x + sx * 5, y + sy * 4, 0), WHITE)
    for k in range(6):
        S("AidRoof", (10.8 / 6 + 0.02, 9.2, 0.35), (x - 5.4 + (k + 0.5) * 1.8, y, 6.0), GRASS_D if k % 2 else WHITE,
          bevel=0.03)
    for k in range(10):
        B("AidScallop", (0.5, 0.2, 0.4), (x - 4.95 + k * 1.1, y - 4.7, 5.9), GRASS_D if k % 2 else WHITE, seg=8, rings=4)
    S("AidRoofTop", (11.0, 1.0, 0.6), (x, y, 6.35), GRASS_D)
    # board with white plus on green
    S("AidBoard", (4.6, 0.4, 3.0), (x, y - 4.4, 6.9), GRASS_D)
    S("AidPlusV", (0.9, 0.3, 2.2), (x, y - 4.7, 7.3), WHITE, bevel=0.03)
    S("AidPlusH", (2.2, 0.3, 0.9), (x, y - 4.7, 7.95), WHITE, bevel=0.03)
    # stretcher
    for sy in (-1, 1):
        S("StretchPole", (0.35, 7.0, 0.35), (x - 2.4 + sy * 1.1, y, 1.2), WOOD_D)
    S("StretchCloth", (2.0, 5.6, 0.2), (x - 2.4, y, 1.4), ORANGE, bevel=0.04)
    S("StretchPillow", (1.6, 1.0, 0.5), (x - 2.4, y + 2.2, 1.6), WHITE, bevel=0.15)
    for sx in (-1, 1):
        for sy in (-1, 1):
            S("StretchLeg", (0.3, 0.3, 1.2), (x - 2.4 + sx * 1.1, y + sy * 2.6, 0), STEEL_D)
    # crutches leaning on a post
    for k in range(2):
        cx = x + 4.2 + k * 0.9
        BAR("Crutch", (cx, y - 3.0, 0.1), (cx - 0.3, y - 3.8, 4.4), 0.3, STEEL)
        S("CrutchPad", (1.0, 0.5, 0.4), (cx - 0.3, y - 3.8, 4.3), BLACK, studs="none")
        S("CrutchGrip", (0.7, 0.3, 0.3), (cx - 0.15, y - 3.4, 2.4), BLACK, studs="none")
    # first-aid kit box + bandage rolls on a table
    S("AidTable", (4.0, 2.2, 0.4), (x + 2.6, y + 2.0, 2.2), WOOD)
    for sx in (-1, 1):
        S("AidTableLeg", (0.4, 0.4, 2.2), (x + 2.6 + sx * 1.6, y + 2.0, 0), WOOD_D)
    S("AidKit", (1.8, 1.2, 1.1), (x + 2.0, y + 2.0, 2.6), WHITE)
    S("AidKitPlus", (0.9, 0.12, 0.3), (x + 2.0, y + 1.38, 3.0), GRASS_D, bevel=0.02)
    S("AidKitPlus2", (0.3, 0.12, 0.9), (x + 2.0, y + 1.38, 2.7), GRASS_D, bevel=0.02)
    for k in range(3):
        C("Bandage", 0.4, 0.4, 0.7, (x + 3.4 + k * 0.0, y + 1.4 + k * 0.6, 2.6), CREAM, sides=10)
    # bench + giant cartoon bone sign
    S("BenchSeat", (5.0, 1.6, 0.4), (x, y + 7, 1.4), WOOD_L)
    S("BenchBack", (5.0, 0.4, 1.4), (x, y + 7.7, 1.8), WOOD_L)
    for sx in (-1, 1):
        S("BenchLeg", (0.4, 1.4, 1.4), (x + sx * 2.0, y + 7, 0), WOOD_D)
    bone("AidBone", x - 7.5, y - 3, 0.0, 1.0)


def bone(p, x, y, z, k=1.0, col=CREAM):
    """Cartoon bone on a post (game motif) — knob ends + shaft."""
    S(p + "Post", (0.6 * k, 0.6 * k, 4.0 * k), (x, y, z), WOOD_D)
    S(p + "Shaft", (4.0 * k, 0.9 * k, 1.0 * k), (x, y, z + 4.0 * k), col, bevel=0.15)
    for sx in (-1, 1):
        for sz in (-1, 1):
            B(p + "Knob", (0.75 * k, 0.6 * k, 0.75 * k), (x + sx * 2.1 * k, y, z + 4.5 * k + sz * 0.55 * k), col, seg=10, rings=6)


def lifted(dz, fn, *a, **k):
    """Run a builder, then raise everything it made by dz (terrace tops)."""
    n0 = len(CH[CUR[0]])
    fn(*a, **k)
    new = CH[CUR[0]][n0:]
    for o in new:
        o.location.z += dz
    vb.restud(new)
    return new


def vignettes(rnd):
    chunk("Map_BoneZone")
    # west meadow terrace (top z=3): picnic spot + rock garden + trees + bench lookout
    reg(kit.picnic_spot(nm("Picnic"), (-170, -90), z=3.0))
    reg(kit.picnic_spot(nm("Picnic"), (-158, -78), z=3.0, cloth=("#2590D1", "#FFFFFF")))
    reg(kit.rock_garden(nm("RockG"), (-185, -66), z=3.0, rnd=rnd))
    reg(kit.rock_garden(nm("RockG"), (-150, -110), z=3.0, rnd=rnd))
    for (x, y, h) in ((-190, -108, 12), (-145, -64, 11), (-200, -50, 13), (-125, -125, 10)):
        round_tree("MeadowTree", x, y, vh(x, y), h, rnd, leaf=GRASS, fruit=RED if h > 11 else None)
    reg(kit.signpost(nm("Sign"), (-108, -86), z=0.0, arrows=((ORANGE, 0), (TEAL, 120), (GOLD, -110))))
    # east first-aid terrace (top z=3): main aid camp + flower beds + trees
    lifted(3.0, first_aid, 165, -90, rnd)
    reg(kit.rock_garden(nm("RockG"), (185, -112), z=3.0, rnd=rnd))
    for (x, y, h) in ((195, -70, 12), (140, -66, 11), (200, -128, 10), (126, -120, 12)):
        round_tree("EastTree", x, y, vh(x, y), h, rnd, leaf=GRASS_D if h == 12 else GRASS)
    reg(kit.signpost(nm("Sign"), (108, -98), z=0.0, arrows=((ORANGE, 180), (GRASS_D, 60), (GOLD, -60))))
    # flower beds along the hub exits and the lift-plaza terraces
    for sx in (-1, 1):
        reg(kit.flower_bed(nm("Bed"), (sx * 82, HUB[1] - 7), (sx * 100, HUB[1] - 7), z=0.0, rnd=rnd))
        reg(kit.flower_bed(nm("Bed"), (sx * 82, HUB[1] + 7), (sx * 100, HUB[1] + 7), z=0.0, rnd=rnd))
        reg(kit.flower_bed(nm("Bed"), (sx * 76, -24), (sx * 124, -24), z=1.5, rnd=rnd,
                           colors=(GOLD, PINK, "#FFFFFF") if sx < 0 else (PINK, "#B678EA", GOLD)))
        reg(kit.rock_garden(nm("RockG"), (sx * 100, -8), z=1.5, rnd=rnd))
        round_tree("LiftTree", sx * 118, -6, 1.5, 11, rnd, leaf=GRASS_L)
        round_tree("LiftTree", sx * 80, -10, 1.5, 9, rnd, leaf=GRASS)
    # signposts at the rim-road forks
    reg(kit.signpost(nm("Sign"), (8, -184), z=0.0, arrows=((ORANGE, 90), (GOLD, 0), (TEAL, 180))))
    reg(kit.signpost(nm("Sign"), (-52, 18), z=0.0, arrows=((TEAL, 0), (ORANGE, 90), (GOLD, 180))))
    # lamp posts along the rim road
    for x in (-160, -100, -60, 60, 100, 160):
        y = -160 if abs(x) >= 150 else (-172 if abs(x) >= 100 else -184)
        kit_lamp(x, y + 6.5, 0.0)
    # flank pines framing the valley sides
    for k in range(12):
        sx = -1 if k % 2 == 0 else 1
        x = sx * rnd.uniform(258, 285)
        y = -230 + k * 26 + rnd.uniform(-4, 4)
        pine("SidePine", x, y, vh(x, y), rnd.uniform(12, 16), rnd, snow=False)
    # "BONE ZONE" entrance arch over the south path (faces the bases)
    ax, ay = 0.0, -175.0
    for sx in (-1, 1):
        S("ArchPillar", (3.0, 3.0, 13), (ax + sx * 13, ay, 0), STONE_L)
        S("ArchPillarCap", (3.8, 3.8, 1.0), (ax + sx * 13, ay, 13), STONE_D)
        bone("ArchBone", ax + sx * 13, ay, 14.0, 0.6)
    S("ArchBeam", (29, 2.4, 4.6), (ax, ay, 9.0), NAVY)
    S("ArchBeamTop", (30, 2.8, 0.6), (ax, ay, 13.6), ORANGE)
    S("ArchBeamBot", (30, 2.8, 0.6), (ax, ay, 8.6), ORANGE)
    pixtext("ArchTxt", "BONE ZONE", ax, ay - 1.2, 10.0, 0.5, CREAM)


# ------------------------------------------------------------------------------------------------
# Base rim: 6 studded pads + fences + stairs + garden strip + back ridge pines
# ------------------------------------------------------------------------------------------------
BASE_COLS = [RED, BLUE, GRASS_D, GOLD, CRYSTAL, ORANGE]


def base_rim(rnd):
    chunk("Map_BaseRim")
    for i, (bx, by) in enumerate(BASES):
        col = BASE_COLS[i]
        S("BasePad", (48, 40, 1.0), (bx, by, RIM_Z), STONE_L, bevel=0.12)
        for sx in (-1, 1):  # trim frame (raised border)
            S("BaseTrimX", (1.2, 40.0, 0.35), (bx + sx * 23.4, by, BASE_TOP), col, bevel=0.05)
        for sy in (-1, 1):
            S("BaseTrimY", (45.6, 1.2, 0.35), (bx, by + sy * 19.4, BASE_TOP), col, bevel=0.05)
        for sx in (-1, 1):
            for sy in (-1, 1):
                S("BaseCorner", (2.2, 2.2, 1.6), (bx + sx * 23.4, by + sy * 19.4, BASE_TOP), STONE_D)
                S("BaseCornerCap", (2.6, 2.6, 0.5), (bx + sx * 23.4, by + sy * 19.4, BASE_TOP + 1.6), col)
        # low fences on the sides and back (front stays open)
        fence_run_y("BaseFence", bx - 25.6, by - 18, by + 12, RIM_Z, col=WOOD, h=2.4)
        fence_run_y("BaseFence", bx + 25.6, by - 18, by + 12, RIM_Z, col=WOOD, h=2.4)
        fence_run("BaseFence", bx - 22, bx + 22, by - 21.6, RIM_Z, col=WOOD, h=2.4)
        # number plaque on a front post pair
        sign_board("BaseNum", bx - 16, by + 21.6, RIM_Z, 4.0, 3.2, CREAM, col, text=str(i + 1), px=0.5)
        # stairs from the pad front down to the rim road (rim edge -> valley floor)
        edge = rim_edge(bx)
        for k in range(3):
            S("BaseStair", (12, 2.0, RIM_Z - k * 1.33), (bx, edge + 1.0 + k * 2.0, 0), STONE_L if k % 2 else STONE, bevel=0.06)
        SPAN("BaseWalk", bx - 5, bx + 5, by + 20, edge, RIM_Z, RIM_Z + 0.25, CREAM, bevel=0.05)
        for sx in (-1, 1):
            kit_lamp(bx + sx * 8, edge - 1.5, RIM_Z)
        mark(f"Base{i + 1}", (bx, by, BASE_TOP), 0.0, (48, 40, 0), accent=col)
        # garden strip between pads
        if i < len(BASES) - 1:
            nx_, ny_ = BASES[i + 1]
            gx, gy = (bx + nx_) / 2, (by + ny_) / 2
            reg(kit.flower_bed(nm("RimBed"), (gx - 1, gy - 12), (gx - 1, gy + 10), z=RIM_Z, rnd=rnd))
            round_tree("RimTree", gx + 3, gy - 14, RIM_Z, 11, rnd, leaf=GRASS if i % 2 else GRASS_D, fruit=GOLD if i % 2 else None)
            reg(kit.rock_garden(nm("RimRock"), (gx + 3, gy + 6), z=RIM_Z, rnd=rnd))
    # back ridge pines + rocks (frames the bases from the south)
    for k in range(22):
        x = -270 + k * 26 + rnd.uniform(-5, 5)
        y = rnd.uniform(-276, -262)
        pine("RidgePine", x, y, 15.0, rnd.uniform(12, 17), rnd)
    for k in range(10):
        x = -250 + k * 52 + rnd.uniform(-6, 6)
        rock_cluster("RidgeRock", x, -252, 9.0, rnd.uniform(2.5, 3.5), (STONE, STONE_L, STONE_D), rnd, cap=GRASS_L)


# ------------------------------------------------------------------------------------------------
# Build / export
# ------------------------------------------------------------------------------------------------
def build(seed=11):
    vb.reset_scene()
    CH.clear()
    MARK.clear()
    rnd = random.Random(seed)
    build_mountain(seed)
    valley_ground()
    hub(rnd)
    lift_plaza(rnd)
    paths(rnd)
    stream()
    landing(rnd)
    vignettes(rnd)
    base_rim(rnd)
    return CH


def _tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def join_all(max_tris=14000):
    """One mesh per colour group per chunk (= one MeshPart per colour in Roblox), split by tri budget."""
    out = {}
    for cname, objs in CH.items():
        groups = {}
        for o in objs:
            if o.type != "MESH" or not o.data.materials:
                continue
            groups.setdefault(o.data.materials[0].name, []).append(o)
        meshes = []
        for mname, g in sorted(groups.items()):
            g.sort(key=lambda o: (round(o.location.y / 40), o.location.x))
            bins, cur, t = [], [], 0
            for o in g:
                k = _tris(o)
                if cur and t + k > max_tris:
                    bins.append(cur)
                    cur, t = [], 0
                cur.append(o)
                t += k
            if cur:
                bins.append(cur)
            short = mname.replace("M_#", "").replace("_Studs", "s")
            for bi, b in enumerate(bins):
                name = f"{cname}_{short}" + (f"_{bi + 1}" if len(bins) > 1 else "")
                meshes.append(vb.join(name, b) if len(b) > 1 else b[0])
                meshes[-1].name = name
        out[cname] = meshes
    return out


def write_layout(out_dir):
    peaks = []
    for pk in PEAKS:
        peaks.append({"n": pk["n"], "name": pk["name"], "padHeight": pk["z"], "launchLipY": round(pk["ylast"], 2),
                      "faceSteps": pk["steps"], "avgSlopeDeg": round(pk["avg_slope"], 1), "x": pk["x"]})
    data = {
        "version": 1,
        "units": "studs",
        "axes": "Blender: X east, Y north, Z up. Roblox = (x, z, -y). rotationY = yaw in degrees, 0 = model front faces +Y (north); 180 = faces south (valley).",
        "chunks": sorted(CH.keys()),
        "peaks": peaks,
        "markers": MARK,
    }
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "layout.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def export(out_dir, meshes):
    manifest = []
    for cname, ms in meshes.items():
        fbx = vb.export_fbx(os.path.join(out_dir, f"{cname}.fbx"), ms)
        vb.export_glb(os.path.join(out_dir, f"{cname}.glb"), ms)
        tris = sum(_tris(m) for m in ms)
        manifest.append({"name": cname, "file": os.path.relpath(fbx, ROOT), "tris": tris, "parts": len(ms), "kind": "map_chunk",
                         "meshes": [{"name": m.name, "tris": _tris(m)} for m in ms]})
    return manifest


def main(out_dir):
    import time

    t0 = time.time()
    build()
    n_parts = sum(len(v) for v in CH.values())
    print(f"built {n_parts} pieces in {time.time() - t0:.0f}s")
    write_layout(out_dir)
    meshes = join_all()
    print(f"joined in {time.time() - t0:.0f}s")
    man = export(out_dir, meshes)
    mpath = os.path.join(ROOT, "games", "ragdoll-off-a-mountain", "assets", "manifest-map.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2)
    for m in man:
        print(m["name"], m["tris"], "tris", m["parts"], "meshes", "max", max(x["tris"] for x in m["meshes"]))
    print("TOTAL", sum(m["tris"] for m in man), "tris", sum(m["parts"] for m in man), "meshparts", "pieces", n_parts)
    for pk in PEAKS:
        print(pk["name"], "lipY", round(pk["ylast"], 1), "steps", pk["steps"], "avg slope", round(pk["avg_slope"], 1))
    return man


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv[0] if argv else os.path.join(ROOT, "games", "ragdoll-off-a-mountain", "assets", "export", "map"))
