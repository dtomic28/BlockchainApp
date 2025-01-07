import hashlib
import time
from datetime import datetime


class DataBlock:
    def __init__(self, index, diff, previous_hash="0"):
        self.index = index
        self.timestamp = datetime.now()
        self.data = f"Block Data {index}"
        self.previous_hash = previous_hash
        self.diff = diff
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        sha = hashlib.sha256()
        sha.update(f"{self.index}{self.timestamp}{self.data}{
                   self.previous_hash}{self.diff}{self.nonce}".encode())
        return sha.hexdigest()

    def increment_nonce(self):
        self.nonce += 1
        self.hash = self.calculate_hash()

    def is_valid(self):
        """Check if the hash meets the difficulty requirement."""
        return self.hash.startswith("0" * self.diff)

    def __str__(self):
        return f"Block {self.index} | Hash: {self.hash} | Nonce: {self.nonce} | Diff: {self.diff}"
