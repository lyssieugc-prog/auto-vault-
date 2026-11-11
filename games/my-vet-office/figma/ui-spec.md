# My Vet Office! — UI spec

> **STATUS: UI IS BLOCKED ON FIGMA.** No Figma file exists for this game yet. The Figma MCP
> server announced itself in the designer session (2026-11-11), but its tools (`create_new_file`,
> `create_session`, `use_figma`, `get_screenshot`) could not be called from that session, so
> **no frames were created, no screenshots were taken, and no frame was checked by eye.** This
> document is the full build brief: once Figma tools are callable, build the file from it, screenshot every
> frame, and fill in `figma.json`. Everything here is **PENDING owner approval**.

Tokens: `figma/tokens.json` (house) + `games/my-vet-office/figma/tokens.override.json` (this game).
Mapping rules: `figma/roblox-mapping.md`. Sample data comes from the game's real data
(`src/shared/Config.luau`, `Cases.luau`, `Procedures.luau`, `Species.luau`,
`GameLogic:snapshot()`, `Appointment.snapshot()`).

---

## 0. Design direction (and where it departs from the house style)

Owner's direction for this game (verbatim): *"Avoid generic Roblox simulator UI with enormous
colorful buttons everywhere. Interfaces should resemble simplified real veterinary software while
remaining easy for younger players to understand."*

The look is a friendly practice-management app: warm cream/white panels, a teal clinical accent,
soft coral only for alerts and emergencies, dark readable text, calm motion. To stay easy for
younger players: big plain-language labels, one primary action per screen, icons next to every
label, colour never used alone (every badge has a word).

**House-style rules waived for this game** (owner direction overrides house-style §1–2; the lead
should log this as a game exception in `games/my-vet-office/lessons.md`. The designer could only
write files under `figma/`):

| House rule (§1–2, components.md) | My Vet Office! |
|---|---|
| Dark navy panel `#1E1B33` | Warm white panel `#FFFDF9` on cream canvas `#F6F1E9`. The realistic-profile `#2A2F3A` is used only for the computer-monitor bezel. |
| Thick saturated title bar, icon tilted −8° breaking the corner | Teal title bar (64 px at 1080p) with a 6 % paw-print pattern. The round icon badge breaks the top-left corner by 12 px with **no tilt**. |
| White text, 2–4 px dark stroke + drop shadow | Dark text on light surfaces and white text on teal. **No text strokes** or shadow copies. |
| Fredoka One everywhere | Nunito (ExtraBold/Bold/SemiBold) plus Roboto Mono for numbers, vitals and money. |
| Cards: saturated block + sunburst + stud texture + glossy render | White cards with 1 px `line` stroke and a soft shadow. Renders sit on a pale tinted tile. No sunburst and no studs in the UI. |
| Lime pill buy buttons with gloss + 5 px lip | Teal primary buttons with a 3 px darker lip and no gloss. No Robux buttons (v1 has no products). |
| Rotated Tags (New!, MYTHIC!…) | Flat status badges (EMERGENCY, FOLLOW-UP, ROUTINE, LOW STOCK, Lv 5). They are not rotated. |
| Back.Out pop from 0.2 scale, hover tilt −2° | Calm open: 0.96 → 1 scale + fade, 0.22 s Quad.Out. Hover 1.02, no tilt. Press 0.97. See §0.4. |
| Shop / Eggs / Daily / Index / Season Pass screens | Not designed: v1 has no monetization, and the contract asks for the clinic screens listed below. |

### 0.1 Theme decor (the "frame decor / title bar / close X / open animation" reskin)
- **Title bar pattern:** tiled paw prints in white at 6 % opacity (ImageLabel `Pattern`, ScaleType
  Tile). The VetComputer title bar also has a thin white **ECG heartbeat line** (`EcgLine`) that
  sweeps once across the bar when the window opens.
- **Themed close X:** `Close` is a 44×44 rounded square (radius 10) in `coralDark` `#C2493A`,
  styled like a sticking plaster: a lighter `#E8735E` centre pad with three tiny dot perforations
  and a white 3 px X. The hit area is always ≥ 44 px, even when the visual is smaller (phone).
- **Frame decor (subtle, at most 2 per window):**
  - VetComputer: the window is drawn as a **monitor**. It has a 14 px bezel `Bezel` in `#2A2F3A`
    with a teal power LED `PowerLed` bottom-centre, a yellow **sticky note** `StickyNote` on the
    top-right bezel corner (rotated 4°, handwritten-style Nunito "Order more cough syrup!"), and a
    small round **paw magnet** `PawMagnet` holding it.
  - Invoice: a **clipboard clip** `Clip` on the top edge and a zig-zag torn bottom edge `TornEdge`.
  - Dialogue: the speech-bubble tail `Tail` points at the customer.
  - Magnifier: the lens rim `Rim` looks like an otoscope head (dark grey ring with a teal cap tab).
- **Level chip** in the HUD is shaped like a **collar tag** (rounded hexagon).

### 0.2 Colour + contrast (WCAG estimates on `#FFFDF9`)
| Use | Colour | Contrast |
|---|---|---|
| Primary text | `#1F2A30` | ≈ 14:1 |
| Muted text (labels, meta) | `#5B6670` | ≈ 5.9:1 |
| Teal (buttons, active tab, links) / white text on teal | `#177E80` | ≈ 4.9:1 |
| Emergency / danger fill with white text | `#C2493A` | ≈ 4.9:1 |
| Coral `#E8735E` | decoration, meter ends, toast edge strip only. **Never** used behind text. | 3.0:1 |
| Follow-up badge: text `#8A5A0B` on `#FCEFD6` | | ≈ 5.6:1 |
| Success: `#2C7445` on `#DDF0E2` | | ≈ 5.3:1 |
| Stars `#F2B33D` | always paired with the number, e.g. "4.2" | decorative |

### 0.3 Type scale
| Token | 1920×1080 | Phone 844×390 | Font |
|---|---|---|---|
| display | 40 | — | Nunito ExtraBold |
| h1 (window title) | 32 → shown at 28 in title bars | 20 | Nunito ExtraBold |
| h2 (section) | 24 | 17 | Nunito Bold |
| body | 20 | 15 | Nunito SemiBold |
| small (meta, badges) | 16 | 14 | Nunito Bold |
| numbers / money / vitals | 20–48 | 15–28 | Roboto Mono |

No text may be smaller than 16 px at 1080p or 14 px on the phone. In Roblox, every TextLabel uses
TextScaled + `UITextSizeConstraint` with MaxTextSize = the token size and MinTextSize = 14.

