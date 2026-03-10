"""
matiks_scraper.py
─────────────────
Fetches the daily CrossMath puzzle from matiks.in's GraphQL API
and parses it into a clean, solver-ready structure.

Usage:
    python matiks_scraper.py
    python matiks_scraper.py --date 2026-03-06

Requirements:
    pip install requests
"""

import argparse
import json
import requests
from datetime import date
import os
from dotenv import load_dotenv

# 1. Load the .env file
load_dotenv()

# 2. Grab the actual secret string from the environment
my_secret_token = os.getenv("AUTHORIZATION_KEY")

# 3. Use it in your headers
headers = {
    "Content-Type": "application/json",
    "authorization": my_secret_token  # <--- NO QUOTES HERE
}

print(f"Sending request with token starting with: {my_secret_token[:10]}...")

API_URL = "https://server.matiks.org/api"

QUERY = """
query GetDailyPuzzleByType($date: String!, $puzzleType: PuzzleType!) {
  getDailyPuzzleByType(date: $date, puzzleType: $puzzleType) {
    id
    difficulty
    solvedBy
    cells {
      isVisible
      value
      type
      __typename
    }
    puzzleType
    puzzleDate
    availableAnswers
    stats {
      numOfSubmission
      averageTime
      bestTime
      __typename
    }
    __typename
  }
}
"""

def fetch_puzzle(puzzle_date: str) -> dict:
    """POST the GraphQL query and return the raw response JSON."""
    payload = {
        "operationName": "GetDailyPuzzleByType",
        "variables": {
            "date": puzzle_date,
            "puzzleType": "CrossMath"
        },
        "query": QUERY
    }
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://www.matiks.in",
        "referer": "https://www.matiks.in/",
        "authorization": my_secret_token,  # <-- replace with actual value from .env
        "x-app-version": "1.18.629",
        "x-device-id": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-request-id": "web_4917448b-b964-47be-a3c7-d558b58f4a76",
        "x-session-id": "web_5b315f72-f96d-4c0b-a616-a8b138615f29",
        "x-timezone": "Asia/Calcutta",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    resp = requests.post(API_URL, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def parse_puzzle(raw: dict) -> dict:
    print(json.dumps(raw, indent=2))  # <-- add this
    puzzle_data = raw["data"]["getDailyPuzzleByType"]
    """
    Converts the raw API response into a structured puzzle dict:

    {
        "id": str,
        "date": str,
        "difficulty": str,
        "available_answers": [int, ...],   # numbers to place
        "grid": [                           # 7x7 raw cell grid
            [ {"isVisible": bool, "value": str, "type": str}, ... ],
            ...
        ],
        "rows": [                           # 3 equation rows
            {"operands": [...], "operators": [...], "result": int},
            ...
        ],
        "cols": [                           # 3 equation columns
            {"operands": [...], "operators": [...], "result": int},
            ...
        ],
        "blanks": [                         # (row_idx, col_idx) of hidden cells
            (int, int), ...
        ]
    }

    Grid coordinates refer to operand rows/cols (0-2), not the raw 7x7 grid.
    """
    puzzle_data = raw["data"]["getDailyPuzzleByType"]
    cells = puzzle_data["cells"]  # 7x7 grid

    # ── extract the 3×3 operand sub-grid (every other row/col) ──────────────
    # Rows 0,2,4 and cols 0,2,4 are operand positions in the 7x7 layout
    operand_rows = [0, 2, 4]
    operand_cols = [0, 2, 4]

    grid_3x3 = []
    for r in operand_rows:
        row = []
        for c in operand_cols:
            cell = cells[r][c]
            row.append({
                "value": cell["value"],
                "is_blank": not cell["isVisible"],
            })
        grid_3x3.append(row)

    # ── row equations: row operators at cols 1,3 and result at col 6 ────────
    row_op_cols = [1, 3]
    rows = []
    for r in operand_rows:
        ops = [cells[r][c]["value"] for c in row_op_cols]
        result = int(cells[r][6]["value"])
        operands = [cells[r][c]["value"] for c in operand_cols]
        rows.append({"operands": operands, "operators": ops, "result": result})

    # ── col equations: col operators at rows 1,3 and result at row 6 ────────
    col_op_rows = [1, 3]
    cols = []
    for c in operand_cols:
        ops = [cells[r][c]["value"] for r in col_op_rows]
        result = int(cells[6][c]["value"])
        operands = [cells[r][c]["value"] for r in operand_rows]
        cols.append({"operands": operands, "operators": ops, "result": result})

    # ── locate blank cells (to be filled) ───────────────────────────────────
    blanks = [
        (ri, ci)
        for ri, r in enumerate(grid_3x3)
        for ci, cell in enumerate(r)
        if cell["is_blank"]
    ]

    return {
        "id": puzzle_data["id"],
        "date": puzzle_data["puzzleDate"],
        "difficulty": puzzle_data["difficulty"],
        "available_answers": [int(x) for x in puzzle_data["availableAnswers"]],
        "grid": grid_3x3,
        "rows": rows,
        "cols": cols,
        "blanks": blanks,
    }


def print_puzzle(puzzle: dict):
    """Pretty-print the parsed puzzle."""
    print(f"\n{'─'*40}")
    print(f"  Matiks CrossMath — {puzzle['date']}  ({puzzle['difficulty']})")
    print(f"{'─'*40}")

    print("\nGrid (? = blank to fill):")
    for ri, row in enumerate(puzzle["grid"]):
        row_eq = puzzle["rows"][ri]
        parts = []
        for ci, cell in enumerate(row):
            val = "?" if cell["is_blank"] else cell["value"]
            if ci < 2:
                parts.append(f"{val:>4} {row_eq['operators'][ci]}")
            else:
                parts.append(f"{val:>4} = {row_eq['result']}")
        print("  " + "  ".join(parts))
        if ri < 2:
            col_ops = [puzzle["cols"][ci]["operators"][ri] for ci in range(3)]
            print(f"  {'':>4} {col_ops[0]}  {'':>4} {col_ops[1]}  {'':>4} {col_ops[2]}")

    print("\nColumn results:")
    for ci, col in enumerate(puzzle["cols"]):
        print(f"  Col {ci+1}: = {col['result']}")

    print(f"\nAvailable answers: {puzzle['available_answers']}")
    print(f"Blank positions (row, col): {puzzle['blanks']}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Matiks CrossMath puzzle")
    parser.add_argument("--date", default=str(date.today()), help="Puzzle date YYYY-MM-DD")
    args = parser.parse_args()

    print(f"[*] Fetching puzzle for {args.date} …")
    raw = fetch_puzzle(args.date)
    puzzle = parse_puzzle(raw)

    print_puzzle(puzzle)

    # Also dump the structured puzzle as JSON for the solver
    out_file = f"puzzle_{args.date}.json"
    with open(out_file, "w") as f:
        json.dump(puzzle, f, indent=2)
    print(f"[*] Puzzle saved to {out_file}")