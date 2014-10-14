import sys as _sys

import PyQt4.QtCore as _QtCore

from server_lookup import ServerAnnouncer as _ServerAnnouncer
from connection import Connection as _Connection


class _Server(_QtCore.QCoreApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self._announcer = _ServerAnnouncer()

        self._client_awaiter = _Connection.Awaiter()
        self._client_awaiter.connected.connect(self._on_client_connected)

    def _on_client_connected(self, client_connection):
        print('Client {} connected'.format(client_connection.remote_address))
        client_connection.send('kek')

if __name__ == '__main__':
    _sys.exit(_Server(_sys.argv).exec_())