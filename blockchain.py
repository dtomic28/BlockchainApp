from datetime import datetime
from block import DataBlock


class Blockchain:
    def __init__(self, diff):
        self.chain = []
        self.diff = diff
        self.block_generation_interval = 10  # in seconds
        self.difficulty_adjustment_interval = 10  # Adjust every 10 blocks

    def create_genesis_block(self):
        """Creates the first block with no previous hash."""
        genesis_block = DataBlock(0, self.diff)
        self.chain.append(genesis_block)

    def get_latest_block(self):
        """Returns the latest block in the chain."""
        return self.chain[-1] if self.chain else None

    def add_block(self, block):
        """Adds a block to the chain after validation."""
        if self.validate_block(block):
            self.chain.append(block)
            # ✅ Proper difficulty adjustment called here
            self.diff = self.adjust_difficulty()
        else:
            print("Invalid block. Not added to chain.")

    def validate_block(self, block):
        """Validates a block's integrity."""
        if block.index != len(self.chain):
            return False
        if block.previous_hash != (self.get_latest_block().hash if self.get_latest_block() else "0"):
            return False
        if block.calculate_hash() != block.hash:
            return False
        return True

    def validate_chain(self):
        """Validates the entire blockchain's integrity."""
        for i in range(1, len(self.chain)):
            if not self.validate_block(self.chain[i]):
                return False
        return True

    def adjust_difficulty(self):
        """Adjusts the mining difficulty based on block generation speed."""
        if len(self.chain) < self.difficulty_adjustment_interval:
            return self.diff

        latest_block = self.get_latest_block()
        prev_adjustment_block = self.chain[-self.difficulty_adjustment_interval]

        time_expected = self.block_generation_interval * \
            self.difficulty_adjustment_interval
        time_taken = (latest_block.timestamp -
                      prev_adjustment_block.timestamp).total_seconds()

        if time_taken < time_expected / 2:
            return self.diff + 1
        elif time_taken > time_expected * 2:
            return max(1, self.diff - 1)  # Prevent diff from dropping below 1
        return self.diff
