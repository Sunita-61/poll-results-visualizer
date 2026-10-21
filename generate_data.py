"""CLI script to generate bundled sample poll responses.

Usage:
    python generate_data.py [--respondents 200] [--seed 42] [--output data/sample_poll_responses.csv]
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure src can be imported directly when running script
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.synthetic_data import generate_synthetic_poll_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate reproducible synthetic poll responses for Poll Results Visualizer."
    )
    parser.add_argument(
        "--respondents",
        type=int,
        default=200,
        help="Number of distinct survey respondents (default: 200). Generates ~800 responses.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic output (default: 42).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/sample_poll_responses.csv",
        help="Output CSV file path (default: data/sample_poll_responses.csv).",
    )
    parser.add_argument(
        "--noise",
        action="store_true",
        help="Inject minor realistic noise (whitespace, duplicate rows, malformed dates) to test data cleaning.",
    )

    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating synthetic poll responses for {args.respondents} respondents (seed={args.seed})...")
    df = generate_synthetic_poll_data(
        num_respondents=args.respondents,
        random_seed=args.seed,
        add_noise=args.noise,
    )

    df.to_csv(out_path, index=False)
    print(f"Successfully saved {len(df)} poll responses to {out_path.resolve()}")
    print("Schema preview:")
    print(df.head(3))


if __name__ == "__main__":
    main()
