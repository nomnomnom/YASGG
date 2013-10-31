# -*- coding: utf-8 -*-
import os
from . import logger

#from exceptions import WindowsError


if not getattr(__builtins__, 'WindowsError', None):
    class WindowsError(OSError):
        pass
else:
    class WindowsError(WindowsError):
        pass


def walkdir(dir_2_walk, recrusive=True):
    """ Walk a directory using a generator"""
    dir_content = []
    try:
        dir_content = os.listdir(dir_2_walk)
    except WindowsError as e:
        if e.errno == 5:  # access denied errors
            logger.error(e.message)

    for file_walked in dir_content:
        fullpath = os.path.abspath(os.path.join(dir_2_walk, file_walked))
        if recrusive and os.path.isdir(fullpath) and not os.path.islink(fullpath):
            for x in walkdir(fullpath):
                yield x
        else:
            yield fullpath


def checkdir(path):
    """Create the dir if it does not exist"""
    if not os.path.isdir(path):
        os.makedirs(path)