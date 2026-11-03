#!/usr/bin/env python3
"""Regression tests for style_check.py: language, genre and first person on the texts the harness writes.

Run with: python3 -m unittest discover -s skills/system/sf-writing-style/scripts -p 'test_*.py'
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_check as sc  # noqa: E402  # pyright: ignore[reportMissingImports]

PR_EN = (
    "Adds export controls to the reports page so users can download the data they see. The download keeps the "
    "current filters and the date range. It's not a new report, it's the same table as a file.\n"
)
README_EN = """---
title: Platform runbook
---

# Deploy

We deploy the cluster with Terraform first, then Helm. Our state file lives in a bucket that only the platform team
can write.
"""
SPEC_IT = """---
os: linux
host: paolo-cto-framework-12
tags: [sway, tablet]
---

# Rotazione tablet

Abbiamo configurato la rotazione automatica. Il nostro script legge l'orientamento e ruota lo schermo.
"""
SLACK_IT = "Abbiamo rilasciato la nuova pipeline su staging. Il job di build ora dura quattro minuti invece di dodici.\n"
STUDY_EN = """---
tipo: studio
lang: en
cliente: Example Client Ltd
---

# Regions

The workloads move from us-east-1 to europe-west1, and the US-based nodes are drained first. We propose a pilot.
"""


def kinds(result, key, field):
    return [x[field] for x in result[key]]


class LanguageTest(unittest.TestCase):
    def test_english_without_front_matter_is_english(self):
        r = sc.check(PR_EN)
        self.assertEqual(r['lang'], 'en')
        self.assertIn('antithesis', kinds(r, 'tells', 'tell'))

    def test_italian_without_front_matter_is_italian(self):
        self.assertEqual(sc.check(SLACK_IT)['lang'], 'it')

    def test_front_matter_lang_wins(self):
        self.assertEqual(sc.check('---\nlang: it\ntipo: doc\n---\n\n' + PR_EN)['lang'], 'it')


class GenreTest(unittest.TestCase):
    def test_front_matter_without_document_keys_is_plain_text(self):
        for text in (README_EN, SPEC_IT):
            r = sc.check(text)
            self.assertEqual(r['genre'], 'text')
            self.assertEqual(r['voice'], [])

    def test_sf_docs_genres_are_unchanged(self):
        cases = {
            '---\ntipo: studio\ncliente: X\n---\n\nTesto.\n': 'doc',
            '---\ncliente: X\n---\n\nTesto.\n': 'offer',
            '---\ncliente: X\n---\n\n<!-- slide: cover -->\nTesto.\n': 'deck',
            '---\nevento: Codemotion\n---\n\n<!-- slide: cover -->\nTesto.\n': 'talk',
        }
        for text, genre in cases.items():
            self.assertEqual(sc.check(text)['genre'], genre, text)


class FirstPersonTest(unittest.TestCase):
    def test_region_and_country_are_not_first_person(self):
        r = sc.check(STUDY_EN)
        words = kinds(r, 'voice', 'word')
        self.assertEqual(words, ['We'])

    def test_english_moves_for_english_documents(self):
        move = sc.check(STUDY_EN)['voice'][0]['move']
        self.assertTrue(move.startswith('First person plural'), move)



class CalqueTest(unittest.TestCase):
    def test_italian_calques_name_the_english_term(self):
        r = sc.check('---\ntipo: studio\nlang: it\n---\n\nIl team legge il cruscotto di uso e costi. Il dispiegamento avviene ogni sera.\n')
        found = {b['phrases'][0].lower(): b['use'] for b in r['banned'] if b.get('use')}
        self.assertEqual(found, {'cruscotto': 'dashboard', 'dispiegamento': 'deploy'})

    def test_english_terms_and_ordinary_italian_pass(self):
        r = sc.check('---\ntipo: studio\nlang: it\n---\n\nIl team legge la dashboard. Il rilascio segue la specifica.\n')
        self.assertEqual([b for b in r['banned'] if b.get('use')], [])


if __name__ == '__main__':
    unittest.main()
