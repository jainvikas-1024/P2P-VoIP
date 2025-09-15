# Peer-to-Peer VoIP Platform

This project is a lightweight, decentralized peer-to-peer (P2P) platform that enables real-time voice over IP (VoIP) calls between users. It is built using Python's native socket programming and threading capabilities, emphasizing simplicity and a minimal footprint.

## Abstract

This platform allows users to connect and communicate directly without relying on centralized servers for media transmission. A simple tracker server handles peer registration and discovery. The system is designed to be a practical demonstration of P2P networking principles, socket programming, and real-time audio communication.

## Features

* **Peer Registration:** Peers can register with a central tracker server to become discoverable.
* **Peer Discovery:** Users can retrieve a list of all currently online and registered peers.
* **VoIP Calls:** The platform allows users to initiate and receive one-to-one voice calls.
* **Real-time Audio Streaming:** Low-latency audio communication is achieved using the UDP protocol.
* **Concurrent Operations:** Multithreading is used to handle network operations and the user interface simultaneously, ensuring a non-blocking user experience.

## Technical Stack

* **Programming Language:** Python 3.x (Version 3.7 or higher is required).
* **Core Libraries:**
    * `socket`: Used for low-level network communication (TCP for registration, UDP for voice).
    * `threading`: To manage concurrent operations.
    * `pyaudio`: For real-time audio input and output streaming.

## System Requirements

* **Hardware:**
    * A working microphone (internal or external).
    * Speakers or headphones.
* **Network:**
    * A stable internet connection.
    * Open TCP/UDP ports are required for the application to function correctly.

## Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Install the required Python package:**
    The only external dependency is `PyAudio`. Install it using pip:
    ```bash
    pip install pyaudio
    ```

3.  **Configuration:**
    Before running, you must configure the network settings in `peer.py`. Set the `TRACKER_IP` to the IP address where the `tracker.py` server is running.
    ```python
    # Network Configuration in peer.py
    TRACKER_IP = 'Tracker IP_Address' # e.g., '127.0.0.1' for local testing
    TRACKER_PORT = 6000
    ```

## How to Run the Application

1.  **Start the Tracker Server:**
    The tracker is responsible for registering peers. **It must be run on a Linux machine.**
    ```bash
    python3 tracker.py
    ```
    The tracker will start listening for incoming peer connections.

2.  **Run the Peer Application:**
    Start the peer client on each user's machine (Linux or Windows).
    ```bash
    python3 peer.py
    ```
