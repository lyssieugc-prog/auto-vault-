# UI Component Specs (house style)

All sizes are relative (Scale). Tokens refer to `tokens.json`.

## Window
- Title bar: saturated theme colour, height 14% of window, UIGradient top-light → bottom-dark,
  pattern overlay (theme). Oversized icon (≈ 1.4× bar height) breaking top-left corner, rotated -8°.
- Title: `font.title`, white, UIStroke `stroke.textLarge` `color.stroke`, shadow copy offset (0, 3px).
- Body: `color.panel`, UICorner `radius.panel`, outer UIStroke 4px darker.
- Close X: square, `color.red`, white stroked X, top-right, overlaps edge by 25%.
- Behind window: rotating Sunburst ImageLabel (`motion.sunburstSecondsPerTurn`).
- Open: `UIAnim.popOpen` (Back.Out 0.35s). Close: `UIAnim.close`.
- Theme decor: 2–4 ImageLabels hanging off corners (clouds/coral/pumpkins…).

## Card (item / pass / pack)
- Saturated colour block + UIGradient + sunburst rays + tiled stud texture (ImageTransparency 0.85).
- Inner border lighter (UIStroke inside frame child), outer stroke dark 3px.
- Big glossy item render (ViewportFrame or pre-rendered PNG from Blender preview).
- Optional Tag, rarity strip, price button. Hover/press via `UIAnim.bindButton`.
- Locked: dark overlay + "???" silhouette + LOCKED! tag. Claimed: green CLAIMED stamp.

## BuyButton
- Pill, `color.green` with darker lip (`color.greenLip`, `button.lipPx`) as a child frame below.
- White gloss stripe top 30% at `button.glossOpacity`. Robux icon + white price, stroked.
- Gift button (small square) beside every Robux price.

## Tag
- Rotated `tag.rotationMinDeg..MaxDeg`, heavy caps text, colour by meaning: New! (lime), EXCLUSIVE
  (purple), SECRET (black), MYTHIC! (rainbow), LIMITED! (red), BEST DEAL! (gold), SAVE % (red).

## HUD
- Left column: Shop, Index, Store buttons (square, icon + label). Right column: Pets/Eggs.
- Top-centre: nav pills + currency counters with "+" button (opens shop page).
- Centre-top: progress bar (next goal / rebirth). Event timer banner.
- Bottom: numbered hotbar slots. All buttons ≥ `touch.minTargetPx`.

## Screens (required, see house-style §1)
Shop · Egg roll (odds strip + pity counter) · Daily Rewards (7-day grid) · Playtime Rewards ·
Index · Upgrades · Season 1 Pass · Trading (if game trades) · Settings.

## Feedback
Number pop (`UIAnim.numberPop`), claim sequence (flash → burst text → confetti → stamp → fly away),
error slam text, live countdowns (`UIAnim.countdown`).
