import json
import math
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "1.json"
OUTPUT_FILE = "submission.json"

RANDOM_SEED = 42

# Competition limit
MAX_PLANTS_PER_TICK = 20

# The official score uses the 50x50 grid as Cmax.
GRID_COVERAGE_DENOMINATOR = 2500

# Initial plants from the challenge rules.
STARTING_PLANTS = {
    "Grass",
    "Rose Bush",
    "Dwarf Sunflower",
    "Lavender",
    "Oak Tree",
}


# ============================================================
# PATHS
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCE_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "additional-resources")
)


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class Cell:
    row: int
    col: int
    terrain: Any = None
    soil: Any = None


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


# ============================================================
# FILE HELPERS
# ============================================================

def load_json_file(path: str) -> Optional[Any]:
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"ERROR reading {path}: {exc}")
        return None


def load_input() -> Dict[str, Any]:
    path = os.path.join(SCRIPT_DIR, INPUT_FILE)

    data = load_json_file(path)

    if data is None:
        raise FileNotFoundError(
            f"Could not load {path}"
        )

    return data


def load_resource(filename: str) -> Any:
    path = os.path.join(RESOURCE_DIR, filename)

    data = load_json_file(path)

    if data is None:
        raise FileNotFoundError(
            f"Could not load resource:\n{path}"
        )

    return data


# ============================================================
# GARDEN
# ============================================================

def parse_garden(data: Dict[str, Any]) -> Dict[Tuple[int, int], Cell]:

    cells = {}

    for raw in data.get("cells", []):

        try:
            row = int(raw["row"])
            col = int(raw["col"])
        except (KeyError, TypeError, ValueError):
            continue

        cells[(row, col)] = Cell(
            row=row,
            col=col,
            terrain=raw.get("terrain"),
            soil=raw.get("soil"),
        )

    return cells


# ============================================================
# PLANT DATASET
# ============================================================

def parse_plant_catalogue(
    data: Any,
) -> Dict[str, PlantInfo]:

    plants = {}

    if not isinstance(data, list):
        print("ERROR: plant_dataset.json is not a list.")
        return plants

    for raw in data:

        if not isinstance(raw, dict):
            continue

        name = raw.get("plant")
        index = raw.get("index")

        if name is None or index is None:
            continue

        try:
            index = int(index)
        except (TypeError, ValueError):
            continue

        growth = raw.get("growth", {})

        if not isinstance(growth, dict):
            growth = {}

        preferred_soil = raw.get(
            "preferred_soil",
            [],
        )

        if not isinstance(preferred_soil, list):
            preferred_soil = []

        plants[str(name)] = PlantInfo(
            index=index,
            name=str(name),
            raw=raw,
            time_to_maturity=float(
                growth.get("time_to_maturity", 1)
            ),
            spread_rate=float(
                growth.get("spread_rate", 0)
            ),
            spread_range=float(
                growth.get("spread_range", 0)
            ),
            invasiveness_rank=float(
                growth.get("invasiveness_rank", 0)
            ),
            preferred_soil=preferred_soil,
        )

    return plants


# ============================================================
# CLASSIFICATIONS
# ============================================================

def parse_classifications(data: Any) -> Dict[str, Set[str]]:

    result = {}

    if not isinstance(data, dict):
        return result

    for group, members in data.items():

        if not isinstance(members, list):
            continue

        result[str(group)] = {
            str(member)
            for member in members
        }

    return result


def build_group_lookup(
    classifications: Dict[str, Set[str]]
) -> Dict[str, Set[str]]:

    lookup = {}

    for group, members in classifications.items():

        for plant in members:
            lookup.setdefault(plant, set()).add(group)

    return lookup


# ============================================================
# ANIMAL / ECOSYSTEM CONDITIONS
# ============================================================

def parse_animals(data: Any) -> Dict[str, Dict[str, Any]]:

    animals = {}

    if not isinstance(data, list):
        return animals

    for animal in data:

        if not isinstance(animal, dict):
            continue

        name = animal.get("name")

        if name:
            animals[str(name)] = animal

    return animals


def compare(
    actual: float,
    operator: str,
    target: float,
) -> bool:

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


# ============================================================
# UNLOCK STATE
# ============================================================

@dataclass
class EcosystemState:

    counts: Dict[str, int] = field(default_factory=dict)

    planted_species: Set[str] = field(default_factory=set)

    animals_present: Set[str] = field(default_factory=set)

    events: Set[str] = field(default_factory=set)


