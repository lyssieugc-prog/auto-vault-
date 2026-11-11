"""
vet_common — shared helpers for My Vet Office Blender scripts (pets + props).

Builds on blender/lib/vault_blocky.py (materials, stud TEXTURE, joins, export) and adds:
  * centre-based chunky primitives: box / taper / seg (box along a vector) / orb / dome / tube / torus
    — every non-face, non-neon piece gets world-space texture studs at vb.STUD_PITCH (0.5).
  * build_rig(): armature with uniform bone orientation + one rigid mesh per bone (`<Bone>_Geo`,
    100 % weighted to that bone) so Roblox can drive each part with a Motor6D.
  * pose helpers, tri/bone checks, and a Cycles preview renderer using the bible §10 lighting.

Units: 1 Blender unit = 1 stud. Front = +Y, up = +Z, character LEFT = -X.
"""

from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "blender", "lib"))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

import vault_blocky as vb  # noqa: E402
import vault_kit as vk  # noqa: E402

EXPORT_DIR = os.path.join(REPO, "games", "my-vet-office", "assets", "export")
PREVIEW_DIR = os.path.join(REPO, "games", "my-vet-office", "assets", "previews")

MAX_TRIS_PER_MESH = 15000  # qa/performance-budget.md (Roblox hard cap 20k)

# ---------------------------------------------------------------------------------------------
# Primitives (centre-based). All return the new object; `out` lists collect them.
# ---------------------------------------------------------------------------------------------


def _rot(rot):
    if rot is None:
        return None
    return tuple(math.radians(a) for a in rot)


def _finish(obj, color, emission=0.0, studs=True, rot=None, smooth=False, roughness=0.55):
    obj.data.materials.clear()
    obj.data.materials.append(vb.palette_material(color, color, emission, roughness=roughness))
    if rot is not None:
        obj.rotation_euler = _rot(rot)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    if studs and emission == 0:
        vb.stud_surface(obj, "all")
    else:
        obj["vault_stud_mode"] = "none"
    return obj


def _bevel(bm, r, seg, dims, axis=None):
    if r > 0:
        r = min(r, min(dims) * 0.45)
        edges = list(bm.edges)
        if axis is not None:  # only edges running along `axis` (0=x,1=y,2=z): continuous extruded look
            edges = [e for e in edges if abs((e.verts[1].co - e.verts[0].co).normalized()[axis]) > 0.9]
        # profile=0.5 + clamp: bmesh's default profile makes multi-segment bevels concave/pinched
        # (cross-shaped boxes). vault_blocky.block() has the same issue for segments >= 2 (reported).
        bmesh.ops.bevel(bm, geom=edges, offset=r, segments=seg, affect="EDGES", profile=0.5,
                        clamp_overlap=True)


def box(name, size, center, color, r=0.05, seg=1, rot=None, studs=True, emission=0.0, top=(1.0, 1.0),
        shear=(0.0, 0.0), roughness=0.55, bevel_axis=None):
    """Chunky box centred on `center`. top=(fx, fy) scales the +Z end (taper), shear offsets it (x, y).
    bevel_axis=1 rounds only the edges running along Y (segments that must butt seamlessly)."""
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        up = v.co.z > 0
        fx, fy = top if up else (1.0, 1.0)
        v.co.x = v.co.x * sx * fx + (shear[0] if up else 0.0)
        v.co.y = v.co.y * sy * fy + (shear[1] if up else 0.0)
        v.co.z *= sz
    _bevel(bm, r, seg, (sx * min(1, top[0]), sy * min(1, top[1]), sz), bevel_axis)
    obj = vb._new_mesh_object(name, bm)
    obj.location = center
    return _finish(obj, color, emission, studs, rot, roughness=roughness)


def taper(name, size, center, color, top=(0.7, 0.7), **kw):
    return box(name, size, center, color, top=top, **kw)


