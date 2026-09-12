#!/usr/bin/env python3
"""
Level 2: 2-Billion Exponential Spread Engine
World: 70x100 (500 ticks) | 8-Species High Spread Pool (1, 2, 4, 5, 6, 7, 11, 12)
"""
import json
import os
from collections import defaultdict

INPUT_FILE = "2.json"
OUTPUT_FILE = "submission.json"
MAX_PLANTS_PER_TICK = 20
ACTIVE_7 = [1, 2, 4, 5, 6, 11, 12]


def validate_actions(actions, data):
    plantable = {
        (int(cell["row"]), int(cell["col"]))
        for cell in data["cells"]
        if int(cell["terrain"]) == 0
    }
    seen_positions = set()
    for tick, plants in actions:
        if not 0 <= tick < int(data["ticks"]):
            raise ValueError(f"Invalid tick: {tick}")
        if len(plants) > MAX_PLANTS_PER_TICK:
            raise ValueError(f"Too many plants at tick {tick}")
        for plant in plants:
            position = (plant["row"], plant["col"])
            if position not in plantable:
                raise ValueError(f"Non-plantable position: {position}")
            position_at_tick = (tick, position)
            if position_at_tick in seen_positions:
                raise ValueError(f"Duplicate position at tick {tick}: {position}")
            seen_positions.add(position_at_tick)

def solve():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    plantable = [(int(c["row"]), int(c["col"])) for c in data.get("cells", []) if int(c.get("terrain", 0)) == 0]
    grouped = defaultdict(list)

    # 15 Grass + 15 Lavender, 15 Oak Tree, and 15 Rose Bush.
    early_batches = [
        [1] * 15 + [6] * 5,
        [6] * 10 + [12] * 10,
        [12] * 5 + [2] * 15,
    ]
    for tick, batch in enumerate(early_batches):
        for position, plant_index in zip(plantable[:len(batch)], batch):
            grouped[tick].append({"plant_index": plant_index, "row": position[0], "col": position[1]})

    # Use the requested seven-species pool in the final-tick lifespan window.
    species_queue = [ACTIVE_7[i % len(ACTIVE_7)] for i in range(len(plantable))]
    
    harvest_plantable = list(plantable)
    harvest_plantable.sort()

    cur_tick = max(0, int(data["ticks"]) - 97)
    while species_queue and harvest_plantable and cur_tick < int(data["ticks"]):
        batch_size = min(MAX_PLANTS_PER_TICK, len(species_queue), len(harvest_plantable))
        for _ in range(batch_size):
            p_idx = species_queue.pop(0)
            r, c = harvest_plantable.pop(0)
            grouped[cur_tick].append({"plant_index": p_idx, "row": r, "col": c})
        cur_tick += 1

    actions = [(tick, plants) for tick, plants in sorted(grouped.items())]
    validate_actions(actions, data)
    submission = {"actions": [{"tick": tick, "plants": plants} for tick, plants in actions]}
    with open(os.path.join(script_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"[+] Level 2 done: {sum(len(plants) for _, plants in actions)} plants across ticks {actions[0][0]}..{actions[-1][0]}.")

if __name__ == "__main__":
    solve()