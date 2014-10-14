import pickle as _pickle
import struct as _struct

import PyQt4.QtCore as _QtCore
import PyQt4.QtNetwork as _QtNetwork

import config as _config


class Connection(_QtCore.QObject):
    class Failure(Exception):
        pass

    class Awaiter(_QtCore.QObject):
        def __init__(self):
            super().__init__()

            self._tcp_server = _QtNetwork.QTcpServer()
            self._tcp_server.newConnection.connect(self._new_connection)
            self._tcp_server.listen(_QtNetwork.QHostAddress.Any, _config.connection_port)

        connected = _QtCore.pyqtSignal(_QtCore.QObject)  # actually Connection but python can't

        def _new_connection(self):
            while self._tcp_server.hasPendingConnections():
                client_socket = self._tcp_server.nextPendingConnection()
                client_connection = Connection(tcp_socket=client_socket)
                self.connected.emit(client_connection)

    def __init__(self, address=None, **kwargs):
        assert (address is None) == ('tcp_socket' in kwargs)

        super().__init__()

        if address is None:
            tcp_socket = kwargs['tcp_socket']
        else:
            tcp_socket = _QtNetwork.QTcpSocket()
            tcp_socket.connectToHost(address, _config.connection_port)
            if not tcp_socket.waitForConnected(int(_config.connection_timeout * 1000)):
                raise Connection.Failure(tcp_socket.errorString())

        self._tcp_socket = tcp_socket
        self._tcp_socket.readyRead.connect(self._receive)
        self._remote_address = self._tcp_socket.peerAddress().toString()

        self._receive_buffer = bytearray()

        self._beater = _QtCore.QTimer()
        self._beater.timeout.connect(self._beat)
        self._beater.start(int(_config.heartbeat_interval * 1000))

    @property
    def remote_address(self):
        return self._remote_address

    def _send_bytes(self, buffer):
        send_buffer = bytearray()
        send_buffer += _struct.pack('!I', len(buffer))
        send_buffer += buffer
        while len(send_buffer) > 0:
            written = self._tcp_socket.write(send_buffer)
            if written == -1:
                error = self._tcp_socket.errorString()
                self._disconnect(error)
                raise Connection.Failure(error)
            del send_buffer[:written]

    def send(self, message):
        buffer = _pickle.dumps(message)
        self._send_bytes(buffer)

    received = _QtCore.pyqtSignal(object)

    def _receive(self):
        buffer = self._tcp_socket.read(self._tcp_socket.bytesAvailable())
        self._receive_buffer += buffer
        while True:
            if len(self._receive_buffer) < 4:
                break
            size, = _struct.unpack('!I', self._receive_buffer[:4])
            if len(self._receive_buffer) < 4 + size:
                break
            buffer = self._receive_buffer[4:4 + size]
            del self._receive_buffer[:4 + size]
            if buffer != b'':
                message = _pickle.loads(buffer)
                self.received.emit(message)

    def _disconnect(self, reason):
        self.disconnected.emit(reason)
        self._tcp_socket.close()
        self._beater.stop()

    def disconnect(self):
        self._disconnect(None)

    disconnected = _QtCore.pyqtSignal(str)

    def _beat(self):
        try:
            self._send_bytes(b'')
        except Connection.Failure:
            pass
