
from unittest import skip, TestCase

from huhu.parser import ApacheLogParser


class ApacheLogParserBasicsTest(TestCase):
    """
    Test basic, as well as miscellaneous, functionality.
    """
    def test_clean_whitespace_from_log_format(self):
        clean = "%h %l %u %t \"%r\" %>s %b"
        dirty = "  \t %h %l %u %t \"%r\" %>s %b \n "
        parser = ApacheLogParser(dirty)
        self.assertEqual(parser.log_format, clean)

    def test_build_regex(self):
        parser = ApacheLogParser("%h %l %u %t \"%r\" %>s %b")
        pattern = parser.regex.pattern
        self.assertTrue(pattern.startswith('^'))
        self.assertTrue(pattern.endswith('$'))

    def test_unalias_easy(self):
        """
        Unalias simple directives like 'remote_host' (%h)
        """
        parser = ApacheLogParser("%h %l %u %t \"%r\" %>s %b")
        fields = parser.namedtuple._fields
        expected = (
            'remote_host',
            'remote_logname',
            'remote_user',
            'time_received',
            'request',
            'status',
            'response_size')
        self.assertEqual(fields, expected)

    def test_unalias_request_headers(self):
        parser = ApacheLogParser("\"%{Referer}i\" \"%{User-agent}i\"")
        fields = parser.namedtuple._fields
        expected = (
            'request_header_referer',
            'request_header_user_agent'
        )
        self.assertEqual(len(fields), len(expected))
        self.assertEqual(fields, expected)


class ApacheCommonLogFormatTest(TestCase):
    """
    Test parsing log files in the 'Common Log Format'
    """
    common_format = "%h %l %u %t \"%r\" %>s %b"
    line = ('127.0.0.1 user-identifier frank [10/Oct/2000:13:55:36 -0700]'
            ' "GET /apache_pb.gif HTTP/1.0" 200 2326')

    def test_parse_common_log_line(self):
        parser = ApacheLogParser(self.common_format)
        data = parser.parse(self.line)
        expected = {
            'status': '200',
            'remote_host': '127.0.0.1',
            'remote_logname': 'user-identifier',
            'remote_user': 'frank',
            'request': 'GET /apache_pb.gif HTTP/1.0',
            'response_size': '2326',
            'time_received': '[10/Oct/2000:13:55:36 -0700]'
        }
        self.assertEqual(data._asdict(), expected)


class ApacheExtendedLogFormatTest(TestCase):
    """
    NCSA extended/combined log format
    """
    extended_format = "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
    line = ('66.249.66.1 - - [01/Jan/2017:09:00:00 +0000] '
            '"GET /contact.html HTTP/1.1" 200 250 "http://www.example.com/" '
            '"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"')

    def test_parse_line(self):
        parser = ApacheLogParser(self.extended_format)
        data = parser.parse(self.line)
        expected = {
            'request_header_referer':
                'http://www.example.com/',
            'request_header_user_agent':
                'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'remote_host': '66.249.66.1',
            'remote_logname': '-',
            'remote_user': '-',
            'request': 'GET /contact.html HTTP/1.1',
            'response_size': '250',
            'status': '200',
            'time_received': '[01/Jan/2017:09:00:00 +0000]',
        }
        self.assertEqual(data._asdict().keys(), expected.keys())
        self.assertEqual(data._asdict(), expected)


class ApacheMyFavouriteLogFormatTest(TestCase):
    my_format = "%{Host}i %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %D"

    line = ('arg.co.nz 122.56.197.201 - - [04/Mar/2019:06:25:40 +0000] '
            '"GET /s/common/images/logo.847646ee69b7.png HTTP/1.1" 200 19380 '
            '"https://arg.co.nz/services/" '
            '"Mozilla/5.0 (Linux; Android 6.0.1; ONE E1003) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/72.0.3626.105 Mobile Safari/537.36" 184')

    def test_parse_line(self):
        parser = ApacheLogParser(self.my_format)
        data = parser.parse(self.line)
        expected = {
            'request_header_host': 'arg.co.nz',
            'remote_host': '122.56.197.201',
            'remote_logname': '-',
            'remote_user': '-',
            'request': 'GET /s/common/images/logo.847646ee69b7.png HTTP/1.1',
            'request_header_referer': 'https://arg.co.nz/services/',
            'request_header_user_agent': 'Mozilla/5.0 (Linux; Android 6.0.1; ONE E1003) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/72.0.3626.105 Mobile Safari/537.36',
            'response_size': '19380',
            'status': '200',
            'time_received': '[04/Mar/2019:06:25:40 +0000]',
            'usec_taken': '184',
        }
        self.assertEqual(data._asdict().keys(), expected.keys())
        self.assertEqual(data._asdict(), expected)

    def test_parse_ip6(self):
        line = ('- ::1 - - [04/Mar/2019:06:32:23 +0000] "OPTIONS * HTTP/1.0" '
                '200 - "-" "Apache/2.4.7 (Ubuntu) (internal dummy connection)" 168')
        parser = ApacheLogParser(self.my_format)
        data = parser.parse(line)
        expected = {
            'request_header_host': '-',
            'remote_host': '::1',
            'remote_logname': '-',
            'remote_user': '-',
            'time_received': '[04/Mar/2019:06:32:23 +0000]',
            'request': 'OPTIONS * HTTP/1.0',
            'status': '200',
            'response_size': '-',
            'request_header_referer': '-',
            'request_header_user_agent':
                'Apache/2.4.7 (Ubuntu) (internal dummy connection)',
            'usec_taken': '168',
        }
        self.assertEqual(dict(data._asdict()), expected)