def coverage(
    state: EcosystemState,
    plant: str,
) -> float:

    count = state.counts.get(plant, 0)

    return count / GRID_COVERAGE_DENOMINATOR


def group_count(
    state: EcosystemState,
    group: str,
    classifications: Dict[str, Set[str]],
) -> int:

    members = classifications.get(group, set())

    return sum(
        state.counts.get(plant, 0)
        for plant in members
    )


def group_coverage(
    state: EcosystemState,
    group: str,
    classifications: Dict[str, Set[str]],
) -> float:

    return (
        group_count(
            state,
            group,
            classifications,
        )
        / GRID_COVERAGE_DENOMINATOR
    )


# ============================================================
# ANIMAL UNLOCK EVALUATION
# ============================================================

def evaluate_animal_condition(
    condition: Dict[str, Any],
    state: EcosystemState,
    classifications: Dict[str, Set[str]],
) -> bool:

    if not isinstance(condition, dict):
        return False

    condition_type = condition.get("type")

    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    if condition_type == "coverage":

        species = condition.get("species", [])

        if not species:
            return False

        # Animal JSON uses a list here.
        plant = str(species[0])

        actual = coverage(
            state,
            plant,
        )

        threshold = float(
            condition.get("threshold", 0)
        )

        operator = condition.get(
            "operator",
            ">=",
        )

        return compare(
            actual,
            operator,
            threshold,
        )

    # --------------------------------------------------------
    # Group coverage
    # --------------------------------------------------------

    if condition_type == "group_coverage":

        group = condition.get(
            "species_group",
            [],
        )

        # In animals.json this field can contain the
        # actual members rather than a classification name.
        if isinstance(group, list):

            actual_count = sum(
                state.counts.get(str(plant), 0)
                for plant in group
            )

        else:
            actual_count = group_count(
                state,
                str(group),
                classifications,
            )

        actual = (
            actual_count
            / GRID_COVERAGE_DENOMINATOR
        )

        threshold = float(
            condition.get("threshold", 0)
        )

        operator = condition.get(
            "operator",
            ">=",
        )

        return compare(
            actual,
            operator,
            threshold,
        )

    # --------------------------------------------------------
    # Count
    # --------------------------------------------------------

    if condition_type == "count":

        if "species" in condition:

            actual = state.counts.get(
                str(condition["species"]),
                0,
            )

        elif "species_group" in condition:

            group = condition["species_group"]

            if isinstance(group, list):

                actual = sum(
                    state.counts.get(
                        str(plant),
                        0,
                    )
                    for plant in group
                )

            else:

                actual = group_count(
                    state,
                    str(group),
                    classifications,
                )

        else:
            return False

        threshold = float(
            condition.get("threshold", 0)
        )

        operator = condition.get(
            "operator",
            ">=",
        )

        return compare(
            actual,
            operator,
            threshold,
        )

    # --------------------------------------------------------
    # Dominance
    # --------------------------------------------------------

    if condition_type == "dominance":

        total = sum(state.counts.values())

        if total <= 0:
            return False

        if condition.get("mode") == "single_species":

            largest = max(
                state.counts.values(),
                default=0,
            )

            dominance = largest / total

            threshold = float(
                condition.get("threshold", 0)
            )

            return dominance >= threshold

    return False


def evaluate_animal_requirements(
    animal: Dict[str, Any],
    state: EcosystemState,
    classifications: Dict[str, Set[str]],
) -> bool:

    requirements = animal.get(
        "requirements",
        {},
    )

    if not isinstance(requirements, dict):
        return False

    operation = requirements.get(
        "type",
        "AND",
    )

    conditions = requirements.get(
        "conditions",
        [],
    )

    results = [
        evaluate_animal_condition(
            condition,
            state,
            classifications,
        )
        for condition in conditions
    ]

    if operation == "OR":
        return any(results)

    return all(results)


# ============================================================
# PLANT UNLOCK EVALUATION
# ============================================================

