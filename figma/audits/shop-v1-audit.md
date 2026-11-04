# Shop v1 audit: REJECTED by the owner ("generic mobile-game clipart")

Evidence: `shop-v1-rejected.png`, Figma `LKQvsczbhomTqLmT9me2oZ` node `10:14895`, at 1280×720.
Also rejected: the 16 vector icons (`12:3`–`12:101`) and the RewardCard v2 set (`13:9244`).
They are kept in the file as rejected examples and are not deleted.

## Quality gaps (specific, not "needs polish")
| # | Gap | What's on screen | What the benchmark does |
|---|---|---|---|
| 1 | **No item art at all** | Every card's hero is a flat yellow rounded square | Each card has a large rendered item (shaded, lit, rim light) that fills about 55% of the card |
| 2 | **No hierarchy** | Four equal cards in a row, all the same blue, same size | One dominant featured hero, then secondary offers, then small packs. Your eye lands in one place first |
| 3 | **Text collisions** | Corner tags ("BEST DEAL!") sit on top of the card titles and are unreadable | Tags break the card *edge* at an angle and never cover the title |
| 4 | **Stud texture as noise** | The same stud tile on the panel, cards, tabs and title bar, so nothing separates | Pattern only where it helps (card backs or the title bar), at low contrast. The body stays calm so the art pops |
| 5 | **Flat framing** | A single stroke and a single fill per card | 3 to 4 layers: dark outer outline, then a coloured bevel, then a lighter inner rim, then a gradient body with an inner shadow. The bottom lip gives depth |
| 6 | **Weak type** | Title and labels use one stroke; no shadow offset; prices read "R$ —" | Heavy outline plus an offset drop shadow. Numbers are the biggest text on a buy card. Old price is struck through |
| 7 | **Empty composition** | About 25% of the panel is dead space below the cards; a dev note sits in the UI | The panel is full: hero, offers and a promo strip. Developer notes stay out of the art |
| 8 | **No theme** | Nothing says which game this is | Frame decor, the title icon and the art are all themed to the game |
| 9 | **Decoration ≠ quality** | Sparkles and gradients were added to cover missing art | Sparkles accent finished art; they can't replace it |

## Root cause (the workflow, not effort)
The art was built from vector primitives through the Figma Plugin API: rectangles, ellipses and
simple paths. That method can make good **frames, buttons, type and layout**. It cannot make
**illustrated collectibles**. Painterly shading, rim light, material variety and character
appeal need either a 3D render or a hand-drawn illustration. More vector layers only give better
clipart.

## Proposed asset-production method
1. **Item and collectible art = Blender renders.** Model the item in the vault's 3D style
   (texture studs, chunky parts, bible §13 review). Render a hero shot in Cycles with key, rim
   and fill lights on a transparent background, at 1024 px, then export a PNG. Real Roblox
   simulators make their shop art the same way, and the art then matches the in-game model
   exactly. This runs headless here (`bpy`), so it's tested.
2. **Frames, type, layout = Figma**, as reusable components with variables. The rendered
   PNGs go in as image fills on an `Art` slot, so the art can be swapped without rebuilding
   anything.
3. **Optional:** use Figma's image generation for background or painterly accents only. Or the
   owner supplies or commissions illustrations, which go into the same `Art` slot.
4. **Review gate:** a screenshot at 1280×720 *and* at phone width (about 844×390), each
   compared with the reference, before any other screen.

## Single shop window plan (pending owner OK on the method)
1280×720, an original theme, one layout:
- **Left 45%: the featured collectible hero.** A large Blender render on a sunburst, a rarity
  plate, a countdown, a strikethrough price and a lime buy button.
- **Right column: three purchase options** (small, medium, best value) as stacked offer cards,
  each with its own rendered art. Only the best-value card gets the "BEST DEAL" ribbon.
- **Bottom strip: rarity cards.** Common, Rare, Epic, Legendary and Mythic, each with an odds
  label ("1 in N"). Mythic gets the rainbow stroke.
- **Top-right: premium promo.** The Season 1 Pass or VIP banner, with its own gold or purple
  treatment.
- Prices stay `CONFIG_REQUIRED`. The buy button only opens a confirmation; success is shown
  only after the server confirms it.
