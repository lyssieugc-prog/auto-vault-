# Figma → Roblox Mapping

| Figma | Roblox |
|---|---|
| Frame | `Frame` (BackgroundColor3 from fill; Size/Position as Scale of parent) |
| Auto layout (vertical/horizontal) | `UIListLayout` (FillDirection, Padding as UDim scale, alignment) |
| Grid auto layout | `UIGridLayout` (CellSize scale) |
| Corner radius | `UICorner` (CornerRadius scale = radius / min(w,h)) |
| Stroke | `UIStroke` (ApplyStrokeMode Border for frames, Contextual for text) |
| Linear gradient | `UIGradient` (Color sequence, Rotation) |
| Text | `TextLabel` (TextScaled + `UITextSizeConstraint` max; Font from tokens) |
| Text stroke | `UIStroke` on TextLabel + duplicated shadow TextLabel offset (0, 0.04) |
| Image / icon | `ImageLabel` (uploaded decal asset id), ScaleType Fit |
| Button component | `ImageButton`/`TextButton` + `UIAnim.bindButton` |
| Aspect lock | `UIAspectRatioConstraint` |
| Min/max size | `UISizeConstraint` (touch targets ≥ 44px) |
| Drop shadow | ImageLabel 9-slice shadow behind frame |
| Variant: locked/claimed | child overlay frames toggled by script |
| Prototype animation | `UIAnim` call noted in an Attribute `Motion` on the instance |

Rules
- Scale only. No Offset sizes except stroke thickness and the button lip.
- ScreenGui: `ResetOnSpawn=false`, `ZIndexBehavior=Sibling`, `ScreenInsets=DeviceSafeInsets`.
- Name instances exactly like Figma layers so scripts and screenshots can be diffed.
