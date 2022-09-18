#!/usr/bin/env python3
# coding=utf-8
"""Appends source information to txt files"""
import csvw

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Appends source information to txt files.')
    parser.add_argument("filename", help='filename')
    parser.add_argument("source", help="bibtex key")
    args = parser.parse_args()

    out = []
    with csvw.UnicodeDictReader(args.filename, delimiter=';') as reader:
        for i, row in enumerate(reader, 1):
            if row['source']:
                print('Skipping line %d - already has content: %r' % (i, row['source']))
            else:
                row['source'] = args.source
            out.append(row)

    header = out[0].keys()

    with csvw.UnicodeWriter(args.filename, delimiter=";") as writer:
        writer.writerow(header)
        for o in out:
            writer.writerow([o[h] for h in header])
    