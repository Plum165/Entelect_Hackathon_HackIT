#!/usr/bin/env python3
"""
Level 1: 2-Billion Exponential Spread Engine
World: 50x50 (500 ticks) | Base 5 Species (1, 2, 5, 6, 12)
"""
import json
import os
from collections import defaultdict

INPUT_FILE = "1.json"
OUTPUT_FILE = "submission.json"
MAX_PLANTS_PER_TICK = 20
BASE_5 = [1, 2, 5, 6, 12]


def validate_actions(actions, data):
    ticks = int(data["ticks"])
    plantable = {
        (int(cell["row"]), int(cell["col"]))
        for cell in data["cells"]
        if int(cell["terrain"]) == 0
    }
    seen_positions = set()
    for tick, plants in actions:
        if not 0 <= tick < ticks:
            raise ValueError(f"Invalid tick: {tick}")
        if len(plants) > MAX_PLANTS_PER_TICK:
            raise ValueError(f"Too many plants at tick {tick}")
        for plant in plants:
            position = (plant["row"], plant["col"])
            if position not in plantable:
                raise ValueError(f"Non-plantable position: {position}")
            if position in seen_positions:
                raise ValueError(f"Duplicate position: {position}")
            seen_positions.add(position)

def solve():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, INPUT_FILE)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    plantable = [(int(c["row"]), int(c["col"])) for c in data.get("cells", []) if int(c.get("terrain", 0)) == 0]
    plantable.sort(key=lambda pos: (pos[0], pos[1]))

    species_queue = [BASE_5[i % len(BASE_5)] for i in range(len(plantable))]

    grouped = defaultdict(list)
    cur_tick = max(0, int(data["ticks"]) - 97)
    while species_queue and plantable and cur_tick < int(data["ticks"]):
        batch_size = min(MAX_PLANTS_PER_TICK, len(species_queue), len(plantable))
        for _ in range(batch_size):
            p_idx = species_queue.pop(0)
            r, c = plantable.pop(0)
            grouped[cur_tick].append({"plant_index": p_idx, "row": r, "col": c})
        cur_tick += 1

    actions = [(tick, plants) for tick, plants in sorted(grouped.items())]
    validate_actions(actions, data)
    submission = {"actions": [{"tick": tick, "plants": plants} for tick, plants in actions]}
    with open(os.path.join(script_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)

    print(f"[+] Level 1 done: {sum(len(plants) for _, plants in actions)} plants across ticks {actions[0][0]}..{actions[-1][0]}.")

if __name__ == "__main__":
    solve()