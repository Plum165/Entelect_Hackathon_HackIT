#!/usr/bin/env python3
import json, os, random
from collections import defaultdict

INPUT_FILE = "4.json"
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

    # Step 1: Bootstrap Virexids count >= 10 (Ticks 0..1)
    for i in range(15):
        r, c = plantable[i]
        actions.append({"tick": 0, "plant_index": 1, "row": r, "col": c})  # 15 Grass
    for i in range(15, 30):
        r, c = plantable[i]
        actions.append({"tick": 1, "plant_index": 6, "row": r, "col": c})  # 15 Lavender

    # Step 2: Harvest across plantable cells using exact 6-way parity (Ticks 715..795)
    active_species = [1, 2, 5, 6, 11, 12]
    # Sows up to 1,600 plants (80 ticks * 20 plants/tick)
    max_harvest_plants = min(len(plantable), 80 * MAX_PLANTS_PER_TICK)
    species_queue = [active_species[i % len(active_species)] for i in range(max_harvest_plants)]
    random.shuffle(species_queue)
    
    harvest_plantable = list(plantable)
    random.shuffle(harvest_plantable)

    cur_tick = 715
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

    print(f"[+] Level 4 Complete: {len(actions)} actions written across {len(grouped)} ticks.")

if __name__ == "__main__":
    solve()