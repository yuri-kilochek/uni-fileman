import sys

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *
from PyQt4.QtGui import *

import config


class ServerListener(QObject):
    server_detected = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self._udp_socket = QUdpSocket()
        self._udp_socket.bind(QHostAddress.Any, config.announce_port)
        self._udp_socket.readyRead.connect(self._ready_read)

    def _ready_read(self):
        while self._udp_socket.hasPendingDatagrams():
            token, address, _ = self._udp_socket.readDatagram(self._udp_socket.pendingDatagramSize())
            if token.decode() == config.announce_token:
                self.server_detected.emit(address.toString())


class ServerList(QMainWindow):
    _dead_interval = 2 * config.announce_interval

    server_picked = pyqtSignal(str)

    def update_server(self, server_address):
        for item in map(self._servers.item, range(self._servers.count())):
            if item.text() == server_address:
                timer = item.data(Qt.UserRole)
                timer.restart()
                return
        item = QListWidgetItem(server_address)
        timer = QElapsedTimer()
        timer.start()
        item.setData(Qt.UserRole, timer)
        self._servers.addItem(item)

    def __init__(self):
        super().__init__()

        self._servers = QListWidget(self)
        self._servers.itemDoubleClicked.connect(self._on_pick)
        self.setCentralWidget(self._servers)

        self._server_dropper = QTimer()
        self._server_dropper.timeout.connect(self._drop_dead_servers)
        self._server_dropper.start(int(ServerList._dead_interval * 1000))

    def _on_pick(self, item):
        address = item.text()
        self.server_picked.emit(address)

    def _drop_dead_servers(self):
        for i in range(self._servers.count()):
            item = self._servers.item(i)
            timer = item.data(Qt.UserRole)
            if timer.elapsed() / 1000.0 > ServerList._dead_interval:
                self._servers.takeItem(i)


class ServerConnection(QObject):
    class Failed(Exception):
        pass

    def __init__(self, address):
        super().__init__()

        self._tcp_socket = QTcpSocket()
        self._tcp_socket.connectToHost(address, config.connection_port)
        if not self._tcp_socket.waitForConnected(int(config.connection_timeout * 1000)):
            raise ServerConnection.Failed(self._tcp_socket.errorString())

    @property
    def address(self):
        address = self._tcp_socket.peerAddress()
        if address == QHostAddress.Null:
            return None
        return address.toString()

    def disconnect(self):
        self._tcp_socket.close()


class Client(QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self.server_listener = ServerListener()
        self.server_listener.server_detected.connect(self._on_server_detected)

        self.server_list = ServerList()
        self.server_list.server_picked.connect(self._on_server_picked)
        self.server_list.show()

        self.server_connection = None

    def _on_server_detected(self, server_address):
        #print('Server {} detected'.format(server_address))
        self.server_list.update_server(server_address)

    def _on_server_picked(self, server_address):
        print('Trying to connect to {}'.format(server_address))
        try:
            self.server_connection = ServerConnection(server_address)
            print('Connected to {}'.format(self.server_connection.address))
        except ServerConnection.Failed as e:
            print('Failed to connect: {}'.format(e))

    def _on_disconnected(self):
        print('Disconnected')
        self.server_connection = None

if __name__ == '__main__':
    sys.exit(Client(sys.argv).exec_())
