#-*- coding: utf-8 -*-
import logging

VERSION = (0, 1, 0, 'final', 1)
LOG_LEVEL = logging.DEBUG


# init logging
logger = logging
logger.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=LOG_LEVEL)


# Taken from Django project
def get_version(version=None):
    """Derives a PEP386-compliant version number from VERSION."""
    if version is None:
        version = VERSION
    assert len(version) == 5
    assert version[3] in ('alpha', 'beta', 'rc', 'final', 'dev')

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for alpha, beta and rc releases

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''
    if version[3] != 'final':
        if version[3] == 'dev':
            sub = version[3]
        else:
            mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c', 'dev': 'dev'}
            sub = mapping[version[3]] + str(version[4])

    return main + sub