def evaluate_plant_condition(
    condition: Any,
    state: EcosystemState,
    classifications: Dict[str, Set[str]],
) -> bool:

    if not isinstance(condition, dict):
        return False

    # --------------------------------------------------------
    # Boolean tree
    # --------------------------------------------------------

    operation = condition.get("op")

    if operation in ("AND", "and"):

        return all(
            evaluate_plant_condition(
                child,
                state,
                classifications,
            )
            for child in condition.get(
                "children",
                [],
            )
        )

    if operation in ("OR", "or"):

        return any(
            evaluate_plant_condition(
                child,
                state,
                classifications,
            )
            for child in condition.get(
                "children",
                [],
            )
        )

    if operation in ("NOT", "not"):

        children = condition.get(
            "children",
            [],
        )

        return not all(
            evaluate_plant_condition(
                child,
                state,
                classifications,
            )
            for child in children
        )

    # --------------------------------------------------------
    # Leaf conditions
    # --------------------------------------------------------

    condition_type = condition.get("type")

    if condition_type == "species_present":

        species = str(
            condition.get("species")
        )

        return species in state.animals_present

    if condition_type == "species_absent":

        species = str(
            condition.get("species")
        )

        return species not in state.animals_present

    if condition_type == "coverage":

        plant = str(
            condition.get("plant")
        )

        actual = coverage(
            state,
            plant,
        )

        target = float(
            condition.get("value", 0)
        )

        return compare(
            actual,
            condition.get(
                "operator",
                ">=",
            ),
            target,
        )

    if condition_type == "count":

        plant = condition.get("plant")

        if plant is not None:

            actual = state.counts.get(
                str(plant),
                0,
            )

        else:

            group = condition.get(
                "species_group"
            )

            if isinstance(group, list):

                actual = sum(
                    state.counts.get(
                        str(x),
                        0,
                    )
                    for x in group
                )

            else:
                actual = group_count(
                    state,
                    str(group),
                    classifications,
                )

        target = float(
            condition.get("value", 0)
        )

        return compare(
            actual,
            condition.get(
                "operator",
                ">=",
            ),
            target,
        )

    if condition_type == "feature_count":

        feature = condition.get("feature")

        # These environmental features are represented by
        # cell metadata in some level configurations.
        # We handle known features separately elsewhere.
        actual = state.counts.get(
            f"__feature__{feature}",
            0,
        )

        target = float(
            condition.get("value", 0)
        )

        return compare(
            actual,
            condition.get(
                "operator",
                ">=",
            ),
            target,
        )

    if condition_type == "event":

        event = str(
            condition.get("event")
        )

        return event in state.events

    return False


def parse_unlock_conditions(
    data: Any,
) -> Dict[str, Dict[str, Any]]:

    result = {}

    if not isinstance(data, list):
        return result

    for entry in data:

        if not isinstance(entry, dict):
            continue

        plant = entry.get("plant")
        unlock = entry.get("unlock")

        if plant and isinstance(unlock, dict):
            result[str(plant)] = unlock

    return result


# ============================================================
# TERRAIN / PLACEMENT RULES
# ============================================================

def get_rules(
    plant: PlantInfo,
) -> Dict[str, Any]:

    rules = plant.raw.get(
        "rules",
        {},
    )

    if isinstance(rules, dict):
        return rules

    return {}


def is_burnt_soil(cell: Cell) -> bool:

    # Dataset represents burnt soil as a soil ID where
    # applicable. We don't invent a new ID here.
    #
    # This function intentionally returns False unless the
    # input explicitly labels it.
    if isinstance(cell.soil, str):
        return cell.soil.lower() in {
            "burnt",
            "burnt_soil",
        }

    return False


def is_water(cell: Cell) -> bool:

    if isinstance(cell.terrain, str):
        return cell.terrain.lower() in {
            "water",
            "lake",
            "river",
            "wetland",
        }

    return False


def is_rock_or_path(cell: Cell) -> bool:

    if isinstance(cell.terrain, str):
        return cell.terrain.lower() in {
            "rock",
            "path",
            "rock_or_path",
        }

    return False


def is_plantable_cell(
    cell: Cell,
) -> bool:

    # The Level 1 instance uses numeric terrain IDs.
    #
    # Terrain 0 is treated as ordinary plantable ground.
    # Terrain 1 and 2 are environmental terrain and are
    # reserved for adjacency/special interactions.
    #
    # This avoids the previous solver's mistake of assuming
    # every supplied cell is plantable.
    return cell.terrain == 0


def adjacent_cells(
    cell: Cell,
    cells: Dict[Tuple[int, int], Cell],
) -> List[Cell]:

    result = []

    for dr, dc in (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    ):

        neighbour = cells.get(
            (cell.row + dr, cell.col + dc)
        )

        if neighbour is not None:
            result.append(neighbour)

    return result


