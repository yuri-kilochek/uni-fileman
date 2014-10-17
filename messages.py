import os as _os
from fnmatch import fnmatch as _fnmatch

import config as _config


class Find:
    def __init__(self, pattern):
        self.__pattern = pattern

    @property
    def pattern(self):
        return self.__pattern


class Found:
    def __init__(self, files=()):
        self.__files = tuple(files)

    @property
    def files(self):
        return self.__files


def match(name, pattern):
    if pattern == '':
        pattern = '*'
    return _fnmatch(name, pattern)


def find(pattern):
    if pattern == '':
        pattern = '*'

    found_files = []

    for parent, _, files in _os.walk(_config.root_directory):
        for file in files:
            file = _os.path.relpath(_os.path.join(parent, file), _config.root_directory)
            if match(file, pattern):
                found_files.append(file)

    return found_files
