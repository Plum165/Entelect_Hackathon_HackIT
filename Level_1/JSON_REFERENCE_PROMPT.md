# Prompt: Generate the Level 1 JSON Reference

You are working inside my Entelect University Cup 2 / HackIT repository.

Create a comprehensive Markdown document at:

`Level_1/JSON_REFERENCE.md`

The document must explain everything important about the JSON and resource files used by Level 1. It must be detailed enough that another developer or AI coding assistant can understand the challenge data and build a correct solver without repeatedly opening the source JSON files.

## Non-negotiable source and accuracy rules

1. Inspect the actual repository files before writing the document.
2. Base every claim only on information explicitly present in the files.
3. Treat the JSON files as authoritative when prose documentation is stale or contradictory.
4. Inspect at least these files:
   - `Level_1/1.json`
   - `Level_1/level_1.py`
   - `additional-resources/plant_dataset.json`
   - `additional-resources/plant_unlock_conditions.json`
   - `additional-resources/animals.json`
   - `additional-resources/classifications.json`
5. Also inspect any other Level 1 documentation, submission examples, or code that explains how the resources are interpreted.
6. Do not modify the solver or any existing source file. For this task, create only `Level_1/JSON_REFERENCE.md`.
7. Do not invent terrain meanings, simulator mechanics, event schedules, coverage denominators, action validation rules, or other semantics.
8. If a numeric ID or field meaning cannot be established from the repository, write exactly:

   > The repository does not define the semantic meaning of this numeric value.

9. If an implementation detail is suggested but not explicitly defined, label it:

   `UNKNOWN / REQUIRES SIMULATOR DOCUMENTATION`

10. Preserve exact names, indices, values, thresholds, comparison operators, nesting, and boolean structure from the JSON files. Preserve `>` versus `>=`, `<` versus `<=`, `AND`, `OR`, and `NOT` exactly.
11. If files conflict, document the conflict explicitly instead of silently selecting one interpretation.

## Required document contents

Use clear headings, tables, code blocks, and readable tree-style logic. Include exact JSON field names and exact values. The following sections are required.

### 1. Level 1 input file

Document the complete structure of `Level_1/1.json`, including:

- grid dimensions
- number of ticks
- whether animals are enabled
- starting conditions
- number of supplied cells
- every field present
- cell object structure
- row and column coordinate conventions
- terrain values and frequencies
- soil values and frequencies
- what the values in this specific Level 1 instance represent
- any fields whose meaning is unknown

Include a field table with `Field`, `Type`, `Meaning`, and `Example` columns where useful.

### 2. Plant dataset

Document the exact JSON structure of `additional-resources/plant_dataset.json` and create a complete catalogue of all 31 plants.

For every plant include every field present in the JSON, including at minimum:

- index
- exact plant name
- time to maturity
- spread rate
- spread range
- invasiveness
- preferred soil
- root type
- spread mechanism
- spread type
- special rules
- conditional growth modifiers
- all unusual or seemingly unimportant fields
- exact values

Do not omit fields merely because they appear irrelevant.

### 3. Plant special rules

Create a dedicated section for every special rule in `plant_dataset.json`. Cover, when present:

- shade requirements and shade radius
- burnt soil
- subsurface growth
- nutrient transfer
- coexistence
- neighbour limits
- isolated or death conditions
- adjacency bonuses and penalties
- seasonal modifiers
- special spread mechanisms
- resurrection
- soil regeneration
- animal avoidance
- every other special rule

For each rule state:

1. Which plant uses it.
2. The exact JSON field and value.
3. What the rule appears to mean from the source.
4. Whether the repository defines enough semantics to implement it exactly.

Mark unclear implementation semantics as `UNKNOWN / REQUIRES SIMULATOR DOCUMENTATION`.

### 4. Starting plants

Using only actual repository evidence, identify plants available at the beginning of Level 1.

Create a table with:

`Plant | Index | Starting status | Evidence`

Clearly distinguish:

- initially available plants
- unlocked plants
- plants requiring ecosystem conditions
- plants whose starting status cannot be established

### 5. Plant unlock conditions

Document the exact schema of `additional-resources/plant_unlock_conditions.json`.

Create a dependency table for every unlockable plant:

`Plant | Index | Requirements | Dependencies`

Expand every requirement into readable logic. For example:

```text
Blue Moss
    AND
    +-- Loamcrawlers present
    +-- Grass coverage > 0.03
    +-- Rose Bush coverage > 0.01
```

Preserve all of the following without simplification:

- `AND`
- `OR`
- `NOT`
- `species_present`
- `species_absent`
- coverage conditions
- count conditions
- event conditions
- feature-count conditions
- group requirements
- exact comparison operators
- exact thresholds

### 6. Unlock dependency graph

Build a human-readable graph showing how plants can unlock one another. Continue through all possible dependencies.

Also identify:

- prerequisite plants
- prerequisite animals or ecosystem species
- prerequisite events
- prerequisite coverage thresholds
- prerequisite counts
- possible circular dependencies
- plants that appear impossible without an external event
- plants independently unlockable
- every path where multiple paths exist

Use Mermaid if helpful, but include a readable text representation too when the graph is complex.

### 7. Animals and ecosystem species

Document `additional-resources/animals.json`. Do not assume it is irrelevant because `animals_enabled` is false in the input.

Determine whether its ecosystem species appear as conditions or effects in Level 1 rules.

Create a table:

`Species | Requirements | Effects`

Document every species. For requirements preserve:

- `AND` and `OR`
- plant coverage
- group coverage
- plant counts
- group counts
- dominance
- thresholds
- operators

For every effect document:

- target plant or group
- effect type
- multiplier or value
- exact target

### 8. Ecosystem dependency chains

Explain how animal or ecosystem species interact with plant unlocks. Build the complete dependency chain, such as:

```text
Lavender coverage
        |
        v
    Nectaris
        |
        +------> Orange Blossom
        +------> Moonpetal Lily
```

Explicitly identify important ecosystem milestones needed for later plants.

### 9. Classifications

Document `additional-resources/classifications.json`.

Create a table of every classification or group and all exact plant members:

`Classification | Members`

Explain why each classification matters to the solver only when supported by the repository. Pay attention to groups used by:

- animal requirements
- animal effects
- plant unlock conditions
- growth or spread effects
- root types
- scoring or diversity

Do not assign gameplay meaning to a group without evidence.

### 10. Cross-file relationships

Add a section titled exactly:

`## Cross-file relationships`

Explain the actual relationships among `1.json`, the plant dataset, unlock conditions, animals, and classifications. Include a corrected diagram if the source files support one, for example:

```text
1.json
 |
 | defines the Level 1 environment
 v
Plant dataset
 |
 | defines plant identities and properties
 v
Plant unlock conditions
 |
 | defines availability requirements
 v
Animals / ecosystem species
 |
 | defines ecosystem requirements and effects
 v
Classifications
 |
 | defines groups referenced by other resources
```

Correct or qualify this example according to the repository.

### 11. Complete plant dependency table

Create one master table containing all 31 plants with these columns:

`Index | Plant | Initially available? | Unlock requirement | Animal dependency | Event dependency | Important special rule`

This must be the primary quick-reference table for a solver.

### 12. Coverage thresholds

Extract every coverage threshold from both:

- `plant_unlock_conditions.json`
- `animals.json`

Create a table:

`Threshold | Plants/species affected | Exact comparison`

Keep exact operators and decimal values. Explain how coverage is represented only if explicitly defined. If the denominator is not defined, state that clearly and do not assume a grid-size calculation such as `plant_count / 2500`.

### 13. Count thresholds

Extract all count requirements from both resource files.

Create a table:

`Species/group | Required count | Operator | Used by`

