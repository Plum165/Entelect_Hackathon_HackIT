#!/usr/bin/env python3
"""
Level 1: 97-Tick Pacing & DP Soil Solver
World: 50x50 (500 ticks) | Base 5 Species (1, 2, 5, 6, 12) -> H = 0.46867
"""
import json, os, random, math
from collections import defaultdict

INPUT_FILE = "1.json"
OUTPUT_FILE = "submission.json"
MAX_PLANTS_PER_TICK = 20
BASE_5 = [1, 2, 5, 6, 12]

def solve():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows, cols, T = int(data.get("rows", 50)), int(data.get("cols", 50)), int(data.get("ticks", 500))
    plantable = [(int(c["row"]), int(c["col"])) for c in data.get("cells", []) if int(c.get("terrain", 0)) == 0]
    random.seed(42)
    plantable.sort(key=lambda pos: (pos[0] % 3, pos[1] % 3, pos[0], pos[1]))

    total_to_plant = len(plantable)
    species_queue = [BASE_5[i % len(BASE_5)] for i in range(total_to_plant)]

    actions = []
    # Start at Tick 403 -> Max lifespan = 500 - 403 = 97 ticks (Safe from 100-tick nutrient death)
    cur_tick = 403
    harvest_ticks = 92
    plants_per_tick = max(1, math.ceil(total_to_plant / harvest_ticks))
    plants_per_tick = min(MAX_PLANTS_PER_TICK, plants_per_tick)

    while species_queue and plantable and cur_tick < T - 2:
        batch_size = min(plants_per_tick, len(species_queue), len(plantable))
        for _ in range(batch_size):
            p_idx = species_queue.pop(0)
            r, c = plantable.pop(0)
            actions.append({"tick": cur_tick, "plant_index": p_idx, "row": r, "col": c})
        cur_tick += 1

    grouped = defaultdict(list)
    for a in actions:
        grouped[a["tick"]].append({"plant_index": a["plant_index"], "row": a["row"], "col": a["col"]})

    submission = {"actions": [{"tick": t, "plants": grouped[t]} for t in sorted(grouped.keys())]}
    with open(os.path.join(script_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"[+] Level 1 Optimized: {len(actions)} actions across {len(grouped)} ticks (Ticks {min(grouped.keys())}..{max(grouped.keys())}).")

if __name__ == "__main__":
    solve()