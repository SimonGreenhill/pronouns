#!/usr/bin/env python3
# coding=utf-8
"""Tries to standardise glyphs tc"""

import csvw
import unicodedata
from pathlib import Path

EXTENSIONS_TO_IGNORE = ('.py', '.gz', '.zip')

CODERS = [
    'Amos Teo',
    'Charlotte van Tongeren',
    'James Bednall',
    'Keira Mullan',
    'Kyla Quinn',
    'Louise Baird',
    'Luis Miguel Berscia',
    'Marie-France Duhamel',
    'Matt Carroll',
    'Naomi Peck',
    'Nick Evans',
    'Oscar McLoughlin-Ning',
    'Owen Edwards',
    'Roberto Herrera',
    'Simon Greenhill',
    'Stef Spronck',
    'Susan Ford',
    'Thiago Chaçon',
    'Wolfgang Barth',
    '?'
]

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

    known_files = None   # monkey patch later
    
    def __init__(self, filename):
        self.filename = filename
        self.errors, self.rows = [], []
        for row in get(filename, ','):
            self.rows.append(row)
        
        if filename.suffix != '.csv':
            self.error(f"Invalid suffix: {filename}")
        
        if filename.name not in self.known_files:
            self.error(f"File not listed in etc/languages.tsv")
        else:
            self.known_files[filename.name] += 1

        self.check()
        self.report()

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



def check_languages_tsv(filename="etc/languages.tsv"):
    for i, row in enumerate(get(filename, "\t"), 2):
        lid = int(row['LocalID'])

        # checks
        if not len(row['Filename']):
            yield f"L{i} - no filename"

        if not row['Filename'].endswith('.csv'):
            yield f"L{i} - {row['Filename']} should be a CSV file"

        if len(row['Glottocode']) != 8:
            yield f"L{i} - invalid glottocode '{row['Glottocode']}'"

        if row['Analect'] not in ("Free", "Bound"):
            yield f"L{i} - invalid analect '{row['Analect']}'"

        if not row['Coder']:
            yield f"L{i} - no coder"
        elif row['Coder'] not in CODERS:
            yield f"L{i} - bad coder '{row['Coder']}'"


PARADIGMS = {o['ID']: o['English'] for o in get('etc/concepts.tsv', "\t")}

SOURCES = list(get_sources('./raw/sources.bib'))
SOURCES.append('UNKNOWN')

Checker.known_files = {o['Filename']: 0 for o in get('etc/languages.tsv', "\t")}


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
    
    
    # check languages.tsv
    print("\n./etc/languages.tsv:")
    for e in check_languages_tsv():
        print(f" {e}")
        errors += 1

    for f in sorted(Checker.known_files):
        if Checker.known_files[f] != 1:
            print(f" `{f}` seen {Checker.known_files[f]} times.")
            errors += 1
    
    print(f"\n\nTOTAL ERRORS: {errors}\n")