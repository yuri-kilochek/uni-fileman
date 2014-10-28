import io as _io
import json as _json
import sys as _sys
import os as _os
from fnmatch import fnmatch as _fnmatch
import datetime as _datetime

import PyQt4.QtCore as _QtCore

import lookup as _lookup
from connection import Connection as _Connection
import messages as _messages

from config import config as _config


class _ClientConnection(_Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__username = None

        self.__log('Подключение из {}'.format(self.remote_address), 'Успешно')

    def __on_received_login(self, message):
        self.__log_event('Вход в систему как \'{}\''.format(message.username))

        with _io.open(_config['users-database'], mode='r', encoding='UTF-8') as users_database:
            users = _json.load(users_database)

        if message.username in users:
            if message.password == users[message.username]:
                self.__username = message.username
                self.send(_messages.Authorize())
                self.__log_status('Успешно')
            else:
                self.send(_messages.Error('Неверный пароль'))
                self.__log_status('Ошибка: Неверный пароль')
        else:
            self.send(_messages.Error('Пользователя с таким именем не существует'))
            self.__log_status('Ошибка: Пользователя с таким именем не существует')

    def __on_received_logout(self, message):
        self.__log_event('Выход из системы')

        if self.__username is None:
            self.send(_messages.Error('Не был выполнен вход в систему'))
            self.__log_status('Ошибка: Не был выполнен вход в систему')
            return

        self.send(_messages.Deauthorize())
        self.__log_status('Успешно')
        self.__username = None

    def __on_received_search(self, message):
        pattern = message.pattern
        if pattern == '':
            pattern = '*'

        self.__log_event('Поиск \'{}\''.format(pattern))

        if self.__username is None:
            self.send(_messages.Error('Поиск не удался: Не был выполнен вход в систему'))
            self.__log_status('Ошибка: Не был выполнен вход в систему')
            return

        files = []

        for parent, _, directory_files in _os.walk(_config['root-directory']):
            for file in directory_files:
                file = _os.path.relpath(_os.path.join(parent, file), _config['root-directory'])
                if _fnmatch(file, pattern):
                    files.append(file)

        self.send(_messages.SetAll(files))
        self.__log_status('Успешно')

    def __on_received_rename(self, message):
        self.__log_event('Переименование \'{}\' в \'{}\''.format(message.old_name, message.new_name))

        if self.__username is None:
            self.send(_messages.Error('Переименование не удалось: Не был выполнен вход в систему'))
            self.__log_status('Ошибка: Не был выполнен вход в систему')
            return

        if '/' in message.new_name:
            self.send(_messages.Error('Переименование не удалось: \'{}\' не является допустимым названием для файла.'.format(message.new_name)))
            self.__log_status('Ошибка: \'{}\' не является допустимым названием для файла'.format(message.new_name))
            return

        abs_old_name = _os.path.normpath(_os.path.join(_config['root-directory'], message.old_name))
        abs_new_name = _os.path.normpath(_os.path.join(_config['root-directory'], message.new_name))

        if not _os.path.exists(abs_old_name):
            self.send(_messages.Error('Переименование не удалось: файла с именем \'{}\' не существует.'.format(message.old_name)))
            self.__log_status('Ошибка: файла с именем \'{}\' не существует.'.format(message.old_name))
            return
        if _os.path.exists(abs_new_name):
            self.send(_messages.Error('Переименование не удалось: файл с именем \'{}\' уже существует.'.format(message.new_name)))
            self.__log_status('Ошибка: файл с именем \'{}\' уже существует.'.format(message.new_name))
            return

        _os.rename(abs_old_name, abs_new_name)

        self.send(_messages.Change(message.old_name, message.new_name))
        self.__log_status('Успешно')

    def __on_received_delete(self, message):
        self.__log_event('Удаление \'{}\''.format(message.name))

        if self.__username is None:
            self.send(_messages.Error('Удаление не удалось: Не был выполнен вход в систему'))
            self.__log_status('Ошибка: Не был выполнен вход в систему')
            return

        abs_name = _os.path.normpath(_os.path.join(_config['root-directory'], message.name))

        if not _os.path.exists(abs_name):
            self.send(_messages.Error('Удаление не удалось: файла с именем \'{}\' не существует.'.format(message.name)))
            self.__log_status('Ошибка: файла с именем \'{}\' не существует.'.format(message.name))
            return

        _os.remove(abs_name)

        self.send(_messages.Forget(message.name))
        self.__log_status('Успешно')

    def _on_received(self, message):
        handler = {
            _messages.Login: self.__on_received_login,
            _messages.Logout: self.__on_received_logout,
            _messages.Search: self.__on_received_search,
            _messages.Rename: self.__on_received_rename,
            _messages.Delete: self.__on_received_delete,
        }.get(type(message))
        if handler is None:
            raise AssertionError('Unexpected message: {}'.format(message))
        handler(message)

    def _on_disconnected(self, reason):
        if self.__username is not None:
            self.__log('Выход из системы', 'Успешно')
            self.__username = None
        self.__log('Отключение', 'Успешно')

    def __log_event(self, event):
        self.__event = event

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

    def __log(self, event, status):
        self.__log_event(event)
        self.__log_status(status)


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