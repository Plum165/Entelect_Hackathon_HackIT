#!/usr/bin/env python3
"""
Level 1: Greenhouse Study - DP Soil Transportation Solver
"""
import json, os, random
from collections import defaultdict

INPUT_FILE = "1.json"
OUTPUT_FILE = "submission.json"
MAX_PLANTS_PER_TICK = 20

# Soil preferences from plant_dataset.json:
# Grass(1): [0,1], Rose(2): [0,1], Sunflower(5): [0,1], Lavender(6): [0,1], Oak(12): [0,1]
BASE_SPECIES = [1, 2, 5, 6, 12]

def solve():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    plantable = [(int(c["row"]), int(c["col"])) for c in data.get("cells", []) if int(c.get("terrain", 0)) == 0]
    random.seed(42)
    random.shuffle(plantable)

    total_to_plant = len(plantable)
    species_queue = [BASE_SPECIES[i % len(BASE_SPECIES)] for i in range(total_to_plant)]
    random.shuffle(species_queue)

    actions = []
    cur_tick = 410
    
    while species_queue and plantable and cur_tick < 500:
        batch_size = min(MAX_PLANTS_PER_TICK, len(species_queue), len(plantable))
        for _ in range(batch_size):
            p_idx = species_queue.pop()
            r, c = plantable.pop()
            actions.append({"tick": cur_tick, "plant_index": p_idx, "row": r, "col": c})
        cur_tick += 1

    grouped = defaultdict(list)
    for a in actions:
        grouped[a["tick"]].append({"plant_index": a["plant_index"], "row": a["row"], "col": a["col"]})

    submission = {"actions": [{"tick": t, "plants": grouped[t]} for t in sorted(grouped.keys())]}
    with open(os.path.join(script_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"[+] Level 1 Optimized: {len(actions)} actions across {len(grouped)} ticks.")

if __name__ == "__main__":
    solve()