import os as _os
from fnmatch import fnmatch as _fnmatch

import config as _config


class Command:
    def execute(self):
        raise NotImplementedError()


class Find(Command):
    def __init__(self, pattern=''):
        if pattern == '':
            pattern = '*'
        self.__pattern = pattern

    def execute(self):
        found_files = []

        for parent, _, files in _os.walk(_config.root_directory):
            for file in files:
                if _fnmatch(file, self.__pattern):
                    found_files.append(_os.path.relpath(_os.path.join(parent, file), _config.root_directory))

        return self, found_files
