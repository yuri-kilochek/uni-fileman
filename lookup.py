import PyQt4.QtCore as _QtCore
import PyQt4.QtNetwork as _QtNetwork

import config as _config


class Announcer:
    def __init__(self):
        self._udp_socket = _QtNetwork.QUdpSocket()

        self._timer = _QtCore.QTimer()
        self._timer.timeout.connect(self._announce)
        self._timer.start(int(_config.heartbeat_interval * 1000))

    def _announce(self):
        self._udp_socket.writeDatagram(
            _config.announce_token.encode(),
            _QtNetwork.QHostAddress.Broadcast,
            _config.announce_port
        )


class Monitor(_QtCore.QObject):
    def __init__(self):
        super().__init__()

        self._servers = {}

        self._udp_socket = _QtNetwork.QUdpSocket()
        self._udp_socket.bind(_QtNetwork.QHostAddress.Any, _config.announce_port)
        self._udp_socket.readyRead.connect(self._ready_read)

        self._timer = _QtCore.QTimer()
        self._timer.timeout.connect(self._remove_dead_servers)
        self._timer.start(int(_config.heartbeat_interval * 1000))

    def _ready_read(self):
        while self._udp_socket.hasPendingDatagrams():
            token, address, _ = self._udp_socket.readDatagram(self._udp_socket.pendingDatagramSize())
            if token.decode() == _config.announce_token:
                self._vitalize_server(address.toString())

    server_found = _QtCore.pyqtSignal(str)

    def _vitalize_server(self, server_address):
        if server_address in self._servers:
            server_elapsed_timer = self._servers[server_address]
            server_elapsed_timer.restart()
            return
        server_elapsed_timer = _QtCore.QElapsedTimer()
        server_elapsed_timer.start()
        self._servers[server_address] = server_elapsed_timer
        self.server_found.emit(server_address)

    server_lost = _QtCore.pyqtSignal(str)

    def _remove_dead_servers(self):
        for address in list(self._servers.keys()):
            elapsed_timer = self._servers[address]
            if elapsed_timer.elapsed() >= int(2 * _config.heartbeat_interval * 1000.0):
                self._servers.pop(address)
                self.server_lost.emit(address)
