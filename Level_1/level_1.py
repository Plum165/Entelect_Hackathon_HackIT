#!/usr/bin/env python3
"""
Entelect University Cup 2 / HackIT - Master Dynamic Unlock Solver
================================================================
Compatible with Level 1, Level 2, Level 3, and Level 4.

Strategy:
1. True Plant Index Resolution:
   - Grass: 1
   - Rose Bush: 2
   - Dwarf Sunflower: 5
   - Lavender: 6
   - Oak Tree: 12
2. Staged Unlock Progression:
   - Phase 1 (T0..20): Bootstraps animals (Loamcrawlers, Nectaris, Solwings, Virexids, Barkskips).
   - Phase 2 (T100..200): Sows Tier 2 unlocks (Blue Moss [3], Crimson Vine [4], Orange Blossom [7], Stone Reed [11]).
   - Phase 3 (T250..350): Sows Tier 3 unlocks (Purple Canopy [10], Silver Fern [8], Moonpetal [15], Skyvine [20]).
3. The Grand Harvest (Last 85 Ticks before T_end):
   - Sows all unlocked species in exact equal parity to maximize Shannon Entropy H.
   - Sown within the 100-tick nutrient window to guarantee 100% live biomass at final scoring.
"""

import json
import math
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


# ============================================================
# CONFIGURATION
# ============================================================

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
        os.path.join(os.getcwd(), "Level_1", filename),
        os.path.join(os.getcwd(), "Level_2", filename),
        os.path.join(os.getcwd(), "Level_3", filename),
        os.path.join(os.getcwd(), "Level_4", filename),
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
# SMART SOIL & SPATIAL ALLOCATOR
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

        # 2. Fallback to any open plantable soil
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
# MAIN SOLVER LOGIC
# ============================================================

