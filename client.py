#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys as _sys

import PyQt4.QtCore as _QtCore
import PyQt4.QtGui as _QtGui

import lookup as _lookup
from connection import Connection as _Connection
import messages as _messages
from translation import translate as _tr

# виджет окна подключения
class _ConnectFrame(_QtGui.QWidget):
    # нажатие кнопки "подключиться"
    connect_commanded = _QtCore.pyqtSignal(str)

    # конструктор
    def __init__(self):
        super().__init__()

        self.setLayout(_QtGui.QVBoxLayout())

        header = _QtGui.QLabel()
        header.setText(_tr('Active servers'))
        self.layout().addWidget(header)

        self.__server_list = _QtGui.QListView()
        self.__server_list.setSelectionMode(_QtGui.QListView.SingleSelection)
        self.layout().addWidget(self.__server_list, 1)

        buttons = _QtGui.QHBoxLayout()

        buttons.addStretch(1)

        connect = _QtGui.QPushButton()
        connect.setText(_tr('Connect'))
        connect.pressed.connect(self.__on_connect_pressed)
        buttons.addWidget(connect, 0)

        self.layout().addLayout(buttons)

    # обработчик нажатия "подключиться"
    def __on_connect_pressed(self):
        indexes = self.__server_list.selectionModel().selectedIndexes()
        if len(indexes) == 0:
            return
        address = self.__server_list.model().data(indexes[0], _QtCore.Qt.DisplayRole)
        self.connect_commanded.emit(address)

    # установить модель списка серверов
    def set_server_list(self, server_list):
        self.__server_list.setModel(server_list)


# виджет окна авторизации
class _LoginFrame(_QtGui.QWidget):
    # нажатие кнопки "войти"
    login_commanded = _QtCore.pyqtSignal(str, str)
    # нажатие кнопки "отключиться"
    disconnect_commanded = _QtCore.pyqtSignal()

    # конструктор
    def __init__(self):
        super().__init__()

        self.setLayout(_QtGui.QVBoxLayout())

        form = _QtGui.QFormLayout()

        username = _QtGui.QLineEdit()
        form.addRow(_tr('Username'), username)

        password = _QtGui.QLineEdit()
        password.setEchoMode(_QtGui.QLineEdit.Password)
        form.addRow(_tr('Password'), password)

        self.layout().addLayout(form, 0)

        self.layout().addStretch(1)

        buttons = _QtGui.QHBoxLayout()

        disconnect = _QtGui.QPushButton()
        disconnect.setText(_tr('Disconnect'))
        disconnect.pressed.connect(self.disconnect_commanded)
        buttons.addWidget(disconnect, 0)

        buttons.addStretch(1)

        login = _QtGui.QPushButton()
        login.setText(_tr('Login'))
        login.pressed.connect(lambda: self.login_commanded.emit(username.text(), password.text()))
        buttons.addWidget(login, 0)

        self.layout().addLayout(buttons, 0)


