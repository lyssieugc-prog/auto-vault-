# My Vet Office! — Game Design Document

> Status: **v1 vertical-slice spec** · 2026-11-11 · Owner pitch: "Realistic Veterinary Simulator" +
> "Ultra-realistic interactivity & animal animation" (both briefs, in chat).
> Decisions Claude made without asking are marked *(inferred)* — override any of them.
> Everything visual is **pending owner approval**.

## 0. Brief
| Field | Value |
|---|---|
| Name | My Vet Office! |
| Pitch (owner) | "Someone enters My Vet Office! and immediately feels like they own a real veterinary clinic… The animals are the stars. Make them feel alive." |
| Genre | Simulation (procedural job sim) + light business management. Borrowed: `genres/tycoon.md` (progression/unlocks, *without* purchase pads), `genres/building-roleplay.md` (placement, roles, multiplayer). **Not** a click-tycoon. |
| Style profile | `style/profiles/realistic-building.md` + house studded-blocky language *(inferred — see §11 open question)* |
| Theme palette | Warm cream `#F6F1E9`, clinical teal `#177E80`, soft coral accent `#E8735E` (alerts/emergencies) — `figma/tokens.override.json` |
| Core loop | Customer arrives → check-in → call patient → help onto table → examine with real tools → diagnose → treat → invoice/payment → XP, reputation, cash → expand & decorate |
| Currency | Cash (server-only), XP → clinic level, Reputation (★ rolling average) |
| Hero creature | Golden Retriever (the showcase first patient) |
| Monetization | **None in v1.** Placeholders only after the owner approves (rule 5) |

## 1. Core gameplay & player experience
The player is the owner and only vet of a tiny, struggling office. The fantasy is *competence and
care*: reading a nervous animal, calming it, using instruments properly, working out what's wrong
from evidence, and seeing the animal visibly feel better.

Pillars (in priority order):
1. **Animals are alive.** Personality-driven minds (fear, trust, stress, pain, energy, curiosity,
   comfort, sociability) drive every animation and decision. No static models, no frozen patients.
2. **Every procedure is physical.** Open the cabinet, take the tool, put it on the right spot and
   hold it, look through the otoscope, clean until covered, wrap the bandage around the leg. No
   loading bars, no "hold E".
3. **Diagnosis is earned.** The owner describes symptoms; the game never tells you the answer.
4. **The business supports the vet work**, never replaces it: stock, deliveries you shelve, bills,
   staff who physically work, building and decorating your own clinic.
5. **"Just one more patient."** Each visit is 3–6 minutes, ends with a visible reunion + payment.

## 2. First 15 minutes
| Time | Beat | System |
|---|---|---|
| 0:00 | Spawn in your tiny clinic (reception, 3 waiting chairs, one exam room). Ambient clinic sounds, warm morning light. | World, startLayout |
| 0:06 | Front door chimes: **Maya walks in with Biscuit, a golden retriever** on a leash. He trots beside her, stops to sniff the doormat, looks around, tail wagging. | spawnPatient (forced showcase case), AnimalBehavior Follow/Sniff/LookAt |
| 0:30 | Tutorial: check them in at the reception computer. Maya: "Biscuit has this honking cough since we got back from the dog park." Chart opens with the complaint. | Appointment.checkIn, Tutorial "CheckIn" |
| 1:00 | Maya sits; Biscuit sits beside her, then lies down, yawns, licks his nose. | Settle + gestures |
| 1:20 | Walk to the waiting room and **call Biscuit**. He follows *you* now; hesitates half a second at the exam-room door (confident dog → short). | callPatient, Hesitate (fear-based) |
| 2:00 | **Help him onto the table**: big dog = front paws first, then support the back. He sits, looks around, pants, ears moving. Pet him — he leans into your hand. | helpOntoTable, PoseGraph, Comfort "Lean" |
| 2:40 | **Stethoscope**: open the equipment cabinet, take the stethoscope, place on the heart, hold → heartbeat audio + bpm readout; both lungs → *harsh* sounds. Biscuit turns his head toward it. | Procedures.Stethoscope |
| 3:40 | **Thermometer**: drawer → ask him to stand → hold → wait for the beep → **102.9 °F (fever)**. | Procedures.Thermometer |
| 4:30 | Vet computer: review chart (cough + harsh lungs + fever) → diagnose **Kennel cough**. | diagnose |
| 5:00 | Treatment: medicine cabinet → set the weight-based dose → give it. He visibly relaxes (pain/stress drop, tail wag rises). | Administer + Relief stimulus |
| 5:40 | Finish visit → he jumps down, **excited reunion** with Maya → invoice prints at reception → $95, ★★★★½, +40 XP. | pay, Excited |
| 6:00 | Tutorial: name your clinic on the sign. | rename (TextService filtered) |
| 6–9 | Second patient (random: beagle with ear infection / cat with ear mites / chihuahua…). | case pool |
| 9–12 | Supplies running low → order on the computer → **carry the delivery box** from the back door to the cabinet. | order/shelve |
| 12–15 | Place a plant or art print in the waiting room (build mode). ~Level 2 lands around patient 5–7. | placement |

