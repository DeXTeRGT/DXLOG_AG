from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QUdpSocket, QHostAddress


from LoggerHelper import getLoggerHandle
from configparser import ConfigParser

ReadConfiguration = ConfigParser()
ReadConfiguration.read('config/Configuration.conf')

logger  = getLoggerHandle()


class UdpServer(QObject):
    dataReceived = pyqtSignal(str, QHostAddress, int)  # Signal to emit received data along with sender's address and port

    def __init__(self, port=int(ReadConfiguration['UDP_SERVER']['udp_listen_port'])):
        super().__init__()
        self.socket = QUdpSocket(self)  # Create a QUdpSocket instance
        self.socket.bind(QHostAddress(ReadConfiguration['UDP_SERVER']['udp_listen_if']), port)  # Bind the socket to any address and specified port
        self.socket.readyRead.connect(self.on_ready_read)  # Connect the readyRead signal to the slot
        logger.info ('UDP Server is started and listening @ {} port {} '.format(ReadConfiguration['UDP_SERVER']['udp_listen_if'], ReadConfiguration['UDP_SERVER']['udp_listen_port']))
        
    @pyqtSlot()
    def on_ready_read(self):
        # Loop to read all available datagrams
        while self.socket.hasPendingDatagrams():
            datagram = self.socket.receiveDatagram()
            data = datagram.data()  # Get the data as QByteArray
            decoded_data = data.data().decode('utf-8')
            sender = datagram.senderAddress()
            sender_port = datagram.senderPort()
            self.dataReceived.emit(decoded_data, sender, sender_port)  # Emit the received data, sender address, and port

    def send_data(self, data, address, port):
        # Send data to a specified address and port
        self.socket.writeDatagram(data.encode('utf-8'), QHostAddress(address), port)

    def stop(self):
        # Gracefully stop the server
        self.socket.close()
        #self.errorOccurred.emit("Server stopped")