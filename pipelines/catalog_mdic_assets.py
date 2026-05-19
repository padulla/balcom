"""Cataloga links de arquivos da página oficial da base bruta MDIC."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta"

ALLOWED_EXT = {".csv", ".zip", ".xlsx", ".xls"}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=DEFAULT_URL, help="página com lista de arquivos")
    p.add_argument(
        "--output",
        default="docs/mdic_assets_catalog.csv",
        help="csv de saída com os links encontrados",
    )
    return p.parse_args()


def is_data_asset(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in ALLOWED_EXT)


def main() -> None:
    args = parse_args()

    with urlopen(args.url) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    parser = LinkParser()
    parser.feed(html)

    assets = sorted({urljoin(args.url, href) for href in parser.links if is_data_asset(urljoin(args.url, href))})

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_page", "asset_url", "generated_at_utc"])
        for asset in assets:
            writer.writerow([args.url, asset, generated_at])

    print(f"Catálogo gerado com {len(assets)} links: {output}")


if __name__ == "__main__":
    main()