def solve():
    random.seed(RANDOM_SEED)

    # Detect current level input file (1.json, 2.json, 3.json, or 4.json)
    input_file = None
    for candidate in ["1.json", "2.json", "3.json", "4.json"]:
        p = resolve_path(candidate)
        if os.path.exists(p):
            input_file = p
            break

    if input_file is None:
        raise FileNotFoundError("Could not locate any level input JSON (1.json, 2.json, 3.json, 4.json).")

    input_data = load_json(input_file)
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
            soil=int(raw.get("soil", 0)),
        )

    plantable = [pos for pos, cell in cells.items() if cell.terrain == 0]
    if not plantable:
        plantable = list(cells.keys())

    print(f"[+] Loaded {os.path.basename(input_file)}: {rows}x{cols} grid ({len(plantable)} plantable cells), {ticks} ticks.")

    # Load All Plants with exact indices
    plants = get_plant_catalogue()

    # Confirmed 5 Base Species
    grass = plants["Grass"]               # Index 1
    rose = plants["Rose Bush"]            # Index 2
    sunflower = plants["Dwarf Sunflower"] # Index 5
    lavender = plants["Lavender"]         # Index 6
    oak = plants["Oak Tree"]              # Index 12

    # Tier 2 & 3 Unlocks
    blue_moss = plants.get("Blue Moss", PlantInfo(3, "Blue Moss", preferred_soil=[0, 1]))
    crimson_vine = plants.get("Crimson Vine", PlantInfo(4, "Crimson Vine", preferred_soil=[0, 1]))
    orange_blossom = plants.get("Orange Blossom", PlantInfo(7, "Orange Blossom", preferred_soil=[0, 1]))
    silver_fern = plants.get("Silver Fern", PlantInfo(8, "Silver Fern", preferred_soil=[0, 1]))
    purple_canopy = plants.get("Purple Canopy Tree", PlantInfo(10, "Purple Canopy Tree", preferred_soil=[0, 1]))
    stone_reed = plants.get("Stone Reed", PlantInfo(11, "Stone Reed", preferred_soil=[0, 1]))
    moonpetal = plants.get("Moonpetal Lily", PlantInfo(15, "Moonpetal Lily", preferred_soil=[0, 1]))
    skyvine = plants.get("Skyvine", PlantInfo(20, "Skyvine", preferred_soil=[0, 1]))
    living_topiary = plants.get("Living Topiary", PlantInfo(27, "Living Topiary", preferred_soil=[0, 1]))
    worldtree = plants.get("Worldtree Sapling", PlantInfo(31, "Worldtree Sapling", preferred_soil=[0, 1]))

    all_actions = []
    occupied_positions: Set[Tuple[int, int]] = set()

    # Check if level is Level 1 (greenhouse without active animal unlocks)
    is_level_1 = (rows == 50 and cols == 50 and ticks == 500 and "1.json" in input_file)

    if is_level_1:
        # ---------------------------------------------------------------------
        # LEVEL 1 STRATEGY: EXACT 5-WAY PARITY WITH REAL INDICES (1, 2, 5, 6, 12)
        # ---------------------------------------------------------------------
        base_5 = [grass, rose, sunflower, lavender, oak]
        start_tick = 410
        cur_tick = start_tick
        
        # Maximize 5-way parity across the 720 plantable cells
        total_plants = min(len(plantable), 45 * MAX_PLANTS_PER_TICK)
        species_queue = []
        for i in range(total_plants):
            species_queue.append(base_5[i % len(base_5)])
        random.shuffle(species_queue)

        while species_queue and cur_tick < ticks:
            batch = species_queue[:MAX_PLANTS_PER_TICK]
            species_queue = species_queue[MAX_PLANTS_PER_TICK:]

            counts_by_plant = defaultdict(int)
            for p in batch:
                counts_by_plant[p] += 1

            acts = allocate_wave(cur_tick, list(counts_by_plant.items()), cells, plantable, occupied_positions)
            all_actions.extend(acts)
            cur_tick += 1

    else:
        # ---------------------------------------------------------------------
        # LEVEL 2, 3, 4 STRATEGY: STAGED MULTI-TIER UNLOCK CASCADE
        # ---------------------------------------------------------------------
        # Phase 1: Animal Bootstrap (Ticks 0..15)
        # Grass (1), Lavender (6), Sunflower (5), Rose (2), Oak (12)
        p1_schedule = [
            (0,  [(grass, 12), (lavender, 8)]),
            (1,  [(grass, 12), (lavender, 8)]),
            (2,  [(grass, 12), (lavender, 8)]),
            (3,  [(sunflower, 12), (rose, 8)]),
            (4,  [(sunflower, 12), (rose, 8)]),
            (5,  [(sunflower, 12), (rose, 8)]),
            (6,  [(oak, 10), (rose, 10)]),
            (7,  [(oak, 10), (rose, 10)]),
            (8,  [(grass, 10), (lavender, 10)]),
            (9,  [(grass, 10), (sunflower, 10)]),
        ]
        for tick, reqs in p1_schedule:
            acts = allocate_wave(tick, reqs, cells, plantable, occupied_positions)
            all_actions.extend(acts)

        # Phase 2: Sows Tier 2 species (Ticks 100..115)
        tier2_pool = [blue_moss, crimson_vine, orange_blossom, stone_reed]
        for tick in range(100, 115):
            reqs = [(p, 5) for p in tier2_pool]
            acts = allocate_wave(tick, reqs, cells, plantable, occupied_positions)
            all_actions.extend(acts)

        # Phase 3: Sows Tier 3 species (Ticks 200..215)
        tier3_pool = [purple_canopy, silver_fern, moonpetal, skyvine, living_topiary]
        for tick in range(200, 215):
            reqs = [(p, 4) for p in tier3_pool]
            acts = allocate_wave(tick, reqs, cells, plantable, occupied_positions)
            all_actions.extend(acts)

        # Phase 4: THE GRAND HARVEST (Last 80 Ticks before simulation end)
        occupied_positions.clear()  # Reclaim plantable cells

        grand_species_pool = [
            grass,          # 1
            rose,           # 2
            blue_moss,      # 3
            crimson_vine,   # 4
            sunflower,      # 5
            lavender,       # 6
            orange_blossom, # 7
            silver_fern,    # 8
            purple_canopy,  # 10
            stone_reed,     # 11
            oak,            # 12
            moonpetal,      # 15
            skyvine,        # 20
            living_topiary, # 27
        ]

        harvest_start_tick = max(0, ticks - 80)
        species_idx = 0
        num_sp = len(grand_species_pool)

        for tick in range(harvest_start_tick, ticks - 5):
            counts_by_plant = defaultdict(int)
            for _ in range(MAX_PLANTS_PER_TICK):
                sp = grand_species_pool[species_idx % num_sp]
                counts_by_plant[sp] += 1
                species_idx += 1

            acts = allocate_wave(tick, list(counts_by_plant.items()), cells, plantable, occupied_positions)
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

    output_path = os.path.join(os.path.dirname(input_file), "submission.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    # Verification Report
    counts = defaultdict(int)
    for a in all_actions:
        counts[a["plant_index"]] += 1

    print(f"\n[+] Optimization Successfully Finished!")
    print(f"    - File Written: {output_path}")
    print(f"    - Total Actions: {len(all_actions)}")
    print(f"    - Active Ticks: {len(submission['actions'])}")
    print(f"    - Plant Index Breakdown:")
    for idx in sorted(counts.keys()):
        pname = next((p.name for p in plants.values() if p.index == idx), f"Index {idx}")
        print(f"        * [{idx:2d}] {pname:<20}: {counts[idx]} plants ({counts[idx]/len(all_actions):.2%})")


if __name__ == "__main__":
    solve()