def cell_satisfies_special_rule(
    plant: PlantInfo,
    cell: Cell,
    cells: Dict[Tuple[int, int], Cell],
) -> bool:

    rules = get_rules(plant)

    # --------------------------------------------------------
    # Water adjacency
    # --------------------------------------------------------

    if rules.get(
        "must_be_adjacent_to_water"
    ):

        if not any(
            is_water(neighbour)
            for neighbour in adjacent_cells(
                cell,
                cells,
            )
        ):
            return False

    # --------------------------------------------------------
    # Rock/path adjacency
    # --------------------------------------------------------

    if rules.get(
        "must_be_adjacent_to_rock_or_path"
    ):

        if not any(
            is_rock_or_path(neighbour)
            for neighbour in adjacent_cells(
                cell,
                cells,
            )
        ):
            return False

    # --------------------------------------------------------
    # Burnt soil
    # --------------------------------------------------------

    if rules.get(
        "must_be_burnt_soil"
    ):

        if not is_burnt_soil(cell):
            return False

    return True


def soil_is_preferred(
    plant: PlantInfo,
    cell: Cell,
) -> bool:

    if not plant.preferred_soil:
        return True

    return cell.soil in plant.preferred_soil


# ============================================================
# PLACEMENT ENGINE
# ============================================================

def choose_cells_for_plant(
    plant: PlantInfo,
    cells: Dict[Tuple[int, int], Cell],
    used_positions: Set[Tuple[int, int]],
    amount: int,
    existing_positions: List[Tuple[int, int]],
) -> List[Tuple[int, int]]:

    candidates = []

    for cell in cells.values():

        pos = (
            cell.row,
            cell.col,
        )

        if pos in used_positions:
            continue

        if not is_plantable_cell(cell):
            continue

        if not cell_satisfies_special_rule(
            plant,
            cell,
            cells,
        ):
            continue

        preferred = soil_is_preferred(
            plant,
            cell,
        )

        # Spread candidates around the map rather than
        # putting everything into one small area.
        if existing_positions:

            nearest = min(
                math.dist(
                    pos,
                    existing,
                )
                for existing in existing_positions
            )

        else:
            nearest = 9999.0

        # Preferred soil is strongly favoured.
        score = (
            (100000 if preferred else 0)
            + nearest
            + random.random()
        )

        candidates.append(
            (
                score,
                cell.row,
                cell.col,
            )
        )

    candidates.sort(
        reverse=True
    )

    return [
        (row, col)
        for _, row, col in candidates[:amount]
    ]


# ============================================================
# EVENT DETECTION
# ============================================================

def detect_events(
    data: Dict[str, Any],
) -> Set[str]:

    events = set()

    # Search the input recursively for explicit event names.
    def walk(obj: Any):

        if isinstance(obj, dict):

            for key, value in obj.items():

                if isinstance(value, str):

                    if value in {
                        "Drought",
                        "Rain",
                        "Ash Eclipse",
                    }:
                        events.add(value)

                walk(value)

        elif isinstance(obj, list):

            for value in obj:
                walk(value)

    walk(data)

    return events


# ============================================================
# STATE UPDATE
# ============================================================

def apply_action(
    state: EcosystemState,
    action: Action,
) -> None:

    state.counts[action.plant] = (
        state.counts.get(
            action.plant,
            0,
        )
        + 1
    )

    state.planted_species.add(
        action.plant
    )


def update_animals(
    state: EcosystemState,
    animals: Dict[str, Dict[str, Any]],
    classifications: Dict[str, Set[str]],
) -> List[str]:

    newly_unlocked = []

    for name, animal in animals.items():

        if name in state.animals_present:
            continue

        if evaluate_animal_requirements(
            animal,
            state,
            classifications,
        ):

            state.animals_present.add(
                name
            )

            newly_unlocked.append(
                name
            )

    return newly_unlocked


# ============================================================
# UNLOCK DEPENDENCY SOLVER
# ============================================================

def find_newly_unlocked_plants(
    state: EcosystemState,
    plants: Dict[str, PlantInfo],
    unlocks: Dict[str, Dict[str, Any]],
    classifications: Dict[str, Set[str]],
    unlocked: Set[str],
) -> List[str]:

    newly_unlocked = []

    for plant_name in plants:

        if plant_name in unlocked:
            continue

        # Starting plants are available immediately.
        if plant_name in STARTING_PLANTS:

            unlocked.add(
                plant_name
            )

            newly_unlocked.append(
                plant_name
            )

            continue

        unlock = unlocks.get(
            plant_name
        )

        if unlock is None:
            continue

        if evaluate_plant_condition(
            unlock,
            state,
            classifications,
        ):

            unlocked.add(
                plant_name
            )

            newly_unlocked.append(
                plant_name
            )

    return newly_unlocked


