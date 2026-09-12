#!/usr/bin/env python3
"""
Entelect University Cup 2 / HackIT - Level 1 Solver (Continuous Seasonal Edition)
================================================================================
Fixes:
- Continuous planting across seasons to prevent Winter extinction.
- Massive Spring re-bloom (ticks 400-485) ensuring dense live coverage at tick 500.
- High capacity utilization (hundreds of plants placed on preferred soils).
"""

import json
import math
import os
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


INPUT_FILE = "1.json"
OUTPUT_FILE = "submission.json"
RANDOM_SEED = 42
MAX_PLANTS_PER_TICK = 20


@dataclass
class Cell:
    row: int
    col: int
    terrain: int = 0
    soil: int = 1


@dataclass
class PlantInfo:
    index: int
    name: str
    spread_rate: float = 0.0
    spread_range: float = 0.0
    preferred_soil: List[int] = field(default_factory=list)


def resolve_path(filename: str) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(current_dir, filename),
        os.path.join(current_dir, "..", "additional-resources", filename),
        os.path.join(current_dir, "additional-resources", filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.getcwd(), "additional-resources", filename),
        os.path.join(os.getcwd(), "Level_1", filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return os.path.join(current_dir, filename)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    random.seed(RANDOM_SEED)

    # 1. Load Grid
    input_path = resolve_path(INPUT_FILE)
    input_data = load_json(input_path)
    rows = int(input_data.get("rows", 50))
    cols = int(input_data.get("cols", 50))
    ticks = int(input_data.get("ticks", 500))

    cells = {}
    for raw in input_data.get("cells", []):
        r, c = int(raw["row"]), int(raw["col"])
        cells[(r, c)] = Cell(
            row=r,
            col=c,
            terrain=int(raw.get("terrain", 0)),
            soil=int(raw.get("soil", 1)),
        )

    plantable = [pos for pos, cell in cells.items() if cell.terrain == 0]
    if not plantable:
        plantable = list(cells.keys())

    # 2. Load Plant Dataset & Find Unlocked Starting Species
    plants_data = load_json(resolve_path("plant_dataset.json"))
    unlocks_data = load_json(resolve_path("plant_unlock_conditions.json"))

    locked_names = {entry["plant"] for entry in unlocks_data if "plant" in entry}

    unlocked_plants: List[PlantInfo] = []
    for raw in plants_data:
        idx = int(raw["index"])
        name = str(raw["plant"])
        growth = raw.get("growth", {})
        preferred_soil = [
            int(s) for s in raw.get("preferred_soil", [])
            if isinstance(s, (int, str)) and str(s).isdigit()
        ]

        if name not in locked_names:
            unlocked_plants.append(PlantInfo(
                index=idx,
                name=name,
                spread_rate=float(growth.get("spread_rate", 0.0)),
                spread_range=float(growth.get("spread_range", 0.0)),
                preferred_soil=preferred_soil,
            ))

    if not unlocked_plants:
        # Fallback to base Grass
        unlocked_plants = [PlantInfo(index=1, name="Grass", spread_rate=0.4, preferred_soil=[1, 2])]

    print(f"[*] Starting Species Available ({len(unlocked_plants)}): {[p.name for p in unlocked_plants]}")

    # 3. Multi-Season Continuous Planting Schedule
    # - Wave 1 (Spring Year 1): Ticks 0..8
    # - Wave 2 (Summer Year 1): Ticks 100..106
    # - Wave 3 (Autumn Year 1): Ticks 200..204
    # - Wave 4 (Spring Year 2 - Heavy Bloom): Ticks 400..435 (Dense final population)
    planting_ticks = (
        list(range(0, 9)) +
        list(range(100, 107)) +
        list(range(200, 205)) +
        list(range(400, 436))
    )

    actions = []
    used_positions: Set[Tuple[int, int]] = set()

    for tick in planting_ticks:
        if tick >= ticks:
            break

        # In Spring Year 2 (tick 400+), reset used_positions to replant over winter-dead ground
        if tick == 400:
            used_positions.clear()

        # Pick plantable positions
        available = [p for p in plantable if p not in used_positions]
        if not available:
            used_positions.clear()
            available = plantable

        random.shuffle(available)
        batch = available[:MAX_PLANTS_PER_TICK]

        for r, c in batch:
            cell = cells[(r, c)]
            # Match preferred soil
            chosen = next((p for p in unlocked_plants if cell.soil in p.preferred_soil), unlocked_plants[0])
            
            actions.append({
                "tick": tick,
                "plant_index": chosen.index,
                "row": r,
                "col": c,
            })
            used_positions.add((r, c))

    # 4. Group by tick and write submission.json
    grouped = defaultdict(list)
    for a in actions:
        grouped[a["tick"]].append({
            "plant_index": a["plant_index"],
            "row": a["row"],
            "col": a["col"],
        })

    submission = {
        "actions": [
            {"tick": t, "plants": grouped[t]}
            for t in sorted(grouped.keys())
        ]
    }

    output_path = os.path.join(os.path.dirname(input_path), OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"[+] Successfully wrote {len(actions)} actions across {len(grouped)} ticks to {output_path}")


if __name__ == "__main__":
    main()