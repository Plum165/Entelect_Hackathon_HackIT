#!/usr/bin/env python3
"""
Entelect University Cup 2 / HackIT - Level 2 Solver
===================================================
World Size: 70 x 100 (7000 cells) | Ticks: 500
Strategy:
- Disjoint spatial coordinate offsets to prevent "plant already occupies cell" collisions.
- Spring Year 1 Bootstrap (Ticks 0..5): Dispersed epicenters across all quadrants.
- Summer/Autumn Refresh (Ticks 100, 200): Disjoint intermediate coordinates.
- Spring Year 2 Massive Reseeding (Ticks 400..450): Guarantees dense, mature coverage at tick 500.
"""

import json
import math
import os
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "2.json"
FALLBACK_INPUT_FILE = "1.json"
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
        os.path.join(os.getcwd(), "Level_2", filename),
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

    # 1. Load Level 2 Map
    input_path = resolve_path(INPUT_FILE)
    if not os.path.exists(input_path):
        input_path = resolve_path(FALLBACK_INPUT_FILE)

    input_data = load_json(input_path)
    rows = int(input_data.get("rows", 70))
    cols = int(input_data.get("cols", 100))
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

    print(f"[+] Loaded Level 2: {rows}x{cols} grid ({len(cells)} cells, {len(plantable)} plantable).")

    # 2. Identify Valid Starting Plants (no unlock conditions)
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
        unlocked_plants = [PlantInfo(index=1, name="Grass", spread_rate=0.4, preferred_soil=[1, 2])]

    print(f"[+] Valid Starting Species ({len(unlocked_plants)}): {[p.name for p in unlocked_plants]}")

    actions = []
    used_positions: Set[Tuple[int, int]] = set()

    # -------------------------------------------------------------------------
    # Helper: schedule a wave using a disjoint grid offset
    # -------------------------------------------------------------------------
    def schedule_wave(
        start_tick: int,
        max_ticks_for_wave: int,
        stride_r: int,
        stride_c: int,
        offset_r: int,
        offset_c: int,
        species_weights: Dict[int, float],
    ):
        nonlocal actions, used_positions
        candidate_coords = []
        for r in range(offset_r, rows - 1, stride_r):
            for c in range(offset_c, cols - 1, stride_c):
                if (r, c) in cells and cells[(r, c)].terrain == 0 and (r, c) not in used_positions:
                    candidate_coords.append((r, c))

        random.shuffle(candidate_coords)
        cur_tick = start_tick
        tick_count = 0

        for r, c in candidate_coords:
            cell = cells[(r, c)]

            # Soil match preference
            chosen = None
            for p in unlocked_plants:
                if cell.soil in p.preferred_soil:
                    chosen = p
                    break

            if chosen is None:
                # Weighted pick
                r_val = random.random()
                cum = 0.0
                for p in unlocked_plants:
                    cum += species_weights.get(p.index, 1.0 / len(unlocked_plants))
                    if r_val <= cum:
                        chosen = p
                        break
                if chosen is None:
                    chosen = unlocked_plants[0]

            actions.append({
                "tick": cur_tick,
                "plant_index": chosen.index,
                "row": r,
                "col": c,
            })
            used_positions.add((r, c))
            tick_count += 1

            if tick_count >= MAX_PLANTS_PER_TICK:
                cur_tick += 1
                tick_count = 0
                if cur_tick >= start_tick + max_ticks_for_wave:
                    break

    # Balanced species weight profile
    weights = {}
    for p in unlocked_plants:
        if p.spread_rate >= 0.3:
            weights[p.index] = 0.55  # Fast colonizers (Grass)
        elif p.spread_rate >= 0.15:
            weights[p.index] = 0.30  # Flowers (Rose Bush)
        else:
            weights[p.index] = 0.15  # Anchor trees (Oak)
    tot = sum(weights.values())
    for k in weights:
        weights[k] /= tot

    # -------------------------------------------------------------------------
    # WAVE 1 (Spring Year 1, Ticks 0..4): Grid stride 7, offset (1, 1)
    # -------------------------------------------------------------------------
    schedule_wave(start_tick=0, max_ticks_for_wave=5, stride_r=7, stride_c=7, offset_r=1, offset_c=1, species_weights=weights)

    # -------------------------------------------------------------------------
    # WAVE 2 (Summer Year 1, Ticks 100..103): Grid stride 7, disjoint offset (4, 4)
    # -------------------------------------------------------------------------
    schedule_wave(start_tick=100, max_ticks_for_wave=4, stride_r=7, stride_c=7, offset_r=4, offset_c=4, species_weights=weights)

    # -------------------------------------------------------------------------
    # WAVE 3 (Autumn Year 1, Ticks 200..202): Grid stride 8, disjoint offset (2, 5)
    # -------------------------------------------------------------------------
    schedule_wave(start_tick=200, max_ticks_for_wave=3, stride_r=8, stride_c=8, offset_r=2, offset_c=5, species_weights=weights)

    # -------------------------------------------------------------------------
    # WAVE 4 (Spring Year 2, Ticks 400..430): Post-Winter Massive Bloom
    # Clear used_positions so we repopulate the entire 70x100 grid for peak score at tick 500
    # -------------------------------------------------------------------------
    used_positions.clear()
    schedule_wave(start_tick=400, max_ticks_for_wave=15, stride_r=4, stride_c=4, offset_r=0, offset_c=0, species_weights=weights)
    schedule_wave(start_tick=415, max_ticks_for_wave=15, stride_r=4, stride_c=4, offset_r=2, offset_c=2, species_weights=weights)

    # Group actions by tick
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

    print(f"\n[+] Successfully generated Level 2 submission:")
    print(f"    - File: {output_path}")
    print(f"    - Total Actions Scheduled: {len(actions)}")
    print(f"    - Active Ticks: {len(submission['actions'])}")
    print(f"    - Spring Year 2 Seeding (Ticks 400-445): {sum(len(v) for k, v in grouped.items() if k >= 400)} plants")


if __name__ == "__main__":
    main()