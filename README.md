# Procedural Worlds

**Paste a story, get it told as a hand-inked animated graphic novel.** A Blender 5.2 engine (pure Python / `bpy`, no external assets) builds every place in the story from a seed, frames each beat as a comic shot, and renders it in an ink style: wobbly brush outlines, flat cel shading, hatching, grime and paper grain. A web player presents the result as a motion comic.

```
story text --story/parse.py--> story.json --tools/render_story.py (Blender)--> clips + stills --web/--> motion comic
```

![Kitchen, golden hour](renders/hero/kitchen_7_golden.jpg)

## Gallery

| | |
|---|---|
| ![Island, dusk](renders/hero/coastal_island_42_dusk.jpg) | ![Island, day](renders/hero/coastal_island_1_day.jpg) |
| ![Alley, night](renders/hero/cyberpunk_alley_42_night.jpg) | ![Kitchen, night](renders/hero/kitchen_42_night.jpg) |
| ![Island, golden](renders/hero/coastal_island_7_golden.jpg) | ![Alley, dusk](renders/hero/cyberpunk_alley_7_dusk.jpg) |

Seed × mood contact sheets (seeds 1 / 7 / 42 × day, golden hour, dusk, night):
[kitchen](renders/sheets/kitchen_sheet.jpg) · [island](renders/sheets/coastal_island_sheet.jpg) · [alley](renders/sheets/cyberpunk_alley_sheet.jpg).
A short fly-through with "boiling" lines: [renders/flythrough_coastal_island_42_dusk.mp4](renders/flythrough_coastal_island_42_dusk.mp4).

## Features
- **Three scene generators**, each deterministic per seed, in four moods (day, golden hour, dusk, night):
  - **Coastal island:** cliffs with inked strata, a lighthouse and cottage, sea stacks, grass placed with Geometry Nodes, and an ink-drawn sea with foam rings and no visible horizon edge.
  - **Kitchen interior:** a lived-in room with a checker floor, cabinets, a cork board, pans and clutter, and a hallway beyond the door.
  - **Cyberpunk alley:** fire escapes, neon blade signs, sagging cables, lanterns, and neon streaks reflected in a wet road.
- **Ink style module (`ink.py`)** that any scene gets automatically:
  - Grease Pencil Line Art outlines: heavy silhouettes, thin inner lines, noise, tapered ends and overshoot.
  - Cel shading through Shader to RGB, with hatching in shadow, grime in corners, stains and drips.
  - A hand-made wobble on all geometry (Geometry Nodes).
  - An inked sky with outlined clouds and a sun or moon disc.
  - Compositor effects: line wobble, paper grain, ink blots and a vignette.
- **Fly-through camera** that follows a spline. The lines "boil" every two frames, like hand-drawn animation.
- **Sidebar panel:** presets, an Ink/Realistic style toggle and quality settings.

## Tell a story
```
python story/parse.py my_story.txt -o story/examples/my_story.json          # Gemini if GEMINI_API_KEY is set, else offline keywords
tools/blender.sh -b --factory-startup -P tools/render_story.py -- story/examples/my_story.json
tools/blender.sh -b --factory-startup -P tools/export_animatic.py -- story_out/my-story
cd web && npm run sync && npm run dev
```
- `story/schema.json` is the shared story format: scenes with setting layers, plus beats with a shot type, focus, camera move, caption and off-panel dialogue.
- Example stories are in `story/examples/`.
- There are no character models: the story is told through places, objects, POV shots, captions and speech balloons.

## Walk the story (first person, Godot)
Blender builds every world and Godot runs it.
```
tools/blender.sh -b --factory-startup -P tools/build_world.py -- story/examples/the_last_watch.json   # -> story_out/<slug>/world/*.glb + world.json
walk.bat the-last-watch            # or: godot --path godot -- --story ../story_out/the-last-watch/world
```
- **Controls:** WASD or arrow keys to move, mouse to look, Shift to sprint, E to continue to the next scene, N to skip a scene, Esc to free the mouse.
- **Story beats:** captions and off-panel dialogue appear as you reach each beat's place.
- **Look:** ink cel bands, boiling edge lines, hatching and paper grain are drawn in real time.
- **Requirements:** Godot 4.x. `walk.bat` uses `.tools/godot/` if present, otherwise `godot` on PATH. Running with no story argument shows a picker.

## Install
- **As an extension (Blender 4.2+):** zip the `procedural_worlds/` folder (it contains `blender_manifest.toml`), then Preferences > Add-ons > Install from Disk. The extension install path is not verified yet.
- **As a legacy add-on:** zip the same folder, then Preferences > Add-ons > Install from Disk.
- **Panel:** 3D Viewport > N sidebar > **Worlds**. Pick a preset or a scene, seed and mood, then press **Generate world**.

## Headless tools
On Windows Store installs, call Blender through `tools/blender.sh`.
```
tools/blender.sh -b --factory-startup -P tools/smoke_test.py -- KITCHEN 7 GOLDEN
tools/blender.sh -b --factory-startup -P tools/grid.py -- KITCHEN            # seed x mood contact sheet
tools/blender.sh -b --factory-startup -P tools/hero.py -- KITCHEN:7:GOLDEN   # 1920x1080 hero
tools/blender.sh -b --factory-startup -P tools/flythrough.py -- COASTAL_ISLAND 42 DUSK 48
tools/blender.sh -b --factory-startup -P tools/check_invariants.py
```

See `CLAUDE.md` for architecture, Blender 5.x API notes and status.
