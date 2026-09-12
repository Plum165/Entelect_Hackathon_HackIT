#!/usr/bin/env python3
"""
Entelect University Cup 2 / HackIT - Level 2 Solver
===================================================
World Size: 70 x 100 (7000 cells)
Ticks: 500
Features: Seasons (every 100 ticks), Active Animals, Weather Conditions

Strategy:
- Multi-wave cluster planting across 6 map epicenters.
- Preferred soil matching for maximum growth multiplier.
- Dynamic starting unlock resolution (strictly verified against unlock dataset).
- Phased seasonal reinforcement (Spring initial seeding + Summer boost + Autumn anchors).
"""

import json
import math
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "2.json"
FALLBACK_INPUT_FILE = "1.json"
OUTPUT_FILE = "submission.json"

RANDOM_SEED = 42
MAX_PLANTS_PER_TICK = 20


# ============================================================
# DATA CLASSES
# ============================================================

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
    time_to_maturity: float = 1.0
    spread_rate: float = 0.0
    spread_range: float = 0.0
    invasiveness_rank: float = 0.0
    preferred_soil: List[int] = field(default_factory=list)


@dataclass
class Action:
    tick: int
    plant_index: int
    row: int
    col: int


# ============================================================
# PATH RESOLUTION
# ============================================================

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
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# PARSING
# ============================================================

def parse_input(data: Dict[str, Any]) -> Tuple[int, int, int, Dict[Tuple[int, int], Cell]]:
    rows = int(data.get("rows", 70))
    cols = int(data.get("cols", 100))
    ticks = int(data.get("ticks", 500))

    cells = {}
    for raw in data.get("cells", []):
        r = int(raw["row"])
        c = int(raw["col"])
        cells[(r, c)] = Cell(
            row=r,
            col=c,
            terrain=int(raw.get("terrain", 0)),
            soil=int(raw.get("soil", 1)),
        )
    return rows, cols, ticks, cells


def parse_plants(data: List[Dict[str, Any]]) -> Dict[int, PlantInfo]:
    plants = {}
    for raw in data:
        idx = int(raw["index"])
        name = str(raw["plant"])
        growth = raw.get("growth", {})
        preferred_soil = [
            int(s) for s in raw.get("preferred_soil", [])
            if isinstance(s, (int, str)) and str(s).isdigit()
        ]

        plants[idx] = PlantInfo(
            index=idx,
            name=name,
            time_to_maturity=float(growth.get("time_to_maturity", 1.0)),
            spread_rate=float(growth.get("spread_rate", 0.0)),
            spread_range=float(growth.get("spread_range", 0.0)),
            invasiveness_rank=float(growth.get("invasiveness_rank", 0.0)),
            preferred_soil=preferred_soil,
        )
    return plants


def get_unlocked_plants_at_start(
    plants: Dict[int, PlantInfo],
    unlock_data: List[Dict[str, Any]]
) -> List[PlantInfo]:
    """Identifies species with zero prerequisite lock entries."""
    locked_names = {entry["plant"] for entry in unlock_data if "plant" in entry}
    unlocked = [p for p in plants.values() if p.name not in locked_names]

    if not unlocked:
        # Fallback base plants
        unlocked = [p for p in plants.values() if p.index in (1, 2, 5)]

    return unlocked


# ============================================================
# MULTI-WAVE SPATIAL PLANNER
# ============================================================

