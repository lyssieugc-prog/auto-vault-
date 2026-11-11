"""
Quick asset gate for My Vet Office (run with a bpy-enabled Python, repo root):
    python games/my-vet-office/blender/test_assets.py

Checks (numbers only — looks are judged from the renders by eye and by the owner):
  * Golden Retriever: every required bone exists with the exact name + required parent, one rigid
    `<Bone>_Geo` mesh per bone weighted 100 % to that bone, tri budget, paws flat on the ground at rest,
    Sit/Lie poses keep the dog on (not through) the floor, no stud geometry, stud texture in use.
  * Exam-room props: per-mesh tri budgets, stud texture in use, door pivot on the hinge.
  * Exports exist and are non-empty.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import exam_room_props as props  # noqa: E402
import golden_retriever as gr  # noqa: E402
import vet_common as vc  # noqa: E402

EXPECTED_PARENTS = {
    "Root": None, "Pelvis": "Root", "SpineLow": "Pelvis", "SpineMid": "SpineLow", "Chest": "SpineMid",
    "Neck": "Chest", "Head": "Neck", "Jaw": "Head", "EarL": "Head", "EarR": "Head", "LidL": "Head", "LidR": "Head",
    "EyeL": "Head", "EyeR": "Head", "Tail1": "Pelvis", "Tail2": "Tail1", "Tail3": "Tail2", "Tail4": "Tail3",
    "ShoulderL": "Chest", "ElbowL": "ShoulderL", "WristL": "ElbowL", "PawFL": "WristL",
    "ShoulderR": "Chest", "ElbowR": "ShoulderR", "WristR": "ElbowR", "PawFR": "WristR",
    "HipL": "Pelvis", "KneeL": "HipL", "HockL": "KneeL", "PawBL": "HockL",
    "HipR": "Pelvis", "KneeR": "HipR", "HockR": "KneeR", "PawBR": "HockR",
}

failures = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def test_dog():
    arm, meshes, n = gr.build()
    rep = gr.check(arm, meshes)  # raises on bone/tri/paw/pose failures
    bones = arm.data.bones
    for b, parent in EXPECTED_PARENTS.items():
        check(b in bones, f"bone {b} exists")
        if b in bones:
            got = bones[b].parent.name if bones[b].parent else None
            check(got == parent, f"bone {b} parent {got} == {parent}")
    check(set(bones.keys()) == set(EXPECTED_PARENTS), "no extra/missing bones")
    check(len(meshes) == len(EXPECTED_PARENTS), f"{len(meshes)} rigid parts (one per bone)")
    check(rep["tris_total"] <= gr.MAX_TRIS, f"dog tris {rep['tris_total']} <= {gr.MAX_TRIS}")
    check(rep["tris_max_part"] <= vc.MAX_TRIS_PER_MESH, f"largest part {rep['tris_max_part']} <= 15k")
    check(n >= 150, f"{n} pieces before join (>= 150)")
    check(3.0 <= rep["head_top"] <= 3.5, f"head top {rep['head_top']} studs (~3.2)")
    check(any(m.get("vault_studs") for m in bpy.data.materials), "stud texture in use")
    check(not any(o.get("vault_kind") == "studs" for o in bpy.data.objects), "no stud geometry")
    for name in gr.POSES:
        check(rep[f"pose_{name}_min_z"] > -0.08, f"pose {name} stays on the floor ({rep[f'pose_{name}_min_z']})")


def test_props():
    for name in props.PROPS:
        vc.vb.reset_scene()
        obj, n = props.build_one(name)
        rep = props.check({name: (obj, n)})[name]
        check(rep["tris"] <= props.MAX_TRIS[name], f"{name} tris {rep['tris']} <= {props.MAX_TRIS[name]}")
        if name == "CabinetDoor":
            check(tuple(round(v, 3) for v in obj.location) == tuple(round(v, 3) for v in props.HINGE),
                  "cabinet door origin is the hinge axis")


def test_exports():
    files = ["golden_retriever"] + list(props.FILES.values())
    for f in files:
        for ext in ("fbx", "glb"):
            p = os.path.join(vc.EXPORT_DIR, f"{f}.{ext}")
            check(os.path.exists(p) and os.path.getsize(p) > 1000, f"export {f}.{ext}")


if __name__ == "__main__":
    test_dog()
    test_props()
    test_exports()
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1 if failures else 0)
