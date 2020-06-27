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
from urllib import parse
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QStringListModel
# from multiprocessing import Process, Pipe
from MainWin import Ui_MainWindow

reqQueue = []
addup = 1
beforeLen = 0


def handle_client(cli_socket):
    global reqQueue
    global addup

    print(addup)
    addup += 1
    request_data = cli_socket.recv(1024)
    reqQueue.append(parse.unquote(request_data.decode('utf-8')))
    print(reqQueue)
    # 构造响应数据
    response_start_line = "HTTP/1.1 200 OK\r\n"
    response_headers = "Server: test server\r\n"
    response_body = "<div>test body</div>"
    response = response_start_line + response_headers + "\r\n" + response_body
    # 向客户端返回响应数据
    cli_socket.send(bytes(response, "utf-8"))
    # 关闭客户端连接
    cli_socket.close()


class HTTPServer():
    def __init__(self, port):
        self.address = ""
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
            # handle_client_process = Process(target=handle_client, args=(client_socket,))
            handle_client_thread = HTTPHandlerThread(client_socket)
            # handle_client_process.start()
            handle_client_thread.start()


class MainWin(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWin, self).__init__()
        self.setupUi(self)
        self.server = HTTPServer(8000)
        self.server.start_server()
        self.serverStatusLabel.setText("localhost:" + str(self.server.port) + "已连接！")
        self.sendButton.clicked.connect(self.send_rest)
        self.reqListView.clicked.connect(self.display_details)
        self.clearButton.clicked.connect(self.clear_requests)
        self.start_display()

    def send_rest(self):
        method = self.methodComboBox.currentText()
        url = self.urlLineEdit.text()
        data = json.loads(self.reqTextEdit.toPlainText())
        if method == 'GET':
            res = requests.get(url, data)
        else:
            res = requests.post(url, json=data)
        if res.status_code == 200:
            self.resTextEdit.setText(res.text)
        else:
            self.resTextEdit.setText("Wrong HTTP response!")

    def start_display(self):
        display_thread = HTTPDisplayThread(self)
        display_thread.start()

    def display(self):
        global reqQueue
        global beforeLen

        while True:
            if len(reqQueue) > beforeLen:
                beforeLen = len(reqQueue)
                slm = QStringListModel()
                slm.setStringList(reqQueue)
                self.reqListView.setModel(slm)
            time.sleep(1)

    def display_details(self, index):
        QMessageBox.information(self, "QListView", reqQueue[index.row()])

    def clear_requests(self):
        global reqQueue
        global beforeLen

        reqQueue = []
        slm = QStringListModel()
        slm.setStringList(reqQueue)
        self.reqListView.setModel(slm)
        beforeLen = 0


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


class HTTPDisplayThread(threading.Thread):
    def __init__(self, window):
        threading.Thread.__init__(self)
        self.window = window

    def run(self):
        self.window.display()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWin()
    win.show()
    sys.exit(app.exec_())