# ============================================================
# TARGET PLANNING
# ============================================================

def required_count_for_coverage(
    threshold: float,
) -> int:

    # Strict ">" threshold:
    return math.floor(
        threshold
        * GRID_COVERAGE_DENOMINATOR
    ) + 1


def target_initial_coverage(
    state: EcosystemState,
    plant: str,
    threshold: float,
) -> int:

    required = required_count_for_coverage(
        threshold
    )

    current = state.counts.get(
        plant,
        0,
    )

    return max(
        0,
        required - current,
    )


def build_priority_plan(
    state: EcosystemState,
    unlocked: Set[str],
    plants: Dict[str, PlantInfo],
) -> List[Tuple[str, int]]:

    """
    Build targets that deliberately unlock the dependency
    graph rather than randomly planting all species.

    We prioritise the earliest unlock bottlenecks.
    """

    targets = []

    # --------------------------------------------------------
    # Stage 1: create ecosystem triggers
    # --------------------------------------------------------

    # Loamcrawlers:
    # Grass >= 4%, Rose >= 10
    targets.append(
        (
            "Grass",
            target_initial_coverage(
                state,
                "Grass",
                0.04,
            ),
        )
    )

    targets.append(
        (
            "Rose Bush",
            max(
                0,
                10
                - state.counts.get(
                    "Rose Bush",
                    0,
                ),
            ),
        )
    )

    # Nectaris:
    # Lavender >= 2%
    targets.append(
        (
            "Lavender",
            target_initial_coverage(
                state,
                "Lavender",
                0.02,
            ),
        )
    )

    # Solwings:
    # Sunflower >= 3%, Rose >= 2%
    targets.append(
        (
            "Dwarf Sunflower",
            target_initial_coverage(
                state,
                "Dwarf Sunflower",
                0.03,
            ),
        )
    )

    targets.append(
        (
            "Rose Bush",
            target_initial_coverage(
                state,
                "Rose Bush",
                0.02,
            ),
        )
    )

    # Virexids:
    # Lavender >= 10 and Grass >= 10
    targets.append(
        (
            "Lavender",
            max(
                0,
                10
                - state.counts.get(
                    "Lavender",
                    0,
                ),
            ),
        )
    )

    targets.append(
        (
            "Grass",
            max(
                0,
                10
                - state.counts.get(
                    "Grass",
                    0,
                ),
            ),
        )
    )

    # Barkskips:
    # Oak >= 8
    targets.append(
        (
            "Oak Tree",
            max(
                0,
                8
                - state.counts.get(
                    "Oak Tree",
                    0,
                ),
            ),
        )
    )

    # --------------------------------------------------------
    # Only use currently unlocked plants
    # --------------------------------------------------------

    filtered = []

    for plant, amount in targets:

        if (
            amount > 0
            and plant in unlocked
            and plant in plants
        ):
            filtered.append(
                (
                    plant,
                    amount,
                )
            )

    return filtered


# ============================================================
# FALLBACK DIVERSITY TARGETS
# ============================================================

def choose_diversity_targets(
    state: EcosystemState,
    unlocked: Set[str],
    plants: Dict[str, PlantInfo],
) -> List[Tuple[str, int]]:

    result = []

    # Once unlocks are happening, maintain representation
    # across unlocked species instead of allowing Grass/Rose
    # to dominate the final ecosystem.

    unlocked_plants = [
        name
        for name in unlocked
        if name in plants
    ]

    unlocked_plants.sort(
        key=lambda name: (
            state.counts.get(name, 0),
            plants[name].time_to_maturity,
        )
    )

    for plant in unlocked_plants:

        current = state.counts.get(
            plant,
            0,
        )

        # Give each newly unlocked species a meaningful
        # starting population.
        if current == 0:
            result.append(
                (
                    plant,
                    5,
                )
            )

    return result


# ============================================================
# MAIN PLANNER
# ============================================================

