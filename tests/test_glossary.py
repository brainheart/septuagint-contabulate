"""English reading aids: Wiktionary dictionary forms and glosses, with gaps
filled from the Greek New Testament's word-by-word analysis."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GlossaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = json.loads((ROOT / 'docs/data/glossary.json').read_text(encoding='utf-8'))
        cls.tokens = json.loads((ROOT / 'docs/data/tokens.json').read_text(encoding='utf-8'))
        cls.L = cls.g['lemmas']

    def first(self, form):
        return self.L[self.g['forms'][form][2][0]]['lemma']

    def test_counts_and_forms(self):
        self.assertEqual(set(self.g['forms']), set(self.tokens))
        for e in self.L:
            self.assertEqual(e['n'], sum(n for _, n in e['forms']))
            for f, n in e['forms']:
                self.assertEqual(n, sum(x[1] for x in self.tokens[f]))

    def test_sources_pinned_and_credited(self):
        from scripts.glossary import EXTRACT_FILE, load_extract
        extract = load_extract(ROOT / 'source_text/lexicon' / EXTRACT_FILE)
        self.assertEqual(extract['source']['language'], 'grc')
        self.assertIn('MorphGNT', extract['source']['supplement'])
        self.assertEqual(self.g['meta'], {'lang': 'grc', 'dir': 'ltr'})

    def test_greek_assignments(self):
        self.assertEqual(self.first('τοῦ'), 'ὁ')          # article, not the many nouns whose tables print it
        self.assertEqual(self.first('κύριος'), 'κύριος')
        self.assertEqual(self.L[self.g['forms']['κύριος'][2][0]]['pos'], 'noun')
        self.assertEqual(self.first('βασιλέως'), 'βασιλεύς')
        self.assertEqual(self.first('ἐλέους'), 'ἔλεος')
        self.assertEqual(self.first('υἱοῖς'), 'υἱός')       # from the New Testament analysis
        self.assertEqual(self.first('καὶ'), 'καί')          # grave read as acute
        from scripts.glossary import candidates
        self.assertIn('ἔλεος', candidates('ἔλεός'))         # enclitic second accent
        self.assertEqual(candidates('δ')[0], "δ'")          # elided

    def test_coverage(self):
        c = self.g['coverage']
        self.assertGreater(1 - c['words_without_lemma'] / c['words'], 0.91)


if __name__ == '__main__':
    unittest.main()
