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
        """Continuously listen for incoming client connections."""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()

                # ✅ Prevent duplicate connections by checking IP and Port
                if client_address in self.subscribers:
                    self.write_line(f"Duplicate connection from {
                                    client_address}, ignoring.", "error")
                    client_socket.close()
                    continue

                self.subscribers[client_address] = client_socket
                self.request_chain_sync(client_socket)
                if self.write_line:
                    self.write_line(f"New connection from {
                                    client_address}", "success")

                threading.Thread(target=self.handle_client, args=(
                    client_socket,), daemon=True).start()
            except Exception as e:
                if self.write_line:
                    self.write_line(
                        f"Error accepting connection: {e}", "error")

    def connect_to_node(self, port):
        """Connect to another node and ensure only one connection per node."""
        address = ("127.0.0.1", port)

        # ✅ Check for existing connection before creating a new one
        if address in self.subscribers:
            if self.write_line:
                self.write_line(
                    f"Already connected to node at port {port}", "info")
            return False

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(address)
            packet = {"type": "CONNECT", "port": port}
            client_socket.send(pickle.dumps(packet))

            # ✅ Register the new connection
            self.subscribers[address] = client_socket
            self.request_chain_sync(client_socket)

            threading.Thread(target=self.handle_client, args=(
                client_socket,), daemon=True).start()
            if self.write_line:
                self.write_line(f"Connected to node on port {port}", "success")
            return True
        except Exception as e:
            if self.write_line:
                self.write_line(f"Error connecting to node at port {
                                port}: {e}", "error")
            return False

    def request_chain_sync(self, client_socket):
        """Request chain synchronization from a connected node."""
        try:
            sync_request = {"type": "SYNC_REQUEST"}
            client_socket.send(pickle.dumps(sync_request))
            if self.write_line:
                self.write_line(
                    "Requesting chain synchronization from a peer...", "info")
        except Exception as e:
            self.write_line(f"Error requesting chain sync: {e}", "error")

    def request_chain_sync_all(self):
        """Request chain synchronization from all connected nodes."""
        sync_request = {"type": "SYNC_REQUEST"}
        self.broadcast(sync_request)
        if self.write_line:
            self.write_line(
                "Requesting chain sync from all connected nodes...", "info")

    def handle_client(self, client_socket):
        """Handle incoming messages from connected clients."""
        try:
            while self.running:
                data = client_socket.recv(4096)
                if data:
                    packet = pickle.loads(data)
                    self.process_packet(packet, client_socket)
        except Exception as e:
            self.write_line(f"Connection error: {e}", "error")
            client_socket.close()

    def process_packet(self, packet, client_socket):
        """Process incoming packets with enhanced conflict handling."""
        if packet["type"] == "BLOCK":
            new_block = packet["block"]

            # ✅ Check if the received block belongs to the current chain
            if self.blockchain.add_block(new_block):
                self.write_line(
                    f"Block {new_block.index} added successfully.", "info")
                self.request_chain_sync_all()  # Ask for chain sync after block addition
            else:
                # Request sync if rejected
                self.request_chain_sync(client_socket)

        elif packet["type"] == "SYNC_REQUEST":
            # ✅ Send the entire chain to the requesting node
            client_socket.send(pickle.dumps(
                {"type": "CHAIN_RESPONSE", "chain": self.blockchain.chain}))

        elif packet["type"] == "CHAIN_RESPONSE":
            received_chain = packet["chain"]
            self.synchronize_chain(received_chain)

    def synchronize_chain(self, received_chain):
        """Synchronize with the received chain using the longest chain rule and validation."""
        # ✅ Proper conflict resolution logic added here
        if self.blockchain.validate_chain(received_chain):
            if len(received_chain) > len(self.blockchain.chain):
                self.blockchain.chain = received_chain
                self.write_line(
                    "Chain replaced with a longer valid chain.", "success")
            else:
                self.write_line(
                    "Received chain is not longer. No changes made.", "info")
        else:
            self.write_line("Received chain is invalid.", "error")

    def start_mining(self):
        """Mining loop with proper chain comparison after every block."""
        while self.running:
            latest_block = self.blockchain.get_latest_block()
            previous_hash = latest_block.hash if latest_block else "0"
            new_block = DataBlock(index=len(
                self.blockchain.chain), diff=self.blockchain.diff, previous_hash=previous_hash)

            while not new_block.is_valid():
                new_block.increment_nonce()
                if new_block.nonce % 500000 == 0 and self.write_line:
                    self.write_line(f"{new_block}", "error")

            # ✅ Proper conflict handling after mining
            if self.blockchain.add_block(new_block):
                self.broadcast({"type": "BLOCK", "block": new_block})
                self.request_chain_sync_all()
                self.write_line(
                    f"{new_block}", "success")

    def broadcast(self, packet):
        """Broadcast a packet to all connected nodes."""
        for address, client_socket in list(self.subscribers.items()):
            try:
                client_socket.send(pickle.dumps(packet))
            except Exception as e:
                print(f"Error broadcasting to {
                    address}: {e}")
                client_socket.close()
                del self.subscribers[address]
