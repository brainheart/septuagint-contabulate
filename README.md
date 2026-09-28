# Septuagint Contabulate

A static [Contabulate](https://contabulate.org/) instance for H. B. Swete's
Septuagint: a sortable, filterable table of all 55 books in the Open Greek and
Latin transcription, by section, book, chapter, verse, word, bigram, and trigram,
with search-term and text-metric columns. Canonical URL (not yet deployed):
https://septuagint.contabulate.org/

- Books follow Swete's own order and numbering, including LXX-only books
  (1 Esdras, 3–4 Maccabees, Psalms of Solomon, Odes, Psalm 151) and both Old
  Greek and Theodotion Daniel/Susanna/Bel.
- Greek normalization matches gnt-contabulate (NFC; case and elision ignored;
  accents and breathings kept).
- Sources, repairs, and known limits: `SOURCES.md` and `docs/sources.html`.

## Build and test

```sh
python3 build.py                     # regenerates docs/data, docs/lines, docs/instance.json
python3 -m unittest discover -v      # corpus, numbering, tokenizer, metadata checks
npm ci && npx playwright test        # browser tests against python3 -m http.server 8782
```

Generated files under `docs/data`, `docs/lines`, and `docs/instance.json` are
build output; edit `scripts/source.py`, `build.py`, or `instance-meta.json` and rebuild.

## License

Code: MIT (see `LICENSE`). Greek text and derived data: Swete's edition is public
domain; the First1KGreek digitization and the data derived from it (`source_text/`,
`docs/data/`, `docs/lines/`) are CC BY-SA 4.0, attribution Open Greek and Latin /
University of Leipzig (see `DATA-LICENSE.md`).
