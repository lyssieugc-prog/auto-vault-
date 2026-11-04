"""
Ragdoll Off a Mountain — LAUNCH CANNONS (spec §3.3). Five ORIGINAL cannons, each bigger/cooler.

    python3 games/ragdoll-off-a-mountain/blender/cannons.py [export_dir] [--samples N] [--only Name]
                                                            [--no-render] [--no-icons] [--no-lineup]

Conventions: 1 unit = 1 stud, Z up, FRONT = +Y, pivot bottom-centre. Base fits the 8-stud
`CannonMountN` ring. Barrel axis tilted 25 deg up toward +Y, inner opening >= 4 studs.
Exports per cannon: <Name>_Body + <Name>_Neon meshes under a root empty with attachment empties
`Pivot`, `Seat`, `Muzzle`. Also writes previews (front/side/back), a lineup hero shot and
transparent 1024x1024 shop-card icons (assets/ui/cannon_<n>.png).

This file also holds the shared modeling/render helpers used by hub_props.py.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GAME = os.path.abspath(os.path.join(HERE, ".."))
sys.path[:0] = [os.path.join(ROOT, "blender", "lib")]

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import vault_blocky as vb  # noqa: E402
import vault_kit as kit  # noqa: E402


def _ensure_real_stud_textures():
    """blender/textures/*.png are Git-LFS pointers in this checkout (not real PNGs), which silently
    disables the stud bump. Regenerate the identical library tile into a temp cache instead
    (shared files are left untouched)."""
    hpath, _ = vb.stud_texture_paths()
    try:
        with open(hpath, "rb") as f:
            ok = f.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        ok = False
    if not ok:
        import tempfile
        vb._TEX_DIR = os.path.join(tempfile.gettempdir(), "vault_stud_tex")
        hp, _ = vb.stud_texture_paths()
        vb.ensure_stud_textures(force=not os.path.exists(hp))


_ensure_real_stud_textures()

EXPORT_DIR = os.path.join(GAME, "assets", "export", "props")
PREVIEW_DIR = os.path.join(GAME, "assets", "previews", "props")
UI_DIR = os.path.join(GAME, "assets", "ui")

TILT = 25.0
S, R, C, B = vb.solid, vb.rounded, vb.cyl, vb.ball
SH = kit.shades

# Game palette
STONE, STONE_D = "#8E96A3", "#6E7683"
BONE = "#FFF1CF"
SNAP = "#FF8A1F"
GOLD = "#FFD93B"
INK = "#1A1A1A"
NAVY = "#1E1B33"


# ================================================================================================
# Geometry helpers (techniques, not assets)
# ================================================================================================

def xf(objs, M):
    """Apply a world transform to objects built in a local frame (unparented)."""
    for o in objs:
        o.matrix_basis = M @ o.matrix_basis
    return objs


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def Rx(deg):
    return Matrix.Rotation(math.radians(deg), 4, "X")


def Ry(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Y")


def Rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Z")


def aim(direction):
    """Rotation matrix taking local +Z onto `direction`."""
    d = Vector(direction).normalized()
    return Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()


def barrel_matrix(pivot, tilt=TILT):
    """Barrel-local frame: barrel axis = local +Z (back -> front), 'up' = local -Y, right = +X.
    Maps to world: axis -> +Y tilted `tilt` deg upward, about `pivot`."""
    return T(*pivot) @ Rx(tilt - 90.0)


def polar(a_deg, r):
    """Point on a barrel cross-section; a=90 is the top of the barrel, a=0 is the right side."""
    a = math.radians(a_deg)
    return r * math.cos(a), -r * math.sin(a)


def radial(a_deg, r, z, spin=0.0):
    """Matrix placing a piece (built with its outward normal = local +Z) on a barrel surface."""
    return Rz(-a_deg) @ T(r, 0, z) @ Ry(90) @ Rz(spin)


def tube(name, r1, r2, h, t, loc, color, sides=24, a0=0.0, a1=360.0, studs="all", rot=None):
    """Hollow tube / ring / flared shell along +Z (outer r1 at z=0 -> r2 at z=h, wall t).
    Partial arcs (a0..a1 degrees) get end caps."""
    full = abs((a1 - a0) - 360.0) < 1e-6
    bm = bmesh.new()
    n = sides if full else max(2, int(round(sides * (a1 - a0) / 360.0)))
    cnt = n if full else n + 1
    ob, ot, ib, it = [], [], [], []
    for i in range(cnt):
        a = math.radians(a0 + (a1 - a0) * i / n)
        c, s = math.cos(a), math.sin(a)
        ob.append(bm.verts.new((c * r1, s * r1, 0)))
        ot.append(bm.verts.new((c * r2, s * r2, h)))
        ib.append(bm.verts.new((c * (r1 - t), s * (r1 - t), 0)))
        it.append(bm.verts.new((c * (r2 - t), s * (r2 - t), h)))
    for i in range(n):
        j = (i + 1) % cnt
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ib[i], ib[j], ob[j], ob[i]))
    if not full:
        bm.faces.new((ob[0], ot[0], it[0], ib[0]))
        bm.faces.new((ob[-1], ib[-1], it[-1], ot[-1]))
    obj = vb._new_mesh_object(name, bm)
    obj.location = loc
    return vb._finish(obj, color, 0.0, studs, rot)


def prism(name, pts, depth, color, plane="xz", loc=(0, 0, 0), studs="all", rot=None):
    """Extruded 2D outline (signs, icons, fins, brackets, gear teeth).
    plane 'xz': outline in X/Z, extruded along Y (faces +-Y) centred on loc.
    plane 'yz': outline in Y/Z, extruded along X.  plane 'xy': outline in X/Y, extruded along Z."""
    bm = bmesh.new()
    d = depth / 2.0

    def v3(u, v, w):
        if plane == "xz":
            return (u, w, v)
        if plane == "yz":
            return (w, u, v)
        return (u, v, w)

    # ensure CCW
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if area < 0:
        pts = list(reversed(pts))
    lo = [bm.verts.new(v3(u, v, -d)) for u, v in pts]
    hi = [bm.verts.new(v3(u, v, d)) for u, v in pts]
    n = len(pts)
    flip = plane == "xz"  # xz maps (u,v,w)->(x,w,v): handedness flips
    f1 = bm.faces.new(list(reversed(lo)) if not flip else lo)
    f2 = bm.faces.new(hi if not flip else list(reversed(hi)))
    for i in range(n):
        j = (i + 1) % n
        q = (lo[i], lo[j], hi[j], hi[i])
        bm.faces.new(q if not flip else tuple(reversed(q)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    del f1, f2
    obj = vb._new_mesh_object(name, bm)
    obj.location = loc
    return vb._finish(obj, color, 0.0, studs, rot)


def beam(name, a, b, w, d, color, kind="solid", sides=10, bevel=0.04, studs="all"):
    """Chunky beam/strut between two points (cross-section w x d). kind: solid|cyl|rounded."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    if kind == "cyl":
        o = C(name, w, d, L, (0, 0, 0), color, sides=sides, studs=studs)
    elif kind == "rounded":
        o = R(name, (w, d, L), (0, 0, 0), color, radius=min(w, d) * 0.3, studs=studs)
    else:
        o = S(name, (w, d, L), (0, 0, 0), color, bevel=bevel, studs=studs)
    xf([o], T(*a) @ aim(b - a))
    return o


def neon(obj, strength=4.0, hex_color=None):
    """Swap a piece to a Neon (emissive, unstudded) material. Separate cache key from plastic."""
    col = hex_color or obj.data.materials[0].get("roblox_color", "#FFFFFF")
    m = vb.palette_material("Neon" + col, col, emission=strength)
    obj.data.materials.clear()
    obj.data.materials.append(m)
    if "vault_stud_mode" in obj:
        del obj["vault_stud_mode"]
    return obj


def N(obj, strength=4.0):
    return neon(obj, strength)


def bolts(prefix, pts, color="#D9DEE6", r=0.16):
    return [B(f"{prefix}{i}", (r, r, r), p, color, segments=6, rings=4, studs="none") for i, p in enumerate(pts)]


def ring_bolts(prefix, r, z, n, a_off=0.0, color="#D9DEE6", size=0.16):
    pts = []
    for i in range(n):
        x, y = polar(a_off + 360.0 * i / n, r)
        pts.append((x, y, z))
    return bolts(prefix, pts, color, size)


def gear(prefix, r, thick, teeth, color, hub_color, tooth=0.5):
    """Gear built facing +Z (disc + teeth + hub + spokes holes). Place with xf()."""
    P = [C(f"{prefix}Disc", r, r, thick, (0, 0, 0), color, sides=max(12, teeth))]
    for i in range(teeth):
        a = 360.0 * i / teeth
        t = S(f"{prefix}Tooth{i}", (tooth, tooth * 0.9, thick * 0.9), (0, 0, 0), color, bevel=0.03)
        xf([t], Rz(a) @ T(r + tooth * 0.35, 0, thick * 0.05) @ Rz(90))
        P.append(t)
    P.append(C(f"{prefix}Hub", r * 0.38, r * 0.38, thick + 0.3, (0, 0, 0), hub_color, sides=10))
    P.append(C(f"{prefix}Cap", r * 0.18, r * 0.18, thick + 0.5, (0, 0, 0), "#D9DEE6", sides=8))
    for i in range(4):  # lightening holes read as dark insets
        a = math.radians(45 + 90 * i)
        P.append(C(f"{prefix}Hole{i}", r * 0.16, r * 0.16, thick + 0.06, (math.cos(a) * r * 0.62, math.sin(a) * r * 0.62, -0.03),
                   SH(color)["deep"], sides=8))
    return P


def star_pts(r_out, r_in, n=5, rot=90.0):
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + 180.0 * i / n)
        r = r_out if i % 2 == 0 else r_in
        pts.append((math.cos(a) * r, math.sin(a) * r))
    return pts


def circle_pts(r, n=16, cx=0.0, cy=0.0):
    return [(cx + math.cos(2 * math.pi * i / n) * r, cy + math.sin(2 * math.pi * i / n) * r) for i in range(n)]


def bone_icon(prefix, scale, color, depth=0.3, plane="xz"):
    """Flat cartoon bone (shaft + 4 knobs) in the given plane, centred at the origin, along u."""
    s = scale
    P = [prism(f"{prefix}Shaft", [(-1.1 * s, -0.28 * s), (1.1 * s, -0.28 * s), (1.1 * s, 0.28 * s), (-1.1 * s, 0.28 * s)],
               depth, color, plane)]
    for i, (u, v) in enumerate(((-1.15, 0.33), (-1.15, -0.33), (1.15, 0.33), (1.15, -0.33))):
        P.append(prism(f"{prefix}Knob{i}", circle_pts(0.42 * s, 12, u * s, v * s), depth, color, plane))
    return P


def cartoon_bone(prefix, a, b, r, color, knob=None, kind="rounded"):
    """3D cartoon bone between points a and b: chunky shaft + 2 knob balls at each end."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    side = d.cross(Vector((0, 1, 0)))
    if side.length < 0.2:
        side = d.cross(Vector((1, 0, 0)))
    side.normalize()
    k = knob or r * 0.85
    shaft = beam(f"{prefix}Shaft", a, b, 2 * r, 2 * r, color, kind=kind)
    P = [shaft]
    sh = SH(color)
    for e, p in (("A", a), ("B", b)):
        for j, sgn in enumerate((-1, 1)):
            P.append(B(f"{prefix}Knob{e}{j}", (k, k, k), p + side * sgn * k * 0.75 - d * (0 if e == "A" else 0) , sh["light"],
                       segments=10, rings=6))
    return P


def all_bounds(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    bpy.context.view_layer.update()
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


# ================================================================================================
# Finish / export
# ================================================================================================

def _mat_flags(o):
    m = o.data.materials[0] if o.data.materials else None
    if m is None:
        return "body"
    if o.name.startswith("Screen"):
        return "screen"
    if m.get("vault_accent"):
        return "accent"
    if m.get("roblox_neon"):
        return "neon"
    if m.get("roblox_glass"):
        return "glass"
    return "body"


def finish_model(name, objs, out_dir, kind, attachments=None):
    """Restud, join into <=3 meshes (body / neon / screen|accent|glass), parent to a root empty
    with attachment empties, export FBX + GLB. Returns manifest entry + mesh list."""
    objs = [o for o in objs if o is not None]
    vb.restud(objs)
    parts = len(objs)
    groups = {}
    for o in objs:
        groups.setdefault(_mat_flags(o), []).append(o)
    names = {"body": f"{name}_Body", "neon": f"{name}_Neon", "screen": "Screen", "accent": "Accent", "glass": f"{name}_Glass"}
    meshes = []
    for key in ("body", "accent", "screen", "glass", "neon"):
        if key in groups:
            m = vb.join(names[key], groups[key])
            m.data.name = names[key]
            meshes.append(m)
    assert len(meshes) <= 3, f"{name}: {len(meshes)} meshes"
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for m in meshes:
        m.parent = root
    for an, M in (attachments or {}).items():
        e = bpy.data.objects.new(an, None)
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 1.0
        bpy.context.scene.collection.objects.link(e)
        e.matrix_basis = M
        e.parent = root
    bpy.context.view_layer.update()
    per = {}
    tris = 0
    for m in meshes:
        t = vb.poly_report([m])["tris"]
        per[m.name] = t
        tris += t
        assert t <= 15000, f"{m.name} has {t} tris"
    os.makedirs(out_dir, exist_ok=True)
    fbx = vb.export_fbx(os.path.join(out_dir, f"{name}.fbx"), [root])
    vb.export_glb(os.path.join(out_dir, f"{name}.glb"), [root])
    lo, hi = all_bounds(meshes)
    entry = {"name": name, "file": os.path.relpath(fbx, GAME).replace(os.sep, "/"), "tris": tris, "meshes": per,
             "parts": parts, "kind": kind, "size": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)],
             "attachments": sorted((attachments or {}).keys())}
    print(f"[export] {name}: {tris} tris {per} parts={parts} size={entry['size']}")
    return entry, meshes


# ================================================================================================
# Rendering (bible §10)
# ================================================================================================

def setup_render(samples=28, res=(1280, 720), transparent=False, icon=False):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.33, 0.64, 1.0, 1)
    bg.inputs[1].default_value = 0.5 if not icon else 0.35
    for o in [o for o in scene.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    if icon:
        lights = (("Key", 4.0, (0.93, 0.0, 2.76), (1.0, 0.97, 0.92), 0.15),
                  ("Rim", 5.0, (1.16, 0.0, -0.71), (0.75, 0.9, 1.0), 0.1),
                  ("Fill", 1.5, (1.27, 0.0, 1.79), (0.95, 0.9, 1.0), 0.4))
    else:
        lights = (("Sun", 5.0, (0.75, 0.0, 2.6), (1.0, 0.96, 0.9), 0.12),
                  ("Fill", 1.2, (1.0, 0.0, -0.6), (0.75, 0.85, 1.0), 0.3))
    for name, energy, rot, col, ang in lights:
        lo = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        lo.data.energy, lo.data.color, lo.data.angle = energy, col, ang
        lo.rotation_euler = rot
        scene.collection.objects.link(lo)
    return scene


def camera():
    scene = bpy.context.scene
    cam = bpy.data.objects.get("ReviewCam")
    if not cam:
        cam = bpy.data.objects.new("ReviewCam", bpy.data.cameras.new("ReviewCam"))
        scene.collection.objects.link(cam)
    cam.data.clip_end = 3000
    scene.camera = cam
    return cam


def shoot(path, loc, target, lens=50):
    scene = bpy.context.scene
    cam = camera()
    cam.location = loc
    cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("[render]", path)
    return path


def fit_distance(lo, hi, lens, aspect, margin=1.25):
    size = hi - lo
    rad = max(size.x, size.y, size.z) * 0.5
    vfov = 2 * math.atan(18.0 / lens / aspect) if aspect >= 1 else 2 * math.atan(18.0 / lens)
    return rad / math.tan(vfov / 2) * margin


def review_ground(size=70, z=0.0, color="#4FC33A"):
    """Studded grass ground for review shots (not exported)."""
    g = SH(color)
    P = [S("RevGround", (size, size, 0.6), (0, 0, z - 0.6), g["base"], bevel=0.0)]
    return P


def render_views(name, meshes, prev_dir, samples, extra=None, lens=50):
    """FRONT (+Y), SIDE (+X), BACK (-Y) review shots, framed on the model's bounds."""
    lo, hi = all_bounds(meshes)
    c = (lo + hi) / 2
    d = fit_distance(lo, hi, lens, 16 / 9, 1.35)
    out = []
    views = {"FRONT": (0.28, 1.0), "SIDE": (1.0, -0.12), "BACK": (-0.28, -1.0)}
    for v, (dx, dy) in views.items():
        dirv = Vector((dx, dy, 0)).normalized()
        loc = c + dirv * d + Vector((0, 0, d * 0.28))
        out.append(shoot(os.path.join(prev_dir, f"{name}_{v}.png"), loc, c, lens))
    return out


# ================================================================================================
# Cannons
# ================================================================================================

def mount_ring(prefix="Mount", r=4.0):
    """The game's CannonMount ring (context only, not exported): steel ring + hazard dashes."""
    P = [tube(f"{prefix}Ring", r + 0.5, r + 0.5, 0.45, 1.3, (0, 0, -0.45), "#5B6B82", sides=32)]
    for i in range(16):
        col = "#FFC21A" if i % 2 == 0 else INK
        P.append(tube(f"{prefix}Haz{i}", r + 0.65, r + 0.65, 0.12, 0.45, (0, 0, -0.45), col, sides=32,
                      a0=i * 22.5, a1=(i + 1) * 22.5))
    return P


def party_popper():
    """Tier 1 — giant cardboard party-popper tube on a gift-box stand."""
    name = "Cannon1_PartyPopper"
    KR = SH("#D98B3A")
    PINK, TEAL, YEL, PUR = SH("#FF5FA2"), SH("#22C3A6"), SH(GOLD), SH("#B678EA")
    P = []
    # --- base: studded round plate + wrapped gift box + bow + spilled confetti
    P += [C("PPBase", 3.95, 3.95, 0.45, (0, 0, 0), PUR["dark"], sides=28),
          C("PPBaseTop", 3.55, 3.55, 0.3, (0, 0, 0.45), PUR["base"], sides=28),
          R("PPGift", (4.6, 4.6, 1.7), (0, 0, 0.75), PINK["base"], radius=0.12),
          S("PPRibbonX", (4.72, 0.9, 1.74), (0, 0, 0.73), YEL["base"]),
          S("PPRibbonY", (0.9, 4.72, 1.74), (0, 0, 0.73), YEL["base"]),
          R("PPLid", (5.1, 5.1, 0.7), (0, 0, 2.45), PINK["light"], radius=0.12),
          S("PPLidRibX", (5.22, 0.9, 0.74), (0, 0, 2.43), YEL["light"]),
          S("PPLidRibY", (0.9, 5.22, 0.74), (0, 0, 2.43), YEL["light"])]
    # bow on the front face of the gift
    for sx in (-1, 1):
        P.append(R(f"PPBowLoop{sx}", (1.3, 0.5, 0.9), (sx * 0.75, 2.62, 1.25), YEL["base"], radius=0.2, rot=(0, math.radians(sx * 25), 0)))
        P.append(S(f"PPBowTail{sx}", (0.45, 0.3, 1.0), (sx * 0.45, 2.55, 0.45), YEL["dark"], rot=(0, math.radians(-sx * 18), 0)))
    P.append(R("PPBowKnot", (0.6, 0.6, 0.6), (0, 2.6, 1.4), YEL["dark"], radius=0.18))
    rnd = random.Random(11)
    for i in range(14):  # spilled confetti on the base rim (tells the story: it already popped once)
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(2.95, 3.4)
        col = (PINK["base"], TEAL["base"], YEL["base"], PUR["light"])[i % 4]
        P.append(S(f"PPSpill{i}", (0.42, 0.3, 0.1), (math.cos(a) * r, math.sin(a) * r, 0.75), col, bevel=0.02,
                   rot=(0, 0, rnd.uniform(0, 3.1))))
    # --- cradle: ribbon-wrapped uprights + trunnion knobs
    pivot = (0, 0.0, 5.5)
    r_at = lambda z: 1.45 + (z + 2.0) * (2.6 - 1.45) / 7.0  # flare from back (z=-2) to mouth (z=5)
    for sx in (-1, 1):
        x = sx * (r_at(0) + 0.45)
        P += [S(f"PPCradle{sx}", (0.7, 1.6, 2.6), (x, 0, 3.15), TEAL["base"]),
              S(f"PPCradleBand{sx}", (0.78, 0.5, 2.62), (x, 0, 3.14), TEAL["light"]),
              C(f"PPTrunnion{sx}", 0.55, 0.55, 0.7, (x - sx * 0.35, 0, pivot[2]), TEAL["dark"], sides=12,
                rot=(0, math.radians(90 * sx), 0)),
              B(f"PPTrunnionCap{sx}", (0.42, 0.42, 0.42), (x + sx * 0.4, 0, pivot[2]), YEL["base"], segments=10, rings=6)]
        P.append(N(B(f"PPBulb{sx}", (0.3, 0.3, 0.3), (x, 0.55, 5.85), "#FFE45C", segments=8, rings=5, studs="none"), 5))
    # --- barrel (barrel-local frame: +Z axis, up = -Y)
    BP = []
    segs = [(-2.0, -0.6, KR["dark"]), (-0.6, 1.0, KR["base"]), (1.0, 2.6, KR["light"]), (2.6, 4.2, KR["base"])]
    for i, (z0, z1, col) in enumerate(segs):
        BP.append(tube(f"PPTube{i}", r_at(z0), r_at(z1), z1 - z0, 0.32, (0, 0, z0), col, sides=28))
    stripe_cols = (PINK["base"], TEAL["base"], YEL["base"], PUR["base"], PINK["light"])
    for i, z in enumerate((-1.55, -0.6, 1.0, 2.6, 3.7)):  # raised confetti stripe bands
        BP.append(tube(f"PPStripe{i}", r_at(z) + 0.09, r_at(z + 0.45) + 0.09, 0.45, 0.2, (0, 0, z - 0.22),
                       stripe_cols[i], sides=28))
    BP.append(tube("PPMouthRim", r_at(4.2) + 0.25, r_at(4.9) + 0.3, 0.7, 0.7, (0, 0, 4.2), YEL["base"], sides=28))
    BP.append(tube("PPMouthLip", r_at(4.9) + 0.35, r_at(4.9) + 0.35, 0.22, 0.45, (0, 0, 4.9), YEL["light"], sides=28))
    BP.append(C("PPBackCap", r_at(-2.0) + 0.12, r_at(-2.0) + 0.12, 0.4, (0, 0, -2.35), KR["deep"], sides=28))
    BP.append(C("PPBackDisc", 0.9, 0.9, 0.25, (0, 0, -2.55), PINK["dark"], sides=16))
    BP.append(C("PPThroat", r_at(1.2) - 0.3, r_at(1.2) - 0.3, 0.15, (0, 0, 1.2), "#3A2A55", sides=24, studs="none"))
    BP.append(N(tube("PPThroatGlow", r_at(1.4) - 0.3, r_at(1.4) - 0.3, 0.2, 0.18, (0, 0, 1.36), "#FF5FD0", sides=24), 4))
    # confetti chips stuck on the tube (varied size/spin; skip the stripe bands)
    for i in range(22):
        z = rnd.uniform(-1.3, 3.4)
        if any(abs(z - zz) < 0.35 for zz in (-1.55, -0.6, 1.0, 2.6)):
            z += 0.4
        a = rnd.uniform(0, 360)
        s = rnd.uniform(0.32, 0.5)
        chip = S(f"PPChip{i}", (s, s * rnd.uniform(0.6, 1.0), 0.09), (0, 0, 0),
                 stripe_cols[rnd.randrange(5)], bevel=0.02)
        BP.append(xf([chip], radial(a, r_at(z) - 0.02, z, rnd.uniform(0, 90)))[0])
    # star labels on the sides
    for sx, a in ((1, 0), (-1, 180)):
        st = prism(f"PPStar{sx}", star_pts(0.9, 0.42), 0.16, YEL["base"], plane="xy")
        BP.append(xf([st], radial(a, r_at(0.2) + 0.02, 0.2, 90))[0])
    # streamers spilling out of the mouth and draping down over the rim (gravity = world down)
    down = Vector((0, math.sin(math.radians(90 - TILT)), -math.cos(math.radians(90 - TILT))))
    for k, (a0, col) in enumerate(((60, PINK["base"]), (95, TEAL["base"]), (128, YEL["base"]), (25, PUR["light"]),
                                   (160, PINK["light"]), (205, TEAL["light"]), (335, YEL["light"]))):
        x0, y0 = polar(a0, r_at(4.9) - 0.15)
        p = Vector((x0, y0, 4.7))
        outward = Vector((x0, y0, 0)).normalized()
        dirv = (outward * 0.6 + Vector((0, 0, 1.0))).normalized()
        nseg = 5 if 30 < a0 < 150 else 3
        for j in range(nseg):
            q = p + dirv * (0.75 if j else 0.9)
            BP.append(beam(f"PPStreamer{k}_{j}", p, q, 0.5, 0.14, col))
            p = q
            dirv = (dirv * 0.45 + down * 0.75 + outward * 0.25 + Vector((0, 0, 0.12))).normalized()
        BP.append(xf([S(f"PPStreamerEnd{k}", (0.5, 0.14, 0.32), (0, 0, 0), col)], T(*p) @ aim(dirv) @ Rz(25))[0])
    # pull-string out of the back cap + ring tab
    BP.append(C("PPStringBoss", 0.38, 0.38, 0.35, (0, -0.6, -2.85), KR["deep"], sides=10))
    BP.append(beam("PPString0", (0, -0.6, -2.7), (0, 0.6, -3.5), 0.3, 0.3, "#FFFFFF", kind="cyl", sides=8))
    BP.append(beam("PPString1", (0, 0.6, -3.5), (0, 1.9, -3.35), 0.3, 0.3, "#FFFFFF", kind="cyl", sides=8))
    ringtab = tube("PPPullRing", 0.75, 0.75, 0.3, 0.32, (0, 0, -0.15), "#E13A2A", sides=16)
    xf([ringtab], T(0, 2.6, -3.3) @ Ry(90))
    BP.append(ringtab)
    BM = barrel_matrix(pivot)
    xf(BP, BM)
    P += BP
    att = {"Pivot": T(*pivot) @ Rx(TILT), "Seat": BM @ T(0, 0, 1.6) @ Rx(90), "Muzzle": BM @ T(0, 0, 5.2) @ Rx(90)}
    return name, P, att


def barrel_blaster():
    """Tier 2 — wooden stave barrel with iron hoops on a 4-wheel carriage + lit fuse."""
    name = "Cannon2_BarrelBlaster"
    OAK, WOOD = SH("#B5733A"), SH("#8A5530")
    IRON = SH("#4A5260")
    ROPE = SH("#D9B77A")
    P = []
    # --- carriage
    P += [C("BBTurn", 3.95, 3.95, 0.4, (0, 0, 0), WOOD["deep"], sides=28),
          tube("BBTurnBand", 4.02, 4.02, 0.2, 0.25, (0, 0, 0.1), IRON["base"], sides=28)]
    for i, x in enumerate((-2.6, -1.3, 0.0, 1.3, 2.6)):  # bed planks
        P.append(S(f"BBPlank{i}", (1.26, 6.6, 0.55), (x, 0, 2.55), (OAK["base"], OAK["dark"], OAK["light"])[i % 3]))
    for sy in (-1, 1):
        P.append(S(f"BBBedBeam{sy}", (6.9, 0.8, 0.6), (0, sy * 2.3, 1.95), WOOD["base"]))
        P.append(C(f"BBAxle{sy}", 0.32, 0.32, 8.0, (-4.0, sy * 2.3, 1.9), IRON["dark"], sides=10, rot=(0, math.radians(90), 0)))
        for sx in (-1, 1):  # spoked wheels
            wx = sx * 3.75
            P.append(xf([tube(f"BBWheelRim{sx}{sy}", 1.5, 1.5, 0.6, 0.32, (0, 0, -0.3), IRON["base"], sides=20)],
                        T(wx, sy * 2.3, 1.9) @ Ry(90))[0])
            P.append(xf([tube(f"BBWheelWood{sx}{sy}", 1.18, 1.18, 0.5, 0.25, (0, 0, -0.25), WOOD["light"], sides=20)],
                        T(wx, sy * 2.3, 1.9) @ Ry(90))[0])
            for k in range(3):
                sp = S(f"BBSpoke{sx}{sy}{k}", (0.32, 2.05, 0.34), (0, 0, -0.17), WOOD["base"])
                P.append(xf([sp], T(wx, sy * 2.3, 1.9) @ Ry(90) @ Rz(60 * k + 15))[0])
            P.append(C(f"BBHub{sx}{sy}", 0.48, 0.42, 0.8, (wx - sx * 0.1, sy * 2.3, 1.9), IRON["light"], sides=10,
                       rot=(0, math.radians(90 * sx), 0)))
    for sx in (-1, 1):  # side rails with iron corner brackets
        P.append(S(f"BBRail{sx}", (0.5, 6.8, 0.7), (sx * 3.05, 0, 3.1), WOOD["dark"]))
        for sy in (-1, 1):
            P.append(S(f"BBBracket{sx}{sy}", (0.62, 0.7, 0.82), (sx * 3.05, sy * 3.1, 3.04), IRON["base"]))
    # stepped cheeks (classic carriage profile) holding the trunnions
    pivot = (0, -0.2, 6.9)
    prof = [(-1.6, 0), (1.4, 0), (1.4, 2.4), (0.6, 2.4), (0.6, 3.6), (-0.6, 3.6), (-0.6, 2.9), (-1.6, 1.4)]
    for sx in (-1, 1):
        ch = prism(f"BBCheek{sx}", prof, 0.6, OAK["dark"], plane="yz", loc=(sx * 3.35, pivot[1], 3.3))
        P.append(ch)
        P.append(S(f"BBCheekStrap{sx}", (0.7, 1.4, 0.3), (sx * 3.35, pivot[1], pivot[2] + 0.35), IRON["base"]))
        P.append(C(f"BBTrunnion{sx}", 0.55, 0.55, 0.9, (sx * 3.0, pivot[1], pivot[2]), IRON["dark"], sides=12,
                   rot=(0, math.radians(90 * sx), 0)))
        P += bolts(f"BBCheekBolt{sx}", [(sx * 3.67, pivot[1] + dy, 3.4 + dz) for dy, dz in ((-1.0, 0.6), (0.9, 0.6), (0.9, 1.9))],
                   IRON["light"], 0.16)
    # rope coil + bucket on the back of the bed (story: loading the next launch)
    for k in range(3):
        P.append(tube(f"BBRope{k}", 0.85, 0.85, 0.26, 0.32, (-1.6, -2.4, 2.85 + k * 0.26), ROPE["base"] if k % 2 == 0 else ROPE["dark"], sides=14))
    P += [C("BBBucket", 0.6, 0.75, 0.95, (1.7, -2.5, 2.85), WOOD["light"], sides=12),
          tube("BBBucketHoop", 0.74, 0.74, 0.18, 0.12, (1.7, -2.5, 3.5), IRON["base"], sides=12),
          C("BBBucketWater", 0.62, 0.62, 0.05, (1.7, -2.5, 3.72), "#3EC6FF", sides=12, studs="none")]
    # trail handle at the back
    P += [S("BBTrail", (1.2, 1.7, 0.55), (0, -3.95, 2.2), WOOD["base"], rot=(math.radians(-12), 0, 0)),
          xf([tube("BBTrailRing", 0.55, 0.55, 0.3, 0.25, (0, 0, -0.15), IRON["base"], sides=14)], T(0, -4.95, 2.35) @ Ry(90))[0]]
    # --- barrel (barrel-local frame)
    BP = []
    z0, zm, z1 = -2.2, 1.4, 5.0
    ra, rm = 2.25, 2.62
    n = 16
    for i in range(n):
        a = 360.0 * i / n + 11.25
        col = (OAK["base"], OAK["light"], OAK["dark"], OAK["base"], WOOD["light"])[(i * 3) % 5]
        w = 2 * math.pi * rm / n * 0.97
        for half, (za, zb, r_a, r_b) in enumerate(((z0, zm, ra, rm), (zm, z1, rm, ra))):
            st = beam(f"BBStave{i}_{half}", (r_a + 0.22, 0, za), (r_b + 0.22, 0, zb), 0.44, w, col)
            BP.append(xf([st], Rz(a))[0])
    rr = lambda z: ra + (rm - ra) * (1 - abs(z - zm) / (zm - z0 if z < zm else z1 - zm))
    for i, z in enumerate((-1.8, -0.2, 3.0, 4.35)):
        BP.append(tube(f"BBHoop{i}", rr(z) + 0.62, rr(z + 0.5) + 0.62, 0.5, 0.36, (0, 0, z), IRON["base"] if i % 2 else IRON["dark"], sides=28))
        BP += ring_bolts(f"BBHoopRivet{i}_", rr(z + 0.25) + 0.65, z + 0.25, 8, 22.5, IRON["light"], 0.14)
    BP.append(tube("BBMuzzle", ra + 0.85, ra + 0.95, 0.7, 0.9, (0, 0, 4.85), IRON["dark"], sides=28))
    BP.append(tube("BBMuzzleLip", ra + 1.05, ra + 1.05, 0.25, 0.4, (0, 0, 5.55), IRON["light"], sides=28))
    BP.append(C("BBThroat", ra - 0.02, ra - 0.02, 0.2, (0, 0, 1.6), "#2B1C12", sides=24, studs="none"))
    BP.append(C("BBBackHead", ra + 0.45, ra + 0.45, 0.45, (0, 0, z0 - 0.3), WOOD["dark"], sides=24))
    BP.append(C("BBBackPlate", 1.6, 1.6, 0.35, (0, 0, z0 - 0.6), IRON["base"], sides=16))
    BP.append(B("BBCascabel", (0.65, 0.65, 0.65), (0, 0, z0 - 1.1), IRON["dark"], segments=12, rings=8))
    BP.append(C("BBCascabelNeck", 0.38, 0.38, 0.5, (0, 0, z0 - 1.0), IRON["base"], sides=10))
    # fuse: iron touch-hole cup on top + curling rope fuse + glowing spark
    fx, fy = polar(90, rr(-1.0) + 0.44)
    BP.append(xf([C("BBFuseCup", 0.45, 0.38, 0.45, (0, 0, 0), IRON["light"], sides=10)], T(fx, fy, -1.0) @ Rx(90))[0])
    p = Vector((fx, fy - 0.4, -1.0))
    dirs = [Vector((0.2, -1, -0.3)), Vector((0.5, -0.7, -0.5)), Vector((0.7, -0.2, -0.6)), Vector((0.4, -0.5, -0.4))]
    for j, d in enumerate(dirs):
        q = p + d.normalized() * 0.75
        BP.append(beam(f"BBFuse{j}", p, q, 0.3, 0.3, ROPE["dark"] if j % 2 else ROPE["base"], kind="cyl", sides=8))
        p = q
    BP.append(N(B("BBSpark", (0.38, 0.38, 0.38), tuple(p), "#FF8A1F", segments=10, rings=6, studs="none"), 6))
    spark = prism("BBSparkStar", star_pts(0.75, 0.28, 4, 0), 0.1, "#FFD93B", plane="xy", studs="none")
    BP.append(N(xf([spark], T(*p) @ Rx(90))[0], 5))
    BM = barrel_matrix(pivot)
    xf(BP, BM)
    P += BP
    att = {"Pivot": T(*pivot) @ Rx(TILT), "Seat": BM @ T(0, 0, 2.0) @ Rx(90), "Muzzle": BM @ T(0, 0, 5.8) @ Rx(90)}
    return name, P, att


def rocket_rig():
    """Tier 3 — chunky rocket launch tube on a tripod turntable with fins, tanks, hazard bands, thruster."""
    name = "Cannon3_RocketRig"
    HULL, RED, HAZ, STEEL = SH("#F2F5FA"), SH("#E13A2A"), SH("#FFC21A"), SH("#5B6B82")
    ORANGE = SH(SNAP)
    P = []
    # --- turntable + hazard rim
    P += [C("RRBase", 3.95, 3.95, 0.5, (0, 0, 0), STEEL["dark"], sides=32),
          C("RRDeck", 3.4, 3.4, 0.3, (0, 0, 0.5), STEEL["base"], sides=32),
          C("RRSpin", 1.9, 1.9, 0.55, (0, 0, 0.8), STEEL["light"], sides=20)]
    for i in range(16):
        P.append(tube(f"RRHaz{i}", 3.95, 3.95, 0.3, 0.55, (0, 0, 0.5), HAZ["base"] if i % 2 == 0 else INK, sides=32,
                      a0=i * 22.5, a1=(i + 1) * 22.5))
    P += ring_bolts("RRDeckBolt", 3.1, 0.8, 12, 15, "#D9DEE6", 0.13)
    # tripod legs (splayed) to a hub
    hub_z = 3.6
    for i, a in enumerate((90, 210, 330)):
        ar = math.radians(a)
        foot = Vector((math.cos(ar) * 3.0, math.sin(ar) * 3.0, 0.8))
        top = Vector((math.cos(ar) * 0.9, math.sin(ar) * 0.9, hub_z))
        P.append(beam(f"RRLeg{i}", foot + Vector((0, 0, 0.3)), top, 0.75, 0.75, RED["base"]))
        P.append(beam(f"RRLegSleeve{i}", foot + (top - foot) * 0.45, foot + (top - foot) * 0.62, 0.95, 0.95, STEEL["base"]))
        P.append(C(f"RRFoot{i}", 0.75, 0.6, 0.4, tuple(foot), STEEL["dark"], sides=10))
        P += bolts(f"RRFootBolt{i}", [tuple(foot + Vector((math.cos(ar + d) * 0.55, math.sin(ar + d) * 0.55, 0.42)))
                                      for d in (1.6, -1.6)], "#D9DEE6", 0.12)
    P += [C("RRHub", 1.35, 1.2, 1.1, (0, 0, hub_z - 0.3), STEEL["base"], sides=16),
          tube("RRHubBand", 1.42, 1.42, 0.3, 0.25, (0, 0, hub_z + 0.1), HAZ["base"], sides=16)]
    pivot = (0, -0.4, 7.2)
    for sx in (-1, 1):  # yoke arms up to the trunnions
        P.append(prism(f"RRYoke{sx}", [(-0.9, 0), (0.9, 0), (0.6, 3.8), (-0.6, 3.8)], 0.6, RED["dark"], plane="yz",
                       loc=(sx * 2.95, pivot[1], hub_z + 0.3)))
        P.append(S(f"RRYokeFoot{sx}", (3.0, 1.2, 0.5), (sx * 1.6, pivot[1], hub_z + 0.3), RED["dark"]))
        P.append(C(f"RRTrunnion{sx}", 0.6, 0.6, 0.8, (sx * 2.7, pivot[1], pivot[2]), STEEL["light"], sides=12,
                   rot=(0, math.radians(90 * sx), 0)))
    # control box on the deck (story: the launch button)
    P += [R("RRCtrlBox", (1.6, 1.0, 1.2), (0, -3.0, 0.8), STEEL["base"], radius=0.12),
          S("RRCtrlPanel", (1.3, 0.12, 0.8), (0, -2.47, 1.0), NAVY, studs="none"),
          N(C("RRButtonBig", 0.3, 0.3, 0.25, (0.25, -2.45, 1.45), "#FF3030", sides=10, studs="none", rot=(math.radians(-90), 0, 0)), 4),
          N(S("RRLedG", (0.22, 0.1, 0.18), (-0.35, -2.42, 1.55), "#5CFF6B", studs="none"), 4),
          N(S("RRLedY", (0.22, 0.1, 0.18), (-0.35, -2.42, 1.2), "#FFD93B", studs="none"), 4),
          beam("RRLever", (-0.5, -3.0, 2.0), (-0.8, -2.8, 2.7), 0.18, 0.18, INK, kind="cyl", sides=6),
          B("RRLeverKnob", (0.24, 0.24, 0.24), (-0.82, -2.79, 2.75), RED["base"], segments=8, rings=5)]
    # --- rocket tube (barrel-local)
    BP = []
    z0, z1 = -3.2, 5.2
    ro, t = 2.45, 0.38
    for i, (za, zb, col) in enumerate(((z0, -1.4, HULL["dark"]), (-1.4, 1.2, HULL["base"]), (1.2, 3.4, HULL["light"]), (3.4, z1, HULL["base"]))):
        BP.append(tube(f"RRTube{i}", ro, ro, zb - za, t, (0, 0, za), col, sides=28))
    for i, z in enumerate((-1.4, 1.2)):
        BP.append(tube(f"RRRedBand{i}", ro + 0.15, ro + 0.15, 0.6, 0.3, (0, 0, z - 0.3), RED["base"], sides=28))
        BP += ring_bolts(f"RRBandBolt{i}_", ro + 0.17, z, 10, 18, "#D9DEE6", 0.12)
    for i in range(14):  # hazard band behind the nose collar
        BP.append(tube(f"RRHazBand{i}", ro + 0.1, ro + 0.1, 0.9, 0.22, (0, 0, 3.6), HAZ["base"] if i % 2 == 0 else INK, sides=28,
                       a0=i * 360 / 14, a1=(i + 1) * 360 / 14))
    BP.append(tube("RRNose", ro + 0.55, ro + 0.4, 0.9, 0.95, (0, 0, z1 - 0.2), RED["base"], sides=28))
    BP.append(tube("RRNoseLip", ro + 0.48, ro + 0.48, 0.25, 0.4, (0, 0, z1 + 0.7), RED["light"], sides=28))
    BP += ring_bolts("RRNoseBolt", ro + 0.55, z1 + 0.25, 12, 0, "#D9DEE6", 0.13)
    BP.append(C("RRThroat", ro - t, ro - t, 0.15, (0, 0, 1.4), "#1B2233", sides=24, studs="none"))
    BP.append(N(tube("RRThroatRing", ro - t, ro - t, 0.15, 0.2, (0, 0, 1.56), "#3EF0FF", sides=24), 3))
    # tail: engine bell + neon thruster ring
    BP += [C("RRTailCap", ro + 0.05, ro + 0.05, 0.4, (0, 0, z0 - 0.4), STEEL["base"], sides=28),
           C("RRBell", 1.2, 1.9, 1.3, (0, 0, 0), STEEL["dark"], sides=20),
           N(tube("RRThrusterRing", 2.05, 2.05, 0.35, 0.35, (0, 0, 0), "#3EF0FF", sides=24), 5),
           N(C("RRThrusterCore", 1.45, 1.45, 0.12, (0, 0, 0), "#9CF8FF", sides=20, studs="none"), 3)]
    for o in BP[-3:]:
        xf([o], T(0, 0, z0 - 0.35) @ Rx(180))
    BP[-1].matrix_basis = T(0, 0, z0 - 1.5) @ Rx(180)
    BP[-2].matrix_basis = T(0, 0, z0 - 1.5) @ Rx(180)
    # 4 fins (X pattern) with white tip caps
    fin = [(-0.2, 0), (2.4, 0), (2.4, 0.5), (0.6, 2.2), (-0.6, 2.2), (-1.0, 0.5)]
    for i, a in enumerate((45, 135, 225, 315)):
        f = prism(f"RRFin{i}", [(v, u) for u, v in fin], 0.42, RED["base"], plane="xz")
        BP.append(xf([f], Rz(-a) @ T(ro - 0.1, 0, z0 + 0.2) @ Rx(0))[0])
        cap = S(f"RRFinCap{i}", (0.4, 0.5, 1.5), (0, 0, 0), HULL["light"])
        BP.append(xf([cap], Rz(-a) @ T(ro - 0.1 + 2.2 + 0.18, 0, z0 + 0.2 - 0.75))[0])
    # saddle fuel tanks on the upper flanks + straps + feed pipes
    for sx in (-1, 1):
        tx, ty = polar(90 - sx * 52, ro + 0.95)
        BP += [C(f"RRTank{sx}", 0.85, 0.85, 4.2, (tx, ty, -1.6), ORANGE["base"], sides=16),
               B(f"RRTankCapA{sx}", (0.85, 0.85, 0.6), (tx, ty, -1.6), ORANGE["dark"], segments=14, rings=8),
               B(f"RRTankCapB{sx}", (0.85, 0.85, 0.6), (tx, ty, 2.6), ORANGE["light"], segments=14, rings=8),
               tube(f"RRTankStripe{sx}", 0.9, 0.9, 0.5, 0.15, (tx, ty, 0.3), HULL["light"], sides=16)]
        for k, z in enumerate((-0.9, 1.7)):
            BP.append(tube(f"RRStrap{sx}{k}", 0.97, 0.97, 0.32, 0.14, (tx, ty, z), STEEL["dark"], sides=16))
        px, py = polar(90 - sx * 40, ro + 0.1)
        BP.append(beam(f"RRPipe{sx}", (tx * 0.92, ty * 0.92, 2.9), (px, py, 3.2), 0.3, 0.3, STEEL["light"], kind="cyl", sides=8))
    # top sight rail + 2 beacon lights
    sx_, sy_ = polar(90, ro + 0.05)
    BP.append(S("RRSightRail", (0.6, 0.5, 3.8), (sx_, sy_ - 0.2, -0.4), STEEL["base"]))
    for k, z in enumerate((-0.1, 3.0)):
        BP.append(C(f"RRBeaconBase{k}", 0.35, 0.35, 0.3, (0, 0, 0), STEEL["dark"], sides=10))
        BP.append(N(B(f"RRBeacon{k}", (0.3, 0.3, 0.3), (0, 0, 0.35), "#FF8A1F", segments=10, rings=6, studs="none"), 5))
        xf(BP[-2:], T(sx_, sy_ - 0.45, z) @ Rx(90))
    BM = barrel_matrix(pivot)
    xf(BP, BM)
    P += BP
    att = {"Pivot": T(*pivot) @ Rx(TILT), "Seat": BM @ T(0, 0, 2.0) @ Rx(90), "Muzzle": BM @ T(0, 0, 6.0) @ Rx(90)}
    return name, P, att


def mega_mortar():
    """Tier 4 — stubby huge mortar on a stone + steel geared turntable with gauges and pipes."""
    name = "Cannon4_MegaMortar"
    GUN, BRASS, ST = SH("#5B6B82"), SH("#E0A93A"), SH(STONE)
    P = []
    # --- stone + steel turntable
    P += [C("MMStone", 4.3, 4.15, 1.3, (0, 0, 0), ST["dark"], sides=10),
          C("MMStoneCap", 4.05, 4.05, 0.3, (0, 0, 1.3), ST["base"], sides=10)]
    rnd = random.Random(7)
    for i in range(10):  # exposed stone blocks round the plinth (varied)
        if i in (2,):
            continue  # front face keeps room for the control panel
        a = math.radians(36 * i + 18)
        s = rnd.uniform(0.9, 1.25)
        P.append(R(f"MMBlock{i}", (1.5 * s, 0.6, 0.75 * s), (math.cos(a) * 4.1, math.sin(a) * 4.1, rnd.uniform(0.1, 0.4)),
                   (ST["light"], ST["base"], STONE_D)[i % 3], radius=0.12, rot=(0, 0, a + math.pi / 2)))
    P += [C("MMTable", 3.9, 3.9, 0.55, (0, 0, 1.6), GUN["dark"], sides=32),
          C("MMTableTop", 3.45, 3.45, 0.25, (0, 0, 2.15), GUN["base"], sides=32)]
    for i in range(30):  # turntable ring gear teeth
        a = 360.0 * i / 30
        P.append(xf([S(f"MMRingTooth{i}", (0.42, 0.55, 0.5), (0, 0, 0), BRASS["dark"], bevel=0.03)],
                    Rz(a) @ T(3.95, 0, 1.62))[0])
    P += ring_bolts("MMTableBolt", 3.2, 2.4, 14, 0, BRASS["light"], 0.14)
    for i, ad in enumerate((54, 126, 234, 306)):  # base lights on the stone faces
        a = math.radians(ad)
        P.append(N(S(f"MMBaseLight{i}", (0.8, 0.2, 0.35), (math.cos(a) * 4.1, math.sin(a) * 4.1, 0.75), "#A8F03C", studs="none",
                     rot=(0, 0, a + math.pi / 2)), 4))
    # front control panel on the plinth: brass plate + pressure gauge + red valve wheel
    fy = 4.12
    P += [S("MMPanel", (2.6, 0.3, 1.0), (0, fy, 0.15), BRASS["base"]),
          S("MMPanelTrim", (2.8, 0.2, 0.18), (0, fy + 0.05, 1.15), BRASS["dark"]),
          C("MMPanelGauge", 0.42, 0.42, 0.2, (-0.6, fy + 0.15, 0.65), "#FFF8E8", sides=14, studs="none", rot=(math.radians(-90), 0, 0)),
          tube("MMPanelBezel", 0.48, 0.48, 0.22, 0.1, (-0.6, fy + 0.15, 0.65), BRASS["light"], sides=14, rot=(math.radians(-90), 0, 0)),
          N(S("MMPanelNeedle", (0.08, 0.06, 0.34), (-0.6, fy + 0.4, 0.6), "#FF3030", studs="none", rot=(0, math.radians(35), 0)), 3),
          C("MMValveStem", 0.14, 0.14, 0.5, (0.7, fy + 0.15, 0.65), BRASS["dark"], sides=8, rot=(math.radians(-90), 0, 0)),
          xf([tube("MMValve", 0.48, 0.48, 0.16, 0.13, (0, 0, -0.08), "#E13A2A", sides=14)], T(0.7, fy + 0.62, 0.65) @ Rx(-90))[0]]
    for k in range(2):
        P.append(xf([S(f"MMValveSpoke{k}", (0.9, 0.12, 0.12), (0, 0, -0.06), "#B6261D")], T(0.7, fy + 0.62, 0.65) @ Rx(-90) @ Rz(45 + 90 * k))[0])
    pivot = (0, -0.6, 6.9)
    prof = [(-2.2, 0), (2.2, 0), (1.5, 3.6), (1.1, 4.9), (-1.1, 4.9), (-1.7, 3.0)]
    for sx in (-1, 1):  # massive steel cheeks
        P.append(prism(f"MMCheek{sx}", prof, 0.8, GUN["base"], plane="yz", loc=(sx * 3.9, pivot[1], 2.4)))
        P.append(prism(f"MMCheekPlate{sx}", [(u * 0.7, v * 0.7 + 0.3) for u, v in prof], 0.2, GUN["light"], plane="yz",
                       loc=(sx * 4.38, pivot[1], 2.4)))
        P += bolts(f"MMCheekBolt{sx}", [(sx * 4.5, pivot[1] + dy, 2.4 + dz) for dy, dz in ((-1.2, 0.8), (1.2, 0.8), (-0.9, 2.4), (0.9, 2.4))],
                   BRASS["light"], 0.16)
        # big brass gear on the trunnion + small drive gear
        g = gear(f"MMGear{sx}", 1.9, 0.45, 14, BRASS["base"], GUN["dark"])
        xf(g, T(sx * 4.5, pivot[1], pivot[2]) @ Ry(90 * sx))
        P += g
        g2 = gear(f"MMGearS{sx}", 0.95, 0.4, 9, BRASS["dark"], GUN["dark"], tooth=0.42)
        xf(g2, T(sx * 4.5, pivot[1] - 1.85, pivot[2] - 2.1) @ Ry(90 * sx) @ Rz(10))
        P += g2
    cx = 5.1
    P += [beam("MMCrank", (4.9, pivot[1] - 1.85, pivot[2] - 2.1), (cx + 0.2, pivot[1] - 1.85, pivot[2] - 2.1), 0.3, 0.3, GUN["dark"], kind="cyl"),
          beam("MMCrankArm", (cx, pivot[1] - 1.85, pivot[2] - 2.1), (cx, pivot[1] - 2.7, pivot[2] - 2.9), 0.32, 0.32, GUN["dark"]),
          B("MMCrankKnob", (0.32, 0.32, 0.32), (cx + 0.15, pivot[1] - 2.75, pivot[2] - 2.95), "#E13A2A", segments=8, rings=5)]
    # --- barrel (barrel-local)
    BP = []
    ro, ri = 3.0, 2.4
    BP += [tube("MMBody", ro, ro + 0.15, 4.6, ro - ri, (0, 0, -1.8), GUN["base"], sides=32),
           B("MMBreech", (ro + 0.05, ro + 0.05, 2.2), (0, 0, -1.8), GUN["dark"], segments=24, rings=12),
           tube("MMBand0", ro + 0.35, ro + 0.35, 0.8, 0.5, (0, 0, -1.4), GUN["light"], sides=32),
           tube("MMBand1", ro + 0.4, ro + 0.45, 0.8, 0.5, (0, 0, 1.0), GUN["light"], sides=32),
           tube("MMMuzzle", ro + 0.45, ro + 0.95, 1.2, ro + 0.95 - ri, (0, 0, 2.8), GUN["dark"], sides=32),
           tube("MMMuzzleLip", ro + 1.05, ro + 1.05, 0.45, 0.42, (0, 0, 3.95), BRASS["base"], sides=32),
           tube("MMMuzzleFace", ro + 0.62, ro + 0.62, 0.12, ro + 0.62 - ri - 0.1, (0, 0, 4.0), GUN["light"], sides=32),
           tube("MMInnerLiner", ri + 0.02, ri + 0.02, 0.8, 0.22, (0, 0, 3.5), BRASS["dark"], sides=32),
           C("MMThroat", ri, ri, 0.15, (0, 0, 0.6), "#151A24", sides=28, studs="none"),
           N(tube("MMThroatGlow", ri, ri, 0.18, 0.22, (0, 0, 0.75), "#A8F03C", sides=28), 3)]
    BP += ring_bolts("MMBandBoltA", ro + 0.37, -1.0, 14, 0, BRASS["light"], 0.15)
    BP += ring_bolts("MMBandBoltB", ro + 0.45, 1.4, 14, 12, BRASS["light"], 0.15)
    BP += ring_bolts("MMLipBolt", ro + 0.3, 4.14, 12, 0, BRASS["light"], 0.16)
    for j in range(8):  # brass clamp blocks around the muzzle
        BP.append(xf([S(f"MMClamp{j}", (1.3, 0.9, 0.5), (0, 0, 0), BRASS["dark"])], radial(22.5 + 45 * j, ro + 0.1, 2.5))[0])
    BP += [C("MMBreechKnob", 0.8, 0.8, 0.7, (0, 0, -4.6), BRASS["base"], sides=14),
           B("MMBreechBall", (0.6, 0.6, 0.6), (0, 0, -4.7), BRASS["dark"], segments=10, rings=6)]
    # two pressure gauges on the upper flanks (dial face + neon needle + ticks) with feed pipes
    for k, (a, z) in enumerate(((60, -0.4), (120, 2.0))):
        gp = [C(f"MMGaugeBody{k}", 0.95, 0.95, 0.5, (0, 0, 0), BRASS["base"], sides=18),
              C(f"MMGaugeFace{k}", 0.78, 0.78, 0.08, (0, 0, 0.5), "#FFF8E8", sides=18, studs="none"),
              N(S(f"MMGaugeNeedle{k}", (0.12, 0.62, 0.06), (0, 0.24, 0.58), "#FF3030", studs="none", rot=(0, 0, math.radians(-35 + 70 * k))), 3),
              B(f"MMGaugePin{k}", (0.12, 0.12, 0.08), (0, 0, 0.6), INK, segments=6, rings=4, studs="none"),
              tube(f"MMGaugeBezel{k}", 0.98, 0.98, 0.15, 0.2, (0, 0, 0.5), BRASS["light"], sides=18)]
        for j in range(5):
            ta = math.radians(150 - 30 * j)
            gp.append(S(f"MMGaugeTick{k}_{j}", (0.08, 0.2, 0.04), (math.cos(ta) * 0.6, math.sin(ta) * 0.6, 0.56),
                        "#E13A2A" if j == 4 else INK, studs="none", rot=(0, 0, ta - math.pi / 2)))
        xf(gp, radial(a, ro + 0.65, z, 90 if a < 90 else -90))
        BP += gp
        px, py = polar(a, ro + 0.2)
        BP.append(xf([C(f"MMGaugeStem{k}", 0.25, 0.25, 0.7, (0, 0, 0), BRASS["dark"], sides=8)], radial(a, ro - 0.1, z))[0])
    # sight + hazard tag on top
    tx, ty = polar(90, ro + 0.4)
    BP += [S("MMSight", (0.5, 0.6, 1.6), (tx, ty - 0.1, 1.1), GUN["dark"]),
           S("MMSightTip", (0.3, 0.9, 0.3), (tx, ty - 0.45, 2.55), "#E13A2A")]
    BM = barrel_matrix(pivot)
    xf(BP, BM)
    P += BP
    att = {"Pivot": T(*pivot) @ Rx(TILT), "Seat": BM @ T(0, 0, 1.0) @ Rx(90), "Muzzle": BM @ T(0, 0, 4.4) @ Rx(90)}
    return name, P, att


def meteor_launcher():
    """Tier 5 — sci-fi twin-rail cannon: armoured shroud, neon coils, cooling vents, big crystal core."""
    name = "Cannon5_MeteorLauncher"
    NV, WH, PU = SH("#2A2F5A"), SH("#E8ECFF"), SH("#8E4FE0")
    DK = SH("#171A38")
    CY = "#3EF0FF"
    P = []
    # --- pedestal: octagon base with neon groove, armour feet, stepped tiers, armoured neck
    P += [C("MLBase", 4.3, 4.15, 0.7, (0, 0, 0), DK["base"], sides=8),
          N(tube("MLBaseGlow", 3.95, 3.95, 0.22, 0.35, (0, 0, 0.72), CY, sides=8), 2.5),
          C("MLBaseTier", 3.6, 3.3, 0.8, (0, 0, 0.7), NV["base"], sides=8),
          C("MLBaseTop", 3.0, 3.0, 0.3, (0, 0, 1.5), PU["dark"], sides=8)]
    for i in range(8):
        a = math.radians(22.5 + 45 * i)
        P.append(R(f"MLFoot{i}", (1.5, 0.9, 0.6), (math.cos(a) * 3.85, math.sin(a) * 3.85, 0), PU["base"] if i % 2 else NV["light"],
                   radius=0.12, rot=(0, 0, a + math.pi / 2)))
        P.append(N(S(f"MLFootLed{i}", (0.6, 0.12, 0.18), (math.cos(a) * 4.32, math.sin(a) * 4.32, 0.25), CY, studs="none",
                     rot=(0, 0, a + math.pi / 2)), 2.5))
    P += [C("MLNeck", 2.3, 1.9, 2.6, (0, 0, 1.8), NV["dark"], sides=8),
          tube("MLNeckBand", 2.15, 2.1, 0.4, 0.3, (0, 0, 3.1), PU["base"], sides=8)]
    for i in range(4):
        a = math.radians(45 + 90 * i)
        P.append(prism(f"MLNeckPlate{i}", [(-0.8, 0), (0.8, 0), (0.55, 2.3), (-0.55, 2.3)], 0.3, WH["dark"], plane="xz"))
        xf([P[-1]], T(math.cos(a) * 2.1, math.sin(a) * 2.1, 1.85) @ Rz(math.degrees(a) - 90) @ Rx(-8))
    pivot = (0, -1.0, 9.2)
    P.append(C("MLGimbalHub", 2.6, 2.6, 0.8, (0, 0, 4.4), NV["base"], sides=16))
    P.append(N(tube("MLGimbalGlow", 2.65, 2.65, 0.18, 0.2, (0, 0, 4.7), CY, sides=16), 2.5))
    for sx in (-1, 1):
        P.append(S(f"MLArmBase{sx}", (2.4, 2.6, 0.6), (sx * 2.9, pivot[1], 4.8), NV["light"]))
        P.append(prism(f"MLArm{sx}", [(-1.5, 0), (1.5, 0), (1.0, 4.9), (-1.0, 4.9)], 0.7, NV["base"], plane="yz",
                       loc=(sx * 3.95, pivot[1], 5.4)))
        P.append(prism(f"MLArmStripe{sx}", [(-0.3, 0.3), (0.3, 0.3), (0.3, 4.2), (-0.3, 4.2)], 0.12, PU["light"], plane="yz",
                       loc=(sx * 4.35, pivot[1], 5.4)))
        P.append(C(f"MLTrunnion{sx}", 0.9, 0.9, 1.0, (sx * 3.5, pivot[1], pivot[2]), DK["base"], sides=12,
                   rot=(0, math.radians(90 * sx), 0)))
        P.append(N(C(f"MLTrunnionGlow{sx}", 0.5, 0.5, 0.1, (sx * 4.5, pivot[1], pivot[2]), CY, sides=12, studs="none",
                     rot=(0, math.radians(90 * sx), 0)), 3))
    # --- barrel (barrel-local)
    BP = []
    ro, ri = 2.55, 2.1
    z0, z1 = -4.8, 7.4
    BP.append(tube("MLTube", ro, ro, z1 - z0, ro - ri, (0, 0, z0), NV["dark"], sides=24))
    # armoured rear shroud (octagon, flats on the sides) with purple bands
    BP += [C("MLShroud", 3.35, 3.35, 5.2, (0, 0, z0), NV["base"], sides=8, rot=(0, 0, math.radians(22.5))),
           C("MLShroudCap", 3.0, 2.7, 0.6, (0, 0, z0 + 5.2), NV["light"], sides=8, rot=(0, 0, math.radians(22.5)))]
    for i, z in enumerate((z0 + 0.5, z0 + 3.9)):
        BP.append(C(f"MLShroudBand{i}", 3.5, 3.5, 0.55, (0, 0, z), PU["base"], sides=8, rot=(0, 0, math.radians(22.5))))
    for k, a in enumerate((90, 270)):  # neon slit on top/bottom of shroud
        gx, gy = polar(a, 3.1)
        BP.append(N(S(f"MLShroudSlit{k}", (0.5, 0.2 if a == 90 else 0.2, 2.2), (gx, gy * 1.0, z0 + 1.35), PU["light"], studs="none"), 3))
    # neon coils on the exposed front of the tube
    for i, z in enumerate((1.0, 2.3, 3.6, 4.9)):
        BP.append(N(tube(f"MLCoil{i}", ro + 0.5, ro + 0.5, 0.55, 0.5, (0, 0, z), CY, sides=24), 3))
        BP.append(tube(f"MLCollar{i}", ro + 0.3, ro + 0.3, 0.5, 0.35, (0, 0, z + 0.6), DK["light"], sides=24))
    # twin rails (top + bottom): chunky prongs running past the muzzle
    for k, a in enumerate((90, 270)):
        rx_, ry_ = polar(a, ro + 1.45)
        out = -1 if a == 90 else 1
        BP += [S(f"MLRail{k}", (1.7, 1.2, z1 + 2.6 - 0.4), (rx_, ry_, 0.4), NV["light"]),
               S(f"MLRailCap{k}", (1.1, 0.3, z1 + 2.2 - 0.6), (rx_, ry_ + out * 0.7, 0.6), WH["base"]),
               R(f"MLRailTip{k}", (2.1, 1.5, 1.3), (rx_, ry_, z1 + 2.0), PU["base"], radius=0.25),
               N(S(f"MLRailTipGlow{k}", (1.4, 0.18, 0.5), (rx_, ry_ - out * 0.75, z1 + 2.4), CY, studs="none"), 3)]
        for j in range(5):
            BP.append(N(S(f"MLRailLed{k}{j}", (0.25, 0.2, 0.6), (rx_ + 0.62, ry_ + out * 0.62, 1.2 + j * 1.6), CY, studs="none"), 3))
        for j, z in enumerate((0.6, 1.9, 3.2, 4.5, 5.8)):
            sx_, sy_ = polar(a, ro + 0.45)
            BP.append(S(f"MLStrut{k}{j}", (1.0, 0.75, 0.35), (sx_, sy_, z + 0.05), WH["dark"]))
    # side cooling vents (fin stacks) on the shroud flats
    for sx in (-1, 1):
        vx = sx * 3.15
        BP.append(S(f"MLVentBox{sx}", (0.8, 2.8, 2.6), (vx, 0, z0 + 0.95), DK["base"]))
        for j in range(5):
            BP.append(S(f"MLVentFin{sx}{j}", (0.75, 3.0, 0.26), (vx + sx * 0.6, 0, z0 + 1.0 + j * 0.56), WH["dark"] if j % 2 else WH["base"]))
        BP.append(N(S(f"MLVentGlow{sx}", (0.12, 2.0, 2.3), (vx + sx * 0.45, 0, z0 + 1.1), PU["light"], studs="none"), 3))
    # muzzle brake: armoured ring + slots + neon lip
    BP += [tube("MLMuzzle", ro + 0.8, ro + 0.8, 1.3, ro + 0.8 - ri, (0, 0, z1 - 0.3), WH["base"], sides=24),
           tube("MLMuzzleBand", ro + 0.9, ro + 0.9, 0.35, 0.3, (0, 0, z1 - 0.3), PU["base"], sides=24),
           N(tube("MLMuzzleGlow", ro + 0.85, ro + 0.85, 0.25, 0.35, (0, 0, z1 + 1.0), CY, sides=24), 3.5)]
    for j in range(6):
        sl = S(f"MLMuzzleSlot{j}", (0.7, 0.45, 0.14), (0, 0, 0), DK["base"], studs="none")
        BP.append(xf([sl], radial(30 + 60 * j, ro + 0.79, z1 + 0.45, 90))[0])
    BP.append(C("MLThroat", ri, ri, 0.15, (0, 0, 2.2), "#120E2A", sides=24, studs="none"))
    BP.append(N(tube("MLThroatGlow", ri, ri, 0.22, 0.25, (0, 0, 2.38), "#C45BFF", sides=24), 3))
    # crystal core at the breech: open cage (2 rings + 4 bars) holding a big faceted crystal
    cz = z0 - 2.4
    BP += [C("MLBreech", 2.9, 2.9, 0.7, (0, 0, z0 - 0.7), DK["base"], sides=8, rot=(0, 0, math.radians(22.5))),
           tube("MLCageRingA", 2.7, 2.7, 0.5, 0.45, (0, 0, z0 - 1.1), PU["base"], sides=16),
           tube("MLCageRingB", 2.5, 2.5, 0.5, 0.45, (0, 0, z0 - 4.2), PU["base"], sides=16),
           C("MLCageEnd", 1.2, 1.2, 0.5, (0, 0, z0 - 4.6), DK["light"], sides=8)]
    for j in range(4):
        a = 45 + 90 * j
        cx_, cy_ = polar(a, 2.45)
        BP.append(beam(f"MLCageBar{j}", (cx_, cy_, z0 - 0.7), (cx_ * 0.92, cy_ * 0.92, z0 - 4.2), 0.42, 0.42, WH["base"]))
        dx_, dy_ = polar(a, 0.9)
        BP.append(beam(f"MLCageSpoke{j}", (cx_ * 0.92, cy_ * 0.92, z0 - 4.0), (dx_, dy_, z0 - 4.3), 0.3, 0.3, WH["dark"]))
    crystal = B("MLCrystal", (1.7, 1.7, 1.9), (0, 0, cz), "#C45BFF", segments=6, rings=2, studs="none")
    crystal.data.polygons.foreach_set("use_smooth", [False] * len(crystal.data.polygons))
    BP.append(N(crystal, 4))
    inner = B("MLCrystalHeart", (0.9, 0.9, 2.5), (0, 0, cz), "#F3C4FF", segments=4, rings=2, studs="none", rot=(0, 0, math.radians(30)))
    inner.data.polygons.foreach_set("use_smooth", [False] * len(inner.data.polygons))
    BP.append(N(inner, 5))
    for j in range(3):
        a = 120 * j + 90
        cx_, cy_ = polar(a, 1.55)
        sh_ = B(f"MLShard{j}", (0.45, 0.45, 0.9), (cx_, cy_, z0 - 4.0), "#E8A6FF", segments=4, rings=2, studs="none")
        sh_.data.polygons.foreach_set("use_smooth", [False] * len(sh_.data.polygons))
        BP.append(N(sh_, 4))
    for sx in (-1, 1):
        BP.append(beam(f"MLCable{sx}", (sx * 3.3, 1.0, z0 + 0.6), (sx * 2.3, 1.6, z0 - 0.9), 0.4, 0.4, INK, kind="cyl", sides=8))
    BM = barrel_matrix(pivot)
    xf(BP, BM)
    P += BP
    att = {"Pivot": T(*pivot) @ Rx(TILT), "Seat": BM @ T(0, 0, 3.0) @ Rx(90), "Muzzle": BM @ T(0, 0, z1 + 1.2) @ Rx(90)}
    return name, P, att


CANNONS = [party_popper, barrel_blaster, rocket_rig, mega_mortar, meteor_launcher]
SCALE = {"Cannon3_RocketRig": 1.08}


def build(fn):
    name, P, att = fn()
    k = SCALE.get(name, 1.0)
    if k != 1.0:
        vb.scale_group(P, k)
        att = {n: T(*(M.to_translation() * k)) @ M.to_3x3().to_4x4() for n, M in att.items()}
    return name, P, att


# ================================================================================================
# Driver
# ================================================================================================

def icon_render(meshes, path, samples):
    """Transparent 1024x1024 shop-card icon, 3/4 view, key + rim + fill."""
    setup_render(samples, (1024, 1024), transparent=True, icon=True)
    lo, hi = all_bounds(meshes)
    c = (lo + hi) / 2
    d = fit_distance(lo, hi, 50, 1.0, 1.18)
    dirv = Vector((0.72, 0.85, 0.42)).normalized()
    return shoot(path, c + dirv * d, c + Vector((0, 0, -0.2)), 50)


def lineup(prev_dir, samples):
    """Hero: all five cannons on mount rings along a studded launch deck, smallest -> biggest."""
    vb.reset_scene()
    xs = [-26.0, -14.0, -1.5, 11.5, 26.0]
    allm = []
    for i, fn in enumerate(CANNONS):
        _, P, _ = build(fn)
        P += mount_ring(f"Mount{i}")
        P.append(prism(f"Plaque{i}", [(-1.4, 0), (1.4, 0), (1.4, 1.0), (-1.4, 1.0)], 0.3, GOLD, plane="xz", loc=(0, 5.0, -0.4)))
        for k in range(i + 1):
            st = prism(f"PlaqueStar{i}_{k}", star_pts(0.32, 0.14), 0.12, "#E13A2A", plane="xz", loc=(-0.9 * (i / 2) + k * 0.45 * 2 - (i * 0.45) + (i * 0.9) / 2, 5.2, 0.1))
            P.append(st)
        xf(P, T(xs[i], 0, 0))
        allm += P
    deck = SH("#C98A4B")
    allm += [S("Deck", (74, 16, 1.0), (0, 0, -1.45), deck["base"]),
             S("DeckLip", (74.4, 1.2, 1.2), (0, 7.6, -1.55), "#FFC21A")]
    for i in range(30):
        allm.append(S(f"DeckHaz{i}", (1.2, 1.24, 1.22), (-36.0 + i * 2.5, 7.6, -1.56), INK))
    allm += review_ground(200, -1.45)
    vb.restud(allm)
    setup_render(samples)
    return shoot(os.path.join(prev_dir, "Cannons_Lineup_HERO.png"), (14, 52, 20), (0, 0, 5.0), 32)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    opts = {"out": EXPORT_DIR, "samples": 28, "only": None, "render": True, "icons": True, "lineup": True}
    it = iter(argv)
    for a in it:
        if a == "--samples":
            opts["samples"] = int(next(it))
        elif a == "--only":
            opts["only"] = next(it)
        elif a == "--no-render":
            opts["render"] = False
        elif a == "--no-icons":
            opts["icons"] = False
        elif a == "--no-lineup":
            opts["lineup"] = False
        else:
            opts["out"] = os.path.abspath(a)
    return opts


def merge_manifest(entries, path):
    data = []
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    names = {e["name"] for e in entries}
    data = [d for d in data if d["name"] not in names] + entries
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def main():
    opts = parse_args()
    entries = []
    for n, fn in enumerate(CANNONS, start=1):
        if opts["only"] and opts["only"] not in fn.__name__ and opts["only"] not in str(n):
            continue
        vb.reset_scene()
        name, P, att = build(fn)
        entry, meshes = finish_model(name, P, opts["out"], "cannon", att)
        entries.append(entry)
        if opts["render"]:
            mr = mount_ring()
            vb.restud(mr)
            review_ground(80, -0.45)
            setup_render(opts["samples"])
            render_views(name, meshes, PREVIEW_DIR, opts["samples"])
        if opts["icons"]:
            for o in [o for o in bpy.context.scene.objects if o.name.startswith(("Rev", "Mount"))]:
                bpy.data.objects.remove(o)
            icon_render(meshes, os.path.join(UI_DIR, f"cannon_{n}.png"), max(24, opts["samples"]))
    merge_manifest(entries, os.path.join(GAME, "assets", "manifest-props.json"))
    if opts["lineup"] and opts["render"] and not opts["only"]:
        lineup(PREVIEW_DIR, opts["samples"])


if __name__ == "__main__":
    main()
