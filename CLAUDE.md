# Procedural Worlds — Blender add-on (handoff for Claude Code)

## What this is
A Blender add-on (Python/`bpy`). One sidebar panel (View3D > N > **Worlds**): pick a scene type, seed, size, mood -> it builds a *complete* scene: geometry, procedural materials, lighting, camera, render settings, and by default renders it as a **hand-inked graphic-novel panel** (see Art direction). Goal: impressive showcase renders + a reusable tool. Not a web/Three.js project.

## Art direction: hand-drawn ink flow look
Every render must look DRAWN, not 3D-rendered; target is `reference/ink_style_ref.png` (cluttered kitchen panel).
- Ink: thick, slightly wobbly black brush outlines with varying weight; heavier on silhouettes, thinner inside.
- Shading: flat 2-3 tone cel shading; shadows are a darker, muted version of the same hue.
- Texture: hatching in shadows, ink blots/drips/smudges/grimy stains near edges, paper grain over the frame.
- Palette: muted, slightly dirty (sage/teal, ochre, cream, faded terracotta) unified by black ink.
- Shapes: hand-made, wonky, never perfectly straight.
- Implemented once in `procedural_worlds/ink.py`, applied automatically by `core.generate()` to ANY scene; never hand-tune per scene (scenes may only pass hints, see Contracts).

## Session log
- Final 5-hour session started **2026-10-16 19:13 IST** (checkpoints 20:43 / 22:13 / 23:13 / 23:53).
- Remote: **https://github.com/fabastic/procedural-worlds** (private), branch `master` tracks `origin/master`. Push after every commit.

## Status (read this first)
- **Ink style module (`ink.py`) — done, applied to every scene by `core.generate()`:** Line Art (GP v3) heavy silhouettes + thin inner/crease/intersection lines with noise, taper, overshoot; `PW_InkToon` cel bands + muted shadow hue + occlusion-gated hatching + AO grime/stains/drips; `PW_InkWonk` GN wobble; inked sky world (bands, outlined clouds, sun/moon disc, stars); compositor (line wobble, paper tint/mottle/grain, blots, smudges, warm vignette, bloom for strong emitters).
- **Scenes (all three registered, grids looked at, invariants pass):**
  - `COASTAL_ISLAND` (`scene_island.py`): cliffs with inked strata, lighthouse + cottage, sea stacks, GN grass, ink-authored sea with foam rings (baked `pw_shore` attribute), gulls. Heroes: `renders/hero/coastal_island_*.jpg`.
  - `KITCHEN` (`scene_kitchen.py`, the showpiece, built by a subagent): checker floor, teal trim, cabinets, cork board, pans, fridge, hallway beyond doorway, per-mood lamps. Heroes: `renders/hero/kitchen_*.jpg`.
  - `CYBERPUNK_ALLEY` (`scene_alley.py`, built by a subagent): modular buildings, fire escapes, blade neon signs, cables, lanterns, wet road with streak reflection decals. Heroes: `renders/hero/cyberpunk_alley_*.jpg`. Slow: 15-35 s/frame at 960x540 (Line Art).
- **Fly-through:** `anim.py` (`setup_flythrough`, `set_video_output`), operator `pw.flythrough`, `tools/flythrough.py` -> MP4; GP noise reseeds every 2 frames + compositor wobble keyed to frame = line boil. `tools/video_frames.py` decodes MP4 frames via the sequencer (no ffmpeg on this machine).
- **Panel:** presets, Ink/Realistic style toggle, quality, fly-through box. `blender_manifest.toml` present (not yet tested as an extension install).
- **Known issues:** night kitchen outlines *look* dark brown but measured line cores are ~0.04 (near-black); it is antialiasing over warm-lit surfaces, not a pipeline bug (GP layer/object lights are off); NIGHT palette is dark on lit scenes (alley lifts its own colours); realistic mode keeps the stylized island sea; island gulls tiny.

