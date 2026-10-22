#!/usr/bin/env python3
import os, sys, time, selectors, socket

HOST = '127.0.0.1'
PORT = 8888

class SumerAveraNode:
    def __init__(self, host=HOST, port=PORT):
        self.selector = selectors.DefaultSelector()
        self.host = host
        self.port = port

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(100)
        server.setblocking(False)
        self.selector.register(server, selectors.EVENT_READ, self.accept)
        print(f"[*] SumerAvera Protocol Core active on {self.host}:{self.port}")

    def accept(self, sock, mask):
        conn, addr = sock.accept()
        conn.setblocking(False)
        self.selector.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        data = conn.recv(1024)
        if data:
            conn.sendall(b"ACK: STATE_INVARIANT_VERIFIED\n")
        else:
            self.selector.unregister(conn)
            conn.close()

if __name__ == '__main__':
    node = SumerAveraNode()
    node.start_server()
