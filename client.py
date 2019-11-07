#!/usr/bin/env python
import socket
import sys, select
import time
import threading
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QErrorMessage


class StoppableThread(threading.Thread):
    #  Thread class with a stop() method.
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('client.ui', self)
        self.localIP = socket.gethostbyname(socket.getfqdn())
        self.pushButton.clicked.connect(self.run)
        self.lineEdit_9.setText(self.localIP)
        host = self.lineEdit_4
        port = int(self.lineEdit_6.text())

        self.send_address = (host, port)  # Set the address to send to
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create Socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make Socket Reusable
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Allow incoming broadcasts
        self.s.setblocking(False)  # Socket non-block
        self.s.bind(('', port))  # Binding port

    # def main(self):
    #     while True:
    #         time.sleep(1)
    #         try:
    #             message, address = self.s.recvfrom(1024)  # Buffer size
    #             if message:
    #                 self.show(address + " >  " + message)  # Show this message
    #         except:
    #             pass

    def run(self):
        input = self.lineEdit.text()
        if (input != ''):
            self.s.sendto(input, self.send_address)
            self.show('Me >  ' + input)

    def show(self, text):
        self.textBrowser.setText(self.textBrowser.setText() + '\n' + text)

app = QApplication(sys.argv)
ex = MyWidget()

def main():
    global ex
    while True:
        time.sleep(1)
        try:
            message, address = ex.s.recvfrom(1024)  # Buffer size
            if message:
                ex.show(address + " >  " + message)  # Show this message
        except:
            pass

thr = threading.Thread(main)
ex.show()
sys.exit(app.exec_())