## In progress right now
- Ink style pass (session 0:00-1:30) was paused at 19:16 to create the GitHub repo; nothing uncommitted.

## Blocked
- Nothing.

## Next
- See the session plan: ink pass -> scene polish -> 20-40 s animatic at 12 fps -> ship (heroes, README, manifest, reinstall).

## Running Blender headless on this machine (important)
- The Store install's `blender.exe` (`C:\Program Files\WindowsApps\BlenderFoundation.Blender_5.2.2.0_x64__ppwjx1n5r4v9t\Blender\blender.exe`) **cannot be exec'd from Git Bash or PowerShell ("Access denied")**. Use the app-execution alias via **`tools/blender.sh`** (wraps `%LOCALAPPDATA%\Microsoft\WindowsApps\blender-launcher.exe`). The launcher drops stdout, so the wrapper redirects Python stdout/stderr to a temp log, replays it, and propagates the exit code (`--python-exit-code 3`).
- `tools/blender.sh -b --factory-startup -P tools/smoke_test.py -- COASTAL_ISLAND 1 [MOOD] [OUT] [RX RY]` — EEVEE ink render, ~4-15 s.
- `tools/blender.sh -b --factory-startup -P tools/grid.py -- COASTAL_ISLAND [1,7,42] [DAY,GOLDEN,DUSK,NIGHT]` — 12 renders in one session (~50 s) + contact sheet `renders/grid/<scene>_sheet.png`. Judge the sheet next to the reference.
- `tools/blender.sh -b --factory-startup -P tools/check_invariants.py -- [SCENE ...]`.
- Scripts delete the factory cube/camera/light first (they'd pollute renders).

## Blender 5.x API facts (don't relearn)
- EEVEE engine id `BLENDER_EEVEE`; Principled sockets `Transmission Weight`, `Emission Color`, `Emission Strength`; `ShaderNodeMix` sockets share names -> look up by identifier (`Factor_Float`, `A_Color`, `B_Color`, out `Result_Color`); enum introspection unreliable -> try/except assignments.
- **Compositor:** `scene.node_tree` is gone; use `scene.compositing_node_group = bpy.data.node_groups.new(name, "CompositorNodeTree")`; output is a `NodeGroupOutput` (+ `tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")`), there is no Composite node. Shader texture/math nodes (`ShaderNodeTexNoise`, `TexVoronoi`, `TexWhiteNoise`, `TexWave`, `Math`, `Mix`, `MapRange`, `VectorMath`, `SeparateXYZ`) work inside compositor trees; coordinates come from `CompositorNodeImageCoordinates` (outputs `Uniform`, `Normalized`, `Pixel`). Render Layers only exposes `Image`/`Alpha` unless passes are enabled.
- **Grease Pencil v3:** data is `bpy.data.grease_pencils` (type `GreasePencil`), object type `GREASEPENCIL`. Line Art is an object modifier `"LINEART"` (`GreasePencilLineartModifier`), thickness is **`radius` in world metres** (default 0.0025 = invisible at scene scale; no screen-space option) -> ink.py derives it from camera distance + lens. Other modifiers: `GREASE_PENCIL_NOISE/THICKNESS/LENGTH/SUBDIV/...`; layer filter is `tree_node_filter`. Set `gp.stroke_depth_order = "2D"` for Line Art (with "3D" the strokes z-fight under the surfaces and vanish). Length modifier `random_*_factor` is a fraction of stroke length (0.6 = huge stray tails); keep `use_curvature=False`.
- **Geometry Nodes modifier inputs:** `md["Socket_1"] = v` raises in 5.x; use `md.properties.inputs.Socket_1.value = v` (+ `obj.update_tag()`); see `ink.set_modifier_input`.
- `obj.matrix_world` is stale right after creating/moving objects in a script -> `context.view_layer.update()` before reading it.
- Light Path "Is Camera Ray" works in the EEVEE world shader (camera sees the inked sky, lighting sees a flat ambient).
- Freestyle still exists (`scene.render.use_freestyle`) but is unused.
- Live bridge: Blender 5.x needs **Preferences > System > Network > Allow Online Access** ON, then Preferences > Add-ons > MCP > **Start MCP Bridge Server** (port 9876).

## Layout
```
procedural_worlds/        the add-on package (zip this folder to install)
  __init__.py             bl_info, PropertyGroup, operators (generate / random seed), panel
  core.py                 collection mgmt + purge, fbm noise, material helpers, mood lighting, camera, render setup, generate()
  ink.py                  ink style: toon group, wobble GN group, Line Art outlines, inked sky world, compositor
  scenes.py               REGISTRY only
  scene_island.py         coastal island generator
  scene_kitchen.py        kitchen interior generator
  scene_alley.py          cyberpunk alley generator
tools/blender.sh          headless Blender wrapper (see above)
tools/smoke_test.py       one EEVEE ink render + invariant asserts
tools/grid.py             seed x mood grid + contact sheet
tools/check_invariants.py determinism / leak / naming check
tools/hero.py             1920x1080 full-quality JPEG heroes -> renders/hero/
renders/                  output stills (png gitignored except renders/hero/)
```

## Contracts
- A scene generator is a class with `LABEL` and `build(col, seed, size, detail, height, mood="GOLDEN", **kw) -> dict`. It must add ALL objects to `col` (collection `PW_Generated`), name them `PW_*`, be deterministic for a seed (`random.Random(seed)` only), and returns info: `camera` (`target`, `distance`, `height`, `angle`, `lens`, or explicit `location`; `clip_end`, `shift_y`), optional `sun_dir=(elev_deg, azim_deg)`, `sun_scale`, `sky_scale`, `ink={line_scale, wobble, grime, hatch, sea_color, ao_distance}`. Register it in `scenes.REGISTRY`; the panel enum picks it up.
- `core.generate(..., ink=True)` clears previous `PW_*` objects + purges zero-user `PW_*` datablocks, builds, applies mood lighting (DAY/GOLDEN/DUSK/NIGHT, `core.MOODS`), camera, then `ink.apply()` and render setup (ink forces `BLENDER_EEVEE` + Standard view transform). `ink=False` strips ink nodes and renders realistic (Cycles/AgX by default).
- Ink hints: `obj["pw_line"]=0` (no outlines), `obj["pw_wonk"]` (wobble multiplier, 0 = off), `mat["pw_flat"]=1` (flat unlit), `mat["pw_hatch"]`, `mat["pw_grime"]`, `mat["pw_ink_custom"]=1` (material authored for ink already; untouched). Materials with Emission Strength > 0 become flat bright "neon ink" (>= 2 also blooms).
- How ink converts materials: keeps the original node tree, inserts group `PW_InkToon` fed by whatever drives the Principled Base Color, relinks the output (original link remembered in `mat["pw_ink_orig"]`, restored by `ink.remove()`).

## How to verify (do this loop)
1. Change code, render (`tools/grid.py` for the seed x mood sheet, smoke test for a single frame).
2. LOOK at the image next to `reference/ink_style_ref.png`; write a 3-line critique (reads hand-drawn? worst issue? next fix?); fix it. "No errors" is not success.
3. `tools/check_invariants.py` before committing.

## Roadmap (in order)
1. ~~Ink style module~~ (done).
2. ~~Coastal island hero quality~~ (done).
3. Kitchen interior showpiece (2 hero renders). 4. Cyberpunk alley (2 hero renders).
5. Camera fly-through operator + low-res MP4; lines boil every 2 frames (GP noise `use_random`, compositor wobble keyed to frame).
6. Panel presets incl. Ink/Realistic toggle, `blender_manifest.toml`, README with hero renders; reinstall into the user add-ons folder.

## Conventions
- No external deps; pure `bpy`/`bmesh`/`mathutils` (+ numpy only in tools). Everything procedural, no image textures.
- Commit messages short and imperative. Don't commit large renders (>2 MB); keep hero renders in `renders/hero/`.
