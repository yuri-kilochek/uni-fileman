import sys as _sys

import PyQt4.QtCore as _QtCore
import PyQt4.QtGui as _QtGui

import lookup as _lookup
from connection import Connection as _Connection


class _ServerListModel(_QtCore.QAbstractListModel):
    def __init__(self, server_monitor):
        super().__init__()

        self._servers = []

        self._server_monitor = server_monitor
        self._server_monitor.server_found.connect(self._on_server_found)
        self._server_monitor.server_lost.connect(self._on_server_lost)

    def _on_server_found(self, address):
        i = len(self._servers)
        self.beginInsertRows(_QtCore.QModelIndex(), i, i)
        self._servers.append(address)
        self.endInsertRows()

    def _on_server_lost(self, address):
        i = self._servers.index(address)
        self.beginRemoveRows(_QtCore.QModelIndex(), i, i)
        self._servers.pop(i)
        self.endRemoveRows()

    def rowCount(self, parent=None):
        return len(self._servers)

    def data(self, index, role=None):
        if role == _QtCore.Qt.DisplayRole:
            return self._servers[index.row()]
        return None


class _MainWindow(_QtGui.QMainWindow):
    def __init__(self):
        super().__init__()

        self._server_list = _QtGui.QListView(self)
        self._server_list.doubleClicked.connect(self._server_picked)
        self.setCentralWidget(self._server_list)

    server_picked = _QtCore.pyqtSignal(str)

    def _server_picked(self, index):
        address = self.server_list_model.data(index, _QtCore.Qt.DisplayRole)
        self.server_picked.emit(address)

    @property
    def server_list_model(self):
        return self._server_list.model()

    @server_list_model.setter
    def server_list_model(self, model):
        self._server_list.setModel(model)


class _Client(_QtGui.QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self._server_monitor = _lookup.Monitor()

        self._main_window = _MainWindow()
        self._main_window.server_list_model = _ServerListModel(self._server_monitor)
        self._main_window.server_picked.connect(self._on_server_picked)
        self._main_window.show()

        self._server_connection = None

    def _on_server_picked(self, server_address):
        print('Trying to connect to {}'.format(server_address))
        try:
            self._server_connection = _Connection(server_address)
            print('Connected to {}'.format(self._server_connection.remote_address))
            self._server_connection.received.connect(self._on_received)
            self._server_connection.disconnected.connect(self._on_disconnected)
        except _Connection.Failure as e:
            print('Failed to connect: {}'.format(e))

    def _on_received(self, message):
        print('Server says: {}'.format(message))

    def _on_disconnected(self, reason):
        if reason is None:
            print('Disconnected')
        else:
            print('Disconnected: {}'.format(reason))
        self._server_connection = None

if __name__ == '__main__':
    _sys.exit(_Client(_sys.argv).exec_())
