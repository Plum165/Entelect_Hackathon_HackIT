# Root Cause Analysis - Level 2

Level 2 is the 70 x 100, 500-tick plant-grid instance for the Entelect Hack<IT> Solo **Root Cause Analysis** challenge. The objective is to cultivate the most diverse and long-lived final plant sample on Photospheria.

## Input

| Field | Value |
|---|---:|
| Input file | `2.json` |
| Rows | 70 |
| Columns | 100 |
| Ticks | 500 |
| Animals enabled | `true` |
| Supplied cells | 1,110 |
| Cells with `terrain == 0` | 411 |

The input cells contain `row`, `col`, `terrain`, and `soil`. Terrain frequencies are `0:411`, `1:595`, and `2:104`. Among plantable cells, soil frequencies are `1:245` and `2:166`.

The resource files in `additional-resources/` define plant and ecosystem data. This README does not assign names to numeric terrain or soil codes because the repository does not define those meanings.

## Solver strategy

`level_2.py` dynamically loads `2.json` and creates two phases:

1. early count-based trigger actions over ticks 0-2 using Grass, Lavender, Oak Tree, and Rose Bush;
2. a final planting schedule using the seven-index pool `[1, 2, 4, 5, 6, 11, 12]`, beginning at `ticks - 97`.

Actions are grouped by tick and capped at 20 plants per tick. The script also checks that coordinates come from terrain-0 cells, ticks are in range, and a coordinate is not repeated within the same tick. A later tick may reuse an early trigger coordinate because the current strategy treats it as a later planting/replacement.

The repository does not include the official simulator, so this script cannot locally prove that every unlock and replacement is accepted by the evaluator.

## Run

```powershell
cd Level_2
python level_2.py
```

The script writes `submission.json`. The checked-in run generates 60 early trigger actions plus 411 final-window planting actions.

## Files

- `2.json` - Level 2 grid input.
- `level_2.py` - solver.
- `submission.json` - generated actions.
- `Level_2.ipynb` - notebook work.