### 0.4 Motion (tag each instance with Attribute `Motion`, per roblox-mapping.md)
| Motion id | What | Implementation note |
|---|---|---|
| `clinic.open` | UIScale 0.96 → 1 and CanvasGroup GroupTransparency 1 → 0, 0.22 s Quad.Out | `UIAnim.popOpen` starts at 0.2 scale with Back overshoot, which is too bouncy for this look. It needs a game-local helper (or a `fromScale`/easing option on popOpen); the lead or systems decide. |
| `clinic.monitorWake` | VetComputer: bezel `clinic.open`; the `Screen` fades from `#1F2A30` to content in 0.2 s; `EcgLine` sweeps left → right in 0.6 s, once | |
| `clinic.close` | scale 1 → 0.97 + fade, 0.15 s Quad.In | `UIAnim.close` (0.18 s Back.In) is acceptable as a fallback |
| `clinic.toastIn` | slide from +40 px right + fade, 0.25 s Quad.Out. Auto-dismiss after 6 s (emergencies stay until handled) | |
| `clinic.emergencyPulse` | `UIAnim.pulse(toast, 0.03)` for 3 s, then stop | |
| `clinic.printOut` | Invoice slides up from below (y +40 %) in 0.45 s Quad.Out, lines fade in top→bottom with a 0.04 s stagger, then stars fill one by one (0.12 s each) | Prefer fades over `UIAnim.stagger` (its Back pop from 0 is too bouncy) |
| `clinic.typeIn` | Dialogue `Text` types at 40 chars/s; tap to skip | |
| `clinic.iris` | Magnifier `Lens` grows from 0 → 1, 0.25 s Quad.Out | |
| `clinic.sheet` | BuildMode toolbar slides down and catalog slides up, 0.25 s Quad.Out | |
| `clinic.numberPop` | "+$95", "+40 XP" over `Cash` / `XpBar` | `UIAnim.numberPop` uses FredokaOne + gold with a stroke. Request a colour/font option or a local variant (teal `+$95` in Roboto Mono) |
| buttons | hover 1.02 (no tilt), press 0.97, 0.12 s | `UIAnim.bindButton` hard-codes 1.05 + −2° tilt; same request as above |

### 0.5 Safe areas + touch
- Every ScreenGui: `ResetOnSpawn=false`, `ZIndexBehavior=Sibling`, `ScreenInsets=DeviceSafeInsets`,
  `IgnoreGuiInset=false`.
- The top 72 px at 1080p (58 px Roblox topbar + gap) stays clear on the left 320 px (Roblox menu
  and chat buttons).
- Phone reserves: **bottom-left 40 % × 55 %** for the thumbstick and a **bottom-right 150×150 px**
  zone for the jump button. HUD buttons stay outside both zones.
- Every button is ≥ 44×44 px at the phone size (`MobileUI.enforceTouchTarget`). Visual size may
  be smaller only when an invisible `HitArea` child extends it.

---

## 1. Component library (Figma page "Components")

Build as Figma components/variants. The Roblox instance name equals the layer name.

| Component | Variants | Anatomy (layer names) | Roblox |
|---|---|---|---|
| `Window` | size = L (1440×860) / M (960×680) / S (560×420) | `Shadow`, `Body` (panel, radius 16, 1 px `line`), `TitleBar` (teal, 64 px, `Pattern`, `TitleIcon` 56 px circle badge, `Title`), `Close`, `Content` | Frame + UICorner + UIStroke; CanvasGroup root for fades |
| `Button` | kind = Primary / Secondary / Danger / Ghost; size = L 56 / M 48 / S 44; state = Default / Hover / Pressed / Disabled | `Lip` (3 px, darker), `Face`, `Icon` (24 px), `Label` | TextButton (Face) + Frame lip + UIAnim-style bind |
| `Badge` | Emergency (coralDark/white), FollowUp (amberSoft/amberText), Routine (tealSoft/tealDark), Waiting (panelAlt/muted), Done (greenSoft/greenText), Low (coralSoft/coralDark), Locked (lockedFill/lockedText + lock icon) | `Icon?`, `Label` (small, caps) | Frame + UICorner pill |
| `Tab` | state = Active (teal fill, white) / Inactive (transparent, muted) / Hover; alert = on/off | `Icon`, `Label`, `AlertDot` (10 px coralDark) | TextButton |
| `Toast` | Emergency / Arrival / Impatient / Info / Success | `Strip` (6 px left edge colour), `Icon`, `Title`, `Body`, `Action` (Ghost S), `Dismiss` | Frame in UIListLayout |
| `StatChip` | default / warning | `Icon`, `Value` (mono), `Label?` | Frame |
| `ProgressBar` | thin 8 / regular 12 | `Track` (panelAlt), `Fill` (teal; coralDark when failing) | Frame + child Frame Size X = progress |
| `RangeReadout` | normal / outside | `Name`, `Value` (mono 40), `Unit`, `RangeBar` (`Normal` band tealSoft, `Marker`), `RangeText` ("Normal 60–140") | Frame |
| `StarRating` | 0–5 in 0.5 steps | `Star1..Star5` (each with `Half`), `Number` | ImageLabels |
| `ChecklistItem` | Done (green check) / Current (teal ring + bold) / Upcoming (grey ring) / Problem (coral ring) | `Mark`, `Label`, `Meta?` | Frame |
| `PatientRow` | default / selected / emergency / followUp / impatient | `Priority` (Badge), `Avatar` (40 px species icon), `PetName`, `Breed`, `Owner`, `Reason`, `Waited`, `Status` | TextButton row |
| `Stepper` | default / disabled | `Minus`, `QtyValue`, `Plus`, `Presets` (5, 10, 25) | Frame |
| `CatalogCard` | default / selected / locked / cantAfford / wrongRoom / owned | `Tile` (pale tint), `Render`, `ItemName`, `Price`, `Footprint`, `LockBadge` | ImageButton |
| `HireCard` | hireable / locked / blocked (debt) | `RoleIcon`, `Role`, `Jobs`, `Wage`, `HireCost`, `UnlockLevel`, `HireButton` | Frame |
| `Segmented` | 2–6 segments | `Seg_<name>` | Frame + UIListLayout |

**Name-uniqueness rule:** the client binds with `FindFirstChild(name, true)`, so every contract
name (`Cash`, `Level`, `Text`, `Treat`, `Progress`…) must appear **exactly once** inside its
ScreenGui. Component sub-parts that repeat (`Fill`, `Label`, `Icon`) must be reached by path, e.g.
`HUD.TopBar.XpBar.Fill`, never by a recursive search.

---

## 2. HUD (ScreenGui `HUD`, DisplayOrder 0)

Frames in Figma: `HUD` (1920×1080) and `HUD/Phone` (844×390). The world shows through; panels use
`hudGlass` at 6 % transparency with a card shadow.

### 2.1 Layer tree (1920×1080)
```
HUD
├─ TopBar                      Frame  pos (48,72) size 640×96  → Scale (0.025,0.067) (0.333,0.089)
│  ├─ ClinicLogo               ImageLabel 64 px round, teal paw mark
│  ├─ ClinicName               TextLabel h2  "Paws & Whiskers Vet"
│  ├─ Level                    Frame (collar-tag chip)  "Lv 3" + muted "Small Vet Office"
│  └─ XpBar                    Frame 300×10 (ProgressBar thin)
│     ├─ Fill                  Frame Size X = 0.58
│     └─ XpText                TextLabel small "1,105 / 1,372 XP"
├─ StatusBar                   Frame  right-aligned at (1872,72) AnchorPoint (1,0), 620×64, UIListLayout H
│  ├─ Cash                     StatChip  icon wallet + "$1,240"   (mono)
│  ├─ Reputation               StatChip  ★★★★☆ (StarRating S) + "4.2"
│  ├─ Day                      StatChip  calendar icon + "Day 6"
│  └─ Clock                    StatChip  clock icon + "10:45 AM"
├─ TutorialBanner              Frame top-centre (960,190) AnchorPoint (0.5,0) 880×64, tealSoft, radius pill
│  ├─ StepChip                 TextLabel small tealDark "Step 5 of 10"
│  ├─ Text                     TextLabel body "Review the chart on the computer and choose a diagnosis."
│  └─ Arrow                    ImageLabel (points toward target; world beam handled separately)
├─ AlertsList                  Frame right (1872,152) AnchorPoint (1,0) 420×(auto), UIListLayout V, Padding 8, max 3 shown
│  ├─ Toast (Emergency)        "EMERGENCY · Rocket (Beagle)"  "Holding up a front paw — needs an exam room now." Action "View"
│  ├─ Toast (Impatient)        "Sam is getting impatient"      "Honey has waited 3:05 in the waiting room." Action "Call in"
│  └─ Toast (Arrival)          "New arrival"                   "Priya checked in Mochi (follow-up visit)."
├─ ComputerButton              TextButton bottom-right (1872,1032) AnchorPoint (1,1) 132×104, white card, teal monitor icon, Label "Computer"
│  └─ Badge                    "3" coralDark circle (waiting count)
└─ BuildButton                 TextButton left of ComputerButton, gap 16, 132×104, teal hammer+ruler icon, Label "Build"
```
The bottom-centre is left empty for Roblox's backpack and chat. There is no left button column
and no hotbar: nothing in v1 needs them (deliberate departure from components.md "HUD").

