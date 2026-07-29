# Timetable PDF Links

Timetable PDF Links is an agent skill for adding clickable room or map links to exported MyTimetable-style PDF timetables.

The skill collects map URLs from a live browser timetable, matches them to the colored class blocks in an exported PDF, and writes invisible URI annotations so each class block becomes clickable.

## Installation

### Codex

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/wordcuplife/timetable-pdf-links.git ~/.agents/skills/timetable-pdf-links
```

Restart Codex after installation. Invoke the skill with `$timetable-pdf-links`, or ask Codex to add clickable map links to an exported timetable PDF.

## Requirements

The PDF step uses:

- Python 3
- `pypdf`
- `Pillow`
- Poppler's `pdftoppm`

Install missing Python dependencies if needed:

```bash
python3 -m pip install pypdf Pillow
```

Install Poppler with your platform package manager, for example:

```bash
brew install poppler
```

## Usage

Example request:

```text
$timetable-pdf-links I have my timetable open in Chrome and an exported Timetable.pdf. Collect the class map links and add them to the PDF.
```

The skill expects:

- a live MyTimetable-style browser page containing `.e-appointment` class blocks;
- an exported timetable PDF with colored class blocks;
- one map URL per timetable block, in the same visual order.

The deterministic PDF step can also be run directly:

```bash
python3 scripts/add_timetable_links.py \
  --input-pdf /path/to/MyTimetable.pdf \
  --links-json /path/to/links.json \
  --output-pdf /path/to/Timetable.pdf
```

The `links.json` file may be a list of URL strings or a list of objects containing `href` or `url`.

## What It Does

- Reads visible timetable blocks from a browser page.
- Sorts blocks in visual order.
- Collects the matching room or map URL for each block.
- Renders the exported PDF and detects colored timetable blocks.
- Adds URI annotations to the matching PDF rectangles.
- Verifies that the final PDF contains the expected number of links.

## Scope

This skill was written for MyTimetable-style pages and University of Melbourne map links. It can be adapted to similar timetable systems if their browser blocks and room-link patterns are compatible.

Do not publish personal timetable PDFs, browser data, or collected class links in this repository.

## Repository Contents

- `SKILL.md`: the agent workflow.
- `scripts/add_timetable_links.py`: deterministic PDF link annotation script.
- `agents/openai.yaml`: UI metadata for the skill.
- `AGENTS.md`: maintenance guidance.
- `LICENSE`: MIT licence.

## License

MIT
