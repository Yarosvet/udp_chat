import socket
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QErrorMessage
from Crypto.Cipher import DES


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('client.ui', self)
        self.localIP = socket.gethostbyname(socket.getfqdn())
        self.pushButton.clicked.connect(self.run)
        self.lineEdit_9.setText(self.localIP)
        self.localPort = 20001
        self.bufferSize = 1024
        self.UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.UDPServerSocket.bind((self.localIP, self.localPort))

    def pad(self, text):
        if not isinstance(bytes, text):
            text = text.encode('utf-8')
            print('1')
        while len(text) % 8 != 0:
            text += b' '
        return text

    def encrypt(self, text, key):
        key = self.pad(key)
        des = DES.new(key, DES.MODE_ECB)
        text = self.pad(text)
        print(text)
        return des.encrypt(text)

    def run(self):
        global UDPServerSocket
        text = self.encrypt(self.lineEdit.text(), self.lineEdit_7.text())
        ip = self.lineEdit_4.text()
        port = self.lineEdit_6.text()
        data = self.encrypt(text, self.lineEdit_7.text())
        data = data.decode('utf-8')
        print(data)
        UDPServerSocket.sendto(data, [ip, port])
        print('sent')
        # except Exception:
        #     print(0)
        #     error_dialog = QErrorMessage()
        #     error_dialog.showMessage('Error. Check the fields.')


def decrypt(text, key):
    try:
        des = DES.new(key, DES.MODE_ECB)
        return des.decrypt(text).decode('utf-8')
    except Exception:
        return 'PYTHON EXCEPTION!!!'


def show_message(text, key):
    pass  # доделать


# def answerer():
#     bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
#     message = bytesAddressPair[0]
#     address = bytesAddressPair[1]
#     print(clientMsg)
#     UDPServerSocket.sendto(bytesToSend, address)


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
sys.exit(app.exec_())
