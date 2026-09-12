#!/usr/bin/env python3
import json, os, random
from collections import defaultdict

INPUT_FILE = "2.json"
OUTPUT_FILE = "submission.json"
MAX_PLANTS_PER_TICK = 20

def solve():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    plantable = [(int(c["row"]), int(c["col"])) for c in data.get("cells", []) if int(c.get("terrain", 0)) == 0]
    random.seed(42)
    random.shuffle(plantable)

    actions = []
    occupied = set()

    def plant_batch(tick, plant_idx_list):
        nonlocal actions, occupied
        for p_idx in plant_idx_list:
            if len(occupied) >= len(plantable):
                occupied.clear()
            avail = [pos for pos in plantable if pos not in occupied]
            if not avail:
                occupied.clear()
                avail = plantable
            pos = random.choice(avail)
            occupied.add(pos)
            actions.append({"tick": tick, "plant_index": p_idx, "row": pos[0], "col": pos[1]})

    # Phase 1: Bootstrap Animals (Ticks 0..15)
    # Grass(1), Rose(2), Sunflower(5), Lavender(6), Oak(12)
    p1 = [
        (0, [1]*12 + [6]*8),
        (1, [1]*12 + [6]*8),
        (2, [1]*12 + [6]*8),
        (3, [5]*12 + [2]*8),
        (4, [5]*12 + [2]*8),
        (5, [5]*12 + [2]*8),
        (6, [12]*10 + [2]*10),
        (7, [12]*10 + [2]*10),
        (8, [1]*10 + [6]*10),
        (9, [1]*10 + [5]*10),
    ]
    for t, batch in p1:
        plant_batch(t, batch)

    # Phase 2: Tier 2 Unlocks (Ticks 100..115)
    # Blue Moss(3), Crimson Vine(4), Orange Blossom(7), Stone Reed(11)
    tier2 = [3, 4, 7, 11]
    for t in range(100, 115):
        plant_batch(t, [tier2[i % len(tier2)] for i in range(MAX_PLANTS_PER_TICK)])

    # Phase 3: Tier 3 Unlocks (Ticks 200..215)
    # Purple Canopy(10), Silver Fern(8), Moonpetal(15), Skyvine(20)
    tier3 = [10, 8, 15, 20]
    for t in range(200, 215):
        plant_batch(t, [tier3[i % len(tier3)] for i in range(MAX_PLANTS_PER_TICK)])

    # Phase 4: THE GRAND HARVEST (Ticks 410..495)
    occupied.clear()
    grand_pool = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 15, 20, 27]
    idx_counter = 0

    for t in range(410, 496):
        batch = []
        for _ in range(MAX_PLANTS_PER_TICK):
            batch.append(grand_pool[idx_counter % len(grand_pool)])
            idx_counter += 1
        plant_batch(t, batch)

    grouped = defaultdict(list)
    for a in actions:
        grouped[a["tick"]].append({"plant_index": a["plant_index"], "row": a["row"], "col": a["col"]})

    submission = {"actions": [{"tick": t, "plants": grouped[t]} for t in sorted(grouped.keys())]}
    with open(os.path.join(script_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"[+] Level 2 Done: {len(actions)} actions written across {len(grouped)} ticks.")

if __name__ == "__main__":
    solve()