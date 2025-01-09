import socket
import threading
import pickle
from block import DataBlock
import time


class BlockchainNetwork:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.subscribers = {}
        self.server_socket = None
        self.running = False
        self.lock = threading.RLock()
        self.write_line = None
        self.mining_active = False

    def set_write_callback(self, write_function):
        self.write_line = write_function

    def start_server(self, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("127.0.0.1", port))
        self.server_socket.listen(5)
        self.running = True
        self.write_line(f"Server started on port {port}", "info")

        threading.Thread(target=self.listen_for_clients, daemon=True).start()
        threading.Thread(target=self.periodic_synchronization,
                         daemon=True).start()

    def periodic_synchronization(self, interval=30):
        """Synchronize the blockchain periodically."""
        while self.running:
            time.sleep(interval)
            with self.lock:
                self.write_line("Periodic synchronization triggered.", "info")
                for client_socket in list(self.subscribers.values()):
                    self.request_chain_sync(client_socket)

    def listen_for_clients(self):
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.write_line(f"New connection from {
                                client_address}", "info")
                with self.lock:
                    self.subscribers[client_address] = client_socket
                self.request_chain_sync(client_socket)
                threading.Thread(target=self.handle_client, args=(
                    client_socket,), daemon=True).start()
            except Exception as e:
                self.write_line(f"Error accepting connection: {e}", "error")

    def connect_to_node(self, port):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("127.0.0.1", port))
            with self.lock:
                self.subscribers[("127.0.0.1", port)] = client_socket
            self.write_line(f"Connected to node on port {port}", "success")
            self.request_chain_sync(client_socket)
            threading.Thread(target=self.handle_client, args=(
                client_socket,), daemon=True).start()
        except Exception as e:
            self.write_line(f"Error connecting to node on port {
                            port}: {e}", "error")

    def handle_client(self, client_socket):
        """Client handler with simplified error handling."""
        try:
            while self.running:
                data_chunk = client_socket.recv(4096)
                if not data_chunk:
                    self.write_line("Client disconnected.", "info")
                    self._disconnect_client(client_socket)
                    return

                try:
                    packet = pickle.loads(data_chunk)
                    self.process_packet(packet, client_socket)
                except (pickle.UnpicklingError, EOFError) as e:
                    pass
        except (ConnectionResetError, OSError) as e:
            self.write_line(f"Connection error: {e}", "error")
            self._disconnect_client(client_socket)

    def send_packet(self, client_socket, packet):
        """Simplified packet sender."""
        try:
            serialized_packet = pickle.dumps(packet)
            client_socket.sendall(serialized_packet)
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            self.write_line(f"Error sending data: {
                            e}. Disconnecting client.", "error")
            self._disconnect_client(client_socket)

    def process_packet(self, packet, client_socket):
        """Simplified packet processing."""
        packet_type = packet.get("type")

        if packet_type == "BLOCK":
            new_block = packet["block"]

            # Prevent self-rejection: Ignore if block already exists
            latest_block = self.blockchain.get_latest_block()
            if latest_block and latest_block.hash == new_block.hash:
                return

            if self.blockchain.add_block(new_block):
                self.write_line(f"Added: {new_block}", "success")
                self.broadcast({"type": "BLOCK", "block": new_block})
            else:
                self.write_line(
                    f"Block {new_block.index} rejected. Syncing chain...", "error")
                self.request_chain_sync(client_socket)

        elif packet_type == "SYNC_REQUEST":
            self.send_packet(
                client_socket, {"type": "CHAIN_RESPONSE", "chain": self.blockchain.chain})

        elif packet_type == "CHAIN_RESPONSE":
            received_chain = packet["chain"]
            if self.blockchain.validate_chain(received_chain):
                if len(received_chain) > len(self.blockchain.chain):
                    self.blockchain.chain = received_chain
                    self.write_line(
                        "Replaced with a longer valid chain.", "success")
            else:
                self.write_line("Received chain was invalid.", "error")

        elif packet_type == "CONNECT":
            port = packet["port"]
            if port not in [addr[1] for addr in self.subscribers]:
                self.connect_to_node(port)

        else:
            self.write_line(f"Unknown packet type: {packet_type}", "error")

    def broadcast(self, packet):
        """Broadcast a packet to all connected nodes."""
        with self.lock:
            for client_socket in list(self.subscribers.values()):
                self.send_packet(client_socket, packet)

    def request_chain_sync(self, client_socket):
        """Send a chain sync request."""
        self.send_packet(client_socket, {"type": "SYNC_REQUEST"})

    def _disconnect_client(self, client_socket):
        """Gracefully disconnect a client."""
        with self.lock:
            for address, sock in list(self.subscribers.items()):
                if sock == client_socket:
                    del self.subscribers[address]
                    client_socket.close()
                    self.write_line(f"Client {address} disconnected.", "info")

    def start_mining(self):
        """Start the mining process."""
        self.mining_active = True
        threading.Thread(target=self.mine_block, daemon=True).start()

    def stop_mining(self):
        """Stop the mining process."""
        self.mining_active = False
        self.write_line("Mining stopped.", "info")

    def mine_block(self):
        """Simplified mining loop without restarting."""
        while self.mining_active:
            with self.lock:
                latest_block = self.blockchain.get_latest_block()
                previous_hash = latest_block.hash if latest_block else "0"

            # Create a new block and mine until valid
            new_block = DataBlock(index=len(self.blockchain.chain),
                                  diff=self.blockchain.diff,
                                  previous_hash=previous_hash)

            # Continuous mining without resetting
            while not new_block.is_valid():
                new_block.increment_nonce()
                if new_block.nonce % 500000 == 0:
                    self.write_line(f"Mining... Current nonce: {
                                    new_block.nonce}", "info")

            # Check if chain has changed during mining
            with self.lock:
                latest_block_after_mining = self.blockchain.get_latest_block()
                if latest_block_after_mining.hash == previous_hash:
                    if self.blockchain.add_block(new_block):
                        self.broadcast({"type": "BLOCK", "block": new_block})
                        self.write_line(f"Mined: {new_block}", "success")
                else:
                    self.write_line(
                        "Chain changed during mining. Skipping block.", "error")
