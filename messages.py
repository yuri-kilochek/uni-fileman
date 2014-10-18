import os as _os
from fnmatch import fnmatch as _fnmatch

import config as _config


class Find:
    def __init__(self, pattern):
        self.pattern = pattern


class Found:
    def __init__(self, files):
        self.files = files


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

    return Found(found_files)


class Rename:
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name


class Renamed:
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name


class RenameFailed:
    def __init__(self, reason):
        self.reason = reason


def rename(old_name, new_name):
    if _os.path.exists(new_name):
        return RenameFailed('\'{}\' already exists.'.format(new_name))
    _os.rename(old_name, new_name)
    return Renamed(old_name, new_name)
