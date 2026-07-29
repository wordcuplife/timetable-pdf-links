# Repository Guide

This repository contains a Markdown-based Codex skill for adding clickable map links to exported timetable PDFs.

## Key Files

- `SKILL.md` is the source of truth for the agent workflow.
- `scripts/add_timetable_links.py` performs the deterministic PDF annotation step.
- `agents/openai.yaml` provides skill-list metadata.
- `README.md` is the public installation and usage guide.
- `LICENSE` contains the MIT licence.

## Maintenance Contract

Keep the browser collection workflow and the PDF annotation script aligned. If the expected browser block selector, link pattern, PDF block detection logic, or output filename changes, update both `SKILL.md` and `README.md`.

Preserve these core requirements:

- Verify `.e-appointment` block count before collecting links.
- Collect block text, ARIA labels, and rectangles in one page evaluation.
- Sort browser blocks and PDF blocks in the same visual order.
- Stop if the collected link count does not match the detected PDF block count.
- Use `scripts/add_timetable_links.py` for the PDF write step.
- Validate the final URI annotation count before reporting success.

## Editing Guidance

Do not add real timetable PDFs, screenshots, collected links, browser exports, personal schedules, local machine paths, credentials, or private student data to this repository.

Before publishing a change:

1. Run the skill validator against the repository.
2. Check that `scripts/add_timetable_links.py` still parses its CLI arguments.
3. Search for private paths and tokens.
4. Confirm the README installation command points to this repository.