### 2.2 States
- `TutorialBanner.Visible = snapshot.tutorial ~= nil`. `StepChip` = index in `Config.tutorial.steps`.
  The banner nudges once (`clinic.toastIn`) when the step changes.
- `Cash` turns `coralDark` with the label "Debt $40" when `clinic.debt > 0`.
- `Level` up: chip flashes teal; a Dialogue-style "Level 4 — Assistant unlocked" toast (Success).
- `ComputerButton.Badge` = number of appointments in phase Waiting/AtReception. Hidden at 0. It
  turns coralDark when any appointment is an emergency (and stays coralDark otherwise too, with a
  number).
- Roles: visitors (role `Visitor`) see `BuildButton` disabled with the tooltip "Ask the owner for
  build access".

### 2.3 Data binding
| Layer | Source |
|---|---|
| `ClinicName` | `snapshot.clinic.name` (default `Config.clinic.defaultName`) |
| `Level` | `clinic.level` + the title of the highest `Config.milestones` entry ≤ level |
| `XpBar.Fill` | `(xp - xpThis) / (xpNext - xpThis)` |
| `Cash` | `Format.abbreviate(clinic.cash)` with a `$` prefix; full number below 100k |
| `Reputation` | `clinic.reputation` (1 dp) → stars in 0.5 steps |
| `Day` / `Clock` | `clinic.day`. Clock is derived from the day timer: 720 s maps to 8:00 AM–8:00 PM |
| `AlertsList` | server events (arrival / emergency / impatience). Use the `Toast` template `AlertsList.Template` (Visible=false) |

### 2.4 Phone `HUD/Phone` (844×390, safe insets L/R 47, bottom 21)
- `TopBar` 300×64 at (59,52): `ClinicName` truncates at 18 chars, then `Level` chip + `XpBar` on line 2.
- `StatusBar` top-right, one row of 3 chips: `Cash`, `Reputation` ("4.2★" compact), `Clock`
  (`Day` merged as "D6 · 10:45"; the `Day` label stays as an instance but sits inside the Clock chip).
- `TutorialBanner` below TopBar at the centre, 460 wide, up to 2 lines at 14 px, with no StepChip.
- `AlertsList` shows max 1 toast (the newest; emergencies take priority), 300 wide, under StatusBar.
  The body is 1 line at 14 px.
- `ComputerButton` / `BuildButton` 64×64 (icon + 14 px label beneath, inside the card) stacked
  vertically on the right edge at y 140–290, above the jump-button zone.

---

## 3. VetComputer (ScreenGui `VetComputer`, DisplayOrder 10)

Opened from the in-world `VetComputer` desk (ProximityPrompt) or `HUD.ComputerButton`. A dim
backdrop `Dim` (`dim` at 0.65 transparency) sits behind it. Motion `clinic.monitorWake`.

Frames in Figma: `VetComputer/<Page>` for each of the 8 pages (1920×1080) + `VetComputer/Phone`
(PatientsPage and ChartPage at 844×390).

### 3.1 Shell layer tree (1920×1080)
```
VetComputer
├─ Dim                         Frame full-screen
└─ Window                      Frame 1440×860 centred, Scale (0.75,0.796), UIAspectRatioConstraint 1.674
   ├─ Bezel                    Frame #2A2F3A radius 20, 14 px border
   │  ├─ PowerLed              Frame 8 px teal circle, bottom-centre
   │  ├─ StickyNote            ImageLabel 150×120, rotated 4°, top-right corner, "Order more cough syrup!"
   │  └─ PawMagnet             ImageLabel 28 px
   └─ Screen                   Frame canvas #F6F1E9 radius 8
      ├─ TitleBar              Frame 64 px teal, Pattern (paw 6 %), EcgLine
      │  ├─ TitleIcon          56 px white circle, teal stethoscope icon, overlaps top-left by 12 px
      │  ├─ Title              "Paws & Whiskers Vet — Practice Manager"
      │  ├─ SignedIn           small white 80 % "Dr. You · Exam 1"
      │  └─ Close              plaster-style X, 44×44
      ├─ Tabs                  Frame left sidebar 232 wide, panel white, UIListLayout V, Padding 4
      │  ├─ PatientsTab        icon clipboard-list  "Patients"   AlertDot on (emergency waiting)
      │  ├─ ChartTab           icon file-medical    "Chart"
      │  ├─ DiagnoseTab        icon search-heart    "Diagnose"
      │  ├─ TreatTab           icon syringe         "Treat"
      │  ├─ InventoryTab       icon box             "Inventory"  AlertDot on (low stock)
      │  ├─ StaffTab           icon id-badge        "Staff"
      │  ├─ FinanceTab         icon receipt         "Finance"
      │  └─ ProgressTab        icon stairs          "Progress"
      ├─ PatientHeader         Frame 1160×72 top of content (persists on Chart/Diagnose/Treat)
      │  ├─ HeaderAvatar       48 px species icon
      │  ├─ HeaderName         h2 "Biscuit"   + muted "Golden Retriever · Owner: Maya"
      │  └─ HeaderPhase        Badge Routine "IN EXAM 1"
      └─ Pages                 Frame content area 1160×700
         ├─ PatientsPage  ├─ ChartPage  ├─ DiagnosePage  ├─ TreatPage
         ├─ InventoryPage ├─ StaffPage  ├─ FinancePage   └─ ProgressPage
```
Tabs are 216×56 (label body 20, icon 24). The active tab has a teal fill, white text and a 4 px
tealDark left bar. A sidebar is used rather than a top tab row because real practice software
uses sidebar navigation and the labels never have to shrink. The contract name `Tabs` is kept.

Pages toggle by `Visible`, with one page visible at a time. ChartTab/DiagnoseTab/TreatTab are
Disabled (muted, tooltip "Select a patient first") until the player handles a patient.

