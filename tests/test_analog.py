
from io import StringIO
from unittest import TestCase

from huhu import analog
from huhu import dns
from huhu import utils

from . import DNSCACHE_PATH


class AnalogReaderReadFile(TestCase):
    def setUp(self):
        self.file = open(DNSCACHE_PATH, encoding='ascii')

    def tearDown(self):
        self.file.close()

    def test_parse_1000(self):
        parser = analog.DNSCacheReader(self.file)
        num_rows = 0
        for row in parser:
            num_rows += 1
            self.assertIsInstance(row, dns.Record)
            self.assertIsInstance(row.ip, int)
            if row.hostname is not None:
                self.assertIsInstance(row.hostname, str)
            self.assertIsInstance(row.timestamp, int)
        self.assertEqual(num_rows, 1000)


class AnalogReaderBadInput(TestCase):
    def setUp(self):
        lines = (
            '21117208 124.128.138.153 *\n'
            'not-enough-fields\n'
            '20878239 6.66.666.666 bad.ip.address.format\n')
        self.file = StringIO(lines)

    def tearDown(self):
        self.file.close()

    def test_bad_input(self):
        parser = analog.DNSCacheReader(self.file)

        # 1st is okay
        r = next(parser)
        self.assertTrue(isinstance(r, dns.Record))

        # 2nd hasn't enough fields
        with self.assertRaisesRegex(ValueError, "^format error: 2: 'not-enou"):
            r = next(parser)

        # 3rd has bad IP address
        with self.assertRaisesRegex(ValueError, "^format error: 3: '20878239"):
            r = next(parser)

        # There is no 4th!
        with self.assertRaises(StopIteration):
            r = next(parser)


class AnalogWriter(TestCase):
    def setUp(self):
        # Fake file
        self.output = StringIO()
        self.input = open(DNSCACHE_PATH, encoding='ascii')

        # Fake DNS record
        ip32 = utils.ip4_quad2int('192.168.0.1')
        timestamp = 1234567890
        hostname = '192-168-0-1.building-3.nasa.gov'
        self.record = dns.Record(ip32, timestamp, hostname)

    def tearDown(self):
        self.input.close()
        self.output.close()

    def test_write_good(self):
        """
        Write `Record` object to file.
        """
        writer = analog.DNSCacheWriter(self.output)
        writer.write(self.record)
        contents = self.output.getvalue()
        expected = '20576131 192.168.0.1 192-168-0-1.building-3.nasa.gov\n'
        self.assertEqual(contents, expected)

    def test_write_no_hostname(self):
        """
        Write `Record` object with no hostname.
        """
        writer = analog.DNSCacheWriter(self.output)
        self.record.hostname = None
        writer.write(self.record)
        expected = '20576131 192.168.0.1 *\n'
        contents = self.output.getvalue()
        self.assertEqual(contents, expected)

    def test_round_trip(self):
        """
        Do a byte-by-byte comparison after a read-write round-trip.
        """
        # Read a bunch of records objects from input file
        reader = analog.DNSCacheReader(self.input)
        records = [record for record in reader]

        # Read same file again, as a plain string this time
        self.input.seek(0)
        file_contents = self.input.read().lower()

        # Write records
        writer = analog.DNSCacheWriter(self.output)
        for record in records:
            writer.write(record)
        contents = self.output.getvalue()

        # Compare
        self.assertEqual(contents, file_contents)
