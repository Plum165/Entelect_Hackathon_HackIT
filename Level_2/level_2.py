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
HARVEST_POOL = [4, 6, 4, 6, 4, 5, 4, 12, 6, 4]


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

    # Trigger the required ecosystem species shortly before harvest. Keeping
    # these late prevents Oak Tree from dominating for the whole simulation.
    early_batches = [
        [1] * 10 + [6] * 10,
        [12] * 10,
        [2] * 10,
    ]
    early_offset = 0
    for tick, batch in enumerate(early_batches):
        trigger_cells = plantable[early_offset:early_offset + len(batch)]
        for position, plant_index in zip(trigger_cells, batch):
            grouped[380 + tick].append({"plant_index": plant_index, "row": position[0], "col": position[1]})
        early_offset += len(batch)

    # Compensate for the evaluator's observed spread imbalance: Crimson Vine
    # and Lavender receive more seeds, while Sunflower and Oak receive fewer.
    harvest_plantable = plantable[early_offset:]
    harvest_plantable.sort()
    species_queue = [HARVEST_POOL[i % len(HARVEST_POOL)] for i in range(len(harvest_plantable))]

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