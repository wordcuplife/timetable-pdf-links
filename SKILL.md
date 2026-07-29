---
name: timetable-pdf-links
description: Add clickable room/map links to a MyTimetable-style class timetable PDF. Use when the user has a browser timetable page with `.e-appointment` class blocks, wants Codex to collect each class block's address/map URL from the browser, then apply those URLs as hyperlink annotations to an exported timetable PDF named `Timetable.pdf`.
---

# Timetable PDF Links

## Overview

Use this skill to create a linked timetable PDF from a live browser timetable and an exported, unlinked PDF. The workflow has two independent parts: collect links from the browser's `.e-appointment` blocks, then add those links to matching colored blocks in the PDF.

## Workflow

1. Ask the user to open the timetable page in Chrome or the in-app browser before starting browser collection.
2. Use the browser-control skill matching the user's browser choice. Read that browser skill first and follow its safety rules.
3. On the timetable page, verify the page contains `.e-appointment` elements. Count them and report the count before processing.
4. Extract each `.e-appointment` block's visible text, `aria-label`, and bounding rectangle with one page evaluation.
5. Sort blocks in visual order: ascending `y`; for blocks whose `y` differs by 8 px or less, ascending `x`.
6. Click each sorted block, one at a time, and extract the map/address URL from the resulting detail panel or page.
7. Ask the user for the exported unlinked timetable PDF path if it has not already been provided.
8. Render the PDF to PNG, detect the colored class blocks, sort them in the same visual order, and confirm the PDF block count matches the collected link count.
9. Run `scripts/add_timetable_links.py` to write URI annotations and save `Timetable.pdf`.
10. Verify the output PDF has the expected number of URI annotations and render it for a final visual check.

## Browser Link Collection

Prefer direct page evaluation for stable data extraction:

```js
const blocks = await tab.playwright.evaluate(() => {
  const items = [...document.querySelectorAll('.e-appointment')].map((el, domIndex) => {
    const r = el.getBoundingClientRect();
    return {
      domIndex,
      text: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim(),
      aria: el.getAttribute('aria-label'),
      rect: { x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height }
    };
  });
  items.sort((a, b) => Math.abs(a.rect.y - b.rect.y) > 8 ? a.rect.y - b.rect.y : a.rect.x - b.rect.x);
  return items;
});
```

Click the sorted blocks in that order. After each click, extract links whose `href` contains `maps.unimelb.edu.au`. Treat a link as valid only when the detail text or link text matches the clicked block's room/building code.

If clicking does not refresh the detail, do not reuse the previous link. Fall back to deriving the URL from the room code in the block text only when the link pattern has already been observed on the same site during the task:

- `PAR-115-L2-200` -> `https://maps.unimelb.edu.au/point?identifier=PAR;115;2;200`
- `PAR-105-G-G06` -> `https://maps.unimelb.edu.au/point?identifier=PAR;105;0;G06`
- `PAR-379-B1-B132` -> `https://maps.unimelb.edu.au/point?identifier=PAR;379;0.1;B132`

Mapping rules:

- Campus is the first segment, usually `PAR`.
- Building is the numeric second segment.
- `G` maps to level `0`.
- `L<number>` maps to that number.
- `B<number>` maps to `0.<number>`.
- Room is the final segment, preserving letters and digits.

Stop and ask the user if a block has no room code, has multiple different map links, opens a login/CAPTCHA page, or the PDF block count does not match the collected link count.

## PDF Processing

Use `scripts/add_timetable_links.py` for the deterministic PDF step. It expects:

- an input PDF path,
- a JSON file containing collected links in visual order,
- an output path, normally `Timetable.pdf`.

The script renders the PDF with `pdftoppm`, identifies saturated colored blocks, sorts them visually, writes invisible URI annotations with `pypdf`, and validates the annotation count.

Example:

```bash
python3 scripts/add_timetable_links.py \
  --input-pdf /path/to/MyTimetable.pdf \
  --links-json /path/to/links.json \
  --output-pdf /path/to/Timetable.pdf
```

The links JSON must be either a list of strings or a list of objects containing `href` or `url`.

## Validation

Always perform these checks before final delivery:

- `pdfinfo` confirms the output exists and has the expected page count.
- The script reports URI annotation count equal to the collected link count.
- A rendered PNG of the output PDF visually matches the input PDF.
- The final path is named `Timetable.pdf` unless the user explicitly requested another name.
