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
import os

HOST = '127.0.0.1'
PORT = 8888
SECRET_KEY = os.environ.get("SUMER_SECRET_ZERO_DRIFT", "digiparamara-secure-master-key").encode('utf-8')

class DigiParaMaraNode:
    def __init__(self, host=HOST, port=PORT):
        self.selector = selectors.DefaultSelector()
        self.host = host
        self.port = port
        self.nonce_cache = {}
        self.buffers = {}

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
        self.buffers[conn] = bytearray()
        self.selector.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        try:
            chunk = conn.recv(1024)
            if not chunk:
                self.close_connection(conn)
                return

            self.buffers[conn].extend(chunk)
           
            while len(self.buffers[conn]) >= 56:
                packet = bytes(self.buffers[conn][:56])
                del self.buffers[conn][:56]

                if self.validate_payload(packet):
                    conn.sendall(b"ACK: AUTHENTICATED_FRESHNESS_VERIFIED\n")
                else:
                    conn.sendall(b"REJECT: INGRESS_VALIDATION_FAILED\n")
                   
        except (ConnectionResetError, BrokenPipeError, BlockingIOError):
            self.close_connection(conn)

    def close_connection(self, conn):
        try:
            self.selector.unregister(conn)
        except Exception:
            pass
        if conn in self.buffers:
            del self.buffers[conn]
        conn.close()

    def validate_payload(self, payload: bytes) -> bool:
        if len(payload) != 56:
            return False

        received_hmac = payload[:32]
        body = payload[32:]

        expected = hmac.new(SECRET_KEY, body, hashlib.sha256).digest()
        if not hmac.compare_digest(received_hmac, expected):
            return False

        timestamp = int.from_bytes(body[:8], 'big')
        nonce = body[8:]

        now = int(time.time())
        if abs(now - timestamp) > 30:
            return False

        self.nonce_cache = {k: v for k, v in self.nonce_cache.items() if now - v < 60}
        nonce_key = (bytes(nonce), timestamp)
        if nonce_key in self.nonce_cache:
            return False

        self.nonce_cache[nonce_key] = now
        return True

if __name__ == '__main__':
    node = DigiParaMaraNode()
    node.start_server()
