#!/usr/bin/env python3

import glob
import logging
from pprint import pprint as dump
import sys
from time import perf_counter

from huhu.parser import ApacheLogParser, ApacheLogParserError
from huhu.utils import magic_open


log_format = "%{Host}i %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %D"


def parse(path):
    parser = ApacheLogParser(log_format)
    for path in glob.glob(path):
        with magic_open(path) as fp:
            for linenum, line in enumerate(fp, 1):
                try:
                    data = parser.parse(line)
                except ApacheLogParserError:
                    print(line.strip())
                    print(parser.regex.pattern)
                    print()
        return linenum


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'usage: {sys.argv[0]} PATH', file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]

    start = perf_counter()
    numlines = parse(path)
    elapsed = perf_counter() - start
    lines_per_sec = round(numlines / elapsed)
    print(f"Parsed {numlines:,} lines in {elapsed:.2f} seconds.", end=' ')
    print(f"{lines_per_sec:,} lines per second.")
