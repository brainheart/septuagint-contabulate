"""Swete's Septuagint (Open Greek and Latin, First1KGreek TEI) loader.

Books appear in the order of Swete's own edition, derived from each TEI file's
volume and first page, and keep Swete's chapter and verse numbering: four
books of Kingdoms, Esdras B as one book of 23 chapters, Old Greek and
Theodotion Daniel/Susanna/Bel side by side, Esther with its additions as
lettered verses, and the Odes numbered by the verses of their source books.

Parsing rules (TEI walk, OCR repairs, Esther and Isaiah quirks) follow
polyglot-contabulate/scripts/polyglot/sources.py; see SOURCES.md.
"""
import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET

TEI = "{http://www.tei-c.org/ns/1.0}"
# Greek ";" is the question mark (sibling gnt-contabulate counts it too).
SENTENCE_RE = r"[.!?;;]+"

# First1KGreek work -> (book code, Greek title, English title, section).
# Listed in Swete's order; load_books() checks it against the TEI volume/page.
WORKS = [
    ("001", "Gen", "Γένεσις", "Genesis", "Law"),
    ("002", "Exod", "Ἔξοδος", "Exodus", "Law"),
    ("003", "Lev", "Λευιτικόν", "Leviticus", "Law"),
    ("004", "Num", "Ἀριθμοί", "Numbers", "Law"),
    ("005", "Deut", "Δευτερονόμιον", "Deuteronomy", "Law"),
    ("006", "Josh", "Ἰησοῦς", "Joshua", "Histories"),
    ("008", "Judg", "Κριταί", "Judges", "Histories"),
    ("010", "Ruth", "Ῥούθ", "Ruth", "Histories"),
    ("011", "1Kgdms", "Βασιλειῶν Αʹ", "1 Kingdoms", "Histories"),
    ("012", "2Kgdms", "Βασιλειῶν Βʹ", "2 Kingdoms", "Histories"),
    ("013", "3Kgdms", "Βασιλειῶν Γʹ", "3 Kingdoms", "Histories"),
    ("014", "4Kgdms", "Βασιλειῶν Δʹ", "4 Kingdoms", "Histories"),
    ("015", "1Chr", "Παραλειπομένων Αʹ", "1 Chronicles", "Histories"),
    ("016", "2Chr", "Παραλειπομένων Βʹ", "2 Chronicles", "Histories"),
    ("017", "1Esd", "Ἔσδρας Αʹ", "1 Esdras", "Histories"),
    ("018", "2Esd", "Ἔσδρας Βʹ", "2 Esdras = Ezra–Nehemiah", "Histories"),
    ("027", "Ps", "Ψαλμοί", "Psalms", "Poetry & Wisdom"),
    ("029", "Prov", "Παροιμίαι", "Proverbs", "Poetry & Wisdom"),
    ("031", "Song", "Ἆσμα", "Song of Songs", "Poetry & Wisdom"),
    ("032", "Job", "Ἰώβ", "Job", "Poetry & Wisdom"),
    ("033", "Wis", "Σοφία Σαλωμῶνος", "Wisdom of Solomon", "Poetry & Wisdom"),
    ("034", "Sir", "Σοφία Σειράχ", "Sirach", "Poetry & Wisdom"),
    ("019", "Esth", "Ἐσθήρ", "Esther", "Histories"),
    ("020", "Jdt", "Ἰουδίθ", "Judith", "Histories"),
    ("021", "Tob", "Τωβίτ", "Tobit", "Histories"),
    ("036", "Hos", "Ὡσηέ", "Hosea", "Prophets"),
    ("037", "Amos", "Ἀμώς", "Amos", "Prophets"),
    ("038", "Mic", "Μιχαίας", "Micah", "Prophets"),
    ("039", "Joel", "Ἰωήλ", "Joel", "Prophets"),
    ("040", "Obad", "Ὀβδιού", "Obadiah", "Prophets"),
    ("041", "Jonah", "Ἰωνᾶς", "Jonah", "Prophets"),
    ("042", "Nah", "Ναούμ", "Nahum", "Prophets"),
    ("043", "Hab", "Ἀμβακούμ", "Habakkuk", "Prophets"),
    ("044", "Zeph", "Σοφονίας", "Zephaniah", "Prophets"),
    ("045", "Hag", "Ἀγγαῖος", "Haggai", "Prophets"),
    ("046", "Zech", "Ζαχαρίας", "Zechariah", "Prophets"),
    ("047", "Mal", "Μαλαχίας", "Malachi", "Prophets"),
    ("048", "Isa", "Ἠσαΐας", "Isaiah", "Prophets"),
    ("049", "Jer", "Ἱερεμίας", "Jeremiah", "Prophets"),
    ("050", "Bar", "Βαρούχ", "Baruch", "Prophets"),
    ("051", "Lam", "Θρῆνοι", "Lamentations", "Prophets"),
    ("052", "EpJer", "Ἐπιστολὴ Ἰερεμίου", "Letter of Jeremiah", "Prophets"),
    ("053", "Ezek", "Ἰεζεκιήλ", "Ezekiel", "Prophets"),
    ("056", "DanOG", "Δανιήλ", "Daniel, Old Greek", "Prophets"),
    ("057", "DanTh", "Δανιήλ", "Daniel, Theodotion", "Prophets"),
    ("054", "SusOG", "Σουσάννα", "Susanna, Old Greek", "Prophets"),
    ("055", "SusTh", "Σουσάννα", "Susanna, Theodotion", "Prophets"),
    ("058", "BelOG", "Βὴλ καὶ Δράκων", "Bel and the Dragon, Old Greek", "Prophets"),
    ("059", "BelTh", "Βὴλ καὶ Δράκων", "Bel and the Dragon, Theodotion", "Prophets"),
    ("023", "1Macc", "Μακκαβαίων Αʹ", "1 Maccabees", "Histories"),
    ("024", "2Macc", "Μακκαβαίων Βʹ", "2 Maccabees", "Histories"),
    ("025", "3Macc", "Μακκαβαίων Γʹ", "3 Maccabees", "Histories"),
    ("026", "4Macc", "Μακκαβαίων Δʹ", "4 Maccabees", "Histories"),
    ("035", "PssSol", "Ψαλμοὶ Σαλωμῶντος", "Psalms of Solomon", "Poetry & Wisdom"),
    ("028", "Odes", "Ὠδαί", "Odes", "Poetry & Wisdom"),
]
SWETE_FILE = {"034": "tlg0527.tlg034.1st1K-grc2.xml"}  # grc1 there is Hart's edition

