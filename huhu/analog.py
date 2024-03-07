"""
Analog log processor interoperability.

Huhu was written to replace a legacy analog (http://analog.cx/) installation.
This module contains code to read and write some of the data files that the
analog system used.
"""

import socket

from . import dns
from . import utils


class DNSCacheReader:
    """
    Reader for Analog's dnscache files.

    Produces an iterator that returns a Record object for each line in the
    input file.

    Huhu was built to replace a large Analog setup, so needed to be able to take
    advantage of the large reverse DNS cache files that were already present.

    The cache file is space delimited with three fields per line::

        20878239 118.92.145.70 118-92-145-70.dsl.dyn.ihug.co.nz
        21148889 121.63.230.155 *
        21148889 150.101.154.99 mail.advantagekitchens.com.au

    1) The number of *minutes* since Jan 1 1970 (ie. unix time / 60).
    2) IP address being looked up
    3) Result of reverse DNS lookup, or an asterix on failure.

    See http://www.analog.cx/docs/dns.html for details.
    """
    def __init__(self, _file):
        """
        Initialise object.

        _file
            File object.  Should be opened in text mode.
        """
        self._file = _file
        self._cur_line = 0

    def parse(self, line):
        """
        Attempt to create Record object from input string.

        Returns Record object, or None.
        """
        try:
            timestamp, ip, hostname = line.split()
            ip = utils.ip4_quad2int(ip)
            timestamp = int(timestamp) * 60
            hostname = None if hostname == '*' else hostname.lower()
        except (ValueError, socket.error):
            msg = "format error: {}: '{}'".format(self._cur_line, line)
            raise ValueError(msg)
        return dns.Record(ip, timestamp, hostname)

    def __iter__(self):
        self._cur_line = 0
        return self

    def __next__(self):
        self._cur_line += 1
        line = next(self._file)
        line = line.rstrip()
        dns_record = self.parse(line)
        return dns_record


class DNSCacheWriter:
    """
    Write DNS cache file.

    See the documentation for AnalogDNSCacheReader for more details.
    """
    def __init__(self, file):
        """
        Initialise object.

        file
            File object
        """
        self._file = file

    def write(self, record):
        "Write a dns Record object to output"
        assert isinstance(record, dns.Record)
        timestamp = record.timestamp//60
        ip = utils.ip4_int2quad(record.ip)
        hostname = record.hostname
        if hostname is None:
            hostname = '*'
        line = "{} {} {}\n".format(timestamp, ip, hostname)
        self._file.write(line)
