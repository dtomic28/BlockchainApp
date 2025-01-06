from blockchain import Blockchain
from network import BlockchainNetwork
from gui import BlockchainGUI
import threading

if __name__ == "__main__":
    blockchain = Blockchain(diff=4)
    blockchain.create_genesis_block()

    network = BlockchainNetwork(blockchain)
    threading.Thread(target=network.start_server, args=(5000,)).start()

    gui = BlockchainGUI(blockchain)
    gui.run()
