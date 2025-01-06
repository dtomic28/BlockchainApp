import secrets
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class DataBlock:
    def __init__(self, index, diff, previous_hash="0"):
        self.index = index
        self.timestamp = datetime.now()
        self.data = secrets.token_bytes(16)
        self.previous_hash = previous_hash
        self.diff = diff
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Calculates the block hash using SHA-256 and proof-of-work"""
        while True:
            hasher = hashes.Hash(hashes.SHA256(), backend=default_backend())
            hasher.update(self.get_data_string().encode("utf-8"))
            hash_value = hasher.finalize().hex()
            if hash_value[:self.diff] == "0" * self.diff:
                return hash_value
            self.nonce += 1

    def get_data_string(self):
        """Returns the concatenated block data for hashing"""
        return f"{self.index}{self.timestamp}{self.data.hex()}{self.previous_hash}{self.diff}{self.nonce}"

    def __str__(self):
        """Returns a readable representation of the block"""
        return f"Index: {self.index}, Hash: {self.hash}, PrevHash: {self.previous_hash}, Nonce: {self.nonce}, Timestamp: {self.timestamp}"
