import sys as _sys

import PyQt4.QtCore as _QtCore

import lookup as _lookup
from connection import Connection as _Connection
from commands import Command as _Command


class _ClientConnection(_Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        print('Client {} connected'.format(self.remote_address))

    def _on_received(self, message):
        print('Client {} sent: {}'.format(self.remote_address, message))
        if isinstance(message, _Command):
            self.send(message.execute())

    def _on_disconnected(self, reason):
        print('Client {} disconnected'.format(self.remote_address) + ('' if reason is None else ': {}'.format(reason)))


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