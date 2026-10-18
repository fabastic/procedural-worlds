@echo off
rem Walk the story in first person (Godot 4.x). Usage: walk.bat [story-slug]   e.g. walk.bat the-last-watch
rem Uses .tools\godot\Godot*.exe if present, else "godot" on PATH. Build worlds first with tools/build_world.py.
setlocal
set "HERE=%~dp0"
set "GODOT="
for %%f in ("%HERE%.tools\godot\Godot_v*_win64.exe") do set "GODOT=%%f"
if "%GODOT%"=="" set "GODOT=godot"
if "%~1"=="" (
  "%GODOT%" --path "%HERE%godot"
) else (
  "%GODOT%" --path "%HERE%godot" -- --story "%HERE%story_out\%~1\world"
)
