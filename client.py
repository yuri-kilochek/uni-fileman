import sys

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *
from PyQt4.QtGui import *

import config


class ServerMonitor(QObject):
    server_found = pyqtSignal(str)
    server_lost = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self._servers = {}

        self._udp_socket = QUdpSocket()
        self._udp_socket.bind(QHostAddress.Any, config.announce_port)
        self._udp_socket.readyRead.connect(self._ready_read)

        self._timer = QTimer()
        self._timer.timeout.connect(self._remove_dead_servers)
        self._timer.start(int(config.announce_interval * 1000))

    def _ready_read(self):
        while self._udp_socket.hasPendingDatagrams():
            token, address, _ = self._udp_socket.readDatagram(self._udp_socket.pendingDatagramSize())
            if token.decode() == config.announce_token:
                self._vitalize_server(address.toString())

    def _vitalize_server(self, server_address):
        if server_address in self._servers:
            server_elapsed_timer = self._servers[server_address]
            server_elapsed_timer.restart()
            return
        server_elapsed_timer = QElapsedTimer()
        server_elapsed_timer.start()
        self._servers[server_address] = server_elapsed_timer
        self.server_found.emit(server_address)

    def _remove_dead_servers(self):
        for address in list(self._servers.keys()):
            elapsed_timer = self._servers[address]
            if elapsed_timer.elapsed() / 1000.0 >= 2 * config.announce_interval:
                self._servers.pop(address)
                self.server_lost.emit(address)


class ServerListModel(QAbstractListModel):
    def __init__(self, server_monitor):
        super().__init__()

        self._servers = []

        self._server_monitor = server_monitor
        self._server_monitor.server_found.connect(self._on_server_found)
        self._server_monitor.server_lost.connect(self._on_server_lost)

    def rowCount(self, parent=None):
        return len(self._servers)

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            return self._servers[index.row()]
        return None

    def _on_server_found(self, address):
        i = len(self._servers)
        self.beginInsertRows(QModelIndex(), i, i)
        self._servers.append(address)
        self.endInsertRows()

    def _on_server_lost(self, address):
        i = self._servers.index(address)
        self.beginRemoveRows(QModelIndex(), i, i)
        self._servers.pop(i)
        self.endRemoveRows()


class MainWindow(QMainWindow):
    server_picked = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self._server_list = QListView(self)
        self._server_list.doubleClicked.connect(self._server_picked)
        self.setCentralWidget(self._server_list)

    def _server_picked(self, index):
        address = self.server_list_model.data(index, Qt.DisplayRole)
        self.server_picked.emit(address)

    @property
    def server_list_model(self):
        return self._server_list.model()

    @server_list_model.setter
    def server_list_model(self, model):
        self._server_list.setModel(model)


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

        self._server_monitor = ServerMonitor()

        self._main_window = MainWindow()
        self._main_window.server_list_model = ServerListModel(self._server_monitor)
        self._main_window.server_picked.connect(self._on_server_picked)
        self._main_window.show()

        self._server_connection = None

    def _on_server_picked(self, server_address):
        print('Trying to connect to {}'.format(server_address))
        try:
            self._server_connection = ServerConnection(server_address)
            print('Connected to {}'.format(self._server_connection.address))
        except ServerConnection.Failed as e:
            print('Failed to connect: {}'.format(e))

    def _on_disconnected(self):
        print('Disconnected')
        self._server_connection = None

if __name__ == '__main__':
    sys.exit(Client(sys.argv).exec_())
