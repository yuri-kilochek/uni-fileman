import sys as _sys

import PyQt4.QtCore as _QtCore

import lookup as _lookup
from connection import Connection as _Connection


class _Server(_QtCore.QCoreApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self._announcer = _lookup.Announcer()

        self._client_awaiter = _Connection.Awaiter()
        self._client_awaiter.connected.connect(self._on_client_connected)

        self._client_connections = set()

    def _on_client_connected(self, client_connection):
        print('Client {} connected'.format(client_connection.remote_address))
        self._client_connections.add(client_connection)
        client_connection.send('kek')
        client_connection.disconnected.connect(lambda reason: self._on_disconnected(client_connection, reason))

    def _on_disconnected(self, client_connection, reason):
        if reason is None:
            print('Client {} disconnected'.format(client_connection.remote_address))
        else:
            print('Client {} disconnected: {}'.format(client_connection.remote_address, reason))
        self._client_connections.remove(client_connection)

if __name__ == '__main__':
    _sys.exit(_Server(_sys.argv).exec_())