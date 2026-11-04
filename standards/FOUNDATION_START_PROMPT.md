# Paste into Claude Code

You are maintaining my **GitHub-backed Roblox brainrot/studded game-generation vault**. Read and treat `GAME_SYSTEMS.md`, `UI_ANIMATION_STANDARDS.md` and `VALIDATION_PLAN.md` as permanent project standards. Do not silently override them. My long-term workflow is that I give you only a game name and description, and you build a coherent game matching these rules.

**Do not start a large complete game right now.** First establish and TEST the reusable foundation:

1. Check which connections/actions actually work for GitHub, Figma, Blender and Roblox Studio. State unsupported actions honestly; don't claim to see Studio if you cannot inspect it. Create a test branch and work in the existing project/repository.
2. Build a Figma-first UI style system and a functional Roblox **UI playground**: Shop, Inventory, HUD x2→x128 context multiplier, 50-tier free/premium battle pass, Daily Rewards, Quests, Index, Settings and first-time guided Tutorial. Show bubbly spring hover, glossy diagonal shine, press bounce, menu transitions, rarity reveal, and UI sounds; support mobile tap, mute and reduced motion. Give me editor-visible UI preview screens in Studio WITHOUT requiring Play, then independently verify gameplay interaction in Play.
3. Create an original **Blender-only visual art test**: a themed studded environment fragment, a base, a decorated machine and one collectible/package. I want studs represented in intentional material/UV texture detail, not merely a few studs modeled as separate objects. Batch export/import and place everything in Roblox Studio so I can see the actual map in EDIT MODE. Never use Studio Parts to model final custom assets.
4. Once those pass visual review, build the reusable six-player/six-progressive-base foundation, one base per player. Configured max server size must be six. Build themed base stages in Blender. Later implement secure data, rewards and economy.
5. Output `TEST_RESULTS.md` with screenshots/evidence where supported, specific file paths, exact tests performed, blockers and next actions. Commit working code/assets to GitHub only after verifying the tool permits it. Never claim "done" solely because you wrote code.

Keep ALL existing style references and aesthetic standards. Do not copy individual reference assets. Ask me to visually review the UI playground and the Blender packaging/stud texture test before scaling up.
