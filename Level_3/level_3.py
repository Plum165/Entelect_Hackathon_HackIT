#!/usr/bin/env python3
"""
Level 3: Multi-Tick Horizon & Formula Diagnostic Solver
World: 150x150 (22,500 cells, 800 ticks) | 1,253 Plantable Cells
"""
import json, os, random, math
from collections import defaultdict

INPUT_FILE = "3.json"
OUTPUT_FILE = "submission.json"
MAX_PLANTS_PER_TICK = 20

def solve():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows, cols, T = int(data.get("rows", 150)), int(data.get("cols", 150)), int(data.get("ticks", 800))
    C_max = rows * cols
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

    # 2. Grand 10-Species Harvest Stretched across Ticks 705..790
    active_10 = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
    total_to_plant = len(plantable)
    species_queue = [active_10[i % len(active_10)] for i in range(total_to_plant)]
    
    harvest_plantable = list(plantable)
    harvest_plantable.sort(key=lambda pos: (pos[0] % 4, pos[1] % 4, pos[0], pos[1]))

    cur_tick = 705
    plants_per_tick = max(1, math.ceil(total_to_plant / 80))
    plants_per_tick = min(MAX_PLANTS_PER_TICK, plants_per_tick)

    harvest_actions = []
    while species_queue and harvest_plantable and cur_tick < T - 2:
        batch_size = min(plants_per_tick, len(species_queue), len(harvest_plantable))
        for _ in range(batch_size):
            p_idx = species_queue.pop(0)
            r, c = harvest_plantable.pop(0)
            act = {"tick": cur_tick, "plant_index": p_idx, "row": r, "col": c}
            actions.append(act)
            harvest_actions.append(act)
        cur_tick += 1

    grouped = defaultdict(list)
    lifespans = []
    counts = defaultdict(int)
    for a in harvest_actions:
        lifespans.append(T - a["tick"])
        counts[a["plant_index"]] += 1

    for a in actions:
        grouped[a["tick"]].append({"plant_index": a["plant_index"], "row": a["row"], "col": a["col"]})

    submission = {"actions": [{"tick": t, "plants": grouped[t]} for t in sorted(grouped.keys())]}
    with open(os.path.join(script_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    # -------------------------------------------------------------------------
    # MATHEMATICAL FORMULA VARIABLE PRINTOUT
    # -------------------------------------------------------------------------
    C = len(harvest_actions)
    K = len(counts)
    H = -sum((cnt / C) * (math.log(cnt / C) / math.log(31)) for cnt in counts.values())
    coverage_ratio = C / C_max
    mean_lifespan = sum(lifespans) / len(lifespans)

    print("=" * 70)
    print(f" LEVEL 3 SCORING FORMULA VARIABLES")
    print("=" * 70)
    print(f" Grid Size (C_max)     : {C_max} cells ({rows}x{cols})")
    print(f" Total Ticks (T)       : {T}")
    print(f" Live Plants at End(C) : {C} ({C/C_max:.4%} of C_max)")
    print(f" Species Count (K)     : {K} species")
    print(f" Exact Entropy (H)     : {H:.6f} (Max for K=10: {math.log(10)/math.log(31):.6f})")
    print(f" Harvest Ticks Used    : {min(a['tick'] for a in harvest_actions)} to {max(a['tick'] for a in harvest_actions)} ({len(set(a['tick'] for a in harvest_actions))} ticks)")
    print(f" Lifespans (l_ij)      : min={min(lifespans)}, max={max(lifespans)}, mean={mean_lifespan:.2f} ticks")
    print("-" * 70)
    print(f" PARAMETER SOLVER MATRIX:")
    for alpha in [1.0, 1.5, 2.0]:
        main_val = H * (coverage_ratio ** alpha)
        for k in [1.0, 1.5, 2.0]:
            long_val = (1.0 / C_max) * sum((l / T) ** k for l in lifespans)
            unscaled_score = 0.8 * main_val + 0.2 * long_val
            print(f"   alpha={alpha:.1f}, k={k:.1f}  ->  Main={main_val:.6f}, Long={long_val:.6f}  =>  RawSum={unscaled_score:.6f}")
    print("=" * 70)

if __name__ == "__main__":
    solve()