## 3. Veterinary examination mechanics
All procedures are step machines in `src/shared/Procedures.luau`; the server validates every step.

| Step kind | Player does | Server checks |
|---|---|---|
| open | walk to the cabinet/drawer/fridge and click it | right target, player within 7 studs of that furniture in this room |
| take | pick the tool | right tool |
| approach | stand by the patient | server-measured distance |
| pose | ask for Stand / Sit / Lie (sternal/lateral) | patient settled in that pose (PoseGraph — animated, never teleported) |
| place | press & hold the instrument on the body | on the landmark (body-normalised coords), held for N seconds of *server* time; pull-away rolls |
| scan | magnified lens (otoscope, coat check): drag to pan, dwell to notice | coverage ≥ X per side; findings only if you dwelt on them |
| stroke | rub / clean / massage | grid coverage of the region; anti-teleport sample continuity; ≤32 samples per batch |
| wrap | circle around the paw | accumulated angle (capped per input) ≥ 3 turns |
| pull | slow upward drag (ticks) | speed limit — yanking resets |
| dose | slider | within tolerance of the weight-based target |
| wait | real timer (thermometer beep, fluids) | server clock |
| record | write findings | — |

Readings are physiological, not canned: heart rate = patient's true rate + stress × 35 bpm, so
calming first gives an accurate number (the chart warns "patient stressed, may read high").

v1 exams: Visual, Stethoscope, Thermometer, Otoscope, Coat & skin check, Belly palpation (L2).
Level 5+: Blood test, X-ray; level 10: Ultrasound (defined in Cases, procedures in milestone M3).

## 4. Animal AI & animation requirements
**Mind** (`AnimalMind.luau`): 8 attributes, breed baselines, condition modifiers, stimuli
(Pet, Comfort, Treat, Brush, LoudNoise, Bark, OwnerNear/Away, StrangerApproach, PickedUp,
Procedure, PainfulTouch, Relief, Reunite) whose effect depends on state (a terrified dog pulls away
from petting). Derived params feed animation: tail wag speed/height, ear pose, tremble, pant,
breath rate, blink interval, gait scale, limp, head height, purr, sleepiness, cooperation.

**Behaviour** (`AnimalBehavior.luau`), emergent from states + triggers: Follow (heel distance,
gait from distance), Sniff (curiosity × breed quirk), LookAt (sounds > animals/people > leader),
Settle (sit → lie when tired), Hesitate (fear-weighted, at thresholds), Hide (carrier / behind
owner), Table (requested pose, looks to owner when stressed), Carried, Excited (reunion), Sleep.
One-shot gestures from a species+breed weighted table.

**Poses** (`PoseGraph.luau` + `PoseLibrary.luau`): Stand, Sit, LieSternal, LieLateral, RollOver,
Crouch, Loaf, Curl, Carried — routed through intermediate poses with timed, eased cross-fades.

**Animation framework** (`AnimBlend.luau` + client `AnimalAnimator.luau`):
locomotion blend space (idle/walk/trot/run/sprint) with stride-synced phase (paws planted —
foot-slide is unit-tested to 0), 4-beat walk / diagonal trot / rotary gallop leg phases, limp on
the injured leg, additive breathing/panting/trembling/tail/ears/blinks/head look (critically
damped springs), two-bone foot IK + pelvis drop on uneven surfaces, gesture + reaction clips with
envelopes, distance LOD (full ≤40 studs @60 Hz with IK, mid @30 Hz, low @10 Hz, off) + budget
(4 full, 8 mid); the examined patient is always full.

**Performance:** one server loop at 5 Hz for every animal (100 animals < 20 ms per tick in tests),
one client loop for every animal; no per-animal scripts.

