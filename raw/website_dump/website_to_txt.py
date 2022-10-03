import gzip
import json
from collections import defaultdict, Counter
from pathlib import Path

import csvw
import attr
from pyglottolog import Glottolog


GLOTTOLOG = Path("/Users/simon/Library/Application Support/cldf/glottolog")

RAW_DIR = Path(".")

# remove duplicates and replace "in press's" etc with published versions
SOURCES_TO_RENAME = {
    # OLD -> NEW
    'Evans_et_al_to_appear': 'EvansEtAl_2017',
    'green-rebecca-1987': 'green-1987',
    'casad-eugene-1984': 'casad-1984',
    'casad-eugene-h': 'casad-1984',
    'aikhenvald-2003b': 'aikhenvald-2003',
    'matthew-j-carroll-2017': 'carroll-2017',
    'carroll-mj-2017': 'carroll-2017',
    'tsunoda-1988': 'tsunoda-1981',  # wrong year
    'evans-personal-communication-1': 'evans-2013',
    'evans-personal-communication-2': 'evans-2013',
    'doehler': 'doehler-2013',
    'doehler-christian': 'doehler-2013',
    'doehler-spreadsheet': 'doehler-2013',
    
}


SOURCES_TO_IGNORE = {
    248: 'greenhill-2014',   # Simon's test data
}


PARADIGMS_TO_IGNORE = {
    28: 'aneityum', # have cleaned version
    85: 'klon', # have cleaned version
    124: 'korowai', # have cleaned version
    125: 'teiwa', # have cleaned version
    126: 'usan', # have cleaned version
    127: 'kobon', # have cleaned version
    132: 'fasu ', # have cleaned version
    136: 'mian', # have cleaned version
    137: 'oksapmin',  # have cleaned version
    151: 'sentani', # have cleaned version
    152: 'abui', # have cleaned version
    168: 'adang', # have cleaned version
    169: 'mauwake', # have cleaned version
    
    475: 'yagua',   # empty, 476 is complete variant.
    468: 'bribri',  # empty, 470 is complete variant.
    469: 'bribri',  # empty, 470 is complete variant.
    
    490: 'Macaguán',  # 489 is better

    496: 'chimila', # empty, 523 is complete variant.


    511: 'tsafiki', # empty, 516 is complete variant.
    515: 'cabiyari', # empty, 526 is complete variant.
    639: 'arammba-setavi',  # empty, 641 is complete variant.
    640: 'arammba-setavi',  # empty, 641 is complete variant.
    648: 'english', # empty, 237 is complete variant.
    672: 'crow',  # duplicate list see 342
    
    678: 'malay-manado', # empty, 679 is complete variant.

    699: 'nggarna', # empty, no data.
}



PARADIGMS_TO_RENAME = {
    # (Language, Dialect, Variant)
    338: ('Cupeño', '', '[ICR OMN]'),
    462: ('Cupeño', '', '[ICR RH]'),
    
    664: ('Burarra', '', '[ICR NE]'),
    692: ('Burarra', '', '[ICR LB]'),
    667: ('Burarra', '', '[ICR RH]'),

    659: ('Cora', '', '[ICR KQ]'),
    691: ('Cora', '', '[ICR LB]'),
    669: ('Cora', '', '[ICR NE]'),
    660: ('Cora', '', '[ICR TCC]'),
    655: ('Cora', '', '[ICR WB]'),

    653: ('Mekens', '', '[ICR LB]'),
    668: ('Mekens', '', '[ICR RH]'),
    661: ('Mekens', '', '[ICR TCC]'),
    656: ('Mekens', '', '[ICR WB]'),
    
    658: ('Mundari', '', '[ICR KQ]'),
    652: ('Mundari', '', '[ICR LB]'),
    662: ('Mundari', '', '[ICR TCC]'),
    
    651: ('Ngiti', '', '[ICR LB]'),
    665: ('Ngiti', '', '[ICR TCC]'),
    654: ('Ngiti', '', '[ICR WB]'),
    
    657: ('Welsh', '', '[ICR KQ]'),
    663: ('Welsh', '', '[ICR NE]'),
    666: ('Welsh', '', '[ICR RH]'),

    414: ('Tariana', '', '[ICR OMN]'),
    534: ('Tariana', '', '[ICR TCC]'),

    467: ('Northern Embera', '', '[Mortensen]'),
    503: ('Northern Embera', '', '[Pardo and Aguirre]'),
    
    477: ('Cubeo', '', '[Chacon]'),
    429: ('Cubeo', '', '[Morse and Maxwell]'),
}



