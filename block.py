from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class DataBlock:
    def __init__(self, index, diff, previous_hash="0", timestamp=None, data=""):
        self.index = index
        self.timestamp = timestamp if timestamp else datetime.now()
        self.data = data
        self.previous_hash = previous_hash
        self.diff = diff
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        hasher = hashes.Hash(hashes.SHA256(), backend=default_backend())
        hasher.update(f"{self.index}{self.timestamp}{self.data}{
                      self.previous_hash}{self.diff}{self.nonce}".encode("utf-8"))
        return hasher.finalize().hex()

    def increment_nonce(self):
        """Increment nonce and recalculate hash."""
        self.nonce += 1
        self.hash = self.calculate_hash()

    def is_valid(self):
        return self.hash.startswith("0" * self.diff)

    def __str__(self):
        return f"Block {self.index} | Hash: {self.hash} | Nonce: {self.nonce} | Diff: {self.diff}"
