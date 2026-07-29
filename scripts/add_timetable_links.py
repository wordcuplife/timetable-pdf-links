#!/usr/bin/env python3
"""Add URI annotations to colored timetable blocks in a rendered PDF."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from collections import deque
from pathlib import Path
from typing import Iterable

from PIL import Image
from pypdf import PdfReader, PdfWriter


def load_links(path: Path) -> list[str]:
    data = json.loads(path.read_text())
    links: list[str] = []
    for item in data:
        if isinstance(item, str):
            links.append(item)
        elif isinstance(item, dict):
            href = item.get("href") or item.get("url")
            if not href:
                raise ValueError(f"Link object missing href/url: {item!r}")
            links.append(str(href))
        else:
            raise ValueError(f"Unsupported link item: {item!r}")
    if not links:
        raise ValueError("No links found in links JSON")
    return links


def render_first_page(pdf: Path, workdir: Path, dpi: int) -> Path:
    if shutil.which("pdftoppm") is None:
        raise RuntimeError("pdftoppm is required to render the PDF; install Poppler first")
    prefix = workdir / "render"
    subprocess.run(
        ["pdftoppm", "-png", "-f", "1", "-singlefile", "-r", str(dpi), str(pdf), str(prefix)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    png = prefix.with_suffix(".png")
    if not png.exists():
        raise RuntimeError(f"Rendered PNG not found: {png}")
    return png


def is_colored(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    mx = max(pixel)
    mn = min(pixel)
    return mx > 120 and (mx - mn) > 60 and not (r > 245 and g > 245 and b > 245)


def colored_components(png: Path, min_area: int, min_width: int, min_height: int) -> tuple[list[tuple[int, int, int, int]], tuple[int, int]]:
    img = Image.open(png).convert("RGB")
    width, height = img.size
    pix = img.load()
    mask = bytearray(width * height)
    for y in range(height):
        row = y * width
        for x in range(width):
            if is_colored(pix[x, y]):
                mask[row + x] = 1

    seen = bytearray(width * height)
    boxes: list[tuple[int, int, int, int]] = []
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if not mask[idx] or seen[idx]:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            seen[idx] = 1
            xs: list[int] = []
            ys: list[int] = []
            while q:
                cx, cy = q.popleft()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < width and 0 <= ny < height:
                        nidx = ny * width + nx
                        if mask[nidx] and not seen[nidx]:
                            seen[nidx] = 1
                            q.append((nx, ny))
            area = len(xs)
            x0, x1 = min(xs), max(xs)
            y0, y1 = min(ys), max(ys)
            if area >= min_area and (x1 - x0) >= min_width and (y1 - y0) >= min_height:
                boxes.append((x0, y0, x1, y1))

    boxes.sort(key=lambda b: (b[1], b[0]))
    return boxes, (width, height)


def add_links(input_pdf: Path, output_pdf: Path, links: list[str], boxes: Iterable[tuple[int, int, int, int]], image_size: tuple[int, int]) -> int:
    reader = PdfReader(str(input_pdf))
    if len(reader.pages) != 1:
        raise ValueError(f"Expected a 1-page timetable PDF, found {len(reader.pages)} pages")

    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    page = reader.pages[0]
    page_w = float(page.mediabox.width)
    page_h = float(page.mediabox.height)
    img_w, img_h = image_size
    sx = page_w / img_w
    sy = page_h / img_h

    count = 0
    for box, link in zip(boxes, links):
        x0, y0, x1, y1 = box
        inset = 1
        rect = [
            (x0 + inset) * sx,
            page_h - (y1 - inset) * sy,
            (x1 - inset) * sx,
            page_h - (y0 + inset) * sy,
        ]
        writer.add_uri(0, link, rect, border=[0, 0, 0])
        count += 1

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open("wb") as f:
        writer.write(f)
    return count


def count_uri_annotations(pdf: Path) -> int:
    reader = PdfReader(str(pdf))
    total = 0
    for page in reader.pages:
        for annot_ref in page.get("/Annots") or []:
            annot = annot_ref.get_object()
            action = annot.get("/A")
            if action and action.get("/URI"):
                total += 1
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Add map hyperlinks to colored timetable blocks in a PDF.")
    parser.add_argument("--input-pdf", required=True, type=Path)
    parser.add_argument("--links-json", required=True, type=Path)
    parser.add_argument("--output-pdf", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--min-area", type=int, default=500)
    parser.add_argument("--min-width", type=int, default=30)
    parser.add_argument("--min-height", type=int, default=20)
    args = parser.parse_args()

    links = load_links(args.links_json)
    with tempfile.TemporaryDirectory() as tmp:
        png = render_first_page(args.input_pdf, Path(tmp), args.dpi)
        boxes, image_size = colored_components(png, args.min_area, args.min_width, args.min_height)

    if len(boxes) != len(links):
        raise SystemExit(f"Detected {len(boxes)} colored blocks, but got {len(links)} links")

    written = add_links(args.input_pdf, args.output_pdf, links, boxes, image_size)
    verified = count_uri_annotations(args.output_pdf)
    if verified != len(links):
        raise SystemExit(f"Wrote {written} links, but verified {verified} URI annotations")

    print(f"output_pdf={args.output_pdf}")
    print(f"colored_blocks={len(boxes)}")
    print(f"uri_annotations={verified}")


if __name__ == "__main__":
    main()
