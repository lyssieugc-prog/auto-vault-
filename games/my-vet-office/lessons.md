# My Vet Office — Game-specific lessons & exceptions

Corrections that apply ONLY to this game (format: lessons/README.md). Global rules live in
lessons/global.md.

### G-20261111-01 — Game exception: clinic-software UI instead of house simulator UI
- Scope: game-specific (owner pitch: "Avoid generic Roblox simulator UI with enormous colorful
  buttons everywhere. Interfaces should resemble simplified real veterinary software")
- Rule: this game waives house-style UI §1–2 items that read as simulator UI (dark navy panels,
  text strokes, Fredoka One, sunbursts/studs on cards, lime buy pills, rotated tags, Back.Out
  bounce, shop/egg/pass screens). Uses the cream/teal/coral clinic palette in
  `figma/tokens.override.json`. Full table: `figma/ui-spec.md` §0.
- Status: inferred from the pitch — pending owner confirmation.

### G-20261111-02 — No purchase pads / passive income
- Scope: game-specific (owner: "Do not make a generic Roblox tycoon", "Avoid simple purchase pads")
- Rule: vault Tycoon/Currency income/Rarity/Rebirth are not used. Rooms are empty shells you
  furnish with grid placement; money only comes from treating patients.