# виджет списка файлов
class _FilesFrame(_QtGui.QWidget):
    # нажатие кнопки "найти"
    search_commanded = _QtCore.pyqtSignal(str)
    # нажатие кнопки "переименовать"
    rename_commanded = _QtCore.pyqtSignal(str, str)
    # нажатие кнопки "удалить"
    delete_commanded = _QtCore.pyqtSignal(str)
    # нажатие кнопки "выйти"
    logout_commanded = _QtCore.pyqtSignal()

    # конструктор
    def __init__(self):
        super().__init__()

        self.setLayout(_QtGui.QVBoxLayout())

        search_box = _QtGui.QHBoxLayout()

        search_label = _QtGui.QLabel()
        search_label.setText(_tr('Search pattern'))
        search_box.addWidget(search_label, 0)

        search_pattern = _QtGui.QLineEdit()
        search_box.addWidget(search_pattern, 1)

        search = _QtGui.QPushButton()
        search.setText(_tr('Search'))
        search.pressed.connect(lambda: self.search_commanded.emit(search_pattern.text()))
        search_box.addWidget(search, 0)

        self.layout().addLayout(search_box, 0)

        self.__file_list = _QtGui.QListView()
        self.__file_list.setSelectionMode(_QtGui.QListView.ExtendedSelection)
        self.layout().addWidget(self.__file_list, 1)

        bottom_buttons = _QtGui.QHBoxLayout()

        logout = _QtGui.QPushButton()
        logout.setText(_tr('Logout'))
        logout.pressed.connect(self.logout_commanded)
        bottom_buttons.addWidget(logout, 0)

        bottom_buttons.addStretch(1)

        rename = _QtGui.QPushButton()
        rename.setText(_tr('Rename'))
        rename.pressed.connect(self.__on_rename_pressed)
        bottom_buttons.addWidget(rename, 0)

        delete = _QtGui.QPushButton()
        delete.setText(_tr('Delete'))
        delete.pressed.connect(self.__on_delete_pressed)
        bottom_buttons.addWidget(delete, 0)

        self.layout().addLayout(bottom_buttons, 0)

    # список выделенных пользователем файлов
    @property
    def __selected_files(self):
        files = []
        for index in self.__file_list.selectionModel().selectedIndexes():
            file = self.__file_list.model().data(index, _QtCore.Qt.DisplayRole)
            files.append(file)
        return files

    # обработчик нажатия "переименовать"
    def __on_rename_pressed(self):
        for old_name in self.__selected_files:
            dialog = _QtGui.QInputDialog(self)
            dialog.setWindowTitle(_tr('Rename'))
            dialog.setLabelText(_tr('New filename'))
            dialog.setOkButtonText(_tr('OK'))
            dialog.setCancelButtonText(_tr('Cancel'))
            dialog.setTextValue(old_name)
            if dialog.exec_() == 1:
                new_name = dialog.textValue()
                self.rename_commanded.emit(old_name, new_name)

    # обработчик нажатия "удалить"
    def __on_delete_pressed(self):
        for file in self.__selected_files:
            button = _QtGui.QMessageBox.question(self, _tr('Delete'),
                _tr('Are you sure you want to delete \'{filename}\'?').format(filename=file), _tr('Yes'), _tr('No'))
            if button == 0:
                self.delete_commanded.emit(file)

    # установить модель списка файлов
    def set_file_list(self, file_list):
        self.__file_list.setModel(file_list)


# основное окно
class _MainWindow(_QtGui.QMainWindow):
    # нажатие кнопки "подключиться"
    connect_commanded = _QtCore.pyqtSignal(str)
    # нажатие кнопки "отключиться"
    disconnect_commanded = _QtCore.pyqtSignal()
    # нажатие кнопки "войти"
    login_commanded = _QtCore.pyqtSignal(str, str)
    # нажатие кнопки "выйти"
    logout_commanded = _QtCore.pyqtSignal()
    # нажатие кнопки "найти"
    search_commanded = _QtCore.pyqtSignal(str)
    # нажатие кнопки "переименовать"
    rename_commanded = _QtCore.pyqtSignal(str, str)
    # нажатие кнопки "удалить"
    delete_commanded = _QtCore.pyqtSignal(str)

    # коснтруктор
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Fileman')

        # показать окно "о программе"
        def show_about():
            _QtGui.QMessageBox.about(None, _tr('About'), '{}\n\t{}'.format(
                _tr('Fileman (c) 2014'), _tr('made by Yuri Kilochek and Peter Sharapov')))

        self.menuBar().addMenu(_tr('File')).addAction(_tr('Exit')).triggered.connect(_QtGui.QApplication.quit)
        window_menu = self.menuBar().addMenu(_tr('Window'))
        window_menu.addAction(_tr('Maximize')).triggered.connect(lambda: self.showNormal() if self.isMaximized() else self.showMaximized())
        window_menu.addAction(_tr('Minimize')).triggered.connect(self.showMinimized)
        self.menuBar().addMenu(_tr('Help')).addAction(_tr('About')).triggered.connect(show_about)

        self.__connection_frame = _ConnectFrame()
        self.__connection_frame.connect_commanded.connect(self.connect_commanded)

        self.__login_frame = _LoginFrame()
        self.__login_frame.disconnect_commanded.connect(self.disconnect_commanded)
        self.__login_frame.login_commanded.connect(self.login_commanded)

        self.__files_frame = _FilesFrame()
        self.__files_frame.logout_commanded.connect(self.logout_commanded)
        self.__files_frame.search_commanded.connect(self.search_commanded)
        self.__files_frame.rename_commanded.connect(self.rename_commanded)
        self.__files_frame.delete_commanded.connect(self.delete_commanded)

        self.resize(800, 600)

        self.show_connection()

    # извлечь текущий виджет из оконной иерархии (для предотвращения его удаления)
    def __detach_current_frame(self):
        if self.centralWidget() is not None:
            self.centralWidget().setParent(None)

    # показать окно подключения
    def show_connection(self):
        self.__detach_current_frame()
        self.setCentralWidget(self.__connection_frame)

    # показать окно авторизации
    def show_login(self):
        self.__detach_current_frame()
        self.setCentralWidget(self.__login_frame)

    # показать писок файлов
    def show_files(self):
        self.__detach_current_frame()
        self.setCentralWidget(self.__files_frame)

    # установить модель списка серверов
    def set_server_list(self, server_list):
        self.__connection_frame.set_server_list(server_list)

    # установить модель списка файлов
    def set_file_list(self, file_list):
        self.__files_frame.set_file_list(file_list)


