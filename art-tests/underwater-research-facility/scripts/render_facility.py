"""
Renders for the Underwater Research Facility test (Cycles CPU, headless-safe).
    python art-tests/underwater-research-facility/scripts/render_facility.py [samples] [only_shot]
Outputs to art-tests/underwater-research-facility/renders/.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path[:0] = [HERE, os.path.join(ROOT, "blender", "lib")]

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import build_facility as bf  # noqa: E402
import uw_kit as uw  # noqa: E402
import vault_blocky as vb  # noqa: E402

OUT = os.path.join(HERE, "..", "renders")

SHOTS = {  # name: (camera, target, lens)
    "01_full_environment": ((98, 112, 70), (0, 2, 2), 28),
    "02_research_hub": ((30, 26, 21), (0, -14, 11), 30),
    "03_lab_windows": ((42, 17, 7.5), (40, -14, 4.5), 30),
    "04_aquarium_dome": ((10, 70, 16), (-8, 30, 9), 30),
    "05_bubblemunch_closeup": ((-2, 54, 13), (-8, 31, 10.0), 34),
    "06_submarine_dock": ((92, 62, 15), (62, 33, 6), 30),
    "07_ruins_dig_site": ((-24, 76, 22), (-55, 40, 6), 30),
    "08_coral_reef": ((36, 74, 6.5), (26, 54, 2.5), 34),
    "09_tunnels_and_pod": ((-16, 14, 14), (-30, -15, 6), 30),
    "12_submarine_closeup": ((76, 52, 10), (62, 35, 6), 34),
    "13_trench_bridge": ((44, 78, 10), (32, 56, -2), 32),
}


def lighting(scene, samples):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    try:
        scene.cycles.use_denoising = True
    except Exception:
        pass
    scene.cycles.max_bounces = 6
    scene.cycles.transmission_bounces = 6
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.05, 0.33, 0.58, 1)  # lagoon blue; lower ambient = more contrast
    bg.inputs[1].default_value = 0.75
    if "UWHaze" not in scene.objects:  # bounded underwater haze (a world volume would swallow the sun)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(6, 5, 30))
        haze = bpy.context.active_object
        haze.name = "UWHaze"
        haze.scale = (200, 160, 60)
        mat = bpy.data.materials.new("M_UWHaze")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        vol = nt.nodes.new("ShaderNodeVolumeScatter")
        vol.inputs["Color"].default_value = (0.55, 0.88, 1.0, 1)
        vol.inputs["Density"].default_value = 0.0012
        vol.inputs["Anisotropy"].default_value = 0.3
        nt.links.new(vol.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
        haze.data.materials.append(mat)
    for name, energy, rot, col, ang in (("SunTop", 5.2, (0.5, 0.2, 0.75), (1.0, 0.98, 0.92), 0.12),
                                        ("Fill", 1.1, (1.1, -0.4, 3.7), (0.6, 0.85, 1.0), 0.3)):
        if name not in scene.objects:
            light = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
            light.data.energy, light.data.color, light.data.angle = energy, col, ang
            light.rotation_euler = rot
            scene.collection.objects.link(light)


def shoot(scene, cam, name, loc, target, lens):
    cam.location = loc
    cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.abspath(os.path.join(OUT, f"{name}.png"))
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath


def camera(scene):
    cam = bpy.data.objects.get("ReviewCam")
    if not cam:
        cam = bpy.data.objects.new("ReviewCam", bpy.data.cameras.new("ReviewCam"))
        scene.collection.objects.link(cam)
    cam.data.clip_end = 2000
    scene.camera = cam
    return cam


def material_preview(samples):
    """Swatch board: every facility material studded (normal map) vs smooth glass/water/glow."""
    vb.reset_scene()
    uw.install()
    scene = bpy.context.scene
    lighting(scene, samples)
    sw = [("Yellow hull", bf.YEL), ("Lagoon teal", bf.TEAL), ("Deep navy", bf.NAVY), ("Coral", bf.CORAL),
          ("Seabed sand", bf.SAND), ("Slate rock", bf.ROCK), ("Ruin stone", "#9FB3B0"), ("Steel", bf.STEEL)]
    for i, (_, col) in enumerate(sw):
        x = -10.5 + (i % 4) * 7
        y = 4 if i < 4 else -3
        vb.rounded(f"Swatch{i}", (5, 5, 2.4), (x, y, 0), col, radius=0.25)
        vb.rounded(f"SwatchStep{i}", (2.6, 2.6, 1.2), (x + 0.8, y + 0.8, 2.4), col, radius=0.15)
    uw.glass(vb.ball("GlassSample", (2.2, 2.2, 2.2), (-6, -10, 2.2), "#CFF7FF", segments=24, rings=12, studs="none"))
    vb.solid("WaterSample", (6, 4, 0.4), (2, -10, 0), "#3EC6FF", studs="none", bevel=0.02)
    vb.ball("GlowSample", (1.2, 1.2, 1.2), (9, -10, 1.4), "#7CF7FF", segments=16, rings=8, emission=5)
    vb.solid("PreviewFloor", (60, 60, 1), (0, 0, -1), bf.SAND, bevel=0.0)
    cam = camera(scene)
    out = [shoot(scene, cam, "10_material_board", (0, 26, 20), (0, -1, 0.5), 32),
           shoot(scene, cam, "11_stud_macro", (-7.0, 9.6, 4.6), (-9.5, 4.5, 2.2), 55)]
    return out


def main(samples=20, only=None):
    os.makedirs(OUT, exist_ok=True)
    bf.build_all()
    scene = bpy.context.scene
    lighting(scene, samples)
    cam = camera(scene)
    out = []
    for name, (loc, tgt, lens) in SHOTS.items():
        if only and only not in name:
            continue
        out.append(shoot(scene, cam, name, loc, tgt, lens))
    if not only or "material" in only or "stud" in only:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(HERE, "..", "underwater_facility.blend")))
        out += material_preview(samples)
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    print(main(int(argv[0]) if argv else 20, argv[1] if len(argv) > 1 else None))