### 3.2 PatientsPage
```
PatientsPage
├─ PageTitle              h2 "Waiting room"   + muted "3 waiting · 1 in exam"
├─ WaitingList            ScrollingFrame 760×560, UIListLayout V, AutomaticCanvasSize Y
│  ├─ ColumnHeader        small caps muted: PRIORITY · PATIENT · OWNER · REASON FOR VISIT · WAITED
│  ├─ Template            PatientRow (Visible=false)
│  └─ rows (cloned)       PatientRow 760×76
├─ CallButton             Button Primary L, bottom-right of list: "Call Rocket in"
├─ CheckInButton          Button Secondary L (shown when the selected row is AtReception): "Check in"
└─ Calendar               Frame 368×640 right column
   ├─ Today               h2 "Today · Day 6"
   ├─ TodayStats          3 mini stats: "Seen 5" · "Waiting 3" · "Avg ★ 4.3"
   ├─ Timeline            8 AM → 8 PM vertical strip, dots for each visit seen today; "Now" line at 10:45
   └─ FollowUps           list "Follow-ups due": "Mochi — ears (Priya)"
```
Sample rows (sorted: emergencies first, then follow-ups, then by wait time; the in-progress
patient is pinned at the bottom):
| Priority | Patient | Owner | Reason (owner's words, truncated 1 line) | Waited | Status |
|---|---|---|---|---|---|
| EMERGENCY | Rocket · Beagle | Diego | "Rocket stepped on something on our walk and is holding up a front paw." | 0:40 | Waiting |
| FOLLOW-UP | Mochi · Domestic Shorthair | Priya | "Mochi won't stop scratching both ears — there's dark gunk in there." | 2:10 | Waiting |
| ROUTINE | Honey · Golden Retriever | Sam | "Honey is due for their yearly checkup and shots!" | **3:05** (amber, impatient) | Waiting |
| ROUTINE | Biscuit · Golden Retriever | Maya | "Biscuit has this honking cough since we got back from the dog park." | — | In Exam 1 (you) |

States: row selected = tealSoft fill + 3 px teal left bar. `Waited` turns amber at 75 % of the
patience time and coralDark past patience (patience is server-side; the client shows only the
colour state). `CallButton` is Disabled with the label "Exam room busy" when every exam room is
occupied, and hidden when nothing is selected. Empty state: illustration of an empty waiting chair
+ "No one waiting. Patients arrive every minute or so."

Binding: `snapshot.appointments[]` → `patient.name/breed`, `customer.name/complaint`,
`emergency`, `followUp`, `waited`, `phase`, `claimedBy`.

### 3.3 ChartPage (patient record)
```
ChartPage
├─ Signalment             card 380×300
│  ├─ PetName             "Biscuit"
│  ├─ Breed               "Golden Retriever"     (label/value rows, small muted labels)
│  ├─ Species             "Dog"
│  ├─ Age                 "4 years"
│  ├─ Weight              "68 lb"   (mono)
│  └─ Owner               "Maya"
├─ Complaint              card 380×200, quote style (left teal bar 4 px)
│  ├─ ComplaintLabel      small caps "OWNER SAYS"
│  └─ ComplaintText       "Biscuit has this honking cough since we got back from the dog park."
├─ Findings               card 760×330  h2 "Exam findings"
│  ├─ Template            FindingRow: `ExamIcon`, `ExamName`, `FindingText`, `Flag?`
│  ├─ Visual check        "Occasional dry, honking cough; eyes bright."
│  ├─ Stethoscope         "Heart 96 bpm (normal), normal rhythm; Left lung: Harsh, 31 breaths/min; Right lung: Harsh, 30 breaths/min"
│  └─ Temperature         "Temperature 103.2°F (FEVER; normal 100.5–102.5)"   Flag = Low-style badge "OUTSIDE NORMAL"
├─ History                card 760×190  h2 "Visit history"
│  ├─ Today               ordered chart entries: Complaint recorded → Visual check → Stethoscope → Temperature
│  └─ Previous            "No previous visits" (follow-ups list the earlier visit's diagnosis + treatments)
└─ RecordHint             muted small "Exams are done with real tools in the exam room. Results appear here."
```
`Flag` only comes from words already in the summary text ("FEVER", "outside normal", "low"). It
is never computed from the hidden case. Empty findings: "No exams yet — grab a tool from the
equipment cabinet."

Binding: `appt.patient.*`, `appt.customer.complaint`, `appt.chart[]` (kind Complaint / Exam /
Diagnosis / Treatment).

### 3.4 DiagnosePage
```
DiagnosePage
├─ PageTitle              h2 "Choose a diagnosis"  + muted "Pick what the findings point to. You'll find out if you were right at checkout."
├─ DiagnosisList          ScrollingFrame 640×560, radio rows 640×60, alphabetical
│  ├─ Template            row: `Radio`, `DiagnosisName`, `LockBadge?`
│  ├─ Ear infection (otitis externa)
│  ├─ Ear mites
│  ├─ Healthy — routine wellness
│  ├─ Kennel cough (infectious tracheobronchitis)   ← selected (teal radio, tealSoft row)
│  ├─ Paw pad cut
│  ├─ Tick infestation
│  ├─ Upset stomach (gastroenteritis)
│  ├─ Broken leg (fracture)               Locked "Lv 5"
│  ├─ Low red blood cells (anemia)        Locked "Lv 5"
│  ├─ Swallowed object (foreign body)     Locked "Lv 5"
│  └─ Pregnancy check                     Locked "Lv 10"
├─ EvidenceSummary        card 500×560 "Your findings" (read-only copy of ChartPage.Findings + complaint)
├─ ConfirmDiagnosis       Button Primary L "Confirm diagnosis"  (Disabled until a row is selected)
└─ ConfirmDialog          Window S "Confirm Kennel cough?"  "You can't change this for this visit." [Go back] [Confirm]
```
**No hints:** the list is alphabetical and never ordered, filtered, highlighted or scored by the
case. Unlocked names sort first, locked ones after. The page shows no "correct" or "incorrect"
feedback (the server returns `correct = nil`). Disabled with "Examine the patient first" until
the phase is Exam/OnTable and no procedure is running.

### 3.5 TreatPage
```
TreatPage
├─ PageTitle              h2 "Treatment plan"  + muted "Diagnosis: Kennel cough (infectious tracheobronchitis)"
├─ TreatmentList          ScrollingFrame 760×560, rows 760×80
│  ├─ Template            row: `Radio`, `TreatmentName`, `Supplies` ("Cough syrup ×1 · 3 in stock"), `Price` (mono), `StockBadge`
│  ├─ Vaccination                     Vaccine vial ×1 (6) · Syringe ×1 (20)       $40   READY
│  ├─ Clean ear canal                 Ear cleaner ×1 (5) · Cotton pads ×2 (30)    $30   READY
│  ├─ Medicated ear drops             Ear drops ×1 (4)                            $25   READY
│  ├─ Anti-mite spot-on               Anti-mite spot-on ×1 (3)                    $30   READY
│  ├─ Cough medicine + rest plan      Cough syrup ×1 (3)                          $35   READY   ← selected
│  ├─ Clean wound                     Antiseptic ×1 (6) · Gauze ×2 (20)           $30   READY
│  ├─ Bandage                         Bandage roll ×1 (8)                         $25   READY
│  ├─ Remove ticks                    Tick remover (tool)                         $30   READY
│  ├─ Tick prevention chew            Tick chew ×1 (4)                            $20   READY
│  ├─ Tummy medicine + bland diet     Stomach medicine ×1 (0) · Bland diet food ×1 (0)  $40  OUT OF STOCK
│  ├─ Fluids (hydration)              Fluid bag ×1 (0) · Syringe ×1 (20)          $55   OUT OF STOCK
│  ├─ Apply cast                      Locked "Lv 5"
│  └─ Retrieve swallowed object       Locked "Lv 20"
├─ PlanSummary            card 360 "This visit": done treatments with green checks; "Billed only if the treatment fits the problem."
├─ StartTreatment         Button Primary L "Start: Cough medicine + rest plan"
└─ FinishVisitButton      Button Secondary L "Send to checkout"
```
States: OUT OF STOCK rows are disabled and show a link "Order on Inventory". Done rows show a
green "DONE" badge and are disabled. `StartTreatment` is Disabled with "Finish the current
procedure first" while a procedure runs. The list is **never** filtered by the diagnosis.

### 3.6 InventoryPage
```
InventoryPage
├─ PageTitle              h2 "Supplies"  + muted "Boxes arrive at the back door — carry them to the shelf."
├─ StockTable             ScrollingFrame 760×520, header ITEM · IN STOCK · UNIT COST · STATUS
│  ├─ Template            row 760×56: `ItemIcon`, `ItemName`, `InStock` (mono), `UnitCost` (mono), `StockBadge`
│  └─ rows                every Cases.supplies entry, e.g. Cough syrup 3 $10.00 LOW · Syringe 20 $1.00 · Stomach medicine 0 $9.00 OUT · Fluid bag 0 $14.00 OUT · Cast roll 0 $15.00 OUT (Lv 5)
├─ OrderPanel             card 360×520 right
│  ├─ OrderItem           h2 "Cough syrup"
│  ├─ QtyStepper          Stepper: Minus · QtyValue "10" · Plus · Presets 5 / 10 / 25 (range 1–50)
│  ├─ OrderCost           "10 × $10.00 = $100"   (mono; Cost = ceil(cost × qty))
│  ├─ CashAfter           muted "Cash after order: $1,140"
│  └─ OrderButton         Button Primary L "Order · $100"
└─ Deliveries             strip 1160×150 bottom, h2 "Waiting to be shelved (2 / 6)"
   ├─ Template            box card 168×110: kraft-brown box icon, `BoxItem` "Cough syrup", `BoxQty` "×10", `BoxId` "#7"
   └─ Box_7, Box_8
```
States: LOW (≤ 2) = Low badge; OUT (0) = Emergency-style badge "OUT". `OrderButton` is Disabled
with the label "Shelve the boxes already waiting first" when there are 6 deliveries, and "Not
enough cash" when cost > cash. `QtyStepper.Minus` is disabled at 1 and `Plus` at 50.
Binding: `clinic.stock`, `clinic.deliveries[] {id,item,qty}`, `Cases.supplies`.

### 3.7 StaffPage
```
StaffPage
├─ PageTitle              h2 "Staff"  + muted "1 / 12 staff · wages are paid at the end of each day"
├─ HireCards              UIGridLayout 3 columns, cards 360×220
│  ├─ Template            HireCard
│  ├─ Receptionist        jobs "Check-in · Checkout · Phone"   Wage "$45/day"   HireButton "Hire · $300"
│  ├─ Janitor             jobs "Clean tables · Mop · Empty bins" Wage "$30/day" HireButton "Hire · $200"
│  ├─ Assistant           Locked "Unlocks at Lv 4"  ($400 · $55/day)
│  ├─ Technician          Locked "Unlocks at Lv 6"  ($700 · $80/day)
│  └─ Veterinarian        Locked "Unlocks at Lv 12" ($2,000 · $160/day)
├─ Team                   card 1160×140 "Your team": row "Lena · Receptionist · $45/day"
└─ FriendRoles            card 1160×160 "Friends in your clinic"
   ├─ Template            row: `FriendAvatar`, `FriendName`, `RoleDropdown` (Vet / Receptionist / Technician / Assistant / Visitor)
   └─ note                muted "Visitors can look around but can't change anything."
```
States: all `HireButton`s are disabled with "Pay off your bills first" when debt > 0, and with
"No room for more staff" at 12. Only the owner sees `RoleDropdown`; others see the role as a Badge.
Binding: `Config.staffRoles`, `clinic.staff[] {id, role, name, wage}`, `snapshot.role`.

### 3.8 FinancePage
```
FinancePage
├─ PageTitle              h2 "Finances · Day 6"
├─ StatTiles              3 tiles 370×130
│  ├─ Revenue             "$412"  greenText,  small "Revenue today"
│  ├─ Expenses            "$186"  coralDark,  small "Expenses today"
│  └─ Profit              "$226"  textPrimary (coralDark + "−" if negative), small "Profit today"
├─ DailyBills             card 560×300 "End-of-day bills"  (closes in `CloseCountdown` "4:12", UIAnim.countdown)
│  ├─ Rent                "$85"   muted "($40 + $15 × 3 rooms)"
│  ├─ Utilities           "$30"   muted "($15 + $5 × 3 rooms)"
│  ├─ Wages               "$45"
│  ├─ BillsTotal          "$160"
│  └─ Debt                (only when debt > 0) coralSoft row "Unpaid bills $40" + `PayBillsButton` Danger M "Pay bills"
└─ Ledger                 ScrollingFrame 580×500 "Today's ledger"
   ├─ Template            row: `EntryLabel`, `EntryAmount` (mono, green +, coral −)
   └─ sample              "Visit: Mochi +$85" · "Visit: Scout +$95" · "Supplies: Cough syrup −$100" · "Catalog: Tall plant −$45" · "Visit: Pepper +$70"
```
Binding: `clinic.finance {day, revenue, expenses, profit}`, `clinic.expenses {rent, utilities,
wages}`, `clinic.debt`, ledger entries (`label`, `amount`, `day`). Note: the ledger is **not** in
`GameLogic:snapshot()` today. The server must add `ledger` (today's entries) for this list
to show real data.

### 3.9 ProgressPage
```
ProgressPage
├─ PageTitle              h2 "Clinic progress"  + "Level 3 · 1,105 / 1,372 XP" + ProgressBar
└─ Ladder                 ScrollingFrame 1160×600, vertical timeline (teal line, dot per milestone)
   ├─ Milestone_1   Lv 1   "Small Vet Office"             REACHED (green)  "Checkups, vaccinations, minor illnesses"
   │                       unlock chips: Visual check, Stethoscope, Temperature, Ear exam, Coat & skin check, Vaccination, Cough medicine, Bandage, Golden Retriever, Beagle, Domestic Shorthair
   ├─ StepUnlocks_2 Lv 2   small row: Belly palpation · Tummy medicine · Fluids · Chihuahua · Waiting room TV
   ├─ StepUnlocks_3 Lv 3   small row: Exam room 2 ($1,500) · Receptionist · Janitor        ← "YOU ARE HERE" marker
   ├─ StepUnlocks_4 Lv 4   small row: Assistant
   ├─ Milestone_2   Lv 5   "Established Clinic"           NEXT (teal ring)  "Blood tests, X-rays, complex diagnoses"
   │                       chips: Blood test, X-ray, Apply cast, Lab ($3,500), Imaging ($5,000), X-ray machine, Blood analyser, Fracture / Anemia / Foreign body diagnoses
   ├─ StepUnlocks_6/8 Lv 6 Technician · Lv 8 Kennels + Recovery kennel
   ├─ Milestone_3   Lv 10  "Advanced Veterinary Practice"  locked  "Ultrasound, dental, new species"   chips: Ultrasound, Ultrasound cart, Pregnancy check
   ├─ StepUnlocks_12 Lv 12 Veterinarian
   ├─ Milestone_4   Lv 20  "Animal Hospital"               locked  "Surgery, recovery rooms, emergencies"   chips: Surgery room ($15,000), Surgical table, Retrieve swallowed object
   ├─ Milestone_5   Lv 35  "Premium Veterinary Hospital"   locked  "Specialists, larger staff"
   └─ Milestone_6   Lv 50  "Veterinary Empire"             locked  "Multiple locations, departments"
```
Milestone cards are 1040×120, with smaller step rows 1040×48. Locked milestones use
`lockedFill`, but their text stays readable (`textMuted`, not 30 % grey). Chips come from
`Config.unlocks`, `Config.rooms`, `Config.catalog` (minLevel) and `Config.staffRoles`. Lv 35/50 have
no data yet, so they show the note only.

### 3.10 VetComputer phone (`VetComputer/Phone`, 844×390)
- Full screen inside the safe area (750×369). The bezel shrinks to 6 px and `StickyNote` /
  `PawMagnet` are hidden.
- `TitleBar` is 40 px with title "Practice Manager". The visual `Close` is 36 px, but a `HitArea`
  extends it to 44×44.
- `Tabs` becomes a horizontal scrolling strip under the title bar (44 px tall, labels 14 px,
  icon + label). Short labels: Patients · Chart · Diagnose · Treat · Stock · Staff · Money ·
  Progress (instance names unchanged). The active tab auto-scrolls into view.
- `PatientHeader` is a 36 px single line, "Biscuit · Golden Retriever · Maya".
- Pages are single-column scroll views. `PatientRow` becomes 2 lines (badge + name/breed +
  waited, then the complaint truncated). The `Calendar` collapses to a "Today" chip row above the
  list. `CallButton` sticks to the bottom-right at 48 px.
- ChartPage stacks Signalment → Complaint → Findings → History.

---

## 4. ExamOverlay (ScreenGui `ExamOverlay`, DisplayOrder 5)

Shown while `appt.running` is set. It is **non-blocking**: there's no dim, the centre ~55 % of
the screen stays clear so the animal and the vet's hands are visible, and the overlay covers
≤ 25 % of the screen area. Panels use `hudGlass`.

Frames: `ExamOverlay` (1920×1080, sample = Biscuit, Stethoscope, step 4 of 5) +
`ExamOverlay/Dose` (state: Cough medicine dose step) + `ExamOverlay/Phone` (844×390).

### 4.1 Layer tree (1920×1080)
```
ExamOverlay
├─ StepPanel                   Frame left (48,200) 420×560
│  ├─ ProcedureName            h2 "Stethoscope"  + muted "Biscuit · Golden Retriever"
│  ├─ StepLabel                body bold "Place the stethoscope on the heart and hold still"
│  ├─ Progress                 ProgressBar regular 372×12 (hold / coverage / wait progress)  — `Fill` child
│  ├─ StepList                 UIListLayout V of ChecklistItem
│  │  ├─ Step1  Done      "Open the equipment cabinet"
│  │  ├─ Step2  Done      "Pick up the stethoscope"
│  │  ├─ Step3  Done      "Move close to the patient"
│  │  ├─ Step4  Current   "Listen: heart · left lung · right lung"   Meta "1 / 3"
│  │  └─ Step5  Upcoming  "Record your findings"
│  ├─ RecordButton             Button Primary M "Record in chart"  (Visible only on record step; UIAnim.pulse 0.04)
│  └─ Cancel                   Button Ghost S "Stop procedure"  (top-right of panel, icon X)
├─ PatientPanel                Frame right (1872,200) AnchorPoint (1,0) 380×400
│  ├─ MoodMeter                Frame 332×64
│  │  ├─ Track                 gradient tealSoft → amberSoft → coralSoft, with words "Calm" (left) "Stressed" (right)
│  │  ├─ Marker                10×28 dark pill at stress = 0.22
│  │  └─ MoodText              small bold "Calm — tail wagging"
│  └─ Reading                  RangeReadout
│     ├─ Name                  small caps "HEART RATE"
│     ├─ Value                 mono 48 "96"  Unit "bpm"
│     ├─ RangeBar              Normal band 60–140 (tealSoft), Marker at 96
│     └─ RangeText             "Normal for dogs: 60–140"
├─ PoseButtons                 Segmented, bottom-right (1872,1032) AnchorPoint (1,1) 4 × 120×72
│  ├─ Stand                    icon + "Stand"
│  ├─ Sit                      icon + "Sit"
│  ├─ LieSternal               icon + "Lie down"
│  └─ LieLateral               icon + "On side"
├─ ComfortButtons              bottom-centre (960,1032) AnchorPoint (0.5,1) 4 × 88×88 round cards, gap 16
│  ├─ Pet                      hand icon "Pet"
│  ├─ Comfort                  heart icon "Comfort"
│  ├─ Treat                    bone icon "Treat"   (+ muted "38 left": Treats stock)
│  └─ Brush                    brush icon "Brush"
│     └─ (each) Cooldown       radial ImageLabel 0.8 s sweep after use
└─ DoseSlider                  Frame centred above ComfortButtons (960,920) AnchorPoint (0.5,1) 640×150; Visible only on dose steps
   ├─ DoseTitle                "Cough syrup — set the dose"
   ├─ DoseGuide                muted "Patient weighs 68 lb · Label: 0.1 ml per lb"
   ├─ Track / Knob             0.0–15.0 ml, 0.1 steps (drops: integer 0–10)
   ├─ DoseValue                mono 32 "6.8 ml"
   ├─ DoseHelp                 Ghost S "Show me the math" → "68 × 0.1 = 6.8 ml"
   └─ DoseConfirm              Button Primary M "Draw up dose"
```

### 4.2 States by step kind (`Procedures.describe` → kind/label/target/tool/pose)
| Kind | StepLabel text | Progress | Other |
|---|---|---|---|
| open | "Open the {target}" (EquipmentCabinet → "equipment cabinet", Drawer → "drawer", Fridge → "vaccine fridge", MedCabinet → "medicine cabinet") | hidden | world highlight on target |
| take | "Pick up the {tool}" | hidden | |
| approach | "Move closer to the patient" | hidden | |
| pose | "Ask {name} to {pose}" | hidden | the requested PoseButton gets a teal ring + pulse; the others stay usable |
| place | "Place the {tool} on the {point} and hold still" | hold time | Reading updates on `PointDone` |
| scan | opens **Magnifier** | coverage | |
| stroke | label or "Gently rub over the area" | coverage | |
| wrap | "Wrap the bandage around the leg (3 turns)" | turns / 3 | |
| pull | "Grip and pull slowly" | per-tick | "Too fast! Slow and steady." in coralDark replaces StepLabel for 2 s |
| dose | "Set the dose" | hidden | DoseSlider visible, ComfortButtons hidden |
| wait | label ("Wait for the beep") | timer | |
| record | "Record your findings in the chart" | full | RecordButton visible |

- **Pulled away:** StepLabel flashes coralDark "{name} pulled away — help them relax first" for
  2.5 s. MoodMeter.Marker shakes ±4 px for 0.3 s. The current Step row shows the Problem mark.
- **Wrong dose:** DoseValue turns coralDark and the server message ("That's too much" / "That's
  not enough") shows under it.
- **Reading outside normal:** Value turns coralDark and the Marker sits outside the band; the
  RangeText stays. Temperature sample: "TEMPERATURE 103.2 °F · Normal 100.5–102.5".
  "Patient stressed, may read high" shows in amberText when the server reading is `stressed`.
- MoodMeter mapping (from `AnimalMind.snapshot`): stress < 0.3 "Calm", < 0.55 "Uneasy",
  < 0.75 "Stressed", else "Very stressed — calm first". The text always pairs with the colour.
- ComfortButtons are disabled during their 0.8 s cooldown (`Config.clinic.comfortCooldown`).
  `Treat` is disabled at 0 Treats.

### 4.3 Phone `ExamOverlay/Phone` (844×390)
- `StepPanel` collapses to a top-left card 300×112 (ProcedureName + StepLabel 2 lines + Progress +
  "4/5"). Tapping it expands `StepList` downward (max 200 tall). `Cancel` is a 44 px X icon on
  the card. `RecordButton` replaces Progress on the record step.
- `PatientPanel` is a top-right card 220×112: MoodMeter (track + word) and a compact Reading
  ("96 bpm · normal 60–140").
- `ComfortButtons` is a bottom-centre row at x 250–594 (outside the thumbstick zone), 4 × 64 px,
  14 px labels.
- `PoseButtons` show only during pose steps, as a popover row above ComfortButtons (4 × 72×56).
- `DoseSlider` replaces the ComfortButtons row while dosing (500×120). The knob hit area is
  44 px.

---

## 5. Magnifier (ScreenGui `Magnifier`, DisplayOrder 6)

Opened by scan steps (Otoscope = ear canal, FurCheck = coat close-up). Sample frame: **Ear exam
— Mochi (Domestic Shorthair), Right ear**. Motion `clinic.iris`.

```
Magnifier
├─ Dim                    full-screen dim 0.5 transparency (the lens IS the view, so dim is OK here)
├─ Lens                   Frame 640×640 circle at (720,540) AnchorPoint (0.5,0.5), UICorner 0.5, ClipsDescendants
│  ├─ View                ViewportFrame / zoomed render of the ear canal or coat patch (pans with drag)
│  ├─ Crosshair           thin white 40 % ring 64 px at centre
│  ├─ DwellRing           teal ring that fills over 0.5 s while hovering a spot
│  └─ Rim                 otoscope rim: 24 px dark-grey ring, teal cap tab at top
├─ Header                 Frame top-left (48,72) "Ear exam — Mochi"  muted "Drag to look around. Hold still on anything unusual."
├─ SideToggle             Segmented under the lens: "Left ear" | "Right ear" (FurCheck: "Left side" | "Right side")
│  ├─ L                   + `Coverage` ProgressBar thin "Looked over 100%"
│  └─ R                   + `Coverage` "Looked over 62%"
├─ FoundList              card right (1872,200) AnchorPoint (1,0) 520×520  h2 "Noticed"
│  ├─ Template            row: side Badge (L/R) + note
│  ├─ "Left — Dark coffee-ground debris"
│  ├─ "Right — Dark coffee-ground debris"
│  └─ "Right — Tiny moving white specks"
└─ DoneButton             Button Primary L under FoundList "Done looking"
```
States: `DoneButton` is Disabled with "Look over both sides first" until each side reaches
minCoverage (0.55 otoscope / 0.5 coat) or every spot on it is found. FoundList is empty at first:
"Nothing noticed yet — move the lens slowly." It shows **only** spots the player discovered (no
count of remaining spots, because that would be a hint). A found spot gets a small teal pin
inside the lens. Phone: the Lens is 300 px on the left half, FoundList is a 300 px card on the
right, and SideToggle and DoneButton go under FoundList.

---

## 6. Invoice (ScreenGui `Invoice`, DisplayOrder 11)

Printed at the reception `InvoicePrinter`. Paper style. Motion `clinic.printOut`. Sample: Biscuit.

```
Invoice
├─ Dim
└─ Paper                  Frame 560×800 centred, `paper` #FFFEFA, soft shadow, radius 4 (top), TornEdge bottom
   ├─ Clip                ImageLabel clipboard clip 160×56 top-centre, overlaps by 28 px
   ├─ Letterhead          paw logo + "Paws & Whiskers Vet" (h2, tealDark) + muted "Invoice #0042 · Day 6 · 10:52 AM"
   ├─ PatientLine         "Patient: Biscuit (Golden Retriever)"  "Owner: Maya"
   ├─ Divider             dashed 1 px lineStrong
   ├─ Lines               UIListLayout V, row 480×40: `LineLabel` left, `LineAmount` mono right
   │  ├─ Consultation                         $50
   │  ├─ Temperature                          $10
   │  └─ Cough medicine + rest plan           $35
   ├─ Divider
   ├─ Total               "TOTAL" h2 + mono 40 "$95"
   ├─ Stars               StarRating L (5 × 44 px) + "4.5" + italic quote "Thank you! Biscuit already seems happier."
   ├─ XpEarned            small tealDark "+40 XP"
   ├─ FollowUpNote        (only when bill.followUp) amberSoft row "Follow-up recommended — Biscuit may come back."
   └─ PayButton           Button Primary L full-width "Take payment · $95"
```
Free exams (Visual check, Stethoscope, Coat check, Palpation) aren't billed, so they get no line,
matching `Appointment.bill`. The invoice shows no "correct" / "wrong" stamp; the star rating and
follow-up note are the feedback. After `PayButton`: number pop "+$95" at HUD.Cash, then the
Invoice closes (`clinic.close`). Phone: Paper 340×360 scrollable, with PayButton pinned at the
bottom.

---

## 7. BuildMode (ScreenGui `BuildMode`, DisplayOrder 4)

Realistic-building profile deltas: toolbar, categorized catalog, grid toggle, mobile drag.
Motion `clinic.sheet`. The world stays visible; there's no dim.

```
BuildMode
├─ Toolbar                Frame top-centre (960,72) AnchorPoint (0.5,0) 760×80, white card, Segmented
│  ├─ Place               icon plus-square  "Place"   (active)
│  ├─ Rotate              icon rotate-cw    "Rotate"  (90° steps; R key)
│  ├─ Move                icon arrows       "Move"
│  ├─ Delete              icon trash        "Delete"  (refund 50 %: shows "Refund $22" in Cost)
│  └─ Paint               icon roller       "Paint"   (switches Catalog to Walls/Floors)
├─ GridToggle             switch right of Toolbar "Grid snap" (on)
├─ RoomPicker             dropdown left of Toolbar "Room: Waiting ▾" → Reception · Waiting · Exam 1 · Exam 2 (Buy $1,500, Lv 3) · Lab (Lv 5) · Imaging (Lv 5) · Kennels (Lv 8) · Surgery (Lv 20)
├─ Cost                   pill under Toolbar "Tall plant · $45   |   Cash $1,240"  (coralDark when unaffordable)
├─ ExitButton             Button Secondary M top-right "Done"
└─ Catalog                bottom sheet 1824×300 at (960,1032) AnchorPoint (0.5,1)
   ├─ CategoryTabs        Furniture · Medical · Decor · Lighting · Walls · Floors   (each a Tab: Furniture, Medical, Decor, Lighting, Walls, Floors)
   ├─ Items               ScrollingFrame horizontal, UIGridLayout cells 168×208
   │  ├─ Template         CatalogCard
   │  └─ Decor sample     Tall plant $45 1×1 · Shelf plant $35 2×1 · Paw-print rug $90 6×4 · Dog art print $50 (wall) · Cat art print $50 (wall) · Treat jar stand $40 · Waiting room TV $260 (Waiting room only, Lv 2)
   └─ CollapseHandle      44 px grab bar
```
Category contents (from `Config.catalog` / `Config.finishes`):
- **Furniture:** Waiting chair $60, Waiting bench $140, Drawer unit $180, Reception counter $500
  (essential), Vet computer desk $300.
- **Medical:** Exam table $400 (essential), Equipment cabinet $250, Medicine cabinet $300, Vaccine
  fridge $350, Hand-wash sink $200, Pet weighing scale $220, Invoice printer $120, Recovery kennel
  $320 (Lv 8), X-ray machine $4,000 (Lv 5), Blood analyser $2,500 (Lv 5), Ultrasound cart $6,000
  (Lv 10), Surgical table $9,000 (Lv 20).
- **Decor:** listed above.
- **Lighting:** **no items exist in `Config.catalog` yet.** The tab shows the empty state "Lamps
  are coming soon". Gameplay/art needs to add lighting items, or this tab should be removed;
  that's the lead's call.
- **Walls (Paint):** Warm cream (free, owned), Sage green $80, Sky blue $80, Blush pink $80, Oak
  panel $220, Paw wallpaper $260.
- **Floors (Paint):** Clean vinyl (free, owned), Checker tile $150, Warm oak $240, Terrazzo speckle
  $300.

Card states: selected (teal 3 px border), locked (Lv badge, render desaturated 60 %), cantAfford
(price in coralDark), wrongRoom (muted "Exam rooms only", disabled for the current room), owned
finish ("In use" Done badge). Placement validity shows in the world (green/coral ghost outline),
not in the UI.

Phone: Toolbar becomes a vertical right rail (5 × 52 px, icon-only with labels in a long-press
tooltip) above the jump zone. RoomPicker + Cost become a top-left chip. The Catalog bottom sheet
is 40 % tall and collapsible, with 2 rows of 120×150 cards. Drag to place with one finger;
Rotate is a button (no keyboard).

---

## 8. Dialogue (ScreenGui `Dialogue`, DisplayOrder 12)

Customer speech. Motion: bubble `clinic.open` from the tail origin, text `clinic.typeIn`.

```
Dialogue
└─ Bubble                 Frame bottom-centre (960,1000) AnchorPoint (0.5,1) 1000×240, white, radius 20, card shadow
   ├─ Tail                ImageLabel 40×24 pointing up toward the customer
   ├─ Portrait            ViewportFrame 120 px circle (customer avatar head + pet icon badge)
   ├─ Name                h2 "Maya"   + muted "Biscuit's owner"
   ├─ Text                body 22 "Hi! Biscuit has this honking cough since we got back from the dog park."
   └─ Options             UIListLayout V, Secondary M buttons 520×48, max 3
      ├─ Option1          "Let's take a look — come on in, Biscuit!"
      ├─ Option2          "Has he been eating normally?"
      └─ Option3          "Please take a seat in the waiting room."
```
States: tap the bubble to skip typing. Options appear after typing finishes, with a 0.04 s
stagger. An `Option` with consequences (e.g. "Send home") uses the Danger style. Personality tone
comes through the wording only. Phone: full width inside the safe insets (750×170), Portrait
64 px, Options become a 2-column grid of 44 px rows, and Text is 15 px with a 3-line max and
scroll.

---

## 9. Roblox mapping notes (per `figma/roblox-mapping.md`)

| Figma | This game |
|---|---|
| Frame → Frame | Sizes in Scale of parent. The px in this doc are at 1920×1080 (or 844×390): scale = px / parent px |
| Window root | `CanvasGroup` (needed for fade motion) with a UIScale child |
| Auto layout | UIListLayout (Padding as UDim scale); grids use UIGridLayout |
| Corner radius | UICorner scale = radius / min(w,h). Pills use 0.5 |
| 1 px card stroke | UIStroke Thickness 1, ApplyStrokeMode Border, colour `line`. **No text UIStroke** (game exception) |
| Text | TextLabel, TextScaled, UITextSizeConstraint (Max = token size, Min 14), FontFace from tokens.override |
| Shadows | 9-slice ImageLabel `Shadow` (ZIndex −1) |
| Icons | single-colour PNG @2x exported to `games/my-vet-office/assets/ui/` (uploads need owner approval), ImageColor3 tinted from tokens so one asset serves teal/white/muted |
| Lists | ScrollingFrame + UIListLayout + `AutomaticCanvasSize = Y`, a `Template` child (Visible=false) cloned by the client |
| Variants (locked / selected / disabled) | child overlay frames or property swaps toggled by script, e.g. `LockBadge.Visible` |
| Motion | String Attribute `Motion` = the motion id from §0.4 |
| Touch | `MobileUI.enforceTouchTarget` on every GuiButton. `HitArea` (transparent TextButton) where the visual is < 44 px |
| Phone layout | one ScreenGui per screen. The client swaps layout by toggling `Desktop` / `Phone` child containers, **or** repositions the same instances (preferred, so names stay unique). The layout is picked with `MobileUI.isTouch()` + viewport aspect |

ScreenGui properties (all): `ResetOnSpawn=false`, `ZIndexBehavior=Sibling`,
`ScreenInsets=DeviceSafeInsets`, `IgnoreGuiInset=false`, `Enabled=false` (except HUD).
DisplayOrder: HUD 0 · BuildMode 4 · ExamOverlay 5 · Magnifier 6 · VetComputer 10 · Invoice 11 ·
Dialogue 12.

### Server/data gaps found while designing
1. `GameLogic:snapshot()` has no `ledger`, so FinancePage.Ledger can't show real rows.
2. No exam room occupancy / room list per appointment in the snapshot, so `CallButton`'s "Exam
   room busy" state needs a field.
3. Patience is not in the snapshot (only `waited`). The impatience colour needs a 0..1
   `patienceLeft` or a server-sent impatient event.
4. `Config.catalog` has no Lighting items (§7).
5. The client (`Main.client.luau`) still binds template names (`HUD.Gems`, `HUD.CollectButton`)
   that aren't part of this game's contract.
6. `UIAnim.popOpen`, `bindButton` and `numberPop` are hard-wired to the bouncy house style (§0.4),
   so they need options or a game-local motion helper.

---

## 10. Figma build checklist (to do when the Figma tools can be called)
1. `create_new_file` "My Vet Office — UI" → `create_session` → load the figma-use skill.
2. Variables from `tokens.override.json` (collections: Color, Type, Radius, Spacing).
3. Page "Components": every component in §1 with variants.
4. Page "Screens 1080p": `HUD`, `VetComputer/Patients`, `/Chart`, `/Diagnose`, `/Treat`,
   `/Inventory`, `/Staff`, `/Finance`, `/Progress`, `ExamOverlay`, `ExamOverlay/Dose`, `Magnifier`,
   `Invoice`, `BuildMode`, `Dialogue`. Use a blurred clinic-interior placeholder behind the non-dim
   screens so contrast is judged realistically.
5. Page "Screens Phone": `HUD/Phone`, `ExamOverlay/Phone`, `VetComputer/Phone` (Patients + Chart).
6. `get_screenshot` each frame and look at it: clutter, "simulator-y" feel, contrast, any text
   < min size, touch targets. Fix, then re-shoot. Save PNGs to `games/my-vet-office/figma/screens/`.
7. Fill `figma.json` (fileKey, fileUrl, version, frame node ids).