# модель списка серверов
class _ActiveServerList(_QtCore.QAbstractListModel):
    # конструктор
    def __init__(self):
        super().__init__()

        self.__servers = []

        self.__server_monitor = _lookup.Monitor()
        self.__server_monitor.server_found.connect(self.__on_server_found)
        self.__server_monitor.server_lost.connect(self.__on_server_lost)

    # обработчик найденного сервера
    def __on_server_found(self, address):
        i = len(self.__servers)
        self.beginInsertRows(_QtCore.QModelIndex(), i, i)
        self.__servers.append(address)
        self.endInsertRows()

    # обработчик потерянного сервера
    def __on_server_lost(self, address):
        i = self.__servers.index(address)
        self.beginRemoveRows(_QtCore.QModelIndex(), i, i)
        self.__servers.pop(i)
        self.endRemoveRows()

    # количество элементов
    def rowCount(self, parent=_QtCore.QModelIndex()):
        return len(self.__servers)

    # содержимое эелемента
    def data(self, index, role=_QtCore.Qt.DisplayRole):
        if role in (_QtCore.Qt.DisplayRole, _QtCore.Qt.UserRole):
            return self.__servers[index.row()]
        return None


# модель списка файлов на удалённом сервере
class _ServerFileList(_QtCore.QAbstractListModel):
    # конструктор
    def __init__(self, server_connection):
        super().__init__()

        self.__on_received_slot = self.__on_received

        self.__files = []

        self.__server_connection = server_connection
        self.__server_connection.received.connect(self.__on_received_slot)

    # обработчик сообщения "обновить весь список список"
    def __on_received_set_all(self, message):
        self.beginResetModel()
        self.__files = message.files
        self.endResetModel()

    # обработчик сообщения "файл изменился"
    def __on_received_change(self, message):
        i = self.__files.index(message.old_name)
        self.__files[i] = message.new_name
        index = self.createIndex(i, 0)
        self.dataChanged.emit(index, index)

    # обработчик сообщения "файл пропал"
    def __on_received_forget(self, message):
        i = self.__files.index(message.file)
        self.beginRemoveRows(_QtCore.QModelIndex(), i, i)
        self.__files.pop(i)
        self.endRemoveRows()

    # обработчик сообщения "деавторизация"
    def __on_received_deauthorize(self, message):
        self.__server_connection.received.disconnect(self.__on_received_slot)

    # обработчик сообщения "ошибка"
    def __on_received_error(self, message):
        _QtGui.QMessageBox.warning(None, _tr('Error'), message.description, _tr('OK'))

    # обработчик принятых сообщений
    def __on_received(self, message):
        handler = {
            _messages.SetAll: self.__on_received_set_all,
            _messages.Change: self.__on_received_change,
            _messages.Forget: self.__on_received_forget,
            _messages.Deauthorize: self.__on_received_deauthorize,
            _messages.Error: self.__on_received_error,
        }.get(type(message))
        if handler is None:
            raise AssertionError('Unexpected message: {}'.format(message))
        handler(message)

    # количество элементов
    def rowCount(self, parent=_QtCore.QModelIndex()):
        return len(self.__files)

    # содержимое элемента
    def data(self, index, role=_QtCore.Qt.DisplayRole):
        if role == _QtCore.Qt.DisplayRole:
            return self.__files[index.row()]
        return None


