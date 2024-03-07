
from os.path import join
from unittest import TestCase

from huhu.utils import date2epoch, epoch2date, ip4_int2quad, ip4_quad2int, magic_open

from . import DATA_FOLDER


class Date2EpochTest(TestCase):
    """
    Convert date to integer epoch timestamp
    """
    def test_date2epoch_actual_epoch(self):
        date = '[01/Jan/1970:00:00:00 +0000]'
        epoch = date2epoch(date)
        self.assertTrue(isinstance(epoch, int))
        self.assertEqual(epoch, 0)

    def test_date2epoch_one_billion_utc(self):
        date = '[09/Sep/2001:01:46:40 +0000]'
        epoch = date2epoch(date)
        self.assertEqual(epoch, 1_000_000_000)

    def test_date2epoch_one_billion_nz(self):
        date = '[09/Sep/2001:13:46:40 +1200]'
        epoch = date2epoch(date)
        self.assertEqual(epoch, 1_000_000_000)

    def test_date2epoch_one_billion_greenland(self):
        date = '[08/Sep/2001:21:46:40 -0400]'
        epoch = date2epoch(date)
        self.assertEqual(epoch, 1_000_000_000)

    def test_date2epoch_how_low_can_we_go(self):
        date = '[01/Jan/0001:00:00:00 +0000]'
        epoch = date2epoch(date)
        self.assertLess(epoch, -2**35)

    def test_date2epoch_no_year_zero(self):
        date = '[31/Dec/0000:23:59:59 +0000]'
        with self.assertRaises(ValueError):
            date2epoch(date)

    def test_date2epoch_how_high_can_we_go(self):
        date = '[31/Dec/9999:23:59:59 +0000]'
        epoch = date2epoch(date)
        self.assertGreater(epoch, 2**37)

    def test_date2epoch_year_must_be_four_digits(self):
        date = '[01/Jan/10000:00:00:00 +0000]'
        with self.assertRaises(ValueError):
            date2epoch(date)


class Epoch2DateTest(TestCase):
    """
    Convert integer epoch timestamp to date string.
    """
    def test_epoch2date_zero(self):
        epoch = 0
        date = epoch2date(epoch)
        self.assertTrue(isinstance(date, str))
        self.assertEqual(date, '[01/Jan/1970:00:00:00 +0000]')

    def test_epoch2date_one_billion(self):
        date = epoch2date(1_000_000_000)
        self.assertEqual(date, '[09/Sep/2001:01:46:40 +0000]')

    def test_epoch2date_round_trip(self):
        # Go from epoch integer to datestring...
        epoch = 1234567890
        date = epoch2date(epoch)
        self.assertEqual(date, '[13/Feb/2009:23:31:30 +0000]')

        # ...back to epoch integer
        self.assertEqual(date2epoch(date), epoch)

    def test_epoch2date_y2k28(self):
        """
        The end is near!  It's the Y2K38 bug!
        """
        epoch = 2**31 - 1
        date = epoch2date(epoch)
        self.assertEqual(date, '[19/Jan/2038:03:14:07 +0000]')

        # Add one second...  Will the world end?
        epoch += 1
        date = epoch2date(epoch)
        self.assertEqual(date, '[19/Jan/2038:03:14:08 +0000]')

    def test_epoch2date_the_distant_future(self):
        epoch = 2**34
        date = epoch2date(epoch)
        self.assertEqual(date, '[30/May/2514:01:53:04 +0000]')


class IP4Int2QuadTest(TestCase):
    def test_ip4_int2quad(self):
        """
        Convert IPv4 address as 32-bit integer to quad-decimal format
        """
        self.assertEqual(ip4_int2quad(0), '0.0.0.0')
        self.assertEqual(ip4_int2quad(3221226219), '192.0.2.235')
        self.assertEqual(ip4_int2quad(4294967295), '255.255.255.255')


class IP4Quad2IntTest(TestCase):
    def test_ip4_quad2int(self):
        """
        Convert IPv4 address as quad-decimal format to a 32-bit integer
        """
        self.assertEqual(ip4_quad2int('0.0.0.0'), 0)
        self.assertEqual(ip4_quad2int('192.0.2.235'), 3221226219)
        self.assertEqual(ip4_quad2int('255.255.255.255'), 4294967295)


class MagicOpenTest(TestCase):
    def test_magic_open_plain_text(self):
        self._check_file(join(DATA_FOLDER, 'access.log'))

    def test_magic_open_gz_compressed(self):
        self._check_file(join(DATA_FOLDER, 'access.log.gz'))

    def test_magic_open_bz2(self):
        self._check_file(join(DATA_FOLDER, 'access.log.bz2'))

    def test_magic_open_xz_compressed(self):
        self._check_file(join(DATA_FOLDER, 'access.log.xz'))

    def _check_file(self, path):
        "Check that the contents given input file looks right"
        with magic_open(path) as fp:
            for count, line in enumerate(fp, 1):
                self.assertTrue(isinstance(line, str))
                self.assertGreater(len(line), 50)
        self.assertEqual(count, 1000)