def generate_actions(
    data: Dict[str, Any],
    cells: Dict[Tuple[int, int], Cell],
    plants: Dict[str, PlantInfo],
    unlocks: Dict[str, Dict[str, Any]],
    animals: Dict[str, Dict[str, Any]],
    classifications: Dict[str, Set[str]],
) -> List[Action]:

    ticks = int(
        data.get(
            "ticks",
            500,
        )
    )

    state = EcosystemState()

    # Known environmental events, if explicitly present.
    state.events.update(
        detect_events(data)
    )

    unlocked = set()

    # --------------------------------------------------------
    # Initial unlocked plants
    # --------------------------------------------------------

    for plant in STARTING_PLANTS:

        if plant in plants:
            unlocked.add(
                plant
            )

    print(
        "\nInitial unlocked plants:"
    )

    for plant in sorted(unlocked):
        print(
            f"  [{plants[plant].index:2}] {plant}"
        )

    # --------------------------------------------------------
    # Prepare cells
    # --------------------------------------------------------

    plantable_cells = [
        cell
        for cell in cells.values()
        if is_plantable_cell(cell)
    ]

    print(
        f"\nPlantable terrain-0 cells: "
        f"{len(plantable_cells)}"
    )

    if not plantable_cells:
        raise RuntimeError(
            "No plantable terrain-0 cells found."
        )

    random.seed(RANDOM_SEED)
    random.shuffle(plantable_cells)

    used_positions: Set[
        Tuple[int, int]
    ] = set()

    positions_by_plant: Dict[
        str,
        List[Tuple[int, int]]
    ] = {}

    actions: List[Action] = []

    # --------------------------------------------------------
    # We use the first part of the run to establish the
    # ecosystem needed for unlocks.
    # --------------------------------------------------------

    print("\n=== Unlock preparation ===")

    for tick in range(
        min(ticks, 100)
    ):

        tick_actions = 0

        # ----------------------------------------------------
        # Update animal state
        # ----------------------------------------------------

        newly_animals = update_animals(
            state,
            animals,
            classifications,
        )

        for animal in newly_animals:

            print(
                f"  Ecosystem unlocked: "
                f"{animal}"
            )

        # ----------------------------------------------------
        # Update plant unlocks
        # ----------------------------------------------------

        newly_plants = find_newly_unlocked_plants(
            state,
            plants,
            unlocks,
            classifications,
            unlocked,
        )

        for plant in newly_plants:

            print(
                f"  Plant unlocked: "
                f"{plant} "
                f"(index {plants[plant].index})"
            )

        # ----------------------------------------------------
        # Priority targets
        # ----------------------------------------------------

        targets = build_priority_plan(
            state,
            unlocked,
            plants,
        )

        # After the major ecosystem triggers are established,
        # start adding newly unlocked species.
        if not targets:

            targets = choose_diversity_targets(
                state,
                unlocked,
                plants,
            )

        # ----------------------------------------------------
        # Plant up to 20 this tick
        # ----------------------------------------------------

        for plant_name, requested in targets:

            if tick_actions >= MAX_PLANTS_PER_TICK:
                break

            if plant_name not in unlocked:
                continue

            if plant_name not in plants:
                continue

            amount = min(
                requested,
                MAX_PLANTS_PER_TICK
                - tick_actions,
            )

            if amount <= 0:
                continue

            existing = positions_by_plant.setdefault(
                plant_name,
                [],
            )

            chosen = choose_cells_for_plant(
                plants[plant_name],
                cells,
                used_positions,
                amount,
                existing,
            )

            for row, col in chosen:

                action = Action(
                    tick=tick,
                    plant=plant_name,
                    row=row,
                    col=col,
                )

                actions.append(action)

                apply_action(
                    state,
                    action,
                )

                used_positions.add(
                    (row, col)
                )

                existing.append(
                    (row, col)
                )

                tick_actions += 1

                if tick_actions >= MAX_PLANTS_PER_TICK:
                    break

        # ----------------------------------------------------
        # If no priority action was required, continue with
        # controlled diversity.
        # ----------------------------------------------------

        if tick_actions == 0:

            targets = choose_diversity_targets(
                state,
                unlocked,
                plants,
            )

            for plant_name, requested in targets:

                if tick_actions >= MAX_PLANTS_PER_TICK:
                    break

                if plant_name not in plants:
                    continue

                amount = min(
                    requested,
                    MAX_PLANTS_PER_TICK
                    - tick_actions,
                )

                chosen = choose_cells_for_plant(
                    plants[plant_name],
                    cells,
                    used_positions,
                    amount,
                    positions_by_plant.get(
                        plant_name,
                        [],
                    ),
                )

                for row, col in chosen:

                    action = Action(
                        tick=tick,
                        plant=plant_name,
                        row=row,
                        col=col,
                    )

                    actions.append(action)

                    apply_action(
                        state,
                        action,
                    )

                    used_positions.add(
                        (row, col)
                    )

                    positions_by_plant.setdefault(
                        plant_name,
                        [],
                    ).append(
                        (row, col)
                    )

                    tick_actions += 1

                    if tick_actions >= MAX_PLANTS_PER_TICK:
                        break

        # ----------------------------------------------------
        # Stop early if every plantable cell is occupied.
        # ----------------------------------------------------

        if len(used_positions) >= len(
            plantable_cells
        ):
            break

    # ========================================================
    # SECOND PHASE
    # ========================================================

    print("\n=== Diversity expansion ===")

    for tick in range(
        min(ticks, 100),
        ticks,
    ):

        if len(used_positions) >= len(
            plantable_cells
        ):
            break

        # Re-evaluate ecosystem.
        newly_animals = update_animals(
            state,
            animals,
            classifications,
        )

        for animal in newly_animals:
            print(
                f"  Ecosystem unlocked: "
                f"{animal}"
            )

        newly_plants = find_newly_unlocked_plants(
            state,
            plants,
            unlocks,
            classifications,
            unlocked,
        )

        for plant in newly_plants:
            print(
                f"  Plant unlocked: "
                f"{plant}"
            )

        targets = choose_diversity_targets(
            state,
            unlocked,
            plants,
        )

        # If every unlocked species already has a presence,
        # fill selectively using underrepresented species.
        if not targets:

            candidates = sorted(
                (
                    plant
                    for plant in unlocked
                    if plant in plants
                ),
                key=lambda name:
                    state.counts.get(
                        name,
                        0,
                    ),
            )

            targets = [
                (
                    name,
                    1,
                )
                for name in candidates[:10]
            ]

        tick_actions = 0

        for plant_name, requested in targets:

            if tick_actions >= MAX_PLANTS_PER_TICK:
                break

            if plant_name not in plants:
                continue

            # We deliberately use a small number per species
            # here to preserve diversity.
            amount = min(
                requested,
                3,
                MAX_PLANTS_PER_TICK
                - tick_actions,
            )

            chosen = choose_cells_for_plant(
                plants[plant_name],
                cells,
                used_positions,
                amount,
                positions_by_plant.get(
                    plant_name,
                    [],
                ),
            )

            for row, col in chosen:

                action = Action(
                    tick=tick,
                    plant=plant_name,
                    row=row,
                    col=col,
                )

                actions.append(action)

                apply_action(
                    state,
                    action,
                )

                used_positions.add(
                    (row, col)
                )

                positions_by_plant.setdefault(
                    plant_name,
                    [],
                ).append(
                    (row, col)
                )

                tick_actions += 1

                if tick_actions >= MAX_PLANTS_PER_TICK:
                    break

    return actions


