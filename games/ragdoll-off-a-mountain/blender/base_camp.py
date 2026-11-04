"""
Base Camp for "Ragdoll Off a Mountain" — shared base kit + 5 progressive stages (game.md §3.6).

    python3 games/ragdoll-off-a-mountain/blender/base_camp.py <out_dir> [--render] [--samples N] [--only NAME]

Exports (out_dir, default games/ragdoll-off-a-mountain/assets/export/basecamp):
    BaseCamp_Kit.fbx/.glb      always present: Lift pad, Bone Clinic, 4 pet pedestals, TrophyBoard, OwnerSign,
                               path + fence (TrophyBoard / OwnerSign are separate meshes for SurfaceGuis)
    BaseCamp_Stage1..5.fbx/.glb  the building set for that stage (toggle one at a time, kit stays)
    markers.json               relative to pad top centre (+Y = front, toward the mountain)
--render writes FRONT/SIDE/BACK/HERO per stage + KIT close-up + LINEUP to assets/previews/basecamp.

Origin = pad top centre; pad is 48 x 40 studs (x -24..24, y -20..20). 1 unit = 1 stud, Z up.
Built ORIGINAL for this game with vault_blocky / vault_kit techniques (bible ★, §3b, §13).
"""

from __future__ import annotations

import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "blender", "lib"))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import vault_blocky as vb  # noqa: E402
import vault_kit as kit  # noqa: E402

GAME = os.path.join(ROOT, "games", "ragdoll-off-a-mountain")
DEFAULT_OUT = os.path.join(GAME, "assets", "export", "basecamp")
PREVIEWS = os.path.join(GAME, "assets", "previews", "basecamp")

# ---- palette (alpine sub-palette, >= 2 shades per material) ------------------------------------
WOOD = kit.shades("#A8683A")
LOGC = kit.shades("#94582F")
CREAM = kit.shades("#FFF1CF")
RED = kit.shades("#E13A2A")
GRN = kit.shades("#2E9A3E")
LEAF = kit.shades("#4CC24A")
STONE = kit.shades("#8E96A3")
GOLD = kit.shades("#FFD93B")
PINK = kit.shades("#FF8FB8")
ORNG = kit.shades("#FF8A1F")
TEAL = kit.shades("#22C3A6")
BLUE = kit.shades("#2F8FE0")
SNOW, SNOW_D = "#F4FBFF", "#D9ECF7"
IRON = "#3A3F4B"
GLASS = "#9BE1FF"
LAMP = "#FFE7A8"
NEON_ORANGE = "#FF8A1F"
NEON_CYAN = "#5CF2FF"
NEON_GOLD = "#FFD93B"
DARK_IN = "#5A3A22"  # interior shadow wood

S, R, C, B = vb.solid, vb.rounded, vb.cyl, vb.ball
D90 = math.pi / 2


# ---- model sections: each stage set is exported as a few MODELS (each <= 3 meshes, <= 15k tris) ----
_SECTION = ["Main"]


def section(name):
    """Tag every untagged mesh with the current model name, then switch to a new model."""
    for o in bpy.data.objects:
        if o.type == "MESH" and "bc_model" not in o:
            o["bc_model"] = _SECTION[0]
    _SECTION[0] = name


# ---- generic geometry helpers ------------------------------------------------------------------

def rod(name, a, b, r, col, sides=8, emission=0.0, r2=None, studs="all"):
    """Cylinder from point a to point b (poles, ropes, rails, logs at any angle)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    rot = tuple(d.to_track_quat("Z", "Y").to_euler())
    return C(name, r, r if r2 is None else r2, d.length, tuple(a), col, sides=sides, rot=rot,
             emission=emission, studs=studs)


def beam(name, a, b, w, h, col, emission=0.0, studs="all"):
    """Box beam from a to b with a w x h cross-section (braces, rafters, guy ropes)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    rot = tuple(d.to_track_quat("Z", "Y").to_euler())
    return S(name, (w, h, d.length), tuple(a), col, rot=rot, emission=emission, studs=studs, bevel=min(0.04, w * 0.3))


