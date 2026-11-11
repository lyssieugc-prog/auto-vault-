# My Vet Office! — Studio playtest plan (not yet run)

Follows `qa/playtest.md`. Server + 1 client, then Server + 2 clients for multiplayer.
Record results in `qa/playtest-<date>.md`. Nothing here has been run yet.

## A. Showcase appointment (golden retriever)
| # | Do | Expect |
|---|---|---|
| 1 | Join | Plot claimed, starter furniture placed from Blender models, no warnings about missing assets |
| 2 | Wait ≤10 s | Customer + golden retriever walk in via pathfinding; dog walks at heel, paws don't slide, sniffs, tail wags |
| 3 | Check in at reception computer | Customer sits; dog sits/lies beside, gestures (yawn, lick nose) |
| 4 | Call to Exam1 | Dog follows *you*, brief hesitation at the door |
| 5 | Front paws → back | Smooth lift onto the table (no teleport), sits, breathes, pants, ears move, blinks |
| 6 | Pet | Dog leans in, eyes half-close |
| 7 | Stethoscope steps | Cabinet door opens, tool in hand, hold on heart/lungs; reading + "Harsh" lungs; dog turns head |
| 8 | Thermometer | Dog stands up through the pose graph; beep after 5 s; FEVER |
| 9 | Diagnose kennel cough, give cough medicine with the right dose | Relief: tail wag up, panting down |
| 10 | Finish + print invoice | Dog jumps down, excited reunion, $95 ★4.5, +40 XP, leaves together |
| 11 | Rejoin (DataStore "real" in a private place) | Cash/XP/layout/tutorial persist |

## B. Behaviour variety
Chihuahua (L2): trembles, hesitates long, pulls away until comforted/treat. Cat: stays in the
carrier until opened + calm; crouches; hisses if scared; purrs when comfortable. Paw cut: limps,
bandage appears on the front-left leg.

## C. Multiplayer + security
Friend invited → Visitor can't treat/build; set Vet → can call other patients, can't take yours.
Exploit probes: fire `Procedure` with NaN/huge payloads, `Place` off-grid, `Order` qty 1e9,
`PrintInvoice` from across the map → all rejected, no state change.

## D. Performance
6 plots × 4 patients: server Heartbeat < 2 ms for animals; client 60 fps on a mid phone with LOD.
