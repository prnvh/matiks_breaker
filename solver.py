"""
solver.py
─────────
Solves the Matiks CrossMath puzzle using backtracking.
Takes the parsed puzzle dict (from scraper.py) and finds the correct
placement of available_answers into the blank cells.

Usage:
    python solver.py                        # fetches today's puzzle
    python solver.py --date 2026-03-06     # specific date

Requirements:
    pip install requests
"""

import argparse
from itertools import permutations
from datetime import date

# ── reuse scraper logic ───────────────────────────────────────────────────────
from scraper import fetch_puzzle, parse_puzzle, print_puzzle


# ── operator evaluation ───────────────────────────────────────────────────────

def apply_op(a: int, op: str, b: int) -> float:
    if op == '+': return a + b
    if op == '-': return a - b
    if op == '*': return a * b
    if op in ('÷', '/'):
        if b == 0:
            return float('inf')
        return a / b
    raise ValueError(f"Unknown operator: {op}")


def eval_row_or_col(operands: list, operators: list) -> float:
    """Evaluate: a op1 b op2 c  (left to right, no precedence)"""
    result = operands[0]
    for op, val in zip(operators, operands[1:]):
        result = apply_op(result, op, val)
    return result


# ── solver ────────────────────────────────────────────────────────────────────

def solve(puzzle: dict) -> dict | None:
    """
    Tries all permutations of available_answers into blank positions.
    Returns a filled puzzle dict on success, or None if unsolvable.
    """
    blanks = puzzle["blanks"]           # list of (row_idx, col_idx)
    answers = puzzle["available_answers"]

    # build a mutable 3x3 grid of values
    grid = [[None] * 3 for _ in range(3)]
    for ri, row in enumerate(puzzle["grid"]):
        for ci, cell in enumerate(row):
            if not cell["is_blank"]:
                grid[ri][ci] = int(cell["value"])

    def check_all(g):
        # check all 3 rows
        for ri, eq in enumerate(puzzle["rows"]):
            ops = eq["operators"]
            operands = [g[ri][ci] if g[ri][ci] is not None else int(eq["operands"][ci])
                        for ci in range(3)]
            # use actual grid values (already substituted)
            vals = [g[ri][0], g[ri][1], g[ri][2]]
            if None in vals:
                return False
            if eval_row_or_col(vals, ops) != eq["result"]:
                return False

        # check all 3 cols
        for ci, eq in enumerate(puzzle["cols"]):
            ops = eq["operators"]
            vals = [g[0][ci], g[1][ci], g[2][ci]]
            if None in vals:
                return False
            if eval_row_or_col(vals, ops) != eq["result"]:
                return False

        return True

    # try every permutation of answers into blank slots
    for perm in permutations(answers, len(blanks)):
        # fill in the blanks
        for (ri, ci), val in zip(blanks, perm):
            grid[ri][ci] = val

        if check_all(grid):
            # build solution dict
            solution = {(ri, ci): val for (ri, ci), val in zip(blanks, perm)}
            return solution, grid

        # reset
        for ri, ci in blanks:
            grid[ri][ci] = None

    return None, None


# ── pretty print solution ─────────────────────────────────────────────────────

def print_solution(puzzle: dict, grid: list):
    print("\n✅ SOLUTION FOUND\n")
    row_data = puzzle["rows"]
    col_data = puzzle["cols"]

    for ri in range(3):
        eq = row_data[ri]
        a, b, c = grid[ri]
        print(f"  {a:>4} {eq['operators'][0]} {b:>4} {eq['operators'][1]} {c:>4} = {eq['result']}")
        if ri < 2:
            col_ops = [col_data[ci]["operators"][ri] for ci in range(3)]
            print(f"  {'':>4} {col_ops[0]} {'':>4} {col_ops[1]} {'':>4}")

    print(f"\n  =      =      =")
    print(f"  {col_data[0]['result']:>4}   {col_data[1]['result']:>4}   {col_data[2]['result']:>4}")

    print("\nBlank answers placed:")
    for (ri, ci), val in zip(puzzle["blanks"], [grid[ri][ci] for ri, ci in puzzle["blanks"]]):
        print(f"  Row {ri+1}, Col {ci+1} → {val}")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve Matiks CrossMath puzzle")
    parser.add_argument("--date", default=str(date.today()), help="Puzzle date YYYY-MM-DD")
    args = parser.parse_args()

    print(f"[*] Fetching puzzle for {args.date} …")
    raw = fetch_puzzle(args.date)
    puzzle = parse_puzzle(raw)
    print_puzzle(puzzle)

    print("[*] Solving …")
    solution, grid = solve(puzzle)

    if grid:
        print_solution(puzzle, grid)
    else:
        print("❌ No solution found — check puzzle data.")