# ============================================================
# VALIDATION
# ============================================================

def validate_actions(
    actions: List[Action],
    cells: Dict[Tuple[int, int], Cell],
    plants: Dict[str, PlantInfo],
    ticks: int,
) -> None:

    if not actions:
        raise ValueError(
            "No actions generated."
        )

    by_tick: Dict[int, int] = {}

    occupied: Set[
        Tuple[int, int]
    ] = set()

    for action in actions:

        if action.tick < 0 or action.tick >= ticks:
            raise ValueError(
                f"Invalid tick: {action.tick}"
            )

        if action.plant not in plants:
            raise ValueError(
                f"Unknown plant: {action.plant}"
            )

        pos = (
            action.row,
            action.col,
        )

        if pos not in cells:
            raise ValueError(
                f"Cell {pos} does not exist."
            )

        if not is_plantable_cell(
            cells[pos]
        ):
            raise ValueError(
                f"Cell {pos} is not plantable "
                f"(terrain={cells[pos].terrain})."
            )

        by_tick[action.tick] = (
            by_tick.get(
                action.tick,
                0,
            )
            + 1
        )

        if by_tick[action.tick] > MAX_PLANTS_PER_TICK:
            raise ValueError(
                f"Tick {action.tick} contains "
                f"{by_tick[action.tick]} plants."
            )

        # We don't reject repeated positions globally because
        # the official rules permit replacement.
        occupied.add(pos)


# ============================================================
# SUBMISSION CONVERSION
# ============================================================

def create_submission(
    actions: List[Action],
    plants: Dict[str, PlantInfo],
) -> Dict[str, Any]:

    grouped: Dict[
        int,
        List[Dict[str, Any]]
    ] = {}

    for action in actions:

        grouped.setdefault(
            action.tick,
            [],
        ).append(
            {
                "plant_index": plants[
                    action.plant
                ].index,
                "row": action.row,
                "col": action.col,
            }
        )

    return {
        "actions": [
            {
                "tick": tick,
                "plants": grouped[tick],
            }
            for tick in sorted(grouped)
        ]
    }


