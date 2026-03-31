#!/usr/bin/env python3
"""Clonador estructural de imaginaits.com.

- Lee sitemap.xml (o fallback a enlaces de home)
- Extrae secciones semánticas básicas de cada página
- Descarga imágenes reales detectadas en img/srcset/picture/css/lazy attrs
- Genera reportes de arquitectura, contenido e imágenes

Uso:
  python project/scripts/clone_imaginaits.py --root project
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

BASE_URL = "https://imaginaits.com/"
SITEMAP_URLS = [
    "https://www.imaginaits.com/sitemap.xml",
    "https://imaginaits.com/sitemap.xml",
    "https://imaginaits.com/wp-sitemap.xml",
]
UA = "Mozilla/5.0 (compatible; ImaginaCloneBot/1.0)"


@dataclass
class PageRecord:
    url: str
    slug: str
    title: str
    headings: list[str]
    ctas: list[str]
    links: list[str]
    images: list[str]


class PageExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title = ""
        self._in_title = False
        self._capture_heading = False
        self._capture_button = False
        self.headings: list[str] = []
        self.buttons: list[str] = []
        self.links: list[str] = []
        self.images: list[str] = []
        self.inline_styles: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attr = {k: (v or "") for k, v in attrs}

        if tag == "title":
            self._in_title = True

        if tag in {"h1", "h2", "h3", "h4"}:
            self._capture_heading = True

        if tag in {"button"}:
            self._capture_button = True

        if tag == "a" and attr.get("href"):
            self.links.append(urljoin(self.base_url, attr["href"]))

        if tag == "img":
            self._collect_image(attr)

        if tag == "source":
            self._collect_srcset(attr.get("srcset", ""))

        style = attr.get("style", "")
        if style:
            self.inline_styles.append(style)

    def handle_endtag(self, tag: str):
        if tag == "title":
            self._in_title = False
        if tag in {"h1", "h2", "h3", "h4"}:
            self._capture_heading = False
        if tag == "button":
            self._capture_button = False

    def handle_data(self, data: str):
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title += (" " + text).strip()
        if self._capture_heading:
            self.headings.append(text)
        if self._capture_button:
            self.buttons.append(text)

    def _collect_image(self, attr: dict[str, str]):
        for key in ("src", "data-src", "data-lazy-src", "data-original"):
            value = attr.get(key, "")
            if value:
                self.images.append(urljoin(self.base_url, value))
        self._collect_srcset(attr.get("srcset", ""))
        self._collect_srcset(attr.get("data-srcset", ""))

    def _collect_srcset(self, srcset: str):
        if not srcset:
            return
        for candidate in srcset.split(","):
            url_part = candidate.strip().split(" ")[0]
            if url_part:
                self.images.append(urljoin(self.base_url, url_part))

    def collect_css_background_images(self):
        pattern = re.compile(r"background-image\s*:\s*url\(([^)]+)\)", re.I)
        for style in self.inline_styles:
            for match in pattern.findall(style):
                cleaned = match.strip('"\' ')
                if cleaned:
                    self.images.append(urljoin(self.base_url, cleaned))


def fetch_text(url: str, timeout: int = 25) -> str:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", "ignore")


def safe_slug(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "index"
    return re.sub(r"[^a-z0-9-]+", "-", path.lower())


def discover_urls() -> tuple[list[str], str]:
    errors: list[str] = []
    for sitemap_url in SITEMAP_URLS:
        try:
            xml_body = fetch_text(sitemap_url)
            root = ET.fromstring(xml_body)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = [loc.text.strip() for loc in root.findall(".//sm:loc", ns) if loc.text]
            if urls:
                return sorted(set(urls)), f"sitemap:{sitemap_url}"
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{sitemap_url} -> {exc}")

    try:
        home = fetch_text(BASE_URL)
        parser = PageExtractor(BASE_URL)
        parser.feed(home)
        urls = [u for u in parser.links if "imaginaits.com" in u]
        urls.append(BASE_URL)
        return sorted(set(urls)), "fallback:home-links | " + " ; ".join(errors)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{BASE_URL} -> {exc}")
        return [], "network-unavailable | " + " ; ".join(errors)


def classify_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if path == "":
        return "home"
    if any(k in path for k in ("categoria", "category")):
        return "categoria"
    if any(k in path for k in ("landing", "demo", "integraciones", "api", "manual")):
        return "landing"
    return "pagina"


def uniq(items: Iterable[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def download_image(url: str, root: Path) -> tuple[str, str]:
    parsed = urlparse(url)
    name = Path(parsed.path).name or f"image-{abs(hash(url))}.bin"
    out = root / "assets" / "images" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=30) as res:
            out.write_bytes(res.read())
        return str(out.relative_to(root)), "correcta"
    except Exception:  # noqa: BLE001
        return "IMAGEN NO DISPONIBLE – REVISIÓN MANUAL", "faltante"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="project", help="Ruta raíz del proyecto")
    args = ap.parse_args()
    root = Path(args.root)
    pages_dir = root / "pages" / "mirror"
    data_dir = root / "data"
    pages_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    urls, discovery_source = discover_urls()

    page_records: list[PageRecord] = []
    validation_rows: list[dict[str, str]] = []

    for url in urls:
        try:
            html = fetch_text(url)
        except Exception as exc:  # noqa: BLE001
            validation_rows.append(
                {
                    "pagina": url,
                    "seccion": "page",
                    "imagen_original": "-",
                    "estado": f"error: {exc}",
                }
            )
            continue

        slug = safe_slug(url)
        (pages_dir / f"{slug}.html").write_text(html, encoding="utf-8")

        ex = PageExtractor(url)
        ex.feed(html)
        ex.collect_css_background_images()
        images = uniq([u for u in ex.images if urlparse(u).scheme in {"http", "https"}])

        local_images = []
        for image_url in images:
            local_path, status = download_image(image_url, root)
            local_images.append(local_path)
            validation_rows.append(
                {
                    "pagina": url,
                    "seccion": "media",
                    "imagen_original": image_url,
                    "estado": status,
                }
            )

        page_records.append(
            PageRecord(
                url=url,
                slug=slug,
                title=ex.title.strip() or slug,
                headings=uniq(ex.headings),
                ctas=uniq(ex.buttons),
                links=uniq(ex.links),
                images=local_images,
            )
        )

    architecture = {
        "source": discovery_source,
        "home": [u for u in urls if classify_url(u) == "home"],
        "paginas_principales": [u for u in urls if classify_url(u) == "pagina"],
        "categorias": [u for u in urls if classify_url(u) == "categoria"],
        "landings": [u for u in urls if classify_url(u) == "landing"],
    }

    (data_dir / "architecture.json").write_text(json.dumps(architecture, indent=2, ensure_ascii=False), encoding="utf-8")
    (data_dir / "pages.json").write_text(
        json.dumps([asdict(p) for p in page_records], indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with (data_dir / "image-validation.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["pagina", "seccion", "imagen_original", "estado"])
        writer.writeheader()
        writer.writerows(validation_rows)

    print(f"Descubiertas {len(urls)} URLs. Fuente: {discovery_source}")
    print(f"Páginas volcadas en: {pages_dir}")
    print(f"Reportes en: {data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
