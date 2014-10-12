import sys

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

import config
from common import *


class Announcer:
    def __init__(self):
        self._udp_socket = QUdpSocket()

        self._timer = QTimer()
        self._timer.timeout.connect(self._announce)
        self._timer.start(int(config.announce_interval * 1000))

    def _announce(self):
        self._udp_socket.writeDatagram(config.announce_token.encode(), QHostAddress.Broadcast, config.announce_port)


class ClientAwaiter(QObject):
    client_connected = pyqtSignal(Connection)

    def __init__(self):
        super().__init__()

        self._tcp_server = QTcpServer()
        self._tcp_server.newConnection.connect(self._new_connection)
        self._tcp_server.listen(QHostAddress.Any, config.connection_port)

    def _new_connection(self):
        while self._tcp_server.hasPendingConnections():
            client_socket = self._tcp_server.nextPendingConnection()
            client_connection = Connection(client_socket)
            self.client_connected.emit(client_connection)


class Server(QCoreApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self._announcer = Announcer()

        self._client_awaiter = ClientAwaiter()
        self._client_awaiter.client_connected.connect(self._on_client_connected)

    def _on_client_connected(self, client_connection):
        print('Client {} connected'.format(client_connection.remote_address))
        client_connection.send('kek')

if __name__ == '__main__':
    sys.exit(Server(sys.argv).exec_())