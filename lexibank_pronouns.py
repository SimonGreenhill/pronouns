import gzip
import json
from collections import defaultdict
from pathlib import Path

import csvw
import attr
import pylexibank
from clldutils.misc import slug

# where to start numbering the paradigms and lexemes in textfiles
# needs to be larger than whatever's in the website dump
TEXT_START_PARADIGM_ID = 800

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
}

@attr.s
class PronounConcept(pylexibank.Concept):
    LocalID = attr.ib(default=None)
    Slug = attr.ib(default=None)
    Person = attr.ib(default=None)
    Number = attr.ib(default=None)
    Gender = attr.ib(default=None)
    Alignment = attr.ib(default=None)
    Sequence = attr.ib(default=None)


@attr.s
class PronounLexeme(pylexibank.Lexeme):
    LocalID = attr.ib(default=None)
    Comment = attr.ib(default=None)
    Paradigm_ID = attr.ib(default=None)


@attr.s
class PronounLanguage(pylexibank.Language):
    LocalID = attr.ib(default=None)
    Dialect = attr.ib(default=None)



def keep_lexeme(fields, paradigm):
    """Returns true if this lexeme is to be kept"""
    if fields['source'] in SOURCES_TO_IGNORE:
        #print("REMOVING: Bad source", fields)
        return False
    if paradigm in PARADIGMS_TO_IGNORE:
        #print("REMOVING: Bad paradigm", fields)
        return False
    return True


def get_language(x):
    x = x.split(" ")
    return (" ".join(x[0:-1]), x[-1])


def read_text_files(dirname, start_paradigm_id=TEXT_START_PARADIGM_ID):
    for pdm_pk, filename in enumerate(dirname.glob("*.txt"), start_paradigm_id):
        language, glottocode = get_language(filename.stem)
        
        with csvw.UnicodeDictReader(filename, delimiter=";") as reader:
            for row in reader:
                if row['word'] != '#':
                    yield (pdm_pk, language, glottocode, filename.name, row)



class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "pronouns"

    language_class = PronounLanguage
    concept_class = PronounConcept
    lexeme_class = PronounLexeme

    # define the way in which forms should be handled
    form_spec = pylexibank.FormSpec(
        brackets={"(": ")"},        # characters that function as brackets
        separators=";/,",           # characters that split forms e.g. "a, b".
        missing_data=(),            # characters that denote missing data.
        strip_inside_brackets=False # don't remove characters inside brackets
    )

    def cmd_download(self, args):
        pass
        
    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.

        A `pylexibank.cldf.LexibankWriter` instance is available as `args.writer`. Use the methods
        of this object to add data.
        """
        
        args.writer.add_sources()
        
        languages = args.writer.add_languages(
            lookup_factory=lambda x: x['LocalID']
        )
        
        concepts = args.writer.add_concepts(
            id_factory="Slug",
            lookup_factory=lambda c: int(c.attributes['localid'])
        )
        
        # add paradigm table
        args.writer.cldf.add_component(dict(
            url='paradigms.csv',
            tableSchema=dict(
                columns=[
                    dict(name='ID'),
                    dict(name='Language_ID'),
                    dict(name='Analect'),
                    dict(name='Label'),
                    dict(name='Source'),
                    dict(name='Comment'),
                ],
                primaryKey=['ID'])
        ))
        
        
        # PROCESS WEBSITE DUMP:: -----------------------
        
        # one pass to get records into a dict of dicts so we can merge
        # information across objects
        models = defaultdict(dict)
        with gzip.open(self.raw_dir / 'dump.json.gz', 'r') as handle:
            for record in json.loads(handle.read().decode('utf-8')):
                models[record['model']][record['pk']] = record['fields']
        
        # load source mapping
        sources = {}
        for pk, fields in models['core.source'].items():
            #print("%s : %s %s %s" % (fields['slug'], fields['author'], fields['year'], fields['reference']))
            sources[pk] = SOURCES_TO_RENAME.get(fields['slug'], fields['slug'])
        
        # add paradigms from website
        for pk, fields in models['pronouns.paradigm'].items():
            if pk >= TEXT_START_PARADIGM_ID:  # safety check
                raise RuntimeError('paradigm id %d will clash with TEXT_START_PARADIGM_ID' % pk)
            if pk in PARADIGMS_TO_IGNORE:
                continue
            args.writer.objects['paradigms.csv'].append(dict(
                ID=pk,
                Language_ID=languages[str(fields['language'])],
                Analect=fields['analect'],
                Comment=fields['comment'].strip(),  # some trailing spaces in data
                Label=fields['label'],
                Source=sources[fields['source']],
            ))
        
        # find paradigm members for adding to lexemes next...
        pdm_members = {}
        for pk, fields in models['pronouns.pronoun'].items():
            for lex_id in fields['entries']:
                pdm_members[lex_id] = (fields['paradigm'], fields['pronountype'])
        
        # add lexical items
        for pk, fields in models['lexicon.lexicon'].items():
            try:
                pdm_pk = pdm_members[pk][0]
            except KeyError:
                pdm_pk = None
            
            if keep_lexeme(fields, pdm_pk):
                args.writer.add_forms_from_value(
                    LocalID=pk,
                    Language_ID=languages[str(fields['language'])],
                    Parameter_ID=concepts[fields['word']],
                    Value=fields['entry'],
                    Source=sources[fields['source']],
                    Comment=fields['annotation'],
                    Paradigm_ID=pdm_pk
                )


        # PROCESS TEXT FILES:: -----------------------------------
        added_paradigms = []
        start_lexeme_id = 100000
        for pdm_pk, language, glottocode, filename, fields in read_text_files(self.raw_dir / 'txt'):
            
            language_id = slug(language)
            
            # add paradigm if we don't have it
            if pdm_pk not in added_paradigms:
                args.writer.objects['paradigms.csv'].append(dict(
                    ID=pdm_pk,
                    Language_ID=language_id,
                    Analect='F',
                    Comment='',
                    Label='',
                    Source=fields['source']
                ))
                added_paradigms.append(pdm_pk)
            
            # add lexeme
            lex = args.writer.add_forms_from_value(
                LocalID=str(start_lexeme_id),
                Language_ID=language_id,
                Parameter_ID=fields['parameter'],
                Value=fields['word'],
                Source=fields['source'],
                Comment=fields['comment'],
                Paradigm_ID=pdm_pk
            )
            start_lexeme_id += 1
