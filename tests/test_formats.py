
from unittest import skip, TestCase

from huhu import formats
from huhu import request


@skip("Refactoring in progress")
class ApacheCustomTest(TestCase):
    """
    Test ApacheCustom format
    """
    def test_line1(self):
        format_ = formats.ApacheCustom()
        line = (
            r'messiah.co.nz 74.52.50.50 - - [21/Feb/2010:00:09:57 +1300] '
            r'"GET / HTTP/1.0" 200 8121 "-" '
            r'"Pingdom.com_bot_version_1.4_(http://www.pingdom.com/)"')
        req = format_.parse(line)
        self.assertTrue(isinstance(req, request.Request))
        self.assertEqual(req.domain, 'messiah.co.nz')
        self.assertEqual(req.ip, 1244934706)
        self.assertEqual(req.host, None)
        self.assertEqual(req.timestamp, 1266664197)
        self.assertEqual(req.path, '/')
        self.assertEqual(req.status, 200)
        self.assertEqual(req.size, 8121)
        self.assertEqual(req.referrer, None)
        self.assertEqual(
            req.user_agent,
            'Pingdom.com_bot_version_1.4_(http://www.pingdom.com/)')

    def test_line2(self):
        line = (
            r'whitecliffe.ac.nz 222.152.20.152 - - '
            r'[21/Feb/2010:00:06:28 +1300] '
            r'"GET /tmp/showcase/graphic-design/thumbnails/IMG_6996.jpg '
            r'HTTP/1.1" 200 2325 '
            r'"http://whitecliffe.ac.nz/showcase/graphic-design/" '
            r'"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET '
            r'CLR 2.0.50727; InfoPath.2; .NET CLR 3.5.30729; .NET '
            r'CLR 3.0.30618)"')
        req = format_.parse(line)
        self.assertTrue(isinstance(req, request.Request))
        self.assertEqual(req.domain, 'whitecliffe.ac.nz')
        self.assertEqual(req.ip, 3734508696)
        self.assertEqual(req.host, None)
        self.assertEqual(req.timestamp, 1266663988)
        self.assertEqual(req.path, '/tmp/showcase/graphic-design/thumbnails/IMG_6996.jpg')
        self.assertEqual(req.status, 200)
        self.assertEqual(req.size, 2325)
        self.assertEqual(req.referrer, 'http://whitecliffe.ac.nz/showcase/graphic-design/')
        self.assertEqual(req.user_agent, (
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; '
            '.NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.5.30729; '
            '.NET CLR 3.0.30618)'))

    def test_line3(self):
        line = (
            r'www.ribbonrose.co.nz 74.73.120.92 - - '
            r'[21/Feb/2010:11:19:03 +1300] '
            r'"GET /images/layout/sub-nav-back.jpg HTTP/1.1" 200 1400 '
            r'"http://www.ribbonrose.co.nz/css/default.css" "Mozilla/5.0 '
            r'(Windows; U; Windows NT 6.0; en-US; rv:1.9.0.17) Gecko/2009122116'
            r' Firefox/3.0.17 (.NET CLR 3.5.30729)"')
        req = format_.parse(line)
        self.assertTrue(isinstance(req, request.Request))
        self.assertEqual(req.domain, 'ribbonrose.co.nz')
        self.assertEqual(req.ip, 1246328924)
        self.assertEqual(req.timestamp, 1266704343)
        self.assertEqual(req.path, '/images/layout/sub-nav-back.jpg')
        self.assertEqual(req.status, 200)
        self.assertEqual(req.size, 1400)
        self.assertEqual(req.referrer, 'http://www.ribbonrose.co.nz/css/default.css')
        self.assertEqual(
            req.user_agent,
            "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.17) "
            "Gecko/2009122116 Firefox/3.0.17 (.NET CLR 3.5.30729)")

    def test_line_bogus(self):
        format_ = formats.ApacheCustom()
        line = 'blah blah blah'
        with self.assertRaisesRegex(ValueError, "^Bogus line found: 'blah blah blah'$"):
            format_.parse(line)

    def test_missing_fields(self):
        format_ = formats.ApacheCustom()
        line = (
            r'- 74.52.50.50 - - [21/Feb/2010:00:09:57 +1300] '
            r'"GET / HTTP/1.0" 200 - "-" "-"')
        req = format_.parse(line)
        self.assertEqual(req.domain, None)
        self.assertEqual(req.ip, 1244934706)
        self.assertEqual(req.host, None)
        self.assertEqual(req.timestamp, 1266664197)
        self.assertEqual(req.path, '/')
        self.assertEqual(req.status, 200)
        self.assertEqual(req.size, None)
        self.assertEqual(req.referrer, None)
        self.assertEqual(req.user_agent, None)


