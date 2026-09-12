# The Root Thing - Level 1

Level 1 is the 50 x 50, 500-tick plant-grid instance for the Entelect Hack<IT> Solo competition. It is the only checked-in level input with `animals_enabled` set to `false`.

## Input

| Field | Value |
|---|---:|
| Input file | `1.json` |
| Rows | 50 |
| Columns | 50 |
| Ticks | 500 |
| Animals enabled | `false` |
| Supplied cells | 1,060 |
| Cells with `terrain == 0` | 720 |

Each supplied cell has `row`, `col`, `terrain`, and `soil` fields. The current input contains terrain frequencies `0:720`, `1:180`, and `2:160`. Among terrain-0 cells, soil frequencies are `1:360` and `2:360`.

The repository does not define the semantic names of these numeric terrain or soil values. The solver therefore uses only the explicit plantability rule in its code: `terrain == 0`.

## Solver

`level_1.py` loads `1.json`, extracts plantable coordinates, and schedules all 720 coordinates from tick 403 onward. It uses the five-index pool:

```text
[1, 2, 5, 6, 12]
```

The schedule is deterministic, uses no external packages, and limits each tick to 20 plants. The planting start is derived from the JSON tick count as `ticks - 97`, rather than being tied to the grid dimensions.

The local code does not simulate growth, nutrient depletion, unlocks, or final scoring. Those behaviors belong to the competition simulator and are not fully defined by this repository.

## Output

Running the solver creates `submission.json` with grouped actions:

```powershell
cd Level_1
python level_1.py
```

The output uses `plant_index`, `row`, and `col` for each plant action. The checked-in run produces 720 actions across ticks 403-438.

## Files

- `1.json` - Level 1 grid input.
- `level_1.py` - solver.
- `submission.json` - generated plant actions.
- `Level_1.ipynb` - notebook work.
- `JSON_REFERENCE.md` - detailed resource and JSON reference.
- `JSON_REFERENCE_PROMPT.md` - prompt for regenerating the reference.
