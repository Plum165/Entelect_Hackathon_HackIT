#!/usr/bin/env python3
"""
Level 3: 2-Billion Exponential Spread Engine
World: 150x150 (800 ticks) | 8-Species High Spread Pool (1, 2, 4, 5, 6, 7, 11, 12)
"""
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

    # 1. Early Unlock Triggers (Ticks 0..3)
    p1 = [
        (0, [1]*10 + [6]*10),
        (1, [12]*12 + [2]*8),
        (2, [12]*3 + [1]*5 + [6]*5 + [2]*7),
    ]
    for t, batch in p1:
        for idx, p_idx in enumerate(batch):
            r, c = plantable[idx % len(plantable)]
            actions.append({"tick": t, "plant_index": p_idx, "row": r, "col": c})

    # 2. Seed Epicenters across Ticks 715..775 (Giving 25-85 ticks of massive exponential expansion)
    active_8 = [1, 2, 4, 5, 6, 7, 11, 12]
    total_to_plant = len(plantable)
    species_queue = [active_8[i % len(active_8)] for i in range(total_to_plant)]
    
    harvest_plantable = list(plantable)
    harvest_plantable.sort(key=lambda pos: (pos[0] % 4, pos[1] % 4, pos[0], pos[1]))

    cur_tick = 715
    while species_queue and harvest_plantable and cur_tick < 785:
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

    print(f"[+] Level 3 Exponential Engine Done: {len(actions)} seed epicenters active across Ticks {min(grouped.keys())}..{max(grouped.keys())}.")

if __name__ == "__main__":
    solve()