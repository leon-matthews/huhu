#!/usr/bin/env python3

import os

import huhu

# Read log file into SQL DB
###########################


# LogFile iterator
in_file = 'temtp/access.2020-06-10.log'
my_logfile = huhu.logfile.LogFile(in_file)
print("Opened input logfile: '{}'".format(in_file))

# Parser iterator
my_format = huhu.formats.ApacheCustom()
my_parser = huhu.parser.Parser(my_logfile, my_format)
print("Created parser using custom format object.")

# Create database from iterators
out_file = 'access.db'
if os.path.isfile(out_file):
    os.remove(out_file)
    print("Delete old database file: '{}'".format(out_file))

for req in my_parser:
    pass

#~ db = huhu.request.RequestDB(out_file)
#~ print("Create database file: '{}'".format(out_file))
#~ print("Adding requests to database")
#~ db.add_requests(my_parser)
print("Finished")
print()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} PATH_TO_LOG", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
