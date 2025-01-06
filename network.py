import socket
import threading
import pickle


class BlockchainNetwork:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.subscribers = {}
        self.server_socket = None
        self.running = True

    def start_server(self, port):
        """Start a node server on a specified port."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("127.0.0.1", port))
        self.server_socket.listen(5)
        print(f"Node started on port {port}")
        threading.Thread(target=self.listen_for_clients).start()

    def listen_for_clients(self):
        """Continuously listen for incoming peer connections."""
        while self.running:
            client_socket, address = self.server_socket.accept()
            print(f"New connection from {address}")
            threading.Thread(target=self.handle_client,
                             args=(client_socket,)).start()

    def handle_client(self, client_socket):
        """Handle incoming packets from peers."""
        while self.running:
            try:
                data = client_socket.recv(4096)
                if data:
                    packet = pickle.loads(data)
                    self.process_packet(packet, client_socket)
            except Exception:
                client_socket.close()
                break

    def process_packet(self, packet, client_socket):
        """Process received packets for synchronization and block sharing."""
        if packet["type"] == "SYNC":
            response = {"type": "SYNC_RESP", "chain": self.blockchain.chain}
            client_socket.send(pickle.dumps(response))
        elif packet["type"] == "BLOCK":
            new_block = packet["block"]
            self.blockchain.add_block(new_block)

    def broadcast(self, packet):
        """Broadcast a message to all connected nodes."""
        for client_socket in self.subscribers.values():
            try:
                client_socket.send(pickle.dumps(packet))
            except Exception:
                continue
