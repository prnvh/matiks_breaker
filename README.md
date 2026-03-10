# Matiks CrossMath Solver

Scrapes and solves the daily [Matiks CrossMath](https://www.matiks.in/) puzzle using GraphQL API interception and backtracking.

---

## What it does

Matiks CrossMath presents a 3×3 grid where each row and column forms a math equation. Some cells are blank — your job is to place the given numbers correctly so all 6 equations hold.

This tool:
1. **Scrapes** today's puzzle directly from Matiks' GraphQL API
2. **Parses** the raw 7×7 cell grid into a clean, structured format
3. **Solves** it via permutation-based backtracking and prints the solution

---

## How it works

### Scraper (`scraper.py`)
- Intercepts the `GetDailyPuzzleByType` GraphQL query that the Matiks web app uses
- Parses the raw 7×7 cell layout into a 3×3 operand grid, extracting row/column operators, results, and blank positions
- Saves the structured puzzle as a JSON file (e.g. `puzzle_2026-03-06.json`)

### Solver (`solver.py`)
- Loads the parsed puzzle (or fetches it fresh)
- Tries all permutations of the available answer digits into the blank positions
- Validates each permutation against all 6 equations (left-to-right evaluation, no operator precedence)
- Prints the completed grid with the solution highlighted

---

## Usage

```bash
pip install requests
```

**Fetch and display today's puzzle:**
```bash
python scraper.py
```

**Fetch and solve today's puzzle:**
```bash
python solver.py
```

**Specify a date:**
```bash
python scraper.py --date 2026-03-06
python solver.py --date 2026-03-06
```

---

## Example output

```
────────────────────────────────────────
  Matiks CrossMath — 2026-03-06  (Medium)
────────────────────────────────────────

✅ SOLUTION FOUND

     3 +    6 *    2 = 18
       -      +
     4 *    1 +    5 = 9
       +      -
     7 -    2 *    3 = 15

  =      =      =
    18      9     15

Blank answers placed:
  Row 1, Col 2 → 6
  Row 2, Col 1 → 4
```

---

## Technical notes

- The Matiks app exposes a public GraphQL endpoint — no login required for daily puzzles
- The 7×7 raw grid interleaves operands, operators, and results; the scraper maps these to clean row/column structures
- The solver uses `itertools.permutations` — worst case is 9! ≈ 362,880 permutations, which runs in under a second

---

## Files

| File | Description |
|------|-------------|
| `scraper.py` | Fetches and parses the daily puzzle |
| `solver.py` | Solves the parsed puzzle via backtracking |
| `puzzle_YYYY-MM-DD.json` | Auto-generated structured puzzle output |
