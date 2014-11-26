#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io as _io
import json as _json
import sys as _sys
import os as _os
from fnmatch import fnmatch as _fnmatch
import datetime as _datetime
import signal as _signal


import PyQt4.QtCore as _QtCore

import lookup as _lookup
from connection import Connection as _Connection
import messages as _messages

from config import config as _config
from translation import translate as _tr

# подключение к слиенту
class _ClientConnection(_Connection):
    # конструктор
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__username = None
        self.__client_about_to_disconnect = False

        self.__log(_tr('Connected from {address}').format(address=self.remote_address), _tr('Success'))

    # обработчик сообщения "войти"
    def __on_received_login(self, message):
        self.__log_event(_tr('Logging in as \'{username}\'').format(username=message.username))

        with _io.open(_config['users-database'], mode='r', encoding='UTF-8') as users_database:
            users = _json.load(users_database)

        if message.username in users:
            if message.password == users[message.username]:
                self.__username = message.username
                self.send(_messages.Authorize())
                self.__log_status(_tr('Success'))
            else:
                self.send(_messages.Error(_tr('Login failed: {reason}').format(reason=_tr('Invalid password'))))
                self.__log_status(_tr('Error: {reason}').format(reason=_tr('Invalid password')))
        else:
            self.send(_messages.Error(_tr('Login failed: {reason}').format(reason=_tr('Unknown username'))))
            self.__log_status(_tr('Error: {reason}').format(reason=_tr('Unknown username')))

    # обработчик сообщения "выйти"
    def __on_received_logout(self, message):
        self.__log_event(_tr('Logging out'))

        if self.__username is None:
            self.send(_messages.Error(_tr('Logout failed: {reason}').format(reason=_tr('Not logged in'))))
            self.__log_status(_tr('Error: {reason}').format(reason=_tr('Not logged in')))
            return

        self.send(_messages.Deauthorize())
        self.__log_status(_tr('Success'))
        self.__username = None

    # обработчик сообщения "найти"
    def __on_received_search(self, message):
        pattern = message.pattern
        if pattern == '':
            pattern = '*'

        self.__log_event(_tr('Searching for \'{pattern}\'').format(pattern=pattern))

        if self.__username is None:
            self.send(_messages.Error(_tr('Search failed: {reason}').format(reason=_tr('Not logged in'))))
            self.__log_status(_tr('Error: {reason}').format(reason=_tr('Not logged in')))
            return

        files = []

        for parent, _, directory_files in _os.walk(_config['root-directory']):
            for file in directory_files:
                file = _os.path.relpath(_os.path.join(parent, file), _config['root-directory'])
                if _fnmatch(file, pattern):
                    files.append(file)

        self.send(_messages.SetAll(files))
        self.__log_status(_tr('Success'))

    # обработчик сообщения "переименовать"
    def __on_received_rename(self, message):
        self.__log_event(_tr('Renaming {old_filename} to {new_filename}').format(
            old_filename=message.old_name,
            new_filename=message.new_name))

        if self.__username is None:
            self.send(_messages.Error(_tr('Rename failed: {reason}').format(reason=_tr('Not logged in'))))
            self.__log_status(_tr('Error: {reason}').format(reason=_tr('Not logged in')))
            return

        if '/' in message.new_name:
            self.send(_messages.Error(_tr('Rename failed: {reason}').format(
                reason=_tr('{filename} is not a valid file name').format(filename=message.new_name))))
            self.__log_status(_tr('Error: {reason}').format(
                reason=_tr('{filename} is not a valid file name').format(filename=message.new_name)))
            return

        abs_old_name = _os.path.normpath(_os.path.join(_config['root-directory'], message.old_name))
        abs_new_name = _os.path.normpath(_os.path.join(_config['root-directory'], message.new_name))

        if not _os.path.exists(abs_old_name):
            self.send(_messages.Error(_tr('Rename failed: {reason}').format(
                reason=_tr('{filename} does not exist').format(filename=message.old_name))))
            self.__log_status(_tr('Error: {reason}').format(
                reason=_tr('{filename} does not exist').format(filename=message.old_name)))
            return
        if _os.path.exists(abs_new_name):
            self.send(_messages.Error(_tr('Rename failed: {reason}').format(
                reason=_tr('{filename} already exists').format(filename=message.new_name))))
            self.__log_status(_tr('Error: {reason}').format(
                reason=_tr('{filename} already exists').format(filename=message.new_name)))
            return

        _os.rename(abs_old_name, abs_new_name)

        self.send(_messages.Change(message.old_name, message.new_name))
        self.__log_status(_tr('Success'))

    # обработчик сообщения "удалить"
    def __on_received_delete(self, message):
        self.__log_event(_tr('Deleting \'{filename}\'').format(filename=message.name))

        if self.__username is None:
            self.send(_messages.Error(_tr('Delete failed: {reason}').format(reason=_tr('Not logged in'))))
            self.__log_status(_tr('Error: {reason}').format(reason=_tr('Not logged in')))
            return

        abs_name = _os.path.normpath(_os.path.join(_config['root-directory'], message.name))

        if not _os.path.exists(abs_name):
            self.send(_messages.Error(_tr('Delete failed: {reason}').format(
                reason=_tr('{filename} does not exist').format(filename=message.name))))
            self.__log_status(_tr('Error: {reason}').format(
                reason=_tr('{filename} does not exist').format(filename=message.name)))
            return

        _os.remove(abs_name)

        self.send(_messages.Forget(message.name))
        self.__log_status(_tr('Success'))

    # обработчик сообщения "сейчас отключусь"
    def __on_received_about_to_disconnect(self, message):
        self.__client_about_to_disconnect = True

    # обработчик сообщений
    def _on_received(self, message):
        handler = {
            _messages.Login: self.__on_received_login,
            _messages.Logout: self.__on_received_logout,
            _messages.Search: self.__on_received_search,
            _messages.Rename: self.__on_received_rename,
            _messages.Delete: self.__on_received_delete,
            _messages.AboutToDisconnect: self.__on_received_about_to_disconnect,
        }.get(type(message))
        if handler is None:
            raise AssertionError('Unexpected message: {}'.format(message))
        handler(message)

    # обработчик собыйтия "отключение"
    def _on_disconnected(self, reason):
        if self.__client_about_to_disconnect:
            if self.__username is not None:
                self.__log(_tr('Logging out'), _tr('Success'))
                self.__username = None
            self.__log(_tr('Disconnecting'), _tr('Success'))
        else:
            self.__log(_tr('Connection broken unexpectedly'), _tr('Error'))

    # записать в лог суть события
    def __log_event(self, event):
        self.__event = event

    # записать в лог результат события
    def __log_status(self, status):
        now = _datetime.datetime.now()

        if self.__username is None:
            username = ''
        else:
            username = '<{}>'.format(self.__username)

        with _io.open(_config['log-file'], mode='a', encoding='UTF-8') as log_file:
            log_file.write('{:04}.{:02}.{:02}-{:02}:{:02}:{:02}.{:03} '.format(
                now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond // 1000))
            log_file.write('| ')
            log_file.write('{} {}'.format(self.remote_address, username).ljust(30))
            log_file.write('| ')
            log_file.write(self.__event.ljust(50))
            log_file.write('| ')
            log_file.write(status)
            log_file.write('\n')
        del self.__event

    # записать событие в лог целиком
    def __log(self, event, status):
        self.__log_event(event)
        self.__log_status(status)


# приложение сервера
class _Server(_QtCore.QCoreApplication):
    #  конструктор
    def __init__(self, argv):
        super().__init__(argv)

        self._client_connections = set()

        # обработчик завершения приложения
        def disconnect_all():
            for connection in list(self._client_connections):
                connection.disconnect()
        self.aboutToQuit.connect(disconnect_all)

        self._announcer = _lookup.Announcer()

        self._client_awaiter = _ClientConnection.spawn_awaiter()
        self._client_awaiter.connected.connect(self._on_client_connected)

    # обработчки собыйтия "клиент подключился"
    def _on_client_connected(self, client_connection):
        client_connection.disconnected.connect(lambda: self._client_connections.remove(client_connection))
        self._client_connections.add(client_connection)


if __name__ == '__main__':
    server = _Server(_sys.argv)

    _signal.signal(_signal.SIGINT, lambda *_: server.quit())
    _signal.signal(_signal.SIGTERM, lambda *_: server.quit())

    _sys.exit(server.exec_())