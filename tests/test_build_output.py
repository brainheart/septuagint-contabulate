"""Corpus integrity, Swete order and numbering, Greek tokenizer, and metadata tests."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unicodedata
import unittest

import build
from scripts import source

ROOT = Path(__file__).resolve().parents[1]
SWETE_ORDER = [
    'Gen', 'Exod', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', 'Ruth', '1Kgdms', '2Kgdms', '3Kgdms', '4Kgdms',
    '1Chr', '2Chr', '1Esd', '2Esd', 'Ps', 'Prov', 'Eccl', 'Song', 'Job', 'Wis', 'Sir', 'Esth', 'Jdt', 'Tob',
    'Hos', 'Amos', 'Mic', 'Joel', 'Obad', 'Jonah', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal',
    'Isa', 'Jer', 'Bar', 'Lam', 'EpJer', 'Ezek', 'DanOG', 'DanTh', 'SusOG', 'SusTh', 'BelOG', 'BelTh',
    '1Macc', '2Macc', '3Macc', '4Macc', 'PssSol', 'Odes',
]


def read(name):
    return json.loads((ROOT / name).read_text())


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.books = read('docs/data/plays.json')
        cls.chunks = read('docs/data/chunks.json')
        cls.lines = read('docs/lines/all_lines.json')
        cls.tokens = read('docs/data/tokens.json')
        cls.text = {r['canonical_id']: r['text'] for r in cls.lines}
        cls.by_id = {r['canonical_id']: r for r in cls.chunks}

    def test_source_checksums(self):
        provenance = source.verify_source_files(ROOT / 'source_text')
        self.assertEqual(provenance['commit'], '8ee111eb44ecef4120c844e10749178d95d1f30c')
        self.assertEqual(len(provenance['files']), 55)
        brenton = provenance['brenton']
        self.assertEqual(brenton['url'], 'https://ebible.org/Scriptures/grcbrent_usfm.zip')
        self.assertEqual(brenton['sha256'], '964b96f1de0d47aabde9e2178a6776ea7851bcab2d6c8c115a94807f61293429')
        self.assertIn('Public Domain', (ROOT / 'source_text/brenton/copr.htm').read_text())

    def test_corpus_totals_and_hierarchy(self):
        self.assertEqual(len(self.books), 56)
        self.assertEqual(sum(b['num_acts'] for b in self.books), 1148)
        self.assertEqual(len(self.chunks), 29583)
        self.assertEqual(sum(b['total_words'] for b in self.books), 592121)
        self.assertEqual(len(self.tokens), 57347)
        self.assertEqual(Counter(b['genre'] for b in self.books),
                         {'Law': 5, 'Histories': 18, 'Poetry & Wisdom': 9, 'Prophets': 24})
        self.assertEqual(self.books[0]['location'], '01.Gen')
        self.assertEqual(self.books[-1]['location'], '56.Odes')
        self.assertEqual([r['canonical_id'] for r in self.chunks], [r['canonical_id'] for r in self.lines])
        self.assertEqual(len({r['scene_id'] for r in self.chunks}), len(self.chunks))
        self.assertEqual(len({r['canonical_id'] for r in self.chunks}), len(self.chunks))
        self.assertEqual(len({r['location'] for r in self.chunks}), len(self.chunks))
        for chunk, line in zip(self.chunks, self.lines):
            self.assertIn(chunk['play_id'], range(1, 57))
            self.assertEqual(chunk['scene_id'], line['line_num'])
            self.assertEqual(chunk['total_words'], len(build.tokenize(line['text'])))
            self.assertTrue(chunk['location'].startswith(f"{chunk['play_id']:02d}.{chunk['play_abbr']}.{chunk['act']:03d}."))

    def test_swete_order_titles_and_lxx_only_books(self):
        self.assertEqual([b['abbr'] for b in self.books], SWETE_ORDER)
        positions = [source.swete_position(source.work_path(ROOT / 'source_text', w[0]))
                     for w in source.WORKS if w[0] not in source.BRENTON_BOOKS]
        self.assertEqual(positions, sorted(positions))
        titles = {b['abbr']: b['title'] for b in self.books}
        self.assertEqual(titles['3Kgdms'], 'Βασιλειῶν Γʹ (3 Kingdoms)')
        self.assertEqual(titles['PssSol'], 'Ψαλμοὶ Σαλωμῶντος (Psalms of Solomon)')
        chapters = {b['abbr']: b['num_acts'] for b in self.books}
        self.assertEqual(chapters['2Esd'], 23)  # Esdras B = Ezra + Nehemiah, one book
        self.assertEqual(chapters['4Macc'], 18)
        self.assertEqual(chapters['PssSol'], 18)
        self.assertEqual(chapters['Odes'], 14)  # Ode 4 is printed in two parts, 4a and 4b
        self.assertEqual(titles['Eccl'], 'Ἐκκλησιαστής (Ecclesiastes)')  # from Brenton
        self.assertIn('λόγον ἐπιδείκνυσθαι μέλλων', self.text['4Macc.1.1'])
        self.assertTrue(self.text['PssSol.1.1'].startswith('ΕΒΟΗΣΑ πρὸς Κύριον'))
        self.assertTrue(self.text['Odes.14.0'].startswith('Ὕμνος ἑωθινός. Δόξα ἐν ὑψίστοις θεῷ'))
        self.assertTrue(self.text['Ps.151.1'].startswith('Μικρὸς ἤμην'))

    def test_native_lxx_numbering(self):
        self.assertEqual(self.text['Ps.22.0'], 'Ψαλμὸς τῷ Δαυείδ.')
        self.assertEqual(self.by_id['Ps.22.0']['scene_label'], 'title')
        self.assertTrue(self.text['Ps.22.1'].startswith('Κύριος ποιμαίνει με'))
        self.assertTrue(self.text['Ps.50.3'].startswith('Ἐλέησόν με, ὁ θεός'))
        self.assertEqual(sum(1 for r in self.chunks if r['play_abbr'] == 'Ps' and r['scene'] == 1), 151)
        self.assertTrue(self.text['3Kgdms.2.35a'].startswith('Καὶ ἔδωκεν Κύριος φρόνησιν'))
        self.assertEqual(self.by_id['3Kgdms.2.35a']['location'], '11.3Kgdms.002.035a')
        self.assertEqual(len([k for k in self.text if k.startswith('3Kgdms.12.24') and k != '3Kgdms.12.24']), 24)
        self.assertIn('2Esd.23.31', self.text)
        self.assertNotIn('Neh.1.1', self.text)
        # Sirach's prologue and Esther's Addition A come before chapter 1
        self.assertTrue(self.text['Sir.1.0'].startswith('ΠΟΛΛΩΝ καὶ μεγάλων'))
        self.assertTrue(self.text['Sir.1.1'].startswith('ΠΑΣΑ σοφία παρὰ Κυρίου'))
        self.assertEqual(self.by_id['Esth.0.1']['act_label'], 'prol.')
        self.assertLess(self.by_id['Esth.3.13']['location'], self.by_id['Esth.3.1a']['location'])
        self.assertLess(self.by_id['Esth.3.7a']['location'], self.by_id['Esth.3.14']['location'])
        # Odes are numbered by the verses of their source books
        self.assertEqual(self.by_id['Odes.4a.9']['location'], '56.Odes.004.a009')
        self.assertEqual(self.by_id['Odes.4b.9']['location'], '56.Odes.004.b009')
        self.assertIn('Odes.5.3', self.text)
        self.assertNotIn('Odes.5.1', self.text)
        # Wisdom's mislabelled chapters 16-20 are 15-19
        self.assertTrue(self.text['Wis.15.1'].startswith('Σὺ δὲ ὁ θεὸς ἡμῶν χρηστὸς'))
        self.assertEqual(max(r['act'] for r in self.chunks if r['play_abbr'] == 'Wis'), 19)
        self.assertEqual(self.lines[0]['text'], 'ΕΝ ΑΡΧΗ ἐποίησεν ὁ θεὸς τὸν οὐρανὸν καὶ τὴν γῆν.')

    def test_ecclesiastes_from_brenton(self):
        eccl = next(b for b in self.books if b['abbr'] == 'Eccl')
        self.assertEqual((eccl['num_acts'], eccl['verse_count']), (12, 222))
        self.assertEqual(eccl['location'], '19.Eccl')
        self.assertEqual(eccl['text_source'], 'Brenton 1851')
        rows = [r for r in self.lines if r['canonical_id'].startswith('Eccl.')]
        self.assertEqual(len(rows), 222)
        self.assertEqual(Counter(r['act'] for r in rows)[1], 18)
        self.assertTrue(all(r['text_source'] == 'Brenton 1851' for r in rows))
        self.assertIn('Ματαιότης ματαιοτήτων', self.text['Eccl.1.2'])
        self.assertTrue(self.text['Eccl.12.14'].startswith('Ὅτι σύμπαν τὸ ποίημα'))
        for text in (r['text'] for r in rows):
            self.assertNotRegex(text, r'\\|\||[0-9]|ʼ')  # no USFM markup; elision as in Swete

    def test_usfm_markup_is_stripped(self):
        path = Path(tempfile.mkdtemp()) / 'sample.usfm'
        path.write_text('\\id ECC test\n\\h ΕΚ\n\\c 1\n\\s1 Heading\n\\p\n'
                        '\\v 1 \\w ῬΗΜΑΤΑ|strong="G4487"\\w* υἱοῦ\\f + \\fr 1:1 \\ft note\\f* Δαυὶδ ,\n'
                        '\\q1 \\nd Κυρίου\\nd* διʼ αὐτοῦ\\x - \\xo 1:1 \\xt Gen 1:1\\x*\n\\v 2 ἐν.\n', encoding='utf-8')
        self.assertEqual(source.parse_usfm(path), {('1', '1'): 'ῬΗΜΑΤΑ υἱοῦ Δαυὶδ, Κυρίου δι’ αὐτοῦ',
                                                    ('1', '2'): 'ἐν.'})

    def test_source_gaps_and_repairs_are_explicit(self):
        # Verse-1 texts lost in the transcription come from Brenton where his
        # neighbouring verses match Swete's (Swete Num 17:1 = Brenton 17:16).
        filled = {'Exod.20.1': ('Exod.19.25', 'Exod.20.2', 'Καὶ ἐλάλησε Κύριος πάντας τοὺς λόγους'),
                  'Num.17.1': ('Num.16.50', 'Num.17.2', 'Καὶ ἐλάλησε Κύριος πρὸς Μωυσῆν, λέγων'),
                  'Num.19.1': ('Num.18.32', 'Num.19.2', 'Καὶ ἐλάλησε Κύριος πρὸς Μωυσῆν καὶ Ἀαρὼν'),
                  '3Kgdms.16.1': ('3Kgdms.15.34', '3Kgdms.16.2', 'Καὶ ἐγένετο λόγος Κυρίου ἐν χειρὶ Ἰοὺ')}
        index = {r['canonical_id']: i for i, r in enumerate(self.lines)}
        for ref, (before, after, incipit) in filled.items():
            self.assertTrue(self.text[ref].startswith(incipit), ref)
            self.assertEqual(self.by_id[ref]['text_source'], 'Brenton 1851')
            self.assertEqual((index[before] + 1, index[after] - 1), (index[ref], index[ref]))
            self.assertLess(self.by_id[before]['location'], self.by_id[ref]['location'])
            self.assertLess(self.by_id[ref]['location'], self.by_id[after]['location'])
        brenton_num = source.parse_usfm(ROOT / 'source_text/brenton/05-NUMgrcbrent.usfm')
        self.assertIn('ἐπέστρεψεν Ἀαρὼν πρὸς Μωυσῆν', brenton_num[('17', '15')])  # = Swete 16:50
        self.assertIn('λάβε παρ’ αὐτῶν ῥάβδον', brenton_num[('17', '17')])  # = Swete 17:2
        # 3 Kgdms 14:1-20 is absent from Codex B (Swete and Brenton alike): a real gap
        self.assertNotIn('3Kgdms.14.1', self.text)
        brenton_rows = {r['canonical_id'] for r in self.lines if r.get('text_source')}
        self.assertEqual(brenton_rows - {k for k in brenton_rows if k.startswith('Eccl.')}, set(filled))
        repairs = read('docs/data/source_repairs.json')
        self.assertEqual(len(repairs), 17)
        self.assertIn({'ref': 'Jdt 9:19', 'printed': '19', 'used': '14'}, repairs)
        self.assertIn({'ref': '3Kgdms 2:35i', 'printed': '35i', 'used': '35l'}, repairs)

    def test_text_normalization_and_ocr_cleanup(self):
        joined = ' '.join(self.text.values())
        for text in self.text.values():
            self.assertTrue(text)
            self.assertEqual(text, unicodedata.normalize('NFC', text))
            self.assertNotRegex(text, r'[0-9<>*+|√£•°]|U\+|\s{2}')
            self.assertNotRegex(text, r'(?:^|\s)(?:[IVXLC]{2,}|om)(?:\s|$)')
        self.assertLess(sum(1 for w in joined.split() if any('a' <= c.lower() <= 'z' for c in w)), 250)
        self.assertGreater(joined.count('Ἰσραήλ') + joined.count('Ἰσραὴλ'), 2500)
        self.assertEqual(source._fix_ocr_greek('καὶ ᾿Ισραὴλ ’lσραὴλ ῾Ροβοὰμ εὐ- σεβὴς XX B τοῦ'),
                         'καὶ Ἰσραὴλ Ἰσραὴλ Ῥοβοὰμ εὐσεβὴς τοῦ')

    def test_greek_tokens_and_sentences(self):
        self.assertEqual(build.tokenize('Ἐν ἀρχῇ λόγος διʼ αὐτοῦ ἀφ’ ἧς'),
                         ['ἐν', 'ἀρχῇ', 'λόγος', 'δι', 'αὐτοῦ', 'ἀφ', 'ἧς'])
        self.assertEqual(build.tokenize('ἔλεος'), build.tokenize(unicodedata.normalize('NFD', 'ἔλεος')))
        self.assertEqual(build.tokenize('ΛΟΓΟΣ'), ['λογος'])
        self.assertEqual(build.count_sentences('τί; ναί. τί; λόγος·'), 3)
        for word in ['ἔλεος', 'ἀγάπη', 'ᾅδης', 'ᾅδου']:
            self.assertIn(word, self.tokens)
        self.assertNotIn('ελεος', self.tokens)
        self.assertIn('ἔλεός', self.tokens)  # enclitic accent is a distinct written form

    def test_browser_and_python_tokenizers_agree_on_entire_corpus(self):
        code = """
        global.window = global;
        require('./docs/js/utils.js');
        const fs = require('fs'); const crypto = require('crypto');
        const lines = JSON.parse(fs.readFileSync('./docs/lines/all_lines.json'));
        const stream = lines.map(l => tokenizeLineText(l.text).join(' ')).join('\\n');
        process.stdout.write(crypto.createHash('sha256').update(stream).digest('hex'));
        """
        actual = subprocess.check_output(['node', '-e', code], cwd=ROOT, text=True)
        stream = '\n'.join(' '.join(build.tokenize(row['text'])) for row in self.lines)
        self.assertEqual(actual, hashlib.sha256(stream.encode()).hexdigest())

    def test_postings_totals_do_not_cross_verse_boundaries(self):
        by_id = {r['scene_id']: r for r in self.chunks}
        for n, filename in [(1, 'tokens'), (2, 'tokens2'), (3, 'tokens3')]:
            index = read(f'docs/data/{filename}.json')
            totals = Counter()
            for term, postings in index.items():
                self.assertEqual(len(term.split()), n)
                for scene_id, count in postings:
                    self.assertGreater(count, 0)
                    totals[scene_id] += count
            for scene_id, chunk in by_id.items():
                self.assertEqual(totals[scene_id], max(0, chunk['total_words'] - n + 1))

    def test_metrics_metadata_and_disabled_capabilities(self):
        instance = read('docs/instance.json')
        meta = read('instance-meta.json')
        self.assertEqual(instance['schema'], 1)
        self.assertEqual(instance['id'], 'septuagint')
        self.assertEqual(instance['created'], '2026-09-28')
        self.assertEqual(instance['language'], 'Koine Greek')
        self.assertEqual(instance['url'], 'https://septuagint.contabulate.org/')
        self.assertEqual((ROOT / 'docs/CNAME').read_text().strip(), 'septuagint.contabulate.org')
        self.assertEqual(instance['stats'], {
            'texts': 56, 'text_label': 'books', 'segments': 29583, 'segment_label': 'verses',
            'words': 592121, 'distinct_words': 57347, 'commentaries': 0, 'comments': 0})
        self.assertEqual(instance['sample_queries'], meta['sample_queries'])
        self.assertIn(len(instance['sample_queries']), (3, 4))
        for sample in instance['sample_queries']:
            self.assertTrue(sample['url'].startswith('https://septuagint.contabulate.org/?'))
        self.assertEqual(sum(c['hapax_count'] for c in self.chunks),
                         sum(sum(count for _, count in p) == 1 for p in self.tokens.values()))
        for chunk in self.chunks:
            self.assertGreater(chunk['char_count'], 0)
            self.assertGreater(chunk['rarity_sum'], 0)
            self.assertNotIn('commentary_interest', chunk)
        self.assertEqual(read('docs/data/characters.json'), [])
        self.assertFalse(read('docs/data/character_name_filter_config.json')['enabled'])


if __name__ == '__main__':
    unittest.main()
