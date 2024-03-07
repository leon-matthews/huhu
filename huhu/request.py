"""
HTTP request object and database.
"""

import sqlite3


class Request:
    """
    Request objects are a sequence object with the following fields:

    domain
        Domain of the website requested, eg. 'lost.co.nz'.  Domains are
        normalised by dropping any 'www.' prefix, if present.
        one if not present.
    ip
        IP address of the requesting host as an integer, eg. 3221226219
        The local util module contains functions to convert the format
    host
        Hostname obtained by running a reverse DNS lookup on the host ip.
        If the lookup failed it is set to None
    timestamp
        UTC timestamp of request using UNIX time, eg. 1234567890
        The local util module contains functions to convert the format, as do
        the standard library time, datetime, and calendar modules.
    path
        Request path, eg. '/', or '/images/logo.png'
    status
        Status of request, eg. 200, or 404
    size
        Size of request, excluding headers, in bytes
    referrer
        Referrering host.  Path information is discarded, as no reports
        currently make any use of it.
    user_agent
        User agent, as reported by requesting host.
    """

    __slots__ = (
        'domain', 'ip', 'host', 'timestamp',
        'path', 'status', 'size', 'referrer', 'user_agent',
    )

    def __init__(self, mapping=None):
        """
        Initialise object.

        Will use mapping, if given, to populate object's properties.
        """
        if mapping:
            for key in self.__slots__:
                if key in mapping:
                    setattr(self, key, mapping[key])

    def __len__(self):
        return len(self.__slots__)

    def __getitem__(self, index):
        return self.__getattribute__(self.__slots__[index])

    def __str__(self):
        return '{} {} {} {} {} {} {} {} "{}"'.format(
            self.domain, self.ip, self.host,
            self.timestamp, self.path, self.status, self.size,
            self.referrer, self.user_agent)


class RequestDB:
    """
    Database of webserver request records.

    path
        Path of database file to create.  Use the special value ':memory:' to
        create a temporary in-RAM database.
    """
    def __init__(self, path):
        self._connection = sqlite3.connect(path)
        self._check_schema()

    def add_requests(self, requests):
        """
        Bulk adding of request tuples into database.

        Uses an SQLite view with triggers to simplify insertion logic.
        """
        with self._connection as con:
            query = (
                "INSERT INTO requests"
                "(domain, ip, host, timestamp, path, "
                "status, size, referrer, user_agent) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);")
            con.executemany(query, requests)

    def count(self):
        "Return number of requests in database"
        sql = "SELECT count(*) FROM requests_base;"
        with self._connection as con:
            cur = con.execute(sql)
            count, = cur.fetchone()
            return count

    def _check_schema(self):
        """
        Create tables, views and triggers if required.

        Pretty simple-minded (but fast) approach.  If our main requests table
        does not exist we go ahead and create everything we need.  If it does,
        we assume that everything else exists and is correct.  Schema changes
        are not expected in what is really just a scratch database.
        """
        with self._connection as con:
            # Enable SQLite3 foreign key support
            con.execute('PRAGMA foreign_keys = ON;')

            # Does main table exist?
            cur = con.execute(
                "SELECT name FROM sqlite_master WHERE "
                "type='table' and name='requests_base';")
            name = cur.fetchone()
            if name is not None:
                return

            # Create it all!
            schema = """

BEGIN;

-- Requests data.  Heavily normalised to save space.
-- --------------------------------------------------
CREATE TABLE requests_base
(
    id            INTEGER PRIMARY KEY,
    domain_id     INTEGER REFERENCES requests_hostnames(id),
    ip            INTEGER,
    host          INTEGER,
    timestamp     INTEGER,
    path_id       INTEGER REFERENCES requests_paths(id),
    status        INTEGER,
    size          INTEGER,
    referrer_id   INTEGER REFERENCES requests_hostnames(id),
    user_agent_id INTEGER REFERENCES requests_user_agents(id)
);

-- Full paths
-- ----------
CREATE TABLE requests_paths
(
    id            INTEGER PRIMARY KEY,
    path          TEXT UNIQUE NOT NULL
);

-- Hostnames
-- ---------
CREATE TABLE requests_hostnames
(
    id            INTEGER PRIMARY KEY,
    hostname      TEXT UNIQUE NOT NULL
);

-- User agents
-- -----------
CREATE TABLE requests_user_agents
(
    id            INTEGER PRIMARY KEY,
    user_agent    TEXT UNIQUE NOT NULL
);

-- Denormalised view of request data
-- ---------------------------------
CREATE VIEW requests AS SELECT
    r.id as id,
    h.hostname as domain,
    r.ip as ip,
    r.host as host,
    r.timestamp as timestamp,
    p.path as path,
    r.status as status,
    r.size as size,
    h2.hostname as referrer,
    u.user_agent as user_agent
FROM requests_base as r
LEFT OUTER JOIN requests_hostnames AS h ON r.domain_id == h.id
LEFT OUTER JOIN requests_paths AS p ON r.path_id = p.id
LEFT OUTER JOIN requests_hostnames AS h2 ON r.referrer_id == h2.id
LEFT OUTER JOIN requests_user_agents AS u ON r.user_agent_id == u.id;

-- Allow inserting into view of requests data using SQLite INSTEAD OF trigger
-- --------------------------------------------------------------------------
CREATE TRIGGER insert_requests_view INSTEAD OF INSERT ON requests
BEGIN
INSERT OR IGNORE INTO requests_hostnames (hostname) VALUES (NEW.domain);
INSERT OR IGNORE INTO requests_paths (path) VALUES (NEW.path);
INSERT OR IGNORE INTO requests_user_agents (user_agent) VALUES (NEW.user_agent);
INSERT INTO requests_base (
    domain_id,
    ip,
    host,
    timestamp,
    path_id,
    status,
    size,
    referrer_id,
    user_agent_id
)
VALUES (
    (SELECT id FROM requests_hostnames WHERE hostname=NEW.domain),
    NEW.ip,
    NEW.host,
    NEW.timestamp,
    (SELECT id FROM requests_paths WHERE path=NEW.path),
    NEW.status,
    NEW.size,
    (SELECT id FROM requests_hostnames WHERE hostname=NEW.referrer),
    (SELECT id FROM requests_user_agents WHERE user_agent=NEW.user_agent)
);
END;

COMMIT;

        """
        con.executescript(schema)
