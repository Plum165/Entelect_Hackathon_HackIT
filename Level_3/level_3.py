#!/usr/bin/env python3
import json, os, random
from collections import defaultdict

INPUT_FILE = "3.json"
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

    # Step 1: Bootstrap Virexids (Ticks 0..1)
    for i in range(15):
        r, c = plantable[i]
        actions.append({"tick": 0, "plant_index": 1, "row": r, "col": c})  # 15 Grass
    for i in range(15, 30):
        r, c = plantable[i]
        actions.append({"tick": 1, "plant_index": 6, "row": r, "col": c})  # 15 Lavender

    # Step 2: Exact 6-Way Parity Harvest across all 1,253 plantable cells (Ticks 720..785)
    active_species = [1, 2, 5, 6, 11, 12]
    total_to_plant = len(plantable)
    species_queue = [active_species[i % len(active_species)] for i in range(total_to_plant)]
    random.shuffle(species_queue)
    
    harvest_plantable = list(plantable)
    random.shuffle(harvest_plantable)

    cur_tick = 720
    while species_queue and harvest_plantable and cur_tick < 800:
        batch_size = min(MAX_PLANTS_PER_TICK, len(species_queue), len(harvest_plantable))
        for _ in range(batch_size):
            p_idx = species_queue.pop()
            r, c = harvest_plantable.pop()
            actions.append({"tick": cur_tick, "plant_index": p_idx, "row": r, "col": c})
        cur_tick += 1

    grouped = defaultdict(list)
    for a in actions:
        grouped[a["tick"]].append({"plant_index": a["plant_index"], "row": a["row"], "col": a["col"]})

    submission = {"actions": [{"tick": t, "plants": grouped[t]} for t in sorted(grouped.keys())]}
    with open(os.path.join(script_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"[+] Level 3 Complete: {len(actions)} actions written across {len(grouped)} ticks.")

if __name__ == "__main__":
    solve()