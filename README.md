# Entelect Hack<IT> - Root Cause Analysis

This repository contains preparation work and Python submissions for the Entelect Hack<IT> Solo competition. The challenge is **Root Cause Analysis**, set on the planet Photospheria. The objective is to build the most useful biological sample by cultivating a diverse and long-lived collection of plant species on a supplied grid.

<img width="1236" height="691" alt="Screenshot 2026-09-12 100009" src="https://github.com/user-attachments/assets/b68e918d-23f9-4df6-8b0f-a4a248a08c0f" />


## Repository status

The active level inputs are JSON files containing:

- grid dimensions and tick limits;
- an `animals_enabled` flag;
- supplied cells with `row`, `col`, `terrain`, and `soil` values.

The plant and ecosystem reference data is stored in `additional-resources/`:

- `plant_dataset.json` - plant indices and plant properties;
- `plant_unlock_conditions.json` - availability requirements;
- `animals.json` - ecosystem species, requirements, and effects;
- `classifications.json` - plant groups and classifications.

`Level_1/JSON_REFERENCE.md` is the detailed reference for these resources. `Level_1/JSON_REFERENCE_PROMPT.md` is a reusable prompt for regenerating that reference from the repository source files.

## Challenge objective

The simulation rewards final plant diversity and the longevity of plants that
remain alive at the end of the run. Plants interact through spreading,
competition, soil preference, environmental features, seasons, events, and,
when enabled, ecosystem species. Locked plants become available only when
their conditions are satisfied.

## Levels

| Level | Input | Grid | Ticks | Animals enabled | Plantable cells |
|---|---|---:|---:|---|---:|
| 1 | `Level_1/1.json` | 50 x 50 | 500 | No | 720 |
| 2 | `Level_2/2.json` | 70 x 100 | 500 | Yes | 411 |
| 3 | `Level_3/3.json` | 150 x 150 | 800 | Yes | 1,253 |
| 4 | `Level_4/4.json` | 200 x 300 | 800 | Yes | 1,191 |

The plantable-cell counts above are calculated from the checked-in inputs by counting cells whose `terrain` value is `0`. The repository does not define the semantic names of the numeric terrain and soil values in the JSON files.

## Solver approach

Each `level_n.py` file:

1. loads its matching level JSON dynamically;
2. extracts cells with `terrain == 0`;
3. creates grouped planting actions;
4. respects the 20-plant-per-tick limit used by the current solver;
5. writes `submission.json` in that level directory.

Levels 2-4 include early planting actions intended to satisfy count-based unlock conditions before the final planting window. Levels 3 and 4 distribute the seven-species pool `[1, 2, 4, 5, 6, 11, 12]`. Level 1 uses the five-species pool `[1, 2, 5, 6, 12]`.

These are solver strategies, not a replacement for the official simulator. The checked-in repository does not contain a complete local evaluator, so hidden-simulator rules must be confirmed against official challenge documentation.

## Running a level

Run each script from its own directory, or use an equivalent path:

```powershell
cd Level_1
python level_1.py
```

Repeat with `Level_2`, `Level_3`, or `Level_4` and the matching script. Each run regenerates that level's `submission.json`.

Python 3.8 or newer is recommended. The solvers use only the Python standard library.

## Submission format

The plant solvers write actions in this structure:

```json
{
  "actions": [
    {
      "tick": 403,
      "plants": [
        {
          "plant_index": 1,
          "row": 0,
          "col": 21
        }
      ]
    }
  ]
}
```

The current scripts group plant actions by tick and use zero-based row and column coordinates taken directly from the input cells.

## Documentation and limitations

The level READMEs document the actual checked-in inputs and implementations. Where the repository does not define a simulator rule, the documentation labels it as unknown rather than assigning a meaning to a numeric code.

<img width="3508" height="2480" alt="Moegamat_Samsodien_EH_Hack_IT__landscape" src="https://github.com/user-attachments/assets/682f1b24-d9a0-4931-80bc-6ccd94900bb7" />

