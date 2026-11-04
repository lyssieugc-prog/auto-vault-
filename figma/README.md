# Figma UI Pipeline

**Rule: all UI starts in Figma and is implemented faithfully in Roblox.**

```
figma/
  tokens.json            design tokens (colours, fonts, strokes, motion) — single source of truth
  components.md          component specs (Window, Card, BuyButton, Tag, HUD, ...)
  roblox-mapping.md      Figma layer → Roblox Instance translation rules
```

## Per-game workflow
1. Create a Figma file `<Game Name> — UI` from the component specs (Figma MCP
   `use_figma` / design tools when connected; otherwise the owner duplicates the library file).
   Record the file key + version in `games/<slug>/figma/figma.json`.
2. Theme the frames for THIS game (frame decor, title bar pattern, close X, open animation).
3. Export icons/decals as PNG @2x → `games/<slug>/assets/ui/` (LFS), upload as Decals in Studio
   (owner approval needed for uploads under their account), record asset IDs.
4. Build ScreenGuis in Studio from the Figma frames using `roblox-mapping.md` (Studio MCP,
   or `figma-to-roblox-ui` skill if installed). Scale-only sizing.
5. Wire motion with `systems/src/Client/UIAnim`.
6. Screenshot Studio UI next to the Figma frame; differences go in the game report.

## Versioned references
`games/<slug>/figma/figma.json`:
```json
{ "fileKey": "", "fileUrl": "", "version": "", "frames": { "HUD": "node-id", "Shop": "node-id" } }
```
Never commit Figma personal access tokens. Use the `FIGMA_TOKEN` env var only.
