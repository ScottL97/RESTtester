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
import base64
from urllib import parse
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QStringListModel, QThread, pyqtSignal
from MainWin import Ui_MainWindow


class HTTPServer(QThread):
    signal = pyqtSignal(list)

    def __init__(self, window, port):
        super().__init__()
        self.window = window
        self.hostname = socket.gethostname()
        self.address = socket.gethostbyname(self.hostname)
        # self.address = "127.0.0.1"
        self.port = port
        self.reqQueue = []

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
            print("[client]: ", client_address)
            self.handle_client(client_socket)
            # print("start to show")
            # 在界面显示请求列表
            self.signal.emit(self.reqQueue)

    def handle_client(self, cli_socket):
        request_data = cli_socket.recv(1024)
        # print(request_data)
        self.reqQueue.append(parse.unquote(request_data.decode('utf-8')))
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

    def clear_queue(self):
        self.reqQueue = []


class MainWin(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWin, self).__init__()
        self.setupUi(self)
        # 启动服务器
        self.server = HTTPServer(self, 8000)
        self.server.start_server()
        self.serverStatusLabel.setText(self.server.address + ":" + str(self.server.port) + "已连接！")
        self.urlLineEdit.setText('http://' + self.server.address + ":" + str(self.server.port))
        # 设置按钮点击事件
        self.sendButton.clicked.connect(self.send_rest)
        self.reqListView.clicked.connect(self.display_details)
        self.clearButton.clicked.connect(self.clear_requests)
        self.encodeButton.clicked.connect(self.start_encode)
        self.decodeButton.clicked.connect(self.start_decode)
        # 点击关闭按钮时释放服务器端口，结束服务器线程
        # 设置在请求列表中新增请求的信号处理函数
        self.server.signal.connect(self.display)

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
                res = requests.get(url, data, verify=False)
            else:
                res = requests.post(url, json=data, verify=False)
            if res.status_code == 200:
                self.resTextEdit.setText('200\n' + str(res.headers) + '\n' + res.text)
            else:
                self.resTextEdit.setText("Wrong HTTP response!\n\n" + res.text)
            res.close()
        except Exception as e:
            print(str(e))
            QMessageBox.warning(self, "连接错误", "URL无法连接，请检查")
            self.resTextEdit.setText(str(e))

    def display(self, queue):
        slm = QStringListModel()
        slm.setStringList(queue)
        self.reqListView.setModel(slm)
        self.clearButton.setText("清空列表（" + str(len(queue)) + "）")

    def display_details(self, index):
        QMessageBox.information(self, "REST Request", self.server.reqQueue[index.row()])

    def clear_requests(self):
        self.server.clear_queue()
        slm = QStringListModel()
        slm.setStringList([])
        self.reqListView.setModel(slm)
        self.clearButton.setText("清空列表")

    def start_encode(self):
        try:
            after_encode = base64.b64encode(bytes(self.decodeTextEdit.toPlainText(), 'utf-8'))
            self.encodeTextEdit.setText(str(after_encode, 'utf-8'))
        except Exception as e:
            print(e)

    def start_decode(self):
        try:
            after_decode = base64.b64decode(self.encodeTextEdit.toPlainText())
            self.decodeTextEdit.setText(str(after_decode, 'utf-8'))
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWin()
    win.show()
    sys.exit(app.exec_())