# приложение клиента
class _Client(_QtGui.QApplication):
    # конструктор
    def __init__(self, argv):
        super().__init__(argv)

        self.__server_connection = None

        # обработчки закрытия приложения
        def on_quit():
            if self.__server_connection is not None:
                try:
                    self.__server_connection.send(_messages.AboutToDisconnect())
                except _Connection.Failure:
                    pass
                self.__server_connection = None
        self.aboutToQuit.connect(on_quit)

        self.__main_window = _MainWindow()
        self.__main_window.connect_commanded.connect(self.__on_connect_commanded)
        self.__main_window.login_commanded.connect(self.__on_login_commanded)
        self.__main_window.disconnect_commanded.connect(self.__on_disconnect_commanded)
        self.__main_window.search_commanded.connect(self.__on_search_commanded)
        self.__main_window.rename_commanded.connect(self.__on_rename_commanded)
        self.__main_window.delete_commanded.connect(self.__on_delete_commanded)
        self.__main_window.logout_commanded.connect(self.__on_logout_commanded)
        self.__main_window.show()

        self.__main_window.set_server_list(_ActiveServerList())
        self.__main_window.show_connection()

    # обработчк команды "подключиться"
    def __on_connect_commanded(self, server_address):
        try:
            self.__server_connection = _Connection(server_address)
            self.__server_connection.disconnected.connect(self.__on_disconnected)
            self.__main_window.show_login()
        except _Connection.Failure as e:
            _QtGui.QMessageBox.critical(None, _tr('Error'), _tr('Failed to connect to {address}:\n\t{error_description}'
                    .format(address=server_address, error_description=e)))

    # обработчк команды "войти"
    def __on_login_commanded(self, username, password):
        def on_received(message):
            self.__server_connection.received.disconnect(on_received)
            if type(message) is _messages.Authorize:
                self.__main_window.set_file_list(_ServerFileList(self.__server_connection))
                self.__main_window.show_files()
                return
            if type(message) is _messages.Error:
                _QtGui.QMessageBox.critical(None, _tr('Error'), message.description)
                return
            raise AssertionError('Unexpected message: {}'.format(message))

        self.__server_connection.received.connect(on_received)
        self.__server_connection.send(_messages.Login(username, password))

    # обработчк команды "отключиться"
    def __on_disconnect_commanded(self):
        self.__main_window.show_connection()
        server_connection = self.__server_connection 
        self.__server_connection = None
        server_connection.disconnect()

    # обработчк команды "найти"
    def __on_search_commanded(self, pattern):
        self.__server_connection.send(_messages.Search(pattern))

    # обработчк команды "переименовать"
    def __on_rename_commanded(self, old_name, new_name):
        self.__server_connection.send(_messages.Rename(old_name, new_name))

    # обработчк команды "удалить"
    def __on_delete_commanded(self, file):
        self.__server_connection.send(_messages.Delete(file))

    # обработчк команды "выйти"
    def __on_logout_commanded(self):
        def on_received(message):
            self.__server_connection.received.disconnect(on_received)
            if type(message) is _messages.Deauthorize:
                self.__main_window.show_login()
                self.__main_window.set_file_list(None)
                return
            if type(message) is _messages.Error:
                _QtGui.QMessageBox.critical(None, _tr('Error'), message.description)
                return
            raise AssertionError('Unexpected message: {}'.format(message))

        self.__server_connection.received.connect(on_received)
        self.__server_connection.send(_messages.Logout())

    # обработчк команды "отключиться"
    def __on_disconnected(self, reason):
        if self.__server_connection is not None:
            self.__server_connection.disconnected.disconnect()
            self.__main_window.show_connection()
            _QtGui.QMessageBox.critical(None, _tr('Error'), _tr('Connection broken unexpectedly'))

if __name__ == '__main__':
    client = _Client(_sys.argv)
    _sys.exit(client.exec_())