# Verse numbers the automatic OCR repair cannot decide, and chapters the
# transcription mislabels (Wisdom 15-19 are tagged 16-20; incipit of the
# first, "Σὺ δὲ ὁ θεὸς ἡμῶν χρηστὸς", is Wis 15:1).
RENUMBER = {"Jdt 9:19": 14}
CHAPTER_RENUMBER = {"Wis": {"16": 15, "17": 16, "18": 17, "19": 18, "20": 19}}
# Label for unnumbered text before verse 1 (psalm titles, oracle headings).
UNNUMBERED_LABEL = {("Lam", 1): "prol.", ("Song", 7): "0", ("Job", 16): "0"}

LATIN_TO_GREEK = str.maketrans("ABEHIKMNOPTXYZ", "ΑΒΕΗΙΚΜΝΟΡΤΧΥΖ")
GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")
OCR_JUNK_RE = re.compile(r"[\x80-\x9f√£^\\>*+•°⁽|/¨΅»´\u070e]")
REPAIRS = []  # (reference, old, new), reported in SOURCES.md and by the build


def verify_source_files(directory):
    provenance = json.loads((directory / "provenance.json").read_text())
    for name, info in provenance["files"].items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != info["sha256"]:
            raise ValueError(f"Source checksum mismatch: {directory / name}")
    return provenance


def work_path(directory, work):
    return directory / "swete" / SWETE_FILE.get(work, f"tlg0527.tlg{work}.1st1K-grc1.xml")


def swete_position(path):
    """(volume, first page) of a work in Swete's edition, from the TEI."""
    head = path.read_text(encoding="utf-8")
    volume = int(re.search(r'<biblScope unit="volume">(\d+)<', head).group(1))
    page = int(re.search(r'<pb [^>]*n="(\d+)"', head).group(1))
    return volume, page


def _fix_mixed_script(text):
    """OCR sometimes uses Latin capitals inside Greek words ("ΜΑΚAPΙΟΣ").
    A lone trailing Latin capital after Greek lowercase is a manuscript
    siglum leaking from the apparatus ("τὸνB") and is dropped."""
    def fix(m):
        w = m.group(0)
        if GREEK_RE.search(w) and re.search(r"[A-Z]", w):
            w = re.sub(r"(?<=[ά-ώἀ-ῷ])[A-Z]+$", "", w)
            return w.translate(LATIN_TO_GREEK)
        return w
    return re.sub(r"[^\s,.;:·()\[\]]+", fix, text)


