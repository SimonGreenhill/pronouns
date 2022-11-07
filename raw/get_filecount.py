#!/usr/bin/env python3
# coding=utf-8
"""Counts csv files in subdirectories."""

from collections import Counter
from pathlib import Path

if __name__ == '__main__':
    
    tally = Counter()
    for d in Path('.').glob("*/*.csv"):
        tally[d.parent.name] += 1
    
    for d in tally.most_common():
        print("%-30s\t%4d" % d)
