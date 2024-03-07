#!/usr/bin/env python3

import logging
import math
import random
import threading
import time


NUM_THREADS = 10


logging.basicConfig(level=logging.DEBUG,
    format='%(levelname)-7s [%(threadName)s] %(message)s',
    )


def generate_name(base_name, index, max_index, sep='_'):
    """
    Generate nicely formatted name by appending given index to base name.
    Length of name remains constant by padding index. eg.::

        >>> generate_name('dns', 7, 10)
        'dns_07'
        >>> generate_name('dns', 42, 500)
        'dns_042'

    base_name
        String to use as base for name, eg. 'thread'
    index
        Integer index
    max_index
        Maximum index expected.  Used to reserve space
    sep
        Seperation between base_name and index.  Defaults to single underscore.
    """
    width = math.ceil(math.log(max_index+1, 10))
    return 'dns{0}{1:0{2}}'.format(sep, index, width)

class Resolver(threading.Thread):
    def __init__(self, name):
        super().__init__(name=name)
        self.daemon = True
    def run(self):
        logging.debug('send')
        time.sleep(random.uniform(1.0, 5.0))
        logging.debug('recieve')

def threads_start(num):
    "Create num threads, return resulting threading.Thread objects in list"
    threads = []
    for i in range(num):
        t = Resolver(name=generate_name('dns', i+1, num))
        t.start()
        threads.append(t)
    return threads

def threads_stop(threads, max_wait=10.0, nap_length=1.0):
    """
    Stop worker threads, waiting for them to finish.

    max_wait
        How many seconds to wait before aborting
    nap_length
        How long to nap before re-checking
    """
    waited = 0.0
    while True:
        logging.debug('Waited {}s for threads to finish'.format(waited))

        for t in threads:
            if t.is_alive():
                break
        else:
            logging.info('All threads finished normally')
            break

        time.sleep(nap_length)
        waited += nap_length
        if waited > max_wait:
            logging.warning('Too long waiting for threads, waiting aborted')
            break


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    logging.info('Start program')

    # Start threads
    logging.info('Start creating {} threads'.format(NUM_THREADS))
    threads = threads_start(NUM_THREADS)
    logging.info('Finish creating {} threads'.format(NUM_THREADS))

    # Wait for threads to finish -- to a point...
    logging.info('Waiting for threads to finish')
    threads_stop(threads)

    logging.info('Finish program')
