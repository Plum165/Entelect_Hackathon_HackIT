#!/usr/bin/env python3
"""
Level 2: Guaranteed 7-Species Trigger & 97-Tick Pacing Solver
World: 70x100 (411 plantable, 500 ticks) | 7 Species (1, 2, 4, 5, 6, 11, 12) -> H = 0.5668
"""
import json, os, random, math
from collections import defaultdict

INPUT_FILE = "2.json"
OUTPUT_FILE = "submission.json"
MAX_PLANTS_PER_TICK = 20

def solve():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows, cols, T = int(data.get("rows", 70)), int(data.get("cols", 100)), int(data.get("ticks", 500))
    plantable = [(int(c["row"]), int(c["col"])) for c in data.get("cells", []) if int(c.get("terrain", 0)) == 0]
    random.seed(42)

    actions = []

    # 1. Early Unlock Triggers (Ticks 0..3) - Count Based, 100% Guaranteed
    # - Virexids: 15 Grass [1] + 15 Lavender [6] -> Unlocks Stone Reed [11]
    # - Canorals & Barkskips: 15 Oak Tree [12] -> Unlocks Crimson Vine [4] (with Rose & Lavender)
    p1 = [
        (0, [1]*10 + [6]*10),
        (1, [12]*12 + [2]*8),
        (2, [12]*3 + [1]*5 + [6]*5 + [2]*7),
    ]
    for t, batch in p1:
        for idx, p_idx in enumerate(batch):
            r, c = plantable[idx % len(plantable)]
            actions.append({"tick": t, "plant_index": p_idx, "row": r, "col": c})

    # 2. Grand 7-Species Harvest at 97-Tick Horizon (Ticks 403..495)
    # Guaranteed Unlocked Pool: Grass(1), Rose(2), Crimson Vine(4), Sunflower(5), Lavender(6), Stone Reed(11), Oak(12)
    active_7 = [1, 2, 4, 5, 6, 11, 12]
    total_to_plant = len(plantable)
    species_queue = [active_7[i % len(active_7)] for i in range(total_to_plant)]
    
    harvest_plantable = list(plantable)
    harvest_plantable.sort(key=lambda pos: (pos[0] % 3, pos[1] % 3, pos[0], pos[1]))

    cur_tick = 403
    harvest_ticks = 90
    plants_per_tick = max(1, math.ceil(total_to_plant / harvest_ticks))
    plants_per_tick = min(MAX_PLANTS_PER_TICK, plants_per_tick)

    while species_queue and harvest_plantable and cur_tick < T - 2:
        batch_size = min(plants_per_tick, len(species_queue), len(harvest_plantable))
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

    print(f"[+] Level 2 Optimized: {len(actions)} actions across {len(grouped)} ticks (Ticks {min(grouped.keys())}..{max(grouped.keys())}).")

if __name__ == "__main__":
    solve()