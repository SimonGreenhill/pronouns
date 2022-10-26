from setuptools import setup
import json


with open('metadata.json', encoding='utf-8') as fp:
    metadata = json.load(fp)


setup(
    name='lexibank_pronouns',
    description=metadata['title'],
    license=metadata.get('license', ''),
    url=metadata.get('url', ''),
    py_modules=['lexibank_pronouns'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'lexibank.dataset': [
            'pronouns=lexibank_pronouns:Dataset',
        ]
    },
    install_requires=[
        'pylexibank>=3.4.0',
        'openpyxl',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
