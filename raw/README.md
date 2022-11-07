# Source directory

This directory contains the "raw" source data of the dataset from which the
CLDF dataset in [`cldf/`](../cldf) is derived.

## Adding a new language

1. Create the csv file and put into the correct directory

The command `xlsx_to_csv.py` can help if you have a xlsx file:

```shell
python xlsx_to_csv.py /path/to/myfile.xls "other/myfile glottocode.csv"
```

2. Make sure the csv follows the naming scheme "<language> <glottocode>.csv", e.g.:
    Uralic/Awiakay zyud1238.csv
    Uralic/Finnish finn1318.csv
    Uralic/Hungarian hung1274.csv
    
3. Add the bibtex source to the `sources.bib`:

```bibtex
@misc{hoenigman-2014,
    author = {Hoenigman, Darja},
    date = {2014},
    howpublished = {personal communication}
}
```


4. Paste the bibtex key from that source into the `source` column in the spreadsheet, e.g.:

```
word,ipa,parameter,description,localid,alternative,comment,translation,glottocode,source
niŋ,,1sg_s,1st (excl) Person Singular,42955,,,,zyud1238,hoenigman-2014
tay,,1sg_o,1st (excl) Person Singular,42954,,,,zyud1238,hoenigman-2014
```

Note: the python script `add_source_to.py` can help:

```python
python add_source_to.py "other/myfile glottocode.csv" hoenigman-2014
```

5. Run `check_languages_tsv.py` and add the new rows it generates into ../etc/languages.tsv.

6. Edit the coder column in that file to match who provided the data.

