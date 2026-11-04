"""
Blender pipeline test. Runs every template headless, checks exports exist, enforces the mobile
triangle budget per exported mesh, and writes a manifest.

Run with either:
    python blender/tests/test_pipeline.py            (needs `pip install bpy==5.2.3`, Python 3.13)
    blender -b -P blender/tests/test_pipeline.py
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))

import bpy  # noqa: E402

import creature  # noqa: E402
import map_layout  # noqa: E402
import prop_kit  # noqa: E402
import scale_reference  # noqa: E402
import vault_blocky as vb  # noqa: E402

# qa/performance-budget.md — Roblox MeshPart hard limit is 20k tris; we keep headroom.
MAX_TRIS_PER_MESH = 15000
MIN_PARTS_CREATURE = 50  # BAD list: "few big plain boxes" (v1 had 18 and was rejected)
MIN_CREATURE_COLOURS = 5  # BAD list: "single flat colour"

failures = []


def check(cond, msg):
    if cond:
        print("  ok  ", msg)
    else:
        print("  FAIL", msg)
        failures.append(msg)


def main():
    out = tempfile.mkdtemp(prefix="vault_blender_")
    print("Blender", bpy.app.version_string, "->", out)
    manifest = []

    r = scale_reference.main(os.path.join(out, "ref"))
    check(os.path.getsize(r["fbx"]) > 0, "scale reference FBX exported")
    cube = bpy.data.objects.get("ScaleRef_4studs")
    check(cube is not None and abs(cube.dimensions.z - 4.0) < 1e-4, "scale cube is exactly 4 units tall")
    manifest.append(r)

    # Style gates (lessons L-20261104-03): checked on the built parts before joining.
    _, parts = creature.build()
    names = {p.name for p in parts}
    colours = {p.data.materials[0].name for p in parts if p.type == "MESH" and p.data.materials}
    head, body = bpy.data.objects["Head"], bpy.data.objects["Body"]
    check(len(parts) >= MIN_PARTS_CREATURE, f"creature has {len(parts)} parts (>= {MIN_PARTS_CREATURE})")
    check(len(colours) >= MIN_CREATURE_COLOURS, f"creature uses {len(colours)} colours (>= {MIN_CREATURE_COLOURS})")
    check(not any(p.get("vault_kind") == "studs" for p in parts), "creature has NO stud geometry")
    check(any(m.get("vault_studs") for m in bpy.data.materials), "creature uses texture studs")
    check({"Eye1", "Eye-1", "Pupil1", "Pupil-1", "Sparkle1", "Mouth"} <= names, "creature has a full face")
    check(head.dimensions.z >= body.dimensions.z * 1.4, "chibi proportions: head >= 1.4x body height")

    r = creature.main(os.path.join(out, "creature"))
    check(os.path.getsize(r["fbx"]) > 0 and os.path.getsize(r["glb"]) > 0, "creature FBX + GLB exported")
    check(r["tris"] <= MAX_TRIS_PER_MESH, f"creature tris {r['tris']} <= {MAX_TRIS_PER_MESH}")
    mats = {m.name for m in bpy.data.materials}
    check(any(bpy.data.materials[m].get("roblox_neon") for m in mats), "creature has a glow (neon) material")
    manifest.append(r)

    for r in prop_kit.main(os.path.join(out, "props")):
        check(os.path.getsize(r["fbx"]) > 0, f"prop {r['name']} exported")
        check(r["tris"] <= MAX_TRIS_PER_MESH, f"prop {r['name']} tris {r['tris']}")
        manifest.append(r)

    results = map_layout.main(os.path.join(out, "map"))
    check(len(results) == 3 + len(map_layout.LAYOUT["zones"]), "map exported one chunk per region")
    for r in results:
        check(r["tris"] <= MAX_TRIS_PER_MESH, f"map chunk {r['name']} tris {r['tris']}")
        manifest.append(r)
    check(os.path.exists(os.path.join(out, "map", "layout.json")), "map layout markers written")
    plaza = next(r for r in results if r["name"] == "Map_Plaza")
    plaza_obj = bpy.data.objects.get("Map_Plaza") or bpy.data.objects.get("Plaza")
    check(plaza_obj is not None and any(m.get("vault_studs") for m in plaza_obj.data.materials),
          f"plaza uses texture studs ({plaza['tris']} tris, no stud geometry)")

    # Style test collection gates (style-guides/3D_STYLE_BIBLE.md)
    import test_collection
    groups, _ = test_collection.build_all()  # _ = terrain + decorations
    all_objs = [o for objs in groups.values() for o in objs]
    check(not any(o.get("vault_kind") == "studs" for o in all_objs), "collection: no physical stud geometry")
    check(any(m.get("vault_studs") for m in bpy.data.materials), "collection: texture studs in use")
    check(abs(vb.STUD_PITCH - 0.5) < 1e-9, "stud spacing is the owner-approved 0.5 studs")
    solids = [o for objs in groups.values() for o in objs if "vault_sx" in o and not o.data.materials[0].get("roblox_neon")
              and "Glass" not in o.name and "Window" not in o.name and o.name != "Frappo_Body"]
    bad = [o.name for o in solids if o.get("vault_stud_mode") != "all"]
    check(not bad, f"collection: studs on all sides of every solid ({len(solids)} solids, missing: {bad[:5]})")
    check(len(groups["Building"]) >= 150, f"building detail parity ({len(groups['Building'])} pieces >= 150)")
    # Core standards (bible §0) — measurable parts
    world = _
    wn = [o.name for o in world]
    check(sum(n.startswith("TerraceCap") for n in wn) >= 4, "std5: stepped terrain terraces present")
    vign = {}
    for o in world:
        if o.name.startswith("Deco_"):
            vign.setdefault(o.name.split("_")[1], set()).add(o.name.split("_")[-1].rstrip("0123456789"))
    check(len(vign) >= 7, f"std7: purposeful vignettes ({len(vign)} >= 7)")
    check(all(len(v) >= 3 for v in vign.values()), "std7: every vignette mixes >= 3 different pieces")
    check(all(test_collection.path_dist(o.location[0], o.location[1]) >= 3.0 for o in world if o.name.startswith("Deco_")),
          "std7: decorations keep paths clear")
    check(sum("Leaf" in o.name for o in groups["Tree"]) >= 8, "std4: tree has >= 8 angular leaf clusters")
    bn = [o.name for o in groups["Brainrot"]]
    check(sum(n.startswith("Detail_") for n in bn) >= 12, "std6: >= 12 theme-appropriate creature details")
    check(not any(n.startswith(("Spike", "Scale")) for n in bn), "std6: no implausible spikes/scales on the frog")
    check(bpy.data.objects["EyeL"].dimensions.x >= 0.3 * 5.5, "std6: exaggerated eyes (>= 30% head width)")
    names = {o.name for o in groups["Brainrot"]}
    check({"EyeL", "EyeR", "PupilL", "PupilR", "Mouth"} <= names, "brainrot has a full face")
    body = bpy.data.objects["Frappo_Body"]
    check(body.get("vault_kind") == "voxel" and body["vault_voxels"] < 1500, "brainrot is merged blocks (<1500 cells)")
    for name, objs in groups.items():
        rep = vb.poly_report(objs)
        check(rep["tris"] <= MAX_TRIS_PER_MESH, f"collection {name} tris {rep['tris']} <= {MAX_TRIS_PER_MESH}")

    # Stud guard: oversize surfaces must fall back to a texture flag instead of exploding tris.
    vb.reset_scene()
    big = vb.block("Huge", (200, 200, 1), (0, 0, 0), "green")
    check(vb.studs(big) is None and big.get("vault_stud_texture") is True, "huge surface uses stud texture")

    vb.write_manifest(os.path.join(out, "manifest.json"), manifest)
    check(os.path.exists(os.path.join(out, "manifest.json")), "manifest written")

    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    code = main()
    if bpy.app.background and "--" not in sys.argv and not sys.argv[0].endswith(".py"):
        pass
    sys.exit(code)