**Rigs:** shared quadruped skeleton (`Species.rigs.Quadruped`, 34 bones), Blender-authored, rigid
per-bone parts → Motor6Ds (`blender/handoff.md`). Breeds: Golden Retriever (hero), Beagle,
Chihuahua (L2, nervous), Domestic Shorthair cat. Quality over quantity (owner: "three
exceptionally animated dog breeds").

## 5. Diagnosis & treatment systems
- **Cases** (`Cases.luau`): Wellness, Otitis, Ear mites, Kennel cough, Paw-pad cut, Ticks,
  Gastroenteritis (L2). Each: species, complaints (≥2 phrasings, never naming the answer), mind
  modifiers, vital deltas, injury, per-exam findings, key exams, required treatments, pay, XP.
- **Vet computer:** patient record, complaint, every exam summary, treatment history (chart).
- **Diagnosis** from a list; correctness is revealed at checkout.
- **Consequences** (manageable): wrong → consultation at 40%, no fee for treatments that don't fit,
  lower stars/XP, and the **same pet returns** for a follow-up (35% of later arrivals).
  Unnecessary paid tests beyond one lower the rating; rough handling (pull-aways >2) too.
- **Treatments:** Vaccination, Clean ear, Ear drops, Anti-mite spot-on, Cough medicine, Clean
  wound, **Bandage (visible on the leg)**, Tick removal, Tick prevention, Tummy medicine + bland
  diet, Fluids. Supplies are consumed on completion.
- **Surgery** (L20, milestone M5): dedicated OR, prep → sterilise → tool tray → vitals monitor →
  sequenced procedural minigames (stylised, non-graphic) → recovery kennel.

## 6. Clinic building & customisation
- Grid placement (1 stud) per room with rotation, bounds, overlap, room-type and level checks;
  50% refund; can't remove the last exam table/reception counter. **No purchase pads.**
- Expansion rooms (Exam2 L3, Lab L5, Imaging L5, Kennels L8, Surgery L20) arrive as **empty
  shells** you furnish.
- Wall/floor finishes per room, clinic name (filtered), staff uniform colour, catalog of 26 items
  incl. medical furniture, decor, lighting. All models from Blender.

## 7. Economy & progression
| Lever | v1 value |
|---|---|
| Start cash | $250 + starter layout |
| Visit revenue | consultation $30–80 + paid exams + fitting treatments (~$60–150) |
| XP to level 2 | 250 (≈ 5–7 patients); curve `250·(L−1)^1.55` |
| Day | 12 real minutes; rent $40 + $15/room, utilities $15 + $5/room, wages |
| Debt | bills never game-over: shortfall becomes debt that blocks hiring/expansion |
| Reputation | rolling average of 20 ratings with a 3★ prior; faster arrivals at higher ★ |
| Arrivals | every 70 s at 3★ (min 25 s), cap 4 active + 0.15/level; emergencies from L4 (8%) |

Milestones: L1 Small Vet Office · L5 Established Clinic · L10 Advanced Practice · L20 Animal
Hospital · L35 Premium Hospital · L50 Veterinary Empire (`Config.milestones`).

Staff (physically do jobs, server AI in M4): Receptionist (L3), Janitor (L3), Assistant (L4),
Technician (L6), Veterinarian (L12).

## 8. UI/UX
Real-vet-software look, not simulator UI. Full spec: `figma/ui-spec.md` (HUD, VetComputer with
Patients / Chart / Diagnose / Treat / Inventory / Staff / Finance / Progress, ExamOverlay,
Magnifier, Invoice, BuildMode, Dialogue + phone variants). Contextual cameras: over-the-shoulder,
ear close-up, paw close-up; smooth, angular speed capped (never spins), always restored.
PC + mobile (touch gestures for every step kind, 44 px targets).

## 9. Technical architecture
```
ReplicatedStorage.GameShared   pure modules (tested under Lune)
  Species · AnimalMind · AnimalBehavior · PoseGraph · PoseLibrary · AnimBlend
  Cases · Procedures · Appointment · Clinic · Config · GameLogic
ServerScriptService.Game       Main (remotes via vault Net + Guard), World (plots, NPCs, sensing)
StarterPlayerScripts.Game      Main (UI binding), AnimalAnimator, Interaction (+ cameras)
vendor/vault                   DataService (session-locked saves), Guard, Net, Tutorial, Format …
```
- Server-authoritative: clients send ids/choices/pointer samples only; money, stock, XP,
  diagnoses, distances and timing are server-side. Hidden diagnosis never leaves the server
  (tested).
- Multiplayer: invites → roles (Owner / CoOwner / Vet / Technician / Receptionist / Assistant /
  Visitor) with a permission matrix; patients are claimed by one vet; released on leave.
- Persistence: vault DataService (session lock, retries, reconcile) with the clinic state in the
  profile; placement ids are strings (DataStore-safe).

## 10. Development milestones
| # | Milestone | State |
|---|---|---|
| M1 | Core systems + full appointment loop (pure, tested) | ✅ 88/88 Lune tests |
| M2 | Vertical slice in Studio: clinic shell + golden retriever + exam props imported, playtest the showcase appointment end-to-end | 🟡 code built; needs Studio + assets |
| M3 | Figma UI built + implemented; X-ray / blood test procedures with simulated images | ❌ |
| M4 | Staff AI (receptionist walk-through, technician escorts), emergencies & random events | ❌ (data ready) |
| M5 | Surgery room, recovery kennels, dental | ❌ |
| M6 | More species (rabbit, hamster, guinea pig, bird, reptile, ferret), multiple locations | ❌ |

## 11. Open questions for the owner
1. **Studs on a "realistic" clinic?** House rule says *everything* studded (incl. pets); this
   pitch says "polished, slightly stylized… not low-effort cartoon". Current plan: studded texture
   everywhere at 0.5 pitch, cleaner proportions. Say if you want fewer studs here.
2. UI departs from house-style §1–2 (no dark navy, no strokes, no sunbursts) per your "avoid
   generic simulator UI" — logged as a game exception in `lessons.md`. OK?
