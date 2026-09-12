#!/usr/bin/env python3
"""
Level 1: Multi-Tick Horizon & Formula Diagnostic Solver
World: 50x50 (2500 cells, 500 ticks) | Base 5 Species (1, 2, 5, 6, 12)
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
    C_max = rows * cols
    plantable = [(int(c["row"]), int(c["col"])) for c in data.get("cells", []) if int(c.get("terrain", 0)) == 0]
    random.seed(42)

    plantable.sort(key=lambda pos: (pos[0] % 3, pos[1] % 3, pos[0], pos[1]))
    total_to_plant = len(plantable)
    species_queue = [BASE_5[i % len(BASE_5)] for i in range(total_to_plant)]

    actions = []
    # Stretched across 95 ticks (Ticks 403 to 498) -> Max lifespans 97 to 2 ticks
    cur_tick = 403
    plants_per_tick = max(1, math.ceil(total_to_plant / 92))  # Spreads evenly across ~92 ticks
    plants_per_tick = min(MAX_PLANTS_PER_TICK, plants_per_tick)

    while species_queue and plantable and cur_tick < T - 1:
        batch_size = min(plants_per_tick, len(species_queue), len(plantable))
        for _ in range(batch_size):
            p_idx = species_queue.pop(0)
            r, c = plantable.pop(0)
            actions.append({"tick": cur_tick, "plant_index": p_idx, "row": r, "col": c})
        cur_tick += 1

    grouped = defaultdict(list)
    lifespans = []
    counts = defaultdict(int)
    for a in actions:
        grouped[a["tick"]].append({"plant_index": a["plant_index"], "row": a["row"], "col": a["col"]})
        lifespans.append(T - a["tick"])
        counts[a["plant_index"]] += 1

    submission = {"actions": [{"tick": t, "plants": grouped[t]} for t in sorted(grouped.keys())]}
    with open(os.path.join(script_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    # -------------------------------------------------------------------------
    # MATHEMATICAL FORMULA VARIABLE PRINTOUT
    # -------------------------------------------------------------------------
    C = len(actions)
    K = len(counts)
    H = -sum((cnt / C) * (math.log(cnt / C) / math.log(31)) for cnt in counts.values())
    coverage_ratio = C / C_max
    mean_lifespan = sum(lifespans) / len(lifespans)

    print("=" * 70)
    print(f" LEVEL 1 SCORING FORMULA VARIABLES")
    print("=" * 70)
    print(f" Grid Size (C_max)     : {C_max} cells ({rows}x{cols})")
    print(f" Total Ticks (T)       : {T}")
    print(f" Live Plants (C)       : {C} ({C/C_max:.4%} of C_max)")
    print(f" Species Count (K)     : {K} species")
    print(f" Exact Entropy (H)     : {H:.6f} (Max theoretical for K=5: {math.log(5)/math.log(31):.6f})")
    print(f" Active Ticks Used     : {min(grouped.keys())} to {max(grouped.keys())} ({len(grouped)} ticks)")
    print(f" Lifespans (l_ij)      : min={min(lifespans)}, max={max(lifespans)}, mean={mean_lifespan:.2f} ticks")
    print("-" * 70)
    print(f" PARAMETER SOLVER MATRIX (Main = H * (C/C_max)^alpha, Long = 1/C_max * sum(l/T)^k):")
    for alpha in [1.0, 1.5, 2.0]:
        main_val = H * (coverage_ratio ** alpha)
        for k in [1.0, 1.5, 2.0]:
            long_val = (1.0 / C_max) * sum((l / T) ** k for l in lifespans)
            unscaled_score = 0.8 * main_val + 0.2 * long_val
            print(f"   alpha={alpha:.1f}, k={k:.1f}  ->  Main={main_val:.6f}, Long={long_val:.6f}  =>  RawSum={unscaled_score:.6f}")
    print("=" * 70)
    print(f"[*] To compute SCALE: SCALE = Leaderboard_Score / RawSum")

if __name__ == "__main__":
    solve()