def _tei_text(el):
    """Text of an element, skipping notes (apparatus, marginalia) and heads."""
    parts = []

    def walk(e):
        tag = e.tag.replace(TEI, "")
        if tag in ("note", "head"):
            if e.tail:
                parts.append(e.tail)
            return
        if tag in ("l", "lb", "p", "lg"):
            parts.append(" ")
        if e.text:
            parts.append(e.text)
        for c in e:
            walk(c)
        if tag in ("l", "p", "lg"):
            parts.append(" ")
        if e.tail:
            parts.append(e.tail)

    walk(el)
    s = "".join(parts).replace("¶", " ").replace("§", " ")
    s = re.sub(r"U\+[0-9A-Fa-f]+", "", s)  # digitizer placeholders for unencoded glyphs
    s = re.sub(r"[¹²³⁰-⁹]", "", s)  # stray superscript digits from the OCR
    s = re.sub(r"\d+", "", s)  # stray OCR digits; Greek numerals are letters
    s = OCR_JUNK_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([,.;:·])", r"\1", s)
    s = unicodedata.normalize("NFC", _fix_mixed_script(s))
    return _fix_ocr_greek(s)


def _fix_ocr_greek(s):
    """Deterministic repairs of common OCR artefacts in the transcription."""
    # Combining marks with no letter to sit on, and stray Hebrew points,
    # would tokenize differently in Python and the browser.
    s = re.sub(r"[\u0591-\u05c7\u034e]", "", s)
    kept = []
    for ch in s:
        if unicodedata.category(ch)[0] == "M" and not (kept and unicodedata.category(kept[-1])[0] in "LM"):
            continue
        kept.append(ch)
    s = "".join(kept)
    # A breathing printed as a detached mark before an initial capital
    # ("᾿Ισραήλ", "῾Ρο", "’lσραήλ") is attached to the letter. Initial Ρ and Υ
    # always take the rough breathing.
    s = re.sub(r"(?:(?<=\s)|^)[’'᾿]l(?=[ά-ώα-ωἀ-ῷ])", "Ἰ", s)

    def attach(m):
        mark, letter = m.group(1), m.group(2)
        rough = mark in "῾‘" or letter in "ΡΥ"
        return unicodedata.normalize("NFC", letter + ("\u0314" if rough else "\u0313"))
    s = re.sub(r"(?:(?<=\s)|^)([’'᾿῾‘]) ?([ΑΕΗΙΟΥΩΡ])(?=[α-ωά-ώἀ-ῷ])", attach, s)
    # Words broken across a printed line ("εύ- σεβής") are rejoined.
    s = re.sub(r"(?<=[α-ωά-ώἀ-ῷ])- (?=[α-ωά-ώἀ-ῷ])", "", s)
    # Standalone marginal chapter references (roman numerals) and apparatus
    # sigla or abbreviations ("B", "om") that escaped the notes.
    s = re.sub(r"(?:(?<=\s)|^)(?:[IVXLC]+|[A-Z]|om)[.,]?(?=\s|$)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"\s+([,.;:·])", r"\1", s)


def _chapters(path):
    edition = ET.parse(path).getroot().find(f".//{TEI}div[@type='edition']")
    preface = []
    for child in edition:
        tag = child.tag.replace(TEI, "")
        if tag in ("p", "lg", "l"):
            text = _tei_text(child)
            if len(text.split()) > 3:  # skips the OCR'd heading "προλοΓοϲ"
                preface.append(text)
    chapters = edition.findall(f"{TEI}div[@subtype='chapter']")
    if not chapters:  # Letter of Jeremiah has verses directly under the edition
        yield "1", " ".join(preface[:1]), [(c.get("n"), _tei_text(c)) for c in edition
                                             if c.get("subtype") == "verse"]
        return
    if preface:
        yield "preface", " ".join(preface), []
    for chdiv in chapters:
        verses, pre = [], []
        for child in chdiv:
            tag = child.tag.replace(TEI, "")
            if tag == "div" and child.get("subtype") == "verse":
                verses.append((child.get("n"), _tei_text(child)))
            elif tag in ("lg", "p", "l") and not verses:
                pre.append(_tei_text(child))
        yield chdiv.get("n"), " ".join(x for x in pre if x).strip(), verses


def _repair_numbers(verses, ref):
    """OCR'd verse numbers that sit between two consecutive neighbours are
    repaired ([19, 220, 21] -> 20); genuine LXX reorderings ([23, 27, 24])
    are left alone because their neighbours are not two apart. A trailing
    "s" on a number that does not continue a run of subverses ("34, 35s")
    is OCR noise."""
    out = []
    for n, text in verses:
        previous = re.match(r"\d+", out[-1][0]).group(0) if out and out[-1][0][:1].isdigit() else None
        if re.fullmatch(r"\d+s", n) and previous != n[:-1]:  # 24r, 24s is a real subverse
            REPAIRS.append((f"{ref}:{n}", n, n[:-1]))
            n = n[:-1]
        out.append((n, text))
    nums = [int(n) if n.isdigit() else None for n, _ in out]
    for i in range(1, len(out) - 1):
        n, prev, nxt = nums[i], nums[i - 1], nums[i + 1]
        if None in (n, prev, nxt):
            continue
        if nxt - prev == 2 and not (prev < n < nxt):
            REPAIRS.append((f"{ref}:{n}", str(n), str(prev + 1)))
            out[i] = (str(prev + 1), out[i][1])
            nums[i] = prev + 1
    for i, (n, text) in enumerate(out):
        manual = RENUMBER.get(f"{ref}:{n}")
        if manual:
            REPAIRS.append((f"{ref}:{n}", n, str(manual)))
            out[i] = (str(manual), text)
    return out


def _verse(book, chapter, chapter_label, verse, label, loc, text, code_chapter=None):
    cid_chapter = code_chapter if code_chapter is not None else chapter
    cid_verse = label if label not in ("title", "prol.", "0", "unnumbered") else "0"
    return {"canonical_id": f"{book}.{cid_chapter}.{cid_verse}", "chapter": chapter,
            "chapter_label": chapter_label, "verse": verse, "verse_label": label,
            "location_verse": loc, "text": text}


def load_book(path, book):
    """Native verses of one work, in document order."""
    out = []
    for cn, title, verses in _chapters(path):
        if cn == "preface":  # Sirach's translator's prologue
            out.append(_verse(book, 1, None, 0, "prol.", "000", title))
            continue
        chapter_label, code_chapter = None, None
        if cn == "prologue":  # Esther: Addition A precedes chapter 1
            chapter, chapter_label, code_chapter = 0, "prol.", 0
        elif re.fullmatch(r"iv[ab]", cn):  # Odes: Swete splits Ode 4 in two
            chapter, chapter_label, code_chapter = 4, "4" + cn[-1], "4" + cn[-1]
        elif cn.isdigit():
            chapter = int(cn)
            fixed = CHAPTER_RENUMBER.get(book, {}).get(cn)
            if fixed:
                REPAIRS.append((f"{book} chapter {cn}", cn, str(fixed)))
                chapter = fixed
        else:
            raise ValueError(f"unexpected chapter {cn} in {path.name}")
        part = chapter_label[-1] if chapter_label and chapter == 4 and book == "Odes" else ""
        if title:
            label = UNNUMBERED_LABEL.get((book, chapter), "title" if verses else "unnumbered")
            out.append(_verse(book, chapter, chapter_label, 0, label, f"{part}000", title, code_chapter))
        anchor, seen, last_letter = 0, set(), {}
        for n, text in _repair_numbers(verses, f"{book} {cn}"):
            if not text:
                continue
            if n == "head" and book == "Isa":
                # Swete prints the end of 31:9 as a heading of chapter 32
                out[-1]["text"] += " " + text
                continue
            if n == "1a1" and book == "Esth":
                n = "11a"  # OCR label for 11a
            match = re.fullmatch(r"(\d+)([A-Za-z]?)", n)
            if not match:
                raise ValueError(f"bad verse {n} in {path.name} {cn}")
            v, letter = int(match[1]), match[2].lower()
            if not letter:
                anchor = v
                out.append(_verse(book, chapter, chapter_label, v, str(v), f"{part}{v:03d}", text, code_chapter))
                continue
            if book == "Esth":
                # Swete's Esther additions are numbered 1a, 2a... (and 1b...) by
                # addition, not by the verse they follow: keep the printed
                # label and place them after the preceding verse.
                loc = f"{anchor:03d}{letter}{v:02d}"
                out.append(_verse(book, chapter, chapter_label, v, n.lower(), loc, text, code_chapter))
                continue
            # Other books keep the printed letter (Sir 7 prints 16a 17a 16b 17b).
            # An OCR letter confusion that repeats a label (35i, 35I for 35l)
            # takes the letter after the last one used for that verse.
            label = f"{v}{letter}"
            if label in seen:
                last = last_letter.get(v, "`")
                label = f"{v}{chr(ord(last) + 1)}"
                REPAIRS.append((f"{book} {cn}:{n}", n, label))
            if label in seen or not label[-1].isalpha() or label[-1] > "z":
                raise ValueError(f"cannot label subverse {book} {cn}:{n}")
            seen.add(label)
            last_letter[v] = label[-1]
            out.append(_verse(book, chapter, chapter_label, v, label, f"{part}{v:03d}{label[-1]}",
                              text, code_chapter))
    return out


def load_books(source_dir):
    verify_source_files(source_dir)
    del REPAIRS[:]
    positions = [swete_position(work_path(source_dir, w[0])) for w in WORKS]
    if positions != sorted(positions):
        raise ValueError("WORKS is not in Swete's volume/page order")
    books = []
    for work, code, greek, english, section in WORKS:
        verses = load_book(work_path(source_dir, work), code)
        books.append({"abbr": code, "title": f"{greek} ({english})", "genre": section,
                      "verses": verses, "swete": positions[len(books)]})
    return books
