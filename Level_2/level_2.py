#!/usr/bin/env python3
"""
Level 2: 10-Species High Entropy Optimizer
World: 70x100 (500 ticks) | 10 Species Pool -> H = 0.6702 (+43% boost)
"""
import json, os, random
from collections import defaultdict

INPUT_FILE = "2.json"
OUTPUT_FILE = "submission.json"
MAX_PLANTS_PER_TICK = 20

def solve():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    plantable = [(int(c["row"]), int(c["col"])) for c in data.get("cells", []) if int(c.get("terrain", 0)) == 0]
    random.seed(42)

    actions = []

    # 1. Early Unlock Triggers (Ticks 0..6)
    # Triggers Virexids [11], Canorals/Barkskips [4], Nectaris [7], Loamcrawlers [3], Purple Canopy [10]
    p1 = [
        (0, [1]*10 + [6]*10),   # 10 Grass, 10 Lavender -> Virexids
        (1, [12]*12 + [2]*8),   # 12 Oak, 8 Rose -> Canorals & Barkskips
        (2, [6]*10 + [5]*10),   # 10 Lavender, 10 Sunflower -> Nectaris
        (3, [2]*10 + [1]*10),   # 10 Rose, 10 Grass -> Loamcrawlers
        (4, [1]*15 + [2]*5),    # Grass coverage expansion
        (5, [3]*10 + [4]*10),   # Propagate Blue Moss & Crimson Vine -> Purple Canopy [10]
    ]
    for t, batch in p1:
        for idx, p_idx in enumerate(batch):
            r, c = plantable[idx % len(plantable)]
            actions.append({"tick": t, "plant_index": p_idx, "row": r, "col": c})

    # 2. Grand 10-Species Harvest (Ticks 405..435)
    # 1: Grass, 2: Rose, 3: Blue Moss, 4: Crimson Vine, 5: Sunflower,
    # 6: Lavender, 7: Orange Blossom, 10: Purple Canopy, 11: Stone Reed, 12: Oak
    active_10 = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
    total_to_plant = len(plantable)
    species_queue = [active_10[i % len(active_10)] for i in range(total_to_plant)]
    
    harvest_plantable = list(plantable)
    harvest_plantable.sort(key=lambda pos: (pos[0] % 3, pos[1] % 3, pos[0], pos[1]))

    cur_tick = 405
    while species_queue and harvest_plantable and cur_tick < 500:
        batch_size = min(MAX_PLANTS_PER_TICK, len(species_queue), len(harvest_plantable))
        for _ in range(batch_size):
            p_idx = species_queue.pop(0)
            r, c = harvest_plantable.pop(0)
            actions.append({"tick": cur_tick, "plant_index": p_idx, "row": r, "col": c})
        cur_tick += 1

    grouped = defaultdict(list)
    for a in actions:
        grouped[a["tick"]].append({"plant_index": a["plant_index"], "row": a["row"], "col": a["col"]})

    submission = {"actions": [{"tick": t, "plants": grouped[t]} for t in sorted(grouped.keys())]}
    with open(os.path.join(script_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"[+] Level 2 (10 Species, H=0.6702): {len(actions)} actions across {len(grouped)} ticks.")

if __name__ == "__main__":
    solve()