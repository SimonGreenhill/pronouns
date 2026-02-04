#!/usr/bin/env python3
# coding=utf-8
"""Tries to standardise glyphs tc"""

import csvw
import unicodedata
from pathlib import Path

EXTENSIONS_TO_IGNORE = ('.py', '.gz', '.zip')


def get(filename, delimiter=","):
    with csvw.UnicodeDictReader(filename, delimiter=delimiter) as reader:
        for row in reader:
            yield(row)

def get_sources(filename):
    with open(filename, 'r') as handle:
        for line in handle:
            if line.startswith("@"):
                yield line.split("{")[1].strip().strip(',')


class Checker(object):
    def __init__(self, filename):
        self.filename = filename
        self.errors, self.rows = [], []
        for row in get(filename, ','):
            self.rows.append(row)
        self.check()
        self.report()
        
        if filename.suffix != '.csv':
            self.error(f"Invalid suffix: {filename}")
        
    def error(self, msg):
        self.errors.append(msg)

    def report(self):
        if self.errors:
            print(f"{self.filename}:")
        for e in self.errors:
            print(f" {e}")
    
    def normalise(self, text):
        # NFC = Normalisation Form C (precomposed preferred)
        return unicodedata.normalize('NFC', text)
    
    def check(self):
        for i, row in enumerate(self.rows, 1):
            # some checks are only valid if we have a stored lexical item in `word`
            entry = row.get('word', '#')
            if entry == '#' or len(entry) == 0:
                has_entry = False
            else:
                has_entry = True
            
            for col, value in row.items():
                if col == 'parameter':
                    if value not in PARADIGMS.keys():
                        self.error(f"Unknown Parameter in row {i}: '{value}'")
                elif col == 'description':
                    pass # Not checked
                    # if value not in PARADIGMS.values():
                    #     self.error(f"Unknown Description in row {i}: '{value}'")
                elif col in ('word', 'ipa', 'comment', 'translation'):
                    if value != self.normalise(value):
                        out = [unicodedata.name(char, 'UNKNOWN') for char in value]
                        self.error(f"Not normalised in row {i}: {value} - {out}")
                elif has_entry and col == 'glottocode':
                    if len(value) != 8:
                        self.error(f"Invalid Glottocode in row {i}: '{value}'")
                elif has_entry and col == 'source':
                    # if we have an entry in `word` we should have a source
                    if value is None or len(value) == 0:
                        self.error(f"Empty Source in row {i}: '{value}'")
                    for s in [v for v in value.split(";")]:
                        if s not in SOURCES:
                            self.error(f"Unknown Source in row {i}: '{s}'")
                        

PARADIGMS = {o['ID']: o['English'] for o in get('etc/concepts.tsv', "\t")}

SOURCES = list(get_sources('./raw/sources.bib'))
SOURCES.append('UNKNOWN')

if __name__ == '__main__':
    errors = 0
    for p in sorted(Path("raw").glob("*/*")):
        if p.is_dir() or p.suffix in EXTENSIONS_TO_IGNORE:
            continue
        try:
            c = Checker(p)
            errors += len(c.errors)
        except Exception as e:
            print(f"Error reading {p}: {e}")
    
    print(errors)