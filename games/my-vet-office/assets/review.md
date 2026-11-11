# My Vet Office — Asset Review (bible §13)

All assets below are **PENDING owner approval**. Renders: `assets/previews/`. Every render listed was opened and
looked at; numbers alone were never used to call anything done. Nothing has been imported into Studio yet.

---

## Golden Retriever (rigged hero patient) — `blender/golden_retriever.py`

**"Does this look like a professionally designed Roblox simulator asset, or a generic procedural block model?"**
Honest answer: **closer to a pro simulator pet than a generic block model, but not yet at the bar of a shipped
top-simulator hero pet.** The face (big brown eyes with two sparkles, separate lids, brows, cream muzzle, glossy nose,
hanging tongue) and the collar + glowing vet tag read as designed and appealing from the front and 3/4. The side
view is still the weakest angle: the torso reads as a long rounded bar with stud domes, and the coat breakup there is
mostly the darker back saddle.

| §13 check | Verdict |
|---|---|
| Silhouette | PASS: domed head, hanging ears, deep chest, angled hind legs, plumed upward tail; reads "golden retriever" |
| Layers | PASS: body mass → saddle / ruff / feathering → toes, claws, collar hardware, face pieces |
| Colour | PASS: coat in 4 shades, cream in 2, red collar accent, cyan neon tag; ≥ 5 colours |
| Surface | PASS (by rule): 0.5-stud texture on every non-face piece; no stud geometry |
| Proportion | PARTIAL (deliberate): enlarged head and eyes, chunky legs, but dog anatomy not chibi. Deviation from house §4 "head ≥ 1.4× body" flagged for the owner |
| Plausibility | PASS: only dog-appropriate detail (feathering, ruff, toes, claws, brows, flews, collar, tag) |
| Handcrafted | PARTIAL: tufts vary in size/angle/tone, but the leg feathering still repeats a similar wedge shape |
| Originality | PASS: built for this game; nothing reused from the calibration sample |

### Iterations (each one rendered and looked at)
1. v1: pale, washed-out lighting; the ear tops stuck up like **antennae** (BAD list); "+"-shaped nose; square eye
   sockets looked like goggles; thin stick legs; spiky white feathering; plank-like back plates.
2. Found the root cause of the crosses and spikes: bmesh's default bevel profile makes multi-segment bevels concave, so
   rounded boxes rendered as cross / T shapes. Fixed in `vet_common.box` (`profile=0.5`, `clamp_overlap`).
   **The same bug is in `blender/lib/vault_blocky.block()` / `rounded()` for segments ≥ 2 — not changed (outside this
   game); the lead should decide whether to fix the shared lib**, because it changes the look of existing pending assets.
3. Rebuilt the ears to hang from the skull side; one chunky nose; removed the sockets; thicker legs; mid-tone clinic
   floor and lower sky strength in the preview lighting.
4. Torso read as a caterpillar / armadillo (bevel bands at every segment) → torso masses now bevel only along their length
   and butt into one continuous body, with rounded end caps and a 4-piece butting back saddle.
5. Tongue now hangs over the lip; flat armour-like shoulder / thigh / flank plates replaced by rounded muscle masses;
   cream britches (the rear looked like a diaper square) split into two tufts plus a rump patch; chest ruff reduced to
   7 bigger overlapping tufts (it read as shingles / scales).
6. Poses: Lie had the forelegs swinging backwards (sign error) → recomputed the angles (sphinx forelegs, folded hocks).
   Pelvis drops tuned so Sit and Lie rest on the floor (script asserts min z > −0.08).

### Remaining weaknesses (honest)
- Side view: the body is long and boxy; it needs a stronger tuck-up (belly rising to the loin) and some darker coat
  waves or feather layers on the flank.
- The stud texture shows as large domes on rounded masses (0.5 pitch on a 1.2-stud-wide body = about 2 studs across).
  That is per the owner rule, but on a small pet it is busy. The owner should confirm this is wanted on pets.
- Leg feathering wedges are similar to each other; the tail plume could be fuller / wavier.
- Back view is acceptable but plainer than the front.
- Rig is untested in Studio: Motor6D conversion, colours per material, and import scale are unverified (see `blender/handoff.md`).

## Exam-room props — `blender/exam_room_props.py`

**Exam table.** Pro or generic? **Pro-leaning.** Stainless top with a rolled rim, rubber mat with ribs and paw-print
inlays, teal apron with a coral band, built-in pet scale with a neon readout, a drawer, coral rubber corner bumpers,
end handles, a telescoping chrome ram in rubber bellows, a pump housing with a coral foot pedal, levelling feet. The
back got a towel bar with a draped coral towel and a clinic label plate (the back was blank in pass 1).
Weakness: the column looks slightly thin under the 6-stud top, and the table is low-contrast teal/steel apart from coral.

**Equipment cabinet + door.** Pro or generic? **Pro-leaning.** Cornice with a coral lip, red-cross sign, 3 stocked
shelves (labelled bottles with caps, glove box with glove tuft, cotton jar, gauze boxes, rolls, spray bottle), 2 drawers
with pulls and tags. The door is a separate mesh with the hinge as its origin: frame, mullion, glass, handle, lock,
hinge knuckles and a paw sticker. Rendered closed and open (105°), and the hinge swings outward correctly.
Fix made: dark seams at the top corners capped. Weakness: interior back panel reads grey through the glass;
cabinet sides are plain teal (only studs).

**Stethoscope / otoscope / thermometer / bandage roll.** Pro or generic? **Readable and on-theme, simpler than the
big props** (correct per bible §3b: detail on par, not more). Fixes made: stethoscope chest piece was sinking into the
tray (placement); bandage "wrap steps" read as random tabs → replaced by one loose-end flap; otoscope shown in profile.
Weakness: stethoscope tubing is a coarse 8-sided pipe; thermometer and bandage backs are plain.

**In context** (`exam_room_context.png`): the golden sits on the table with the tools on the mat and the open cabinet
behind. Scale and palette read as a vet clinic.

## Not done
- Chihuahua and Domestic Shorthair cat (optional): **skipped** rather than done badly. `vet_common.build_rig` +
  the bone table make them a parameter/proportion job, not a rewrite.
