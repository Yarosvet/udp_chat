#!/usr/bin/env python
import socket
import sys, select
import time
import threading
# from simple_thread import SimpleThread
from PyQt5 import uic
import sqlite3
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QErrorMessage


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('client.ui', self)
        self.localIP = socket.gethostbyname(socket.getfqdn())
        self.pushButton.clicked.connect(self.run)
        self.pushButton_2.clicked.connect(self.change_socket)
        self.lineEdit_9.setText(self.localIP)

        self.con = sqlite3.connect("messages.db")
        self.cur = self.con.cursor()

        host = self.lineEdit_4.text()
        port = int(self.lineEdit_6.text())

        self.send_address = (host, port)  # Set the address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create Socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make Socket Reusable
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Allow incoming broadcasts
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind(('', port))  # Binding port
        self.text_on_browser = ''
        thr = threading.Thread(target=self.main)
        thr.start()
        # self.thr = QThread()
        # self.thr.started.connect(self.main)
        # self.thr.thread(self)
        # self.thr.start()
        # self.main(thr_start=True)

    def change_socket(self):
        host = self.lineEdit_4.text()
        port = int(self.lineEdit_6.text())
        self.send_address = (host, port)  # Set the address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create Socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make Socket Reusable
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Allow incoming broadcasts
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind((self.lineEdit_9.text(), port))

    def main(self):
        while True:
            try:
                time.sleep(0.1)
                message, address = self.s.recvfrom(1024)  # Buffer size
                message = message.decode('utf-8')
                self.plainText.appendPlainText(f'{address[0]}:{address[1]} >  {message}')
                self.log_db(address, self.send_address[1], message)
            except:
                pass

    def run(self):
        self.send_address = (self.lineEdit_4.text(), int(self.lineEdit_6.text()))
        input = str(self.lineEdit.text())
        if (input != ''):
            self.s.sendto(bytes(input, 'utf-8'), self.send_address)  # sending text
            self.plainText.appendPlainText('Me >  ' + input)  # Show this message
            self.log_db(self.lineEdit_9.text() + ' (Me)', self.send_address[1], input)

    def log_db(self, ip, port, message):
        self.cur.execute(f"INSERT INTO messages(Ip, Port, Text) VALUES(\'{ip}\', {port}, \'{message}\')")
        self.con.commit()


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
sys.exit(app.exec_())
