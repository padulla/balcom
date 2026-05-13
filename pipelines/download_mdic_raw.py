"""Baixa arquivos brutos da balança comercial para a camada raw.

Uso:
  python pipelines/download_mdic_raw.py --url <arquivo> --fonte mdic --competencia 2025-01
"""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as resp, target.open("wb") as out:
        out.write(resp.read())


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True, help="URL direta do arquivo (CSV/ZIP/XLSX)")
    p.add_argument("--fonte", default="mdic", help="nome da fonte para organizar a pasta raw")
    p.add_argument("--competencia", required=True, help="competência no formato YYYY-MM")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    year = args.competencia.split("-")[0]

    filename = Path(urlparse(args.url).path).name or "arquivo_origem"
    file_path = RAW_ROOT / args.fonte / year / filename

    download_file(args.url, file_path)

    metadata = {
        "fonte_url": args.url,
        "arquivo_origem": str(file_path.relative_to(ROOT)),
        "hash_arquivo": sha256_file(file_path),
        "data_download_utc": datetime.now(timezone.utc).isoformat(),
        "competencia_referente": args.competencia,
    }

    print("Download concluído:")
    for k, v in metadata.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()
