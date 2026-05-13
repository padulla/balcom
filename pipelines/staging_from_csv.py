"""Transforma CSV bruto da camada raw em CSV padronizado na staging."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="arquivo CSV na camada raw")
    p.add_argument("--output", required=True, help="arquivo CSV de saída na staging")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    in_path = ROOT / args.input
    out_path = ROOT / args.output

    df = pd.read_csv(in_path, sep=None, engine="python", encoding="utf-8")
    df.columns = [
        c.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")
        for c in df.columns
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Staging gerado: {out_path}")


if __name__ == "__main__":
    main()
