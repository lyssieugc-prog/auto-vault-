"""
Ragdoll Off a Mountain — "Crash Buddies" pets, Trailhead Egg and currency icon models.
Handoff: games/ragdoll-off-a-mountain/blender/handoff-pets.md (write/read first).

ORIGINAL designs for this game, built in the MERGED VOXEL language (bible §1/§7): the main masses of
each pet are one 0.5-stud merged-block mesh painted in regions (no per-voxel colour noise), plus a crisp
flat-piece cartoon face and chunky accessory pieces. Studs are texture only (vault_blocky.stud_surface).
Technique reference only: blender/templates/creature.py + the Frappo merged-block build (no objects reused).

    python3 games/ragdoll-off-a-mountain/blender/pets.py <out_dir> [assets...] [--samples N] [--no-render]
    assets: pebble_pup avalanche_pug skelly_cat egg_trailhead icon_cash icon_gem lineup   (default: all)

Exports  <out_dir>/<Name>.fbx (Body/Glass/Neon meshes), <Name>_FX.fbx (orbiters + aura, spun in Studio),
         <Name>.glb preview.  Renders -> assets/previews/pets/, UI hero icons -> assets/ui/.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(GAME, "..", ".."))
sys.path[:0] = [os.path.join(ROOT, "blender", "lib")]

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import vault_blocky as vb  # noqa: E402
import vault_kit as kit  # noqa: E402

def _ensure_real_stud_tiles():
    """blender/textures/*.png are Git-LFS pointers in some checkouts (not real PNGs) -> Blender can't load
    the stud bump. Generate the identical tile into a temp dir instead (shared files stay untouched)."""
    hpath, _ = vb.stud_texture_paths()
    try:
        with open(hpath, "rb") as f:
            ok = f.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        ok = False
    if not ok:
        import tempfile
        vb._TEX_DIR = os.path.join(tempfile.gettempdir(), "vault_stud_tiles")
        vb.ensure_stud_textures()


_ensure_real_stud_tiles()

VS = 0.5  # merged block size (studs) — bible §1
PREV = os.path.join(GAME, "assets", "previews", "pets")
UI = os.path.join(GAME, "assets", "ui")
MANIFEST = os.path.join(GAME, "assets", "manifest-pets.json")

WHITE, PUPIL, BLUSH, TONGUE, MOUTH = "#FFFFFF", "#1A1A2E", "#FF8FB1", "#FF6F9B", "#2A1420"
GLASS = "#9BE1FF"


# =============================================================================================
# Merged-block canvas in WORLD units (cell (i,j,k) spans [i*VS,(i+1)*VS] ...)
# =============================================================================================
def _c(i):
    return (i + 0.5) * VS


class Vox:
    def __init__(self):
        self.v = {}

    def _cells(self, lo, hi):
        for i in range(math.floor(lo[0] / VS) - 1, math.ceil(hi[0] / VS) + 1):
            for j in range(math.floor(lo[1] / VS) - 1, math.ceil(hi[1] / VS) + 1):
                for k in range(math.floor(lo[2] / VS) - 1, math.ceil(hi[2] / VS) + 1):
                    yield (i, j, k), (_c(i), _c(j), _c(k))

    def sell(self, ctr, rad, col, p=2.0, pred=None):
        """Super-ellipsoid (p=2 ellipsoid, p=4 chunky rounded box)."""
        lo = [ctr[a] - rad[a] for a in range(3)]
        hi = [ctr[a] + rad[a] for a in range(3)]
        for key, q in self._cells(lo, hi):
            d = sum(abs((q[a] - ctr[a]) / rad[a]) ** p for a in range(3))
            if d <= 1.0 and (pred is None or pred(*q)):
                self.v[key] = col

    def box(self, lo, hi, col):
        for key, q in self._cells(lo, hi):
            if all(lo[a] <= q[a] <= hi[a] for a in range(3)):
                self.v[key] = col

    def paint(self, pred, col, only=None):
        for key in list(self.v):
            q = tuple(_c(n) for n in key)
            if (only is None or self.v[key] in only) and pred(*q):
                self.v[key] = col

    def carve(self, pred):
        for key in list(self.v):
            if pred(*(_c(n) for n in key)):
                del self.v[key]

    def paint_top(self, pred, col, depth=1, only=None):
        """Recolours the top `depth` cells of every column where pred(centre) holds (moss caps, saddles)."""
        tops = {}
        for (i, j, k) in self.v:
            tops[(i, j)] = max(tops.get((i, j), -999), k)
        for (i, j), k in tops.items():
            for d in range(depth):
                key = (i, j, k - d)
                if key in self.v and (only is None or self.v[key] in only) and pred(_c(i), _c(j), _c(k - d)):
                    self.v[key] = col

    def mosaic(self, n, colours, only, seed=1):
        """Chunky colour regions (nearest-seed), so a body reads as big pebble plates — not per-voxel noise."""
        rnd = random.Random(seed)
        keys = [k for k, c in self.v.items() if c in only]
        if not keys:
            return
        seeds = [(rnd.choice(keys), colours[i % len(colours)]) for i in range(n)]
        for k in keys:
            best = min(seeds, key=lambda s: sum((k[a] - s[0][a]) ** 2 for a in range(3)))
            self.v[k] = best[1]

    # surface queries (world units) -------------------------------------------------------
    def front_y(self, x, z):
        i, k = math.floor(x / VS), math.floor(z / VS)
        ys = [key[1] for key in self.v if key[0] == i and key[2] == k]
        return (max(ys) + 1) * VS if ys else None

    def back_y(self, x, z):
        i, k = math.floor(x / VS), math.floor(z / VS)
        ys = [key[1] for key in self.v if key[0] == i and key[2] == k]
        return min(ys) * VS if ys else None

    def side_x(self, y, z, sign):
        j, k = math.floor(y / VS), math.floor(z / VS)
        xs = [key[0] for key in self.v if key[1] == j and key[2] == k]
        if not xs:
            return None
        return (max(xs) + 1) * VS if sign > 0 else min(xs) * VS

    def top_z(self, x, y):
        i, j = math.floor(x / VS), math.floor(y / VS)
        zs = [key[2] for key in self.v if key[0] == i and key[1] == j]
        return (max(zs) + 1) * VS if zs else None

    def mesh(self, name):
        o = vb.voxel_mesh(name, self.v, voxel=VS, jitter=0.0)
        vb.stud_surface(o, "all")
        o["vault_kind"] = "merged_blocks"
        return o


# =============================================================================================
# Part helpers (every helper appends to the current builder)
# =============================================================================================
class Builder:
    def __init__(self, name):
        self.name = name
        self.P, self.FX, self.glass = [], [], set()

    def add(self, o, fx=False, glass=False):
        (self.FX if fx else self.P).append(o)
        if glass:
            self.glass.add(o.name)
        return o


B: Builder = None  # current builder


def S(name, size, loc, col, bevel=0.05, rot=None, fx=False, studs="all"):
    return B.add(vb.solid(name, size, loc, col, bevel=bevel, rot=rot, studs=studs), fx)


def R(name, size, loc, col, radius=0.15, rot=None, fx=False, studs="all"):
    return B.add(vb.rounded(name, size, loc, col, radius=radius, rot=rot, studs=studs), fx)


def BALL(name, radii, ctr, col, seg=12, rings=8, fx=False, emission=0.0, studs="all"):
    return B.add(vb.ball(name, radii, ctr, col, segments=seg, rings=rings, emission=emission, studs=studs), fx)


def CYL(name, r1, r2, h, loc, col, sides=10, rot=None, fx=False, emission=0.0, studs="all"):
    return B.add(vb.cyl(name, r1, r2, h, loc, col, sides=sides, rot=rot, emission=emission, studs=studs), fx)


def GLOW(name, size, loc, col, strength=4.0, bevel=0.04, rot=None, fx=False):
    o = vb.block(name, size, loc, col, bevel=bevel, segments=1, emission=strength)
    if rot:
        o.rotation_euler = rot
    return B.add(o, fx)


def FACE(name, size, loc, col, bevel=0.03, seg=1, emission=0.0, rot=None):
    """Crisp flat face piece (no studs — face exception, bible §2)."""
    o = vb.block(name, size, loc, col, bevel=bevel, segments=seg, emission=emission)
    o["vault_face"] = True
    if rot:
        o.rotation_euler = rot
    return B.add(o)


def bar(name, p0, p1, w, t, col, glow=0.0, fx=False, studs="all", up=(0, 0, 1)):
    """Chunky bar between two points (w = width, t = thickness). Centre-aligned on the segment."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    q = Vector((1, 0, 0)).rotation_difference(d.normalized())
    rot = q.to_euler()
    m = rot.to_matrix()
    loc = (p0 + p1) / 2 - m @ Vector((0, 0, t / 2))
    if glow:
        o = vb.block(name, (L + t * 0.6, w, t), tuple(loc), col, bevel=0.03, emission=glow)
        o.rotation_euler = rot
    else:
        o = vb.solid(name, (L + t * 0.6, w, t), tuple(loc), col, bevel=0.04, rot=rot, studs=studs)
    return B.add(o, fx)


def seat_front(V, name, size, x, z, col, dy=0.0, emission=0.0, bevel=0.03, seg=1, rot=None):
    """Face piece seated on the merged head's front surface (max across its width)."""
    ys = [V.front_y(xx, z + size[2] * f) for xx in (x - size[0] * 0.45, x, x + size[0] * 0.45) for f in (0.15, 0.5, 0.85)]
    ys = [y for y in ys if y is not None]
    y = (max(ys) if ys else 0.0) + size[1] / 2 - 0.02 + dy
    return FACE(name, size, (x, y, z), col, bevel=bevel, seg=seg, emission=emission, rot=rot)


def snowflake(prefix, ctr, size, col, yaw=0.0, strength=4.0, fx=True, thick=0.2):
    """Flat 6-arm snowflake (3 crossed bars + core + arm tips) in a vertical plane facing yaw."""
    c = Vector(ctr)
    rz = Matrix.Rotation(yaw, 3, "Z")
    out = []
    for i in range(3):
        a = math.pi / 3 * i + math.pi / 2
        d = rz @ Vector((math.cos(a), 0, math.sin(a))) * size / 2
        out.append(bar(f"{prefix}Arm{i}", c - d, c + d, thick, thick, col, glow=strength, fx=fx))
        for s in (-1, 1):
            tip = c + d * 0.62 * s
            out.append(GLOW(f"{prefix}Tip{i}{s}", (thick * 1.7, thick * 1.1, thick * 1.7), tuple(tip - Vector((0, 0, thick * 0.85))),
                            col, strength, rot=(0, a + math.pi / 4, yaw), fx=fx))
    out.append(GLOW(f"{prefix}Core", (thick * 2, thick * 1.4, thick * 2), tuple(c - Vector((0, 0, thick))), col, strength,
                    rot=(0, math.pi / 4, yaw), fx=fx))
    return out


def cartoon_bone(prefix, p0, p1, r_shaft, r_knob, col, knob_col=None, glow=0.0, fx=False):
    """Classic cartoon bone: shaft + two knobs at each end (theme: bone-breaking game)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 0.1:
        side = d.cross(Vector((1, 0, 0)))
    side.normalize()
    bar(f"{prefix}Shaft", p0, p1, r_shaft * 2, r_shaft * 2, col, fx=fx)
    kc = knob_col or col
    for e, p in (("A", p0), ("B", p1)):
        for s in (-1, 1):
            q = p + side * r_knob * 0.75 * s
            BALL(f"{prefix}Knob{e}{s}", (r_knob, r_knob, r_knob), tuple(q), kc, seg=10, rings=6, fx=fx,
                 emission=glow, studs="none" if glow else "all")


def ring_of(prefix, n, radius, z, size, colours, ctr=(0.0, 0.0), strength=3.0, phase=0.0):
    for i in range(n):
        a = 2 * math.pi * i / n + phase
        GLOW(f"{prefix}{i}", size, (ctr[0] + math.cos(a) * radius, ctr[1] + math.sin(a) * radius, z),
             colours[i % len(colours)], strength, bevel=0.02, rot=(0, 0, a + math.pi / 2), fx=True)


def sparkles(prefix, pts, col, size=0.28, strength=5.0):
    for i, p in enumerate(pts):
        GLOW(f"{prefix}{i}", (size, size, size), p, col, strength, bevel=0.02, rot=(math.pi / 4, math.pi / 4, 0), fx=True)


# =============================================================================================
# 1. PEBBLE PUP (Common)
# =============================================================================================
def pebble_pup():
    global B
    B = Builder("PebblePup")
    rnd = random.Random(11)
    peb = {"base": "#8F9AA8", "dark": "#6A7383", "light": "#AEB7C4"}
    moss = {"base": "#6FCB4A", "dark": "#4FA83A", "light": "#9BE36A"}
    MUZ = "#F2DDB4"
    pack = {"base": "#E8432E", "dark": "#B02A1F", "light": "#FF7A5C"}
    GOLD, BLUE, BLUE_D = "#FFD93B", "#2E9BD6", "#1F74AD"
    V = Vox()
    for sx in (-1, 1):  # stubby legs
        for (y0, y1) in ((0.0, 1.0), (-2.0, -1.0)):
            V.box((min(sx * 0.5, sx * 1.5), y0, 0.0), (max(sx * 0.5, sx * 1.5), y1, 1.0), peb["base"])
    V.sell((0, -0.5, 1.55), (1.5, 1.75, 1.0), peb["base"], p=2.5)  # torso
    V.sell((0, 0.45, 3.55), (2.05, 1.6, 1.6), peb["base"], p=3.0)  # big head
    V.carve(lambda x, y, z: z > 1.9 and y > 1.85)  # flat face plane at y = 2.0
    V.sell((0, 2.05, 2.55), (1.5, 0.55, 0.6), MUZ, p=2.5)  # wide muzzle block
    V.paint(lambda x, y, z: z < 1.3 and y > -1.6 and abs(x) < 1.0 and z > 0.4, MUZ)  # belly
    V.mosaic(16, [peb["base"], peb["dark"], peb["light"], peb["base"]], {peb["base"]}, seed=4)  # pebble plates
    V.paint(lambda x, y, z: z < 0.5, peb["dark"], only=set(peb.values()))  # darker paw cuffs
    moss_patch = lambda x, y, z: (z > 4.2 and ((x - 0.5) ** 2 + (y + 0.1) ** 2 < 1.6 or (x + 0.9) ** 2 + (y - 0.6) ** 2 < 0.7)) \
        or (z > 2.0 and z < 3.0 and y < -0.9 and abs(x) < 1.2)
    V.paint_top(moss_patch, moss["base"], depth=1, only=set(peb.values()))
    V.paint_top(lambda x, y, z: z > 4.2 and (x - 0.9) ** 2 + (y + 0.5) ** 2 < 0.4, moss["dark"], only={moss["base"]})
    B.add(V.mesh("PebblePup_Blocks"))

    # ---- face ----
    for sx in (-1, 1):
        ex = sx * 1.0
        seat_front(V, f"Eye{sx}", (1.15, 0.14, 1.3), ex, 3.1, WHITE, bevel=0.16, seg=2)
        seat_front(V, f"Pupil{sx}", (0.66, 0.1, 0.86), ex - sx * 0.12, 3.25, PUPIL, dy=0.07, bevel=0.12, seg=2)
        seat_front(V, f"Sparkle{sx}", (0.24, 0.06, 0.24), ex - sx * 0.3, 3.8, WHITE, dy=0.14, emission=1.5)
        seat_front(V, f"SparkleSmall{sx}", (0.13, 0.06, 0.13), ex + sx * 0.02, 3.4, WHITE, dy=0.14, emission=1.5)
        seat_front(V, f"Brow{sx}", (0.75, 0.12, 0.22), ex + sx * 0.05, 4.55, "#565E6C", rot=(0, sx * 0.15, 0))
        seat_front(V, f"Blush{sx}", (0.5, 0.08, 0.26), sx * 1.05, 2.72, BLUSH)
    seat_front(V, "Nose", (0.78, 0.22, 0.42), 0, 2.58, PUPIL, bevel=0.12, seg=2)
    seat_front(V, "NoseShine", (0.2, 0.06, 0.1), -0.15, 2.84, WHITE, dy=0.2, emission=1.0)
    seat_front(V, "Mouth", (1.9, 0.12, 0.46), 0, 2.06, MOUTH, bevel=0.08, seg=2)
    seat_front(V, "Tongue", (0.7, 0.12, 0.28), 0.1, 2.03, TONGUE, dy=0.06, bevel=0.08, seg=2)
    for sx in (-1, 1):
        seat_front(V, f"Tooth{sx}", (0.2, 0.08, 0.16), sx * 0.3, 2.34, WHITE, dy=0.06)
        seat_front(V, f"MouthCorner{sx}", (0.36, 0.12, 0.14), sx * 1.0, 2.42, MOUTH, rot=(0, sx * -0.6, 0))

    # ---- big floppy pebble ears hanging past the cheeks (the "puppy" read from the front) ----
    for sx in (-1, 1):
        R(f"Ear{sx}", (0.62, 1.2, 2.1), (sx * 2.2, 0.35, 2.35), peb["dark"], radius=0.2, rot=(0, -sx * 0.22, 0))
        R(f"EarInner{sx}", (0.3, 0.8, 1.4), (sx * 1.98, 0.4, 2.55), MUZ, radius=0.1, rot=(0, -sx * 0.22, 0))
        R(f"EarTip{sx}", (0.7, 1.0, 0.5), (sx * 2.42, 0.35, 2.2), "#565E6C", radius=0.15, rot=(0, -sx * 0.22, 0))
        R(f"EarMoss{sx}", (0.85, 1.25, 0.34), (sx * 2.0, 0.35, 4.25), moss["dark"], radius=0.1, rot=(0, -sx * 0.25, 0))
    # ---- glued pebble chunks: what the pup is made of (varied size/rotation, intentional spots) ----
    chunks = [(-1.15, -1.05, 4.2, 0.95, "light"), (1.0, -1.05, 3.2, 0.85, "dark"), (-1.5, -1.55, 0.8, 0.85, "light"),
              (1.5, -1.5, 0.9, 0.8, "light"), (-1.55, 0.25, 1.15, 0.7, "dark"), (1.55, 0.45, 1.3, 0.62, "light"),
              (0.1, -1.3, 4.6, 0.7, "dark")]
    for i, (x, y, z, s, t) in enumerate(chunks):
        R(f"Pebble{i}", (s, s * rnd.uniform(0.85, 1.05), s * 0.7), (x, y, z), peb[t], radius=s * 0.24,
          rot=(rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), rnd.uniform(0, 1.5)))
        if i % 2 == 0:
            R(f"PebbleMoss{i}", (s * 0.7, s * 0.6, 0.22), (x, y, z + s * 0.62), moss["base"], radius=0.08,
              rot=(0, 0, rnd.uniform(0, 1.5)))
    # ---- moss tufts + sprout (silhouette feature) ----
    top = V.top_z(0.25, 0.25)
    for i, (x, y, s) in enumerate(((-0.7, 0.9, 0.55), (0.9, -0.35, 0.6), (-1.25, -0.4, 0.45), (1.2, 0.8, 0.42),
                                   (0.0, -0.9, 0.5), (0.4, 1.1, 0.38))):
        z = V.top_z(x, y) or top
        R(f"MossTuft{i}", (s, s * 0.9, s * 0.55), (x, y, z - 0.12), moss["light" if i % 2 else "base"], radius=s * 0.2,
          rot=(0, 0, rnd.uniform(0, 1.5)))
    CYL("SproutStem", 0.17, 0.15, 0.85, (0.15, 0.35, top - 0.1), moss["dark"], sides=8)
    for sx in (-1, 1):
        R(f"SproutLeaf{sx}", (0.95, 0.5, 0.2), (0.15 + sx * 0.45, 0.35, top + 0.62), moss["light"], radius=0.08,
          rot=(0, -sx * 0.45, sx * 0.3))
    R("SproutBud", (0.32, 0.32, 0.3), (0.15, 0.35, top + 0.7), moss["base"], radius=0.1)

    # ---- bandana ----
    for i, (w, z) in enumerate(((1.9, 1.62), (1.3, 1.32), (0.65, 1.02))):
        S(f"Bandana{i}", (w, 0.32, 0.32), (0, 1.1, z), BLUE if i != 1 else BLUE_D, bevel=0.06)
    R("BandanaKnot", (0.45, 0.4, 0.4), (1.15, 0.7, 1.6), BLUE_D, radius=0.1)

    # ---- toes / paw pads ----
    for sx in (-1, 1):
        for ly, face_y in ((0.5, 1.0), (-1.5, -1.0)):
            for t, tx in enumerate((-0.32, 0.0, 0.32)):
                R(f"Toe{sx}_{ly}_{t}", (0.28, 0.2, 0.26), (sx * 1.0 + tx, face_y + 0.06, 0.02), MUZ, radius=0.07)
        S(f"BackPad{sx}", (0.6, 0.12, 0.4), (sx * 1.0, -2.04, 0.15), MUZ, bevel=0.05)

    # ---- pebble tail ----
    for i, (y, z, s, c) in enumerate(((-2.2, 0.7, 0.62, peb["base"]), (-2.65, 0.92, 0.52, peb["light"]),
                                      (-3.05, 1.18, 0.44, peb["dark"]), (-3.35, 1.45, 0.36, moss["base"]))):
        R(f"Tail{i}", (s, s, s), (0, y, z), c, radius=s * 0.25, rot=(0.3 * i, 0, 0.4 * i))

    # ---- tiny hiking backpack (back hero detail) ----
    R("PackBody", (2.0, 1.1, 1.7), (0, -2.45, 1.3), pack["base"], radius=0.22)
    R("PackFlap", (2.1, 1.2, 0.42), (0, -2.5, 2.85), pack["dark"], radius=0.12)
    R("PackPocket", (1.3, 0.36, 0.85), (0, -3.08, 1.45), pack["dark"], radius=0.1)
    S("PackPocketFlap", (1.42, 0.42, 0.22), (0, -3.1, 2.28), pack["light"], bevel=0.05)
    S("PackBuckle", (0.36, 0.12, 0.34), (0, -3.36, 2.05), GOLD, bevel=0.04)
    for sx in (-1, 1):
        R(f"PackSidePocket{sx}", (0.36, 0.8, 0.95), (sx * 1.1, -2.45, 1.45), pack["dark"], radius=0.08)
        bar(f"PackStrap{sx}", (sx * 1.15, -1.95, 2.7), (sx * 1.5, -0.1, 1.0), 0.18, 0.32, pack["dark"])
        S(f"PackStrapBuckle{sx}", (0.12, 0.34, 0.3), (sx * 1.56, -0.75, 1.5), GOLD, bevel=0.03)
    CYL("Bedroll", 0.42, 0.42, 2.3, (-1.15, -2.45, 3.62), BLUE, sides=12, rot=(0, math.pi / 2, 0))
    for sx in (-1, 1):
        CYL(f"BedrollTie{sx}", 0.46, 0.46, 0.16, (sx * 0.6 - 0.08, -2.45, 3.62), pack["dark"], sides=12,
            rot=(0, math.pi / 2, 0))
    # carabiner + clip-on mini lantern (the only glow on a Common)
    for i, (p0, p1) in enumerate((((1.34, -2.95, 2.4), (1.34, -2.95, 1.85)), ((1.34, -2.95, 1.85), (1.34, -3.25, 1.85)),
                                  ((1.34, -3.25, 1.85), (1.34, -3.25, 2.4)))):
        bar(f"Carabiner{i}", p0, p1, 0.12, 0.12, GOLD)
    R("LanternFrame", (0.48, 0.48, 0.62), (1.34, -3.1, 1.08), "#3A3F4B", radius=0.08)
    GLOW("LanternCore", (0.34, 0.54, 0.4), (1.34, -3.1, 1.19), "#FFE27A", 4.0)
    S("LanternCap", (0.56, 0.56, 0.16), (1.34, -3.1, 1.7), "#3A3F4B", bevel=0.04)
    return B


# =============================================================================================
# 2. AVALANCHE PUG (Legendary, hero)
# =============================================================================================
def avalanche_pug():
    global B
    B = Builder("AvalanchePug")
    rnd = random.Random(23)
    snow = {"base": "#E8F3FB", "dark": "#C6DCEE", "light": "#FFFFFF"}
    ice = {"base": "#7FC4F0", "dark": "#4E96D6", "deep": "#3A6FB0", "light": "#BFE6FF"}
    hel = {"base": "#FF8A1F", "dark": "#E06A0C", "light": "#FFB066", "deep": "#B85208"}
    NEON, NEON_L = "#7CF7FF", "#BFFBFF"
    NAVY, NAVY_D, GOLD = "#2E3A55", "#1E2740", "#FFD93B"
    V = Vox()
    for sx in (-1, 1):
        for (y0, y1) in ((0.0, 1.0), (-2.0, -1.0)):
            V.box((min(sx * 0.75, sx * 1.75), y0, 0.0), (max(sx * 0.75, sx * 1.75), y1, 1.0), snow["base"])
    V.sell((0, -0.6, 1.6), (1.9, 1.85, 1.0), snow["base"], p=2.5)  # chunky torso
    V.sell((0, 0.4, 3.35), (2.55, 1.75, 1.45), snow["base"], p=3.5)  # wide, squat pug head
    V.carve(lambda x, y, z: z > 1.9 and y > 1.85)
    V.sell((0, 2.05, 2.4), (1.5, 0.55, 0.6), ice["base"], p=2.5)  # short pug muzzle (ice mask)
    V.paint(lambda x, y, z: y > 1.4 and z > 2.9 and z < 4.5 and ((abs(x) - 1.12) / 0.95) ** 2 + ((z - 3.65) / 0.85) ** 2 < 1,
            ice["base"])  # eye-patch mask
    # crash helmet (same merged mesh, so no coplanar overlaps): domed, darker rim, white stripe, dent
    V.sell((0, 0.3, 4.3), (2.8, 2.1, 1.65), hel["base"], p=2.3, pred=lambda x, y, z: z > 4.4)
    V.paint(lambda x, y, z: z < 5.0, hel["dark"], only={hel["base"]})
    V.paint(lambda x, y, z: abs(x) < 0.5 and z > 5.0, WHITE, only={hel["base"]})
    dent = Vector((-1.6, 0.9, 5.45))
    V.paint(lambda x, y, z: (Vector((x, y, z)) - dent).length < 1.0, hel["deep"], only={hel["base"], hel["dark"]})
    V.carve(lambda x, y, z: (Vector((x, y, z)) - dent).length < 0.55 and z > 5.0)
    V.paint(lambda x, y, z: z > 5.6 and x > 0.4 and y > 0.2, hel["light"], only={hel["base"]})  # gloss highlight
    V.paint(lambda x, y, z: z < 0.5, ice["light"], only={snow["base"]})  # frosty socks
    V.paint(lambda x, y, z: y < -0.8 and 3.4 < z < 4.5, ice["light"], only={snow["base"]})  # frosted back of head
    V.paint(lambda x, y, z: y < -0.8 and 2.2 < z < 4.5 and abs(x) < 0.5, ice["base"], only={snow["base"], ice["light"]})
    V.paint(lambda x, y, z: z < 1.25 and z >= 0.5 and abs(x) < 1.3, snow["dark"], only={snow["base"]})  # belly shade
    V.paint_top(lambda x, y, z: y < -0.7 and z < 3.2, ice["light"], depth=1, only={snow["base"]})  # frost saddle
    B.add(V.mesh("AvalanchePug_Blocks"))

    # ---- face ----
    for sx in (-1, 1):
        ex = sx * 1.12
        seat_front(V, f"EyeRim{sx}", (1.6, 0.1, 1.55), ex, 2.95, ice["deep"], bevel=0.18, seg=2)
        seat_front(V, f"Eye{sx}", (1.36, 0.14, 1.32), ex, 3.06, WHITE, dy=0.03, bevel=0.18, seg=2)
        seat_front(V, f"Pupil{sx}", (0.76, 0.1, 0.96), ex - sx * 0.16, 3.2, PUPIL, dy=0.1, bevel=0.14, seg=2)
        seat_front(V, f"PupilGlint{sx}", (0.36, 0.06, 0.36), ex - sx * 0.16, 3.32, ice["dark"], dy=0.15, bevel=0.06)
        seat_front(V, f"Sparkle{sx}", (0.28, 0.06, 0.28), ex - sx * 0.38, 3.82, WHITE, dy=0.19, emission=1.5)
        seat_front(V, f"SparkleSmall{sx}", (0.14, 0.06, 0.14), ex + sx * 0.05, 3.42, WHITE, dy=0.19, emission=1.5)
        seat_front(V, f"Blush{sx}", (0.55, 0.08, 0.26), sx * 1.05, 2.72, BLUSH)
        seat_front(V, f"Jowl{sx}", (0.42, 0.12, 0.16), sx * 1.02, 2.36, MOUTH, rot=(0, sx * -0.6, 0))
        seat_front(V, f"Fang{sx}", (0.2, 0.08, 0.18), sx * 0.42, 2.28, WHITE, dy=0.06)
    for i, (w, z) in enumerate(((0.8, 3.15), (0.55, 3.45), (0.32, 3.75))):  # pug wrinkles on the nose bridge
        seat_front(V, f"Wrinkle{i}", (w, 0.12, 0.17), 0, z, ice["dark"], bevel=0.05)
    seat_front(V, "Nose", (0.95, 0.26, 0.5), 0, 2.52, PUPIL, bevel=0.14, seg=2)
    seat_front(V, "NoseShine", (0.24, 0.06, 0.12), -0.2, 2.82, WHITE, dy=0.24, emission=1.0)
    seat_front(V, "Mouth", (2.0, 0.12, 0.42), 0, 2.06, MOUTH, bevel=0.08, seg=2)
    seat_front(V, "Tongue", (0.66, 0.16, 0.62), 0.12, 1.72, TONGUE, dy=0.04, bevel=0.14, seg=2)  # tongue blep
    seat_front(V, "TongueLine", (0.08, 0.06, 0.34), 0.12, 1.86, "#E04C7E", dy=0.16)

    # ---- snowball cheeks (jowly pug silhouette) + floppy folded ears under the helmet rim ----
    for sx in (-1, 1):
        BALL(f"SnowCheek{sx}", (0.95, 0.75, 0.85), (sx * 2.15, 1.55, 2.45), snow["light"], seg=12, rings=8)
        BALL(f"SnowCheekTop{sx}", (0.45, 0.4, 0.4), (sx * 2.45, 1.45, 3.15), ice["light"], seg=10, rings=6)
        R(f"Ear{sx}", (0.55, 1.05, 1.1), (sx * 2.75, 0.2, 3.55), ice["dark"], radius=0.16, rot=(0, sx * 0.55, 0))
        R(f"EarFold{sx}", (0.45, 0.8, 0.4), (sx * 3.05, 0.25, 3.5), ice["deep"], radius=0.1, rot=(0, sx * 0.55, 0))
    # ---- helmet hardware: goggles, flipped-up visor, chin straps, stickers, back plate ----
    gz = 4.6
    gy = max(V.front_y(x, z) or 0 for x in (-1.2, -0.6, 0.6, 1.2) for z in (4.6, 4.9, 5.2, 5.5))
    vz = (V.top_z(0.25, 1.25) or 5.5) - 0.35
    for sx in (-1, 1):
        CYL(f"GoggleFrame{sx}", 0.52, 0.52, 0.34, (sx * 0.78, gy - 0.12, gz + 0.45), NAVY, sides=12, rot=(-math.pi / 2, 0, 0))
        CYL(f"GoggleLens{sx}", 0.38, 0.38, 0.08, (sx * 0.78, gy + 0.2, gz + 0.45), NEON, sides=12,
            rot=(-math.pi / 2, 0, 0), emission=1.6)
        FACE(f"GoggleGlint{sx}", (0.16, 0.06, 0.3), (sx * 0.78 - 0.18, gy + 0.3, gz + 0.5), WHITE, emission=2.0,
             rot=(0, 0.5, 0))
        S(f"GoggleStrap{sx}", (0.22, 2.6, 0.42), (sx * (V.side_x(0.3, 4.75, sx) * sx + 0.08), 0.3, 4.55), NAVY_D, bevel=0.04)
        bar(f"ChinStrap{sx}", (sx * 2.5, 0.35, 4.55), (sx * 2.3, 0.7, 2.15), 0.34, 0.2, hel["dark"])
        S(f"ChinBuckle{sx}", (0.24, 0.42, 0.36), (sx * 2.33, 0.68, 2.0), GOLD, bevel=0.05)
        CYL(f"VisorScrew{sx}", 0.22, 0.22, 0.2, (sx * 1.86, 1.55, vz + 0.1), NAVY, sides=8, rot=(0, sx * math.pi / 2, 0))
    bar("GoggleBridge", (-0.22, gy + 0.05, gz + 0.45), (0.22, gy + 0.05, gz + 0.45), 0.25, 0.25, NAVY)
    # motocross-style peak visor jutting forward over the goggles (silhouette feature)
    S("Visor", (3.7, 1.5, 0.26), (0, 2.0, vz), hel["light"], bevel=0.06, rot=(0.22, 0, 0))
    S("VisorStripe", (0.62, 1.52, 0.3), (0, 2.0, vz + 0.01), WHITE, bevel=0.04, rot=(0.22, 0, 0))
    S("VisorEdge", (3.8, 0.3, 0.34), (0, 2.72, vz + 0.12), NAVY, bevel=0.05, rot=(0.22, 0, 0))
    # stickers (flat raised decals on the dome sides) — bone (theme) + star
    sxp = V.side_x(0.6, 5.25, 1)
    cartoon_bone("StickerBone", (sxp + 0.04, 0.0, 5.05), (sxp + 0.04, 1.15, 5.5), 0.12, 0.17, "#FFF1CF")
    sxm = V.side_x(0.2, 5.25, -1)
    for i in range(2):
        FACE(f"StickerStar{i}", (0.12, 0.62, 0.62), (sxm - 0.04, 0.1, 5.0), GOLD, rot=(math.pi / 4 * i, 0, 0))
    for i, (p0, p1) in enumerate((((-1.95, 1.55, 5.95), (-1.5, 1.4, 5.55)), ((-1.5, 1.4, 5.55), (-1.6, 1.55, 5.15)))):
        bar(f"DentCrack{i}", p0, p1, 0.14, 0.14, hel["deep"])
    by = V.back_y(0.25, 5.25)
    R("BackPlate", (1.3, 0.2, 0.95), (0, by - 0.06, 4.75), GOLD, radius=0.06)
    snowflake("BackPlateFlake", (0, by - 0.2, 5.22), 0.7, NAVY, yaw=0.0, strength=0.0, fx=False, thick=0.13)
    # ---- frosty mane collar: an ORDERED ruff of chunky snow puffs, alternating snow / ice (fluffy, NOT spikes) ----
    for i in range(11):
        a = math.radians(150 + 240 * i / 10)  # sides + back, leaves the face clear
        x, y = math.cos(a) * 2.15, -0.5 + math.sin(a) * 2.1
        col = snow["light"] if i % 2 == 0 else ice["base"]
        R(f"Mane{i}", (1.05, 1.05, 0.85), (x, y, 1.75), col, radius=0.3, rot=(0, 0, a))
        R(f"ManeTip{i}", (0.55, 0.55, 0.4), (x * 1.12, -0.5 + (y + 0.5) * 1.12, 2.15), ice["dark"] if i % 2 == 0 else ice["light"],
          radius=0.15, rot=(0, 0, a))
    for i in range(6):
        a = math.radians(205 + 130 * i / 5)
        R(f"ManeBack{i}", (0.85, 0.85, 0.7), (math.cos(a) * 1.55, -0.5 + math.sin(a) * 1.6, 2.5), ice["light"] if i % 2 else snow["light"],
          radius=0.25, rot=(0, 0, a))
    hb = V.back_y(0.25, 3.25)
    snowflake("HeadBackFlake", (0, hb - 0.1, 3.0), 0.9, ice["deep"], strength=0.0, fx=False, thick=0.16)
    # ---- chest: collar band + glowing snowflake tag ----
    S("Collar", (2.5, 0.4, 0.4), (0, 1.0, 1.9), ice["deep"], bevel=0.08)
    CYL("TagRing", 0.2, 0.2, 0.12, (0, 1.16, 1.85), GOLD, sides=8, rot=(-math.pi / 2, 0, 0))
    snowflake("Tag", (0, 1.3, 1.42), 0.85, NEON, yaw=0.0, strength=2.0, fx=False, thick=0.17)

    # ---- paws: glowing ice toe pads ----
    for sx in (-1, 1):
        for ly, fy in ((0.5, 1.0), (-1.5, -1.0)):
            for t, tx in enumerate((-0.32, 0.0, 0.32)):
                GLOW(f"ToePad{sx}_{ly}_{t}", (0.26, 0.14, 0.24), (sx * 1.25 + tx, fy + 0.05, 0.04), NEON, 1.8)
        S(f"HeelPad{sx}", (0.62, 0.12, 0.42), (sx * 1.25, -2.04, 0.14), ice["base"], bevel=0.05)
        for i, (y, z) in enumerate(((-0.9, 1.35), (-0.15, 1.9))):  # raised snowflake decals on the flanks
            xs = V.side_x(y, z + 0.1, sx)
            c = Vector((xs + sx * 0.02, y, z + 0.15))
            for j in range(3):
                a = math.pi / 3 * j
                d = Vector((0, math.cos(a), math.sin(a))) * 0.36
                bar(f"FlankFlake{sx}_{i}_{j}", c - d, c + d, 0.22, 0.12, ice["dark"])

    # ---- curly tail with glowing snowball tip ----
    for i, (y, z, s) in enumerate(((-2.65, 2.55, 0.66), (-3.0, 3.0, 0.6), (-2.95, 3.5, 0.55), (-2.6, 3.8, 0.5))):
        R(f"Tail{i}", (s, s, s), (0, y, z), ice["base"] if i % 2 == 0 else ice["light"], radius=s * 0.25,
          rot=(0.4 * i, 0, 0))
    BALL("TailTip", (0.38, 0.38, 0.38), (0, -2.25, 4.1), NEON, seg=10, rings=6, emission=1.8, studs="none")

    # ---- FX (Legendary): snowflake orbiters, double aura ring, frost sparkles ----
    for i, deg in enumerate((15, 50, 135, 170, 215, 270, 325)):  # never parked in front of the face
        a = math.radians(deg)
        snowflake(f"Orbit{i}_", (math.cos(a) * 3.9, -0.3 + math.sin(a) * 3.9, 2.4 + (i % 3) * 1.15), 0.95,
                  NEON, yaw=a - math.pi / 2, strength=1.6, thick=0.2)
    ring_of("AuraOuter", 26, 3.45, 0.04, (0.72, 0.36, 0.1), [NEON, "#3FD4FF"], ctr=(0, -0.3), strength=1.5)
    ring_of("AuraInner", 18, 2.85, 0.04, (0.5, 0.26, 0.08), [NEON_L], ctr=(0, -0.3), strength=1.2, phase=0.1)
    sparkles("Frost", [(-3.0, 1.4, 5.2), (3.1, 1.0, 5.6), (-2.6, -2.4, 4.8), (2.5, -2.6, 1.8), (0.0, 2.9, 6.2),
                       (-3.4, 0.0, 1.3)], NEON, size=0.26, strength=2.0)
    return B


# =============================================================================================
# 3. SKELLY-CAT (Secret)
# =============================================================================================
def skelly_cat():
    global B
    B = Builder("SkellyCat")
    rnd = random.Random(37)
    bone = {"base": "#FFF1CF", "dark": "#E8D3A2", "light": "#FFFAEB", "deep": "#CDB27A"}
    plum = {"base": "#4B3A78", "dark": "#33275A", "light": "#6A55A3"}
    MINT, PINK, GOLD = "#7DFFE9", "#FF3EC8", "#FFD93B"
    RAINBOW = ["#FF4D6D", "#FF9F1C", "#FFE14D", "#5CFF7A", "#4DC3FF", "#B26BFF"]
    V = Vox()
    V.sell((0, -0.5, 1.75), (1.35, 1.7, 0.9), plum["base"], p=2.5)  # soft plum core between the bones
    V.paint(lambda x, y, z: z < 1.4, plum["dark"])
    V.sell((0, 0.45, 3.75), (2.1, 1.55, 1.6), bone["base"], p=3.2)  # skull-ish cute head
    V.carve(lambda x, y, z: z > 2.0 and y > 1.85)
    V.carve(lambda x, y, z: z < 2.9 and abs(x) > 1.6 and y > -0.5)  # narrower jaw = skull read
    for sx in (-1, 1):  # stepped triangular cat ears (part of the merged mass)
        for z, xs in ((5.25, (0.75, 1.75)), (5.75, (0.75, 1.75)), (6.25, (1.25, 1.75)), (6.75, (1.25, 1.25))):
            lo, hi = sorted((sx * xs[0], sx * xs[1]))
            V.box((lo, 0.25 if z > 6 else -0.25, z), (hi, 0.75, z), bone["base"])
    V.paint(lambda x, y, z: z > 6.4, bone["dark"], only={bone["base"]})  # ear tips
    V.paint(lambda x, y, z: y < -0.6 and z < 3.6, bone["dark"], only={bone["base"]})  # shaded back of skull
    V.paint(lambda x, y, z: z < 2.75, bone["dark"], only={bone["base"]})  # jaw shade
    B.add(V.mesh("SkellyCat_Blocks"))

    # ---- face: sockets, glowing eyes, heart nose, toothy grin ----
    for sx in (-1, 1):
        ex = sx * 1.0
        seat_front(V, f"Socket{sx}", (1.72, 0.1, 1.8), ex, 3.05, plum["base"], bevel=0.22, seg=2)
        seat_front(V, f"Eye{sx}", (1.44, 0.14, 1.52), ex, 3.19, "#E6FFFA", dy=0.03, bevel=0.2, seg=2)
        seat_front(V, f"Iris{sx}", (1.0, 0.08, 1.08), ex - sx * 0.12, 3.33, MINT, dy=0.1, bevel=0.16, seg=2, emission=1.4)
        seat_front(V, f"Pupil{sx}", (0.56, 0.08, 0.76), ex - sx * 0.16, 3.47, PUPIL, dy=0.15, bevel=0.12, seg=2)
        seat_front(V, f"Sparkle{sx}", (0.3, 0.06, 0.3), ex - sx * 0.42, 3.95, WHITE, dy=0.2, emission=1.2)
        seat_front(V, f"SparkleSmall{sx}", (0.14, 0.06, 0.14), ex + sx * 0.1, 3.5, WHITE, dy=0.2, emission=1.2)
        seat_front(V, f"Blush{sx}", (0.5, 0.08, 0.26), sx * 1.55, 2.92, BLUSH)
        seat_front(V, f"InnerEar{sx}", (0.5, 0.08, 0.8), sx * 1.38, 5.6, "#FF9CC8")
        for w, (dz, dzz) in enumerate(((0.0, 0.15), (0.3, 0.45), (-0.3, -0.2))):  # chunky whiskers
            bar(f"Whisker{sx}_{w}", (sx * 1.85, 1.75, 2.95 + dz), (sx * 3.05, 1.9, 2.95 + dzz), 0.18, 0.18, plum["light"])
        seat_front(V, f"Nose{sx}", (0.3, 0.1, 0.3), sx * 0.11, 2.86, plum["dark"], rot=(0, sx * 0.7, 0))
        seat_front(V, f"MouthCorner{sx}", (0.34, 0.12, 0.14), sx * 1.12, 2.58, plum["dark"], rot=(0, sx * -0.6, 0))
        R(f"CheekBone{sx}", (0.5, 0.95, 0.6), (sx * 1.92, 1.05, 2.95), bone["light"], radius=0.14)
    seat_front(V, "NoseTip", (0.24, 0.1, 0.24), 0, 2.74, plum["dark"], rot=(0, math.pi / 4, 0))
    seat_front(V, "Mouth", (2.1, 0.12, 0.44), 0, 2.2, plum["dark"], bevel=0.08, seg=2)
    seat_front(V, "Tongue", (0.66, 0.1, 0.2), 0.15, 2.22, TONGUE, dy=0.05, bevel=0.06)
    for i, x in enumerate((-0.6, -0.2, 0.2, 0.6)):
        seat_front(V, f"Tooth{i}", (0.32, 0.08, 0.24), x, 2.42, bone["light"], dy=0.06)

    # ---- skull top: cute bandage (ragdoll theme) + stitched seam on the back ----
    tz = V.top_z(0.25, 0.25)
    S("BandageA", (1.7, 0.5, 0.14), (0.55, -0.25, tz - 0.06), "#FFD0A8", bevel=0.04, rot=(0, 0, 0.7))
    S("BandageB", (1.7, 0.5, 0.14), (0.55, -0.25, tz - 0.04), "#FFC594", bevel=0.04, rot=(0, 0, -0.7))
    S("BandagePad", (0.5, 0.5, 0.12), (0.55, -0.25, tz + 0.06), "#FFF3E6", bevel=0.03)
    by = V.back_y(0.25, 3.75)
    FACE("Seam", (0.18, 0.08, 1.9), (0.0, by - 0.03, 2.9), plum["base"])
    for i in range(4):
        FACE(f"Stitch{i}", (0.6, 0.08, 0.16), (0.0, by - 0.06, 3.1 + i * 0.45), plum["base"], rot=(0, 0.25 * (i % 2 * 2 - 1), 0))

    # ---- ribcage: chunky bone hoops around the plum core (side + back read) ----
    for r, yy in enumerate((0.45, -0.2, -0.85, -1.5)):
        sfac = (1 - abs((yy + 0.5) / 1.7) ** 2.5) ** (1 / 2.5)
        rx, rz = 1.35 * sfac + 0.28, 0.9 * sfac + 0.26
        pts = [(rx * math.cos(t), yy, 1.75 + rz * math.sin(t)) for t in [math.radians(a) for a in range(-30, 211, 40)]]
        for s in range(len(pts) - 1):
            bar(f"Rib{r}_{s}", pts[s], pts[s + 1], 0.42, 0.32, bone["base"] if r % 2 == 0 else bone["light"])
    S("Sternum", (0.6, 0.34, 1.0), (0, 1.12, 1.05), bone["base"], bevel=0.08)
    for i, yy in enumerate((0.6, 0.05, -0.5, -1.05, -1.6)):  # spine vertebrae (rounded knobs, not spikes)
        R(f"Vertebra{i}", (0.6, 0.42, 0.34), (0, yy, 2.72), bone["dark"] if i % 2 else bone["base"], radius=0.1)
    R("Pelvis", (1.7, 0.6, 0.85), (0, -2.05, 1.1), bone["base"], radius=0.18)
    for sx in (-1, 1):
        BALL(f"HipKnob{sx}", (0.32, 0.32, 0.32), (sx * 0.85, -2.1, 1.55), bone["light"], seg=10, rings=6)

    # ---- bone legs: top knob, shaft, double knuckle, paw + toe beans ----
    for sx in (-1, 1):
        for ly in (0.5, -1.5):
            x = sx * 0.85
            BALL(f"LegTopKnob{sx}{ly}", (0.4, 0.4, 0.36), (x, ly, 1.1), bone["light"], seg=10, rings=6)
            CYL(f"LegShaft{sx}{ly}", 0.27, 0.27, 0.8, (x, ly, 0.35), bone["base"], sides=8)
            for t in (-1, 1):
                BALL(f"LegKnuckle{sx}{ly}{t}", (0.26, 0.26, 0.24), (x + t * 0.17, ly, 0.42), bone["dark"], seg=10, rings=6)
            R(f"Paw{sx}{ly}", (0.8, 0.9, 0.36), (x, ly + 0.08, 0.0), bone["light"], radius=0.14)
            for t, tx in enumerate((-0.24, 0.0, 0.24)):
                FACE(f"ToeBean{sx}{ly}{t}", (0.18, 0.08, 0.14), (x + tx, ly + 0.55, 0.12), "#FF9CC8", bevel=0.04)

    # ---- neon collar + bell ----
    for i in range(10):
        a0, a1 = 2 * math.pi * i / 10, 2 * math.pi * (i + 1) / 10
        bar(f"Collar{i}", (math.cos(a0) * 1.45, -0.25 + math.sin(a0) * 1.55, 2.38), (math.cos(a1) * 1.45, -0.25 + math.sin(a1) * 1.55, 2.38),
            0.3, 0.26, PINK, glow=1.8)
    BALL("Bell", (0.34, 0.3, 0.34), (0, 1.42, 1.4), GOLD, seg=12, rings=8)
    FACE("BellSlot", (0.3, 0.08, 0.08), (0, 1.7, 1.25), "#8A5A00")

    # ---- bone tail: vertebra chain curling up into a cartoon bone (silhouette feature) ----
    chain = [(-2.45, 1.55, 0.62), (-2.9, 1.95, 0.58), (-3.2, 2.5, 0.55), (-3.25, 3.1, 0.52), (-3.05, 3.65, 0.48),
             (-2.7, 4.1, 0.45)]
    for i, (y, z, s) in enumerate(chain):
        R(f"TailBone{i}", (s, s * 0.9, s * 0.7), (0, y, z - s * 0.35), bone["base"] if i % 2 == 0 else bone["light"],
          radius=s * 0.22, rot=(math.atan2(-(z - 1.5), 1) * 0.6, 0, 0))
        if i:
            py, pz, _ = chain[i - 1]
            BALL(f"TailDisc{i}", (0.22, 0.22, 0.22), (0, (y + py) / 2, (z + pz) / 2), plum["light"], seg=8, rings=5)
    cartoon_bone("TailTip", (0, -2.55, 4.35), (0, -2.3, 5.25), 0.2, 0.27, bone["light"])

    # ---- FX (Secret = most glow): rainbow aura ring, inner ring, orbiting little bones, sparkles ----
    ring_of("Aura", 30, 3.4, 0.04, (0.62, 0.36, 0.12), RAINBOW, ctr=(0, -0.4), strength=1.6)
    ring_of("AuraInner", 20, 2.85, 0.04, (0.48, 0.24, 0.08), [MINT], ctr=(0, -0.4), strength=1.2, phase=0.1)
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        c = Vector((math.cos(a) * 3.7, -0.4 + math.sin(a) * 3.7, 2.4 + (i % 3) * 1.1))
        d = Vector((-math.sin(a), math.cos(a), 0.45)).normalized() * 0.45
        cartoon_bone(f"OrbitBone{i}_", c - d, c + d, 0.14, 0.18, bone["light"], knob_col=RAINBOW[i], glow=2.0, fx=True)
    sparkles("Spark", [(-3.0, 1.5, 5.6), (3.2, 0.8, 5.0), (-2.4, -2.8, 4.4), (2.8, -2.6, 2.0), (0.4, 3.0, 6.0),
                       (-3.5, -0.2, 1.4), (1.6, -3.4, 5.6), (3.5, 2.2, 3.0)], "#FFF6A8", size=0.26, strength=2.5)
    return B


# =============================================================================================
# 4. TRAILHEAD EGG
# =============================================================================================
EGG_ACCENT = "#FF8A1F"  # recolorable: material renamed "EggAccent" on export


def egg_trailhead(accent=EGG_ACCENT):
    global B
    B = Builder("TrailheadEgg")
    rnd = random.Random(5)
    green = kit.shades("#4CC24A")
    stone = {"base": "#8E96A3", "dark": "#6E7683", "light": "#B4BBC6"}
    SNOW, CREAM, ROPE, ROPE_D = "#F4FBFF", "#FFF6EA", "#D8B07A", "#B58A52"
    zc, hz, R0 = 3.15, 2.95, 2.25

    def egg_r(z):
        t = (z - zc) / hz
        return R0 * math.sqrt(max(0.0, 1 - t * t)) * (1 - 0.17 * t)

    def band(z):
        return 0.22 if int((z - 0.2) / 1.0) % 2 == 0 else 0.0  # stacked rings: every other band steps out

    V = Vox()
    for key, q in V._cells((-3, -3, 0.0), (3, 3, 6.3)):
        x, y, z = q
        if z < zc - hz or z > zc + hz:
            continue
        if math.hypot(x, y) <= egg_r(z) + band(z) - 0.05:
            V.v[key] = CREAM

    def ang(x, y):
        return math.atan2(y, x)

    V.paint(lambda x, y, z: z < 1.5, green["base"])
    V.paint(lambda x, y, z: z < 0.75, green["dark"])
    V.paint(lambda x, y, z: 1.5 <= z < 3.6 + 0.55 * math.sin(3 * ang(x, y)) + 0.35 * math.sin(7 * ang(x, y) + 1), stone["base"])
    V.paint(lambda x, y, z: 2.7 <= z < 3.0, stone["dark"], only={stone["base"]})
    V.paint(lambda x, y, z: z >= 3.0 and z < 3.6 + 0.55 * math.sin(3 * ang(x, y)) + 0.35 * math.sin(7 * ang(x, y) + 1)
            and math.sin(3 * ang(x, y)) > 0.3, stone["light"], only={stone["base"]})
    V.paint(lambda x, y, z: z >= 3.4 and z < 4.3 + 0.4 * math.sin(3 * ang(x, y)), SNOW, only={CREAM})  # snowy peak band
    B.add(V.mesh("TrailheadEgg_Blocks"))

    # ---- braided rope band (twisted segments, two tans) ----
    rz = 2.35
    rr = max(math.hypot(_c(i), _c(j)) for (i, j, k) in V.v if abs(_c(k) - (rz + 0.15)) < 0.26) + 0.08
    n = 28
    for i in range(n):
        a = 2 * math.pi * i / n
        R(f"Rope{i}", (0.62, 0.42, 0.4), (math.cos(a) * rr, math.sin(a) * rr, rz), ROPE if i % 2 else ROPE_D,
          radius=0.14, rot=(0.5 if i % 2 else -0.5, 0, a + math.pi / 2))
    # ---- carabiner clipped to the rope (accent) + glowing gem ----
    fy = rr + 0.2
    pts = [(-0.4, 2.35), (-0.5, 1.6), (-0.3, 1.15), (0.3, 1.15), (0.5, 1.6), (0.4, 2.35)]
    for i in range(len(pts) - 1):
        bar(f"Carabiner{i}", (pts[i][0], fy, pts[i][1]), (pts[i + 1][0], fy, pts[i + 1][1]), 0.26, 0.26, accent)
    bar("CarabinerGate", (-0.35, fy + 0.12, 2.2), (0.38, fy + 0.12, 1.9), 0.18, 0.18, "#C9D1DC")
    GLOW("CarabinerGem", (0.36, 0.2, 0.36), (0, fy + 0.04, 1.4), "#FFE27A", 4.0, rot=(0, math.pi / 4, 0))
    # ---- trail-marker blazes painted on the stone band (raised, purposeful: it's a trail egg) ----
    for i, a in enumerate((math.radians(150), math.radians(235), math.radians(320))):
        r = egg_r(3.0) + band(3.0) + 0.05
        for j, (dz, col, w) in enumerate(((0.0, WHITE, 0.6), (0.18, accent, 0.4))):
            S(f"Blaze{i}_{j}", (w, 0.12, 0.62 - j * 0.24), (math.cos(a) * (r + 0.02 * j), math.sin(a) * (r + 0.02 * j),
                                                       2.95 + dz * 0.6), col, bevel=0.03, rot=(0, 0, a + math.pi / 2))
    # ---- mountain-flag topper ----
    tz = V.top_z(0.25, 0.25)
    R("TopRock", (1.5, 1.3, 0.55), (0, 0, tz - 0.15), stone["dark"], radius=0.14, rot=(0, 0, 0.3))
    R("TopRock2", (1.0, 0.9, 0.5), (0.1, -0.05, tz + 0.35), stone["base"], radius=0.12, rot=(0, 0, -0.2))
    R("TopSnow", (0.75, 0.7, 0.28), (0.1, -0.05, tz + 0.8), SNOW, radius=0.1)
    CYL("FlagPole", 0.09, 0.09, 1.7, (0.35, 0.1, tz + 0.9), "#8A5530", sides=8)
    BALL("FlagKnob", (0.15, 0.15, 0.15), (0.35, 0.1, tz + 2.62), "#FFD93B", seg=8, rings=5)
    for i, (w, h, dz) in enumerate(((1.0, 0.62, 0.0), (0.55, 0.36, 0.13))):
        S(f"Flag{i}", (w, 0.14 + 0.04 * i, h), (0.35 + w / 2, 0.1, tz + 1.95 + dz), accent if i == 0 else WHITE, bevel=0.03)
    # ---- base: grass ring + pebbles (keeps the egg planted on an egg stand) ----
    for i in range(7):
        a = 2 * math.pi * i / 7 + 0.3
        s = rnd.uniform(0.55, 0.8)
        R(f"BaseRock{i}", (s, s * 0.9, s * 0.6), (math.cos(a) * 1.55, math.sin(a) * 1.55, 0.0), stone["base" if i % 2 else "dark"],
          radius=s * 0.2, rot=(0, 0, rnd.uniform(0, 1.5)))
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.75
        for j in range(2):
            S(f"Grass{i}_{j}", (0.18, 0.18, 0.55 - j * 0.15), (math.cos(a) * 1.75 + j * 0.2, math.sin(a) * 1.75, 0.0),
              green["light"] if j else green["base"], bevel=0.03, rot=(0.25 * (j * 2 - 1), 0, a))
    sparkles("EggSpark", [(-2.3, 1.6, 4.8), (2.4, 1.2, 3.8), (1.5, -2.0, 5.4), (-1.8, -1.8, 2.2)], "#FFE27A", size=0.24)
    return B


# =============================================================================================
# 5. CURRENCY ICON MODELS
# =============================================================================================
def icon_cash():
    global B
    B = Builder("IconCash")
    g = {"base": "#FFD93B", "dark": "#E0A800", "light": "#FFF08A", "deep": "#B98400"}
    up = (-math.pi / 2, 0, 0)  # cylinder axis -> +y (coin faces the camera)
    CYL("CoinBody", 1.6, 1.6, 0.6, (0, -0.3, 1.75), g["dark"], sides=20, rot=up)
    for side in (1, -1):
        CYL(f"CoinFace{side}", 1.25, 1.25, 0.12, (0, side * 0.24 - (0.12 if side < 0 else 0), 1.75), g["base"], sides=20, rot=up)
        for i in range(20):  # chunky segmented rim
            a0, a1 = 2 * math.pi * i / 20, 2 * math.pi * (i + 1) / 20
            bar(f"Rim{side}_{i}", (math.cos(a0) * 1.42, side * 0.33, 1.75 + math.sin(a0) * 1.42),
                (math.cos(a1) * 1.42, side * 0.33, 1.75 + math.sin(a1) * 1.42), 0.22, 0.3,
                g["light"] if i % 2 else g["base"], up=(0, 1, 0))
        # stamped bone (theme) — raised shaft + four knobs, tilted
        sy = side * 0.42
        d = Vector((math.cos(0.6), 0, math.sin(0.6))) * 0.62
        c = Vector((0, sy, 1.75))
        bar(f"BoneShaft{side}", c - d, c + d, 0.24, 0.42, g["light"])
        perp = Vector((-math.sin(0.6), 0, math.cos(0.6)))
        for e in (-1, 1):
            for s in (-1, 1):
                BALL(f"BoneKnob{side}{e}{s}", (0.26, 0.16, 0.26), tuple(c + d * e * 1.05 + perp * s * 0.2), g["light"], seg=10, rings=6)
    for i, (x, z, s) in enumerate(((-0.9, 2.75, 0.5), (1.15, 0.95, 0.32))):  # sparkle glints
        for k in range(2):
            GLOW(f"Glint{i}{k}", (s, 0.06, s * 0.22), (x, 0.62, z), "#FFFFFF", 5.0, rot=(0, math.pi / 2 * k + math.pi / 4, 0))
    return B


def icon_gem():
    global B
    B = Builder("IconGem")
    facets = ["#FFB02E", "#FF8A1F", "#FFD36B", "#D9610A"]
    rz = math.pi / 8  # puts a flat facet on +y

    def faceted(o, start=0):
        o.data.materials.clear()
        mats = [vb.palette_material(f"Gem{c}", c, roughness=0.25) for c in facets]
        for m in mats:
            o.data.materials.append(m)
        for i, p in enumerate(o.data.polygons):
            p.material_index = (i + start) % len(mats)
        return o

    pav = CYL("GemPavilion", 0.0, 1.5, 1.3, (0, 0, 0.0), facets[1], sides=8, rot=(0, 0, rz), studs="none")
    gir = CYL("GemGirdle", 1.5, 1.5, 1.2, (0, 0, 1.3), facets[0], sides=8, rot=(0, 0, rz), studs="none")
    crn = CYL("GemCrown", 1.5, 0.9, 0.7, (0, 0, 2.5), facets[2], sides=8, rot=(0, 0, rz), studs="none")
    tab = CYL("GemTable", 0.9, 0.9, 0.08, (0, 0, 3.2), facets[2], sides=8, rot=(0, 0, rz), studs="none")
    for i, o in enumerate((pav, gir, crn)):
        faceted(o, i)
    fy = 1.5 * math.cos(math.pi / 8)
    # SNAP crack: neon zig-zag across the front facet + side facets
    zz = [(-0.55, 2.3), (-0.1, 1.95), (-0.35, 1.7), (0.15, 1.35), (-0.05, 1.12)]
    for i in range(len(zz) - 1):
        bar(f"Snap{i}", (zz[i][0], fy + 0.03, zz[i][1]), (zz[i + 1][0], fy + 0.03, zz[i + 1][1]), 0.14, 0.16, "#FFF6C8", glow=5.0)
    for sx in (-1, 1):
        a = math.pi / 2 + sx * math.pi / 4
        c = Vector((math.cos(a) * fy, math.sin(a) * fy, 1.9))
        t = Vector((-math.sin(a), math.cos(a), 0))
        bar(f"SnapSide{sx}", c + t * 0.3 + Vector((0, 0, 0.3)), c - t * 0.2 - Vector((0, 0, 0.25)), 0.12, 0.14, "#FFF6C8", glow=5.0)
    FACE("GemShine", (0.22, 0.06, 0.7), (-0.75, fy + 0.03, 1.4), "#FFFFFF", emission=2.5)
    FACE("GemShineTop", (0.6, 0.5, 0.06), (-0.25, 0.1, 3.27), "#FFF6E0", emission=1.5, rot=(0, 0, 0.6))
    sparkles("GemSpark", [(-1.6, 0.8, 3.3), (1.7, 0.4, 2.6), (1.0, 1.0, 3.8), (-1.3, 0.6, 0.6)], "#FFFFFF", size=0.24)
    return B


ASSETS = {
    "pebble_pup": ("PebblePup", pebble_pup, "pet", "pet_pebble_pup.png"),
    "avalanche_pug": ("AvalanchePug", avalanche_pug, "pet", "pet_avalanche_pug.png"),
    "skelly_cat": ("SkellyCat", skelly_cat, "pet", "pet_skelly_cat.png"),
    "egg_trailhead": ("TrailheadEgg", egg_trailhead, "egg", "egg_trailhead.png"),
    "icon_cash": ("IconCash", icon_cash, "ui_icon_model", "icon_cash.png"),
    "icon_gem": ("IconGem", icon_gem, "ui_icon_model", "icon_gem.png"),
}


# =============================================================================================
# Rendering (bible §10 review renders + transparent UI hero icons)
# =============================================================================================
SUN, FILL = 3.5, 1.0  # close-up pet review: bible §10 sun 5.0 clips white/cream pets in Standard view


def _bounds(objs):
    bpy.context.view_layer.update()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def _scene(samples, res, transparent):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = transparent
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    world = sc.world or bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.33, 0.64, 1.0, 1) if not transparent else (0.75, 0.85, 1.0, 1)
    bg.inputs[1].default_value = 0.8 if not transparent else 0.55
    return sc


def _clear_rig():
    for o in list(bpy.data.objects):
        if o.get("vault_rig"):
            bpy.data.objects.remove(o, do_unlink=True)


def _light(name, kind, energy, loc_or_dir, target=None, color=(1, 1, 1), size=1.0, angle=0.12):
    ld = bpy.data.lights.new(name, kind)
    ld.energy, ld.color = energy, color
    if kind == "SUN":
        ld.angle = angle
    else:
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    o["vault_rig"] = True
    bpy.context.scene.collection.objects.link(o)
    if kind == "SUN":
        o.rotation_euler = (-Vector(loc_or_dir)).to_track_quat("-Z", "Y").to_euler()
    else:
        o.location = loc_or_dir
        o.rotation_euler = (Vector(target) - Vector(loc_or_dir)).to_track_quat("-Z", "Y").to_euler()
    return o


def _camera(loc, target, lens):
    cam = bpy.data.objects.get("ReviewCam")
    if not cam:
        cam = bpy.data.objects.new("ReviewCam", bpy.data.cameras.new("ReviewCam"))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.clip_end = 500
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def _floor():
    if "PreviewFloor" not in bpy.data.objects:
        vb.solid("PreviewFloor", (80, 80, 1.0), (0, 0, -1.0), "#6CC24A", bevel=0.0)


def _azim_dir(az_deg, el_deg):
    a, e = math.radians(az_deg), math.radians(el_deg)
    return Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))  # az 0 = front (+y)


def render_views(name, objs, samples, views=(("front", 0), ("side", 90), ("back", 180))):
    os.makedirs(PREV, exist_ok=True)
    lo, hi = _bounds(objs)
    ctr = (lo + hi) / 2
    size = max(hi.z - lo.z, (hi.x - lo.x) * 0.62, (hi.y - lo.y) * 0.62)
    out = []
    _scene(samples, (1280, 720), False)
    _floor()
    for label, az in views:
        _clear_rig()
        d = _azim_dir(az + 30, 50)
        _light("Sun", "SUN", SUN, d, color=(1.0, 0.96, 0.9))
        _light("Fill", "SUN", FILL, _azim_dir(az - 120, 25), color=(0.85, 0.92, 1.0), angle=0.4)
        dist = size * 3.3
        cam_dir = _azim_dir(az, 12)
        tgt = Vector((ctr.x, ctr.y, lo.z + (hi.z - lo.z) * 0.47))
        _camera(tuple(tgt + cam_dir * dist), tuple(tgt), 50)
        p = os.path.join(PREV, f"{name}_{label}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        out.append(p)
    return out


def render_icon(filename, objs, samples, az=35, el=16, lens=70, fill_frac=0.86):
    os.makedirs(UI, exist_ok=True)
    floor = bpy.data.objects.get("PreviewFloor")
    if floor:
        bpy.data.objects.remove(floor, do_unlink=True)
    _scene(samples, (1024, 1024), True)
    _clear_rig()
    lo, hi = _bounds(objs)
    ctr = (lo + hi) / 2
    rad = (hi - lo).length / 2
    half = math.atan(18 / lens)
    dist = rad / math.sin(half) * fill_frac
    d = _azim_dir(az, el)
    cam = tuple(ctr + d * dist)
    _camera(cam, tuple(ctr), lens)
    k = dist * dist
    _light("Key", "AREA", 9.0 * k, tuple(ctr + _azim_dir(az - 55, 40) * dist * 0.8), tuple(ctr), (1.0, 0.95, 0.88), size=rad * 1.2)
    _light("Rim", "AREA", 14.0 * k, tuple(ctr + _azim_dir(az + 160, 35) * dist * 0.8), tuple(ctr), (0.75, 0.88, 1.0), size=rad)
    _light("Fill", "AREA", 3.5 * k, tuple(ctr + _azim_dir(az + 60, 5) * dist * 0.8), tuple(ctr), (1.0, 1.0, 1.0), size=rad * 1.5)
    p = os.path.join(UI, filename)
    bpy.context.scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    return p


# =============================================================================================
# Export: <=3 meshes (Body / Glass / Neon) + separate _FX mesh
# =============================================================================================
def _is_neon(o):
    return any(m and m.get("roblox_neon") for m in o.data.materials)


def export_asset(b: Builder, out_dir, kind):
    parts = list(b.P)
    n_parts = len(b.P) + len(b.FX)
    groups = {"Body": [], "Glass": [], "Neon": []}
    for o in parts:
        if o.name in b.glass:
            groups["Glass"].append(o)
        elif _is_neon(o) and all(m.get("roblox_neon") for m in o.data.materials):
            groups["Neon"].append(o)
        else:
            groups["Body"].append(o)
    meshes, tris = [], {}
    for g, objs in groups.items():
        if not objs:
            continue
        tris[g] = vb.poly_report(objs)["tris"]
        meshes.append(vb.join(f"{b.name}_{g}", objs))
    fx = None
    if b.FX:
        tris["FX"] = vb.poly_report(b.FX)["tris"]
        fx = vb.join(f"{b.name}_FX", b.FX)
    if b.name == "TrailheadEgg":  # recolorable accent material for the egg family
        for m in bpy.data.materials:
            if m.get("roblox_color", "").upper() == EGG_ACCENT:
                m.name = "EggAccent" + ("_Studs" if m.get("vault_studs") else "")
    for m in meshes + ([fx] if fx else []):
        m["vault_asset"] = b.name
    os.makedirs(out_dir, exist_ok=True)
    fbx = vb.export_fbx(os.path.join(out_dir, f"{b.name}.fbx"), meshes)
    entries = [{"name": b.name, "file": os.path.relpath(fbx, GAME), "tris": sum(v for k, v in tris.items() if k != "FX"),
                "tris_per_mesh": {k: v for k, v in tris.items() if k != "FX"}, "parts": n_parts, "kind": kind,
                "meshes": [m.name for m in meshes], "status": "PENDING owner approval"}]
    if fx:
        fxp = vb.export_fbx(os.path.join(out_dir, f"{b.name}_FX.fbx"), [fx])
        entries.append({"name": f"{b.name}_FX", "file": os.path.relpath(fxp, GAME), "tris": tris["FX"],
                        "parts": len(b.FX), "kind": f"{kind}_fx", "meshes": [fx.name],
                        "note": "orbiters + aura ring; spin/bob in Studio", "status": "PENDING owner approval"})
    vb.export_glb(os.path.join(out_dir, f"{b.name}.glb"), meshes + ([fx] if fx else []))
    return entries


def _update_manifest(entries):
    data = []
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            data = json.load(f)
    names = {e["name"] for e in entries}
    data = [e for e in data if e["name"] not in names] + entries
    data.sort(key=lambda e: e["name"])
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _move(objs, dx):
    for o in objs:
        if o.parent is None:
            o.location.x += dx


def lineup(samples):
    vb.reset_scene()
    allobjs = []
    for key, dx in (("pebble_pup", -12.5), ("avalanche_pug", -4.2), ("skelly_cat", 4.2), ("egg_trailhead", 12.0)):
        b = ASSETS[key][1]()
        _move(b.P + b.FX, dx)
        vb.restud(b.P + b.FX)
        allobjs += b.P + b.FX
    _scene(samples, (1280, 720), False)
    _floor()
    _clear_rig()
    _light("Sun", "SUN", SUN, _azim_dir(30, 50), color=(1.0, 0.96, 0.9))
    _light("Fill", "SUN", FILL, _azim_dir(-120, 25), color=(0.85, 0.92, 1.0), angle=0.4)
    _camera((0, 30, 9.5), (0, 0, 3.0), 38)
    p = os.path.join(PREV, "pets_lineup.png")
    os.makedirs(PREV, exist_ok=True)
    bpy.context.scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    return p


def main(out_dir, which, samples=32, render=True):
    results = []
    for key in which:
        if key == "lineup":
            if render:
                results.append(lineup(samples))
            continue
        name, fn, kind, icon = ASSETS[key]
        vb.reset_scene()
        b = fn()
        if render:
            views = render_views(name, b.P + b.FX, samples) if kind != "ui_icon_model" else \
                render_views(name, b.P + b.FX, samples, views=(("front", 0), ("side", 90)))
            ic = render_icon(icon, b.P + b.FX, max(samples, 48), az=28 if kind == "ui_icon_model" else 35)
            results += views + [ic]
        entries = export_asset(b, out_dir, kind)
        _update_manifest(entries)
        results.append(entries)
        print(json.dumps(entries))
    return results


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    samples, render, pos = 32, True, []
    i = 0
    while i < len(argv):
        if argv[i] == "--samples":
            samples = int(argv[i + 1])
            i += 2
            continue
        if argv[i] == "--no-render":
            render = False
        else:
            pos.append(argv[i])
        i += 1
    out = pos[0] if pos else os.path.join(GAME, "assets", "export", "pets")
    which = pos[1:] or list(ASSETS) + ["lineup"]
    main(out, which, samples, render)
