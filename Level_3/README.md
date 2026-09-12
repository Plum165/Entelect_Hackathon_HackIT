# The Root Thing - Level 3

Level 3 is the 150 x 150, 800-tick plant-grid instance for the Entelect Hack<IT> Solo competition.

## Input

| Field | Value |
|---|---:|
| Input file | `3.json` |
| Rows | 150 |
| Columns | 150 |
| Ticks | 800 |
| Animals enabled | `true` |
| Supplied cells | 4,921 |
| Cells with `terrain == 0` | 1,253 |

Terrain frequencies are `0:1,253`, `1:1,669`, `2:1,461`, and `4:538`. Among plantable cells, soil frequencies are `1:716` and `2:537`.

The repository does not define semantic names for numeric terrain and soil values. The implementation uses only `terrain == 0` as its plantability test.

## Solver strategy

`level_3.py` loads the level dimensions, tick count, and cells dynamically. It places early count-trigger actions on ticks 0-2, then fills all 1,253 plantable cells from tick 702 using the seven-index pool:

```text
[1, 2, 4, 5, 6, 11, 12]
```

The final schedule is deterministic and balanced by cycling through that pool. Each tick contains at most 20 plant actions. The script reports the number of harvest actions, calculated Shannon entropy for that action pool, and the resulting lifespan range.

The local repository does not contain the official simulator or a complete scoring implementation. Reported entropy is a calculation over scheduled harvest actions, not a proof of the hidden evaluator's final score.

## Run

```powershell
cd Level_3
python level_3.py
```

The script writes `submission.json`. The checked-in run schedules 1,253 final-window planting actions from ticks 702-764, in addition to the early trigger actions.

## Files

- `3.json` - Level 3 grid input.
- `level_3.py` - solver.
- `submission.json` - generated actions.
- `Level_3.ipynb` - notebook work.
