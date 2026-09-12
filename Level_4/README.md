# Root Cause Analysis - Level 4

Level 4 is the largest checked-in plant-grid instance for the Entelect Hack<IT> Solo **Root Cause Analysis** challenge: a 200 x 300 grid running for 800 ticks. The objective is to cultivate the most diverse and long-lived final plant sample on Photospheria.

## Input

| Field | Value |
|---|---:|
| Input file | `4.json` |
| Rows | 200 |
| Columns | 300 |
| Ticks | 800 |
| Animals enabled | `true` |
| Supplied cells | 6,413 |
| Cells with `terrain == 0` | 1,191 |

Terrain frequencies are `0:1,191`, `1:3,418`, `2:1,076`, and `4:728`. Among plantable cells, soil frequencies are `1:425` and `2:766`.

Numeric terrain and soil meanings are not defined by the repository. The solver uses the explicit input-level test `terrain == 0` to select plantable coordinates.

## Solver strategy

`level_4.py` creates early count-trigger actions on ticks 0-2 and then fills all 1,191 plantable cells from tick 702 with the seven-index pool:

```text
[1, 2, 4, 5, 6, 11, 12]
```

Plant actions are grouped by tick and limited to 20 per tick. The deterministic schedule places the final-window actions from ticks 702-761. The script also prints the calculated entropy and lifespan range for the generated schedule.

These calculations describe the local submission generator. The official simulator, unlock semantics, nutrient behavior, and final score are not fully implemented in this repository.

## Run

```powershell
cd Level_4
python level_4.py
```

The script writes `submission.json` in the Level 4 directory.

## Files

- `4.json` - Level 4 grid input.
- `level_4.py` - solver.
- `submission.json` - generated plant actions.
- `4.txt` - separate checked-in competition data; it is not the input used by `level_4.py`.
