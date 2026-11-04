"""
vault_blocky — Blender helper library for the house blocky/studded Roblox look.

Run inside Blender (GUI, `blender -b -P script.py`, the Blender MCP `execute_blender_code`
tool, or the `bpy` PyPI module). Everything is low-poly by construction.

Units: 1 Blender unit = 1 Roblox stud. Exports use FBX scaled for Roblox import
(see `export_fbx`). Pivot convention: bottom-center of each asset.

Main API
    reset_scene()
    palette_material(name, hex, emission=0.0)       -> material (cached by name)
    block(name, size, location, color, bevel=0.08)  -> chunky rounded box
    studs(target, spacing=1.0, ...)                 -> stud cylinders on the top face
    studded_plate(name, w, d, h, location, color)   -> baseplate/platform with studs
    cylinder(...), wedge(...)                       -> other chunky primitives
    group(name, objects)                            -> parent objects to an empty
    join(name, objects)                             -> single mesh (for export)
    poly_report(objects)                            -> {"tris": n, "objects": n}
    export_fbx(path, objects) / export_glb(path, objects)
"""

from __future__ import annotations

import json
import math
import os

import bpy
import bmesh

# House palette (style/house-style.md). Profiles may pass their own hex values.
PALETTE = {
    "red": "#E13A2A",
    "red_dark": "#B6261D",
    "green": "#7ADE43",
    "green_lip": "#57AC35",
    "blue": "#2590D1",
    "blue_alt": "#326BE3",
    "yellow": "#E2C608",
    "purple": "#B678EA",
    "pink": "#DD70E1",
    "lime": "#78BE0E",
    "gold": "#FFD93B",
    "navy": "#1E1B33",
    "white": "#F5F5F5",
    "stone": "#8A8F98",
    "wood": "#A0662E",
    "water": "#3EC6FF",
}

STUD_RADIUS = 0.3
STUD_HEIGHT = 0.18
MAX_STUDS_PER_SURFACE = 400  # mobile budget guard; larger surfaces use a stud texture instead


def _set_size(obj, size):
    """Stores the authored size as scalar props (FBX export can't serialise list props)."""
    obj["vault_sx"], obj["vault_sy"], obj["vault_sz"] = (float(v) for v in size)


def _get_size(obj):
    if "vault_sx" in obj:
        return obj["vault_sx"], obj["vault_sy"], obj["vault_sz"]
    return tuple(obj.dimensions)


def hex_to_rgba(hex_color: str) -> tuple[float, float, float, float]:
    h = PALETTE.get(hex_color, hex_color).lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

    # sRGB -> linear for Blender's color pipeline
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return (lin(r), lin(g), lin(b), 1.0)


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "NONE"


def palette_material(name: str, hex_color: str, emission: float = 0.0, roughness: float = 0.55):
    mat_name = f"M_{name}"
    mat = bpy.data.materials.get(mat_name)
    if mat:
        return mat
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    rgba = hex_to_rgba(hex_color)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = roughness
        if emission > 0:
            bsdf.inputs["Emission Color"].default_value = rgba
            bsdf.inputs["Emission Strength"].default_value = emission
    mat.diffuse_color = rgba
    # Custom props survive FBX export and tell the Studio importer what to do.
    mat["roblox_color"] = PALETTE.get(hex_color, hex_color)
    mat["roblox_neon"] = emission > 0
    return mat


def _assign(obj, material) -> None:
    if material is None:
        return
    obj.data.materials.clear()
    obj.data.materials.append(material)


def _new_mesh_object(name: str, bm: bmesh.types.BMesh):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def block(name, size=(1, 1, 1), location=(0, 0, 0), color="red", bevel=0.08, emission=0.0, segments=1):
    """Chunky box. location is the bottom-center. Bevel gives the soft toy-brick edge."""
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z = (v.co.z + 0.5) * sz  # bottom at z=0
    if bevel > 0:
        b = min(bevel, min(size) * 0.45)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, segments=segments, affect="EDGES")
    obj = _new_mesh_object(name, bm)
    obj.location = location
    _assign(obj, palette_material(color, color, emission))
    obj["vault_kind"] = "block"
    return obj


def cylinder(name, radius=0.5, height=1.0, location=(0, 0, 0), color="red", sides=12, emission=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=radius, radius2=radius, depth=height)
    for v in bm.verts:
        v.co.z += height / 2
    obj = _new_mesh_object(name, bm)
    obj.location = location
    _assign(obj, palette_material(color, color, emission))
    return obj