Include plant counts, group counts, and every named example such as Oak Tree, Purple Canopy Tree, Sporewood Tree, Rose Bush, or any other value actually present.

### 14. Events

Find every event referenced anywhere in the Level 1 resources.

Create a table:

`Event | Referenced by | Requirement`

Determine whether `1.json` specifies when events happen. If timing is unavailable, say so explicitly.

### 15. Special environmental features

Document every feature referenced by unlock conditions or plant rules, including when present:

- burnt soil
- dead matter
- water
- rock or path
- shade
- terrain
- soil
- every other environmental feature

For each feature explain:

- where it is represented
- which file defines it
- which plants or conditions use it
- whether the actual Level 1 input contains enough information to locate it

Do not guess the meaning of raw terrain or soil codes.

### 16. Solver-relevant facts

Add a concise section titled exactly:

`## What a Level 1 solver must understand`

Split it into:

#### Definitely known

Facts explicitly supported by repository files.

#### Partially known

Facts for which some data exists but exact simulator behavior is unclear.

#### Unknown

Facts that cannot be determined from the available files.

Make this section practical for future implementation work.

### 17. Known dangers and common implementation mistakes

List only mistakes relevant to the actual repository, such as:

- planting locked species immediately
- confusing plant indices and names
- ignoring animal or ecosystem conditions
- changing `>` into `>=`
- treating classifications as unlock rules without evidence
- assuming every supplied cell is plantable
- assigning meanings to terrain or soil codes without evidence
- assuming a coverage denominator
- ignoring special plant rules
- ignoring events
- ignoring group coverage
- ignoring documented replacement rules
- exceeding 20 plants per tick
- using an incorrect submission schema

Do not include an example unless the repository supports it.

### 18. Official submission schema

Inspect repository code, examples, and documentation and document the exact expected submission format. At minimum investigate this shape:

```json
{
  "actions": [
    {
      "tick": 0,
      "plants": [
        {
          "plant_index": 1,
          "row": 0,
          "col": 0
        }
      ]
    }
  ]
}
```

Explain only rules supported by the repository:

- required fields
- field types
- valid tick range
- plant index meaning
- row and column meaning
- maximum actions per tick
- whether actions must be grouped by tick
- whether ordering matters
- whether duplicate positions are legal
- all other supported validation rules

### 19. Machine-readable appendix

At the end, add compact reference maps easy for an AI coding assistant to scan:

#### Plant index map

```text
1 = Grass
2 = Rose Bush
...
31 = Worldtree Sapling
```

Use the actual names and indices from the JSON.

#### Classification map

```text
Ground Cover = [...]
Flowering Plants = [...]
```

Use every actual classification.

#### Animal/ecosystem map

```text
Nectaris = ...
Solwings = ...
```

Use every actual species, requirement, and effect.

#### Unlock map

```text
Blue Moss -> ...
Orange Blossom -> ...
```

Use every actual unlockable plant and preserve full boolean requirements.

### 20. Final validation and confidence notes

At the bottom, add:

```markdown
## Source files inspected

- `Level_1/1.json`
- `Level_1/level_1.py`
- `additional-resources/plant_dataset.json`
- `additional-resources/plant_unlock_conditions.json`
- `additional-resources/animals.json`
- `additional-resources/classifications.json`
```

Also add:

```markdown
## Confidence notes

### Explicitly defined by source files
...

### Requires interpretation
...

### Not defined by the available files
...
```

Before finishing, cross-check every plant index, plant unlock, ecosystem species, classification, comparison operator, threshold, event, and special rule against its source file. Explicitly report contradictions and unknowns.

## Deliverable

Create only:

`Level_1/JSON_REFERENCE.md`

Do not implement or modify the solver. After creating the document, report:

1. The file path.
2. A short summary of its contents.
3. Important contradictions or unknowns discovered.
4. The most important facts a future solver implementation must account for.