DIRMAP = {
    'afro1255': RAW_DIR / 'Afro-Asiatic',
    'algi1248': RAW_DIR / 'Algic',
    'araw1281': RAW_DIR / 'Arawakan',
    'atla1278': RAW_DIR / 'Atlantic-Congo',
    'aust1305': RAW_DIR / 'Austroasiatic',
    'aust1307': RAW_DIR / 'Austronesian',
    'cari1283': RAW_DIR / 'Cariban',
    'drav1251': RAW_DIR / 'Dravidian',
    'indo1319': RAW_DIR / 'Indo-European',
    'nakh1245': RAW_DIR / 'Nakh-Daghestanian',
    'nucl1709': RAW_DIR / 'Nuclear Trans New Guinea',
    'pama1250': RAW_DIR / 'Pama-Nyungan',
    'pano1259': RAW_DIR / 'Pano-Tacanan',
    'sali1255': RAW_DIR / 'Salishan',
    'sino1245': RAW_DIR / 'Sino-Tibetan',
    'taik1256': RAW_DIR / 'Tai-Kadai',
    'tupi1275': RAW_DIR / 'Tupian',
    'turk1311': RAW_DIR / 'Turkic',
    'ural1272': RAW_DIR / 'Uralic',
    'utoa1244': RAW_DIR / 'Uto-Aztecan',

    'other': RAW_DIR / 'Other',
}

def get_name(language, dialect, variant, analect, glottocode):
    filename = language.replace('/', '-')
    if dialect:
        filename = "%s (%s)" % (filename, dialect)
    if variant:
        filename = "%s [%s]" % (filename, variant)
        
    if analect in (None, 'F', 'Free', 'free'):
        pass
    elif analect in ('B', 'Bound', 'bound'):
        filename = "%s [bound]" % filename
    else:
        raise ValueError("Bad analect %s" % analect)
    
    filename = '%s %s.csv' % (filename, glottocode)
    return filename


def write_csv(filename, records):
    header = [
        'word', 'ipa', 'parameter', 'description', 'localid', 'alternative',
        'comment', 'translation', 'glottocode', 'source'
    ]

    with csvw.UnicodeWriter(filename, delimiter=",") as writer:
        writer.writerow(header)
        for record in records:
            writer.writerow([record[h].strip() for h in header])



