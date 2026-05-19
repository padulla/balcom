"""Carrega CSV padronizado da staging para tabela fato no SQLite."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "balcom.db"


REQUIRED = ["data_referencia", "fluxo_codigo", "fluxo_nome", "valor_usd_fob", "fonte"]


def get_or_create_dim(conn: sqlite3.Connection, table: str, id_col: str, key_col: str, key_val: str, extra: dict | None = None) -> int:
    row = conn.execute(f"SELECT {id_col} FROM {table} WHERE {key_col} = ?", (key_val,)).fetchone()
    if row:
        return int(row[0])

    cols = [key_col]
    vals = [key_val]
    if extra:
        cols.extend(extra.keys())
        vals.extend(extra.values())

    placeholders = ",".join(["?"] * len(vals))
    conn.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", vals)
    new_row = conn.execute(f"SELECT {id_col} FROM {table} WHERE {key_col} = ?", (key_val,)).fetchone()
    return int(new_row[0])


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="CSV da camada staging")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(ROOT / args.input)

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        for _, r in df.iterrows():
            ano, mes, _ = str(r["data_referencia"]).split("-")
            trimestre = (int(mes) - 1) // 3 + 1
            ano_mes = f"{ano}-{mes}"

            conn.execute(
                """
                INSERT OR IGNORE INTO dim_tempo (data_referencia, ano, mes, trimestre, ano_mes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (r["data_referencia"], int(ano), int(mes), trimestre, ano_mes),
            )
            tempo_id = conn.execute(
                "SELECT tempo_id FROM dim_tempo WHERE data_referencia = ?", (r["data_referencia"],)
            ).fetchone()[0]

            fluxo_id = get_or_create_dim(
                conn,
                "dim_fluxo",
                "fluxo_id",
                "fluxo_codigo",
                str(r["fluxo_codigo"]),
                {"fluxo_nome": str(r["fluxo_nome"])},
            )

            payload = f"{r.get('data_referencia','')}|{r.get('fluxo_codigo','')}|{r.get('valor_usd_fob','')}|{r.get('fonte','')}"
            hash_linha = hashlib.sha256(payload.encode("utf-8")).hexdigest()

            conn.execute(
                """
                INSERT OR IGNORE INTO f_comercio_exterior
                  (tempo_id, fluxo_id, valor_usd_fob, fonte, hash_linha_origem)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tempo_id, fluxo_id, float(r["valor_usd_fob"]), str(r["fonte"]), hash_linha),
            )

    print(f"Carga concluída para arquivo: {args.input}")


if __name__ == "__main__":
    main()
