# Sources, licenses and provenance

| Item | Detail |
|---|---|
| Edition | H. B. Swete, *The Old Testament in Greek according to the Septuagint* (Cambridge, 1887–1912 editions) — public domain |
| Transcription | Open Greek and Latin, First1KGreek `data/tlg0527` TEI (University of Leipzig) — **CC BY-SA 4.0** |
| Upstream | https://github.com/OpenGreekAndLatin/First1KGreek @ `8ee111eb44ecef4120c844e10749178d95d1f30c` |
| Files | `source_text/swete/*.xml` (55 works); URLs and SHA-256 in `source_text/provenance.json` |
| Gap filler | L. C. L. Brenton, *The Septuagint Version of the Old Testament* (London: Bagster, 1851), Greek text (Sixtine edition, Codex Vaticanus-based) — **public domain**; eBible.org `grcbrent` USFM, marked “Public Domain” in its `copr.htm` |
| Brenton files | https://ebible.org/Scriptures/grcbrent_usfm.zip, SHA-256 `964b96f1de0d47aabde9e2178a6776ea7851bcab2d6c8c115a94807f61293429` (retrieved 2026-09-28; not versioned upstream, so pinned by hash); the four books used plus `copr.htm` in `source_text/brenton/`, per-file hashes under `brenton` in `provenance.json`; refetch with `python3 scripts/fetch_brenton.py` |

The files were copied from `polyglot-contabulate/sources/raw/swete/`; their
hashes match that repo's `sources/manifest.json`. Sirach uses `tlg034…grc2`
(Swete); `grc1` there is Hart's edition. `build.py` verifies every hash.

**Why Swete:** Rahlfs–Hanhart (Deutsche Bibelgesellschaft) is in copyright and the
CCAT/CATSS morphological LXX restricts redistribution, so neither can be
republished. The OGL transcription is openly licensed; the data derived from it
stays CC BY-SA 4.0 with attribution (see `DATA-LICENSE.md`). Alternatives
considered in polyglot-contabulate: `nathans/lxx-swete` (token-per-line
derivative, drops structure) and `eliranwong/LXX-Swete-1930` (no explicit license).

## Brenton rows (not Swete)

These rows are Brenton's Greek, not Swete's, and carry `text_source: "Brenton 1851"`
in `chunks.json` and `all_lines.json` (Ecclesiastes also in `plays.json`); the
site marks them with a small “Br” (tooltip “text: Brenton 1851”).

- **Ecclesiastes** (`Eccl`, Ἐκκλησιαστής): all 12 chapters, 222 verses, from
  `22-ECCgrcbrent.usfm`, placed after Proverbs where Swete prints it (vol. 2).
  First1KGreek `tlg0527.tlg030` has no text.
- **Four lost verse-1 texts**, each checked against Swete's neighbours:
  Exod 20:1, Num 19:1, 3 Kgdms 16:1 (same numbering in Brenton), and Num 17:1 =
  Brenton 17:16 (Brenton numbers Num 16:36–50 as 17:1–15; his 17:15 and 17:17
  are Swete's 16:50 and 17:2).
- **Not filled:** 3 Kgdms 14:1. Swete's 14:1 division holds only the numeral
  `XIV`; 14:1–20 is absent from Codex B, and Brenton also goes from 13:34 to 14:21.
- USFM: footnotes/cross-references (`\f`, `\x`), `\w …|attributes\w*`, headings and
  identification lines are dropped, other markers stripped; then whitespace,
  punctuation spacing and NFC as for Swete, and elision `ʼ` → `’`. No OCR repairs.

## Processing (`scripts/source.py`)

- **Order:** Swete's own, taken from each TEI file's volume and first page and
  checked against the `WORKS` table; titles are Greek with English in brackets.
- **Numbering:** Swete's chapters and verses. Canonical IDs use LXX book codes
  (`1Kgdms`…`4Kgdms`, `1Esd`, `2Esd` = Ezra–Nehemiah as 23 chapters, `DanOG`/`DanTh`,
  `SusOG`/`SusTh`, `BelOG`/`BelTh`, `PssSol`, `Odes`).
- **Unnumbered text** before verse 1 is its own verse-0 row: psalm and oracle
  titles (`title`), the prefaces of Sirach and Lamentations (`prol.`), and all of
  Ode 14 (`unnumbered`).
- **Lettered verses** keep their printed letters (3 Kgdms 2:35a, 12:24a–z; Sir 7
  prints 16a 17a 16b 17b); a repeated letter from OCR confusion takes the next
  letter. Esther's additions keep the transcription's labels (`1a`, `1b`…) and
  sort after the verse they follow; Addition A is chapter 0 (`prol.`).
- **Odes** are numbered by the verses of their source books; Swete's split Ode 4
  becomes chapters `4a` and `4b` of one Ode 4 (IDs `Odes.4a.1`, `Odes.4b.9`).
- **Text:** notes/marginalia and heads skipped; digits, digitizer `U+…`
  placeholders, sigla and marginal roman numerals removed; Latin look-alike
  capitals mapped to Greek; detached breathings attached; line-break hyphens
  rejoined; orphan combining marks dropped; NFC.
- **Numbering repairs** (17, listed in `docs/data/source_repairs.json`): numbers
  between two consecutive neighbours (`220` → 20), OCR `s` suffixes (`35s` → 35),
  a repeated subverse letter (`35i` → 35l), Judith 9:19 → 9:14, and Wisdom chapters
  labelled 16–20 → 15–19 (incipit of 15:1 verified).

## Known limits

- **Ecclesiastes and four verses are Brenton's text**, not Swete's (see above);
  Brenton's Sixtine text can differ from Swete's Vaticanus text in spelling and
  readings (e.g. `Θεὸς` capitalised). Judges is Codex A only (no B text in the source).
- Genuine LXX gaps remain gaps: 3 Kgdms 14:1–20 (chapter 14 starts at verse 21),
  Codex B's shorter 1 Kgdms 17–18.
- Residual OCR errors (about 200 tokens with Latin letters; misreadings such as
  `ΦΙΔΟΣΟΦΩΤΑΤΟΝ`). Capitalised unaccented incipits (`ΕΝ ΑΡΧΗ`) count as
  separate word forms.
- Where Swete reorders verses (e.g. Num 6, Sir 7), sorting by Location follows
  the numbers, not the printed sequence.
- No commentary counts; no reviewed proper-name list.
