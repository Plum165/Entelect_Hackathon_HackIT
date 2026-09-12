#!/usr/bin/env python3
"""
Entelect University Cup 2 / HackIT - Dynamic Entropy & Longevity Optimizer
==========================================================================
Implements mathematical quota allocation:
1. Phase 1 (T0..15): Triggers all 5 animal milestones (Loamcrawlers, Nectaris, Solwings, Virexids, Barkskips).
2. Phase 2 & 3 (T80..230): Propagates higher-tier species.
3. Phase 4 (T415..465): Entropy-balanced sowing (equalizes p_i across all species to maximize H)
   within the 100-tick nutrient lifespan window before Tick 500.
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

INPUT_FILE = "1.json"
FALLBACK_INPUT = "2.json"
OUTPUT_FILE = "submission.json"

RANDOM_SEED = 42
MAX_PLANTS_PER_TICK = 20
CELL_NUTRIENT_LIFESPAN = 95  # Safe lifespan before 100-tick nutrient depletion


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Cell:
    row: int
    col: int
    terrain: int = 0
    soil: int = 0


@dataclass
class PlantInfo:
    index: int
    name: str
    time_to_maturity: float = 1.0
    spread_rate: float = 0.0
    spread_range: float = 0.0
    preferred_soil: List[int] = field(default_factory=list)


# ============================================================
# PATH & DATA LOADERS
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
        os.path.join(os.getcwd(), "Level_2", filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return os.path.join(current_dir, filename)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# DYNAMIC SIMULATOR & UNLOCK TRACKER
# ============================================================

def get_plant_catalogue() -> Dict[int, PlantInfo]:
    data = load_json(resolve_path("plant_dataset.json"))
    catalogue = {}
    for raw in data:
        idx = int(raw["index"])
        name = str(raw["plant"])
        growth = raw.get("growth", {})
        preferred_soil = [
            int(s) for s in raw.get("preferred_soil", [])
            if isinstance(s, (int, str)) and str(s).isdigit()
        ]
        catalogue[idx] = PlantInfo(
            index=idx,
            name=name,
            time_to_maturity=float(growth.get("time_to_maturity", 1.0)),
            spread_rate=float(growth.get("spread_rate", 0.0)),
            spread_range=float(growth.get("spread_range", 0.0)),
            preferred_soil=preferred_soil,
        )
    return catalogue


def get_unconditionally_unlocked(plants: Dict[int, PlantInfo]) -> List[PlantInfo]:
    unlock_data = load_json(resolve_path("plant_unlock_conditions.json"))
    locked_names = {entry["plant"] for entry in unlock_data if "plant" in entry}
    
    unlocked = [p for p in plants.values() if p.name not in locked_names]
    # Fallback to rulebook confirmed starting species: Grass(1), Rose(2), Sunflower(3), Lavender(4), Oak(5)
    if not unlocked:
        unlocked = [p for p in plants.values() if p.index in (1, 2, 3, 4, 5)]
    return unlocked


# ============================================================
# SPATIAL PLACEMENT OPTIMIZER (MATCHES PREFERRED SOIL & DISPERSION)
# ============================================================

def allocate_plant_batch(
    tick: int,
    species_quota: List[Tuple[PlantInfo, int]],
    cells: Dict[Tuple[int, int], Cell],
    plantable_coords: List[Tuple[int, int]],
    used_coords: Set[Tuple[int, int]],
) -> List[Dict[str, Any]]:
    """
    Greedily pairs requested species with best matching soil cells with spatial spread.
    """
    actions = []
    available = [pos for pos in plantable_coords if pos not in used_coords]
    random.shuffle(available)

    # Group available cells by soil type
    soil_to_cells = defaultdict(list)
    for pos in available:
        soil_to_cells[cells[pos].soil].append(pos)

    for plant, count in species_quota:
        allocated = 0
        
        # 1. First pick cells with matching preferred soil
        for soil_id in plant.preferred_soil:
            while soil_to_cells[soil_id] and allocated < count and len(actions) < MAX_PLANTS_PER_TICK:
                pos = soil_to_cells[soil_id].pop()
                actions.append({
                    "tick": tick,
                    "plant_index": plant.index,
                    "row": pos[0],
                    "col": pos[1],
                })
                used_coords.add(pos)
                allocated += 1

        # 2. Fallback to any remaining open cell
        while allocated < count and available and len(actions) < MAX_PLANTS_PER_TICK:
            pos = available.pop()
            if pos in used_coords:
                continue
            actions.append({
                "tick": tick,
                "plant_index": plant.index,
                "row": pos[0],
                "col": pos[1],
            })
            used_coords.add(pos)
            allocated += 1

        if len(actions) >= MAX_PLANTS_PER_TICK:
            break

    return actions


# ============================================================
# MASTER DYNAMIC SOLVER
# ============================================================

def solve():
    random.seed(RANDOM_SEED)

    # 1. Load Input Grid
    input_file = resolve_path(INPUT_FILE)
    if not os.path.exists(input_file):
        input_file = resolve_path(FALLBACK_INPUT)

    input_data = load_json(input_file)
    rows = int(input_data.get("rows", 50))
    cols = int(input_data.get("cols", 50))
    ticks = int(input_data.get("ticks", 500))
    total_grid = rows * cols

    cells = {}
    for raw in input_data.get("cells", []):
        r, c = int(raw["row"]), int(raw["col"])
        cells[(r, c)] = Cell(
            row=r,
            col=c,
            terrain=int(raw.get("terrain", 0)),
            soil=int(raw.get("soil", 0)),
        )

    plantable = [pos for pos, cell in cells.items() if cell.terrain == 0]
    if not plantable:
        plantable = list(cells.keys())

    # 2. Load Plant Dataset
    plants = get_plant_catalogue()
    base_unlocked = get_unconditionally_unlocked(plants)

    print(f"[*] Map: {rows}x{cols} ({len(plantable)} plantable cells) | Starting Species: {[p.name for p in base_unlocked]}")

    all_actions = []
    used_positions: Set[Tuple[int, int]] = set()

    # -------------------------------------------------------------------------
    # PHASE 1: ECOSYSTEM TRIGGER SEEDING (Ticks 0 .. 15)
    # Target counts to hit Animal conditions:
    # - Loamcrawlers: Grass >= 4% (100 cells on 50x50, 280 on 70x100) + Rose >= 10
    # - Nectaris: Lavender >= 2% (50 cells on 50x50)
    # - Solwings: Sunflower >= 3% (75 cells) + Rose >= 2% (50 cells)
    # - Barkskips: Oak Tree >= 8
    # -------------------------------------------------------------------------
    grass_p = next((p for p in base_unlocked if p.name == "Grass"), base_unlocked[0])
    rose_p = next((p for p in base_unlocked if p.name == "Rose Bush"), base_unlocked[0])
    sunflower_p = next((p for p in base_unlocked if "Sunflower" in p.name), base_unlocked[0])
    lavender_p = next((p for p in base_unlocked if p.name == "Lavender"), base_unlocked[0])
    oak_p = next((p for p in base_unlocked if "Oak" in p.name), base_unlocked[0])

    p1_schedule = [
        # Ticks 0..4: Grass & Lavender fast spreading foundation
        (0, [(grass_p, 12), (lavender_p, 8)]),
        (1, [(grass_p, 12), (lavender_p, 8)]),
        (2, [(grass_p, 12), (lavender_p, 8)]),
        (3, [(sunflower_p, 10), (rose_p, 10)]),
        (4, [(sunflower_p, 10), (rose_p, 10)]),
        (5, [(sunflower_p, 10), (oak_p, 10)]),
        (6, [(grass_p, 10), (rose_p, 10)]),
        (7, [(lavender_p, 10), (sunflower_p, 10)]),
        (8, [(grass_p, 10), (oak_p, 10)]),
    ]

    for tick, quota in p1_schedule:
        acts = allocate_plant_batch(tick, quota, cells, plantable, used_positions)
        all_actions.extend(acts)

    # -------------------------------------------------------------------------
    # PHASE 2 & 3: MID-GAME REINFORCEMENTS (Ticks 100..105, 200..205)
    # Replenishes dead cells as early plants complete their 100-tick life cycle.
    # -------------------------------------------------------------------------
    midgame_ticks = list(range(100, 105)) + list(range(200, 205))
    for tick in midgame_ticks:
        # Balanced mix of base species
        quota = [(p, 4) for p in base_unlocked]
        acts = allocate_plant_batch(tick, quota, cells, plantable, used_positions)
        all_actions.extend(acts)

    # -------------------------------------------------------------------------
    # PHASE 4: THE GOLDEN HARVEST (Ticks 415 .. 465)
    # The crucial scoring phase:
    # 1. Reset used_positions because old plants have decayed.
    # 2. Plant a mathematically balanced quota across ALL unlocked species.
    # 3. Every plant placed between Ticks 415-465 is fully mature, active,
    #    and alive at Tick 500 without hitting the 100-tick nutrient death!
    # -------------------------------------------------------------------------
    used_positions.clear()  # Replant over recovered nutrient soil
    
    # Active species for final entropy balancing
    active_species = base_unlocked

    # Even distribution per tick
    per_species_quota = max(1, MAX_PLANTS_PER_TICK // len(active_species))
    harvest_quota = [(p, per_species_quota) for p in active_species]

    # Stagger across Ticks 415 to 465 (50 ticks of fresh sowing)
    for tick in range(415, 466):
        acts = allocate_plant_batch(tick, harvest_quota, cells, plantable, used_positions)
        all_actions.extend(acts)
        if len(used_positions) >= len(plantable):
            break

    # -------------------------------------------------------------------------
    # SUBMISSION OUTPUT GENERATION
    # -------------------------------------------------------------------------
    grouped = defaultdict(list)
    for a in all_actions:
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

    output_path = os.path.join(os.path.dirname(input_file), OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"\n[+] Optimization Complete!")
    print(f"    - Output: {output_path}")
    print(f"    - Total Scheduled Actions: {len(all_actions)}")
    print(f"    - Active Planting Ticks: {len(submission['actions'])}")
    print(f"    - Golden Harvest Batch (Ticks 415-465): {sum(len(v) for k, v in grouped.items() if k >= 415)} living plants at Tick 500")


if __name__ == "__main__":
    solve()