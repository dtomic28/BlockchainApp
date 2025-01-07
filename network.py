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
        self.lock = threading.RLock()

    def set_write_callback(self, write_function):
        """Set a callback for GUI message logging."""
        self.write_line = write_function

    def start_server(self, port):
        """Start the server and begin listening for clients."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("127.0.0.1", port))
        self.server_socket.listen(5)
        self.running = True
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
                with self.lock:
                    if client_address in self.subscribers:
                        continue
                    self.subscribers[client_address] = client_socket
                    self.request_chain_sync(client_socket)
                threading.Thread(target=self.handle_client, args=(
                    client_socket,), daemon=True).start()
            except Exception as e:
                self.write_line(f"Error accepting connection: {e}", "error")

    def connect_to_node(self, port):
        """Connect to another node."""
        address = ("127.0.0.1", port)
        with self.lock:
            if address in self.subscribers:
                self.write_line(
                    f"Already connected to node at port {port}", "info")
                return False

            try:
                client_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect(address)
                self.subscribers[address] = client_socket
                self.request_chain_sync(client_socket)
                threading.Thread(target=self.handle_client, args=(
                    client_socket,), daemon=True).start()
                return True
            except Exception as e:
                self.write_line(f"Error connecting to node {
                                port}: {e}", "error")
                return False

    def handle_client(self, client_socket):
        """Handle incoming messages from connected clients with basic error handling."""
        try:
            while self.running:
                data = client_socket.recv(4096)  # Basic chunk receiving
                if not data:
                    break  # Client disconnected

                # Attempt to deserialize the received data
                try:
                    packet = pickle.loads(data)
                    self.process_packet(packet, client_socket)
                except (pickle.UnpicklingError, EOFError):
                    self.write_line(
                        "Received invalid or incomplete data.", "error")
        except (ConnectionResetError, OSError) as e:
            self.write_line(f"Connection error: {e}", "error")
        finally:
            # Clean up and remove the client
            with self.lock:
                for address, socket_obj in list(self.subscribers.items()):
                    if socket_obj == client_socket:
                        del self.subscribers[address]
                        client_socket.close()
                        self.write_line(
                            f"Client {address} disconnected.", "info")

    def process_packet(self, packet, client_socket):
        """Process incoming packets with chain conflict resolution."""
        packet_type = packet.get("type")

        # ✅ Handling Block Reception
        if packet_type == "BLOCK":
            new_block = packet["block"]
            latest_block = self.blockchain.get_latest_block()

            # Prevent duplicate blocks
            if latest_block and latest_block.hash == new_block.hash:
                self.write_line(f"Duplicate block {
                                new_block.index} received, ignoring.", "info")
                return

            # Add block if valid
            if self.blockchain.add_block(new_block):
                self.write_line(
                    f"Block {new_block.index} added successfully.", "success")
                self.broadcast({"type": "BLOCK", "block": new_block})
            else:
                self.write_line(
                    f"Block {new_block.index} rejected. Syncing chain...", "error")
                self.request_chain_sync(client_socket)

        # ✅ Handling Chain Synchronization Requests
        elif packet_type == "SYNC_REQUEST":
            try:
                client_socket.send(pickle.dumps(
                    {"type": "CHAIN_RESPONSE", "chain": self.blockchain.chain}))
            except Exception as e:
                self.write_line(f"Error sending chain: {e}", "error")

        # ✅ Handling Chain Response and Conflict Resolution
        elif packet_type == "CHAIN_RESPONSE":
            received_chain = packet["chain"]
            received_difficulty = self.blockchain.calculate_cumulative_difficulty()
            current_difficulty = self.blockchain.calculate_cumulative_difficulty()

            print(f"Current dif: {current_difficulty}. Recv: {
                received_difficulty}")
            if received_difficulty > current_difficulty and self.blockchain.validate_chain(received_chain):
                self.blockchain.chain = received_chain
                self.write_line(
                    "Chain replaced with a longer valid chain.", "success")
            else:
                self.write_line(
                    "Received chain was invalid or had lower difficulty.", "error")

        # ✅ Handling Peer Connection Requests
        elif packet_type == "CONNECT":
            new_node_port = packet["port"]
            if new_node_port not in [addr[1] for addr in self.subscribers]:
                self.connect_to_node(new_node_port)
                self.write_line(f"Connected to node {
                                new_node_port}.", "success")
            else:
                self.write_line(f"Already connected to node {
                                new_node_port}.", "info")

        else:
            self.write_line(f"Unknown packet type received: {
                            packet_type}", "error")

    def request_chain_sync(self, client_socket):
        """Request a chain sync from a peer."""
        try:
            sync_request = {"type": "SYNC_REQUEST"}
            client_socket.send(pickle.dumps(sync_request))
        except Exception as e:
            self.write_line(f"Error requesting chain sync: {e}", "error")

    def start_mining(self):
        """Mining loop with proper locking."""
        while self.running:
            with self.lock:
                latest_block = self.blockchain.get_latest_block()
                previous_hash = latest_block.hash if latest_block else "0"

            # Mine a new block
            new_block = DataBlock(index=len(
                self.blockchain.chain), diff=self.blockchain.diff, previous_hash=previous_hash)
            while not new_block.is_valid():
                new_block.increment_nonce()

            # Check the chain before finalizing the block
            with self.lock:
                latest_block_after_mining = self.blockchain.get_latest_block()
                if latest_block_after_mining.hash == previous_hash:
                    if self.blockchain.add_block(new_block):
                        self.broadcast({"type": "BLOCK", "block": new_block})
                        self.write_line(f"{new_block}", "success")
                    else:
                        self.write_line(
                            f"Block {new_block.index} rejected during mining.", "error")
                else:
                    self.write_line(
                        "Chain changed during mining. Restarting mining process.", "error")

    def broadcast(self, packet):
        """Broadcast a packet to all connected nodes with basic error handling."""
        with self.lock:
            disconnected_clients = []
            for address, client_socket in list(self.subscribers.items()):
                try:
                    # Serialize and send data
                    serialized_packet = pickle.dumps(packet)
                    client_socket.sendall(serialized_packet)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    self.write_line(f"Error broadcasting to {
                                    address}. Removing client.", "error")
                    disconnected_clients.append(address)

            # Remove any disconnected clients
            for address in disconnected_clients:
                if address in self.subscribers:
                    client_socket = self.subscribers.pop(address)
                    client_socket.close()
                    self.write_line(f"Client {address} removed.", "info")
