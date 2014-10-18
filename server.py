import sys as _sys
import os as _os
from fnmatch import fnmatch as _fnmatch

import PyQt4.QtCore as _QtCore

import lookup as _lookup
from connection import Connection as _Connection
import messages as _messages

import config as _config

_users = {
    'penis': 'cock'
}


class _ClientConnection(_Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        print('Client {} connected'.format(self.remote_address))

        self.__username = None

    def __on_received_login(self, message):
        if message.username in _users:
            if message.password == _users[message.username]:
                self.__username = message.username
                self.send(_messages.Authorize())
            else:
                self.send(_messages.Error('Invalid password'))
        else:
            self.send(_messages.Error('Unknown user'))

    def __on_received_logout(self, message):
        if self.__username is None:
            self.send(_messages.Error('Not logged in'))
            return
        self.send(_messages.Deauthorize())

    def __on_received_search(self, message):
        pattern = message.pattern
        if pattern == '':
            pattern = '*'

        files = []

        for parent, _, directory_files in _os.walk(_config.root_directory):
            for file in directory_files:
                file = _os.path.relpath(_os.path.join(parent, file), _config.root_directory)
                if _fnmatch(file, pattern):
                    files.append(file)

        self.send(_messages.SetAll(files))

    def __on_received_rename(self, message):
        if '/' in message.new_name:
            self.send(_messages.Error('Rename failed: \'{}\' is not a valid file name.'.format(message.new_name)))
            return

        abs_old_name = _os.path.normpath(_os.path.join(_config.root_directory, message.old_name))
        abs_new_name = _os.path.normpath(_os.path.join(_config.root_directory, message.new_name))

        if not _os.path.exists(abs_old_name):
            self.send(_messages.Error('Rename failed: \'{}\' does not exist.'.format(message.old_name)))
            return
        if _os.path.exists(abs_new_name):
            self.send(_messages.Error('Rename failed: \'{}\' already exists.'.format(message.new_name)))
            return

        _os.rename(abs_old_name, abs_new_name)

        self.send(_messages.Change(message.old_name, message.new_name))

    def __on_received_delete(self, message):
        abs_name = _os.path.normpath(_os.path.join(_config.root_directory, message.name))

        if not _os.path.exists(abs_name):
            self.send(_messages.Error('Delete failed: \'{}\' does not exist.'.format(message.name)))
            return

        _os.remove(abs_name)

        self.send(_messages.Forget(message.name))

    def _on_received(self, message):
        print('Client {} sent: {}'.format(self.remote_address, message))
        handler = {
            _messages.Login: self.__on_received_login,
            _messages.Logout: self.__on_received_logout,
            _messages.Search: self.__on_received_search,
            _messages.Rename: self.__on_received_rename,
            _messages.Delete: self.__on_received_delete,
        }.get(type(message))
        if handler is None:
            raise AssertionError('Unexpected message: {}'.format(message))
        handler(message)

    def _on_disconnected(self, reason):
        print('Client {} disconnected'.format(self.remote_address))


class _Server(_QtCore.QCoreApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self._announcer = _lookup.Announcer()

        self._client_awaiter = _ClientConnection.spawn_awaiter()
        self._client_awaiter.connected.connect(self._on_client_connected)

        self._client_connections = set()

    def _on_client_connected(self, client_connection):
        client_connection.disconnected.connect(lambda: self._client_connections.remove(client_connection))
        self._client_connections.add(client_connection)

if __name__ == '__main__':
    _sys.exit(_Server(_sys.argv).exec_())