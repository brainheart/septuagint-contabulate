# Septuagint Contabulate

Independent static instance (Swete LXX, First1KGreek TEI). Run `python3 build.py`,
`python3 -m unittest discover -v`, and `npx playwright test`. Source files are
pinned and checked by SHA-256. Generated files in `docs/data`, `docs/lines`, and
`docs/instance.json` must be rebuilt, not edited. Keep Swete's book order and
numbering; never remap to Rahlfs or KJV. Data derived from the transcription is
CC BY-SA 4.0 with attribution. Ecclesiastes and four lost verse-1 texts come
from Brenton (public domain, `source_text/brenton/`, `scripts/fetch_brenton.py`)
and must stay flagged `text_source`. `created` in `instance-meta.json` stays 2026-09-28.
