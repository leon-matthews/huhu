"""
Useful utility functions.
"""

import bz2
import calendar
from contextlib import contextmanager
import gzip
import logging
import lzma
import os
import socket
import struct
import time


logger = logging.getLogger(__name__)


def date2epoch(date) -> int:
    """
    Convert datetime like '[10/Oct/2000:13:55:36 -0700]' to epoch timestamp.

    Returns integer of timestamp as UTC epoch timestamp, eg.
    >>> date2epoch('[14/Feb/2009:11:31:30 +1200]')
    1234567890
    """
    # Main timestamp
    year = int(date[8:12])
    month = int(date2epoch.months[date[4:7]])
    day = int(date[1:3])
    hour = int(date[13:15])
    minute = int(date[16:18])
    second = int(date[19:21])
    epoch = calendar.timegm((year, month, day, hour, minute, second))

    # Adjust for timezone
    sign = date[-6]
    seconds = int(date[-5:-3])*3600 + int(date[-3:-1])*60
    seconds = - seconds if sign == '+' else seconds
    epoch = epoch + seconds
    return epoch


date2epoch.months = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12',
}


def epoch2date(timestamp) -> str:
    """
    Convert epoch timestamp to date string.

    Note that this is not the exact complement of date2epoch() as this
    method always returns the date in UTC, not local time.

    Date string is returned in the form used in input logs::

        >>> epoch2date(1234567890)
        '[13/Feb/2009:23:31:30 +0000]'
    """
    t = time.gmtime(timestamp)
    date = time.strftime("[%d/%b/%Y:%H:%M:%S +0000]", t)
    return date


def ip4_int2quad(ip) -> str:
    """
    Convert ip4 address as integer to dot-decimal string representation::

        >>> ip4_int2quad(3221226219)
        '192.0.2.235'
    """
    return socket.inet_ntoa(struct.pack('!L', ip))


def ip4_quad2int(ip) -> int:
    """
    Convert ip4 address from dot-decimal string to integer::

        >>> ip4_quad2int('192.0.2.235')
        3221226219
    """
    return struct.unpack('!L', socket.inet_aton(ip))[0]


@contextmanager
def magic_open(path, mode='rt', encoding='utf-8', errors='strict'):
    """
    Open plain or compressed files transparently as context manager.

    Recognises BZ2, GZ, and XZ compressed files. Falls back
    to uncompressed opening if file extension not recognised.

    For example::

        >>> with magic_open(path) as fp:
        ...    do_something()

    Args:
        path: File path to compressed or plain file
        mode: File open mode.
        encoding: Text file encoding.
        errors: How encoding errors should be handled.

    Return:
        A file handle
    """
    filename = os.path.basename(path)
    _, extension = os.path.splitext(filename)
    extension = extension.lower().strip('.')
    logger.debug("Attempting to open file: %r", filename)
    methods = {
        'bz2': bz2,
        'gz': gzip,
        'xz': lzma,
    }
    logger.debug(
        "Supported compressed file extensions are: %s",
        ', '.join(repr(key) for key in methods.keys()))
    method = methods.get(extension)
    kwargs = dict(mode=mode, encoding=encoding, errors=errors)

    # Open file
    if method is None:
        logger.debug("Opening file without compression")
        fp = open(path, **kwargs)
    else:
        logger.debug("Opening file using the '%s' module", method.__name__)
        fp = method.open(path, **kwargs)

    # Context manager
    try:
        yield fp
    finally:
        fp.close()
