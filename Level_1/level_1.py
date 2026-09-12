#!/usr/bin/env python3
"""
Entelect University Cup 2 / HackIT - Level 1 Solver
===================================================
Optimized for PlantSim simulation mechanics:
- Dynamically resolves starting unlocked species from plant_unlock_conditions.json.
- Disperses seed nodes across the 50x50 grid on preferred soils to maximize spread expansion.
- Balances species distribution to maximize total coverage and entropy diversity score.
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

INPUT_FILE = "1.json"
OUTPUT_FILE = "submission.json"

RANDOM_SEED = 42
MAX_PLANTS_PER_TICK = 20


# ============================================================
# DATA STRUCTURES
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
# FILE HELPERS
# ============================================================

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


# ============================================================
# PARSING
# ============================================================

def parse_input(data: Dict[str, Any]) -> Tuple[int, int, int, Dict[Tuple[int, int], Cell]]:
    rows = int(data.get("rows", 50))
    cols = int(data.get("cols", 50))
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
        preferred_soil = [int(s) for s in raw.get("preferred_soil", []) if isinstance(s, (int, str)) and str(s).isdigit()]

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
    """
    Identifies plants that are unconditionally available at tick 0.
    A plant is starting if it has no required condition entry in plant_unlock_conditions.json.
    """
    locked_plant_names = {entry["plant"] for entry in unlock_data if "plant" in entry}
    
    unlocked = [p for p in plants.values() if p.name not in locked_plant_names]
    
    # Fallback to base Grass (1) and Rose Bush (2) if all have entries
    if not unlocked:
        unlocked = [p for p in plants.values() if p.index in (1, 2)]
        
    return unlocked


# ============================================================
# SPATIAL DISPERSION & PLACEMENT ENGINE
# ============================================================

def plan_optimal_garden(
    rows: int,
    cols: int,
    ticks: int,
    cells: Dict[Tuple[int, int], Cell],
    unlocked_plants: List[PlantInfo],
) -> List[Action]:
    """
    Generates high-spread seed distribution:
    1. Filters confirmed plantable cells (terrain == 0).
    2. Groups plantable cells by soil type.
    3. Allocates seeds using Poisson-like distance dispersion to maximize expansion area.
    4. Distributes actions across early ticks respecting MAX_PLANTS_PER_TICK.
    """
    plantable_cells = [c for c in cells.values() if c.terrain == 0]
    if not plantable_cells:
        # Fallback: treat all cells as plantable if terrain IDs are homogeneous
        plantable_cells = list(cells.values())

    actions: List[Action] = []
    used_positions: Set[Tuple[int, int]] = set()

    # Sort unlocked plants by spread potential
    unlocked_plants.sort(key=lambda p: (p.spread_rate, p.spread_range), reverse=True)
    
    print(f"[*] Available Starting Species ({len(unlocked_plants)}):")
    for p in unlocked_plants:
        print(f"    - Index {p.index:2d}: {p.name:<18} (Spread Rate: {p.spread_rate}, Range: {p.spread_range})")

    # Define target species allocation weights
    # Give primary weight to high spreaders (e.g. Grass / index 1) with balanced diversity nodes
    weights: Dict[int, float] = {}
    for p in unlocked_plants:
        if p.spread_rate >= 0.3:
            weights[p.index] = 0.50  # Fast colonizers
        elif p.spread_rate >= 0.15:
            weights[p.index] = 0.30  # Secondary spreaders
        else:
            weights[p.index] = 0.20  # Anchors / Trees

    # Normalize weights
    total_w = sum(weights.values())
    for idx in weights:
        weights[idx] /= total_w

    # Create uniform dispersion grid
    # A regular stride across 50x50 ensures non-overlapping seed nodes
    stride = 3
    candidate_grid = []
    for r in range(1, rows - 1, stride):
        for c in range(1, cols - 1, stride):
            if (r, c) in cells and cells[(r, c)].terrain == 0:
                candidate_grid.append((r, c))

    random.shuffle(candidate_grid)

    current_tick = 0
    tick_action_count = 0

    # Plant candidate dispersion nodes
    for r, c in candidate_grid:
        if (r, c) in used_positions:
            continue

        cell = cells[(r, c)]
        
        # Pick the best unlocked species that prefers this soil
        best_plant = None
        for p in unlocked_plants:
            if cell.soil in p.preferred_soil:
                best_plant = p
                break
        
        # Fallback to weighted random choice among unlocked
        if best_plant is None:
            r_val = random.random()
            cum = 0.0
            for p in unlocked_plants:
                cum += weights[p.index]
                if r_val <= cum:
                    best_plant = p
                    break
            if best_plant is None:
                best_plant = unlocked_plants[0]

        actions.append(Action(
            tick=current_tick,
            plant_index=best_plant.index,
            row=r,
            col=c,
        ))
        used_positions.add((r, c))
        tick_action_count += 1

        if tick_action_count >= MAX_PLANTS_PER_TICK:
            current_tick += 1
            tick_action_count = 0
            if current_tick >= min(ticks, 50):
                break

    return actions


# ============================================================
# SUBMISSION FORMATTER
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
# MAIN PIPELINE
# ============================================================

def main():
    random.seed(RANDOM_SEED)

    # 1. Load Input Grid
    input_path = resolve_path(INPUT_FILE)
    input_data = load_json(input_path)
    rows, cols, ticks, cells = parse_input(input_data)
    print(f"[+] Loaded Level: {rows}x{cols} grid, {ticks} ticks, {len(cells)} cells.")

    # 2. Load Resources
    plants_data = load_json(resolve_path("plant_dataset.json"))
    unlocks_data = load_json(resolve_path("plant_unlock_conditions.json"))
    
    plants = parse_plants(plants_data)
    unlocked_at_start = get_unlocked_plants_at_start(plants, unlocks_data)

    # 3. Generate Spatial Plan
    actions = plan_optimal_garden(
        rows=rows,
        cols=cols,
        ticks=ticks,
        cells=cells,
        unlocked_plants=unlocked_at_start,
    )

    # 4. Format & Write Submission
    submission = format_submission(actions)
    output_path = os.path.join(os.path.dirname(input_path), OUTPUT_FILE)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"[+] Saved valid submission to: {output_path}")
    print(f"[+] Total Scheduled Actions: {len(actions)}")
    print(f"[+] Ticks Utilized: {len(submission['actions'])} (max {MAX_PLANTS_PER_TICK} actions/tick)")


if __name__ == "__main__":
    main()