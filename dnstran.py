#!/usr/bin/env python3

import huhu


path = 'tmp/apache-logs/dnscache'
file = huhu.utils.magic_open(path)
parser = huhu.analog.dns_cache_parser
records = []
for line_number, raw in enumerate(file, 1):
    try:
        record = parser(raw)
    except UnicodeDecodeError:
        print('{:,}: corrupt line ignored: {}'.format(line_number, raw))
        continue
    records.append(record)



# reader = huhu.analog.DNSCacheReader('tmp/dnscache', encoding='ascii')
#~ while True:
    #~ try:
        #~ record = next(reader)
    #~ except UnicodeDecodeError as e:
        #~ print(e)
        #~ continue
    #~ except StopIteration:
        #~ break
    #~ records.append(record)

db = huhu.dns.DNSCache('tmp/dnscache.db')
db.add_records(records)
