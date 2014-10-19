import pickle as _pickle
import struct as _struct

import PyQt4.QtCore as _QtCore
import PyQt4.QtNetwork as _QtNetwork

from config import config as _config


class Connection(_QtCore.QObject):
    class Failure(Exception):
        pass

    class Awaiter(_QtCore.QObject):
        def __init__(self, Connection):
            super().__init__()

            self.__Connection = Connection

            self.__tcp_server = _QtNetwork.QTcpServer()
            self.__tcp_server.newConnection.connect(self.__new_connection)
            self.__tcp_server.listen(_QtNetwork.QHostAddress.Any, _config['connection-port'])

        connected = _QtCore.pyqtSignal(_QtCore.QObject)  # actually Connection but python can't

        def __new_connection(self):
            while self.__tcp_server.hasPendingConnections():
                tcp_socket = self.__tcp_server.nextPendingConnection()
                connection = self.__Connection(tcp_socket=tcp_socket)
                self.connected.emit(connection)

    @classmethod
    def spawn_awaiter(cls):
        return Connection.Awaiter(cls)

    def __init__(self, address=None, tcp_socket=None):
        assert (address is None) != (tcp_socket is None)

        super().__init__()

        if tcp_socket is None:
            tcp_socket = _QtNetwork.QTcpSocket()
            tcp_socket.connectToHost(address, _config['connection-port'])
            if not tcp_socket.waitForConnected(int(_config['connection-timeout'] * 1000)):
                raise Connection.Failure(tcp_socket.errorString())

        self.__tcp_socket = tcp_socket
        self.__tcp_socket.readyRead.connect(self.__receive)
        self.__remote_address = self.__tcp_socket.peerAddress().toString()

        self.__receive_buffer = bytearray()

        self.__beater = _QtCore.QTimer()
        self.__beater.timeout.connect(self.__beat)
        self.__beater.start(int(_config['heartbeat-interval'] * 1000))

        self.received.connect(self._on_received)
        self.disconnected.connect(self._on_disconnected)

    @property
    def remote_address(self):
        return self.__remote_address

    def __send_bytes(self, buffer):
        send_buffer = bytearray()
        send_buffer += _struct.pack('!I', len(buffer))
        send_buffer += buffer
        while len(send_buffer) > 0:
            written = self.__tcp_socket.write(send_buffer)
            if written == -1:
                error = self.__tcp_socket.errorString()
                self.__disconnect(error)
                raise Connection.Failure(error)
            self.__tcp_socket.flush()
            self.__tcp_socket.waitForBytesWritten(int(_config['connection-timeout'] * 1000))
            del send_buffer[:written]

    def send(self, message):
        buffer = _pickle.dumps(message)
        self.__send_bytes(buffer)

    def _on_received(self, message):
        pass

    received = _QtCore.pyqtSignal(object)

    def __receive(self):
        buffer = self.__tcp_socket.read(self.__tcp_socket.bytesAvailable())
        self.__receive_buffer += buffer
        while True:
            if len(self.__receive_buffer) < 4:
                break
            size, = _struct.unpack('!I', self.__receive_buffer[:4])
            if len(self.__receive_buffer) < 4 + size:
                break
            buffer = self.__receive_buffer[4:4 + size]
            del self.__receive_buffer[:4 + size]
            if buffer != b'':
                message = _pickle.loads(buffer)
                self.received.emit(message)

    def _on_disconnected(self, reason):
        pass

    disconnected = _QtCore.pyqtSignal(str)

    def __disconnect(self, reason):
        self.disconnected.emit(reason)
        self.__tcp_socket.close()
        self.__beater.stop()

    def disconnect(self):
        self.__disconnect(None)

    def __beat(self):
        try:
            self.__send_bytes(b'')
        except Connection.Failure:
            pass