def wedge(name, size=(1, 1, 1), location=(0, 0, 0), color="red"):
    """Ramp/wedge: slopes up along +Y."""
    sx, sy, sz = size
    bm = bmesh.new()
    pts = [(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)]
    top = [(-sx / 2, sy / 2, sz), (sx / 2, sy / 2, sz)]
    v = [bm.verts.new(p) for p in pts + top]
    bm.faces.new((v[0], v[1], v[2], v[3]))
    bm.faces.new((v[3], v[2], v[5], v[4]))
    bm.faces.new((v[0], v[4], v[5], v[1]))
    bm.faces.new((v[0], v[3], v[4]))
    bm.faces.new((v[1], v[5], v[2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _new_mesh_object(name, bm)
    obj.location = location
    _assign(obj, palette_material(color, color))
    return obj


def studs(target, spacing=1.0, color=None, margin=0.5, max_studs=MAX_STUDS_PER_SURFACE):
    """LEGACY — physical stud geometry is banned for game assets (L-20261104-04); kept only for
    explicitly owner-approved hero close-ups. Adds a single joined stud mesh on top of a block made by block()/studded_plate().
    Returns the stud object, or None if the surface would exceed max_studs (use a texture)."""
    sx, sy, sz = target.dimensions
    nx = max(1, int((sx - 2 * margin) // spacing) + 1)
    ny = max(1, int((sy - 2 * margin) // spacing) + 1)
    if nx * ny > max_studs:
        target["vault_stud_texture"] = True  # importer applies the stud texture instead
        return None
    # Studs scale with spacing so big map plates keep chunky, readable studs (Roblox ratio).
    radius, height = STUD_RADIUS * spacing, STUD_HEIGHT * spacing
    bm = bmesh.new()
    x0 = -(nx - 1) * spacing / 2
    y0 = -(ny - 1) * spacing / 2
    for ix in range(nx):
        for iy in range(ny):
            ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=radius, radius2=radius, depth=height)
            for vert in ret["verts"]:
                vert.co.x += x0 + ix * spacing
                vert.co.y += y0 + iy * spacing
                vert.co.z += sz + height / 2
    obj = _new_mesh_object(f"{target.name}_Studs", bm)
    mat = target.data.materials[0] if color is None and target.data.materials else None
    _assign(obj, mat or palette_material(color or "white", color or "white"))
    # Stud verts are in the target's local space: parent with identity inverse, zero offset.
    # (Do NOT use target.matrix_world here — it is stale until the depsgraph updates.)
    obj.parent = target
    obj.location = (0, 0, 0)
    return obj


def stud_patch(name, center, cols, rows, spacing=0.9, color="white", radius=None, height=None, parent=None):
    """Studs placed at an exact world position (z = surface top). Use on characters/pets where
    studs must sit on a specific visible area (top of head, back), not the whole top face."""
    r = radius if radius is not None else STUD_RADIUS * spacing * 1.1
    h = height if height is not None else STUD_HEIGHT * spacing * 1.2
    cx, cy, cz = center
    bm = bmesh.new()
    for ix in range(cols):
        for iy in range(rows):
            ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=r, depth=h)
            for vert in ret["verts"]:
                vert.co.x += cx + (ix - (cols - 1) / 2) * spacing
                vert.co.y += cy + (iy - (rows - 1) / 2) * spacing
                vert.co.z += cz + h / 2
    obj = _new_mesh_object(name, bm)
    _assign(obj, palette_material(color, color))
    obj["vault_kind"] = "studs"
    if parent is not None:
        obj.parent = parent
    return obj


def studded_plate(name, width, depth, height=1.0, location=(0, 0, 0), color="green", spacing=1.0):
    plate = block(name, (width, depth, height), location, color, bevel=0.04)
    _set_size(plate, (width, depth, height))
    stud_surface(plate, "all")  # texture studs on every side (L-20261104-05)
    plate["vault_kind"] = "studded_plate"
    return plate


def group(name, objects, location=(0, 0, 0)):
    empty = bpy.data.objects.new(name, None)
    empty.location = location
    bpy.context.scene.collection.objects.link(empty)
    for obj in objects:
        if obj.parent is None:
            obj.parent = empty
    return empty


def _descendants(obj):
    out = []
    for child in obj.children:
        out.append(child)
        out.extend(_descendants(child))
    return out


def join(name, objects):
    """Joins meshes into one object (keeps per-face materials). Fewer draw calls in Roblox."""
    meshes = [o for o in objects if o.type == "MESH"]
    for o in list(meshes):
        meshes.extend(d for d in _descendants(o) if d.type == "MESH" and d not in meshes)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    for o in meshes:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = name
    return result


def poly_report(objects=None) -> dict:
    objs = list(objects or [o for o in bpy.context.scene.objects if o.type == "MESH"])
    for o in list(objs):  # include children such as stud meshes
        objs.extend(d for d in _descendants(o) if d not in objs)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for o in objs:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(depsgraph)
        mesh = ev.to_mesh()
        mesh.calc_loop_triangles()
        tris += len(mesh.loop_triangles)
        ev.to_mesh_clear()
    return {"tris": tris, "objects": len([o for o in objs if o.type == "MESH"])}


def _select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
        for d in _descendants(o):
            d.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]


def export_fbx(path: str, objects=None, global_scale: float = 1.0) -> str:
    """FBX for Roblox (Studio 3D Importer / Open Cloud assets).

    Scale is NOT assumed: the first import of every game must bring in
    `templates/scale_reference.py`'s 4x4x4 cube and confirm it measures 4 studs with the
    importer's File Dimensions setting. Record the working setting in lessons/global.md.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if objects is not None:
        _select_only(objects)
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=objects is not None,
        apply_unit_scale=True,
        global_scale=global_scale,
        axis_forward="-Z",
        axis_up="Y",
        object_types={"MESH", "EMPTY", "ARMATURE"},
        use_custom_props=True,
        add_leaf_bones=False,
        bake_anim=False,
        mesh_smooth_type="FACE",
    )
    return path


def export_glb(path: str, objects=None) -> str:
    """GLB preview for artifacts / review before Roblox import."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if objects is not None:
        _select_only(objects)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=objects is not None)
    return path


def write_manifest(path: str, entries: list[dict]) -> str:
    """assets manifest consumed by games/<slug>/assets/manifest.json + Studio import step."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "assets": entries}, f, indent=2)
    return path


def ring_positions(count: int, radius: float, z: float = 0.0):
    """Evenly spaced points on a circle (plots around a hub, zones around spawn)."""
    for i in range(count):
        a = 2 * math.pi * i / count
        yield (math.cos(a) * radius, math.sin(a) * radius, z), a


# ---------------------------------------------------------------------------------------------
# Reference-derived construction languages (style-guides/3D_STYLE_BIBLE.md)
#   BRICK  — environments/buildings/props: stacked bricks with visible seams, crisp edges,
#            geometry studs on visible top (and some side) faces.
#   VOXEL  — collectibles/creatures: many small cubes, per-voxel colour jitter, pixel faces.
# ---------------------------------------------------------------------------------------------

BRICK_H = 1.2  # LEGO-like brick height in studs (plates = 0.4)
PLATE_H = 0.4
BRICK_BEVEL = 0.035  # crisp edges: seams read, corners don't look soft


def brick(name, size, location, color, top_studs=True, side_studs=(), emission=0.0, spacing=1.0):
    """A brick: crisp box + studs. side_studs: any of '+x','-x','+y','-y'."""
    obj = block(name, size, location, color, bevel=BRICK_BEVEL, segments=1, emission=emission)
    _set_size(obj, size)
    out = [obj]
    if top_studs:
        s = face_studs(obj, "+z", spacing=spacing)
        if s:
            out.append(s)
    for axis in side_studs:
        s = face_studs(obj, axis, spacing=spacing)
        if s:
            out.append(s)
    return out


_AXES = {
    "+z": ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    "+x": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "-x": ((-1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "+y": ((0, 1, 0), (1, 0, 0), (0, 0, 1)),
    "-y": ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
}


def face_studs(target, axis="+z", spacing=1.0, margin=None, color=None, max_studs=MAX_STUDS_PER_SURFACE):
    """Geometry studs on one face of a brick made by brick()/block() (uses vault_size)."""
    sx, sy, sz = _get_size(target)
    lx, ly, lz = target.location
    n, u, v = _AXES[axis]
    dims = {"x": sx, "y": sy, "z": sz}
    names = "xyz"
    su = dims[names[u.index(1)]]
    sv = dims[names[v.index(1)]]
    m = margin if margin is not None else spacing / 2
    nu = max(1, int((su - 2 * m + 1e-6) // spacing) + 1)
    nv = max(1, int((sv - 2 * m + 1e-6) // spacing) + 1)
    if su < spacing * 0.9 or sv < spacing * 0.9:
        return None
    if nu * nv > max_studs:
        target["vault_stud_texture"] = True
        return None
    center = [lx, ly, lz + sz / 2]
    for i in range(3):
        if n[i] != 0:
            half = (sx, sy, sz)[i] / 2
            center[i] += n[i] * half
    r, h = STUD_RADIUS * spacing, STUD_HEIGHT * spacing
    bm = bmesh.new()
    for iu in range(nu):
        for iv in range(nv):
            ou = (iu - (nu - 1) / 2) * spacing
            ov = (iv - (nv - 1) / 2) * spacing
            ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=r, radius2=r, depth=h)
            for vert in ret["verts"]:
                a, b, c = vert.co.x, vert.co.y, vert.co.z + h / 2  # c along normal, 0..h
                vert.co.x = center[0] + a * u[0] + b * v[0] + c * n[0] + ou * u[0] + ov * v[0]
                vert.co.y = center[1] + a * u[1] + b * v[1] + c * n[1] + ou * u[1] + ov * v[1]
                vert.co.z = center[2] + a * u[2] + b * v[2] + c * n[2] + ou * u[2] + ov * v[2]
    obj = _new_mesh_object(f"{target.name}_Studs{axis}", bm)
    mat = target.data.materials[0] if color is None and target.data.materials else None
    _assign(obj, mat or palette_material(color, color))
    obj["vault_kind"] = "studs"
    return obj


def _shade(hex_color: str, factor: float) -> str:
    h = PALETTE.get(hex_color, hex_color).lstrip("#")
    rgb = [min(255, max(0, int(int(h[i : i + 2], 16) * factor))) for i in (0, 2, 4)]
    return "#{:02X}{:02X}{:02X}".format(*rgb)


_FACES = [
    ((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
    ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
    ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
    ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
    ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
    ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)]),
]


def voxel_mesh(name, voxels, voxel=0.25, origin=(0, 0, 0), jitter=0.07, seed=7, emissive=None):
    """Builds ONE mesh from a voxel dict {(ix,iy,iz): '#RRGGBB'}. Hidden faces are culled, verts
    are shared (watertight). Each voxel gets one of 3 shade variants so the voxel grid reads like
    the references. emissive = {hex: strength} for glowing colours."""
    import random

    rnd = random.Random(seed)
    emissive = emissive or {}
    bm = bmesh.new()
    verts = {}
    mats, mat_slot = [], {}

    def vert(p):
        if p not in verts:
            verts[p] = bm.verts.new((origin[0] + p[0] * voxel, origin[1] + p[1] * voxel, origin[2] + p[2] * voxel))
        return verts[p]

    for (x, y, z), col in voxels.items():
        variant = rnd.choice((1 - jitter, 1.0, 1 + jitter)) if col not in emissive else 1.0
        key = (col, variant)
        if key not in mat_slot:
            mat_slot[key] = len(mats)
            mats.append(palette_material(f"{col.lstrip('#')}_{variant:.2f}", _shade(col, variant),
                                         emission=emissive.get(col, 0.0)))
        for (dx, dy, dz), corners in _FACES:
            if (x + dx, y + dy, z + dz) in voxels:
                continue
            f = bm.faces.new([vert((x + cx, y + cy, z + cz)) for cx, cy, cz in corners])
            f.material_index = mat_slot[key]
    obj = _new_mesh_object(name, bm)
    for m in mats:
        obj.data.materials.append(m)
    obj["vault_kind"] = "voxel"
    obj["vault_voxels"] = len(voxels)
    return obj


class VoxelCanvas:
    """Helper to rasterise shapes into a voxel dict (units = voxels). Later writes overwrite."""

    def __init__(self):
        self.v = {}

    def box(self, x0, x1, y0, y1, z0, z1, col):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    self.v[(x, y, z)] = col

    def ellipsoid(self, cx, cy, cz, rx, ry, rz, col, only_if=None):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for z in range(int(cz - rz) - 1, int(cz + rz) + 2):
                    d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 + ((z + 0.5 - cz) / rz) ** 2
                    if d <= 1 and (only_if is None or only_if(x, y, z)):
                        self.v[(x, y, z)] = col

    def cylinder(self, cx, cy, z0, z1, r0, r1, col):
        for z in range(z0, z1 + 1):
            t = 0 if z1 == z0 else (z - z0) / (z1 - z0)
            r = r0 + (r1 - r0) * t
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                for y in range(int(cy - r) - 1, int(cy + r) + 2):
                    if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                        self.v[(x, y, z)] = col

    def paint(self, pred, col):
        """Recolour existing voxels where pred(x, y, z) is true."""
        for k in list(self.v):
            if pred(*k):
                self.v[k] = col

    def downsample(self, f=2, min_fill=4):
        """Merges f^3 cells into one bigger block (majority colour). Owner feedback: collectibles
        should read as chunky MERGED blocks, not hundreds of tiny voxels."""
        cells = {}
        for (x, y, z), col in self.v.items():
            k = (x // f, y // f, z // f)
            cells.setdefault(k, []).append(col)
        out = VoxelCanvas()
        for k, cols in cells.items():
            if len(cols) >= min_fill:
                out.v[k] = max(set(cols), key=cols.count)
        return out

    def front_y(self, x, z):
        """Largest y filled at column (x, z) — the visible front surface (+y faces the camera)."""
        ys = [k[1] for k in self.v if k[0] == x and k[2] == z]
        return max(ys) if ys else None


# ---------------------------------------------------------------------------------------------
# STUD TEXTURE (owner rule, L-20261104-04): studs are part of the SURFACE TEXTURE, never physical
# geometry. One UV unit = one stud. Roblox side: the generated stud normal map is used as a
# MaterialVariant / SurfaceAppearance normal map, tinted by the part colour.
# ---------------------------------------------------------------------------------------------

STUD_TEX_PX = 128
STUD_PITCH = 0.5  # stud spacing in studs — owner chose B (half size), L-20261104-06; bible §2
_TEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "textures")


def stud_texture_paths():
    return os.path.join(_TEX_DIR, "stud_height.png"), os.path.join(_TEX_DIR, "stud_normal.png")


def ensure_stud_textures(force=False):
    """Generates one-stud tile textures (height + tangent-space normal) if missing."""
    hpath, npath = stud_texture_paths()
    if os.path.exists(hpath) and os.path.exists(npath) and not force:
        return hpath, npath
    os.makedirs(_TEX_DIR, exist_ok=True)
    n = STUD_TEX_PX
    R, EDGE = 0.27, 0.03  # Roblox-like stud: ~0.54 stud diameter per 1-stud tile, soft shoulder

    def height(u, v):
        r = math.hypot(u - 0.5, v - 0.5)
        if r >= R + EDGE:
            return 0.0
        if r <= R:
            return 0.55 + 0.45 * (1 - (r / R) ** 2)  # rounded top: shades light->dark like a raised stud
        t = (R + EDGE - r) / EDGE
        return 0.55 * t * t * (3 - 2 * t)

    H = [[height((x + 0.5) / n, (y + 0.5) / n) for x in range(n)] for y in range(n)]
    hp, np_ = [], []
    for y in range(n):
        for x in range(n):
            h = H[y][x]
            hp += [h, h, h, 1.0]
            dx = H[y][(x + 1) % n] - H[y][(x - 1) % n]
            dy = H[(y + 1) % n][x] - H[(y - 1) % n][x]
            k = 6.0
            nx, ny, nz = -dx * k, -dy * k, 1.0
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            np_ += [nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5, 1.0]
    for path, px, name in ((hpath, hp, "stud_height"), (npath, np_, "stud_normal")):
        img = bpy.data.images.new(name, n, n, alpha=False, float_buffer=False)
        img.pixels = px
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
    return hpath, npath


def studded_material(base):
    """Studded variant of a palette material: base colour + stud bump from the height tile."""
    name = base.name + "_Studs"
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = base.copy()
    mat.name = name
    hpath, _ = ensure_stud_textures()
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    uv = nt.nodes.new("ShaderNodeUVMap")
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.get("stud_height_tile") or bpy.data.images.load(hpath)
    img.name = "stud_height_tile"
    img.colorspace_settings.name = "Non-Color"
    tex.image = img
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.12
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mat["vault_studs"] = True
    return mat


def stud_surface(obj, mode="all"):
    """Texture studs at TRUE Roblox size: world-space box UVs, 1 UV unit = 1 stud, so studs keep
    their real size no matter how the object is scaled/rotated (call again via restud() after
    transforming). mode: 'all' (default, owner rule L-20261104-05), 'top', or 'none'."""
    if obj.type != "MESH" or mode == "none":
        return obj
    bpy.context.view_layer.update()
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uvl = me.uv_layers.active.data
    mw = obj.matrix_world
    rot = mw.to_3x3()
    for poly in me.polygons:
        n = (rot @ poly.normal).normalized()
        nx, ny, nz = n
        studded = (mode == "all") or (nz > 0.7)
        for li in poly.loop_indices:
            w = mw @ me.vertices[me.loops[li].vertex_index].co
            if not studded:
                uvl[li].uv = (0.02, 0.02)
            elif abs(nz) >= max(abs(nx), abs(ny)):
                uvl[li].uv = (w.x / STUD_PITCH, w.y / STUD_PITCH)
            elif abs(nx) >= abs(ny):
                uvl[li].uv = (w.y / STUD_PITCH, w.z / STUD_PITCH)
            else:
                uvl[li].uv = (w.x / STUD_PITCH, w.z / STUD_PITCH)
    for i, m in enumerate(me.materials):
        if m is not None and not m.get("vault_studs") and not m.get("roblox_neon"):
            me.materials[i] = studded_material(m)
    obj["vault_stud_mode"] = mode
    return obj


def restud(objs):
    """Recompute stud UVs after moving/scaling/rotating objects."""
    for o in objs:
        mode = o.get("vault_stud_mode")
        if mode and mode != "none":
            stud_surface(o, mode)


def scale_group(objs, k, origin=(0.0, 0.0, 0.0)):
    """Scales a model about an origin (top-level objects), then restuds so studs stay 1 stud."""
    ox, oy, oz = origin
    for o in objs:
        if o.parent is None:
            o.location = (ox + (o.location[0] - ox) * k, oy + (o.location[1] - oy) * k, oz + (o.location[2] - oz) * k)
            o.scale = (o.scale[0] * k, o.scale[1] * k, o.scale[2] * k)
    restud(objs)
    return objs


def _finish(obj, color, emission, studs, rot):
    _assign(obj, palette_material(color, color, emission))
    if rot:
        obj.rotation_euler = rot
    if emission == 0:
        stud_surface(obj, studs)
    return obj


def cyl(name, r1, r2, h, location, color, sides=16, studs="all", rot=None, emission=0.0):
    """Cylinder/cone (r1 bottom, r2 top); location = bottom centre. Studded like every block."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=r1, radius2=r2, depth=h)
    for v in bm.verts:
        v.co.z += h / 2
    obj = _new_mesh_object(name, bm)
    obj.location = location
    return _finish(obj, color, emission, studs, rot)


def ball(name, radii, center, color, segments=18, rings=10, studs="all", rot=None, emission=0.0):
    """Ellipsoid (rx, ry, rz) at a centre point — for heads, eyes, bellies, bushes."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
    rx, ry, rz = radii
    for v in bm.verts:
        v.co.x *= rx
        v.co.y *= ry
        v.co.z *= rz
    obj = _new_mesh_object(name, bm)
    obj.location = center
    for p in obj.data.polygons:
        p.use_smooth = True
    return _finish(obj, color, emission, studs, rot)


def rounded(name, size, location, color, radius=0.3, studs="all", rot=None, emission=0.0):
    """Soft rounded box (pillowy) — location = bottom centre."""
    obj = block(name, size, location, color, bevel=radius, segments=3, emission=emission)
    _set_size(obj, size)
    if rot:
        obj.rotation_euler = rot
    if emission == 0:
        stud_surface(obj, studs)
    return obj


def ellipsoid_front(center, radii, x, z):
    """Front (+y) surface y of an ellipsoid at (x, z) — to seat face pieces on round heads."""
    cx, cy, cz = center
    rx, ry, rz = radii
    t = 1 - ((x - cx) / rx) ** 2 - ((z - cz) / rz) ** 2
    return cy + ry * math.sqrt(max(t, 0.0))


def solid(name, size, location, color, bevel=0.04, studs="all", emission=0.0, rot=None):
    """Default building block for props/maps: one clean chunky solid with crisp edges and
    texture studs. No seams, no stud geometry."""
    obj = block(name, size, location, color, bevel=bevel, segments=1, emission=emission)
    _set_size(obj, size)
    if rot:
        obj.rotation_euler = rot
    if emission == 0:
        stud_surface(obj, studs)
    return obj