def seg(name, a, b, thick, color, r=0.08, segs=1, top=(1.0, 1.0), overlap=0.0, studs=True, emission=0.0):
    """Box running from point a to point b (local +Z along a->b). thick=(x, y) cross-section;
    top scales the b end. overlap extends both ends (hides joint gaps)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length + 2 * overlap
    c = (a + b) / 2
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    obj = box(name, (thick[0], thick[1], L), c, color, r=r, seg=segs, top=top, studs=False, emission=emission)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = q
    if studs and emission == 0:
        vb.stud_surface(obj, "all")
    return obj


def orb(name, radii, center, color, segs=10, rings=7, rot=None, studs=True, emission=0.0, smooth=False):
    """Low-poly ellipsoid (faceted by default: reads chunky, not smooth-blob)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    for v in bm.verts:
        v.co.x *= radii[0]
        v.co.y *= radii[1]
        v.co.z *= radii[2]
    obj = vb._new_mesh_object(name, bm)
    obj.location = center
    return _finish(obj, color, emission, studs, rot, smooth=smooth)


def dome(name, radii, center, color, segs=12, rings=8, rot=None, studs=True, cut=0.0):
    """Upper half-ellipsoid shell cap (z >= cut*rz) — eyelids, caps, domes."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < cut - 1e-4], context="VERTS")
    # close the open rim with a flat cap so the lid is a solid piece
    edges = [e for e in bm.edges if e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    for v in bm.verts:
        v.co.x *= radii[0]
        v.co.y *= radii[1]
        v.co.z *= radii[2]
    obj = vb._new_mesh_object(name, bm)
    obj.location = center
    return _finish(obj, color, 0.0, studs, rot)


def tube(name, radius, height, center, color, sides=12, rot=None, studs=True, emission=0.0, r2=None,
         roughness=0.55):
    """Cylinder centred on `center` along local Z (r2 = top radius for cones)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=radius, radius2=radius if r2 is None else r2,
                          depth=height)
    obj = vb._new_mesh_object(name, bm)
    obj.location = center
    return _finish(obj, color, emission, studs, rot, roughness=roughness)


