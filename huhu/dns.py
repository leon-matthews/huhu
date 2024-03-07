"""
DNS services module.
"""

import sqlite3
import time

from . import utils


class Record:
    """
    Single DNS record.

    Contains three properties.

    ip
        IP address of the requesting host as an integer, eg. 3221226219
        The util module contains functions to convert the format.
    hostname
        Human-readable hostname of IP address, eg. 'lost.co.nz'
    timestamp
        Unix epoch time that record was resolved (or attempted)
    """
    __slots__ = ('ip', 'timestamp', 'hostname')

    def __init__(self, ip, timestamp, hostname):
        self.ip = ip
        self.timestamp = timestamp
        self.hostname = hostname

    def __len__(self):
        """
        Needed for `sqlite3` binding.
        """
        return len(self.__slots__)

    def __repr__(self):
        date = time.strftime('%Y-%m-%d', time.gmtime(self.timestamp))
        ip4 = utils.ip4_int2quad(self.ip)
        return f"{date} {ip4:<15} {self.hostname}"

    def __getitem__(self, index):
        # TODO Is this being used?
        return self.__getattribute__(self.__slots__[index])


class DNSCache:
    """
    Database backed cache of DNS records.

    Holds a cache of looked-up DNS Records.  'Bad' records, where the hostname
    remains unresolved (ie. hostname=None) are stored as well as complete,
    'good' records that have valid hostnames.
    """
    def __init__(self, path):
        """
        Constructor.

        path
            Path of database file to create.  Use the special value ':memory:'
            to create a temporary, in-RAM database.
        """
        self._connection = sqlite3.connect(path)
        self._check_schema()

    def add_records(self, records):
        """
        Bulk adding of 3-tuple dns records.

        It's not an error to save a record with None for the hostname.  Such
        records are useful to avoid re-checking bad address over and over again.
        The flush_bad() method can be used to periodically re-check bad IPs.
        """
        with self._connection as con:
            query = (
                "INSERT OR REPLACE INTO "
                "    dns_cache (ip, timestamp, hostname) "
                "    VALUES (?, ?, ?);")
            con.executemany(query, records)

    def count(self):
        """
        Count the total number of DNS records in cache.

        Returns: int
        """
        sql = "SELECT count(*) FROM dns_cache;"
        with self._connection as con:
            cur = con.execute(sql)
            count, = cur.fetchone()
            return count

    def flush_bad(self, age):
        """"
        Flush 'bad' cache entries that are older than 'age' second.

        A 'bad' cache entry is one where the hostname is NULL, ie. the last
        attempt at a reverse-DNS lookup failed.

        Args:
            age (int):
                Records created more than this number of seconds ago will be
                deleted, eg. 120 days = 120*24*60*60

        Returns: None
        """
        now = int(time.time())
        then = now - age
        with self._connection as con:
            con.execute(
                "DELETE FROM dns_cache WHERE "
                "timestamp < ? AND hostname IS NULL;", (then,))

    def flush_good(self, age):
        """
        Delete 'good' cache entries older than 'age' seconds.

        A 'good' cache entry is one whose hostname field is not NULL.

        Args:
            age (int):
                Records created more than this number of seconds ago will be
                deleted, eg. 120 days = 120*24*60*60

        Returns: None
        """
        now = int(time.time())
        then = now - age
        with self._connection as con:
            con.execute(
                "DELETE FROM dns_cache WHERE "
                "timestamp < ? AND hostname NOT NULL;", (then,))

    def ip2hostname(self, ip):
        """
        Return a single hostname for given IP address.
        """
        ip32 = utils.ip4_quad2int(ip)
        with self._connection as con:
            query = "SELECT hostname FROM dns_cache WHERE ip=?"
            cur = con.execute(query, (ip32,))
            (hostname,) = cur.fetchone()
            return hostname

    def _check_schema(self):
        """
        Create tables, views and triggers, if required.
        """
        with self._connection as con:

            # Does main table exist?
            cur = con.execute(
                "SELECT name FROM sqlite_master WHERE "
                "type='table' and name='dns_cache'")
            name = cur.fetchone()
            if name is not None:
                return

            schema = """

BEGIN;

CREATE TABLE dns_cache
(
    ip        INTEGER PRIMARY KEY,
    timestamp INTEGER,
    hostname  TEXT
);

COMMIT;

        """
        con.executescript(schema)
