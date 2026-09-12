#!/usr/bin/env python3
"""
Level 4: 10-Species High Entropy Optimizer
World: 200x300 (800 ticks) | 1,880 Direct Nodes + Forest Mesh | H = 0.6702
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

    # 1. Early Unlock Triggers (Ticks 0..6)
    p1 = [
        (0, [1]*10 + [6]*10),
        (1, [12]*12 + [2]*8),
        (2, [6]*10 + [5]*10),
        (3, [2]*10 + [1]*10),
        (4, [1]*15 + [2]*5),
        (5, [3]*10 + [4]*10),
    ]
    for t, batch in p1:
        for idx, p_idx in enumerate(batch):
            r, c = plantable[idx % len(plantable)]
            actions.append({"tick": t, "plant_index": p_idx, "row": r, "col": c})

    # 2. Grand 10-Species Harvest (Ticks 705..799)
    active_10 = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
    max_harvest_plants = min(len(plantable), 94 * MAX_PLANTS_PER_TICK)  # 1,880 plants
    species_queue = [active_10[i % len(active_10)] for i in range(max_harvest_plants)]
    
    harvest_plantable = list(plantable)
    harvest_plantable.sort(key=lambda pos: (pos[0] % 5, pos[1] % 5, pos[0], pos[1]))

    cur_tick = 705
    while species_queue and harvest_plantable and cur_tick < 800:
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

    print(f"[+] Level 4 (10 Species, H=0.6702): {len(actions)} actions across {len(grouped)} ticks.")

if __name__ == "__main__":
    solve()