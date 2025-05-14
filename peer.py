import socket
import threading
import os
import json
import pyaudio
from queue import Queue
import time

# Constants
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
VOIP_OFFSET = 10  # offset from base UDP port for audio
CALL_OFFSET = 2   # offset for call signaling

HOST="10.200.250.141"
TRACKER_IP = '127.0.0.1'   #put the tracker ip here
TRACKER_PORT = 6000       #put the tracker port here
PEER_PORT = 7000 + os.getpid() % 1000  # Unique port per peer
PEER_ID = f'peer-{PEER_PORT}'

shared_folder = 'shared'
received_folder = 'received'
peers = {}
incoming_calls = Queue()

# Ensure directories exist
os.makedirs(shared_folder, exist_ok=True)
os.makedirs(received_folder, exist_ok=True)

# === CALL SIGNALLING LISTENER ===
def call_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', PEER_PORT + CALL_OFFSET))
    print(f"[CALL LISTENER] Listening on UDP {PEER_PORT + CALL_OFFSET}")
    while True:
        msg, addr = sock.recvfrom(1024)
        decoded = msg.decode(errors='ignore')
        if decoded.startswith("CALL_REQUEST:"):
            parts = decoded.split(':')
            from_id = parts[1]
            from_voip_port = int(parts[2]) if len(parts) > 2 else (peers.get(from_id, (None, 0))[1] + VOIP_OFFSET)
            print(f"\n[!] Incoming call from {from_id}. Respond from main menu.")
            incoming_calls.put((from_id, addr[0], from_voip_port, addr[1]))
            print('callee-side', from_id, addr[0], from_voip_port, addr[1])


def start_call(peer_id, passive=False, signal_addr=None, existing_sock=None):
    if peer_id not in peers and not passive:
        print("[ERROR] Peer not found.")
        return

    stop_event = threading.Event()

    if existing_sock:
        local_voip_sock = existing_sock
    else:
        local_voip_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_voip_sock.bind(('', 0))
        local_voip_port = local_voip_sock.getsockname()[1]

    if not passive:
        peer_ip, peer_base_port = peers[peer_id]
        signaling_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        signaling_sock.settimeout(10)
        signaling_sock.sendto(
            f"CALL_REQUEST:{PEER_ID}:{local_voip_port}".encode(),
            (peer_ip, peer_base_port + CALL_OFFSET)
        )
        try:
            reply, addr = signaling_sock.recvfrom(1024)
            decoded = reply.decode()
            if not decoded.startswith("CALL_ACCEPT:"):
                print("[CALL DECLINED]")
                return
        except socket.timeout:
            print("[CALL TIMEOUT]")
            return
        signaling_sock.close()
        callee_voip_port = int(decoded.split(':')[1])
        voip_addr = (peer_ip, callee_voip_port)
    else:
        if signal_addr:
            voip_addr = signal_addr
        else:
            print("[ERROR] No signal address provided for passive call.")
            return

    try:
        audio = pyaudio.PyAudio()
        stream_in = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                               input=True, frames_per_buffer=CHUNK)
        stream_out = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                output=True, frames_per_buffer=CHUNK)
    except Exception as e:
        print("[AUDIO ERROR]", e)
        return

    def send_voice():
        try:
            while not stop_event.is_set():
                data = stream_in.read(CHUNK, exception_on_overflow=False)
                local_voip_sock.sendto(data, voip_addr)
        except Exception as e:
            print("[SEND ERROR]", e)

    def recv_voice():
        try:
            while not stop_event.is_set():
                data, _ = local_voip_sock.recvfrom(2048)
                if data == b'END_CALL':
                    print("[CALL ENDED BY PEER]\nPress ENTER to return to MAIN MENU.")
                    stop_event.set()
                    break
                stream_out.write(data)
        except Exception as e:
            print("[RECV ERROR]", e)

    send_thread = threading.Thread(target=send_voice, daemon=True)
    recv_thread = threading.Thread(target=recv_voice, daemon=True)
    send_thread.start()
    recv_thread.start()

    print(f"[VOICE CHAT ACTIVE] Connected to {peer_id} at {voip_addr}. Press Enter to hang up.")
    input()
    stop_event.set()

    # Notify peer to hang up
    try:
        local_voip_sock.sendto(b'END_CALL', voip_addr)
    except:
        pass

    time.sleep(0.5)

    try:
        stream_in.stop_stream()
        stream_out.stop_stream()
        stream_in.close()
        stream_out.close()
        audio.terminate()
        local_voip_sock.close()
        print("[CALL ENDED]")
    except Exception as e:
        print("[CLEANUP ERROR]", e)




# === TRACKER REGISTRATION ===
def register_with_tracker():
    global tracker_socket
    tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #tracker_socket.bind((HOST, 1237))
    tracker_socket.connect((TRACKER_IP, TRACKER_PORT))
    peer_info = {"peer_id": PEER_ID, "port": PEER_PORT}
    tracker_socket.send(json.dumps(peer_info).encode())
    print(f"[REGISTERED] as {PEER_ID}")

# === PEER LIST UPDATES ===
def listen_for_updates():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PEER_PORT + 1))
    server.listen()
    print(f"[UPDATE LISTENER] Running on {PEER_PORT + 1}")
    while True:
        conn, _ = server.accept()
        data = conn.recv(4096).decode()
        global peers
        peers = json.loads(data)
        peers.pop(PEER_ID, None)
        print(f"[PEER LIST UPDATED] {json.dumps(peers, indent=2)}")

# === UDP FILE SHARING (unchanged) ===
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', PEER_PORT))
    print(f"[UDP LISTENER] Listening on {PEER_PORT}")
    while True:
        msg, addr = sock.recvfrom(4096)
        # ... existing file-sharing logic ...
        pass

# === RUN PEER ===
def run_peer():
    register_with_tracker()
    threading.Thread(target=listen_for_updates, daemon=True).start()
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=call_listener, daemon=True).start()

    while True:
        # Handle incoming calls
        while not incoming_calls.empty():
            from_id, from_ip, from_voip_port, from_call_port = incoming_calls.get()
            print(from_id, from_ip, from_voip_port)
            response = input(f"Accept call from {from_id}? (y/n): ").strip().lower()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            signaling_addr = (from_ip, from_call_port)
            if response == 'y':
                # Start VoIP socket and get actual port before replying
                local_voip_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                local_voip_sock.bind(('', 0))
                local_voip_port = local_voip_sock.getsockname()[1]

                # Send CALL_ACCEPT with port
                sock.sendto(f"CALL_ACCEPT:{local_voip_port}".encode(), signaling_addr)

                # Then pass this socket to start_call
                # start_call(from_id, passive=True, signal_addr=(from_ip, peers[from_id][1] + VOIP_OFFSET), existing_sock=local_voip_sock)

                start_call(from_id, passive=True, signal_addr=(from_ip, from_voip_port), existing_sock=local_voip_sock)
            else:
                sock.sendto(b"CALL_DECLINE", signaling_addr)
            sock.close()


        cmd = input("\n1. List Peers\n2. Request File\n3. Start Call\n4. Exit\nChoose: ").strip()
        if cmd == '1':
            print(json.dumps(peers, indent=2))
        elif cmd == '2':
            fname = input("Enter filename: ").strip()
            request_file(fname)
        elif cmd == '3':
            pid = input("Enter peer ID to call: ").strip()
            start_call(pid)
        elif cmd == '4':
            break


if __name__ == '__main__':
    run_peer()
