
import socket
import time
import unittest

from huhu import analog
from huhu import dns
from huhu import utils

from . import DNSCACHE_PATH


class TestDNSRecord(unittest.TestCase):
    def test_record_string(self):
        hostname = '222-154-5-100.jetstream.xtra.co.nz'
        record = dns.Record(3734635876, 1242412860, hostname)
        expected = '2009-05-15 222.154.5.100   ' + hostname
        self.assertEqual(str(record), expected)


class TestDNSCache(unittest.TestCase):
    """
    Test the DNS cache
    """
    def setUp(self):
        self.input = open(DNSCACHE_PATH, encoding='ascii')
        reader = analog.DNSCacheReader(self.input)
        self.records = (record for record in reader)

    def tearDown(self):
        self.input.close()

    def test_errors(self):
        db = dns.DNSCache(':memory:')
        with self.assertRaises(TypeError):
            db.ip2hostname(1234567890)   # Should be a string

        with self.assertRaises(socket.error):
            db.ip2hostname('damn.silly.ip.address')

    def test_queries(self):
        """
        Insert 1000 records from Analog dnscache file
        """
        db = dns.DNSCache(':memory:')

        # Add to database
        db.add_records(self.records)
        count = db.count()
        self.assertEqual(count, 1000)

        # Single lookups
        self.assertEqual(
            db.ip2hostname('118.92.145.70'),
            '118-92-145-70.dsl.dyn.ihug.co.nz')
        self.assertEqual(
            db.ip2hostname('210.86.28.13'),
            'mail.civicwholesale.co.nz')

        # Delete bad records created before 1st Feb 2010
        now = int(time.time())
        age = now - utils.date2epoch('[01/Feb/2010:00:00:00 +0000]')
        db.flush_bad(age)
        self.assertEqual(db.count(), 878)

        # Delete good, but old records: before 1st Nov 2009
        age = now - utils.date2epoch('[01/Oct/2009:00:00:00 +0000]')
        db.flush_good(age)
        self.assertEqual(db.count(), 465)
