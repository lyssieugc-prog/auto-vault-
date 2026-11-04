# Reference Image Catalog

Images are stored with Git LFS under `references/images/<category>/`. Every image needs a row in
`catalog.md` — an uncatalogued image is ignored.

Workflow (house-style §11): owner shares an image/video → Claude describes what it sees (look,
motion, timing) → owner says GOOD (adopt) or BAD (avoid) → the rule goes into the right style file
(global) or the game's notes (game-specific), and the image is catalogued here.

Categories: `ui/`, `maps/`, `models/`, `vfx/`, `thumbnails/`, `vault-baseline/` (renders of our
own templates for regression comparison).
