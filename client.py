import sys as _sys
import os as _os

import PyQt4.QtCore as _QtCore
import PyQt4.QtGui as _QtGui

import lookup as _lookup
from connection import Connection as _Connection
import messages as _messages


class _MainWindow(_QtGui.QWidget):
    def __init__(self):
        super().__init__()

        window_layout = _QtGui.QHBoxLayout()

        self.__server_list = _QtGui.QListView(self)
        self.__server_list.setSelectionMode(_QtGui.QListView.SingleSelection)
        window_layout.addWidget(self.__server_list, 1)

        file_searching = _QtGui.QVBoxLayout()

        pattern_box = _QtGui.QFormLayout()

        self.__search_pattern = _QtGui.QLineEdit(self)
        pattern_box.addRow('Search pattern:', self.__search_pattern)

        file_searching.addLayout(pattern_box)

        self.__file_list = _QtGui.QListView(self)
        file_searching.addWidget(self.__file_list)

        window_layout.addLayout(file_searching, 4)

        self.setLayout(window_layout)

        self.__search_pattern.textEdited.connect(lambda *_: self.search_pattern_changed.emit())

    def set_server_list_model(self, server_list_model):
        if self.__server_list.model() is not None:
            self.__server_list.selectionModel().selectionChanged.disconnect()
        self.__server_list.setModel(server_list_model)
        self.__server_list.selectionModel().selectionChanged.connect(lambda *_: self.selected_server_changed.emit())

    @property
    def selected_server(self):
        selected_indexes = self.__server_list.selectionModel().selectedIndexes()
        if len(selected_indexes) == 0:
            return None
        assert len(selected_indexes) == 1
        selected_index = selected_indexes[0]
        return self.__server_list.model().data(selected_index, _QtCore.Qt.UserRole)

    selected_server_changed = _QtCore.pyqtSignal()

    def set_file_list_model(self, file_list_model):
        self.__file_list.setModel(file_list_model)

    @property
    def search_pattern(self):
        return self.__search_pattern.text()

    search_pattern_changed = _QtCore.pyqtSignal()


class _ActiveServers(_QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()

        self.__servers = []

        self.__server_monitor = _lookup.Monitor()
        self.__server_monitor.server_found.connect(self.__on_server_found)
        self.__server_monitor.server_lost.connect(self.__on_server_lost)

    def __on_server_found(self, address):
        i = len(self.__servers)
        self.beginInsertRows(_QtCore.QModelIndex(), i, i)
        self.__servers.append(address)
        self.endInsertRows()

    def __on_server_lost(self, address):
        i = self.__servers.index(address)
        self.beginRemoveRows(_QtCore.QModelIndex(), i, i)
        self.__servers.pop(i)
        self.endRemoveRows()

    def rowCount(self, parent=_QtCore.QModelIndex()):
        return len(self.__servers)

    def data(self, index, role=_QtCore.Qt.DisplayRole):
        if role in (_QtCore.Qt.DisplayRole, _QtCore.Qt.UserRole):
            return self.__servers[index.row()]
        return None


class _ServerFiles(_QtCore.QAbstractListModel):
    def __init__(self, server_address):
        super().__init__()

        self.__filter_pattern = ''

        self.__files = []

        self.__server_connection = _Connection(server_address)
        self.__server_connection.received.connect(self.__on_received)

        self.__refresh()

    def __refresh(self):
        self.__server_connection.send(_messages.Find(self.__filter_pattern))

    @property
    def filter_pattern(self):
        return self.__filter_pattern

    @filter_pattern.setter
    def filter_pattern(self, filter_pattern):
        self.__filter_pattern = filter_pattern
        self.__refresh()

    def __on_received(self, message):
        print('Server sent {}'.format(message))
        if type(message) is _messages.Found:
            self.beginResetModel()
            self.__files = list(message.files)
            self.endResetModel()
            return
        if type(message) is _messages.Renamed:
            i = self.__files.index(message.old_name)
            self.__files[i] = message.new_name
            self.dataChanged(self.createIndex(i, 0))
            return
        if type(message) is _messages.Deleted:
            i = self.__files.index(message.name)
            self.beginRemoveRows(_QtCore.QModelIndex(), i, i)
            self.__files.pop(i)
            self.endRemoveRows()
            return
        raise AssertionError('Unhandled message: {}'.format(message))

    def rowCount(self, parent=None):
        return len(self.__files)

    def flags(self, index):
        return _QtCore.Qt.ItemIsEnabled | _QtCore.Qt.ItemIsSelectable | _QtCore.Qt.ItemIsEditable

    def data(self, index, role=_QtCore.Qt.DisplayRole):
        if role in (_QtCore.Qt.DisplayRole, _QtCore.Qt.UserRole):
            return self.__files[index.row()]
        if role == _QtCore.Qt.EditRole:
            return _os.path.basename(self.__files[index.row()])
        return None

    def setData(self, index, data, role=_QtCore.Qt.EditRole):
        if role in (_QtCore.Qt.DisplayRole, _QtCore.Qt.UserRole):
            self.__files[index.row()] = data
            self.dataChanged.emit(index, index)
            return True
        if role == _QtCore.Qt.EditRole:
            old_name = self.__files[index.row()]
            new_name = _os.path.join(_os.path.dirname(old_name), data)
            message = _messages.Rename(old_name, new_name)
            self.__server_connection.send(message)
            return False
        return False

    def removeRows(self, start, count, parent=_QtCore.QModelIndex()):
        for name in self.__files[start:start + count]:
            message = _messages.Delete(name)
            self.__server_connection.send(message)
        return False


class _Client(_QtGui.QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self.__main_window = _MainWindow()
        self.__main_window.set_server_list_model(_ActiveServers())
        self.__main_window.selected_server_changed.connect(self.__on_selected_server_changed)
        self.__main_window.show()

    def __on_selected_server_changed(self):
        print('Connection to {}'.format(self.__main_window.selected_server))
        try:
            server_files = _ServerFiles(self.__main_window.selected_server)
            print('Connected')
            self.__main_window.search_pattern_changed.connect(
                lambda: _ServerFiles.filter_pattern.fset(server_files, self.__main_window.search_pattern)
            )
            self.__main_window.set_file_list_model(server_files)
        except _Connection.Failure as e:
            print('Failed to connect: {}'.format(e))


if __name__ == '__main__':
    _sys.exit(_Client(_sys.argv).exec_())
