"""
Web log format classes.

There is one class for every format.  Each class should provide two methods:

parse(line)
    Responsible for both extracting data from a line in the given format, and
    transforming those data into a request.Request object -- the lingua franca
    of the system.  Unused fields in the request object should be left as None.

format(request)
    Given a request object, produce a log file line, to support format
    conversion.  Round-trip conversion using the same log file format should be
    lossless, but may not be when different formats are used, as fields will
    differ.
"""

import re

from . import parser
from . import request
from . import utils


class ApacheCustom:
    """
    Parser for a custom Apache log file format.
    """
    _drop_query_regex = re.compile(r'\?.*$')
    _format = r'"%{Host}i %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"'
    _field_map = {
        '%a': 'remote_ip_address',
        '%A': 'local_ip_address',
        '%b': 'response_size',          # Bytes excluding headers, CLF format
        '%B': 'response_size',          # Bytes excluding headers
        '%D': 'usec_taken',             # Microseconds taken to serve request
        '%f': 'file_name',
        '%h': 'remote_host',            # Plain IP if not resolved
        '%H': 'request_protocol',
        '"%{host}i': 'host',
        '%{referer}i': 'referrer',
        '%{user-agent}i': 'user_agent',
        '%k': 'keepalive_index',        # nth keepalive on same connection
        '%l': 'remote_logname',
        '%m': 'request_method',
        '%p': 'cannonical_port',
        '%P': 'process_id',
        '%q': 'query',
        '%r': 'request',
        '%R': 'handler',
        '%s': 'first_status',           # First status if any internal redirects
        '%>s': 'last_status',           # Last status if any internal redirects
        '%t': 'time_recieved',
        '%T': 'sec_taken',              # See also %D
        '%u': 'remote_user',
        '%U': 'request_path',           # Excluding any query string
        '%v': 'server_name',            # Server name from ServerName
        '%V': 'canonical_server_name',  # Server name from UseCanonicalName
    }

    def __init__(self):
        """
        Initialiser.

        Domain name of host is determined from log file, so so domain needs to
        be passed.
        """
        self._domain = None
        super().__init__()

    def alias(self, name):
        """
        Used by apachelog.parser to rename dictionary keys.
        """
        name = name.lower()
        return self._field_map[name]

    def parse(self, line):
        # Get dictionary of fields from apachelog.parser
        try:
            fields = self.parse(line)
        except parser.ApacheLogParserError:
            msg = "Bogus line found: '{}'".format(line)
            raise ValueError(msg)

        # Create request object from fields mapping
        req = request.Request()

        # Standardise format, etc..
        self.cannonise(fields, req)

        return req

    def cannonise(self, fields, req):

        # Populate request object with values

        # Domain name of website request is for, eg. 'lost.co.nz'
        if self._domain:
            domain = self._domain
        else:
            domain = (
                fields['host'] if 'host' in fields else None) or (
                fields['server_name'] if 'server_name' in fields else None)
            if domain == '-':
                domain = None
            if domain:
                domain = domain.lower()
                domain = domain.replace('www.', '')
        req.domain = domain

        # IP address of remote host
        ip = fields['remote_host']
        if ip == '::1':
            ip = '127.0.0.1'
        ip = utils.ip4_quad2int(ip)
        req.ip = ip

        # Hostname of remote host
        host = None
        req.host = host

        # Timestamp of request (UTC POSIX timestamp)
        timestamp = utils.date2epoch(fields['time_recieved'])
        req.timestamp = timestamp

        # Path of object requested
        path = fields['request'].split()[1]
        path = self._drop_query_regex.sub('', path)
        if not path or path == '*':
            path = None
        req.path = path

        # Status of response, eg. 200, 404
        status = int(fields['last_status'])
        req.status = status

        # Size of response, in bytes
        size = fields['response_size']
        size = None if size == '-' else int(size)
        req.size = size

        # Referrer
        if 'referrer' not in fields:
            referrer = None
        else:
            referrer = fields['referrer']
            if referrer == '-':
                referrer = None
        req.referrer = referrer

        # User agent of remote client
        if 'user_agent' not in fields:
            user_agent = None
        else:
            user_agent = fields['user_agent']
            if user_agent == '-':
                user_agent = None
        req.user_agent = user_agent

        # Return request object
        return req


class ApacheCommon(ApacheCustom):
    _format = r'%h %l %u %t \"%r\" %>s %b'

    def __init__(self, domain):
        """
        Initilise object.

        domain
            Domain of website log file is for.
        """
        self._domain = domain
        super().__init__()


class ApacheCombined(ApacheCommon):
    """
    Same as ApacheCommon with the addition of referrer and user-agent fields.
    """
    _format = r'%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\"'


class ApacheVCommon(ApacheCustom):
    """
    Virtual host version of ApacheCommon.

    One field added.  The first field in log file gives the domain name of the
    virtual host serving the request, eg. 'www.example.com', or 'example.com'.
    """
    _format = r'%v %h %l %u %t \"%r\" %>s %b'


class ApacheVCombined(ApacheCustom):
    """
    Virtual host version of ApacheCombined.

    Virtual host field added, as per the ApacheVCommon class.
    """
    _format = r'%v %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\"'
