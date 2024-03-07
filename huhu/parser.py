
"""
Parser classes that produces a Request object for every line from the log.

Parsers are responsible for both extracting data from log lines and for
transforming those data into a request.Request object -- the lingua franca of
the system.
"""

import collections
import re


APACHE_LOG_DIRECTIVES = {
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
    '%s': 'status',                 # First status if any internal redirects
    '%>s': 'status',                # Last status if any internal redirects
    '%t': 'time_received',
    '%T': 'sec_taken',              # See also %D
    '%u': 'remote_user',
    '%U': 'request_path',           # Excluding any query string
    '%v': 'server_name',            # Server name from ServerName
    '%V': 'canonical_server_name',  # Server name from UseCanonicalName
}


class ApacheLogParserError(Exception):
    """
    Root exception class.
    """


class ApacheLogParserCompilationError(ApacheLogParserError):
    """
    Problem compiling regex from Apache log file format string.
    """


class ApacheLogParser:
    """
    Break a single line of log file into fields, using a regular expression.

    The regular expression is constructed automatically using the log
    file format directly from the Apache server configuration.

    http://httpd.apache.org/docs/current/mod/mod_log_config.html

    Adapted from the Perl CPAN module `Apache::LogRegex` by Peter Hickman
    (peterhi@ntlworld.com), and the Python port, `apachelog` of the same
    by Harry Fuecks (hfuecks@gmail.com>.
    """
    def __init__(self, log_format):
        """
        Construct parser using Apache configuration directive.

        Args:
            log_format (str): Log format string, eg. "%h %l %u %t \"%r\" %>s %b"
        """
        self.log_format = log_format.strip()
        self.regex, labels = self.construct_regex()
        identifiers = self.translate_directives(labels)
        self.namedtuple = collections.namedtuple('Line', identifiers)

    def construct_regex(self):
        """
        Converts the input format to a regular
        expression, as well as extracting fields

        Raises an exception if it couldn't compile
        the generated regex.
        """
        labels = []
        subpatterns = []
        for element in self.log_format.split():
            labels.append(element)
            if element == '%t':
                subpattern = r'(\[[^\]]+\])'
            elif '"' in element:
                subpattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
            else:
                subpattern = r'(\S+)'
            subpatterns.append(subpattern)

        # Build and compile
        pattern = f"^{' '.join(subpatterns)}$"
        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise ApacheLogParserCompilationError(e) from None

        return regex, labels

    def parse(self, line):
        """
        Parses a single line from the log file and returns
        a dictionary of its contents.

        Raises and exception if it couldn't parse the line

        Args:
            line (str): Raw line of data from log file.

        Returns:
            A `collections.namedtuple` object containing the line's data.
        """
        line = line.strip()
        match = self.regex.match(line)
        if not match:
            raise ApacheLogParserError(f"Unable to parse line: {line!r}")
        return self.namedtuple(*match.groups())

    def translate_directives(self, labels):
        """
        Turn configuration directive labels into nice identifiers.
        """
        labels = [label.strip('"') for label in labels]
        identifiers = []
        for label in labels:
            # Easy or hard?
            if label in APACHE_LOG_DIRECTIVES:
                identifier = APACHE_LOG_DIRECTIVES[label]
            else:
                identifier = self.translate_special_case(label)
            identifiers.append(identifier)
        return identifiers

    find_request_header = re.compile(r'^%\{(?P<name>[\w\-]+)\}i$')

    def translate_special_case(self, label):
        identifier = None

        # %{NAME}i: Request Header variable
        match = self.find_request_header.match(label)
        if match:
            name = match['name']
            name = name.replace('-', '_').lower()
            return f'request_header_{name}'

        if identifier is None:
            identifier = label
        return identifier
