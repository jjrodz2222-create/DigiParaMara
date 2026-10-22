#!/usr/bin/env python3
"""
DigiParaMara Core - Hardened Edge Event Loop & Invariant Verification
Repository: jjrodz2222-create/DigiParaMara
"""

import selectors
import socket
import hmac
import hashlib
import time

HOST = '127.0.0.1'
PORT = 8888
SECRET_KEY = b"digiparamara-secure-master-key"

class DigiParaMaraNode:
    def __init__(self, host=HOST, port=PORT):
        self.selector = selectors.DefaultSelector()
        self.host = host
        self.port = port
        self.nonce_cache = {}

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(100)
        server.setblocking(False)
        self.selector.register(server, selectors.EVENT_READ, self.accept)
        print(f"[*] DigiParaMara Core active on {self.host}:{self.port}")

        try:
            while True:
                events = self.selector.select(timeout=1.0)
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)
        except KeyboardInterrupt:
            print("\n[*] Shutting down DigiParaMara node.")
        finally:
            self.selector.close()

    def accept(self, sock, mask):
        conn, addr = sock.accept()
        conn.setblocking(False)
        self.selector.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        try:
            data = conn.recv(1024)
            if not data:
                self.selector.unregister(conn)
                conn.close()
                return

            if self.validate_payload(data):
                conn.sendall(b"ACK: STATE_INVARIANT_VERIFIED\n")
            else:
                conn.sendall(b"REJECT: INGRESS_VALIDATION_FAILED\n")
        except (ConnectionResetError, BlockingIOError):
            pass

    def validate_payload(self, payload: bytes) -> bool:
        if len(payload) < 56:
            return False

        received_hmac = payload[:32]
        timestamp = int.from_bytes(payload[32:40], 'big')
        nonce = payload[40:56]

        current_time = int(time.time())
        if abs(current_time - timestamp) > 30:
            return False

        nonce_key = (nonce, timestamp)
        if nonce_key in self.nonce_cache:
            return False

        self.nonce_cache = {k: v for k, v in self.nonce_cache.items() if current_time - v < 60}
        self.nonce_cache[nonce_key] = current_time

        computed_hmac = hmac.new(SECRET_KEY, payload[32:], hashlib.sha256).digest()
        return hmac.compare_digest(received_hmac, computed_hmac)

if __name__ == '__main__':
    node = DigiParaMaraNode()
    node.start_server()