@skip("Refactoring in progress")
class ApacheCommonTest(TestCase):
    def test_apache_common(self):
        format_ = formats.ApacheCommon('example.com')
        line = (
            r'127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
            r'"GET /apache_pb.gif HTTP/1.0" 200 2326')
        req = format_.parse(line)
        self.assertEqual(req.domain, 'example.com')
        self.assertEqual(req.ip, 2130706433)
        self.assertEqual(req.host, None)
        self.assertEqual(req.timestamp, 971211336)
        self.assertEqual(req.path, '/apache_pb.gif')
        self.assertEqual(req.status, 200)
        self.assertEqual(req.size, 2326)
        self.assertEqual(req.referrer, None)
        self.assertEqual(req.user_agent, None)

    def test_bogus_timestamp(self):
        format_ = formats.ApacheCommon('example.com')
        line = (
            r'127.0.0.1 - frank [10/Oct/200:13:55:36 -0700] '
            r'"GET /apache_pb.gif HTTP/1.0" 200 2326')
        with self.assertRaises(ValueError):
            format_.parse(line)


@skip("Refactoring in progress")
class ApacheCombined(TestCase):
    def test_apache_combined(self):
        format_ = formats.ApacheCombined('example.com')
        line = (
            r'127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
            r'"GET /apache_pb.gif HTTP/1.0" 200 2326 '
            r'"http://www.example.com/start.html" '
            r'"Mozilla/4.08 [en] (Win98; I ;Nav)"')
        req = format_.parse(line)
        self.assertEqual(req.domain, 'example.org')
        self.assertEqual(req.ip, 2130706433)
        self.assertEqual(req.host, None)
        self.assertEqual(req.timestamp, 971211336)
        self.assertEqual(req.path, '/apache_pb.gif')
        self.assertEqual(req.status, 200)
        self.assertEqual(req.size, 2326)
        self.assertEqual(req.referrer, 'http://www.example.com/start.html')
        self.assertEqual(req.user_agent, 'Mozilla/4.08 [en] (Win98; I ;Nav)')


@skip("Refactoring in progress")
class ApacheVCommonTest(TestCase):
    def test_apache_vcommon(self):
        format_ = formats.ApacheVCommon()
        line = (
            r'example.com 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
            r'"GET /apache_pb.gif HTTP/1.0" 200 2326')
        req = format_.parse(line)
        self.assertEqual(req.domain, 'example.com')
        self.assertEqual(req.ip, 2130706433)
        self.assertEqual(req.host, None)
        self.assertEqual(req.timestamp, 971211336)
        self.assertEqual(req.path, '/apache_pb.gif')
        self.assertEqual(req.status, 200)
        self.assertEqual(req.size, 2326)
        self.assertEqual(req.referrer, None)
        self.assertEqual(req.user_agent, None)


@skip("Refactoring in progress")
class ApacheVCombinedTest(TestCase):
    def test_apache_vcombined(self):
        format_ = formats.ApacheVCombined()
        line = (
            r'example.org 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
            r'"GET /apache_pb.gif HTTP/1.0" 200 2326 '
            r'"http://www.example.com/start.html" '
            r'"Mozilla/4.08 [en] (Win98; I ;Nav)"')
        req = format_.parse(line)
        self.assertEqual(req.domain, 'example.org')
        self.assertEqual(req.ip, 2130706433)
        self.assertEqual(req.host, None)
        self.assertEqual(req.timestamp, 971211336)
        self.assertEqual(req.path, '/apache_pb.gif')
        self.assertEqual(req.status, 200)
        self.assertEqual(req.size, 2326)
        self.assertEqual(req.referrer, 'http://www.example.com/start.html')
        self.assertEqual(req.user_agent, 'Mozilla/4.08 [en] (Win98; I ;Nav)')
