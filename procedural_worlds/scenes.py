"""Scene registry. Each generator is a class with LABEL and
build(col, seed, size, detail, height, mood="GOLDEN", **kw) -> info dict (see CLAUDE.md, Contracts).
Add a new scene: write a module with one class and add it to REGISTRY."""
from .scene_island import CoastalIsland
from .scene_kitchen import Kitchen
from .scene_alley import CyberpunkAlley
from .scene_composed import Composed

REGISTRY = {"COASTAL_ISLAND": CoastalIsland, "KITCHEN": Kitchen, "CYBERPUNK_ALLEY": CyberpunkAlley,
            "COMPOSED": Composed}
