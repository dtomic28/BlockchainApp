from blockchain import Blockchain
from network import BlockchainNetwork
from gui import BlockchainGUI
import queue

if __name__ == "__main__":
    blockchain = Blockchain(diff=1)
    blockchain.create_genesis_block()

    network = BlockchainNetwork(blockchain)
    message_queue = queue.Queue()

    gui = BlockchainGUI(blockchain, network, message_queue=message_queue)
    network.set_write_callback(lambda msg, tag: message_queue.put((msg, tag)))

    gui.mainloop()
