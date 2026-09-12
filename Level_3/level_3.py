#!/usr/bin/env python3
"""
Entelect University Cup 2 / HackIT - Level 3 Grand Master Solver
================================================================
World Size: 150 x 150 (22,500 cells, 1253 plantable) | Ticks: 800
Max Actions: 20 plants/tick
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

INPUT_FILE = "3.json"
FALLBACK_INPUT = "2.json"
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
# PATH RESOLUTION & DATA LOADERS
# ============================================================

def resolve_path(filename: str) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(current_dir, filename),
        os.path.join(current_dir, "..", "additional-resources", filename),
        os.path.join(current_dir, "additional-resources", filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.getcwd(), "additional-resources", filename),
        os.path.join(os.getcwd(), "Level_3", filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return os.path.join(current_dir, filename)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_plant_catalogue() -> Dict[str, PlantInfo]:
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
        catalogue[name] = PlantInfo(
            index=idx,
            name=name,
            time_to_maturity=float(growth.get("time_to_maturity", 1.0)),
            spread_rate=float(growth.get("spread_rate", 0.0)),
            spread_range=float(growth.get("spread_range", 0.0)),
            preferred_soil=preferred_soil,
        )
    return catalogue


# ============================================================
# SMART SOIL & TERRAIN ALLOCATOR
# ============================================================

def allocate_wave(
    tick: int,
    species_requests: List[Tuple[PlantInfo, int]],
    cells: Dict[Tuple[int, int], Cell],
    plantable_coords: List[Tuple[int, int]],
    occupied_positions: Set[Tuple[int, int]],
) -> List[Dict[str, Any]]:
    actions = []
    
    # Bucket open plantable cells by soil type
    soil_buckets = defaultdict(list)
    for pos in plantable_coords:
        if pos not in occupied_positions:
            soil_buckets[cells[pos].soil].append(pos)

    for bucket in soil_buckets.values():
        random.shuffle(bucket)

    for plant, count in species_requests:
        allocated = 0
        
        # 1. Match preferred soil
        for s_id in plant.preferred_soil:
            bucket = soil_buckets[s_id]
            while bucket and allocated < count and len(actions) < MAX_PLANTS_PER_TICK:
                pos = bucket.pop()
                if pos in occupied_positions:
                    continue
                actions.append({
                    "tick": tick,
                    "plant_index": plant.index,
                    "row": pos[0],
                    "col": pos[1],
                })
                occupied_positions.add(pos)
                allocated += 1

        # 2. Fallback to open plantable soil
        if allocated < count and len(actions) < MAX_PLANTS_PER_TICK:
            for s_id, bucket in soil_buckets.items():
                while bucket and allocated < count and len(actions) < MAX_PLANTS_PER_TICK:
                    pos = bucket.pop()
                    if pos in occupied_positions:
                        continue
                    actions.append({
                        "tick": tick,
                        "plant_index": plant.index,
                        "row": pos[0],
                        "col": pos[1],
                    })
                    occupied_positions.add(pos)
                    allocated += 1

        if len(actions) >= MAX_PLANTS_PER_TICK:
            break

    return actions


# ============================================================
# MASTER LEVEL 3 SOLVER
# ============================================================

def solve():
    random.seed(RANDOM_SEED)

    # 1. Load Level 3 Map (150x150)
    input_file = resolve_path(INPUT_FILE)
    if not os.path.exists(input_file):
        input_file = resolve_path(FALLBACK_INPUT)

    input_data = load_json(input_file)
    rows = int(input_data.get("rows", 150))
    cols = int(input_data.get("cols", 150))
    ticks = int(input_data.get("ticks", 800))

    cells = {}
    for raw in input_data.get("cells", []):
        r, c = int(raw["row"]), int(raw["col"])
        cells[(r, c)] = Cell(
            row=r,
            col=c,
            terrain=int(raw.get("terrain", 0)),
            soil=int(raw.get("soil", 0)),
        )

    # Strictly filter plantable soil (terrain == 0)
    plantable = [pos for pos, cell in cells.items() if cell.terrain == 0]
    if not plantable:
        plantable = list(cells.keys())

    print(f"[+] Loaded Level 3: {rows}x{cols} grid ({len(plantable)} plantable cells), {ticks} ticks.")

    # 2. Load Plant Dataset
    plants = get_plant_catalogue()

    # Base Species
    grass = plants.get("Grass", PlantInfo(1, "Grass", preferred_soil=[0, 1]))
    rose = plants.get("Rose Bush", PlantInfo(2, "Rose Bush", preferred_soil=[0, 2]))
    sunflower = plants.get("Dwarf Sunflower", PlantInfo(3, "Dwarf Sunflower", preferred_soil=[2]))
    lavender = plants.get("Lavender", PlantInfo(4, "Lavender", preferred_soil=[0, 1]))
    oak = plants.get("Oak Tree", PlantInfo(5, "Oak Tree", preferred_soil=[0, 2]))

    # Unlocked Species Pool
    blue_moss = plants.get("Blue Moss", PlantInfo(6, "Blue Moss", preferred_soil=[1, 2]))
    orange_blossom = plants.get("Orange Blossom", PlantInfo(7, "Orange Blossom", preferred_soil=[0]))
    golden_fern = plants.get("Golden Fern", PlantInfo(9, "Golden Fern", preferred_soil=[2]))
    dahlia = plants.get("Sunburst Dahlia", PlantInfo(10, "Sunburst Dahlia", preferred_soil=[0, 1]))
    thornberry = plants.get("Thornberry Bush", PlantInfo(11, "Thornberry Bush", preferred_soil=[0, 2]))
    twilight = plants.get("Twilight Bloom", PlantInfo(12, "Twilight Bloom", preferred_soil=[2]))
    stonepine = plants.get("Stonepine", PlantInfo(13, "Stonepine", preferred_soil=[2]))
    luminescent_fungi = plants.get("Luminescent Fungi", PlantInfo(14, "Luminescent Fungi", preferred_soil=[1, 3]))
    emberleaf = plants.get("Emberleaf", PlantInfo(15, "Emberleaf", preferred_soil=[0, 3]))
    deeproot_fern = plants.get("Deeproot Fern", PlantInfo(17, "Deeproot Fern", preferred_soil=[2]))
    purple_canopy = plants.get("Purple Canopy Tree", PlantInfo(24, "Purple Canopy Tree", preferred_soil=[0]))

    all_actions = []
    occupied_positions: Set[Tuple[int, int]] = set()

    # -------------------------------------------------------------------------
    # PHASE 1: MASSIVE ECOSYSTEM BOOTSTRAP (Ticks 0 .. 30)
    # -------------------------------------------------------------------------
    for tick in range(0, 31):
        if tick % 4 == 0:
            quota = [(grass, 12), (lavender, 8)]
        elif tick % 4 == 1:
            quota = [(sunflower, 12), (rose, 8)]
        elif tick % 4 == 2:
            quota = [(grass, 10), (sunflower, 10)]
        else:
            quota = [(oak, 4), (lavender, 8), (rose, 8)]

        acts = allocate_wave(tick, quota, cells, plantable, occupied_positions)
        all_actions.extend(acts)

    # -------------------------------------------------------------------------
    # PHASE 2: SUMMER REINFORCEMENTS & TIER 2 SOWING (Ticks 150 .. 170)
    # -------------------------------------------------------------------------
    tier2_species = [blue_moss, orange_blossom, golden_fern, dahlia, thornberry, stonepine, luminescent_fungi]
    for tick in range(150, 171):
        quota = [(p, 3) for p in tier2_species]
        acts = allocate_wave(tick, quota, cells, plantable, occupied_positions)
        all_actions.extend(acts)

    # -------------------------------------------------------------------------
    # PHASE 3: AUTUMN CANOPY & HARDY ADVANCEMENT (Ticks 300 .. 320)
    # -------------------------------------------------------------------------
    tier3_species = [purple_canopy, twilight, deeproot_fern, emberleaf, stonepine, oak]
    for tick in range(300, 321):
        quota = [(p, 4) for p in tier3_species]
        acts = allocate_wave(tick, quota, cells, plantable, occupied_positions)
        all_actions.extend(acts)

    # -------------------------------------------------------------------------
    # PHASE 4: YEAR 2 SPRING BIODIVERSITY (Ticks 450 .. 470)
    # -------------------------------------------------------------------------
    mid_species = [blue_moss, orange_blossom, golden_fern, dahlia, purple_canopy]
    for tick in range(450, 471):
        quota = [(p, 4) for p in mid_species]
        acts = allocate_wave(tick, quota, cells, plantable, occupied_positions)
        all_actions.extend(acts)

    # -------------------------------------------------------------------------
    # PHASE 5: THE GRAND GOLDEN HARVEST (Ticks 715 .. 792)
    # -------------------------------------------------------------------------
    occupied_positions.clear()  # Reclaim all plantable cells

    grand_species_pool = [
        grass,
        rose,
        sunflower,
        lavender,
        oak,
        blue_moss,
        orange_blossom,
        golden_fern,
        dahlia,
        thornberry,
        twilight,
        stonepine,
        luminescent_fungi,
        emberleaf,
        deeproot_fern,
        purple_canopy,
    ]

    species_by_idx = {p.index: p for p in grand_species_pool}
    species_indices = [p.index for p in grand_species_pool]
    num_species = len(species_indices)
    cycle_idx = 0

    for tick in range(715, 793):
        # Count quota by index to prevent unhashable PlantInfo error
        idx_counts = defaultdict(int)
        for _ in range(MAX_PLANTS_PER_TICK):
            s_idx = species_indices[cycle_idx % num_species]
            idx_counts[s_idx] += 1
            cycle_idx += 1

        quota = [(species_by_idx[i], count) for i, count in idx_counts.items()]
        acts = allocate_wave(tick, quota, cells, plantable, occupied_positions)
        all_actions.extend(acts)

        if len(occupied_positions) >= len(plantable) - 20:
            occupied_positions.clear()

    # -------------------------------------------------------------------------
    # ENCODE SUBMISSION JSON
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

    print(f"\n[+] Level 3 Optimization Complete!")
    print(f"    - Submission File: {output_path}")
    print(f"    - Total Scheduled Actions: {len(all_actions)}")
    print(f"    - Active Planting Ticks: {len(submission['actions'])}")
    print(f"    - Grand Harvest Living Batch (Ticks 715-792): {sum(len(v) for k, v in grouped.items() if k >= 715)} plants")


if __name__ == "__main__":
    solve()