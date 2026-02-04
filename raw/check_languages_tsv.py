#!/usr/bin/env python3
# coding=utf-8
"""
Checks languages.tsv contains all the tsv files in this directory
"""

from pathlib import Path
import csvw
from clldutils.misc import slug

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
]


def read_languages(filename):
    with csvw.UnicodeDictReader(filename, delimiter='\t') as reader:
        for row in reader:
            yield row

def split_filename(x):
    x = x.split(" ")
    return (" ".join(x[0:-1]), x[-1])


def get_slug(x):
    label = slug(x['Name'])
    if x['Dialect']:
        label = "%s_%s" % (label, slug(x['Dialect']))
    
    if x['Analect'] == 'Bound':
        label = "%s_b" % label

    if x['Variant']:
        label = "%s_%s" % (label, slug(x['Variant']))

    return label


if __name__ == '__main__':
    header = "ID	LocalID	Name	Dialect	Variant	Filename	Glottocode	Analect	Coder	Comment"
    header = [_.strip() for _ in header.split("\t")]
    
    filelist = {
        p.name for p in Path('.').glob("*/*.csv")
    }
    
    seen, slugs = [], []
    max_id = 0
    # start at line num 2 here as header is swallowed
    for i, row in enumerate(read_languages(Path('../etc/languages.tsv')), 2):
        s = get_slug(row)
        lid = int(row['LocalID'])

        # checks
        if not len(row['Filename']):
            print("ERROR: L%d - no filename" % i)

        if not row['Filename'].endswith('.csv'):
            print("ERROR: L%d - %s should be a CSV file" % (i, row['Filename']))

        if row['Filename'] not in filelist:
            print("ERROR: L%d - %s not in languages.tsv (%s?)" % (i, row['Filename'], s))
        
        if len(row['Glottocode']) != 8:
            print("ERROR: L%d - invalid glottocode '%s'" % (i, row['Glottocode']))

        if row['Analect'] not in ("Free", "Bound"):
            print("ERROR: L%d - invalid analect '%s'" % (i, row['Analect']))

        if not row['Coder']:
            print("ERROR: L%d - no coder - %s" % (i, s))
        elif row['Coder'] not in CODERS:
            print("ERROR: L%d - bad coder '%s'" % (i, row['Coder']))
        

        seen.append(row['Filename'])
        
        if s in slugs:
            raise ValueError("CRASH: %s" % s)
        slugs.append(s)
    
        if lid > max_id:
            max_id = lid
            
        #print("\t".join([row[h] for h in header]))

    unseen = {f for f in filelist if f not in seen}
    if unseen:
        print("\n\n")
        print("NEW DATAFILES TO ADD TO ../etc/languages.tsv")
        print("\n\n")
        print("\t".join(header))
        for f in unseen:
            f = Path(f)

            if ' ' not in f.stem:
                raise ValueError("needs a space so I can identify file stem and glottocode")

            fn, gc = split_filename(f.stem)

            assert len(gc) == 8, 'invalid glottocode?'
            max_id += 1
            
            print("\t".join([
                slug(fn),  # ID
                '%d' % max_id,  # LocalID
                f.stem, # Name
                '', # Dialect
                '', # Variant
                str(f), # Filename
                gc, # Glottocode
                'Free', # Analect
                '?', # Coder
                '', # Comment
            ]))



    assert len(seen) == i - 1, "%d != %d" % (len(seen), i - 1)