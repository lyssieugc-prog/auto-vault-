# UI_ANIMATION_STANDARDS.md — Bright, Bubbly Roblox UI
Version: 1.0 | Mandatory UI style across this vault

## Design direction
Bright and highly polished Roblox simulator UI, expressive but readable: rounded corners, controlled vivid gradients, glossy surface treatment, friendly iconography, high-contrast text and clear visual hierarchy. Game theme determines palette/icons; never abandon the recognizable bright/bubbly component language. Never paste generic default Roblox menus as a final deliverable.

## Figma components (design first)
- Primary, secondary, premium, danger, disabled, selected and locked buttons.
- HUD left/right rail with context-named x2 → x128 multiplier ladder and currently owned state.
- Shop item cards and confirmation dialog; inventory grid with filters/search/detail panel; index/discovery book; daily reward calendar; quests; season 1 50-tier battle pass; codes; settings; rebirth confirmation; event hub; leaderboards; rare discovery toast; loading screen; guided tutorial pointers.
- Each component must have normal, hover, pressed, disabled, loading, selected, error and success states where applicable.
- Responsive desktop + narrow/mobile frames. Document padding, type scale, touch sizes, focus order, safe zones and modal priority.

## Motion contract (tune by test, use shared tokens)
- Hover (desktop): ~1.05–1.08 scale and subtle lift using smooth/spring easing, around 120–200ms. Ensure anchors prevent side buttons from overlapping adjacent HUD.
- Shine: diagonal glint traverses glossy buttons on hover or occasional idle pulse; clip correctly; do not animate every visible control continually.
- Press: compress to ~0.94–0.97 then spring to 1.0, with subtle audio and optional particle/sparkle for meaningful actions.
- Menu open: ~0.85 → 1.03 → 1.00 spring, background dim and optional blur where performant. Close: shrink/fade cleanly; preserve focus and never trap input.
- Reward reveal: pop/scale, rarity accent, theme-fitting sound and particles. Very rare: optional larger cinematic, with skip and reduced-motion alternative.
- Progress bars: smoothly animate server-confirmed progress; show actual values. Notifications slide/fade in and out without blocking core controls.
- Mobile: tap/press/release equivalents (NO dependence on hover). Gamepad focus highlighting. Disable/limit shine and shake with reduced-motion setting.
- Sound: enabled by default, short satisfying hover/click/success/error effects; independent UI SFX slider/toggle, no excessive simultaneous playback.

## Implementation rules
- One reusable `UIEffects`/motion module with tokens and centralized sounds. Respect animation cancellation and rapid clicking; no stacked Tweens/duplicate sounds.
- Use accurate hitboxes and layers, anchoring, UI constraints and screen-size tests. Keep critical gameplay HUD unobstructed.
- Prototype actual interaction states in a standalone **UI playground** in Roblox, linked to preview mock data without live purchases.
- A Studio Edit-mode UI preview MUST show representative screens (shop, inventory, battle pass, multiplier and tutorial) without having to press Play. Runtime tests still required for interactions.
- All purchase buttons must use a confirmation/appropriate Roblox purchase prompt; do not animate success before the server confirms it.

## UI playground acceptance checklist
- [ ] Figma component board created and accessible
- [ ] Roblox edit-mode preview shows HUD and at least five sample screens
- [ ] Buttons animate hover, press, shine and open/close transitions
- [ ] Mobile tap, small screen and gamepad focus considered
- [ ] Shop, inventory, multipliers, battle pass, quests and index contain real state demonstrations
- [ ] Sounds play and settings can mute them
- [ ] Reduce Motion works; no excessive constant movement
- [ ] Overlap, clipping, z-index and text readability audited
- [ ] Rapid-click and modal stacking bugs tested
- [ ] Screenshots/recording of actual UI available for review, not just code output
