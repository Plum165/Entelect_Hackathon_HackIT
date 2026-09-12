#!/usr/bin/env python3
"""
Entelect University Cup 2 / HackIT - Level 1 Solver
===================================================
Optimized dynamic planner and placement engine:
- Manages real-time ecosystem unlocks and animal trigger thresholds.
- Allocates tick action budgets (max 20 plants/tick) using prioritized dynamic stages.
- Employs spatial dispersion and preferred soil matching to maximize colony spread.
- Outputs official submission schema to submission.json.
"""

import json
import math
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# CONFIGURATION & CONSTANTS
# ============================================================

INPUT_FILE = "1.json"
OUTPUT_FILE = "submission.json"

RANDOM_SEED = 42

MAX_PLANTS_PER_TICK = 20
DEFAULT_GRID_SIZE = 50 * 50  # 2500 cells

STARTING_PLANTS = {
    "Grass",
    "Rose Bush",
    "Dwarf Sunflower",
    "Lavender",
    "Oak Tree",
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Cell:
    row: int
    col: int
    terrain: Any = 0
    soil: Any = 1


@dataclass
class PlantInfo:
    index: int
    name: str
    raw: Dict[str, Any] = field(default_factory=dict)
    time_to_maturity: float = 1.0
    spread_rate: float = 0.0
    spread_range: float = 0.0
    invasiveness_rank: float = 0.0
    preferred_soil: List[Any] = field(default_factory=list)


@dataclass
class Action:
    tick: int
    plant: str
    row: int
    col: int


@dataclass
class EcosystemState:
    counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    planted_species: Set[str] = field(default_factory=set)
    animals_present: Set[str] = field(default_factory=set)
    events: Set[str] = field(default_factory=set)
    total_grid_cells: int = DEFAULT_GRID_SIZE


# ============================================================
# FILE HELPERS & RESOURCE RESOLUTION
# ============================================================

def resolve_resource_path(filename: str) -> str:
    """Finds resource files across multiple possible directory configurations."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(current_dir, filename),
        os.path.join(current_dir, "..", "additional-resources", filename),
        os.path.join(current_dir, "additional-resources", filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.getcwd(), "additional-resources", filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    # Fallback to relative path
    return os.path.join(current_dir, "..", "additional-resources", filename)


def load_json(path: str) -> Any:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing required file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# PARSERS
# ============================================================

def parse_garden(data: Dict[str, Any]) -> Dict[Tuple[int, int], Cell]:
    cells = {}
    for raw in data.get("cells", []):
        try:
            r = int(raw["row"])
            c = int(raw["col"])
            cells[(r, c)] = Cell(
                row=r,
                col=c,
                terrain=raw.get("terrain", 0),
                soil=raw.get("soil", 1),
            )
        except (KeyError, TypeError, ValueError):
            continue
    return cells


def parse_plant_catalogue(data: Any) -> Dict[str, PlantInfo]:
    plants = {}
    if not isinstance(data, list):
        return plants

    for raw in data:
        if not isinstance(raw, dict):
            continue
        name = raw.get("plant")
        idx = raw.get("index")
        if name is None or idx is None:
            continue

        growth = raw.get("growth", {})
        preferred_soil = raw.get("preferred_soil", [])
        if not isinstance(preferred_soil, list):
            preferred_soil = []

        plants[str(name)] = PlantInfo(
            index=int(idx),
            name=str(name),
            raw=raw,
            time_to_maturity=float(growth.get("time_to_maturity", 1.0)),
            spread_rate=float(growth.get("spread_rate", 0.0)),
            spread_range=float(growth.get("spread_range", 0.0)),
            invasiveness_rank=float(growth.get("invasiveness_rank", 0.0)),
            preferred_soil=preferred_soil,
        )
    return plants


def parse_classifications(data: Any) -> Dict[str, Set[str]]:
    result = {}
    if isinstance(data, dict):
        for group, members in data.items():
            if isinstance(members, list):
                result[str(group)] = {str(m) for m in members}
    return result


def parse_animals(data: Any) -> Dict[str, Dict[str, Any]]:
    animals = {}
    if isinstance(data, list):
        for animal in data:
            if isinstance(animal, dict) and "name" in animal:
                animals[str(animal["name"])] = animal
    return animals


def parse_unlock_conditions(data: Any) -> Dict[str, Dict[str, Any]]:
    result = {}
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and "plant" in entry and "unlock" in entry:
                result[str(entry["plant"])] = entry["unlock"]
    return result


# ============================================================
# EVALUATION & UNLOCK LOGIC
# ============================================================

def compare(actual: float, operator: str, target: float) -> bool:
    if operator == ">":
        return actual > target
    if operator == ">=":
        return actual >= target
    if operator == "<":
        return actual < target
    if operator == "<=":
        return actual <= target
    if operator in ("=", "=="):
        return actual == target
    if operator == "!=":
        return actual != target
    return False


def get_coverage(state: EcosystemState, plant: str) -> float:
    return state.counts[plant] / state.total_grid_cells


def get_group_count(state: EcosystemState, group: str, classifications: Dict[str, Set[str]]) -> int:
    members = classifications.get(group, set())
    return sum(state.counts[p] for p in members)


def evaluate_animal_condition(
    condition: Dict[str, Any],
    state: EcosystemState,
    classifications: Dict[str, Set[str]],
) -> bool:
    c_type = condition.get("type")
    op = condition.get("operator", ">=")
    target = float(condition.get("threshold", 0))

    if c_type == "coverage":
        species_list = condition.get("species", [])
        if not species_list:
            return False
        actual = get_coverage(state, str(species_list[0]))
        return compare(actual, op, target)

    if c_type == "group_coverage":
        group = condition.get("species_group", [])
        if isinstance(group, list):
            count = sum(state.counts[str(p)] for p in group)
        else:
            count = get_group_count(state, str(group), classifications)
        actual = count / state.total_grid_cells
        return compare(actual, op, target)

    if c_type == "count":
        if "species" in condition:
            actual = state.counts[str(condition["species"])]
        elif "species_group" in condition:
            group = condition["species_group"]
            if isinstance(group, list):
                actual = sum(state.counts[str(p)] for p in group)
            else:
                actual = get_group_count(state, str(group), classifications)
        else:
            return False
        return compare(actual, op, target)

    if c_type == "dominance":
        total = sum(state.counts.values())
        if total <= 0:
            return False
        largest = max(state.counts.values(), default=0)
        dominance = largest / total
        return compare(dominance, op, target)

    return False


def evaluate_animal(
    animal: Dict[str, Any],
    state: EcosystemState,
    classifications: Dict[str, Set[str]],
) -> bool:
    reqs = animal.get("requirements", {})
    if not isinstance(reqs, dict):
        return False
    op = reqs.get("type", "AND")
    conditions = reqs.get("conditions", [])
    results = [evaluate_animal_condition(c, state, classifications) for c in conditions]
    return any(results) if op == "OR" else all(results)


def evaluate_plant_condition(
    condition: Any,
    state: EcosystemState,
    classifications: Dict[str, Set[str]],
) -> bool:
    if not isinstance(condition, dict):
        return False

    op = condition.get("op")
    if op in ("AND", "and"):
        return all(evaluate_plant_condition(c, state, classifications) for c in condition.get("children", []))
    if op in ("OR", "or"):
        return any(evaluate_plant_condition(c, state, classifications) for c in condition.get("children", []))
    if op in ("NOT", "not"):
        return not all(evaluate_plant_condition(c, state, classifications) for c in condition.get("children", []))

    c_type = condition.get("type")
    if c_type == "species_present":
        return str(condition.get("species")) in state.animals_present
    if c_type == "species_absent":
        return str(condition.get("species")) not in state.animals_present

    target_val = float(condition.get("value", 0))
    cmp_op = condition.get("operator", ">=")

    if c_type == "coverage":
        actual = get_coverage(state, str(condition.get("plant")))
        return compare(actual, cmp_op, target_val)

    if c_type == "count":
        plant = condition.get("plant")
        if plant is not None:
            actual = state.counts[str(plant)]
        else:
            group = condition.get("species_group")
            if isinstance(group, list):
                actual = sum(state.counts[str(p)] for p in group)
            else:
                actual = get_group_count(state, str(group), classifications)
        return compare(actual, cmp_op, target_val)

    if c_type == "event":
        return str(condition.get("event")) in state.events

    return False


# ============================================================
# SPATIAL PLACEMENT OPTIMIZER
# ============================================================

def is_plantable(cell: Cell) -> bool:
    # Level 1 convention: terrain == 0 is plantable ground
    return cell.terrain == 0


def select_optimal_cells(
    plant: PlantInfo,
    cells: Dict[Tuple[int, int], Cell],
    used_positions: Set[Tuple[int, int]],
    amount: int,
    existing_coords: List[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    candidates = []

    for pos, cell in cells.items():
        if pos in used_positions or not is_plantable(cell):
            continue

        # Preferred soil match bonus
        is_preferred = (not plant.preferred_soil) or (cell.soil in plant.preferred_soil)

        # Spatial dispersion distance metric
        if existing_coords:
            # Distance to closest existing instance
            min_dist = min(math.hypot(pos[0] - ep[0], pos[1] - ep[1]) for ep in existing_coords)
        else:
            # Distance to center of the grid
            min_dist = math.hypot(pos[0] - 25, pos[1] - 25)

        # Higher score is better
        score = (2000.0 if is_preferred else 0.0) + min_dist * 10.0 + random.uniform(0.0, 1.0)
        candidates.append((score, pos[0], pos[1]))

    candidates.sort(reverse=True, key=lambda x: x[0])
    return [(r, c) for _, r, c in candidates[:amount]]


# ============================================================
# DYNAMIC TARGET ALLOCATION ENGINE
# ============================================================

def build_tick_targets(
    state: EcosystemState,
    unlocked: Set[str],
    plants: Dict[str, PlantInfo],
) -> List[Tuple[str, int]]:
    targets: List[Tuple[str, int]] = []

    # Priority Stage 1: Ecosystem Triggers (Loamcrawlers, Nectaris, Solwings, Virexids, Barkskips)
    req_grass = max(0, int(0.04 * state.total_grid_cells) + 1 - state.counts["Grass"])
    req_rose = max(0, 10 - state.counts["Rose Bush"])
    req_lavender = max(0, int(0.02 * state.total_grid_cells) + 1 - state.counts["Lavender"])
    req_sunflower = max(0, int(0.03 * state.total_grid_cells) + 1 - state.counts["Dwarf Sunflower"])
    req_oak = max(0, 8 - state.counts["Oak Tree"])

    if req_grass > 0 and "Grass" in unlocked:
        targets.append(("Grass", req_grass))
    if req_lavender > 0 and "Lavender" in unlocked:
        targets.append(("Lavender", req_lavender))
    if req_sunflower > 0 and "Dwarf Sunflower" in unlocked:
        targets.append(("Dwarf Sunflower", req_sunflower))
    if req_rose > 0 and "Rose Bush" in unlocked:
        targets.append(("Rose Bush", req_rose))
    if req_oak > 0 and "Oak Tree" in unlocked:
        targets.append(("Oak Tree", req_oak))

    # Priority Stage 2: Secondary Unlocks & Diversity Sowing
    if not targets:
        # Sort unlocked species by current count and growth maturity to maintain high Shannon diversity
        unlocked_list = [p for p in unlocked if p in plants]
        unlocked_list.sort(key=lambda p: (state.counts[p], plants[p].time_to_maturity))

        for plant_name in unlocked_list:
            if state.counts[plant_name] < 12:
                targets.append((plant_name, 12 - state.counts[plant_name]))

    return targets


# ============================================================
# MAIN SOLVER LOGIC
# ============================================================

def generate_solution(
    input_data: Dict[str, Any],
    cells: Dict[Tuple[int, int], Cell],
    plants: Dict[str, PlantInfo],
    unlocks: Dict[str, Dict[str, Any]],
    animals: Dict[str, Dict[str, Any]],
    classifications: Dict[str, Set[str]],
) -> List[Action]:
    ticks = int(input_data.get("ticks", 500))
    grid_size = len(cells) if cells else DEFAULT_GRID_SIZE

    state = EcosystemState(total_grid_cells=grid_size)
    unlocked: Set[str] = set()

    for p in STARTING_PLANTS:
        if p in plants:
            unlocked.add(p)

    used_positions: Set[Tuple[int, int]] = set()
    plant_positions: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
    actions: List[Action] = []

    plantable_count = sum(1 for c in cells.values() if is_plantable(c))
    print(f"[*] Starting simulation: {ticks} ticks, {plantable_count} plantable cells.")

    for tick in range(ticks):
        if len(used_positions) >= plantable_count:
            break

        # 1. Update Animals
        for a_name, a_data in animals.items():
            if a_name not in state.animals_present:
                if evaluate_animal(a_data, state, classifications):
                    state.animals_present.add(a_name)
                    print(f"  [Tick {tick:03d}] Animal Arrived: {a_name}")

        # 2. Update Plant Unlocks
        for p_name, p_info in plants.items():
            if p_name not in unlocked:
                condition = unlocks.get(p_name)
                if condition and evaluate_plant_condition(condition, state, classifications):
                    unlocked.add(p_name)
                    print(f"  [Tick {tick:03d}] Plant Unlocked: {p_name} (Index {p_info.index})")

        # 3. Dynamic Target Planning
        targets = build_tick_targets(state, unlocked, plants)

        # 4. Action Execution
        tick_action_count = 0
        for p_name, requested in targets:
            if tick_action_count >= MAX_PLANTS_PER_TICK:
                break
            if p_name not in unlocked or p_name not in plants:
                continue

            amount = min(requested, MAX_PLANTS_PER_TICK - tick_action_count)
            if amount <= 0:
                continue

            coords = select_optimal_cells(
                plants[p_name],
                cells,
                used_positions,
                amount,
                plant_positions[p_name],
            )

            for r, c in coords:
                actions.append(Action(tick=tick, plant=p_name, row=r, col=c))
                state.counts[p_name] += 1
                state.planted_species.add(p_name)
                used_positions.add((r, c))
                plant_positions[p_name].append((r, c))
                tick_action_count += 1
                if tick_action_count >= MAX_PLANTS_PER_TICK:
                    break

    return actions


# ============================================================
# SUBMISSION ENCODER & VALIDATOR
# ============================================================

def format_submission(actions: List[Action], plants: Dict[str, PlantInfo]) -> Dict[str, Any]:
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for a in actions:
        grouped[a.tick].append({
            "plant_index": plants[a.plant].index,
            "row": a.row,
            "col": a.col,
        })

    return {
        "actions": [
            {
                "tick": t,
                "plants": grouped[t],
            }
            for t in sorted(grouped.keys())
        ]
    }


def validate_submission(actions: List[Action], ticks: int, max_per_tick: int) -> None:
    counts_by_tick: Dict[int, int] = defaultdict(int)
    for a in actions:
        if a.tick < 0 or a.tick >= ticks:
            raise ValueError(f"Invalid tick {a.tick}")
        counts_by_tick[a.tick] += 1
        if counts_by_tick[a.tick] > max_per_tick:
            raise ValueError(f"Exceeded max actions per tick on tick {a.tick}")
    print("[+] Action validation passed successfully.")


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    random.seed(RANDOM_SEED)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Load Inputs
    input_path = os.path.join(script_dir, INPUT_FILE)
    if not os.path.exists(input_path):
        input_path = INPUT_FILE

    input_data = load_json(input_path)
    cells = parse_garden(input_data)

    # Load Resources
    plants_data = load_json(resolve_resource_path("plant_dataset.json"))
    unlocks_data = load_json(resolve_resource_path("plant_unlock_conditions.json"))
    animals_data = load_json(resolve_resource_path("animals.json"))
    classifications_data = load_json(resolve_resource_path("classifications.json"))

    # Parse Resources
    plants = parse_plant_catalogue(plants_data)
    unlocks = parse_unlock_conditions(unlocks_data)
    animals = parse_animals(animals_data)
    classifications = parse_classifications(classifications_data)

    # Execute Planner
    actions = generate_solution(
        input_data=input_data,
        cells=cells,
        plants=plants,
        unlocks=unlocks,
        animals=animals,
        classifications=classifications,
    )

    # Validate
    validate_submission(actions, int(input_data.get("ticks", 500)), MAX_PLANTS_PER_TICK)

    # Write Output
    submission_payload = format_submission(actions, plants)
    output_path = os.path.join(script_dir, OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(submission_payload, f, indent=2)

    print(f"[+] Output written to {output_path}")
    print(f"[+] Total Actions: {len(actions)}")
    print(f"[+] Active Ticks: {len(submission_payload['actions'])}")


if __name__ == "__main__":
    main()