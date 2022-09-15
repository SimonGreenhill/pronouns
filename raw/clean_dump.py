#!/usr/bin/env python3
# coding=utf-8
import gzip
import json

from collections import Counter

IGNORE = [
    'admin.logentry',
    'auth.group',
    'auth.user',
    'auth.permission',
    'contenttypes.contenttype',
    'core.alternatename',
    'core.family',
    'core.location',
    'core.note',
    'entry.task',
    'entry.tasklog',
    'redirects.redirect',
    'reversion.revision',
    'reversion.version',
    'sessions.session',
    'sites.site',
    'statistics.statisticalvalue',
    'watson.searchentry',
    
]



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Does something.')
    parser.add_argument("filename", help='filename')
    args = parser.parse_args()

    removed = Counter()
    with gzip.open('dump.json.gz', 'r') as handle:
        out = []
        for i, record in enumerate(json.loads(handle.read().decode('utf-8')), 1):
            if record['model'] in IGNORE:
                removed[record['model']] += 1
            else:
                out.append(record)
    
    print("%d / %d records kept" % (len(out), i))
    for r in removed.most_common():
        print("\t%-40s\t%d" % r)
    
    # write
    with gzip.open('dump.json.gz', 'w') as handle:
        handle.write(json.dumps(out).encode('utf-8'))
    