# ============================================================
# REPORT
# ============================================================

def print_report(
    actions: List[Action],
    plants: Dict[str, PlantInfo],
) -> None:

    counts: Dict[str, int] = {}

    for action in actions:

        counts[action.plant] = (
            counts.get(
                action.plant,
                0,
            )
            + 1
        )

    print("\n=== FINAL ACTION REPORT ===")

    print(
        f"Total actions: {len(actions)}"
    )

    print(
        f"Distinct planted species: "
        f"{len(counts)}"
    )

    print("\nPlant counts:")

    for name in sorted(
        counts,
        key=lambda x: plants[x].index,
    ):

        print(
            f"  {plants[name].index:2} "
            f"{name:<25} "
            f"{counts[name]:4}"
        )

    print("\nCoverage estimates:")

    for name in sorted(
        counts,
        key=lambda x: plants[x].index,
    ):

        value = (
            counts[name]
            / GRID_COVERAGE_DENOMINATOR
        )

        print(
            f"  {name:<25} "
            f"{value:.2%}"
        )


# ============================================================
# MAIN
# ============================================================

def solve() -> None:

    print("=" * 60)
    print("ENTELECT UNIVERSITY CUP 2 - LEVEL 1 SOLVER")
    print("=" * 60)

    # --------------------------------------------------------
    # Load files
    # --------------------------------------------------------

    data = load_input()

    plant_dataset = load_resource(
        "plant_dataset.json"
    )

    unlock_dataset = load_resource(
        "plant_unlock_conditions.json"
    )

    animal_dataset = load_resource(
        "animals.json"
    )

    classification_dataset = load_resource(
        "classifications.json"
    )

    # --------------------------------------------------------
    # Parse
    # --------------------------------------------------------

    cells = parse_garden(data)

    plants = parse_plant_catalogue(
        plant_dataset
    )

    unlocks = parse_unlock_conditions(
        unlock_dataset
    )

    animals = parse_animals(
        animal_dataset
    )

    classifications = parse_classifications(
        classification_dataset
    )

    # --------------------------------------------------------
    # Basic information
    # --------------------------------------------------------

    rows = int(
        data.get("rows", 0)
    )

    cols = int(
        data.get("cols", 0)
    )

    ticks = int(
        data.get("ticks", 0)
    )

    print(
        f"\nGrid: {rows} x {cols}"
    )

    print(
        f"Ticks: {ticks}"
    )

    print(
        f"Cells supplied: {len(cells)}"
    )

    print(
        f"Plant catalogue: {len(plants)}"
    )

    print(
        f"Plant unlock rules: {len(unlocks)}"
    )

    print(
        f"Ecosystem species: {len(animals)}"
    )

    # --------------------------------------------------------
    # Terrain report
    # --------------------------------------------------------

    terrain_counts: Dict[Any, int] = {}

    for cell in cells.values():

        terrain_counts[cell.terrain] = (
            terrain_counts.get(
                cell.terrain,
                0,
            )
            + 1
        )

    print("\nTerrain:")

    for terrain, count in sorted(
        terrain_counts.items(),
        key=lambda x: str(x[0]),
    ):

        print(
            f"  {terrain}: {count}"
        )

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    actions = generate_actions(
        data,
        cells,
        plants,
        unlocks,
        animals,
        classifications,
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    print(
        "\nValidating generated actions..."
    )

    validate_actions(
        actions,
        cells,
        plants,
        ticks,
    )

    print(
        "Local validation: PASS"
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print_report(
        actions,
        plants,
    )

    # --------------------------------------------------------
    # Official format
    # --------------------------------------------------------

    submission = create_submission(
        actions,
        plants,
    )

    output_path = os.path.join(
        SCRIPT_DIR,
        OUTPUT_FILE,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            submission,
            f,
            indent=2,
        )

    print(
        "\n" + "=" * 60
    )

    print(
        f"SUCCESS: wrote {output_path}"
    )

    print(
        f"Actions: {len(actions)}"
    )

    print(
        f"Ticks used: "
        f"{len(set(a.tick for a in actions))}"
    )

    print("=" * 60)


def main():

    random.seed(
        RANDOM_SEED
    )

    try:
        solve()

    except Exception as exc:

        print()
        print(
            "ERROR:"
        )
        print(
            str(exc)
        )

        sys.exit(1)


if __name__ == "__main__":
    main()