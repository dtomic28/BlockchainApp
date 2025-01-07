from datetime import datetime, timedelta
from block import DataBlock


class Blockchain:
    def __init__(self, diff):
        self.chain = []
        self.diff = diff
        self.block_generation_interval = 10
        self.difficulty_adjustment_interval = 10

    def create_genesis_block(self):
        genesis_block = DataBlock(0, self.diff)
        self.chain.append(genesis_block)

    def get_latest_block(self):
        return self.chain[-1] if self.chain else None

    def add_block(self, block):
        if self.validate_block(block):
            self.chain.append(block)
            self.diff = self.adjust_difficulty()
            return True
        return False

    def validate_block(self, block):
        if block.index != len(self.chain):
            return False
        if block.previous_hash != (self.get_latest_block().hash if self.get_latest_block() else "0"):
            return False
        if block.calculate_hash() != block.hash:
            return False
        if block.timestamp > datetime.now() + timedelta(minutes=1):
            return False
        if self.chain and block.timestamp < self.get_latest_block().timestamp - timedelta(minutes=1):
            return False
        return True

    def adjust_difficulty(self):
        if len(self.chain) < self.difficulty_adjustment_interval:
            return self.diff

        latest_block = self.get_latest_block()
        prev_adjustment_block = self.chain[-self.difficulty_adjustment_interval]
        time_expected = self.block_generation_interval * \
            self.difficulty_adjustment_interval
        time_taken = (latest_block.timestamp -
                      prev_adjustment_block.timestamp).total_seconds()

        if time_taken < (time_expected / 2):
            return self.diff + 1
        elif time_taken > (time_expected * 2):
            return max(1, self.diff - 1)
        return self.diff

    def cumulative_difficulty(self):
        return sum([2**block.diff for block in self.chain])