def prism(name, pts, depth, axis, base, col, emission=0.0, studs="all"):
    """Polygon (u, z) extruded along +y (axis 'y': u = x) or +x (axis 'x': u = y) from base."""
    bm = bmesh.new()
    bx, by, bz = base

    def P(u, z, t):
        return (bx + u, by + t, bz + z) if axis == "y" else (bx + t, by + u, bz + z)

    f = [bm.verts.new(P(u, z, 0)) for u, z in pts]
    k = [bm.verts.new(P(u, z, depth)) for u, z in pts]
    bm.faces.new(f)
    bm.faces.new(list(reversed(k)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((f[i], f[j], k[j], k[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = vb._new_mesh_object(name, bm)
    return vb._finish(obj, col, emission, studs, None)


def flat_poly(name, pts, center, yaw, z, h, col, emission=0.0, studs="all"):
    """Flat polygon (x, y local) rotated by yaw, extruded up by h (floor chevrons, arrows)."""
    bm = bmesh.new()
    c, s = math.cos(yaw), math.sin(yaw)
    cx, cy = center
    w = [(cx + px * c - py * s, cy + px * s + py * c) for px, py in pts]
    lo = [bm.verts.new((u, v, z)) for u, v in w]
    hi = [bm.verts.new((u, v, z + h)) for u, v in w]
    bm.faces.new(lo)
    bm.faces.new(list(reversed(hi)))
    for i in range(len(w)):
        j = (i + 1) % len(w)
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return vb._finish(vb._new_mesh_object(name, bm), col, emission, studs, None)


def ring(name, ro, ri, h, loc, col, sides=28, emission=0.0, studs="all"):
    """Hollow ring / collar (pad rims, neon rings, rope coils)."""
    bm = bmesh.new()
    x, y, z = loc
    ob, ot, ib, it = [], [], [], []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        ca, sa = math.cos(a), math.sin(a)
        ob.append(bm.verts.new((x + ro * ca, y + ro * sa, z)))
        ot.append(bm.verts.new((x + ro * ca, y + ro * sa, z + h)))
        ib.append(bm.verts.new((x + ri * ca, y + ri * sa, z)))
        it.append(bm.verts.new((x + ri * ca, y + ri * sa, z + h)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = vb._new_mesh_object(name, bm)
    return vb._finish(obj, col, emission, studs, None)


def disc_y(name, x, y, z, r, depth, col, sides=12, emission=0.0, studs="all"):
    """Disc facing +y (icons, knobs, clock faces). y = back face."""
    return C(name, r, r, depth, (x, y, z), col, sides=sides, rot=(-D90, 0, 0), emission=emission, studs=studs)


def log_x(name, x0, x1, y, zc, col, r=0.55, cap=True, rnd=None):
    """Horizontal log along X centred at height zc with cream end-grain caps."""
    P = [C(name, r, r, x1 - x0, (x0, y, zc), col, sides=8, rot=(0, D90, 0))]
    if cap:
        P.append(C(name + "CapA", r * 0.72, r * 0.72, 0.08, (x0 - 0.05, y, zc), CREAM["dark"], sides=8, rot=(0, D90, 0)))
        P.append(C(name + "CapB", r * 0.72, r * 0.72, 0.08, (x1 - 0.03, y, zc), CREAM["dark"], sides=8, rot=(0, D90, 0)))
    return P


def log_y(name, y0, y1, x, zc, col, r=0.55, cap=True):
    P = [C(name, r, r, y1 - y0, (x, y0, zc), col, sides=8, rot=(-D90, 0, 0))]
    if cap:
        P.append(C(name + "CapA", r * 0.72, r * 0.72, 0.08, (x, y0 - 0.05, zc), CREAM["dark"], sides=8, rot=(-D90, 0, 0)))
        P.append(C(name + "CapB", r * 0.72, r * 0.72, 0.08, (x, y1 - 0.03, zc), CREAM["dark"], sides=8, rot=(-D90, 0, 0)))
    return P


def _split(u0, u1, holes):
    segs, cur = [], u0
    for a, b in sorted(holes):
        if a > cur:
            segs.append((cur, a))
        cur = max(cur, b)
    if cur < u1:
        segs.append((cur, u1))
    return [(a, b) for a, b in segs if b - a > 0.25]


def wall_openings(prefix, axis, fixed, u0, u1, z0, z1, thick, openings, col):
    """Solid wall (along x if axis 'x' else along y) with rectangular openings (ua, ub, za, zb).
    Pieces butt edge-to-edge (no coplanar overlaps)."""
    P = []
    cuts = sorted({u0, u1} | {o[0] for o in openings} | {o[1] for o in openings})
    for i in range(len(cuts) - 1):
        a, b = cuts[i], cuts[i + 1]
        if b - a < 0.05:
            continue
        mid = (a + b) / 2
        holes = [(o[2], o[3]) for o in openings if o[0] < mid < o[1]]
        zsegs = _split(z0, z1, holes) if holes else [(z0, z1)]
        for k, (za, zb) in enumerate(zsegs):
            if axis == "x":
                P.append(S(f"{prefix}W{i}_{k}", (b - a, thick, zb - za), (mid, fixed, za), col))
            else:
                P.append(S(f"{prefix}W{i}_{k}", (thick, b - a, zb - za), (fixed, mid, za), col))
    return P


def bone_icon(prefix, cx, y, cz, L, col, rot=0.0, depth=0.22, knob=None):
    """Flat cartoon bone facing +y (signs, banners, plaques). y = back face."""
    knob = knob or L * 0.17
    c, s = math.cos(rot), math.sin(rot)
    P = [S(f"{prefix}Shaft", (L * 0.72, depth, L * 0.2), (cx, y + depth / 2, cz - L * 0.1), col,
           rot=(0, -rot, 0))]
    for i, (dx, dz) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        ox, oz = dx * L * 0.37, dz * knob * 0.8
        P.append(disc_y(f"{prefix}Knob{i}", cx + ox * c - oz * s, y, cz + ox * s + oz * c, knob, depth + 0.06, col, sides=10))
    return P


def bone_3d(prefix, center, L, col, rot=(0, 0, 0), emission=0.0):
    """Chunky cartoon 3D bone along local X (trophies)."""
    cx, cy, cz = center
    P = []
    r = L * 0.13
    shaft = C(f"{prefix}Shaft", r, r, L * 0.78, (0, 0, 0), col, sides=10, rot=(0, D90, 0), emission=emission)
    P.append(shaft)
    for i, (dx, dy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        P.append(B(f"{prefix}Knob{i}", (r * 1.55, r * 1.55, r * 1.55), (dx * L * 0.39, dy * r * 1.05, 0), col,
                   segments=12, rings=8, emission=emission))
    # centre the shaft and put everything under one transform
    shaft.location = (-L * 0.39, 0, 0)
    pivot = bpy.data.objects.new(f"{prefix}Pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    for o in P:
        o.parent = pivot
    pivot.location = center
    pivot.rotation_euler = rot
    bpy.context.view_layer.update()
    for o in P:  # bake the parent transform so joins/restuds are simple
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.data.objects.remove(pivot)
    vb.restud(P)
    return P


def snow_lumps(prefix, pts, rnd, size=0.8):
    P = []
    for i, (x, y, z) in enumerate(pts):
        s = size * rnd.uniform(0.7, 1.25)
        P.append(R(f"{prefix}{i}", (s * rnd.uniform(1.0, 1.6), s, s * rnd.uniform(0.6, 0.95)), (x, y, z - s * 0.55),
                   SNOW if i % 3 else SNOW_D, radius=s * 0.22, rot=(0, 0, rnd.uniform(-0.2, 0.2))))
    return P


def roof(prefix, cx, cy, z_eave, half, length, rise, ridge="y", col=RED, ov=1.0, t=0.55, bands=3,
         snow=1.0, rnd=None, fascia=WOOD["deep"], drips=True):
    """Gable roof. ridge 'y': ridge runs along Y (gables face front/back), slopes in X.
    half = half span (wall to ridge), length = along the ridge (incl. overhang).
    bands: alternating-shade shingle bands parallel to the ridge (stepped, layered).
    snow: fraction of the slope covered by the snow cap from the ridge down (0 = none)."""
    rnd = rnd or random.Random(7)
    P = []
    a = math.atan2(rise, half)
    Lsl = math.hypot(half, rise) + ov
    zr = z_eave + rise
    ca, sa = math.cos(a), math.sin(a)
    for s in (-1, 1):
        for k in range(bands):
            l0, l1 = Lsl * k / bands, Lsl * (k + 1) / bands
            lm = (l0 + l1) / 2
            tk = t + 0.12 * (k % 2)
            if ridge == "y":
                loc = (cx + s * ca * lm, cy, zr - sa * lm)
                P.append(S(f"{prefix}Sh{s}_{k}", (l1 - l0, length, tk), loc, col["base"] if k % 2 == 0 else col["dark"],
                           rot=(0, s * a, 0)))
            else:
                loc = (cx, cy + s * ca * lm, zr - sa * lm)
                P.append(S(f"{prefix}Sh{s}_{k}", (length, l1 - l0, tk), loc, col["base"] if k % 2 == 0 else col["dark"],
                           rot=(-s * a, 0, 0)))
        # fascia board along the eave
        e = Lsl - 0.15
        if ridge == "y":
            P.append(S(f"{prefix}Fascia{s}", (0.35, length + 0.2, 0.7), (cx + s * ca * e, cy, zr - sa * e - 0.55), fascia))
        else:
            P.append(S(f"{prefix}Fascia{s}", (length + 0.2, 0.35, 0.7), (cx, cy + s * ca * e, zr - sa * e - 0.55), fascia))
        if snow > 0:
            ls = Lsl * snow
            lm = ls / 2
            nx, nz = s * sa, ca  # outward normal component
            if ridge == "y":
                loc = (cx + s * ca * lm + nx * (t + 0.1), cy, zr - sa * lm + nz * (t + 0.1))
                P.append(S(f"{prefix}Snow{s}", (ls, length - 0.3, 0.6), loc, SNOW, rot=(0, s * a, 0), bevel=0.12))
            else:
                loc = (cx, cy + s * ca * lm + nx * (t + 0.1), zr - sa * lm + nz * (t + 0.1))
                P.append(S(f"{prefix}Snow{s}", (length - 0.3, ls, 0.6), loc, SNOW, rot=(-s * a, 0, 0), bevel=0.12))
            if drips:
                pts = []
                n = int(length / 1.6)
                for i in range(n):
                    u = -length / 2 + 0.8 + i * (length - 1.6) / max(1, n - 1)
                    l = ls - 0.2
                    hpos = s * ca * l + nx * (t + 0.6)
                    zz = zr - sa * l + nz * (t + 0.5)
                    pts.append((cx + hpos, cy + u, zz) if ridge == "y" else (cx + u, cy + hpos, zz))
                P += snow_lumps(f"{prefix}Lump{s}_", pts, rnd, size=0.75)
    # ridge cap
    if ridge == "y":
        P.append(S(f"{prefix}Ridge", (1.1, length + 0.3, 0.6), (cx, cy, zr + t * 0.6), SNOW if snow else fascia, bevel=0.15))
    else:
        P.append(S(f"{prefix}Ridge", (length + 0.3, 1.1, 0.6), (cx, cy, zr + t * 0.6), SNOW if snow else fascia, bevel=0.15))
    return P


def door(prefix, x, y, z, w=2.6, h=4.6, col=None, frame=None, lamps=True, step=True, window=True, mat=True):
    """Front (+y) door: slab + plank grooves + knob + frame + lintel + wall lamps + step + mat.
    y = wall outer face."""
    col = col or WOOD
    frame = frame or WOOD["deep"]
    P = [S(f"{prefix}Slab", (w, 0.3, h), (x, y - 0.25, z), col["base"])]
    for i in (-1, 1):  # vertical plank grooves (raised battens)
        P.append(S(f"{prefix}Batten{i}", (0.22, 0.12, h - 0.6), (x + i * w * 0.25, y + 0.03, z + 0.3), col["dark"]))
    P.append(S(f"{prefix}Brace", (w - 0.4, 0.12, 0.3), (x, y + 0.03, z + h * 0.35), col["dark"]))
    P.append(B(f"{prefix}Knob", (0.2, 0.2, 0.2), (x + w * 0.36, y + 0.25, z + h * 0.45), GOLD["base"], segments=10, rings=6))
    if window:
        P.append(disc_y(f"{prefix}Porthole", x, y - 0.05, z + h * 0.72, 0.42, 0.16, GLASS, studs="none"))
        P.append(C(f"{prefix}PortRim", 0.55, 0.55, 0.12, (x, y + 0.05, z + h * 0.72), frame, sides=12, rot=(-D90, 0, 0)))
    t = 0.38
    P += [S(f"{prefix}FrameL", (t, 0.5, h + t), (x - w / 2 - t / 2, y, z), frame),
          S(f"{prefix}FrameR", (t, 0.5, h + t), (x + w / 2 + t / 2, y, z), frame),
          S(f"{prefix}Lintel", (w + 2 * t + 0.6, 0.65, 0.45), (x, y, z + h), frame)]
    if lamps:
        for i, sx in enumerate((-1, 1)):
            lx = x + sx * (w / 2 + 1.0)
            P += [S(f"{prefix}LampArm{i}", (0.22, 0.7, 0.22), (lx, y + 0.35, z + h - 0.9), IRON),
                  S(f"{prefix}LampCap{i}", (0.75, 0.75, 0.22), (lx, y + 0.75, z + h - 0.25), IRON),
                  B(f"{prefix}LampGlow{i}", (0.28, 0.28, 0.34), (lx, y + 0.75, z + h - 0.62), LAMP, segments=10, rings=6,
                    emission=4),
                  S(f"{prefix}LampBase{i}", (0.6, 0.6, 0.16), (lx, y + 0.75, z + h - 1.05), IRON)]
    if step:
        P.append(S(f"{prefix}Step", (w + 1.4, 1.2, 0.35), (x, y + 0.6, max(0.0, z - 0.35)), STONE["light"]))
    if mat:
        P.append(S(f"{prefix}Mat", (w * 0.8, 0.9, 0.06), (x, y + 0.75, z if z <= 0.36 else z - 0.0), RED["dark"], bevel=0.02))
    return P


def window(prefix, x, y, z, w, h, normal="+y", frame=None, sill=None, mullions=1, transom=True, shutters=None):
    """vault_kit framed_window + a transom bar + optional shutters (front walls)."""
    frame = frame or CREAM["base"]
    P = kit.framed_window(prefix, (x, y, z), w, h, normal=normal, frame=frame, glass=GLASS, sill=sill, mullions=mullions)
    sgn = 1 if normal in ("+y", "+x") else -1
    if transom:
        if normal in ("+y", "-y"):
            P.append(S(f"{prefix}Transom", (w, 0.18, 0.18), (x, y + sgn * 0.08, z + h * 0.55), frame))
        else:
            P.append(S(f"{prefix}Transom", (0.18, w, 0.18), (x + sgn * 0.08, y, z + h * 0.55), frame))
            P.append(S(f"{prefix}MullionX", (0.18, 0.18, h), (x + sgn * 0.08, y, z), frame))
    if shutters and normal in ("+y", "-y"):
        for i, sx in enumerate((-1, 1)):
            sx0 = x + sx * (w / 2 + 0.3 + 0.55)
            P.append(S(f"{prefix}Shutter{i}", (1.0, 0.2, h), (sx0, y + sgn * 0.15, z), shutters["base"]))
            for k in range(3):
                P.append(S(f"{prefix}Slat{i}_{k}", (0.8, 0.08, 0.16), (sx0, y + sgn * 0.27, z + 0.4 + k * (h - 0.8) / 2),
                           shutters["dark"], bevel=0.02))
    return P


def sign_board(prefix, x, y, z, w, h, board=None, border=None, ny=0.35):
    """Plank sign facing +y: board of 2-shade planks + chunky border. y = back face."""
    board = board or WOOD
    border = border or WOOD["deep"]
    P = []
    n = max(2, int(round(h / 0.9)))
    for i in range(n):
        P.append(S(f"{prefix}Plank{i}", (w, ny, h / n), (x, y + ny / 2, z + i * h / n), board["light"] if i % 2 else board["base"],
                   bevel=0.03))
    t = 0.32
    P += [S(f"{prefix}BordT", (w + 2 * t, ny + 0.2, t), (x, y + ny / 2, z + h), border),
          S(f"{prefix}BordB", (w + 2 * t, ny + 0.2, t), (x, y + ny / 2, z - t), border),
          S(f"{prefix}BordL", (t, ny + 0.2, h), (x - w / 2 - t / 2, y + ny / 2, z), border),
          S(f"{prefix}BordR", (t, ny + 0.2, h), (x + w / 2 + t / 2, y + ny / 2, z), border)]
    for i, (dx, dz) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):  # corner bolts
        P.append(disc_y(f"{prefix}Bolt{i}", x + dx * (w / 2 + t / 2), y + ny + 0.1, z + (h + t * 0.0) / 2 + dz * (h / 2 + t / 2) - (0 if dz > 0 else 0),
                        0.12, 0.08, GOLD["base"], sides=8))
    return P


def mountain_icon(prefix, cx, y, cz, wdt, depth=0.2):
    """Flat peak icon (grey peak + snow cap) facing +y."""
    hgt = wdt * 0.7
    return [prism(f"{prefix}Peak", [(-wdt / 2, 0), (wdt / 2, 0), (0, hgt)], depth, "y", (cx, y, cz), STONE["dark"]),
            prism(f"{prefix}Cap", [(-wdt * 0.17, hgt * 0.66), (wdt * 0.17, hgt * 0.66), (0, hgt)], depth, "y",
                  (cx, y + 0.04, cz), SNOW, studs="all")]


def bandage_icon(prefix, cx, y, cz, L, depth=0.2, rot=0.6):
    """Cartoon sticking-plaster icon (NOT a red cross): pink strip + cream pad + holes."""
    P = [R(f"{prefix}Strip", (L, depth, L * 0.34), (cx, y, cz - L * 0.17), PINK["base"], radius=min(0.12, L * 0.1),
           rot=(0, -rot, 0))]
    c, s = math.cos(rot), math.sin(rot)
    P.append(S(f"{prefix}Pad", (L * 0.32, depth, L * 0.26), (cx, y + 0.06, cz - L * 0.13), CREAM["base"], rot=(0, -rot, 0)))
    for i, o in enumerate((-0.32, 0.32)):
        P.append(disc_y(f"{prefix}Hole{i}", cx + o * L * c, y + 0.06, cz + o * L * s, L * 0.04, depth, PINK["dark"], sides=6))
    return P


def pine(prefix, x, y, h=12.0, rnd=None, snow=True):
    """Chunky alpine pine: trunk + 5 skirts of radial, drooping angular slabs (individually placed,
    varied size/yaw) around a core — spiky irregular silhouette, darker below, lighter on top."""
    rnd = rnd or random.Random(11)
    P = [C(f"{prefix}Trunk", 0.7, 0.5, h * 0.3, (x, y, 0), "#8A5530", sides=8),
         S(f"{prefix}Root", (1.9, 1.9, 0.5), (x, y, 0), "#6B3F22", rot=(0, 0, rnd.uniform(0, 1)))]
    tiers = 5
    for t in range(tiers):
        f = 1 - t / tiers
        rad = 3.6 * f + 0.9
        z = h * 0.18 + t * h * 0.15
        n = (7, 6, 6, 5, 4)[t]
        base_col = (GRN["deep"], GRN["dark"], GRN["base"], LEAF["dark"], LEAF["base"])[t]
        alt_col = (GRN["dark"], GRN["base"], LEAF["dark"], GRN["base"], LEAF["light"])[t]
        P.append(S(f"{prefix}Core{t}", (rad * 0.9, rad * 0.9, h * 0.15), (x, y, z), base_col, bevel=0.08, rot=(0, 0, t * 0.5)))
        a0 = rnd.uniform(0, 6.3)
        for k in range(n):
            a = a0 + 2 * math.pi * k / n + rnd.uniform(-0.25, 0.25)
            ln = rad * rnd.uniform(0.85, 1.1)
            wd = rad * rnd.uniform(0.55, 0.75)
            rr = rad * 0.42
            droop = rnd.uniform(0.18, 0.32)
            col = base_col if k % 2 else alt_col
            P.append(S(f"{prefix}T{t}_{k}", (ln, wd, h * 0.1), (x + math.cos(a) * rr, y + math.sin(a) * rr, z + h * 0.03),
                       col, bevel=0.07, rot=(0, droop, a)))
            if snow and (k + t) % 2 == 0:
                P.append(S(f"{prefix}Sn{t}_{k}", (ln * 0.55, wd * 0.6, 0.3),
                           (x + math.cos(a) * (rr - ln * 0.1), y + math.sin(a) * (rr - ln * 0.1), z + h * 0.03 + h * 0.1 - 0.02),
                           SNOW, bevel=0.1, rot=(0, droop, a)))
    zt = h * 0.18 + tiers * h * 0.15
    P.append(S(f"{prefix}Tip", (1.0, 1.0, 1.6), (x, y, zt - 0.4), LEAF["base"], rot=(0.08, -0.06, 0.4)))
    if snow:
        P.append(S(f"{prefix}TipSnow", (0.85, 0.85, 0.4), (x, y, zt + 1.15), SNOW, rot=(0.08, -0.06, 0.4), bevel=0.12))
    return P


def boulder(prefix, x, y, s, rnd, moss=True, snow=False):
    P = [R(f"{prefix}A", (s, s * 0.85, s * 0.7), (x, y, 0), STONE["base"], radius=s * 0.16, rot=(0, 0, rnd.uniform(0, 1.5))),
         R(f"{prefix}B", (s * 0.6, s * 0.55, s * 0.5), (x + s * 0.55, y + s * 0.2, 0), STONE["dark"], radius=s * 0.12,
           rot=(0, 0, rnd.uniform(0, 1.5)))]
    if moss:
        P.append(S(f"{prefix}Moss", (s * 0.55, s * 0.5, 0.18), (x - s * 0.05, y, s * 0.68), LEAF["base"], bevel=0.06))
    if snow:
        P.append(S(f"{prefix}Snow", (s * 0.6, s * 0.5, 0.25), (x - s * 0.05, y, s * 0.68), SNOW, bevel=0.08))
    return P


def lantern_post(prefix, x, y, h=4.6, z=0.0):
    """Alpine lantern on a timber post with a hanging arm."""
    return [S(f"{prefix}Foot", (1.0, 1.0, 0.4), (x, y, z), STONE["dark"]),
            S(f"{prefix}Post", (0.5, 0.5, h), (x, y, z + 0.4), WOOD["dark"]),
            S(f"{prefix}Arm", (1.6, 0.35, 0.35), (x + 0.6, y, z + 0.4 + h - 0.6), WOOD["deep"]),
            S(f"{prefix}Cap", (0.9, 0.9, 0.25), (x + 1.2, y, z + h - 0.75), IRON),
            B(f"{prefix}Glow", (0.32, 0.32, 0.4), (x + 1.2, y, z + h - 1.2), LAMP, segments=10, rings=6, emission=4),
            S(f"{prefix}Bot", (0.7, 0.7, 0.18), (x + 1.2, y, z + h - 1.75), IRON)]


def bench(prefix, x, y, yaw=0.0, col=WOOD):
    c, s = math.cos(yaw), math.sin(yaw)

    def p(dx, dy):
        return (x + dx * c - dy * s, y + dx * s + dy * c)

    P = []
    for i, dx in enumerate((-1.3, 1.3)):
        px, py = p(dx, 0)
        P.append(S(f"{prefix}Leg{i}", (0.4, 1.2, 1.0), (px, py, 0), IRON, rot=(0, 0, yaw)))
    for k in range(2):
        px, py = p(0, -0.3 + k * 0.6)
        P.append(S(f"{prefix}Seat{k}", (3.4, 0.55, 0.22), (px, py, 1.0), col["base"] if k else col["light"], rot=(0, 0, yaw)))
    px, py = p(0, -0.75)
    P.append(S(f"{prefix}Back", (3.4, 0.22, 0.7), (px, py, 1.5), col["dark"], rot=(0, 0, yaw)))
    return P


def flower_box(prefix, x, y, z, w, normal="+y"):
    """Window flower box: timber box + soil + mixed blooms + leaves (purposeful, not scatter)."""
    sg = 1 if normal == "+y" else -1
    P = [S(f"{prefix}Box", (w, 0.9, 0.7), (x, y + sg * 0.45, z), WOOD["dark"]),
         S(f"{prefix}Trim", (w + 0.2, 1.0, 0.18), (x, y + sg * 0.45, z + 0.7), WOOD["deep"]),
         S(f"{prefix}Soil", (w - 0.3, 0.6, 0.1), (x, y + sg * 0.45, z + 0.72), "#5A3A22")]
    cols = (RED["base"], PINK["base"], GOLD["base"], "#B678EA")
    n = max(2, int(w / 0.7))
    for i in range(n):
        fx = x - w / 2 + 0.45 + i * (w - 0.9) / max(1, n - 1)
        hh = 0.35 + 0.2 * ((i * 7) % 3) / 2
        P.append(S(f"{prefix}Leaf{i}", (0.55, 0.45, 0.3), (fx, y + sg * 0.5, z + 0.8), LEAF["base"] if i % 2 else GRN["base"],
                   bevel=0.08, rot=(0, 0, 0.4 * (i % 3))))
        P.append(S(f"{prefix}Bloom{i}", (0.45, 0.45, 0.35), (fx, y + sg * (0.45 + 0.12 * (i % 2)), z + 0.85 + hh), cols[i % 4],
                   bevel=0.1, rot=(0, 0, 0.6 * i)))
    return P


def railing(prefix, a, b, z, h=1.6, col=WOOD, step=0.9, post_every=4):
    """Balcony / porch railing from a to b (xy): top rail + bottom rail + balusters + chunky posts."""
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay)
    yaw = math.atan2(by - ay, bx - ax)
    cx, cy = (ax + bx) / 2, (ay + by) / 2
    P = [S(f"{prefix}Top", (L + 0.4, 0.45, 0.3), (cx, cy, z + h), col["dark"], rot=(0, 0, yaw)),
         S(f"{prefix}Bot", (L, 0.3, 0.25), (cx, cy, z + 0.25), col["dark"], rot=(0, 0, yaw))]
    n = max(2, int(L / step))
    for i in range(n + 1):
        t = i / n
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        if i % post_every == 0:
            P.append(S(f"{prefix}Post{i}", (0.5, 0.5, h + 0.5), (x, y, z), col["deep"], rot=(0, 0, yaw)))
        else:
            P.append(S(f"{prefix}Bal{i}", (0.22, 0.22, h - 0.25), (x, y, z + 0.25), col["base"] if i % 2 else col["light"],
                       rot=(0, 0, yaw)))
    return P


def interior_light(prefix, x, y, z, w=2.0, d=1.0):
    return [S(f"{prefix}Panel", (w, d, 0.15), (x, y, z), LAMP, emission=2.5)]


# ---- shared base kit (always present) ----------------------------------------------------------

KIT_POS = {
    "LiftPad": (16.5, 13.5),
    "Clinic": (-16.5, 12.5),
    "Pets": [(-10.5, 9.0), (-6.5, 9.0), (6.5, 9.0), (10.5, 9.0)],
    "TrophyBoard": (-8.5, 17.0),
    "OwnerSign": (7.0, 18.0),
}
MARKERS = {}


def lift_pad():
    x, y = KIT_POS["LiftPad"]
    P = [C("LiftBase", 3.9, 3.9, 0.45, (x, y, 0), STONE["dark"], sides=28),
         C("LiftRim", 3.6, 3.6, 0.3, (x, y, 0.45), GOLD["base"], sides=28),
         ring("LiftNeon", 3.35, 3.05, 0.12, (x, y, 0.75), NEON_CYAN, emission=4),
         C("LiftDisc", 3.0, 3.0, 0.4, (x, y, 0.45), BLUE["base"], sides=28),
         C("LiftDiscIn", 1.9, 1.9, 0.12, (x, y, 0.85), BLUE["light"], sides=24)]
    # chevron ring: 8 gold chevrons on the rim pointing clockwise (lift is "go")
    chev = [(-0.35, -0.55), (0.15, 0.0), (-0.35, 0.55), (0.05, 0.55), (0.55, 0.0), (0.05, -0.55)]
    for i in range(10):
        a = 2 * math.pi * i / 10
        P.append(flat_poly(f"LiftChev{i}", chev, (x + math.cos(a) * 2.45, y + math.sin(a) * 2.45), a + D90, 0.85, 0.14, GOLD["light"]))
    # big up-arrow in the centre pointing at the mountain (+y)
    P += [S("LiftArrowStem", (0.7, 1.4, 0.12), (x, y - 0.5, 0.97), SNOW, bevel=0.03),
          prism("LiftArrowHead", [(-1.1, 0), (1.1, 0), (0, 1.2)], 0.12, "x", (x, y + 0.2, 0.97), SNOW)]
    # turn the arrow head to lie flat: built in a vertical plane — rebuild flat with a z extrusion instead
    bpy.data.objects.remove(P.pop())
    bm = bmesh.new()
    vs = [bm.verts.new((x + px, y + py, 0.97)) for px, py in ((-1.15, 0.2), (1.15, 0.2), (0, 1.5))]
    vt = [bm.verts.new((x + px, y + py, 1.09)) for px, py in ((-1.15, 0.2), (1.15, 0.2), (0, 1.5))]
    bm.faces.new(vs)
    bm.faces.new(list(reversed(vt)))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((vs[i], vs[j], vt[j], vt[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.append(vb._finish(vb._new_mesh_object("LiftArrowHead", bm), SNOW, 0, "all", None))
    # chairlift pole behind the pad with a little chair + arrow sign pointing at the mountain
    px, py = x + 3.6, y - 2.6
    P += [S("LiftPoleFoot", (1.6, 1.6, 0.6), (px, py, 0), STONE["base"]),
          C("LiftPole", 0.42, 0.35, 11.0, (px, py, 0.6), "#E9EEF5", sides=10),
          S("LiftPoleBandA", (1.0, 1.0, 0.45), (px, py, 4.0), RED["base"]),
          S("LiftPoleBandB", (1.0, 1.0, 0.45), (px, py, 7.0), RED["base"]),
          S("LiftCross", (0.6, 6.0, 0.6), (px, py + 0.5, 11.2), IRON),
          C("LiftWheelA", 0.9, 0.9, 0.35, (px - 0.2, py + 3.2, 11.5), "#C9D3DD", sides=14, rot=(0, D90, 0)),
          C("LiftWheelB", 0.9, 0.9, 0.35, (px - 0.2, py - 2.2, 11.5), "#C9D3DD", sides=14, rot=(0, D90, 0)),
          C("LiftHubA", 0.35, 0.35, 0.5, (px - 0.28, py + 3.2, 11.5), RED["base"], sides=8, rot=(0, D90, 0)),
          S("LiftCableHouse", (1.2, 6.6, 0.9), (px - 0.5, py + 0.5, 11.8), RED["dark"]),
          S("LiftCableHouseCap", (1.4, 6.8, 0.3), (px - 0.5, py + 0.5, 12.7), SNOW, bevel=0.1),
          rod("LiftHanger", (px, py + 3.2, 10.6), (px, py + 3.2, 7.6), 0.1, IRON, sides=6),
          S("LiftChairSeat", (2.6, 1.2, 0.3), (px, py + 3.2, 6.2), RED["base"]),
          S("LiftChairBack", (2.6, 0.3, 1.3), (px, py + 2.7, 6.5), RED["dark"]),
          S("LiftChairArm", (0.2, 1.2, 0.2), (px - 1.3, py + 3.2, 6.9), IRON),
          S("LiftChairArmB", (0.2, 1.2, 0.2), (px + 1.3, py + 3.2, 6.9), IRON),
          S("LiftChairFrame", (0.15, 0.15, 1.5), (px - 1.3, py + 3.2, 6.5), IRON),
          S("LiftChairFrameB", (0.15, 0.15, 1.5), (px + 1.3, py + 3.2, 6.5), IRON),
          beam("LiftChairTop", (px - 1.3, py + 3.2, 7.95), (px + 1.3, py + 3.2, 7.95), 0.18, 0.18, IRON)]
    # arrow sign on the pole pointing +y (toward the mountain), with a peak icon
    P += [S("LiftSignArm", (0.3, 0.6, 0.3), (px, py + 0.3, 8.6), IRON),
          S("LiftSignBoard", (0.45, 3.2, 1.6), (px, py + 1.9, 8.0), BLUE["base"]),
          S("LiftSignBorder", (0.5, 3.4, 0.25), (px, py + 1.9, 9.6), SNOW),
          S("LiftSignBorderB", (0.5, 3.4, 0.25), (px, py + 1.9, 7.75), SNOW)]
    bm = bmesh.new()
    tip = [(py + 3.5, 7.75), (py + 4.6, 8.8), (py + 3.5, 9.85)]
    a0 = [bm.verts.new((px - 0.25, u, z)) for u, z in tip]
    a1 = [bm.verts.new((px + 0.25, u, z)) for u, z in tip]
    bm.faces.new(a0)
    bm.faces.new(list(reversed(a1)))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((a0[i], a0[j], a1[j], a1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.append(vb._finish(vb._new_mesh_object("LiftSignTip", bm), GOLD["base"], 0, "all", None))
    for sx in (-1, 1):  # peak icon both faces
        P.append(prism(f"LiftSignPeak{sx}", [(-0.8, 0), (0.8, 0), (0, 1.0)], 0.12, "x",
                       (px + sx * 0.23 - (0.12 if sx < 0 else 0), py + 1.7, 8.3), SNOW))
        P.append(S(f"LiftSignNeon{sx}", (0.1, 2.8, 0.14), (px + sx * 0.28, py + 1.9, 8.05), NEON_CYAN, emission=4))
    # post bollards with rope (queue feel)
    for i, a in enumerate((2.1, 2.6, 3.7, 4.2)):
        bx, by = x + math.cos(a) * 4.5, y + math.sin(a) * 4.5
        P += [C(f"LiftBollard{i}", 0.3, 0.3, 1.6, (bx, by, 0), GOLD["dark"], sides=8),
              B(f"LiftBollardTop{i}", (0.38, 0.38, 0.3), (bx, by, 1.7), GOLD["light"], segments=10, rings=6)]
    MARKERS["LiftPad"] = {"pos": [x, y, 0.85], "radius": 3.0, "note": "touch to ride the lift to your highest peak"}
    return P


def clinic():
    x, y = KIT_POS["Clinic"]
    P = []
    # canopy frame: 4 posts + striped pink/cream awning roof + scalloped valance
    for i, (dx, dy) in enumerate(((-4, -3.2), (4, -3.2), (-4, 3.0), (4, 3.0))):
        P.append(S(f"ClinicPost{i}", (0.45, 0.45, 6.0), (x + dx, y + dy, 0), "#F2F5FA"))
        P.append(S(f"ClinicPostFoot{i}", (0.9, 0.9, 0.35), (x + dx, y + dy, 0), PINK["dark"]))
    P.append(S("ClinicBeamF", (8.6, 0.5, 0.45), (x, y + 3.0, 6.0), PINK["dark"]))
    P.append(S("ClinicBeamB", (8.6, 0.5, 0.45), (x, y - 3.2, 6.0), PINK["dark"]))
    P += kit.striped_awning("ClinicAwn", x - 4.4, x + 4.4, y - 3.3, 6.6, depth=6.9, tilt=8, colors=(PINK["base"], CREAM["light"]))
    # sign on the canopy front: bandage icon + bone (NO red cross)
    P += sign_board("ClinicSign", x, y + 3.25, 6.9, 5.2, 1.6, board={"base": "#FFFFFF", "light": "#F2F5FA"}, border=PINK["dark"])
    P += bandage_icon("ClinicSignBand", x - 1.4, y + 3.65, 7.7, 1.9)
    P += bone_icon("ClinicSignBone", x + 1.2, y + 3.62, 7.75, 1.9, CREAM["dark"], rot=-0.25)
    # stretcher bed along x (head at -x)
    bx, by = x - 0.5, y
    P += [S("BedFrame", (5.6, 2.6, 0.35), (bx, by, 1.3), "#E9EEF5"),
          S("BedRailL", (5.6, 0.2, 0.35), (bx, by + 1.35, 1.8), PINK["dark"]),
          S("BedRailR", (5.6, 0.2, 0.35), (bx, by - 1.35, 1.8), PINK["dark"]),
          R("BedMattress", (5.2, 2.3, 0.55), (bx, by, 1.62), "#FFFFFF", radius=0.18),
          R("BedPillow", (1.1, 1.8, 0.5), (bx - 2.0, by, 2.15), CREAM["light"], radius=0.2),
          R("BedBlanket", (2.9, 2.45, 0.32), (bx + 0.9, by, 2.1), PINK["base"], radius=0.12),
          S("BedBlanketFold", (0.5, 2.5, 0.38), (bx - 0.55, by, 2.1), PINK["light"], bevel=0.1),
          S("BedHead", (0.35, 2.6, 2.0), (bx - 2.95, by, 1.3), PINK["dark"]),
          S("BedHeadCap", (0.5, 2.8, 0.3), (bx - 2.95, by, 3.3), "#E9EEF5"),
          S("BedFoot", (0.35, 2.6, 1.0), (bx + 2.95, by, 1.3), PINK["dark"])]
    for i, (dx, dy) in enumerate(((-2.4, -1.0), (2.4, -1.0), (-2.4, 1.0), (2.4, 1.0))):
        P += [S(f"BedLeg{i}", (0.25, 0.25, 0.9), (bx + dx, by + dy, 0.45), "#C9D3DD"),
              C(f"BedWheel{i}", 0.3, 0.3, 0.25, (bx + dx - 0.12, by + dy, 0.3), IRON, sides=10, rot=(0, D90, 0))]
    # bandage-roll stand + giant plaster leaning on the bed
    P += [S("StandFoot", (1.2, 1.2, 0.25), (x + 3.2, y + 1.4, 0), "#C9D3DD"),
          C("StandPole", 0.12, 0.12, 4.0, (x + 3.2, y + 1.4, 0.25), "#E9EEF5", sides=8),
          S("StandHook", (1.2, 0.15, 0.15), (x + 3.2, y + 1.4, 4.2), "#E9EEF5"),
          C("StandRollA", 0.45, 0.45, 0.7, (x + 2.65, y + 1.4, 3.3), CREAM["base"], sides=12, rot=(0, D90, 0)),
          C("StandRollB", 0.4, 0.4, 0.6, (x + 3.15, y + 1.4, 3.3), PINK["light"], sides=12, rot=(0, D90, 0)),
          S("StandTape", (0.3, 0.06, 1.2), (x + 2.9, y + 1.8, 2.3), CREAM["base"])]
    P += [R("KitBox", (1.6, 1.1, 1.0), (x + 3.0, y - 1.8, 0), "#FFFFFF", radius=0.12),
          S("KitBoxLid", (1.7, 1.2, 0.25), (x + 3.0, y - 1.8, 1.0), PINK["base"]),
          S("KitBoxHandle", (0.8, 0.2, 0.25), (x + 3.0, y - 1.8, 1.25), PINK["dark"])]
    P += bandage_icon("KitBoxBand", x + 3.0, y - 1.25, 0.65, 0.9, depth=0.06)
    # crutch leaning against the post (bone-themed humour)
    P += [beam("Crutch", (x - 3.6, y + 2.5, 0), (x - 3.85, y + 2.6, 3.8), 0.22, 0.22, "#C9D3DD"),
          S("CrutchTop", (0.25, 1.0, 0.3), (x - 3.85, y + 2.6, 3.8), PINK["base"])]
    MARKERS["ClinicBed"] = {"pos": [bx + 0.4, by, 2.4], "facing": [1, 0, 0], "note": "respawn pose lies along +x"}
    return P


def pet_pedestals():
    P = []
    for i, (x, y) in enumerate(KIT_POS["Pets"]):
        col = (TEAL, GOLD, ORNG, BLUE)[i]
        P += [S(f"Ped{i}Base", (3.0, 3.0, 0.4), (x, y, 0), STONE["dark"]),
              S(f"Ped{i}Body", (2.4, 2.4, 1.0), (x, y, 0.4), WOOD["base"]),
              S(f"Ped{i}Band", (2.5, 2.5, 0.22), (x, y, 0.85), col["dark"]),
              S(f"Ped{i}Top", (2.9, 2.9, 0.35), (x, y, 1.4), col["base"]),
              S(f"Ped{i}TopTrim", (2.5, 2.5, 0.12), (x, y, 1.75), col["light"]),
              S(f"Ped{i}Glow", (1.6, 0.1, 0.2), (x, y + 1.25, 0.55), NEON_CYAN if i % 2 else NEON_GOLD, emission=3),
              S(f"Ped{i}Plaque", (1.2, 0.12, 0.5), (x, y + 1.46, 1.42), GOLD["base"])]
        for k, (dx, dy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            P.append(S(f"Ped{i}Corner{k}", (0.5, 0.5, 0.5), (x + dx * 1.2, y + dy * 1.2, 0.4), WOOD["deep"]))
        P.append(disc_y(f"Ped{i}Paw", x, y + 1.46, 1.9 - 0.95 + 0.17, 0.18, 0.06, CREAM["base"], sides=8))
        MARKERS[f"PetPedestal{i + 1}"] = {"pos": [x, y, 1.87]}
    return P


def trophy_board():
    x, y = KIT_POS["TrophyBoard"]
    P = [S("TBPostL", (0.7, 0.7, 6.2), (x - 3.6, y - 0.1, 0), WOOD["dark"]),
         S("TBPostR", (0.7, 0.7, 6.2), (x + 3.6, y - 0.1, 0), WOOD["dark"]),
         S("TBFootL", (1.2, 1.2, 0.4), (x - 3.6, y - 0.1, 0), STONE["dark"]),
         S("TBFootR", (1.2, 1.2, 0.4), (x + 3.6, y - 0.1, 0), STONE["dark"]),
         S("TBBack", (6.5, 0.4, 3.9), (x, y - 0.3, 1.75), WOOD["base"])]
    P += [S("TBFrameT", (7.2, 0.6, 0.4), (x, y - 0.2, 5.6), GOLD["base"]),
          S("TBFrameB", (7.2, 0.6, 0.4), (x, y - 0.2, 1.35), GOLD["base"]),
          S("TBFrameL", (0.4, 0.6, 3.85), (x - 3.4, y - 0.2, 1.75), GOLD["dark"]),
          S("TBFrameR", (0.4, 0.6, 3.85), (x + 3.4, y - 0.2, 1.75), GOLD["dark"])]
    # crest: gold bone with little stars on a cream arch
    P += [S("TBCrestBase", (3.6, 0.5, 0.9), (x, y - 0.2, 6.0), WOOD["deep"])]
    P += bone_icon("TBCrestBone", x, y - 0.3, 7.3, 3.0, GOLD["light"], depth=0.4)
    for i, sx in enumerate((-1, 1)):
        P.append(S(f"TBStar{i}", (0.55, 0.3, 0.55), (x + sx * 2.3, y - 0.2, 6.3), GOLD["base"], rot=(0, 0.785, 0)))
        P.append(S(f"TBPostCap{i}", (1.0, 1.0, 0.35), (x + sx * 3.6, y - 0.1, 6.2), GOLD["dark"]))
    # the blank SurfaceGui face (separate mesh, no studs)
    face = S("TrophyBoard", (6.4, 0.14, 3.85), (x, y - 0.1, 1.75), CREAM["light"], studs="none", bevel=0.02)
    P.append(face)
    MARKERS["TrophyBoard"] = {"pos": [x, y + 0.04, 3.675], "size": [6.4, 3.85], "normal": [0, 1, 0],
                              "object": "TrophyBoard", "face": "Front (+Y in Blender)"}
    return P


def owner_sign():
    x, y = KIT_POS["OwnerSign"]
    P = [S("OSFoot", (1.3, 1.3, 0.4), (x, y, 0), STONE["dark"]),
         S("OSPost", (0.6, 0.6, 3.6), (x, y, 0.4), WOOD["dark"]),
         R("MailBody", (1.4, 2.2, 1.1), (x, y - 0.1, 3.9), RED["base"], radius=0.15),
         C("MailTop", 0.7, 0.7, 2.2, (x, y - 1.2, 5.0), RED["base"], sides=12, rot=(-D90, 0, 0)),
         S("MailDoor", (1.2, 0.12, 1.3), (x, y + 1.0, 4.0), RED["dark"]),
         B("MailKnob", (0.16, 0.16, 0.16), (x, y + 1.12, 4.6), GOLD["base"], segments=8, rings=6),
         S("MailFlagPole", (0.15, 0.15, 1.6), (x + 0.8, y - 0.2, 4.3), IRON),
         S("MailFlag", (0.12, 0.9, 0.6), (x + 0.82, y + 0.25, 5.3), GOLD["base"]),
         S("OSArm", (4.2, 0.4, 0.4), (x - 1.8, y, 3.4), WOOD["deep"]),
         S("OSChainL", (0.1, 0.1, 0.5), (x - 3.4, y, 2.9), IRON),
         S("OSChainR", (0.1, 0.1, 0.5), (x - 0.5, y, 2.9), IRON),
         S("OSBoard", (3.6, 0.35, 1.9), (x - 1.95, y - 0.17, 1.0), WOOD["base"]),
         S("OSBordT", (3.9, 0.5, 0.25), (x - 1.95, y - 0.1, 2.9), WOOD["deep"]),
         S("OSBordB", (3.9, 0.5, 0.25), (x - 1.95, y - 0.1, 0.75), WOOD["deep"])]
    face = S("OwnerSign", (3.2, 0.1, 1.6), (x - 1.95, y + 0.05, 1.15), CREAM["light"], studs="none", bevel=0.02)
    P.append(face)
    MARKERS["OwnerSign"] = {"pos": [x - 1.95, y + 0.1, 1.95], "size": [3.2, 1.6], "normal": [0, 1, 0],
                            "object": "OwnerSign", "face": "Front (+Y in Blender)"}
    return P


def kit_ground():
    """Entrance path, fence around sides/back, entrance lamps, little vignettes."""
    rnd = random.Random(21)
    P = []
    # two-tile-wide stone path from the front edge to the building zone (stops at y=3.5)
    for li, px in enumerate((-1.5, 1.5)):
        for k in range(6):
            yy = 18.6 - k * 3.0
            P.append(S(f"PathTile{li}_{k}", (2.85, 2.85, 0.22), (px + rnd.uniform(-0.1, 0.1), yy, 0),
                       ("#E4D3A8", "#D2BE8E")[(k + li) % 2], bevel=0.05, rot=(0, 0, math.radians(rnd.uniform(-5, 5)))))
    for k in range(6):
        for sx in (-1, 1):
            if (k + (sx > 0)) % 2 == 0:
                P.append(R(f"PathEdge{k}_{sx}", (0.8, 0.6, 0.35), (sx * 3.5, 18.0 - k * 3.0, 0), "#B8A47A", radius=0.12,
                           rot=(0, 0, rnd.uniform(0, 3))))
    # entrance arch posts with lanterns
    P += lantern_post("EntryLampL", -4.2, 19.3, h=4.4)
    P += lantern_post("EntryLampR", 3.2, 19.3, h=4.4)
    # timber fence: back + sides (front stays open toward the mountain)
    def fence(prefix, a, b, skip_first=False):
        (ax, ay), (bx, by) = a, b
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / 4.0))
        yaw = math.atan2(by - ay, bx - ax)
        out = []
        for i in range(n + 1):
            t = i / n
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            if i == 0 and skip_first:
                pass
            else:
                out.append(S(f"{prefix}P{i}", (0.6, 0.6, 2.6), (x, y, 0), WOOD["dark"] if i % 2 else WOOD["deep"]))
                out.append(S(f"{prefix}C{i}", (0.8, 0.8, 0.22), (x, y, 2.6), SNOW, bevel=0.08))
            if i < n:
                mx, my = ax + (bx - ax) * (t + 0.5 / n), ay + (by - ay) * (t + 0.5 / n)
                for k, zz in enumerate((0.9, 1.9)):
                    out.append(S(f"{prefix}R{i}_{k}", (L / n - 0.6, 0.3, 0.32), (mx, my, zz), WOOD["base"] if k else WOOD["light"],
                                 rot=(0, 0, yaw)))
        return out
    P += fence("FenceBack", (-23.4, -19.4), (23.4, -19.4))
    P += fence("FenceL", (-23.4, -19.4), (-23.4, 5.0), True)
    P += fence("FenceR", (23.4, -19.4), (23.4, 5.0), True)
    # snowy corner boulders where the fence ends (frames the open front)
    P += boulder("CornerRockL", -22.5, 7.2, 2.2, rnd, moss=False, snow=True)
    P += boulder("CornerRockR", 22.3, 7.0, 2.0, rnd, moss=False, snow=True)
    P += kit.flower_bed("BedFL", (-22.5, 19.2), (-13.5, 19.2), colors=(PINK["base"], GOLD["base"], "#FFFFFF"), rnd=rnd)
    P += kit.flower_bed("BedFR", (11.5, 19.2), (21.5, 19.2), colors=(RED["base"], GOLD["base"], "#B678EA"), rnd=rnd)
    for i, (x, y, w, d) in enumerate(((-21.5, -6.0, 3.4, 2.2), (21.3, 1.5, 2.8, 1.8), (-21.0, 4.5, 2.2, 1.6), (21.0, -17.5, 3.0, 2.0),
                                     (-20.5, -17.6, 2.6, 1.8))):
        P += [R(f"Drift{i}", (w, d, 0.5), (x, y, 0), SNOW, radius=0.2, rot=(0, 0, rnd.uniform(-0.3, 0.3))),
              R(f"DriftTop{i}", (w * 0.55, d * 0.6, 0.35), (x + 0.3, y - 0.1, 0.45), SNOW_D, radius=0.14)]
    MARKERS["Spawn"] = {"pos": [0.0, 7.5, 0.22], "facing": [0, 1, 0], "note": "on the path in front of the building"}
    return P


def build_kit():
    P = []
    section("Lift")
    P += lift_pad()
    section("Clinic")
    P += clinic()
    section("Yard")
    P += pet_pedestals()
    P += trophy_board()
    P += owner_sign()
    P += kit_ground()
    return P


# ---- STAGE 1: Trail Tent ------------------------------------------------------------------------

def stage1():
    rnd = random.Random(101)
    section("Tent")
    P = []
    cx, cy = 0.0, -6.0
    half, rise, L = 6.0, 8.4, 11.5
    a = math.atan2(rise, half)
    Lsl = math.hypot(half, rise) + 0.3
    ca, sa = math.cos(a), math.sin(a)
    zr = rise + 0.35
    P.append(S("TentFloor", (12.6, 12.2, 0.35), (cx, cy, 0), "#3C6E8F"))
    # canvas: 3 strips per side (alternating orange shades) + darker hem + bandage patch
    for s in (-1, 1):
        for k in range(3):
            w = L / 3
            loc = (cx + s * ca * Lsl / 2, cy - L / 2 + w * (k + 0.5), zr - sa * Lsl / 2)
            P.append(S(f"Canvas{s}_{k}", (Lsl, w, 0.32), loc, ORNG["base"] if k % 2 == 0 else ORNG["light"], rot=(0, s * a, 0)))
        lh = Lsl - 0.5
        P.append(S(f"Hem{s}", (0.9, L + 0.2, 0.42), (cx + s * ca * lh, cy, zr - sa * lh), RED["base"], rot=(0, s * a, 0)))
        lp = Lsl * 0.45
        nx, nz = s * sa, ca
        P.append(S(f"Patch{s}", (1.8, 1.2, 0.12), (cx + s * ca * lp + nx * 0.32, cy - 1.8, zr - sa * lp + nz * 0.32),
                   CREAM["base"], rot=(0, s * a, 0.0)))
        P.append(S(f"PatchPad{s}", (0.7, 0.6, 0.14), (cx + s * ca * lp + nx * 0.36, cy - 1.8, zr - sa * lp + nz * 0.36),
                   PINK["base"], rot=(0, s * a, 0.0)))
        # rolled-up door flaps at the front edge
        top = Vector((cx, cy + L / 2 + 0.2, zr - 0.2))
        bot = Vector((cx + s * (half + 0.2), cy + L / 2 + 0.2, 0.4))
        P.append(rod(f"FlapRoll{s}", tuple(bot), tuple(top), 0.42, ORNG["dark"], sides=8))
        P.append(rod(f"FlapTie{s}", tuple(bot.lerp(top, 0.5) + Vector((0, 0, 0))), tuple(bot.lerp(top, 0.53)), 0.5, CREAM["dark"], sides=8))
        # guy ropes + stakes
        for k, yy in enumerate((cy - 3.0, cy + 3.0)):
            ap = Vector((cx + s * ca * Lsl * 0.3, yy, zr - sa * Lsl * 0.3 + 0.3))
            st = Vector((cx + s * (half + 3.0), yy, 0.4))
            P.append(rod(f"Guy{s}_{k}", tuple(ap), tuple(st), 0.06, CREAM["dark"], sides=5))
            P.append(S(f"Stake{s}_{k}", (0.35, 0.35, 0.9), (st.x, st.y, 0), WOOD["deep"]))
    # back wall (triangle) + dark interior front so the opening reads as depth
    P.append(prism("TentBack", [(-half, 0.35), (half, 0.35), (0, zr - 0.1)], 0.3, "y", (cx, cy - L / 2, 0), ORNG["dark"]))
    P.append(prism("TentInside", [(-half + 0.7, 0.36), (half - 0.7, 0.36), (0, zr - 1.0)], 0.1, "y", (cx, cy - L / 2 + 0.32, 0),
                   "#7A3A12"))
    # A-frame poles front & back + ridge pole + flag
    for k, yy in enumerate((cy + L / 2 + 0.45, cy - L / 2 - 0.25)):
        P.append(rod(f"PoleL{k}", (cx - half - 0.1, yy, 0), (cx + 0.5, yy, zr + 0.9), 0.2, WOOD["dark"], sides=6))
        P.append(rod(f"PoleR{k}", (cx + half + 0.1, yy, 0), (cx - 0.5, yy, zr + 0.9), 0.2, WOOD["dark"], sides=6))
    P.append(rod("RidgePole", (cx, cy - L / 2 - 0.8, zr + 0.25), (cx, cy + L / 2 + 0.9, zr + 0.25), 0.22, WOOD["deep"], sides=6))
    P.append(S("FlagPole", (0.18, 0.18, 2.4), (cx, cy + L / 2 + 0.45, zr + 0.6), IRON))
    P.append(prism("Flag", [(0, 0), (1.6, 0.45), (0, 0.9)], 0.1, "y", (cx + 0.1, cy + L / 2 + 0.4, zr + 2.0), GOLD["base"]))
    # hanging lantern inside + sleeping bag poking out + mat
    P += [rod("LanternWire", (cx, cy + 1.0, zr - 0.4), (cx, cy + 1.0, zr - 1.5), 0.04, IRON, sides=4),
          S("LanternCap", (0.7, 0.7, 0.2), (cx, cy + 1.0, zr - 1.7), IRON),
          B("LanternGlow", (0.3, 0.3, 0.36), (cx, cy + 1.0, zr - 2.1), LAMP, segments=10, rings=6, emission=5)]
    P += [R("BagBody", (2.0, 6.2, 0.7), (cx - 0.8, cy + 2.4, 0.35), TEAL["base"], radius=0.25),
          R("BagHood", (2.1, 1.3, 0.85), (cx - 0.8, cy - 0.7, 0.35), TEAL["dark"], radius=0.3),
          R("BagPillow", (1.6, 0.9, 0.5), (cx - 0.8, cy - 0.5, 1.05), CREAM["light"], radius=0.2),
          S("BagZip", (0.18, 5.6, 0.12), (cx + 0.15, cy + 2.6, 1.0), GOLD["base"], bevel=0.03),
          S("BagFlap", (1.0, 2.2, 0.2), (cx - 1.4, cy + 4.4, 1.0), TEAL["light"], rot=(0, -0.2, 0.15))]
    P += [S("Mat", (3.4, 2.4, 0.12), (cx + 1.9, cy + 6.6, 0), RED["dark"], bevel=0.03),
          S("MatStripe", (3.0, 0.4, 0.14), (cx + 1.9, cy + 6.6, 0), GOLD["base"], bevel=0.02)]
    # backpack leaning by the door with bedroll + rope coil
    bx, by = cx + 4.6, cy + 7.0
    P += [R("Pack", (1.6, 1.1, 2.2), (bx, by, 0), RED["base"], radius=0.25, rot=(0.15, 0, 0.3)),
          R("PackPocket", (1.1, 0.4, 0.9), (bx + 0.18, by + 0.55, 0.3), RED["dark"], radius=0.12, rot=(0.15, 0, 0.3)),
          C("PackRoll", 0.42, 0.42, 1.9, (bx - 0.95, by - 0.3, 2.35), BLUE["base"], sides=10, rot=(0, D90, 0.3)),
          S("PackStrap", (0.25, 1.2, 0.12), (bx - 0.1, by - 0.1, 2.75), "#3A2A1E"),
          ring("RopeCoil", 0.8, 0.45, 0.3, (bx + 1.8, by - 1.3, 0), CREAM["dark"], sides=14),
          ring("RopeCoil2", 0.75, 0.45, 0.3, (bx + 1.8, by - 1.3, 0.3), "#D9B77E", sides=14)]
    section("Campsite")
    # campfire ring + teepee logs + neon flames + log seats + marshmallow stick
    fx, fy = cx - 9.4, cy + 7.6
    for i in range(9):
        aa = 2 * math.pi * i / 9 + rnd.uniform(-0.1, 0.1)
        s = rnd.uniform(0.75, 1.0)
        P.append(R(f"FireStone{i}", (s, s * 0.85, s * 0.6), (fx + math.cos(aa) * 1.65, fy + math.sin(aa) * 1.65, 0),
                   STONE["base"] if i % 2 else STONE["dark"], radius=0.15, rot=(0, 0, aa)))
    P.append(C("FireAsh", 1.35, 1.35, 0.15, (fx, fy, 0), "#4A4038", sides=14))
    for i in range(5):
        aa = 2 * math.pi * i / 5
        P.append(rod(f"FireLog{i}", (fx + math.cos(aa) * 1.1, fy + math.sin(aa) * 1.1, 0.15), (fx, fy, 1.6), 0.2,
                     LOGC["dark"] if i % 2 else LOGC["base"], sides=6))
    for i, (s, z, col) in enumerate(((1.1, 0.25, NEON_ORANGE), (0.8, 0.9, "#FFB43B"), (0.5, 1.5, NEON_GOLD))):
        P.append(S(f"Flame{i}", (s, s, s * 1.1), (fx + 0.05 * i, fy - 0.05 * i, z), col, emission=4, rot=(0.3, 0.3, 0.6 * i)))
    for k, (dx, dy, yaw) in enumerate(((-3.0, 0.2, 1.5), (0.9, 3.0, 0.15))):
        lx, ly = fx + dx, fy + dy
        P += [C(f"Seat{k}", 0.55, 0.55, 2.6, (lx - 1.3 * math.cos(yaw), ly - 1.3 * math.sin(yaw), 0.55), LOGC["base"], sides=8,
                rot=(0, D90, yaw)),
              S(f"SeatChock{k}", (0.6, 0.6, 0.3), (lx, ly, 0), LOGC["deep"], rot=(0, 0, yaw))]
    P += [C("Stump", 0.75, 0.8, 1.0, (fx + 2.9, fy - 0.6, 0), LOGC["base"], sides=10),
          C("StumpTop", 0.65, 0.65, 0.08, (fx + 2.9, fy - 0.6, 1.0), CREAM["dark"], sides=10),
          rod("Stick", (fx + 2.9, fy - 0.6, 1.1), (fx + 0.9, fy - 0.2, 2.1), 0.06, WOOD["deep"], sides=5),
          R("Marshmallow", (0.4, 0.4, 0.5), (fx + 0.9, fy - 0.2, 1.85), "#FFFFFF", radius=0.12),
          C("Kettle", 0.45, 0.35, 0.6, (fx - 1.0, fy + 1.0, 0.15), BLUE["dark"], sides=10),
          S("KettleHandle", (0.7, 0.1, 0.1), (fx - 1.0, fy + 1.0, 0.95), IRON)]
    # first-aid crate (bandage icon, no cross)
    kx, ky = cx + 9.6, cy + 7.2
    P += [S("Crate", (2.4, 2.0, 1.6), (kx, ky, 0), WOOD["base"]),
          S("CrateLid", (2.6, 2.2, 0.3), (kx, ky, 1.6), WOOD["dark"])]
    for i, dx in enumerate((-1.05, 1.05)):
        P.append(S(f"CrateSlat{i}", (0.3, 2.15, 1.6), (kx + dx, ky, 0), WOOD["deep"]))
    P.append(S("CrateBand", (2.2, 0.12, 1.0), (kx, ky + 1.02, 0.3), "#FFFFFF"))
    P += bandage_icon("CrateIcon", kx, ky + 1.05, 0.8, 1.2, depth=0.1)
    P += [S("CrateTin", (1.0, 0.8, 0.6), (kx - 0.3, ky, 1.9), "#FFFFFF"), S("CrateTinLid", (1.05, 0.85, 0.15), (kx - 0.3, ky, 2.5), PINK["base"])]
    # wooden trail sign: post + 2 arrow boards (to the peak +y, and to camp)
    sx, sy = cx + 12.6, cy + 3.5
    P += [S("TrailPost", (0.55, 0.55, 5.2), (sx, sy, 0), WOOD["dark"]),
          S("TrailCap", (0.85, 0.85, 0.3), (sx, sy, 5.2), WOOD["deep"]),
          S("TrailArrowA", (0.3, 2.6, 0.9), (sx, sy + 1.3, 3.9), WOOD["light"]),
          S("TrailArrowB", (2.4, 0.3, 0.8), (sx - 1.3, sy, 2.8), WOOD["base"])]
    bm_pts = [(sy + 2.6, 3.9), (sy + 3.4, 4.35), (sy + 2.6, 4.8)]
    bm = bmesh.new()
    a0 = [bm.verts.new((sx - 0.15, u, z)) for u, z in bm_pts]
    a1 = [bm.verts.new((sx + 0.15, u, z)) for u, z in bm_pts]
    bm.faces.new(a0)
    bm.faces.new(list(reversed(a1)))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((a0[i], a0[j], a1[j], a1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.append(vb._finish(vb._new_mesh_object("TrailArrowTip", bm), WOOD["light"], 0, "all", None))
    P.append(prism("TrailArrowTipB", [(-0.4, 2.8), (0.4, 2.8), (0, 3.6)], 0.3, "y", (sx - 2.5, sy - 0.15, 0), WOOD["base"]))
    bpy.data.objects[P[-1].name].rotation_euler = (0, -D90, 0)
    bpy.data.objects.remove(P.pop())
    P.append(prism("TrailArrowTipB", [(-2.9, 2.8), (-3.4, 3.2), (-2.9, 3.6)], 0.3, "y", (sx + 0.4, sy - 0.15, 0), WOOD["base"]))
    P += mountain_icon("TrailIconPeak", sx + 0.16, sy + 1.0, 3.98, 0.8, depth=0.08)
    for i in (0, 1):
        bpy.data.objects[P[-1 - i].name].rotation_euler = (0, 0, 0)
    P += [S("TrailIconRot", (0.08, 0.9, 0.12), (sx + 0.18, sy + 1.7, 4.0), RED["base"])]
    # back-of-tent vignette: two small pines + firewood bundle + rock
    P += pine("PineA", -16.0, -15.5, 12, rnd)
    P += pine("PineB", 20.0, -16.0, 10, random.Random(5))
    P += pine("PineC", -20.0, -9.0, 8, random.Random(6))
    P += boulder("TentRock", 12.0, -4.5, 1.8, rnd)
    for i in range(4):
        P.append(C(f"Kindling{i}", 0.3, 0.3, 1.8, (-12.2, cy + 1.0 + i * 0.62, 0.3 + (i % 2) * 0.45), LOGC["base"] if i % 2 else LOGC["dark"],
                   sides=7, rot=(0, D90, 0)))
    # clothesline vignette: bandages + socks drying between two poles (Bone Clinic humour)
    for k, yy in enumerate((-15.0, -8.0)):
        P += [S(f"LinePost{k}", (0.45, 0.45, 5.0), (-13.0, yy, 0), WOOD["dark"]),
              S(f"LinePostFoot{k}", (1.0, 1.0, 0.3), (-13.0, yy, 0), STONE["dark"])]
    P.append(rod("Line", (-13.0, -15.0, 4.7), (-13.0, -8.0, 4.7), 0.05, CREAM["dark"], sides=4))
    for i, (col, ln) in enumerate(((CREAM["base"], 2.2), (PINK["base"], 1.6), (CREAM["light"], 2.6), (RED["base"], 1.3), (PINK["light"], 2.0))):
        yy = -14.2 + i * 1.35
        P.append(S(f"LineCloth{i}", (0.1, 0.9, ln), (-13.0, yy, 4.7 - ln), col, bevel=0.02, rot=(0.06 * (i - 2), 0, 0)))
        P.append(S(f"LinePeg{i}", (0.16, 0.2, 0.35), (-13.0, yy, 4.5), WOOD["light"], bevel=0.02))
    # practice-crash vignette: little wooden ramp into a hay-bale target (what this game is about)
    P += [prism("PracticeRamp", [(-9.5, 0), (-5.5, 0), (-9.5, 1.6)], 2.6, "x", (14.9, 0, 0), WOOD["base"]),
          S("PracticeRampLip", (2.6, 0.5, 0.3), (16.2, -9.55, 1.4), ORNG["base"])]
    for i, (dx, dz) in enumerate(((0, 0), (2.4, 0), (1.2, 1.4))):
        P += [S(f"Hay{i}", (2.3, 1.6, 1.4), (15.0 + dx, -12.0, dz), "#F2C14E"),
              S(f"HayBand{i}", (0.25, 1.65, 1.42), (15.0 + dx - 0.6, -12.0, dz), "#C98A2E")]
    P += [C("TargetRing", 1.1, 1.1, 0.12, (16.2, -11.22, 3.4), RED["base"], sides=16, rot=(-D90, 0, 0)),
          C("TargetMid", 0.7, 0.7, 0.14, (16.2, -11.19, 3.4), "#FFFFFF", sides=16, rot=(-D90, 0, 0)),
          C("TargetEye", 0.32, 0.32, 0.16, (16.2, -11.16, 3.4), RED["base"], sides=12, rot=(-D90, 0, 0))]
    MARKERS.setdefault("StageDoors", {})["1"] = [cx, cy + L / 2 + 1.0, 0.35]
    return P


# ---- STAGE 2: Log Cabin -------------------------------------------------------------------------

def log_walls(prefix, x0, x1, y0, y1, z0, rows, openings, rnd):
    """Log walls with notched (interleaved, overhanging) corners. openings: {"front"/"back"/"left"/"right":
    [(u0, u1, z0, z1)]}; logs are split around openings. Returns parts and actual opening extents."""
    P, ext = [], {}
    over = 0.75
    for wall in ("front", "back", "left", "right"):
        holes = openings.get(wall, [])
        alongx = wall in ("front", "back")
        off = 0.0 if alongx else 0.5
        ext[wall] = []
        for i in range(rows):
            zc = z0 + 0.5 + off + i
            col = LOGC["base"] if (i + (0 if alongx else 1)) % 2 == 0 else LOGC["light"]
            u0, u1 = (x0 - over, x1 + over) if alongx else (y0 - over, y1 + over)
            cut = [(h[0], h[1]) for h in holes if zc + 0.45 > h[2] and zc - 0.45 < h[3]]
            segs = _split(u0, u1, cut) if cut else [(u0, u1)]
            for k, (a, b) in enumerate(segs):
                capa, capb = abs(a - u0) < 1e-6, abs(b - u1) < 1e-6
                nm = f"{prefix}{wall}{i}_{k}"
                if alongx:
                    yy = y1 if wall == "front" else y0
                    P.append(C(nm, 0.55, 0.55, b - a, (a, yy, zc), col, sides=8, rot=(0, D90, 0)))
                    if capa:
                        P.append(C(nm + "Ca", 0.4, 0.4, 0.08, (a - 0.05, yy, zc), CREAM["dark"], sides=8, rot=(0, D90, 0)))
                    if capb:
                        P.append(C(nm + "Cb", 0.4, 0.4, 0.08, (b - 0.03, yy, zc), CREAM["dark"], sides=8, rot=(0, D90, 0)))
                else:
                    xx = x0 if wall == "left" else x1
                    P.append(C(nm, 0.55, 0.55, b - a, (xx, a, zc), col, sides=8, rot=(-D90, 0, 0)))
                    if capa:
                        P.append(C(nm + "Ca", 0.4, 0.4, 0.08, (xx, a - 0.05, zc), CREAM["dark"], sides=8, rot=(-D90, 0, 0)))
                    if capb:
                        P.append(C(nm + "Cb", 0.4, 0.4, 0.08, (xx, b - 0.03, zc), CREAM["dark"], sides=8, rot=(-D90, 0, 0)))
        for h in holes:
            rz = [z0 + 0.5 + off + i for i in range(rows) if z0 + 0.5 + off + i + 0.45 > h[2] and z0 + 0.5 + off + i - 0.45 < h[3]]
            ext[wall].append((h[0], h[1], min(rz) - 0.5, max(rz) + 0.5))
    return P, ext


def stage2():
    rnd = random.Random(202)
    section("Cabin")
    P = []
    x0, x1, y0, y1 = -8.0, 8.0, -16.0, -4.0
    z0 = 1.0
    rows = 7
    P += [S("Found", (17.4, 13.4, 1.0), (0, (y0 + y1) / 2, 0), STONE["base"]),
          S("FoundLip", (17.8, 13.8, 0.25), (0, (y0 + y1) / 2, 0.75), STONE["dark"])]
    for i in range(10):  # chunky exposed foundation stones
        side = i % 2
        xx = rnd.uniform(x0 + 1, x1 - 1)
        P.append(R(f"FoundStone{i}", (rnd.uniform(1.0, 1.8), 0.5, 0.6), (xx, y1 + 0.75 if side else y0 - 0.75, 0.05),
                   STONE["light"] if i % 3 else STONE["dark"], radius=0.12))
    openings = {"front": [(-1.5, 1.5, 1.0, 6.0), (-6.4, -3.2, 3.0, 6.0), (3.2, 6.4, 3.0, 6.0)],
                "left": [(-11.8, -8.2, 3.0, 6.0)], "back": [(-2.0, 2.0, 3.5, 6.0)], "right": [(-8.0, -5.6, 3.0, 6.0)]}
    lw, ext = log_walls("Log", x0, x1, y0, y1, z0, rows, openings, rnd)
    P += lw
    # interior: floor, back wall inner face, stone fireplace (glow), bunk, table with lantern, light
    P += [S("FloorIn", (15.0, 11.0, 0.2), (0, -10, 1.0), WOOD["dark"]),
          S("RugIn", (5.0, 3.5, 0.08), (0, -8.5, 1.2), RED["base"], bevel=0.02),
          S("RugInB", (4.0, 2.5, 0.1), (0, -8.5, 1.2), GOLD["base"], bevel=0.02),
          S("FirePlace", (4.6, 1.6, 4.4), (0, -14.9, 1.2), STONE["base"]),
          S("FirePlaceMantel", (5.4, 2.0, 0.4), (0, -14.8, 5.0), WOOD["deep"]),
          S("FireHole", (2.4, 0.3, 1.8), (0, -14.15, 1.2), "#2A2220"),
          S("FireGlow", (1.8, 0.4, 1.0), (0, -13.95, 1.3), NEON_ORANGE, emission=5),
          S("FireGlowB", (1.0, 0.45, 0.6), (0, -13.85, 1.5), NEON_GOLD, emission=5)]
    P += [S("BunkFrame", (5.0, 2.4, 0.5), (-4.8, -14.4, 2.2), WOOD["base"]),
          R("BunkMattress", (4.8, 2.2, 0.5), (-4.8, -14.4, 2.7), CREAM["light"], radius=0.15),
          R("BunkBlanket", (3.0, 2.3, 0.3), (-4.0, -14.4, 3.0), BLUE["base"], radius=0.1),
          S("BunkLegA", (0.4, 0.4, 1.2), (-7.0, -13.4, 1.2), WOOD["deep"]),
          S("BunkLegB", (0.4, 0.4, 1.2), (-2.6, -13.4, 1.2), WOOD["deep"]),
          S("Table", (2.4, 1.6, 0.25), (4.6, -11.0, 3.0), WOOD["light"]),
          S("TableLeg", (0.4, 0.4, 1.8), (4.6, -11.0, 1.2), WOOD["deep"]),
          B("TableLantern", (0.35, 0.35, 0.45), (4.6, -11.0, 3.7), LAMP, segments=10, rings=6, emission=4),
          S("TrophyMini", (0.8, 0.8, 0.5), (1.5, -14.6, 5.4), GOLD["dark"])]
    P += bone_3d("MantelBone", (-1.2, -14.4, 5.75), 1.6, CREAM["base"])
    P += interior_light("CabinLight", 0, -10, 7.6, 3.0, 1.2)
    # windows in the log openings (frames proud of the logs) + flower-free shutters
    for k, (u0, u1, za, zb) in enumerate(ext["front"][1:]):
        P += window(f"WinF{k}", (u0 + u1) / 2, y1 + 0.35, za + 0.3, u1 - u0 - 0.2, zb - za - 0.6, "+y", frame=CREAM["base"],
                    sill=WOOD["deep"], mullions=1, shutters=GRN)
    u0, u1, za, zb = ext["left"][0]
    P += window("WinL", x0 - 0.35, (u0 + u1) / 2, za + 0.3, u1 - u0 - 0.2, zb - za - 0.6, "-x", frame=CREAM["base"], sill=WOOD["deep"])
    u0, u1, za, zb = ext["right"][0]
    P += window("WinR", x1 + 0.35, (u0 + u1) / 2, za + 0.3, u1 - u0 - 0.2, zb - za - 0.6, "+x", frame=CREAM["base"], sill=WOOD["deep"])
    u0, u1, za, zb = ext["back"][0]
    P += window("WinB", (u0 + u1) / 2, y0 - 0.35, za + 0.3, u1 - u0 - 0.2, zb - za - 0.6, "-y", frame=CREAM["base"], sill=WOOD["deep"])
    u0, u1, za, zb = ext["front"][0]
    P += door("Door", 0, y1 + 0.3, 1.0, w=u1 - u0 - 0.4, h=zb - za - 0.6, col=GRN, frame=WOOD["deep"], lamps=True, step=False, mat=False)
    # stepped log gables (front + back) under the roof
    top = z0 + rows + 0.5
    half, rise = 8.0, 5.2
    for k, yy in enumerate((y1, y0)):
        for i in range(5):
            hw = half * (1 - (i + 0.7) / 5.4)
            P.append(C(f"Gable{k}_{i}", 0.55, 0.55, 2 * hw, (-hw, yy, top + 0.5 + i), LOGC["light"] if i % 2 else LOGC["base"],
                       sides=8, rot=(0, D90, 0)))
    # round vent window in the front gable
    P += [disc_y("GableVent", 0, y1 + 0.35, top + 2.2, 0.75, 0.15, GLASS, studs="none"),
          ring("GableVentRim", 1.0, 0.75, 0.3, (0, 0, 0), CREAM["base"], sides=16)]
    vr = P[-1]
    vr.rotation_euler = (-D90, 0, 0)
    vr.location = (0, y1 + 0.3, top + 2.2)
    vb.restud([vr])
    section("CabinRoof")
    # roof: forest-green shingles, partial snow
    P += roof("Roof", 0, -10, top, half + 0.6, 15.6, rise + 0.4, ridge="y", col=GRN, ov=1.4, bands=4, snow=0.62, rnd=rnd)
    # chimney (stone, stepped) on the right wall
    P += [S("Chim0", (2.4, 2.6, 6.0), (9.4, -11.0, 0), STONE["base"]),
          S("Chim1", (2.0, 2.2, 10.0), (9.4, -11.0, 6.0), STONE["dark"]),
          S("ChimBand", (2.4, 2.6, 0.4), (9.4, -11.0, 12.0), STONE["light"]),
          S("ChimCap", (2.6, 2.8, 0.5), (9.4, -11.0, 16.0), STONE["deep"]),
          S("ChimSnow", (2.3, 2.5, 0.35), (9.4, -11.0, 16.5), SNOW, bevel=0.1)]
    for i in range(5):
        P.append(R(f"ChimStone{i}", (0.9, 0.3, 0.55), (9.4 + rnd.uniform(-0.5, 0.5), -9.65, 1.0 + i * 2.6), STONE["light"], radius=0.1))
    section("Porch")
    # porch: plank deck + steps + posts + lean-to roof + railings + hanging sign
    py0, py1 = -4.0, -0.6
    for i in range(6):
        P.append(S(f"Deck{i}", (14.0, (py1 - py0) / 6 - 0.04, 0.3), (0, py0 + (i + 0.5) * (py1 - py0) / 6, 0.7),
                   WOOD["base"] if i % 2 else WOOD["light"], bevel=0.03))
    P.append(S("DeckBeam", (14.4, 0.5, 0.7), (0, py1 - 0.25, 0.0), WOOD["deep"]))
    for i in range(2):
        P.append(S(f"Step{i}", (3.2, 0.9, 0.35), (0, py1 + 0.45 + i * 0.9, 0.35 - i * 0.35), STONE["light"] if i else STONE["base"]))
    for i, px in enumerate((-6.7, -2.2, 2.2, 6.7)):
        P.append(S(f"PorchPost{i}", (0.6, 0.6, 5.4), (px, py1 - 0.4, 1.0), LOGC["dark"]))
        P.append(S(f"PorchBracket{i}", (0.4, 0.9, 0.4), (px, py1 - 0.85, 5.9), LOGC["deep"], rot=(0.6, 0, 0)))
    P.append(S("PorchBeam", (14.6, 0.7, 0.6), (0, py1 - 0.4, 6.4), LOGC["deep"]))
    pa = math.atan2(1.0, 4.2)
    for i in range(3):
        P.append(S(f"PorchRoof{i}", (15.0 / 3, 4.9, 0.4), (-5.0 + i * 5.0, -2.1, 7.25), GRN["base"] if i % 2 else GRN["dark"],
                   rot=(pa, 0, 0)))
    P.append(S("PorchRoofSnow", (14.6, 2.4, 0.4), (0, -3.1, 7.6), SNOW, rot=(pa, 0, 0), bevel=0.1))
    P += snow_lumps("PorchLump", [(-6.5 + i * 2.6, 0.1, 6.95) for i in range(6)], rnd, size=0.6)
    P += railing("RailL", (-6.7, py1 - 0.4), (-2.2, py1 - 0.4), 1.0, h=1.4, col=LOGC)
    P += railing("RailR", (2.2, py1 - 0.4), (6.7, py1 - 0.4), 1.0, h=1.4, col=LOGC)
    P += [S("SignChainL", (0.1, 0.1, 0.8), (-2.0, py1 - 0.2, 5.6), IRON), S("SignChainR", (0.1, 0.1, 0.8), (2.0, py1 - 0.2, 5.6), IRON)]
    P += sign_board("CabinSign", 0, py1 - 0.35, 4.6, 4.6, 1.0, board=WOOD)
    P += bone_icon("CabinSignBone", -1.2, py1 + 0.0, 5.1, 1.4, CREAM["light"], rot=0.3)
    P += mountain_icon("CabinSignPeak", 1.2, py1 + 0.0, 4.75, 1.3, depth=0.12)
    # rocking chair on the porch + lantern + barrel
    P += [S("ChairSeat", (1.6, 1.5, 0.3), (-4.5, -2.2, 2.2), RED["base"]),
          S("ChairBack", (1.6, 0.3, 1.8), (-4.5, -2.95, 2.5), RED["dark"], rot=(-0.15, 0, 0)),
          S("ChairRockL", (0.25, 1.9, 0.3), (-5.2, -2.2, 1.0), WOOD["deep"], rot=(0.1, 0, 0)),
          S("ChairRockR", (0.25, 1.9, 0.3), (-3.8, -2.2, 1.0), WOOD["deep"], rot=(0.1, 0, 0)),
          S("ChairLegs", (1.6, 1.4, 0.9), (-4.5, -2.2, 1.3), WOOD["dark"]),
          C("Barrel", 0.75, 0.7, 1.6, (5.0, -2.1, 1.0), WOOD["base"], sides=12),
          C("BarrelHoop", 0.79, 0.79, 0.2, (5.0, -2.1, 1.3), IRON, sides=12),
          C("BarrelHoopB", 0.76, 0.76, 0.2, (5.0, -2.1, 2.2), IRON, sides=12),
          C("BarrelLid", 0.66, 0.66, 0.1, (5.0, -2.1, 2.6), WOOD["light"], sides=12)]
    section("Yard")
    # woodpile under a lean-to on the left wall
    wx = -10.8
    P += [S("WoodRackBase", (2.4, 6.2, 0.4), (wx, -10.0, 0), WOOD["deep"]),
          S("WoodRackPostF", (0.4, 0.4, 4.4), (wx - 1.0, -7.1, 0.4), WOOD["deep"]),
          S("WoodRackPostB", (0.4, 0.4, 4.4), (wx - 1.0, -12.9, 0.4), WOOD["deep"]),
          S("WoodRackRoof", (3.2, 7.0, 0.35), (wx + 0.1, -10.0, 4.8), GRN["dark"], rot=(0, 0.35, 0)),
          S("WoodRackSnow", (2.6, 6.6, 0.3), (wx + 0.05, -10.0, 5.15), SNOW, rot=(0, 0.35, 0), bevel=0.1)]
    for r in range(4):
        for c in range(6 - (r % 2)):
            yy = -12.4 + c * 0.95 + (0.47 if r % 2 else 0)
            col = LOGC["base"] if (r + c) % 3 else LOGC["light"]
            P.append(C(f"WoodLog{r}_{c}", 0.44, 0.44, 1.9, (wx - 0.95, yy, 0.85 + r * 0.82), col, sides=7, rot=(0, D90, 0)))
            P.append(C(f"WoodEnd{r}_{c}", 0.32, 0.32, 0.06, (wx + 0.94, yy, 0.85 + r * 0.82), CREAM["dark"], sides=7, rot=(0, D90, 0)))
    P += [C("ChopStump", 0.9, 1.0, 1.1, (-12.0, -3.0, 0), LOGC["base"], sides=10),
          C("ChopStumpTop", 0.8, 0.8, 0.08, (-12.0, -3.0, 1.1), CREAM["dark"], sides=10),
          beam("AxeHandle", (-12.0, -3.0, 1.15), (-11.6, -2.6, 2.6), 0.18, 0.18, WOOD["light"]),
          S("AxeHead", (0.9, 0.2, 0.55), (-11.45, -2.45, 2.45), "#C9D3DD", rot=(0, 0, 0.78))]
    # sled leaning on the right side + pines behind
    P += [S("SledBed", (1.5, 0.25, 3.6), (11.6, -5.6, 0.3), RED["base"], rot=(-0.25, 0, 0)),
          S("SledRunL", (0.12, 0.5, 3.9), (11.0, -5.4, 0.0), IRON, rot=(-0.25, 0, 0)),
          S("SledRunR", (0.12, 0.5, 3.9), (12.2, -5.4, 0.0), IRON, rot=(-0.25, 0, 0))]
    P += pine("CabPineA", -15.5, -15.5, 13, rnd)
    P += pine("CabPineB", 15.0, -16.0, 11, random.Random(9))
    P += boulder("CabRock", 16.5, -7.5, 2.0, rnd)
    MARKERS.setdefault("StageDoors", {})["2"] = [0, 0.6, 0.7]
    return P


# ---- STAGE 3: Ski Lodge -------------------------------------------------------------------------

def stage3():
    rnd = random.Random(303)
    section("LodgeShell")
    P = []
    x0, x1, y0, y1 = -11.0, 11.0, -17.0, -5.0
    th = 0.8
    yc = (y0 + y1) / 2
    W, D = x1 - x0, y1 - y0
    # stone plinth + ground floor (stone-clad lower band) + upper floor wood
    P += [S("Plinth", (W + 1.2, D + 1.2, 1.2), (0, yc, 0), STONE["base"]),
          S("PlinthLip", (W + 1.6, D + 1.6, 0.3), (0, yc, 1.2), STONE["dark"])]
    f1, f2, top = 1.5, 8.5, 15.5
    open_front1 = [(-9.0, -1.4, 2.4, 6.9), (1.0, 3.8, f1, 6.3), (5.4, 9.0, 2.8, 6.4)]
    open_front2 = [(-8.6, -5.4, 10.0, 13.6), (-3.6, -0.4, 10.0, 13.6), (1.4, 5.0, f2 + 0.2, 13.6), (6.4, 9.2, 10.0, 13.6)]
    P += wall_openings("FrontWall", "x", y1 - th / 2, x0, x1, f1, top, th, open_front1 + open_front2, WOOD["base"])
    P += wall_openings("BackWall", "x", y0 + th / 2, x0, x1, f1, top, th, [(-3, 3, 10.0, 13.6)], WOOD["base"])
    P += wall_openings("LeftWall", "y", x0 + th / 2, y0 + th, y1 - th, f1, top, th, [(-13.5, -9.0, 3.0, 6.5), (-13.5, -9.0, 10, 13.6)], WOOD["base"])
    P += wall_openings("RightWall", "y", x1 - th / 2, y0 + th, y1 - th, f1, top, th, [(-13.5, -9.0, 10, 13.6)], WOOD["base"])
    # siding look: alternating-shade horizontal battens on blank wall stretches + corner posts + trim bands
    for i, (zz, col) in enumerate(((f1, STONE["dark"]), (f2 - 0.3, WOOD["deep"]), (top - 0.5, WOOD["deep"]))):
        hh = 0.9 if i == 0 else 0.6
        P += [S(f"BandF{i}", (W + 0.6, 0.35, hh), (0, y1 + 0.17, zz), col),
              S(f"BandB{i}", (W + 0.6, 0.35, hh), (0, y0 - 0.17, zz), col),
              S(f"BandL{i}", (0.35, D + 0.3, hh), (x0 - 0.17, yc, zz), col),
              S(f"BandR{i}", (0.35, D + 0.3, hh), (x1 + 0.17, yc, zz), col)]
    # band 0 sits over the ground-floor front glass bottom -> keep it only below the openings (z 1.5-2.4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(S(f"Corner{sx}{sy}", (1.2, 1.2, top - f1 + 0.4), (sx * (W / 2 + 0.1), yc + sy * (D / 2 + 0.1), f1 - 0.2), WOOD["deep"]))
    for i in range(6):  # horizontal siding battens on the side walls (lower floor)
        zz = 2.6 + i * 0.95
        if not (3.0 <= zz <= 6.5):
            P.append(S(f"SideBat{i}", (0.2, D - 2.4, 0.3), (x1 + 0.1, yc, zz), WOOD["light"]))
        P.append(S(f"SideBatR{i}", (0.2, D - 2.4, 0.3), (x1 + 0.1, yc, zz + 7.0), WOOD["light"]))
    for i in range(6):
        zz = 2.6 + i * 0.95
        if not (3.0 <= zz <= 6.7):
            P.append(S(f"SideBatL{i}", (0.2, D - 2.4, 0.3), (x0 - 0.1, yc, zz), WOOD["light"]))
    # ground floor: big trophy display window (2 mullions) + door + side window
    P += window("Display", -5.2, y1 + 0.05, 2.4, 7.6, 4.5, "+y", frame=CREAM["base"], sill=WOOD["deep"], mullions=2)
    P += door("LodgeDoor", 2.4, y1 + 0.05, f1, w=2.6, h=4.6, col=RED, frame=WOOD["deep"], step=False, mat=False)
    P += window("WinG", 7.2, y1 + 0.05, 2.8, 3.6, 3.6, "+y", frame=CREAM["base"], sill=WOOD["deep"])
    P += window("WinGL", x0 - 0.05, -11.25, 3.0, 4.5, 3.5, "-x", frame=CREAM["base"], sill=WOOD["deep"])
    # upper floor windows + balcony door (glass)
    for k, (a, b) in enumerate(((-8.6, -5.4), (-3.6, -0.4), (6.4, 9.2))):
        P += window(f"WinU{k}", (a + b) / 2, y1 + 0.05, 10.0, b - a, 3.6, "+y", frame=CREAM["base"],
                    sill=WOOD["deep"], shutters=RED if k < 2 else None)
    P += window("BalcDoor", 3.2, y1 + 0.05, f2 + 0.2, 3.6, 5.4, "+y", frame=CREAM["base"], mullions=1)
    P += window("WinUB", 0, y0 - 0.05, 10.0, 6.0, 3.6, "-y", frame=CREAM["base"], sill=WOOD["deep"])
    for k, nrm, xx in (("L", "-x", x0 - 0.05), ("R", "+x", x1 + 0.05)):
        P += window(f"WinU{k}", xx, -11.25, 10.0, 4.5, 3.6, nrm, frame=CREAM["base"], sill=WOOD["deep"])
    section("LodgeInterior")
    # interior: floors, trophy shelf behind the display glass, fireplace glow, lights
    P += [S("Floor1", (W - 1.6, D - 1.6, 0.2), (0, yc, f1), WOOD["dark"]),
          S("Floor2", (W - 1.6, D - 1.6, 0.4), (0, yc, f2 - 0.4), WOOD["dark"]),
          S("ShelfBack", (8.0, 0.4, 5.4), (-5.2, -8.4, f1 + 0.2), RED["dark"])]
    for i in range(3):
        zz = f1 + 0.9 + i * 1.6
        P.append(S(f"Shelf{i}", (8.0, 1.4, 0.25), (-5.2, -7.6, zz), WOOD["light"]))
        for k in range(4):
            tx = -8.2 + k * 2.0
            if (i + k) % 2 == 0:
                P += [S(f"Cup{i}_{k}B", (0.6, 0.6, 0.25), (tx, -7.6, zz + 0.25), GOLD["dark"]),
                      C(f"Cup{i}_{k}S", 0.12, 0.12, 0.3, (tx, -7.6, zz + 0.5), GOLD["base"], sides=8),
                      C(f"Cup{i}_{k}C", 0.25, 0.42, 0.5, (tx, -7.6, zz + 0.8), GOLD["light"], sides=10)]
            else:
                P += bone_3d(f"ShelfBone{i}_{k}", (tx, -7.6, zz + 0.45), 1.2, CREAM["base"], rot=(0, 0, 0.3))
    P += [S("ShelfMedal", (0.7, 0.15, 0.7), (-5.2, -8.15, f1 + 5.0), GOLD["base"], rot=(0, 0.78, 0))]
    P += interior_light("LodgeLight1", -2, -10.5, f2 - 0.6, 6, 1.4)
    P += interior_light("LodgeLight2", 0, -11, top - 0.3, 6, 1.4)
    P += [S("Hearth", (3.6, 1.2, 3.4), (5.5, -16.0, f1), STONE["base"]),
          S("HearthGlow", (1.8, 0.3, 1.2), (5.5, -15.3, f1 + 0.3), NEON_ORANGE, emission=5)]
    section("LodgeFront")
    # striped awning over the display window (red/white, scalloped)
    P += kit.striped_awning("Awn", -9.6, -0.8, y1 + 0.2, 7.5, depth=2.6, tilt=24, colors=(RED["base"], "#FFFFFF"))
    P += [S("AwnBar", (9.0, 0.4, 0.4), (-5.2, y1 + 0.2, 7.3), IRON)]
    # balcony over the door side (right): deck + brackets + railings
    bx0, bx1, by1 = -0.2, 10.4, y1 + 3.2
    P += [S("BalcDeck", (bx1 - bx0, by1 - y1, 0.5), ((bx0 + bx1) / 2, (y1 + by1) / 2, f2 - 0.3), WOOD["dark"]),
          S("BalcEdge", (bx1 - bx0 + 0.3, 0.4, 0.7), ((bx0 + bx1) / 2, by1 - 0.2, f2 - 0.5), WOOD["deep"])]
    for i, px in enumerate((bx0 + 0.4, (bx0 + bx1) / 2, bx1 - 0.4)):
        P.append(beam(f"BalcBrace{i}", (px, y1 + 0.1, f2 - 3.2), (px, by1 - 0.4, f2 - 0.35), 0.45, 0.45, WOOD["deep"]))
    P += railing("BalcRailF", (bx0 + 0.25, by1 - 0.25), (bx1 - 0.25, by1 - 0.25), f2 + 0.2, h=1.6, col=WOOD, post_every=5)
    P += railing("BalcRailL", (bx0 + 0.25, y1 + 0.3), (bx0 + 0.25, by1 - 0.25), f2 + 0.2, h=1.6, col=WOOD, post_every=10)
    P += railing("BalcRailR", (bx1 - 0.25, y1 + 0.3), (bx1 - 0.25, by1 - 0.25), f2 + 0.2, h=1.6, col=WOOD, post_every=10)
    P += [C("BalcPlantPot", 0.5, 0.6, 0.8, (9.2, y1 + 0.9, f2 + 0.2), RED["dark"], sides=10),
          R("BalcPlant", (1.0, 1.0, 0.9), (9.2, y1 + 0.9, f2 + 1.0), LEAF["base"], radius=0.2),
          S("BalcChair", (1.2, 1.2, 0.3), (6.0, y1 + 1.4, f2 + 1.0), BLUE["base"]),
          S("BalcChairB", (1.2, 0.3, 1.4), (6.0, y1 + 0.85, f2 + 1.0), BLUE["dark"])]
    # sign above the awning: "LODGE" board with ski + bone icons (blank planks, icons physical)
    P += sign_board("LodgeSign", -5.2, y1 + 0.1, 8.7, 7.4, 1.6, board=WOOD)
    P += bone_icon("LodgeSignBone", -7.6, y1 + 0.45, 9.55, 1.8, CREAM["light"], rot=0.2)
    for i, (col, rr) in enumerate(((RED["base"], 0.5), (BLUE["base"], -0.5))):
        P.append(S(f"LodgeSignSki{i}", (0.35, 0.2, 2.0), (-3.0 + i * 0.4, y1 + 0.55, 8.55), col, rot=(0, rr, 0)))
    P += mountain_icon("LodgeSignPeak", -5.2, y1 + 0.45, 8.85, 1.6, depth=0.12)
    section("LodgeRoof")
    # roof: red, ridge along X, gables on the sides, snow cap, chimney + vents + weather vane
    P += roof("Roof", 0, yc, top, D / 2 + 0.4, W + 2.4, 6.5, ridge="x", col=RED, ov=1.6, bands=4, snow=0.55, rnd=rnd)
    for k, xx in enumerate((x0, x1)):
        P.append(prism(f"Gable{k}", [(-D / 2 - 0.4, 0), (D / 2 + 0.4, 0), (0, 6.5)], th, "x", (xx - (0 if k else th) + (th if k == 0 else 0) - th / 2 + (0 if k == 0 else 0), yc, top),
                       WOOD["light"]))
        sg = -1 if k == 0 else 1
        P += [disc_y(f"GableWin{k}", 0, 0, 0, 0.9, 0.15, GLASS, studs="none")]
        g = P[-1]
        g.rotation_euler = (0, 0, 0)
        g.rotation_euler = (0, sg * D90, 0) if False else (D90, 0, sg * D90)
        g.location = (xx + sg * 0.35, yc, top + 2.4)
        P.append(ring(f"GableRim{k}", 1.2, 0.9, 0.3, (0, 0, 0), CREAM["base"], sides=16))
        rr = P[-1]
        rr.rotation_euler = (0, D90, 0)
        rr.location = (xx + sg * 0.35 - (0.15 if sg > 0 else 0.15), yc, top + 2.4)
        vb.restud([g, rr])
    P += [S("ChimL", (2.2, 2.2, 9.0), (-7.0, -13.5, top), STONE["base"]),
          S("ChimLBand", (2.6, 2.6, 0.5), (-7.0, -13.5, top + 6.0), STONE["dark"]),
          S("ChimLCap", (2.6, 2.6, 0.5), (-7.0, -13.5, top + 9.0), STONE["deep"]),
          S("ChimLSnow", (2.2, 2.2, 0.35), (-7.0, -13.5, top + 9.5), SNOW, bevel=0.1),
          C("VentA", 0.4, 0.4, 2.4, (6.0, -14.0, top + 2.5), IRON, sides=8),
          C("VentACap", 0.65, 0.65, 0.3, (6.0, -14.0, top + 4.9), IRON, sides=8),
          C("VentB", 0.3, 0.3, 1.6, (7.4, -14.2, top + 2.2), "#C9D3DD", sides=8),
          S("VanePost", (0.25, 0.25, 3.2), (0, yc, top + 6.9), IRON),
          S("VaneArrow", (3.0, 0.18, 0.3), (0, yc, top + 9.4), GOLD["base"], rot=(0, 0, 0.5))]
    P += bone_3d("VaneBone", (0, yc, top + 8.6), 1.6, GOLD["light"], rot=(0, 0, 0.5))
    section("Yard")
    # ski + sled rack (right front)
    rx, ry = 14.8, -6.0
    P += [S("RackFootL", (0.6, 3.2, 0.5), (rx - 2.5, ry, 0), WOOD["deep"]),
          S("RackFootR", (0.6, 3.2, 0.5), (rx + 2.5, ry, 0), WOOD["deep"]),
          S("RackPostL", (0.5, 0.5, 4.4), (rx - 2.5, ry - 0.6, 0.5), WOOD["dark"]),
          S("RackPostR", (0.5, 0.5, 4.4), (rx + 2.5, ry - 0.6, 0.5), WOOD["dark"]),
          S("RackBar", (5.6, 0.5, 0.5), (rx, ry - 0.6, 4.4), WOOD["base"]),
          S("RackBarLow", (5.4, 0.4, 0.4), (rx, ry + 0.7, 0.6), WOOD["base"]),
          S("RackRoof", (6.4, 2.8, 0.3), (rx, ry - 0.6, 5.0), RED["base"]),
          S("RackRoofSnow", (6.0, 2.4, 0.3), (rx, ry - 0.6, 5.3), SNOW, bevel=0.1)]
    skis = (RED["base"], GOLD["base"], TEAL["base"], BLUE["base"], ORNG["base"], PINK["base"])
    for i, col in enumerate(skis):
        xx = rx - 2.0 + i * 0.8
        P.append(S(f"Ski{i}", (0.42, 0.18, 5.0), (xx, ry + 0.9, 0.6), col, rot=(-0.28, 0, 0)))
        P.append(S(f"SkiTip{i}", (0.42, 0.6, 0.18), (xx, ry - 0.5, 5.35), col, rot=(-0.28 - 0.9, 0, 0)))
        P.append(S(f"SkiBind{i}", (0.5, 0.3, 0.4), (xx, ry + 0.45, 2.6), IRON, rot=(-0.28, 0, 0)))
    P += [S("SledBed", (2.2, 3.8, 0.3), (rx, ry + 4.0, 0.6), RED["base"]),
          S("SledRunL", (0.18, 4.2, 0.18), (rx - 0.9, ry + 4.0, 0.0), IRON),
          S("SledRunR", (0.18, 4.2, 0.18), (rx + 0.9, ry + 4.0, 0.0), IRON),
          S("SledCurl", (2.0, 0.3, 1.0), (rx, ry + 5.9, 0.6), RED["dark"])]
    for i in range(3):
        P.append(S(f"SledLeg{i}", (2.0, 0.3, 0.45), (rx, ry + 2.6 + i * 1.3, 0.15), IRON))
    # snowman + bench + lamps (exterior props)
    P += [B("SnowmanA", (1.4, 1.4, 1.2), (-15.0, -4.5, 1.2), SNOW, segments=14, rings=8),
          B("SnowmanB", (1.0, 1.0, 0.9), (-15.0, -4.5, 3.0), SNOW, segments=14, rings=8),
          B("SnowmanC", (0.75, 0.75, 0.7), (-15.0, -4.5, 4.4), SNOW, segments=12, rings=8),
          C("SnowmanNose", 0.15, 0.02, 0.7, (-15.0, -3.85, 4.45), ORNG["base"], sides=6, rot=(-D90, 0, 0)),
          B("SnowmanEyeL", (0.11, 0.08, 0.11), (-15.25, -3.85, 4.7), IRON, segments=6, rings=4),
          B("SnowmanEyeR", (0.11, 0.08, 0.11), (-14.75, -3.85, 4.7), IRON, segments=6, rings=4),
          C("SnowmanHat", 0.55, 0.55, 0.7, (-15.0, -4.5, 4.95), RED["dark"], sides=10),
          C("SnowmanBrim", 0.8, 0.8, 0.12, (-15.0, -4.5, 4.95), RED["base"], sides=12),
          S("SnowmanScarf", (1.6, 1.6, 0.3), (-15.0, -4.5, 3.75), GOLD["base"], bevel=0.12, rot=(0, 0, 0.3)),
          S("SnowmanScarfTail", (0.4, 0.2, 1.0), (-14.6, -3.7, 2.9), GOLD["base"], rot=(0.2, 0.2, 0))]
    P += bench("LodgeBench", -15.0, -10.5, yaw=-D90)
    P += lantern_post("LodgeLamp", -12.5, -2.0)
    P += pine("LodgePineA", -18.5, -15.0, 13, rnd)
    P += pine("LodgePineB", 18.5, -15.5, 12, random.Random(31))
    # stone path to the door
    for i in range(3):
        P.append(S(f"DoorPath{i}", (2.9, 1.0, 1.2 - i * 0.4), (2.4, y1 + 0.5 + i * 1.0, 0), STONE["light"] if i % 2 else STONE["base"]))
    MARKERS.setdefault("StageDoors", {})["3"] = [2.4, y1 + 1.0, 1.5]
    return P


# ---- STAGE 4: Alpine Chalet + trophy tower -------------------------------------------------------

def stage4():
    rnd = random.Random(404)
    section("ChaletShell")
    P = []
    x0, x1, y0, y1 = -11.5, 11.5, -18.0, -5.0
    W, D = x1 - x0, y1 - y0
    yc = (y0 + y1) / 2
    th = 0.9
    f1, f2, top = 1.4, 7.6, 13.6
    P += [S("Plinth", (W + 1.4, D + 1.4, 1.4), (0, yc, 0), STONE["base"]),
          S("PlinthLip", (W + 1.8, D + 1.8, 0.3), (0, yc, 1.1), STONE["dark"])]
    # ground floor: cream plaster with stone quoins; upper floor: warm wood with timber trim
    g_open = [(-9.4, -5.6, 2.6, 6.4), (-1.6, 1.6, f1, 6.2), (5.6, 9.4, 2.6, 6.4)]
    u_open = [(-8.8, -5.2, 9.0, 12.4), (-2.4, 2.4, f2 + 0.2, 12.8), (5.2, 8.8, 9.0, 12.4)]
    P += wall_openings("GF", "x", y1 - th / 2, x0, x1, f1, f2, th, g_open, CREAM["base"])
    P += wall_openings("UF", "x", y1 - th / 2, x0, x1, f2, top, th, u_open, WOOD["base"])
    P += wall_openings("GB", "x", y0 + th / 2, x0, x1, f1, f2, th, [(-2, 2, 2.6, 6.2)], CREAM["base"])
    P += wall_openings("UB", "x", y0 + th / 2, x0, x1, f2, top, th, [(-2, 2, 9.0, 12.4)], WOOD["base"])
    for k, xx in (("L", x0 + th / 2), ("R", x1 - th / 2)):
        P += wall_openings(f"G{k}", "y", xx, y0 + th, y1 - th, f1, f2, th, [(-13.5, -9.5, 2.6, 6.2)], CREAM["base"])
        P += wall_openings(f"U{k}", "y", xx, y0 + th, y1 - th, f2, top, th, [(-15.0, -12.0, 9.0, 12.4), (-11.0, -8.0, 9.0, 12.4)], WOOD["base"])
    for sx in (-1, 1):  # stone quoins on ground-floor corners (alternating sizes)
        for sy in (-1, 1):
            for i in range(5):
                big = i % 2 == 0
                P.append(S(f"Quoin{sx}{sy}{i}", (1.5 if big else 1.1, 1.5 if not big else 1.1, 1.15),
                           (sx * (W / 2 + 0.05 - (0.75 if big else 0.55) + (0.75 if big else 0.55)), yc + sy * (D / 2 + 0.05), f1 + i * 1.24),
                           STONE["light"] if big else STONE["base"]))
    # floor band + cornice + timber trim on upper floor (verticals + X braces between windows)
    P += [S("Band1F", (W + 0.8, 0.5, 0.7), (0, y1 + 0.2, f2 - 0.3), WOOD["deep"]),
          S("Band1B", (W + 0.8, 0.5, 0.7), (0, y0 - 0.2, f2 - 0.3), WOOD["deep"]),
          S("Band1L", (0.5, D + 0.8, 0.7), (x0 - 0.2, yc, f2 - 0.3), WOOD["deep"]),
          S("Band1R", (0.5, D + 0.8, 0.7), (x1 + 0.2, yc, f2 - 0.3), WOOD["deep"]),
          S("Cornice", (W + 0.8, 0.5, 0.6), (0, y1 + 0.2, top - 0.6), WOOD["deep"])]
    for i, xx in enumerate((-11.0, -4.2, 4.2, 11.0)):
        P.append(S(f"TimberV{i}", (0.6, 0.35, top - f2 - 0.6), (xx, y1 + 0.15, f2 + 0.4), WOOD["deep"]))
    for k, (a, b) in enumerate(((-4.2, -2.9), (2.9, 4.2))):
        for d in (0, 1):
            P.append(beam(f"XBrace{k}{d}", ((a if d == 0 else b), y1 + 0.25, f2 + 0.6), ((b if d == 0 else a), y1 + 0.25, top - 0.8),
                          0.4, 0.3, WOOD["deep"]))
    for k in ("L", "R"):
        sx = -1 if k == "L" else 1
        for i, yy in enumerate((-17.3, -11.5, -5.7)):
            P.append(S(f"TimberS{k}{i}", (0.35, 0.6, top - f2 - 0.6), (sx * (W / 2 + 0.15), yy, f2 + 0.4), WOOD["deep"]))
    section("ChaletFront")
    # windows (with flower boxes) + door
    for k, (a, b, za, zb) in enumerate((g_open[0], g_open[2])):
        P += window(f"GWin{k}", (a + b) / 2, y1 + 0.05, za, b - a, zb - za, "+y", frame="#FFFFFF", sill=None, shutters=GRN)
        P += flower_box(f"GBox{k}", (a + b) / 2, y1, za - 1.1, b - a + 0.6)
    for k, (a, b, za, zb) in enumerate((u_open[0], u_open[2])):
        P += window(f"UWin{k}", (a + b) / 2, y1 + 0.05, za, b - a, zb - za, "+y", frame="#FFFFFF", shutters=RED)
        P += flower_box(f"UBox{k}", (a + b) / 2, y1, za - 1.1, b - a + 0.6)
    P += window("BalcDoor", 0, y1 + 0.05, f2 + 0.2, 4.8, 4.6, "+y", frame="#FFFFFF", mullions=1)
    P += door("ChaletDoor", 0, y1 + 0.05, f1, w=3.2, h=4.8, col=RED, frame=WOOD["deep"], step=False, mat=False)
    P += window("GBWin", 0, y0 - 0.05, 2.6, 4, 3.6, "-y", frame="#FFFFFF")
    P += window("UBWin", 0, y0 - 0.05, 9.0, 4, 3.4, "-y", frame="#FFFFFF")
    for k, nrm, xx in (("L", "-x", x0 - 0.05), ("R", "+x", x1 + 0.05)):
        P += window(f"GS{k}", xx, -11.5, 2.6, 4, 3.6, nrm, frame="#FFFFFF", sill=WOOD["deep"])
        for j, (a, b) in enumerate(((-15.0, -12.0), (-11.0, -8.0))):
            P += window(f"US{k}{j}", xx, (a + b) / 2, 9.0, 3, 3.4, nrm, frame="#FFFFFF", sill=WOOD["deep"])
    # interior: floors, trophy cabinet, fireplace, lights
    P += [S("Floor1", (W - 1.8, D - 1.8, 0.2), (0, yc, f1), WOOD["dark"]),
          S("Floor2", (W - 1.8, D - 1.8, 0.4), (0, yc, f2 - 0.4), WOOD["dark"]),
          S("Cabinet", (5.0, 1.4, 4.2), (-7.5, -16.6, f1), WOOD["deep"]),
          S("CabinetShelf", (4.6, 1.0, 0.25), (-7.5, -16.3, f1 + 2.3), WOOD["light"]),
          S("Fire", (4.0, 1.4, 3.6), (7.0, -16.8, f1), STONE["base"]),
          S("FireGlow", (2.0, 0.3, 1.2), (7.0, -16.05, f1 + 0.3), NEON_ORANGE, emission=5)]
    for i in range(3):
        P += [C(f"CabCup{i}", 0.25, 0.4, 0.6, (-9.0 + i * 1.5, -16.3, f1 + 2.55), GOLD["light"], sides=10)]
    P += bone_3d("CabBone", (-7.5, -16.3, f1 + 1.4), 2.2, GOLD["base"])
    P += interior_light("ChLight1", 0, -11, f2 - 0.6, 7, 1.6)
    P += interior_light("ChLight2", 0, -11, top - 0.3, 6, 1.6)
    # front balcony (carved railing) at the upper floor
    P += [S("BalcDeck", (16.0, 2.8, 0.5), (0, y1 + 1.4, f2 - 0.3), WOOD["dark"]),
          S("BalcEdge", (16.3, 0.4, 0.7), (0, y1 + 2.8, f2 - 0.5), WOOD["deep"])]
    for i, px in enumerate((-7.5, -2.5, 2.5, 7.5)):
        P.append(beam(f"BalcBrace{i}", (px, y1 + 0.1, f2 - 2.8), (px, y1 + 2.5, f2 - 0.35), 0.45, 0.45, WOOD["deep"]))
    P += railing("BalcRail", (-7.8, y1 + 2.55), (7.8, y1 + 2.55), f2 + 0.2, h=1.5, col=WOOD, step=0.7, post_every=6)
    for i, xx in enumerate((-5.6, 5.6)):
        P += flower_box(f"BalcBox{i}", xx, y1 + 2.4, f2 + 1.75, 3.2)
    section("ChaletRoof")
    # roof: giant red gable, ridge along Y, thick snow cap, carved sawtooth bargeboard on front
    half, rise = W / 2 + 0.5, 10.0
    P += roof("Roof", 0, yc + 0.8, top, half, D + 4.8, rise, ridge="y", col=RED, ov=2.6, t=0.7, bands=5, snow=0.92, rnd=rnd)
    # front + back gables (wood boards, vertical battens, round window, carved trim)
    for k, (yy, sg) in enumerate(((y1 - th, 1), (y0, -1))):
        P.append(prism(f"Gable{k}", [(-half, 0), (half, 0), (0, rise)], th, "y", (0, yy, top), WOOD["light"]))
        for i in range(-4, 5):
            hh = rise * (1 - abs(i * 2.2) / half) - 0.6
            if hh > 0.6:
                P.append(S(f"GBat{k}_{i}", (0.3, 0.2, hh), (i * 2.2, yy + (th + 0.1 if sg > 0 else -0.1), top), WOOD["dark"]))
    P += [disc_y("GableWin", 0, y1 + 0.1, top + 4.6, 1.3, 0.15, GLASS, studs="none"),
          ring("GableRim", 1.65, 1.3, 0.35, (0, 0, 0), "#FFFFFF", sides=18)]
    gr = P[-1]
    gr.rotation_euler = (-D90, 0, 0)
    gr.location = (0, y1 + 0.05, top + 4.6)
    vb.restud([gr])
    P += [S("GableCross", (2.6, 0.2, 0.22), (0, y1 + 0.3, top + 4.5), "#FFFFFF"),
          S("GableCrossV", (0.22, 0.2, 2.6), (0, y1 + 0.3, top + 3.3), "#FFFFFF")]
    # sawtooth bargeboard along both front roof edges
    a = math.atan2(rise, half)
    for s in (-1, 1):
        for i in range(9):
            l = 1.0 + i * 1.45
            xx = s * math.cos(a) * l
            zz = top + rise - math.sin(a) * l - 0.9
            P.append(S(f"Tooth{s}_{i}", (0.7, 0.3, 0.7), (xx, y1 + 3.3, zz), WOOD["deep"] if i % 2 else GRN["base"], rot=(0, 0.785, 0)))
    P += [S("RidgeFinial", (0.6, 0.6, 1.6), (0, y1 + 3.2, top + rise + 0.5), WOOD["deep"]),
          B("RidgeFinialBall", (0.45, 0.45, 0.45), (0, y1 + 3.2, top + rise + 2.3), GOLD["base"], segments=10, rings=6)]
    # chimney through the snow + sign over the door with bone + peak icons
    P += [S("Chim", (2.4, 2.4, 9.0), (6.0, -15.0, top + 3.0), STONE["base"]),
          S("ChimBand", (2.8, 2.8, 0.5), (6.0, -15.0, top + 8.0), STONE["dark"]),
          S("ChimCap", (2.8, 2.8, 0.5), (6.0, -15.0, top + 12.0), STONE["deep"]),
          S("ChimSnow", (2.4, 2.4, 0.4), (6.0, -15.0, top + 12.5), SNOW, bevel=0.12)]
    P += sign_board("ChaletSign", 0, y1 + 0.3, 6.5, 6.0, 1.0, board=GRN, border=WOOD["deep"])
    P += bone_icon("ChaletSignBone", -1.6, y1 + 0.65, 6.95, 1.5, CREAM["light"], rot=0.2)
    P += mountain_icon("ChaletSignPeak", 1.6, y1 + 0.65, 6.6, 1.3, depth=0.12)
    section("TrophyTower")
    # --- trophy tower (right): stone base, timber shaft, open lantern room, gold bone on top ---
    tx, ty = 17.6, -9.5
    P += [S("TwBase", (5.4, 5.4, 4.0), (tx, ty, 0), STONE["base"]),
          S("TwBaseLip", (5.8, 5.8, 0.4), (tx, ty, 4.0), STONE["dark"]),
          S("TwShaft", (4.4, 4.4, 14.0), (tx, ty, 4.4), CREAM["base"])]
    for i in range(4):  # timber corner posts + band
        sx, sy = (-1, 1, -1, 1)[i], (-1, -1, 1, 1)[i]
        P.append(S(f"TwPost{i}", (0.7, 0.7, 14.0), (tx + sx * 2.05, ty + sy * 2.05, 4.4), WOOD["deep"]))
    for zz in (9.0, 13.6):
        P.append(S(f"TwBand{zz}", (4.8, 4.8, 0.5), (tx, ty, zz), WOOD["deep"]))
    for zz in (5.5, 10.2, 14.6):
        P += window(f"TwWin{int(zz)}", tx, ty + 2.2, zz, 1.4, 2.2, "+y", frame="#FFFFFF", mullions=0, transom=False)
    P += window("TwWinS", tx + 2.2, ty, 10.2, 1.4, 2.2, "+x", frame="#FFFFFF", transom=False)
    P += window("TwWinW", tx - 2.2, ty, 10.2, 1.4, 2.2, "-x", frame="#FFFFFF", transom=False)
    P += [S("TwDeck", (6.4, 6.4, 0.6), (tx, ty, 18.4), WOOD["dark"])]
    for i in range(8):  # gold crenellated railing
        a2 = i * math.pi / 4
        P.append(S(f"TwMerlon{i}", (1.0, 1.0, 1.1), (tx + math.cos(a2) * 2.75, ty + math.sin(a2) * 2.75, 19.0), GOLD["base"] if i % 2 else GOLD["dark"],
                   rot=(0, 0, a2)))
    P += [C("TwPed", 1.3, 1.0, 1.4, (tx, ty, 19.0), WOOD["deep"], sides=10),
          C("TwPedTop", 1.5, 1.5, 0.3, (tx, ty, 20.4), GOLD["dark"], sides=12),
          ring("TwNeon", 1.9, 1.6, 0.15, (tx, ty, 20.4), NEON_GOLD, emission=4)]
    P += bone_3d("TwBone", (tx, ty, 22.5), 4.6, GOLD["base"], rot=(0, -0.5, 0.2))
    for i in range(4):
        a2 = i * math.pi / 2 + 0.4
        P.append(S(f"TwSpark{i}", (0.4, 0.4, 0.4), (tx + math.cos(a2) * 2.4, ty + math.sin(a2) * 2.4, 23.0 + (i % 2)), NEON_GOLD,
                   emission=4, rot=(0.78, 0.78, 0)))
    P += [S("TwDoor", (2.2, 0.3, 3.4), (tx, ty + 2.7, 0.0), WOOD["dark"]),
          S("TwDoorFrame", (2.8, 0.4, 0.4), (tx, ty + 2.75, 3.4), WOOD["deep"])]
    # bridge from the chalet balcony level to the tower
    P += [S("Bridge", (4.0, 2.0, 0.4), (x1 + 2.2, ty, f2 + 4.0), WOOD["dark"])]
    P += railing("BridgeRailA", (x1 + 0.4, ty + 0.9), (tx - 2.2, ty + 0.9), f2 + 4.4, h=1.2, col=WOOD, post_every=3)
    section("Yard")
    # exterior props: sled + hay-style firewood, bench, lamps, pines
    P += bench("ChBench", -8.0, y1 + 4.5, yaw=0.0)
    P += lantern_post("ChLampL", -13.6, -3.0)
    P += lantern_post("ChLampR", 12.2, -2.5)
    P += pine("ChPineA", -18.0, -14.0, 14, rnd)
    P += pine("ChPineB", -19.0, -4.0, 10, random.Random(44))
    P += boulder("ChRock", 21.0, -15.5, 2.2, rnd, snow=True)
    for i in range(3):
        P.append(S(f"DoorPath{i}", (3.4, 1.0, 1.4 - i * 0.45), (0, y1 + 0.5 + i * 1.0, 0), STONE["light"] if i % 2 else STONE["base"]))
    MARKERS.setdefault("StageDoors", {})["4"] = [0, y1 + 1.0, 1.4]
    return P


# ---- STAGE 5: Summit Hall -----------------------------------------------------------------------

def friendly_skull(prefix, cx, cy, cz, s=1.0):
    """Cartoon skull trophy: rounded cream cranium, big round eye sockets with sparkles, happy toothy
    grin, rosy cheeks, gold crown band. Friendly, not scary. Faces +y; cz = bottom."""
    P = [R(f"{prefix}Cranium", (3.0 * s, 2.8 * s, 2.6 * s), (cx, cy, cz + 0.9 * s), CREAM["base"], radius=0.9 * s),
         R(f"{prefix}Jaw", (2.2 * s, 2.2 * s, 1.1 * s), (cx, cy + 0.1 * s, cz), CREAM["dark"], radius=0.4 * s)]
    fy = cy + 1.4 * s
    for i, sx in enumerate((-1, 1)):
        P += [disc_y(f"{prefix}Eye{i}", cx + sx * 0.72 * s, fy - 0.1 * s, cz + 2.1 * s, 0.55 * s, 0.14 * s, "#2B2640", sides=14),
              disc_y(f"{prefix}Spark{i}", cx + sx * 0.72 * s + 0.18 * s, fy + 0.02 * s, cz + 2.3 * s, 0.17 * s, 0.06 * s, "#FFFFFF", sides=8),
              disc_y(f"{prefix}Blush{i}", cx + sx * 1.05 * s, fy - 0.2 * s, cz + 1.35 * s, 0.32 * s, 0.06 * s, PINK["light"], sides=10)]
    P.append(prism(f"{prefix}Nose", [(-0.22 * s, 0), (0.22 * s, 0), (0, 0.4 * s)], 0.1 * s, "y", (cx, fy - 0.05 * s, cz + 1.35 * s), "#2B2640"))
    P.append(S(f"{prefix}Mouth", (1.5 * s, 0.1 * s, 0.5 * s), (cx, fy - 0.12 * s, cz + 0.65 * s), "#2B2640", bevel=0.03))
    for i in range(4):
        P.append(S(f"{prefix}Tooth{i}", (0.3 * s, 0.1 * s, 0.32 * s), (cx - 0.51 * s + i * 0.34 * s, fy - 0.06 * s, cz + 0.83 * s), "#FFFFFF",
                   bevel=0.03))
    P.append(S(f"{prefix}Crown", (3.1 * s, 2.9 * s, 0.4 * s), (cx, cy, cz + 2.8 * s), GOLD["base"]))
    for i in range(5):
        P.append(S(f"{prefix}CrownPt{i}", (0.45 * s, 0.45 * s, 0.45 * s), (cx - 1.2 * s + i * 0.6 * s, cy + 1.3 * s, cz + 3.05 * s),
                   GOLD["light"], rot=(0, 0.785, 0)))
    return P


def stage5():
    rnd = random.Random(505)
    section("HallShell")
    P = []
    x0, x1, y0, y1 = -14.0, 14.0, -17.5, -5.0
    W, D = x1 - x0, y1 - y0
    yc = (y0 + y1) / 2
    th = 1.0
    f1, top = 2.2, 17.0
    # three-tier stone plinth + grand front stairs
    P += [S("Plinth0", (W + 4.0, D + 3.0, 0.8), (0, yc - 0.3, 0), STONE["dark"]),
          S("Plinth1", (W + 2.6, D + 2.0, 0.7), (0, yc - 0.2, 0.8), STONE["base"]),
          S("Plinth2", (W + 1.6, D + 1.2, 0.7), (0, yc, 1.5), STONE["light"])]
    for i in range(4):
        P.append(S(f"Stair{i}", (12.0 - i * 0.6, 1.1, 0.55 * (i + 1)), (0, y1 + 4.4 - i * 1.1, 0), STONE["light"] if i % 2 else STONE["base"]))
    # walls: cream stone with tall windows (stepped tops), wood upper frieze
    wins = [(-12.0, -9.0), (-7.0, -4.0), (4.0, 7.0), (9.0, 12.0)]
    fopen = [(a, b, 4.0, 12.0) for a, b in wins] + [(-2.2, 2.2, f1, 9.0)]
    P += wall_openings("HF", "x", y1 - th / 2, x0, x1, f1, top, th, fopen, CREAM["base"])
    P += wall_openings("HB", "x", y0 + th / 2, x0, x1, f1, top, th, [(a, b, 4.0, 12.0) for a, b in wins], CREAM["base"])
    for k, xx in (("L", x0 + th / 2), ("R", x1 - th / 2)):
        P += wall_openings(f"H{k}", "y", xx, y0 + th, y1 - th, f1, top, th, [(-14.5, -12.0, 4.0, 12.0), (-10.5, -8.0, 4.0, 12.0)], CREAM["base"])
    for k, (a, b) in enumerate(wins):
        xm = (a + b) / 2
        P += window(f"HWin{k}", xm, y1 + 0.05, 4.0, b - a, 8.0, "+y", frame=GOLD["base"], sill=STONE["dark"], mullions=1)
        P += [S(f"HWinArch{k}", (b - a + 0.8, 0.6, 0.6), (xm, y1 + 0.2, 12.3), STONE["dark"]),
              S(f"HWinArch2{k}", (b - a - 0.6, 0.6, 0.5), (xm, y1 + 0.2, 12.9), STONE["dark"]),
              S(f"HWinKey{k}", (0.8, 0.7, 0.9), (xm, y1 + 0.25, 12.6), GOLD["base"])]
        P += window(f"HBWin{k}", xm, y0 - 0.05, 4.0, b - a, 8.0, "-y", frame=GOLD["base"], sill=STONE["dark"])
    for k, nrm, xx in (("L", "-x", x0 - 0.05), ("R", "+x", x1 + 0.05)):
        for j, (a, b) in enumerate(((-14.5, -12.0), (-10.5, -8.0))):
            P += window(f"HS{k}{j}", xx, (a + b) / 2, 4.0, b - a, 8.0, nrm, frame=GOLD["base"], sill=STONE["dark"])
    section("HallFacade")
    # pilasters between windows (front) + frieze + neon cornice strip
    for i, xx in enumerate((-13.5, -8.0, -3.0, 3.0, 8.0, 13.5)):
        P += [S(f"Pil{i}", (1.4, 0.6, top - f1), (xx, y1 + 0.3, f1), CREAM["dark"]),
              S(f"PilCap{i}", (1.9, 0.9, 0.6), (xx, y1 + 0.35, top - 0.6), GOLD["dark"]),
              S(f"PilBase{i}", (1.9, 0.9, 0.6), (xx, y1 + 0.35, f1), STONE["dark"])]
    P += [S("Frieze", (W + 1.2, 1.0, 1.6), (0, y1 + 0.3, top), WOOD["deep"]),
          S("FriezeB", (W + 1.2, 1.0, 1.6), (0, y0 - 0.3, top), WOOD["deep"]),
          S("FriezeL", (1.0, D + 1.6, 1.6), (x0 - 0.3, yc, top), WOOD["deep"]),
          S("FriezeR", (1.0, D + 1.6, 1.6), (x1 + 0.3, yc, top), WOOD["deep"]),
          S("NeonCornice", (W + 1.0, 0.15, 0.3), (0, y1 + 0.85, top + 0.65), NEON_ORANGE, emission=4),
          S("NeonCorniceB", (W + 1.0, 0.15, 0.3), (0, y0 - 0.85, top + 0.65), NEON_ORANGE, emission=4)]
    for i in range(14):  # gold medallions on the frieze
        P.append(disc_y(f"Medal{i}", -13.0 + i * 2.0, y1 + 0.8, top + 1.2, 0.28, 0.12, GOLD["base"], sides=8))
    # portico: 4 round columns + entablature + pediment with gold bone emblem
    py = y1 + 3.0
    for i, xx in enumerate((-5.6, -2.0, 2.0, 5.6)):
        P += [S(f"ColBase{i}", (1.8, 1.8, 0.6), (xx, py, f1), STONE["dark"]),
              C(f"Col{i}", 0.75, 0.65, 10.2, (xx, py, f1 + 0.6), CREAM["light"], sides=10),
              C(f"ColRing{i}", 0.8, 0.8, 0.35, (xx, py, f1 + 4.0), GOLD["base"], sides=10),
              S(f"ColCap{i}", (1.9, 1.9, 0.7), (xx, py, f1 + 10.8), GOLD["dark"])]
    P += [S("Entab", (13.6, 4.2, 1.2), (0, y1 + 1.9, f1 + 11.5), CREAM["dark"]),
          S("EntabNeon", (13.6, 0.15, 0.3), (0, y1 + 4.05, f1 + 11.9), NEON_GOLD, emission=4)]
    P.append(prism("Pediment", [(-7.2, 0), (7.2, 0), (0, 4.4)], 4.2, "y", (0, y1 - 0.2, f1 + 12.7), CREAM["base"]))
    pa = math.atan2(4.4, 7.2)
    for s in (-1, 1):
        L = math.hypot(7.2, 4.4) + 0.6
        P.append(S(f"PedRoof{s}", (L, 4.8, 0.5), (s * math.cos(pa) * L / 2 - s * 0.3, y1 + 1.9, f1 + 12.7 + 4.4 - math.sin(pa) * L / 2 + 0.2),
                   RED["base"], rot=(0, s * pa, 0)))
        P.append(S(f"PedSnow{s}", (L * 0.7, 4.4, 0.3), (s * math.cos(pa) * L * 0.35, y1 + 1.9, f1 + 12.7 + 4.4 - math.sin(pa) * L * 0.35 + 0.65),
                   SNOW, rot=(0, s * pa, 0), bevel=0.1))
    P += bone_icon("PedBone", 0, y1 + 4.0, f1 + 14.1, 3.2, GOLD["light"], depth=0.3)
    P += [disc_y("PedEmblemBack", 0, y1 + 3.95, f1 + 14.1, 1.5, 0.08, RED["dark"], sides=16)]
    # grand door with gold frame
    P += door("HallDoor", 0, y1 + 0.05, f1, w=4.0, h=6.6, col=RED, frame=GOLD["dark"], window=False, step=False, mat=False)
    P += [S("DoorTransom", (4.0, 0.2, 1.6), (0, y1 + 0.1, f1 + 7.0), GLASS, studs="none"),
          S("DoorTransomBar", (4.6, 0.4, 0.3), (0, y1 + 0.2, f1 + 8.7), GOLD["base"])]
    # banners hanging between pilasters (red cloth, gold edges, bone emblem, tassels)
    for k, xx in enumerate((-10.5, -5.5, 5.5, 10.5)):
        col = RED if k % 2 == 0 else GRN
        P += [S(f"BanRod{k}", (3.0, 0.3, 0.3), (xx, y1 + 0.75, 15.6), GOLD["dark"]),
              S(f"Ban{k}", (2.4, 0.18, 6.6), (xx, y1 + 0.85, 9.0), col["base"]),
              S(f"BanEdgeL{k}", (0.25, 0.22, 6.6), (xx - 1.2, y1 + 0.85, 9.0), GOLD["base"]),
              S(f"BanEdgeR{k}", (0.25, 0.22, 6.6), (xx + 1.2, y1 + 0.85, 9.0), GOLD["base"]),
              prism(f"BanTail{k}", [(-1.32, 0), (1.32, 0), (1.32, -1.2), (0, -0.4), (-1.32, -1.2)], 0.18, "y", (xx, y1 + 0.76, 9.0), col["dark"])]
        P += bone_icon(f"BanBone{k}", xx, y1 + 0.94, 13.0, 1.6, CREAM["light"], rot=0.9, depth=0.12)
        P.append(S(f"BanStripe{k}", (2.4, 0.2, 0.3), (xx, y1 + 0.9, 11.0), GOLD["base"]))
    # front banners hide the front windows -> they hang in front of the PILASTER gaps... keep narrow
    section("HallRoof")
    # main roof: red with gold ridge, ridge along X
    P += roof("Roof", 0, yc, top + 1.6, D / 2 + 1.0, W + 3.0, 7.0, ridge="x", col=RED, ov=1.6, t=0.7, bands=4, snow=0.4, rnd=rnd,
              fascia=GOLD["dark"])
    for k, xx in enumerate((x0 - 0.5, x1 - 0.5)):
        P.append(prism(f"HGable{k}", [(-D / 2 - 1.0, 0), (D / 2 + 1.0, 0), (0, 7.0)], 1.0, "x", (xx, yc, top + 1.6), CREAM["dark"]))
    section("Towers")
    # side towers with pointy roofs and pennants
    for k, sx in enumerate((-1, 1)):
        tx, ty = sx * 18.6, -11.5
        P += [S(f"Tw{k}Base", (5.2, 5.2, 3.0), (tx, ty, 0), STONE["dark"]),
              S(f"Tw{k}Body", (4.4, 4.4, 19.0), (tx, ty, 3.0), CREAM["base"]),
              S(f"Tw{k}Band", (4.8, 4.8, 0.6), (tx, ty, 11.0), GOLD["dark"]),
              S(f"Tw{k}Top", (5.2, 5.2, 1.0), (tx, ty, 21.5), WOOD["deep"]),
              S(f"Tw{k}Neon", (5.3, 5.3, 0.25), (tx, ty, 21.0), NEON_ORANGE, emission=3),
              C(f"Tw{k}Roof", 3.6, 0.2, 7.0, (tx, ty, 22.5), RED["base"], sides=4, rot=(0, 0, 0.785)),
              C(f"Tw{k}RoofSnow", 2.0, 0.6, 1.4, (tx, ty, 26.0), SNOW, sides=4, rot=(0, 0, 0.785)),
              S(f"Tw{k}Pole", (0.2, 0.2, 3.2), (tx, ty, 29.2), IRON),
              prism(f"Tw{k}Pennant", [(0, 0), (2.4, 0.5), (0, 1.0)], 0.12, "y", (tx + 0.1, ty, 31.2), GOLD["base"])]
        for zz in (5.0, 13.0):
            P += window(f"Tw{k}Win{zz}", tx, ty + 2.2, zz, 1.6, 4.0, "+y", frame=GOLD["base"], transom=False, mullions=0)
            P += window(f"Tw{k}WinS{zz}", tx + sx * 2.2, ty, zz, 1.6, 4.0, "+x" if sx > 0 else "-x", frame=GOLD["base"], transom=False)
        P += [S(f"Tw{k}Ban", (2.0, 0.18, 5.0), (tx, ty + 2.35, 15.6 - 5.0 + 0.4), RED["base"] if k else GRN["base"])]
        P += bone_icon(f"Tw{k}BanBone", tx, ty + 2.45, 14.0, 1.3, CREAM["light"], rot=0.9, depth=0.1)
        P.append(S(f"Tw{k}Bridge", (2.6, 3.0, 0.6), (sx * 15.2, ty, 11.0), WOOD["deep"]))
    section("HallInterior")
    # interior (through the tall windows): trophy plinths, gold light
    P += [S("HFloor", (W - 2, D - 2, 0.2), (0, yc, f1), "#8A4A2A"),
          S("HCarpet", (4.0, D - 2.4, 0.1), (0, yc, f1 + 0.2), RED["base"], bevel=0.02)]
    for i, xx in enumerate((-10.5, -5.5, 5.5, 10.5)):
        P += [S(f"HPlinth{i}", (2.0, 2.0, 2.4), (xx, -8.0, f1), STONE["light"]),
              C(f"HTrophy{i}", 0.4, 0.8, 1.4, (xx, -8.0, f1 + 2.4), GOLD["light"], sides=10),
              S(f"HTrophyBase{i}", (1.1, 1.1, 0.35), (xx, -8.0, f1 + 2.4), GOLD["dark"])]
    P += interior_light("HLight1", 0, -11, top - 0.4, 20, 2.0)
    P += [S("HBackGlow", (18, 0.3, 4.0), (0, -16.3, 7.0), "#FFC864", emission=1.5)]
    section("Spire")
    # central bone-trophy spire on the ridge
    zr = top + 1.6 + 7.0
    sy = yc
    P += [S("SpBase", (7.0, 7.0, 4.0), (0, sy, zr - 2.0), CREAM["base"]),
          S("SpBaseTrim", (7.6, 7.6, 0.6), (0, sy, zr + 2.0), GOLD["dark"]),
          S("SpMid", (5.2, 5.2, 6.0), (0, sy, zr + 2.6), WOOD["deep"]),
          S("SpMidNeon", (5.35, 5.35, 0.3), (0, sy, zr + 5.0), NEON_ORANGE, emission=4),
          S("SpTop", (6.2, 6.2, 0.8), (0, sy, zr + 8.6), GOLD["base"])]
    for sxx in (-1, 1):  # arched openings with glow on the spire mid section (front/back)
        P += [S(f"SpWin{sxx}", (2.0, 0.2, 3.0), (0, sy + sxx * 2.62, zr + 3.4), "#FFC864", emission=3),
              S(f"SpWinFrame{sxx}", (2.8, 0.3, 0.45), (0, sy + sxx * 2.72, zr + 6.4), GOLD["base"])]
    for i in range(4):
        a2 = i * math.pi / 2 + math.pi / 4
        P.append(S(f"SpButtress{i}", (1.2, 1.2, 6.0), (math.cos(a2) * 3.3, sy + math.sin(a2) * 3.3, zr + 2.6), CREAM["dark"],
                   rot=(0, 0, a2)))
        P.append(C(f"SpFinial{i}", 0.6, 0.0, 1.6, (math.cos(a2) * 3.3, sy + math.sin(a2) * 3.3, zr + 8.6), GOLD["light"], sides=4,
                   rot=(0, 0, a2)))
    P += [C("SpPed", 2.4, 1.8, 1.6, (0, sy, zr + 9.4), RED["dark"], sides=12),
          ring("SpNeonRing", 2.9, 2.5, 0.25, (0, sy, zr + 9.5), NEON_CYAN, emission=4),
          C("SpCupStem", 0.7, 0.7, 1.2, (0, sy, zr + 11.0), GOLD["dark"], sides=10),
          C("SpCup", 1.2, 2.6, 1.6, (0, sy, zr + 12.2), GOLD["base"], sides=12),
          C("SpCupRim", 2.75, 2.75, 0.3, (0, sy, zr + 13.8), GOLD["light"], sides=14)]
    for sxx in (-1, 1):  # cup handles
        P.append(ring(f"SpHandle{sxx}", 1.0, 0.6, 0.4, (0, 0, 0), GOLD["base"], sides=12))
        hnd = P[-1]
        hnd.rotation_euler = (D90, 0, 0)
        hnd.location = (sxx * 2.5, sy + 0.2, zr + 13.0)
        vb.restud([hnd])
    # giant gold bone crossing behind the skull + the friendly skull on the cup
    P += bone_3d("SpBone", (0, sy - 0.8, zr + 16.4), 8.5, GOLD["light"], rot=(0, 0.45, 0))
    P += friendly_skull("SpSkull", 0, sy + 0.3, zr + 14.1, s=1.15)
    for i in range(6):
        a2 = i * math.pi / 3
        P.append(S(f"SpSpark{i}", (0.5, 0.5, 0.5), (math.cos(a2) * 4.4, sy + math.sin(a2) * 4.4, zr + 15.5 + (i % 2) * 1.5),
                   NEON_GOLD, emission=4, rot=(0.78, 0.78, 0)))
    section("Yard")
    # braziers flanking the stairs (neon flames) + gold bone statues + planters
    for k, sx in enumerate((-1, 1)):
        bx, by = sx * 8.2, y1 + 4.2
        P += [S(f"Braz{k}Base", (1.8, 1.8, 0.6), (bx, by, 0), STONE["dark"]),
              C(f"Braz{k}Col", 0.55, 0.45, 3.0, (bx, by, 0.6), STONE["base"], sides=8),
              C(f"Braz{k}Bowl", 0.7, 1.4, 1.0, (bx, by, 3.6), GOLD["dark"], sides=10),
              S(f"Braz{k}FlameA", (1.2, 1.2, 1.3), (bx, by, 4.4), NEON_ORANGE, emission=5, rot=(0.3, 0.3, 0.5)),
              S(f"Braz{k}FlameB", (0.7, 0.7, 0.9), (bx + 0.1, by, 5.3), NEON_GOLD, emission=5, rot=(0.4, 0.2, 1.1))]
        P += pine(f"HallPine{k}", sx * 20.5, -1.5, 11, random.Random(50 + k))
        P += [S(f"Planter{k}", (2.6, 2.6, 1.2), (sx * 20.5, -1.5, 0), STONE["base"]),
              S(f"PlanterLip{k}", (3.0, 3.0, 0.3), (sx * 20.5, -1.5, 1.2), STONE["dark"])]
    MARKERS.setdefault("StageDoors", {})["5"] = [0, y1 + 4.8, 0.55]
    return P


STAGES = {1: stage1, 2: stage2, 3: stage3, 4: stage4, 5: stage5}
STAGE_NAMES = {1: "Trail Tent", 2: "Log Cabin", 3: "Ski Lodge", 4: "Alpine Chalet", 5: "Summit Hall"}

# ---- materials / export --------------------------------------------------------------------------


def glass_material():
    mat = bpy.data.materials.get("M_BaseCampGlass")
    if mat:
        return mat
    mat = bpy.data.materials.new("M_BaseCampGlass")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = vb.hex_to_rgba(GLASS)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Alpha"].default_value = 0.32
    mat["roblox_color"] = GLASS
    mat["roblox_glass"] = True
    mat["roblox_transparency"] = 0.3
    mat["roblox_neon"] = False
    return mat


def apply_glass(objs):
    gm = glass_material()
    for o in objs:
        if o.type == "MESH" and o.data.materials and o.data.materials[0] and o.data.materials[0].name.startswith(f"M_{GLASS}"):
            o.data.materials.clear()
            o.data.materials.append(gm)


def kind_of(o):
    m = o.data.materials[0] if o.data.materials else None
    if m is None:
        return "body"
    if m.get("roblox_glass"):
        return "glass"
    if m.get("roblox_neon"):
        return "neon"
    return "body"


def tris_of(o):
    return vb.poly_report([o])["tris"]


def export_set(name, objs, out_dir, specials=()):
    objs = [o for o in objs if o.name in bpy.data.objects and o.type == "MESH"]
    apply_glass(objs)
    parts = len(objs)
    groups = {}
    keep = []
    for o in objs:
        if o.name in specials:
            keep.append(o)
        else:
            groups.setdefault((o.get("bc_model", "Main"), kind_of(o)), []).append(o)
    joined = []
    for (model, k), lst in sorted(groups.items()):
        jn = vb.join(f"{name}_{model}_{k.capitalize()}", lst)
        jn["bc_model"] = model
        joined.append(jn)
    final = joined + keep
    meshes = [{"name": o.name, "model": o.get("bc_model", o.name), "tris": tris_of(o)} for o in final]
    fbx = vb.export_fbx(os.path.join(out_dir, f"{name}.fbx"), final)
    vb.export_glb(os.path.join(out_dir, f"{name}.glb"), final)
    total = sum(m["tris"] for m in meshes)
    return {"name": name, "file": os.path.relpath(fbx, GAME), "glb": os.path.relpath(fbx[:-4] + ".glb", GAME),
            "tris": total, "meshes": meshes, "parts": parts, "kind": "basecamp"}


def collect(fn):
    before = set(bpy.data.objects.keys())
    _SECTION[0] = "Main"
    P = fn()
    section("Main")
    after = [bpy.data.objects[n] for n in bpy.data.objects.keys() if n not in before]
    return [o for o in after if o.type == "MESH"]


def export_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    entries = []
    vb.reset_scene()
    objs = collect(build_kit)
    entries.append(export_set("BaseCamp_Kit", objs, out_dir, specials=("TrophyBoard", "OwnerSign")))
    for n, fn in STAGES.items():
        vb.reset_scene()
        objs = collect(fn)
        e = export_set(f"BaseCamp_Stage{n}", objs, out_dir)
        e["stage"] = n
        e["title"] = STAGE_NAMES[n]
        entries.append(e)
    markers = {"origin": "pad top centre", "pad": [48, 40], "front": "+Y (toward the mountain)", "units": "studs",
               "axes": "Blender Z-up; Roblox: X same, Blender +Y -> Roblox -Z, Blender Z -> Roblox Y",
               "markers": {k: MARKERS[k] for k in ("Spawn", "LiftPad", "ClinicBed", "PetPedestal1", "PetPedestal2",
                                                   "PetPedestal3", "PetPedestal4", "TrophyBoard", "OwnerSign")},
               "stageDoors": MARKERS.get("StageDoors", {})}
    with open(os.path.join(out_dir, "markers.json"), "w", encoding="utf-8") as f:
        json.dump(markers, f, indent=2)
    man = [{"name": e["name"], "file": e["file"], "glb": e["glb"], "tris": e["tris"], "parts": e["parts"], "kind": e["kind"],
            "meshes": e["meshes"], **({"stage": e["stage"], "title": e["title"]} if "stage" in e else {})} for e in entries]
    with open(os.path.join(GAME, "assets", "manifest-basecamp.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2)
    return entries


# ---- preview renders -----------------------------------------------------------------------------

def preview_ground(ox=0.0):
    """Preview-only pad + surrounding alpine grass (not exported; the map owns the real pad)."""
    P = [S(f"PvPad{ox}", (48, 40, 1.0), (ox, 0, -1.0), "#D9C9A3", bevel=0.05),
         S(f"PvPadLip{ox}", (48.6, 40.6, 0.3), (ox, 0, -1.25), "#B8A47A", bevel=0.05),
         S(f"PvGrass{ox}", (56, 120, 1.0), (ox, 0, -2.0), "#4FC33A", bevel=0.0)]
    return P


def setup_render(samples):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    try:
        scene.cycles.use_denoising = True
    except Exception:
        pass
    scene.cycles.max_bounces = 4
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.33, 0.64, 1.0, 1)
    bg.inputs[1].default_value = 1.0
    for name, energy, rot, col, ang in (("Sun", 5.0, (0.75, 0.15, 0.6), (1.0, 0.96, 0.9), 0.12),
                                        ("Fill", 1.2, (1.0, -0.3, 3.6), (0.75, 0.85, 1.0), 0.3)):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        light.data.energy, light.data.color, light.data.angle = energy, col, ang
        light.rotation_euler = rot
        scene.collection.objects.link(light)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.clip_end = 3000
    scene.collection.objects.link(cam)
    scene.camera = cam
    return scene, cam


def shoot(scene, cam, path, loc, target, lens):
    cam.location = loc
    cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path, flush=True)


STAGE_H = {0: 8, 1: 8, 2: 15, 3: 23, 4: 26, 5: 40}


VIEWS = ["front", "side", "back", "hero"]


def render_all(samples=32, only=None):
    os.makedirs(PREVIEWS, exist_ok=True)
    jobs = [n for n in (0, 1, 2, 3, 4, 5)] + ["lineup"]
    for n in jobs:
        tag = "kit" if n == 0 else ("lineup" if n == "lineup" else f"stage{n}")
        if only and only not in tag:
            continue
        vb.reset_scene()
        if n == "lineup":
            for k in range(1, 6):
                ox = (k - 3) * 54.0
                objs = collect(build_kit) + collect(STAGES[k])
                for o in objs:
                    o.location.x += ox
                preview_ground(ox)
            apply_glass(list(bpy.data.objects))
            scene, cam = setup_render(samples)
            S("PvGrassWide", (400, 160, 1.0), (0, 0, -2.6), "#43B032", bevel=0.0)
            shoot(scene, cam, os.path.join(PREVIEWS, "basecamp_lineup.png"), (0, 175, 95), (0, -4, 9), 30)
            continue
        collect(build_kit)
        if n:
            collect(STAGES[n])
        preview_ground()
        apply_glass(list(bpy.data.objects))
        scene, cam = setup_render(samples)
        h = STAGE_H[n]
        dist = 52 + h * 0.9
        tz = h * 0.35
        if n == 0:
            shoot(scene, cam, os.path.join(PREVIEWS, "kit_front.png"), (0, 52, 22), (0, 8, 2.5), 32)
            shoot(scene, cam, os.path.join(PREVIEWS, "kit_lift_closeup.png"), (8, 30, 10), (16.0, 13.0, 4.5), 35)
            shoot(scene, cam, os.path.join(PREVIEWS, "kit_clinic_closeup.png"), (-8, 28, 8), (-16.5, 12.5, 3.0), 35)
            shoot(scene, cam, os.path.join(PREVIEWS, "kit_boards_pets_closeup.png"), (0, 34, 8), (0, 12, 2.5), 35)
            continue
        if "front" in VIEWS:
            shoot(scene, cam, os.path.join(PREVIEWS, f"{tag}_front.png"), (0, dist, h * 0.55 + 14), (0, -3, tz), 30)
        if "side" in VIEWS:
            shoot(scene, cam, os.path.join(PREVIEWS, f"{tag}_side.png"), (dist, -4, h * 0.55 + 12), (0, -4, tz), 30)
        if "back" in VIEWS:
            shoot(scene, cam, os.path.join(PREVIEWS, f"{tag}_back.png"), (6, -dist, h * 0.55 + 14), (0, -4, tz), 30)
        if "hero" in VIEWS:
            shoot(scene, cam, os.path.join(PREVIEWS, f"{tag}_hero.png"), (dist * 0.55, dist * 0.7, h * 0.4 + 6), (0, -6, tz + 1), 30)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = DEFAULT_OUT
    samples, only, do_render, do_export = 32, None, False, True
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--render":
            do_render = True
        elif a == "--render-only":
            do_render, do_export = True, False
        elif a == "--samples":
            samples = int(argv[i + 1])
            i += 1
        elif a == "--views":
            VIEWS[:] = argv[i + 1].split(",")
            i += 1
        elif a == "--only":
            only = argv[i + 1]
            i += 1
        else:
            out = os.path.abspath(a)
        i += 1
    if do_export:
        for e in export_all(out):
            print(e["name"], e["tris"], "tris", e["parts"], "parts", [(m["name"], m["tris"]) for m in e["meshes"]])
    if do_render:
        render_all(samples, only)
