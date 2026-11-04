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
    """Adds a single joined stud mesh on top of a block made by block()/studded_plate().
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


def studded_plate(name, width, depth, height=1.0, location=(0, 0, 0), color="green", spacing=1.0):
    plate = block(name, (width, depth, height), location, color, bevel=0.06)
    studs(plate, spacing=spacing)
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
