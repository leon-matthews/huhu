"""
Produce error report from access log
"""

from . import logfile


if __name__ == '__main__':
    cache_path = 'data/access.log.pickled'
    try:
        # Attempt to load pre-cached data
        with open(cache_path, 'rb') as fp:
            requests = pickle.load(fp)
    except:
        # Data not pre-cached! :-O
        parser = logfile.ApacheParser()
        input_file = logfile.LogFile('data/access.log.gz', parser)
        requests = input_file.read_data()
        parser.clear_cache()
        with open(cache_path, 'wb') as fp:
            pickle.dump(requests, fp)

    # We only want LogEntry objects with status code of 404
    errors = [x for x in requests if x.status == 404]

    # Build report
    error_stats = collections.defaultdict(int)
    for r in errors:
        key = r.host + r.request
        error_stats[key] += 1

    for key in error_stats:
        print(error_stats[key], key)
