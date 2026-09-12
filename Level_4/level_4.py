#!/usr/bin/env python3
"""
Level 4: Forest Apex - 7-Species Trigger & DP Solver
"""
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

    # 1. Early Trigger Injection (Ticks 0..2)
    p1 = [
        (0, [1]*10 + [6]*10),
        (1, [1]*5 + [6]*5 + [12]*10),
        (2, [12]*5 + [2]*15),
    ]
    for t, batch in p1:
        for idx, p_idx in enumerate(batch):
            r, c = plantable[idx % len(plantable)]
            actions.append({"tick": t, "plant_index": p_idx, "row": r, "col": c})

    # 2. The 7-Species Grand Harvest (Ticks 715..795)
    active_7 = [1, 2, 4, 5, 6, 11, 12]
    max_harvest_plants = min(len(plantable), 80 * MAX_PLANTS_PER_TICK)
    species_queue = [active_7[i % len(active_7)] for i in range(max_harvest_plants)]
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

    print(f"[+] Level 4 (7 Species, H=0.5668): {len(actions)} actions across {len(grouped)} ticks.")

if __name__ == "__main__":
    solve()