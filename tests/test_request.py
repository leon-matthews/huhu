
import os
import tempfile
from unittest import skip, TestCase

from huhu import request


@skip('Being re-developed')
class RequestTester(TestCase):
    "Test the Request class"
    def setUp(self):
        self.values = {
            'domain': 'ribbonrose.co.nz',
            'ip': 1246328924,
            'host': 'gig-4-0-0-nycmnyk-10k05.nyc.rr.com',
            'timestamp': 1265028540,
            'path': '/images/layout/sub-nav-back.jpg',
            'status': 200,
            'size': 1400,
            'referrer': 'http://ribbonrose.co.nz/products/',
            'user_agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.17) '
            'Gecko/2009122116 Firefox/3.0.17 (.NET CLR 3.5.30729)'
        }

    def test_is_sequence(self):
        # Test is sequence by usage, rather than introspection
        req = request.Request(self.values)
        self.assertEqual(len(req), 9)
        for value in req:
            self.assertTrue(value)
        self.assertEqual(req[0], 'ribbonrose.co.nz')
        self.assertEqual(req[4], '/images/layout/sub-nav-back.jpg')

    def test_str(self):
        req = request.Request(self.values)
        line = str(req)
        expected = (
            'ribbonrose.co.nz 1246328924 gig-4-0-0-nycmnyk-10k05.nyc.rr.com '
            '1265028540 /images/layout/sub-nav-back.jpg 200 1400 '
            'http://ribbonrose.co.nz/products/ '
            '"Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.17) '
            'Gecko/2009122116 Firefox/3.0.17 (.NET CLR 3.5.30729)"')
        self.assertEqual(line, expected)

    def test_empty(self):
        # No longer an error to create an empty Request object
        req = request.Request()

        # Or one with only a couple of args
        req = request.Request({'domain': 'lost.co.nz', })


@skip('Being re-developed')
class RequestDBTester(TestCase):
    "Test the RequestDB class"
    _data = os.path.join(os.path.dirname(__file__), 'data')

    def test_create(self):
        rdb = request.RequestDB(':memory:')

        # Let's peek inside the box...
        with rdb._connection as con:

            # Tables
            cur = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")
            tables = {t for (t,) in cur}
            expected = {
                'requests_base',
                'requests_paths',
                'requests_hostnames',
                'requests_user_agents', }
            self.assertEqual(tables, expected)

            # Views
            cur = con.execute(
                "SELECT name FROM sqlite_master WHERE type='view'")
            views = {t for (t,) in cur}
            expected = {'requests'}
            self.assertEqual(views, expected)

            # Indicies
            cur = con.execute(
                "SELECT name FROM sqlite_master WHERE type='index'")
            indicies = {t for (t,) in cur}
            expected = {
                'sqlite_autoindex_requests_hostnames_1',
                'sqlite_autoindex_requests_paths_1',
                'sqlite_autoindex_requests_user_agents_1', }
            self.assertEqual(indicies, expected)

            # Triggers
            cur = con.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'")
            triggers = {t for (t,) in cur}
            expected = {'insert_requests_view'}
            self.assertEqual(triggers, expected)

    def test_open_existing(self):
        """
        Don't throw wobbly when opening existing database
        """
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            db1 = request.RequestDB(path)
            db2 = request.RequestDB(path)
        finally:
            os.remove(path)

    def test_insert_1000(self):
        """
        Create 1000 records in requests database.
        """
        path = os.path.join(self._data, 'access-small.log.gz')
        my_log = logfile.LogFile(path)
        my_format = formats.ApacheCustom()
        my_parser = parser.Parser(my_log, my_format)

        # Send 'em all off to db
        rdb = request.RequestDB(':memory:')
        rdb.add_requests(my_parser)

        # How many created?
        count = rdb.count()
        self.assertEqual(count, 1000)

        # NULL values should only exist in main table
        with rdb._connection as con:
            tables = {
                'requests_paths': 'path',
                'requests_hostnames': 'hostname',
                'requests_user_agents': 'user_agent'}
            for table, column in tables.items():
                sql = f"SELECT count(*) FROM {table} WHERE {column} IS NULL;"
                cur = con.execute(sql)
                count, = cur.fetchone()
                self.assertEqual(count, 0)

        # Check view
        with rdb._connection as con:
            cur = con.execute("SELECT count(*) FROM requests_base;")
            count, = cur.fetchone()
            self.assertEqual(count, 1000)
