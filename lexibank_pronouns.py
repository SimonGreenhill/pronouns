import gzip
import json
import logging
import dataclasses
from collections import defaultdict
from pathlib import Path
from typing import Optional

import csvw
import pylexibank
from clldutils.misc import slug
from pylexibank.util import progressbar


@dataclasses.dataclass
class PronounConcept(pylexibank.Concept):
    LocalID: Optional[str] = None
    English: Optional[str] = None
    Alignment: Optional[str] = None
    Person: Optional[str] = None
    GrammaticalNumber: Optional[str] = None
    Gender: Optional[str] = None
    Sequence: Optional[str] = None


@dataclasses.dataclass
class PronounLexeme(pylexibank.Lexeme):
    Comment: Optional[str] = None
    Paradigm_ID: Optional[str] = None


@dataclasses.dataclass
class PronounLanguage(pylexibank.Language):
    LocalID: Optional[str] = None
    Dialect: Optional[str] = None
    Variant: Optional[str] = None
    Filename: Optional[str] = None
    Comment: Optional[str] = None
    Analect: str = 'Free'
    Coder: Optional[str] = None

    def __post_init__(self):
        if self.Analect not in ('Free', 'Bound'):
            raise ValueError(
                "Analect must be 'Free' or 'Bound', got %r" % (self.Analect,))



def get_language(x):
    x = x.split(" ")
    return (" ".join(x[0:-1]), x[-1])


def read_text_files(filenames):
    expected_columns = ('word', 'ipa', 'parameter', 'comment', 'glottocode', 'source')
    for filename in filenames:
        language, glottocode = get_language(filename.stem)
        with csvw.UnicodeDictReader(filename, delimiter=",") as reader:
            for row in reader:
                if not all([e in row for e in expected_columns]):
                    raise ValueError(
                    "File %s missing expected column: %r" % (
                        filename,
                        [e for e in expected_columns if e not in row]
                    ))
                if row['word'] and row['word'] not in ('', '?'):
                    yield (language, glottocode, filename.name, row)



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
            lookup_factory=lambda x: x['Filename']
        )
        
        # get paradigm IDs
        paradigms = {
            r['ID']: r['LocalID'] for r in self.etc_dir.read_csv('languages.tsv', delimiter="\t", dicts=True)
        }
        
        concepts = args.writer.add_concepts(id_factory="id")

        filenames = list(sorted(self.raw_dir.glob("*/*.csv")))
        logging.info("%d files found" % len(filenames))
        for language, glottocode, filename, record in progressbar(read_text_files(filenames)):
            if filename not in languages:
                logging.warn("WARNING: Unknown language filename '%s' - add details to ./etc/languages.tsv" % filename)
            
            if record['parameter'] not in concepts:
                logging.warn("WARNING: Unknown parameter %s: %r" % (filename, record['parameter']))
                continue
            
            lang_id = languages.get(filename, slug(language))
            
            value = record['word']
            if value in ('-', '#'):
                value = '∅'
            
            lex = args.writer.add_forms_from_value(
                Language_ID=lang_id,
                Parameter_ID=record['parameter'],
                Value=value,
                Source=record['source'],
                Comment=record['comment'],
                Paradigm_ID=paradigms.get(lang_id)
            )