if __name__ == '__main__':
    
    for d in DIRMAP:
        if not DIRMAP[d].exists():
            DIRMAP[d].mkdir()
    
    G = Glottolog(GLOTTOLOG)
    
    # one pass to get records into a dict of dicts so we can merge
    # information across objects
    models = defaultdict(dict)
    with gzip.open(RAW_DIR / 'dump.json.gz', 'r') as handle:
        for record in json.loads(handle.read().decode('utf-8')):
            models[record['model']][record['pk']] = record['fields']
    
    # load source mapping
    sources = {}
    for pk, fields in models['core.source'].items():
        sources[pk] = SOURCES_TO_RENAME.get(fields['slug'], fields['slug'])

    # load languages from etc mapping (which has updated glottocodes etc)
    glottocodes = {}
    # ('ID', 'gapapaiwa'), ('LocalID', '357'), ('Name', 'Gapapaiwa'), ('Dialect', ''), ('ISO639P3code', 'pwg'), ('Glottocode', 'gapa1238')])
    with csvw.UnicodeDictReader(RAW_DIR / '../../etc/languages.tsv', delimiter="\t") as reader:
        for row in reader:
            try:
                pk = int(row['LocalID'])
            except:
                pk = row['LocalID']
            
            glottocodes[pk] = row['Glottocode']


    # load pronoun keys for sorting purposes below:
    pronoun_keys = {}
    with csvw.UnicodeDictReader(RAW_DIR / '../../etc/concepts.tsv', delimiter="\t") as reader:
        for row in reader:
            pronoun_keys[row['Slug']] = int(row['LocalID'])


    # load languages
    # 664 {'editor': ['louise'], 'added': '2017-07-17T00:18:01.509Z',
    # 'language': 'Wati-Wati', 'dialect': None, 'slug': 'wati-wati',
    # 'isocode': None, 'glottocode': None, 'classification': 'Australian,
    # Kulin', 'information': '', 'family': []}
    languages = {}
    for pk, fields in models['core.language'].items():
        assert pk in glottocodes, 'LocalID: %s not in ../../etc/languages.tsv' % pk
        languages[pk] = {'slug': fields['slug'], 'language': fields['language'], 'dialect': fields['dialect']}
    
    
    concepts = {}
    for pk, fields in models['lexicon.word'].items():
        concepts[pk] = {
            'word': fields['word'],  # 3pl N P
            'slug': fields['slug'],  # 3pl_n_p
            'full': fields['full'],  # 3rd Person Plural Neuter
        }

    # get paradigm -> lexeme mappings
    mappings = defaultdict(list)
    for pk, fields in models['pronouns.pronoun'].items():
        mappings[fields['paradigm']].extend(fields['entries'])

    # load lexical items
    lexicon = {}
    for pk, fields in models['lexicon.lexicon'].items():
        if fields['source'] in SOURCES_TO_IGNORE:
            print("REMOVING: Bad source: %d = %s" % (fields['source'], SOURCES_TO_IGNORE[fields['source']]))
            continue

        #{'editor': ['simon'], 'added': '2013-10-10T06:56:14.372Z', 'language':
        #3, 'source': 1, 'word': 72, 'entry': 'ynd', 'phon_entry': None,
        #'source_gloss': None, 'annotation': None, 'loan': False, 'loan_source':
        #None}
        lang_pk = fields['language']
        if lang_pk not in glottocodes:
            raise ValueError("Unknown language %d" % lang_pk)

        assert fields['word'] in concepts
        
        lexicon[pk] = dict(
            word=fields['entry'],
            ipa="",
            parameter=concepts[fields['word']]['slug'],
            description=concepts[fields['word']]['full'],
            alternative="",
            comment=fields['annotation'],
            translation="",
            localid=pk,
            glottocode=glottocodes[lang_pk],
            source=sources[fields['source']],
        )
    
    # load paradigms from website
    # {'editor': ['simon'], 'added': '2013-10-10T06:55:42.384Z', 'language': 3, 'source': 1, 'comment': '', 'analect': 'F', 'label': None}
    
    written_paradigms = []
    for pdm_pk, fields in models['pronouns.paradigm'].items():
        if pdm_pk in PARADIGMS_TO_IGNORE:
            print("REMOVING: Bad paradigm: %d = %s/%s/%s/%s" % (pdm_pk, fields['language'], fields['source'], fields['analect'], fields['label']))
            continue
        
        glottocode = glottocodes[fields['language']]

        if pdm_pk in PARADIGMS_TO_RENAME:
            language, dialect, variant = PARADIGMS_TO_RENAME[pdm_pk]
            print("RENAME: %d -> %s %s" % (pdm_pk, language, variant))
        else:
            language = languages[fields['language']]['language']
            dialect = languages[fields['language']]['dialect']
            variant = None
    
        o = G.languoid(glottocode)
        
        try:
            family_id = o.family.id
        except:
            family_id = 'other'  # no family = isolate
        
        if family_id not in DIRMAP:
            family_id = 'other'
        
        output_dir = DIRMAP[family_id]
        
        # analect - label
        if fields['analect'] in ('F', None):
            analect = 'Free'
        elif fields['analect'] == 'B':
            analect = 'Bound'
        else:
            raise ValueError("Unknown Analect: %s" % fields['analect'])
        
        filename = output_dir / get_name(language, dialect, variant, analect, glottocode)
        
        
        if len(mappings[pdm_pk]) == 0:
            raise ValueError("ERROR %d" % pdm_pk)
        
        # collect lexemes and sort
        records = [lexicon[r] for r in lexicon if r in mappings[pdm_pk]]
        records = sorted(records, key=lambda k: (pronoun_keys[k['parameter']]))
        
        print(
            "WRITING: %d %s (n=%d) -> %s/%s" % (
            pdm_pk, language, len(mappings[pdm_pk]),
            output_dir,
            filename.name
        ))
        
        if filename.exists():
            raise IOError("Filename duplicate! %s" % filename)
        write_csv(filename, records)

        written_paradigms.append({
            'ID': pdm_pk,
            'LocalID': pdm_pk,
            'Name': language,
            'Dialect': dialect,
            'Variant': variant,
            'Filename': filename.name,
            'ISO639P3code': '',
            'Glottocode': glottocode,
            'Analect': analect,
            'Comment': fields['comment'],
        })
    
    header = ["ID", "LocalID", "Name", "Dialect", "Variant", "Filename", "ISO639P3code", "Glottocode", "Analect", "Comment"]
    with csvw.UnicodeWriter('languages.tmp', delimiter="\t") as writer:
        writer.writerow(header)
        for p in written_paradigms:
            writer.writerow([p[h] for h in header])
    