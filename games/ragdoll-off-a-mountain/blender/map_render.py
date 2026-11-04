"""
Review renders for the Ragdoll Off a Mountain map (Cycles CPU, bible §10 lighting).

    python3 games/ragdoll-off-a-mountain/blender/map_render.py [samples] [shot_filter]
Outputs PNGs to games/ragdoll-off-a-mountain/assets/previews/map/.
Builds the map in-process (map.build + map.join_all) — no export.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import map as M  # noqa: E402

OUT = os.path.join(M.ROOT, "games", "ragdoll-off-a-mountain", "assets", "previews", "map")


def lighting(scene, samples):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.33, 0.64, 1.0, 1)
    bg.inputs[1].default_value = 1.0
    for name, energy, rot, col, ang in (("Sun", 5.0, (0.75, 0.15, 0.6), (1.0, 0.96, 0.9), 0.12),
                                        ("Fill", 1.2, (1.0, -0.3, 3.6), (0.75, 0.85, 1.0), 0.4)):
        if name not in scene.objects:
            light = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
            light.data.energy, light.data.color, light.data.angle = energy, col, ang
            light.rotation_euler = rot
            scene.collection.objects.link(light)


def preview_materials():
    """Preview-only looks: water/ice glossy + slightly transmissive (Roblox: Transparency in Studio)."""
    for mat in bpy.data.materials:
        hexc = mat.get("roblox_color", "")
        bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.use_nodes else None
        if not bsdf:
            continue
        if hexc in (M.WATER, M.WATER_D):
            bsdf.inputs["Roughness"].default_value = 0.12
        if hexc in (M.ICE_GLASS, M.ICE):
            bsdf.inputs["Roughness"].default_value = 0.2


def camera(scene):
    cam = bpy.data.objects.get("ReviewCam")
    if not cam:
        cam = bpy.data.objects.new("ReviewCam", bpy.data.cameras.new("ReviewCam"))
        scene.collection.objects.link(cam)
    cam.data.clip_start = 0.5
    cam.data.clip_end = 6000
    scene.camera = cam
    return cam


def shoot(scene, cam, name, loc, target, lens):
    cam.location = loc
    cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", scene.render.filepath, flush=True)


def shots():
    P = {pk["n"]: pk for pk in M.PEAKS}
    s = {
        "01_establishing_SE": ((620, -560, 360), (-10, 330, 230), 20),
        "02_valley_hub": ((150, -250, 95), (0, -70, 0), 30),
        "03_landing_zone": ((30, -60, 45), (0, 75, 8), 24),
        "04_base_rim": ((70, -120, 48), (0, -210, 3), 26),
    }
    for n, pk in P.items():
        px, yl, pz = pk["x"], pk["ylast"], pk["z"]
        s[f"1{n}_peak{n}_pad"] = ((px + 46, yl - 52, pz + 26), (px, yl + 14, pz + 2), 26)
        s[f"2{n}_peak{n}_face"] = ((px + 70 + pz * 0.25, yl - 160 - pz * 0.45, pz * 0.55 + 20), (px, (yl + 100) / 2, pz * 0.45), 24)
    return s


def main(samples=32, only=None):
    os.makedirs(OUT, exist_ok=True)
    M.build()
    M.join_all()
    scene = bpy.context.scene
    lighting(scene, samples)
    preview_materials()
    cam = camera(scene)
    for name, (loc, tgt, lens) in shots().items():
        if only and not any(o in name for o in only.split(",")):
            continue
        shoot(scene, cam, name, loc, tgt, lens)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(int(argv[0]) if argv else 32, argv[1] if len(argv) > 1 else None)