def ring(name, radius, thick, width, center, color, sides=14, rot=None, studs=True, scale=(1, 1)):
    """Flat band (collar, hose clamp): rectangular cross-section torus, axis = local Z."""
    bm = bmesh.new()
    rings_ = []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        ca, sa = math.cos(a) * scale[0], math.sin(a) * scale[1]
        quad = [bm.verts.new((ca * (radius + dr), sa * (radius + dr), dz))
                for dr, dz in ((-thick / 2, -width / 2), (thick / 2, -width / 2), (thick / 2, width / 2),
                               (-thick / 2, width / 2))]
        rings_.append(quad)
    for i in range(sides):
        q0, q1 = rings_[i], rings_[(i + 1) % sides]
        for k in range(4):
            bm.faces.new((q0[k], q1[k], q1[(k + 1) % 4], q0[(k + 1) % 4]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = vb._new_mesh_object(name, bm)
    obj.location = center
    return _finish(obj, color, 0.0, studs, rot)


def torus(name, major, minor, center, color, sides=16, csides=6, rot=None, studs=True, arc=1.0):
    """Round tube bent into a circle / arc (stethoscope tubing, hoses, handles)."""
    bm = bmesh.new()
    n = sides if arc >= 1.0 else sides + 1
    loops = []
    for i in range(n):
        a = 2 * math.pi * arc * i / sides
        c, s = math.cos(a), math.sin(a)
        loop = []
        for j in range(csides):
            b = 2 * math.pi * j / csides
            rr = major + minor * math.cos(b)
            loop.append(bm.verts.new((rr * c, rr * s, minor * math.sin(b))))
        loops.append(loop)
    for i in range(n if arc >= 1.0 else n - 1):
        l0, l1 = loops[i], loops[(i + 1) % n]
        for j in range(csides):
            bm.faces.new((l0[j], l1[j], l1[(j + 1) % csides], l0[(j + 1) % csides]))
    if arc < 1.0:
        bm.faces.new(list(reversed(loops[0])))
        bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = vb._new_mesh_object(name, bm)
    obj.location = center
    return _finish(obj, color, 0.0, studs, rot)


def pipe(name, points, radius, color, csides=6, studs=True):
    """Round tube through a polyline of points (curved hoses / tubing)."""
    pts = [Vector(p) for p in points]
    bm = bmesh.new()
    loops = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        q = Vector((0, 0, 1)).rotation_difference(t)
        loop = []
        for j in range(csides):
            b = 2 * math.pi * j / csides
            loop.append(bm.verts.new(p + q @ Vector((math.cos(b) * radius, math.sin(b) * radius, 0))))
        loops.append(loop)
    for i in range(len(loops) - 1):
        for j in range(csides):
            bm.faces.new((loops[i][j], loops[i + 1][j], loops[i + 1][(j + 1) % csides], loops[i][(j + 1) % csides]))
    bm.faces.new(list(reversed(loops[0])))
    bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = vb._new_mesh_object(name, bm)
    return _finish(obj, color, 0.0, studs, None)


# ---------------------------------------------------------------------------------------------
# Joining / colour attribute
# ---------------------------------------------------------------------------------------------


def add_color_attribute(obj):
    """Per-corner colour from each face's material (fallback for importers that ignore materials)."""
    me = obj.data
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for poly in me.polygons:
        m = me.materials[poly.material_index] if me.materials else None
        col = tuple(m.diffuse_color) if m else (1, 1, 1, 1)
        for li in poly.loop_indices:
            attr.data[li].color = col


def join_into(name, objs, origin=(0, 0, 0)):
    """Join pieces into one mesh named `name`, world transform applied, object origin at `origin`."""
    objs = [o for o in objs if o.type == "MESH"]
    bpy.context.view_layer.update()
    if len(objs) == 1:
        obj = objs[0]
        obj.name = name
    else:
        obj = vb.join(name, objs)
    bpy.context.view_layer.update()
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    obj.data.transform(Matrix.Translation(-Vector(origin)))
    obj.location = origin
    obj.data.name = name
    add_color_attribute(obj)
    return obj


def tri_count(obj):
    me = obj.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


# ---------------------------------------------------------------------------------------------
# Rig: armature + rigid per-bone meshes
# ---------------------------------------------------------------------------------------------

BONE_LEN = 0.22  # bones all point +Y (roll 0): local axes == world axes at rest -> simple Motor6D CFrames


def build_rig(name, bones, parts, root_geo_size=(1.0, 2.6, 0.12)):
    """bones = [(bone, parent|None, head_xyz)], parts = {bone: [objects]}.
    Returns (armature_obj, {bone: mesh_obj})."""
    arm_data = bpy.data.armatures.new(f"{name}_Armature")
    arm = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    heads = {}
    for bname, parent, head in bones:
        eb = arm_data.edit_bones.new(bname)
        eb.head = Vector(head)
        eb.tail = Vector(head) + Vector((0, BONE_LEN, 0))
        eb.roll = 0.0
        eb.use_deform = True
        if parent:
            eb.parent = arm_data.edit_bones[parent]
            eb.use_connect = False
        heads[bname] = Vector(head)
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.show_in_front = True
    arm_data.display_type = "STICK"

    if "Root" in heads and not parts.get("Root"):
        rp = box("RootPart", root_geo_size, (0, 0, root_geo_size[2] / 2), "#FF00FF", r=0.0, studs=False)
        rp.data.materials[0] = _root_material()
        parts["Root"] = [rp]

    meshes = {}
    for bname, _parent, head in bones:
        objs = parts.get(bname) or []
        if not objs:
            continue
        m = join_into(f"{bname}_Geo", objs, origin=head)
        vg = m.vertex_groups.new(name=bname)
        vg.add(list(range(len(m.data.vertices))), 1.0, "REPLACE")
        mod = m.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
        m.parent = arm
        m["vault_bone"] = bname
        if bname == "Root":
            m.hide_render = True
            m["roblox_transparency"] = 1.0
        meshes[bname] = m
    arm["vault_rig"] = "motor6d_rigid"
    return arm, meshes


def _root_material():
    mat = bpy.data.materials.get("M_RootInvisible")
    if mat:
        return mat
    mat = vb.palette_material("RootInvisible", "#FF00FF")
    mat["roblox_transparency"] = 1.0
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Alpha"].default_value = 0.0
    return mat


def set_pose(arm, pose):
    """pose = {bone: (rx, ry, rz) degrees | {"rot": (..), "loc": (..)}} in bone-local (= world-at-rest) axes."""
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
    for b, v in (pose or {}).items():
        pb = arm.pose.bones[b]
        if isinstance(v, dict):
            pb.rotation_euler = _rot(v.get("rot", (0, 0, 0)))
            loc = v.get("loc", (0, 0, 0))
            # pose-bone location is in bone space: bone Y = world Y, bone Z = world -? -> map explicitly
            pb.location = _world_to_bone_loc(pb, loc)
        else:
            pb.rotation_euler = _rot(v)
    bpy.context.view_layer.update()


def _world_to_bone_loc(pb, loc):
    m = pb.bone.matrix_local.to_3x3().inverted()
    return m @ Vector(loc)


def world_bbox(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            w = ev.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        ev.to_mesh_clear()
    return lo, hi


def check_rig(arm, meshes, required_bones, max_total_tris):
    """Asserts bone names/hierarchy present and tri budget. Returns a report dict; raises on failure."""
    names = {b.name for b in arm.data.bones}
    missing = [b for b in required_bones if b not in names]
    extra = sorted(names - set(required_bones))
    per = {b: tri_count(m) for b, m in meshes.items()}
    total = sum(v for b, v in per.items() if b != "Root")
    errors = []
    if missing:
        errors.append(f"missing bones: {missing}")
    if extra:
        errors.append(f"unexpected bones: {extra}")
    if total > max_total_tris:
        errors.append(f"total tris {total} > {max_total_tris}")
    worst = max(per.values()) if per else 0
    if worst > MAX_TRIS_PER_MESH:
        errors.append(f"a part has {worst} tris > {MAX_TRIS_PER_MESH}")
    for b, m in meshes.items():
        groups = [g.name for g in m.vertex_groups]
        if groups != [b]:
            errors.append(f"{m.name} vertex groups {groups} != [{b}]")
    report = {"bones": len(names), "parts": len(meshes), "tris_total": total, "tris_max_part": worst,
              "tris_per_part": per, "errors": errors}
    if errors:
        raise AssertionError("; ".join(errors))
    return report


# ---------------------------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------------------------


def export_rig(arm, base_path):
    set_pose(arm, {})
    fbx = vb.export_fbx(base_path + ".fbx", [arm])
    vb._select_only([arm])
    bpy.ops.export_scene.gltf(filepath=base_path + ".glb", export_format="GLB", use_selection=True,
                              export_skins=True, export_animations=False)
    return fbx, base_path + ".glb"


# ---------------------------------------------------------------------------------------------
# Preview renders (bible §10 lighting)
# ---------------------------------------------------------------------------------------------


def setup_render(res=(1000, 800), samples=24, floor=True, floor_color="#8FD3C3"):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.film_transparent = False
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.33, 0.64, 1.0, 1)
    bg.inputs[1].default_value = 0.55
    if "PreviewSun" not in scene.objects:
        sun = bpy.data.objects.new("PreviewSun", bpy.data.lights.new("PreviewSun", "SUN"))
        sun.data.energy = 5.0
        sun.data.color = (1.0, 0.96, 0.9)
        sun.data.angle = 0.12
        sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(150))
        scene.collection.objects.link(sun)
        fill = bpy.data.objects.new("PreviewFill", bpy.data.lights.new("PreviewFill", "SUN"))
        fill.data.energy = 1.2
        fill.rotation_euler = (math.radians(60), math.radians(-10), math.radians(-30))
        scene.collection.objects.link(fill)
    if floor and "PreviewFloor" not in scene.objects:
        f = box("PreviewFloor", (60, 60, 0.2), (0, 0, -0.1), floor_color, r=0.0, studs=True)
        f.hide_select = True
    return scene


def shoot(path, location, target, lens=50, ortho=None):
    scene = bpy.context.scene
    cam = bpy.data.objects.get("PreviewCam")
    if cam is None:
        cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
        scene.collection.objects.link(cam)
    cam.data.lens = lens
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
    cam.location = location
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def orbit(target, dist, yaw_deg, pitch_deg):
    """Camera position around target; yaw 0 = in front (+Y) of the model."""
    y, p = math.radians(yaw_deg), math.radians(pitch_deg)
    t = Vector(target)
    return t + Vector((math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p))) * dist
