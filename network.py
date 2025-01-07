import socket
import threading
import pickle
from block import DataBlock


class BlockchainNetwork:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.subscribers = {}
        self.server_socket = None
        self.running = False
        self.mining_thread = None
        self.receiver_thread = None
        self.write_line = None

    def set_write_callback(self, write_function):
        """Set the GUI callback function for message queuing."""
        self.write_line = write_function

    def start_server(self, port):
        """Start the server and mining."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("127.0.0.1", port))
        self.server_socket.listen(5)
        self.running = True

        if self.write_line:
            self.write_line(f"Node started on port {port}", "info")

        self.receiver_thread = threading.Thread(
            target=self.listen_for_clients, daemon=True)
        self.receiver_thread.start()
        self.mining_thread = threading.Thread(
            target=self.start_mining, daemon=True)
        self.mining_thread.start()

    def listen_for_clients(self):
        """Continuously listen for new client connections."""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.subscribers[client_address] = client_socket

                # ✅ Handle incoming connection requests properly
                data = client_socket.recv(4096)
                packet = pickle.loads(data)
                if packet["type"] == "CONNECT":
                    if self.write_line:
                        self.write_line(f"New node connected from {
                                        client_address}", "success")

                # ✅ Start listening to the connected node
                threading.Thread(target=self.handle_client, args=(
                    client_socket,), daemon=True).start()

            except Exception as e:
                if self.write_line:
                    self.write_line(
                        f"Error accepting connection: {e}", "error")

    def handle_client(self, client_socket):
        """Handle incoming data from connected clients."""
        try:
            while self.running:
                data = client_socket.recv(4096)
                if data:
                    packet = pickle.loads(data)
                    self.process_packet(packet)
        except Exception as e:
            if self.write_line:
                self.write_line(f"Error receiving data: {e}", "error")
            client_socket.close()

    def process_packet(self, packet):
        """Process incoming packets."""
        if packet["type"] == "BLOCK":
            new_block = packet["block"]
            if self.blockchain.add_block(new_block):
                if self.write_line:
                    self.write_line(
                        f"Valid block {new_block.index} received.", "success")
            else:
                if self.write_line:
                    self.write_line(f"Invalid block {
                                    new_block.index}.", "error")

    def start_mining(self):
        """Mining loop with messages sent to the queue."""
        while self.running:
            latest_block = self.blockchain.get_latest_block()
            previous_hash = latest_block.hash if latest_block else "0"
            new_block = DataBlock(index=len(
                self.blockchain.chain), diff=self.blockchain.diff, previous_hash=previous_hash)

            while not new_block.is_valid():
                new_block.increment_nonce()
                """if new_block.nonce % 100000 == 0 and self.write_line:
                    self.write_line(f"{
                                    new_block}", "error")
                """
            if self.blockchain.add_block(new_block):
                self.broadcast({"type": "BLOCK", "block": new_block})
                if self.write_line:
                    self.write_line(
                        f"{new_block}", "success")

    def connect_to_node(self, port):
        """Attempt to establish a direct connection with another node."""
        try:
            # ✅ Create a new socket and connect to the specified port
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("127.0.0.1", port))

            # ✅ Send a connection request packet
            packet = {"type": "CONNECT", "port": port}
            client_socket.send(pickle.dumps(packet))

            # ✅ Store the connection in the subscribers list
            self.subscribers[(port, "127.0.0.1")] = client_socket

            # ✅ Start a listener for this new connection
            threading.Thread(target=self.handle_client, args=(
                client_socket,), daemon=True).start()
            if self.write_line:
                self.write_line(f"Connected to node on port {port}", "success")

            return True
        except Exception as e:
            if self.write_line:
                self.write_line(f"Error connecting to node on port {
                                port}: {e}", "error")
            return False

    def broadcast(self, packet):
        """Broadcast a packet to all connected clients."""
        for address, client_socket in list(self.subscribers.items()):
            try:
                client_socket.send(pickle.dumps(packet))
                if self.write_line:
                    self.write_line(f"Broadcasting message to {
                                    address}", "info")
            except Exception as e:
                if self.write_line:
                    self.write_line(f"Error sending to {
                                    address}: {e}", "error")
                client_socket.close()
                del self.subscribers[address]
