from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import Qt, pyqtSlot
import sys
import xmltodict
from UDPHelper import UdpServer
from TCPHelper import TcpClient
from PyQt5.QtNetwork import QHostAddress

from LoggerHelper import getLoggerHandle
from configparser import ConfigParser
from SettingsHelper import SettingsWindow
from AboutHelper import AboutWindow
from qt_material import apply_stylesheet

ReadConfiguration = ConfigParser()
ReadConfiguration.read('config/Configuration.conf')

logger  = getLoggerHandle()

class Ui(QtWidgets.QMainWindow):
    Radio1Band = 0
    Radio2Band = 0
    BandMap = {}

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('./resources/AG_Bridge.ui', self)

        self.setWindowIcon(QtGui.QIcon('resources/icon.png'))

        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setFixedSize(260, 174)

        self.dialog = SettingsWindow(self)
        self.AboutDialog = AboutWindow(self)


        self.server = UdpServer(port=12060)
        self.server.dataReceived.connect(self.on_UDPdata_received)  # Connect the dataReceived signal to a custom slot

        self.client = TcpClient()
        self.client.connected.connect(self.on_connected)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.dataReceived.connect(self.on_data_received)
        self.client.errorOccurred.connect(self.on_error_occurred)



        self.Settings.pressed.connect(self.DoSettings)
        self.About.pressed.connect(self.DoAbout)

        logger.info (dict(ReadConfiguration['BAND_SET']))
        self.BandMap = dict(ReadConfiguration['BAND_SET'])

    @pyqtSlot()
    def on_connected(self):
        logger.info('Status: Connected')

    @pyqtSlot()
    def on_disconnected(self):
        logger.info('Status: Disconnected')

    @pyqtSlot(str)
    def on_data_received(self, data):
        logger.debug(data)

    @pyqtSlot(str)
    def on_error_occurred(self, error_message):
        logger.info(f"Error: {error_message}. Retrying...")

    def closeEvent(self, event):
        # Close the connection to the server before closing the window
        self.client.close()
        self.server.stop()

        event.accept()  # Accept the close event and close the window

    @pyqtSlot(str, QHostAddress, int)
    def on_UDPdata_received(self, data, sender, sender_port):
        self.UpdateUDP (data)




    def DXLogMakeTCP_payload(self, UdpDataDict):

        if (UdpDataDict['RadioInfo']['RadioNr'] == '1'):
            if (self.Radio1Band != self.ComputeBandNumber(int(UdpDataDict['RadioInfo']['Freq']))):
                logger.info ("Band: " + str(self.ComputeBandNumber(int(UdpDataDict['RadioInfo']['Freq']))) + " For Radio: " + UdpDataDict['RadioInfo']['RadioNr'] )
                self.Radio1Band = self.ComputeBandNumber(int(UdpDataDict['RadioInfo']['Freq']))
                TcpSendCommand = "C22|port set {} source=MANUAL band={}\n".format(UdpDataDict['RadioInfo']['RadioNr'], self.BandMap[str(self.ComputeBandNumber(int(UdpDataDict['RadioInfo']['Freq'])))])
                logger.debug (TcpSendCommand)
                self.client.send_data (TcpSendCommand)

        if (UdpDataDict['RadioInfo']['RadioNr'] == '2'):
            if (self.Radio2Band != self.ComputeBandNumber(int(UdpDataDict['RadioInfo']['Freq']))):
                logger.info ("Band: " + str(self.ComputeBandNumber(int(UdpDataDict['RadioInfo']['Freq']))) + " For Radio: " + UdpDataDict['RadioInfo']['RadioNr'] )
                self.Radio2Band = self.ComputeBandNumber(int(UdpDataDict['RadioInfo']['Freq']))
                TcpSendCommand = "C22|port set {} source=MANUAL band={}\n".format(UdpDataDict['RadioInfo']['RadioNr'], self.BandMap[str(self.ComputeBandNumber(int(UdpDataDict['RadioInfo']['Freq'])))])
                logger.debug (TcpSendCommand)
                self.client.send_data(TcpSendCommand)



    def UpdateUDP(self, udp_data):
        data = xmltodict.parse(udp_data)
        try:
            if data.get('RadioInfo') is not None:
                logger.debug("Received DXLog UDP Radio Info \n {}".format(data) )
                self.DXLogMakeTCP_payload(data)
        except:
            logger.critical("Received an unparsable package via UDP - dumping data: \n {}".format(data))
            pass


    def ComputeBandNumber (self, freq):
        band=0
        if freq in range(180000,200000):
            band = 160
        if freq in range(350000,380000):
            band = 80
        if freq in range(700000,720000):
            band = 40
        if freq in range(1400000,1435000):
            band = 20
        if freq in range(2100000,2145000):
            band = 15
        if freq in range(2800000,2970000):
            band = 10
        return band

    
    def DoSettings(self):
        self.dialog.show()

    def DoAbout(self):
        self.AboutDialog.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.client.connect()
    apply_stylesheet(app, theme='dark_BLUE.xml')
    window.show()
    sys.exit(app.exec_())

