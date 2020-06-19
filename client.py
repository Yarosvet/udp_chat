#!/usr/bin/env python
import socket
import sys
import pathlib
from pickle import loads, dumps
import rsa
from ui import Ui_Window
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QTimer


def encrypt(bytes_list, public_key, piece=117):
    l = len(bytes_list)
    k = l // piece
    last = bytes_list[k * piece:]
    return [rsa.encrypt(bytes_list[piece * i:piece * (i + 1)], public_key) for i in range(k)] + [
        rsa.encrypt(last, public_key)]


def decrypt(crypted_list, privkey):
    res = bytes()
    for el in crypted_list:
        res += rsa.decrypt(el, privkey)
    return res


class Backend:
    def __init__(self, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind(('', port))  # Binding port
        self.s.listen(1)

        self.conn = 0
        self.message_id = 0
        self.temporary = {}
        self.connected = False

        (self.pubkey, self.privkey) = rsa.newkeys(1024)
        self.connect_pubkey = None
        self.port = port
        self.connect_address = ()

    def file_sender(self, fname):
        if fname != '':
            f = open(fname, 'rb')
            data = f.read()
            f.close()
            encrypted = encrypt(dumps({'file': data, 'file_name': pathlib.Path(fname).name}),
                                self.connect_pubkey)

            self.send_request({'type': 'file', 'data': encrypted})
            self.message_id += 1
            return 'Me >  [File ' + fname + ']'

    def exchange_keys(self):
        self.send_request({'type': 'connect', 'data': {'pubkey': self.pubkey}})

    def change_socket(self, port: int):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind(('', port))  # Binding port
        self.s.listen(1)

    def send_request(self, request):
        pieces = 5
        request['ip'] = self.send_address[0]
        request['request_id'] = self.message_id
        data = request['data']
        cnt = len(data) // pieces
        if len(data) % pieces != 0:
            cnt += 1
        request['count_of_packets'] = cnt
        for i in range(cnt):
            packet = request
            packet['packet_number'] = i + 1
            packet['data'] = data[pieces * i: pieces * (i + 1)]
            self.s.send(dumps(packet))

    def connect(self, ip):
        if not self.connected:
            try:
                self.connected = True
                self.connect_address = (ip, self.port)
                self.s.connect(self.connect_address)
                self.exchange_keys()
                return 0
            except Exception as exc:
                self.connect_address = ()
                # QMessageBox.critical(self, str(type(exc))[8:-2], 'Connection failed\n\n' + str(exc), QMessageBox.Ok)
                self.connected = False
                self.unlock_ui()
                return 'Connection failed\n\n' + str(exc)
        else:
            self.s.close()
            self.connected = False
            self.connect(ip=ip)

    def message_handler(self, request, address):
        if request['type'] == 'message':
            request_id = request['request_id']
            if address[0] not in self.temporary.keys():
                self.temporary[address[0]] = {}
            if request['request_id'] not in self.temporary[address[0]]:
                self.temporary[address[0]][request_id] = {}
            try:
                maximum = max(self.temporary[address[0]][request_id].keys()) + 1
            except ValueError:
                maximum = 0
            self.temporary[address[0]][request_id][maximum] = request['data']
            if len(self.temporary[address[0]][request_id].keys()) == request['count_of_packets']:
                data = []
                for el in self.temporary[address[0]][request_id].values():
                    data += el
                del self.temporary[address[0]][request_id]
                data = loads(decrypt(data, self.privkey))
                self.temporary[address[0]][request['request_id']] = []
                text = data['text']
                # self.ui.plainText.appendPlainText(address[0] + ':' + str(address[1]) + ' >  ' + text)
                return address[0] + ':' + str(address[1]) + ' >  ' + text

        elif request['type'] == 'connect':
            self.connect_pubkey = request['data']['pubkey']

        elif request['type'] == 'file':
            request_id = request['request_id']
            if address[0] not in self.temporary.keys():
                self.temporary[address[0]] = {}
            if request['request_id'] not in self.temporary[address[0]]:
                self.temporary[address[0]][request_id] = {}
            try:
                maximum = max(self.temporary[address[0]][request_id].keys()) + 1
            except ValueError:
                maximum = 0
            self.temporary[address[0]][request_id][maximum] = request['data']
            if len(self.temporary[address[0]][request_id].keys()) == request['count_of_packets']:
                data = []
                for el in self.temporary[address[0]][request_id].values():
                    data += el
                del self.temporary[address[0]][request_id]
                decrypted = loads(decrypt(data, self.privkey))

                fname = QFileDialog.getSaveFileName(self, 'Сохранить файл ' + decrypted['file_name'])[0]
                if fname != '':
                    f = open(fname, 'wb')
                    f.write(decrypted['file'])
                    f.close()
                    self.ui.plainText.appendPlainText(address[0] + ':' + address[1] + ' >  [File ' + fname + ']')

    def reciever(self):
        try:
            if not self.connected:
                self.conn, self.connect_address = self.s.accept()
            else:
                print(self.conn)

                message = self.conn.recv(1024)
                self.message_handler(loads(message), self.connect_address)
        except BlockingIOError:
            pass

    def send_message(self, text):
        if text != '':
            encrypted = encrypt(dumps({'text': text}), self.connect_pubkey)
            request = {'type': 'message', 'data': encrypted}
            self.send_request(request)  # sending text
            self.message_id += 1
            return 'Me >  ' + text


class Window(QMainWindow):
    def __init__(self):
        # Инициализация
        super().__init__()
        self.ui = Ui_Window()
        self.ui.setupUi(self)

        self.engine = Backend(port=int(self.ui.port.text()))

        timer = QTimer(self)
        timer.setInterval(50)
        timer.timeout.connect(self.engine.reciever)
        timer.start()

        self.ui.pushButton.clicked.connect(self.send_message)
        self.ui.pushButton_2.clicked.connect(self.change_socket)
        self.ui.pushButton_3.clicked.connect(self.connect)
        self.ui.send_file.clicked.connect(self.send_file)
        self.ui.label_2.setText('Now your IP seems to be  ' + socket.gethostbyname(socket.getfqdn()))

    def send_message(self):
        text = self.engine.send_message(self.ui.lineEdit.text())
        self.ui.plainText.appendPlainText(text)
        self.ui.lineEdit.setText('')

    def send_file(self):
        text = self.engine.file_sender(QFileDialog.getOpenFileName(self, 'Выбрать файл', '')[0])
        self.ui.plainText.appendPlainText(text)

    def connect(self):
        self.engine.connect(self.ui.reciever_ip.text())

    def change_socket(self):
        self.engine.change_socket(self.ui.port.text())

    def lock_ui(self):
        self.ui.port.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.send_file.setEnabled(True)
        self.ui.pushButton.setEnabled(True)
        self.ui.pushButton_3.setText('DISCONNECT')

    def unlock_ui(self):
        self.ui.port.setEnabled(True)
        self.ui.pushButton_2.setEnabled(True)
        self.ui.send_file.setEnabled(False)
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_3.setText('CONNECT')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter - 1 and self.ui.reciever_ip.text().count(
                '.') == 3 and self.ui.pushButton.isEnabled():
            self.send_message()


app = QApplication(sys.argv)
ex = Window()
ex.show()
sys.exit(app.exec_())
