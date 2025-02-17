﻿"""Tests the `session` module in client–server mode."""

########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from fixtures import logging_disabled
from pytest import raises
from sys import argv
import logging


########################################
# Tests                                #
########################################

def test_start():
    with logging_disabled():
        with raises(ValueError):
            mph.option('session', 'invalid')
            mph.start()
    mph.option('session', 'client-server')
    client = mph.start(cores=1)
    assert client.java is not None
    assert client.cores == 1


########################################
# Main                                 #
########################################

if __name__ == '__main__':

    arguments = argv[1:]
    if 'log' in arguments:
        logging.basicConfig(
            level   = logging.DEBUG if 'debug' in arguments else logging.INFO,
            format  = '[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt = '%H:%M:%S')

    test_start()
