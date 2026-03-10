"""
solver.py
---------
Solves the Matiks CrossMath puzzle using backtracking.

Usage:
    python solver.py                        # fetches today's puzzle
    python solver.py --date 2026-03-06     # specific date
    python solver.py --debug               # show full evaluation trace

Requirements:
    pip install requests
"""

import argparse
from fractions import Fraction
from itertools import permutations
from datetime import date

from scraper import fetch_puzzle, parse_puzzle, print_puzzle


# ── operator evaluation ───────────────────────────────────────────────────────

def apply_op(a, op, b):
    op = op.strip()
    if op == '+':                             return a + b
    if op == '-':                             return a - b
    if op in ('*', '\u00d7', 'x', 'X'):      return a * b
    if op in ('\u00f7', '/', ':', '%'):
        return (a / b) if b != 0 else Fraction(10**18)
    raise ValueError(f"Unknown operator: {op!r}  (hex: {op.encode().hex()})")


def eval_left_to_right(operands, operators):
    """No precedence: a op1 b op2 c evaluated strictly left-to-right."""
    result = Fraction(operands[0])
    for op, val in zip(operators, operands[1:]):
        result = apply_op(result, op, Fraction(val))
    return result


def eval_standard_precedence(operands, operators):
    """Standard math precedence: * / before + -"""
    vals = [Fraction(v) for v in operands]
    ops  = list(operators)
    i = 0
    while i < len(ops):
        if ops[i].strip() in ('*', '\u00d7', 'x', 'X', '\u00f7', '/', ':'):
            combined = apply_op(vals[i], ops[i], vals[i + 1])
            vals = vals[:i] + [combined] + vals[i + 2:]
            ops  = ops[:i]               + ops[i + 1:]
        else:
            i += 1
    result = vals[0]
    for op, val in zip(ops, vals[1:]):
        result = apply_op(result, op, val)
    return result


# ── solver ────────────────────────────────────────────────────────────────────

def solve(puzzle, debug=False):
    blanks  = puzzle["blanks"]
    answers = puzzle["available_answers"]

    if debug:
        print("\n-- DEBUG: Puzzle structure -----------------------------------")
        print(f"  Blanks:            {blanks}")
        print(f"  Available answers: {answers}")
        for i, eq in enumerate(puzzle["rows"]):
            print(f"  Row {i}: ops={[repr(o) for o in eq['operators']]}  result={eq['result']}")
        for i, eq in enumerate(puzzle["cols"]):
            print(f"  Col {i}: ops={[repr(o) for o in eq['operators']]}  result={eq['result']}")

    # Build pre-filled 3x3 grid
    grid = [[None]*3 for _ in range(3)]
    for ri, row in enumerate(puzzle["grid"]):
        for ci, cell in enumerate(row):
            if not cell["is_blank"]:
                grid[ri][ci] = int(cell["value"])

    if debug:
        print("\n  Pre-filled grid (None = blank):")
        for row in grid:
            print(f"    {row}")

    for eval_name, eval_fn in [
        ("left-to-right",      eval_left_to_right),
        ("standard-precedence", eval_standard_precedence),
    ]:
        if debug:
            print(f"\n-- Trying eval mode: {eval_name} --------------------")

        def check_all(g, show=False):
            for ri, eq in enumerate(puzzle["rows"]):
                vals = [g[ri][0], g[ri][1], g[ri][2]]
                if None in vals:
                    return False
                got      = eval_fn(vals, eq["operators"])
                expected = Fraction(eq["result"])
                if show:
                    mark = "OK" if got == expected else "FAIL"
                    print(f"    Row {ri}: {vals[0]} {eq['operators'][0]} {vals[1]} {eq['operators'][1]} {vals[2]} = {got}  (want {expected})  {mark}")
                if got != expected:
                    return False
            for ci, eq in enumerate(puzzle["cols"]):
                vals = [g[0][ci], g[1][ci], g[2][ci]]
                if None in vals:
                    return False
                got      = eval_fn(vals, eq["operators"])
                expected = Fraction(eq["result"])
                if show:
                    mark = "OK" if got == expected else "FAIL"
                    print(f"    Col {ci}: {vals[0]} {eq['operators'][0]} {vals[1]} {eq['operators'][1]} {vals[2]} = {got}  (want {expected})  {mark}")
                if got != expected:
                    return False
            return True

        for perm in permutations(answers, len(blanks)):
            for (ri, ci), val in zip(blanks, perm):
                grid[ri][ci] = val

            if debug:
                print(f"\n  Perm {perm}:")

            passed = check_all(grid, show=debug)

            if passed:
                solution = {(ri, ci): val for (ri, ci), val in zip(blanks, perm)}
                print(f"[+] Solved using {eval_name} evaluation")
                return solution, grid

            for ri, ci in blanks:
                grid[ri][ci] = None

    return None, None


# ── pretty print solution ─────────────────────────────────────────────────────

def print_solution(puzzle, grid):
    print("\nSOLUTION FOUND\n")
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
    print("\nBlanks filled:")
    for (ri, ci) in puzzle["blanks"]:
        print(f"  Row {ri+1}, Col {ci+1} -> {grid[ri][ci]}")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve Matiks CrossMath puzzle")
    parser.add_argument("--date",  default=str(date.today()), help="Puzzle date YYYY-MM-DD")
    parser.add_argument("--debug", action="store_true",       help="Print full evaluation trace")
    args = parser.parse_args()

    print(f"[*] Fetching puzzle for {args.date} ...")
    raw    = fetch_puzzle(args.date)
    puzzle = parse_puzzle(raw)
    print_puzzle(puzzle)

    print("[*] Solving ...")
    solution, grid = solve(puzzle, debug=args.debug)

    if grid:
        print_solution(puzzle, grid)
    else:
        print("No solution found.")
        if not args.debug:
            print(f"\nRun with --debug to see full trace:")
            print(f"  python solver.py --date {args.date} --debug")