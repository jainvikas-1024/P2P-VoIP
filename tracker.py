import socket
import threading
import time
import json

active_peers = {}  # {peer_id: (ip, port)}
lock = threading.Lock()
TRACKER_PORT = 6000
PING_INTERVAL = 10

def handle_peer(conn, addr):
    global active_peers
    data = conn.recv(1024).decode()
    peer_info = json.loads(data)
    peer_id = peer_info["peer_id"]
    peer_port = peer_info["port"]
    peer_ip = addr[0]  # use the IP from the TCP connection

    with lock:
        active_peers[peer_id] = (peer_ip, peer_port)
        print(f"[NEW PEER] {peer_id} at {peer_ip}:{peer_port}")
    broadcast_peer_list()
    try:
        while True:
            msg = conn.recv(1024)
            if not msg:
                # print(msg)
                break
    except:
        pass
    finally:
        with lock:
            if peer_id in active_peers:
                del active_peers[peer_id]
                print(f"[LEAVE] {peer_id} removed")
        broadcast_peer_list()

def broadcast_peer_list():
    peer_list = json.dumps(active_peers)
    for peer_id, (ip, port) in list(active_peers.items()):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port + 1))  # Listening port for updates MAJOR UPDATE
                s.sendall(peer_list.encode())
        except:
            continue

def start_tracker():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', TRACKER_PORT))
    server.listen()
    print(f"[TRACKER] Running on port {TRACKER_PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_peer, args=(conn, addr)).start()

if __name__ == "__main__":
    start_tracker()