def plan_level_2(
    rows: int,
    cols: int,
    ticks: int,
    cells: Dict[Tuple[int, int], Cell],
    unlocked_plants: List[PlantInfo],
) -> List[Action]:
    """
    Executes a multi-wave spatial planting strategy:
    Wave 1: Ticks 0-9   (Spring initial colonization across 6 map quadrants)
    Wave 2: Ticks 100-104 (Summer reinforcement in open corridors)
    Wave 3: Ticks 200-203 (Autumn resilient anchor planting)
    """
    plantable = [c for c in cells.values() if c.terrain == 0]
    if not plantable:
        plantable = list(cells.values())

    actions: List[Action] = []
    used_positions: Set[Tuple[int, int]] = set()

    # Categorize species
    fast_spreaders = [p for p in unlocked_plants if p.spread_rate >= 0.3]
    balanced_plants = [p for p in unlocked_plants if 0.15 <= p.spread_rate < 0.3]
    anchor_trees = [p for p in unlocked_plants if p.spread_rate < 0.15]

    # Fallback assignment
    if not fast_spreaders:
        fast_spreaders = unlocked_plants
    if not balanced_plants:
        balanced_plants = unlocked_plants
    if not anchor_trees:
        anchor_trees = unlocked_plants

    # ------------------------------------------------------------
    # WAVE 1: Ticks 0..9 (Initial Spring Epicenters)
    # Stride = 4 over the 70x100 grid gives ~400 candidate nodes
    # ------------------------------------------------------------
    wave1_candidates = []
    stride_r, stride_c = 4, 4
    for r in range(2, rows - 2, stride_r):
        for c in range(2, cols - 2, stride_c):
            if (r, c) in cells and cells[(r, c)].terrain == 0:
                wave1_candidates.append((r, c))

    random.shuffle(wave1_candidates)

    current_tick = 0
    tick_count = 0

    for r, c in wave1_candidates:
        if (r, c) in used_positions:
            continue

        cell = cells[(r, c)]

        # Determine plant type: 55% Fast Spreader (Grass), 30% Balanced (Rose/Flowers), 15% Trees
        roll = random.random()
        if roll < 0.55:
            pool = fast_spreaders
        elif roll < 0.85:
            pool = balanced_plants
        else:
            pool = anchor_trees

        # Best match on soil
        chosen = next((p for p in pool if cell.soil in p.preferred_soil), pool[0])

        actions.append(Action(tick=current_tick, plant_index=chosen.index, row=r, col=c))
        used_positions.add((r, c))
        tick_count += 1

        if tick_count >= MAX_PLANTS_PER_TICK:
            current_tick += 1
            tick_count = 0
            if current_tick >= 10:  # End of Wave 1
                break

    # ------------------------------------------------------------
    # WAVE 2: Ticks 100..104 (Summer Expansion Boost)
    # Target interstitial coordinates between Wave 1 nodes
    # ------------------------------------------------------------
    wave2_candidates = []
    for r in range(4, rows - 4, 5):
        for c in range(4, cols - 4, 5):
            if (r, c) in cells and cells[(r, c)].terrain == 0 and (r, c) not in used_positions:
                wave2_candidates.append((r, c))

    random.shuffle(wave2_candidates)

    current_tick = 100
    tick_count = 0

    for r, c in wave2_candidates:
        if (r, c) in used_positions:
            continue

        cell = cells[(r, c)]
        # Summer favors fast expansion
        pool = fast_spreaders if random.random() < 0.70 else balanced_plants
        chosen = next((p for p in pool if cell.soil in p.preferred_soil), pool[0])

        actions.append(Action(tick=current_tick, plant_index=chosen.index, row=r, col=c))
        used_positions.add((r, c))
        tick_count += 1

        if tick_count >= MAX_PLANTS_PER_TICK:
            current_tick += 1
            tick_count = 0
            if current_tick >= 105:  # 5 ticks of Summer reinforcement
                break

    # ------------------------------------------------------------
    # WAVE 3: Ticks 200..203 (Autumn Deep Anchor Sowing)
    # Plant durable anchors/trees before Winter
    # ------------------------------------------------------------
    wave3_candidates = []
    for r in range(6, rows - 6, 6):
        for c in range(6, cols - 6, 6):
            if (r, c) in cells and cells[(r, c)].terrain == 0 and (r, c) not in used_positions:
                wave3_candidates.append((r, c))

    random.shuffle(wave3_candidates)

    current_tick = 200
    tick_count = 0

    for r, c in wave3_candidates:
        if (r, c) in used_positions:
            continue

        cell = cells[(r, c)]
        pool = anchor_trees if random.random() < 0.60 else balanced_plants
        chosen = next((p for p in pool if cell.soil in p.preferred_soil), pool[0])

        actions.append(Action(tick=current_tick, plant_index=chosen.index, row=r, col=c))
        used_positions.add((r, c))
        tick_count += 1

        if tick_count >= MAX_PLANTS_PER_TICK:
            current_tick += 1
            tick_count = 0
            if current_tick >= 204:  # 4 ticks of Autumn anchors
                break

    return actions


# ============================================================
# SUBMISSION ENCODER
# ============================================================

def format_submission(actions: List[Action]) -> Dict[str, Any]:
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for a in actions:
        grouped[a.tick].append({
            "plant_index": a.plant_index,
            "row": a.row,
            "col": a.col,
        })

    return {
        "actions": [
            {
                "tick": t,
                "plants": grouped[t],
            }
            for t in sorted(grouped.keys())
        ]
    }


# ============================================================
# MAIN
# ============================================================

def main():
    random.seed(RANDOM_SEED)

    # 1. Resolve Input JSON
    input_path = resolve_path(INPUT_FILE)
    if not os.path.exists(input_path):
        input_path = resolve_path(FALLBACK_INPUT_FILE)

    input_data = load_json(input_path)
    rows, cols, ticks, cells = parse_input(input_data)
    print(f"[+] Loaded Level 2: {rows}x{cols} grid ({len(cells)} cells), {ticks} ticks.")

    # 2. Resolve Datasets
    plants_data = load_json(resolve_path("plant_dataset.json"))
    unlocks_data = load_json(resolve_path("plant_unlock_conditions.json"))

    plants = parse_plants(plants_data)
    unlocked_at_start = get_unlocked_plants_at_start(plants, unlocks_data)

    print(f"[+] Valid Starting Species ({len(unlocked_plants := unlocked_at_start)}):")
    for p in unlocked_at_start:
        print(f"    - [{p.index:2d}] {p.name:<18} (Spread: {p.spread_rate}, Range: {p.spread_range})")

    # 3. Plan Actions
    actions = plan_level_2(
        rows=rows,
        cols=cols,
        ticks=ticks,
        cells=cells,
        unlocked_plants=unlocked_at_start,
    )

    # 4. Save Submission
    submission = format_submission(actions)
    output_path = os.path.join(os.path.dirname(input_path), OUTPUT_FILE)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"\n[+] Saved submission to: {output_path}")
    print(f"[+] Total Actions Scheduled: {len(actions)}")
    print(f"[+] Active Ticks Used: {len(submission['actions'])} (Wave 1: T0-9, Wave 2: T100-104, Wave 3: T200-203)")


if __name__ == "__main__":
    main()