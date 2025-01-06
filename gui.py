import tkinter as tk
from tkinter import messagebox
from block import DataBlock


class BlockchainGUI:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.root = tk.Tk()
        self.root.title("Blockchain Explorer")
        self.setup_gui()

    def setup_gui(self):
        self.add_block_btn = tk.Button(
            self.root, text="Add Block", command=self.add_block)
        self.add_block_btn.pack(pady=10)

        self.validate_btn = tk.Button(
            self.root, text="Validate Chain", command=self.validate_chain)
        self.validate_btn.pack(pady=10)

        self.text_area = tk.Text(
            self.root, state=tk.DISABLED, height=20, width=60)
        self.text_area.pack(pady=10)

    def add_block(self):
        """Mine and add a new block."""
        latest_block = self.blockchain.get_latest_block()
        prev_hash = latest_block.hash if latest_block else "0"
        new_block = DataBlock(len(self.blockchain.chain),
                              self.blockchain.diff, prev_hash)
        self.blockchain.add_block(new_block)
        self.update_text_area()

    def validate_chain(self):
        """Validate the entire blockchain."""
        valid = self.blockchain.validate_chain()
        messagebox.showinfo("Validation", f"Blockchain is {
                            'valid' if valid else 'invalid'}!")

    def update_text_area(self):
        """Update the GUI with the current blockchain state."""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        for block in self.blockchain.chain:
            self.text_area.insert(tk.END, str(block) + "\n")
        self.text_area.config(state=tk.DISABLED)

    def run(self):
        self.root.mainloop()
