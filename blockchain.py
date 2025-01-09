from block import DataBlock
from datetime import datetime, timedelta


class Blockchain:
    def __init__(self, diff):
        self.chain = []
        self.diff = diff
        self.block_generation_interval = 10
        self.difficulty_adjustment_interval = 10

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
            self.diff = self.adjust_difficulty()
            return True
        return False

    def validate_block(self, block):
        """Validates the integrity of a block without recalculating the hash."""
        if len(self.chain) == 0:
            # Ensure the genesis block has the correct initial conditions
            return block.previous_hash == "0" and block.hash == block.calculate_hash()

        last_block = self.get_latest_block()
        # Validate without recalculating the hash
        return (
            block.previous_hash == last_block.hash
            and block.index == last_block.index + 1
            and block.hash.startswith("0" * block.diff)  # Proof of work check
        )

    def validate_chain(self, chain):
        """Validates the entire blockchain without recalculating each hash."""
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]

            if (
                current_block.previous_hash != previous_block.hash or
                current_block.hash != current_block.calculate_hash() or
                not current_block.hash.startswith("0" * current_block.diff)
            ):
                return False
        return True

    def adjust_difficulty(self):
        """Fixed: Consistently use datetime objects."""
        if len(self.chain) < self.difficulty_adjustment_interval:
            return self.diff

        latest_block = self.get_latest_block()
        prev_adjustment_block = self.chain[-self.difficulty_adjustment_interval]

        # Now using timedelta comparison directly
        time_taken = (latest_block.timestamp -
                      prev_adjustment_block.timestamp).total_seconds()
        time_expected = self.block_generation_interval * \
            self.difficulty_adjustment_interval

        if time_taken < time_expected / 2:
            return self.diff + 1
        elif time_taken > time_expected * 2:
            return max(1, self.diff - 1)
        return self.diff

    def calculate_cumulative_difficulty(self):
        """Calculates the cumulative difficulty of the blockchain."""
        return sum(2 ** block.diff for block in self.chain)
