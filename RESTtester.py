#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File  : RESTtester.py.py
@Author: Scott
@Date  : 2020/6/27 16:02
@Desc  :
"""

import requests
import threading
import socket
import sys
import json
import time
import base64
from urllib import parse
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QStringListModel, QThread, pyqtSignal
from MainWin import Ui_MainWindow

reqQueue = []
addUp = 0
beforeLen = 0


def handle_client(cli_socket):
    global reqQueue
    global addUp

    addUp += 1
    # print(addup)
    request_data = cli_socket.recv(1024)
    reqQueue.append(parse.unquote(request_data.decode('utf-8')))
    # print(reqQueue)
    # 构造响应数据
    response_start_line = "HTTP/1.1 200 OK\r\n"
    response_headers = "Server: test server\r\n"
    response_body = "<div>test body</div>"
    response = response_start_line + response_headers + "\r\n" + response_body
    # 向客户端返回响应数据
    cli_socket.send(bytes(response, "utf-8"))
    # 关闭客户端连接
    cli_socket.close()


class HTTPServer:
    def __init__(self, port):
        self.hostname = socket.gethostname()
        self.address = socket.gethostbyname(self.hostname)
        self.port = port

    def start_server(self):
        server_thread = HTTPServerThread(self)
        server_thread.start()

    def run_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.address, self.port))
        server_socket.listen(128)
        print("----------------------------------------")

        while True:
            client_socket, client_address = server_socket.accept()
            print("client: [%s:%s]" % client_address)
            handle_client_thread = HTTPHandlerThread(client_socket)
            handle_client_thread.start()


class MainWin(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWin, self).__init__()
        self.thread = HTTPDisplayThread()
        self.setupUi(self)
        self.server = HTTPServer(8000)
        self.server.start_server()
        self.serverStatusLabel.setText(self.server.address + ":" + str(self.server.port) + "已连接！")
        self.urlLineEdit.setText('http://' + self.server.address + ":" + str(self.server.port))
        self.sendButton.clicked.connect(self.send_rest)
        self.reqListView.clicked.connect(self.display_details)
        self.clearButton.clicked.connect(self.clear_requests)
        self.encodeButton.clicked.connect(self.start_encode)
        self.decodeButton.clicked.connect(self.start_decode)
        self.start_display()

    def send_rest(self):
        method = self.methodComboBox.currentText()
        url = self.urlLineEdit.text().strip()
        data = ''
        try:
            if len(self.reqTextEdit.toPlainText()) != 0:
                data = json.loads(self.reqTextEdit.toPlainText())
        except Exception as e:
            print(e)
            self.resTextEdit.setText(str(e))

        if (len(self.reqTextEdit.toPlainText()) != 0) & (data == ''):
            print('json loads failed: ' + self.reqTextEdit.toPlainText())
            return 1

        if (data != '') & (not isinstance(data, dict)):
            print('data is not a json: ' + str(data))
            self.resTextEdit.setText('data is not a json: ' + str(data))
            return 1

        try:
            if method == 'GET':
                res = requests.get(url, data)
            else:
                res = requests.post(url, json=data)
            if res.status_code == 200:
                self.resTextEdit.setText('200\n' + str(res.headers) + '\n' + res.text)
            else:
                self.resTextEdit.setText("Wrong HTTP response!\n\n" + res.text)
            res.close()
        except Exception as e:
            print(str(e))
            QMessageBox.warning(self, "连接错误", "URL无法连接，请检查")
            self.resTextEdit.setText(str(e))

    def start_display(self):
        self.thread.signal.connect(self.display)
        self.thread.start()

    def display(self):
        global reqQueue
        global beforeLen
        global addUp

        if addUp > beforeLen:
            beforeLen = addUp
            slm = QStringListModel()
            slm.setStringList(reqQueue)
            self.reqListView.setModel(slm)
            self.clearButton.setText("清空列表（" + str(addUp) + "）")

    def display_details(self, index):
        QMessageBox.information(self, "REST Request", reqQueue[index.row()])

    def clear_requests(self):
        global reqQueue
        global beforeLen
        global addUp

        reqQueue = []
        slm = QStringListModel()
        slm.setStringList(reqQueue)
        self.reqListView.setModel(slm)
        self.clearButton.setText("清空列表")
        beforeLen = 0
        addUp = 0

    def start_encode(self):
        try:
            afterEncode = base64.b64encode(bytes(self.decodeTextEdit.toPlainText(), 'utf-8'))
            self.encodeTextEdit.setText(str(afterEncode, 'utf-8'))
        except Exception as e:
            print(e)

    def start_decode(self):
        try:
            afterDecode = base64.b64decode(self.encodeTextEdit.toPlainText())
            self.decodeTextEdit.setText(str(afterDecode, 'utf-8'))
        except Exception as e:
            print(e)


class HTTPServerThread(threading.Thread):
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server

    def run(self):
        print("HTTP Server starting: " + self.server.address + ":" + str(self.server.port))
        self.server.run_server()
        print("HTTP Server stopped.")


class HTTPHandlerThread(threading.Thread):
    def __init__(self, client_socket):
        threading.Thread.__init__(self)
        self.client_socket = client_socket

    def run(self):
        print("Start client socket handler...")
        handle_client(self.client_socket)
        print("Client socket handler finished.")


class HTTPDisplayThread(QThread):
    signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            self.signal.emit()
            time.sleep(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWin()
    win.show()
    sys.exit(app.exec_())
