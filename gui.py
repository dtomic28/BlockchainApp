import tkinter as tk


class BlockchainGUI(tk.Tk):
    def __init__(self, blockchain, network, message_queue):
        super().__init__()
        self.blockchain = blockchain
        self.network = network
        self.message_queue = message_queue
        self.title("Blockchain GUI")

        # Text Area for Display with Formatting
        self.text_area = tk.Text(self, state="disabled", height=20, width=70)
        self.text_area.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        # Adding Text Tags for Formatting
        self.text_area.tag_configure("info", foreground="blue")
        self.text_area.tag_configure("success", foreground="green")
        self.text_area.tag_configure("error", foreground="red")

        # Node Control Inputs
        self.port_label = tk.Label(self, text="Enter Port:")
        self.port_label.grid(row=1, column=0, padx=10)

        self.port_entry = tk.Entry(self)
        self.port_entry.grid(row=1, column=1, padx=10)

        self.start_button = tk.Button(
            self, text="Start Node", command=self.start_node)
        self.start_button.grid(row=1, column=2, padx=10)

        self.connect_label = tk.Label(self, text="Connect to Node Port:")
        self.connect_label.grid(row=2, column=0, padx=10)

        self.connect_entry = tk.Entry(self)
        self.connect_entry.grid(row=2, column=1, padx=10)

        self.connect_button = tk.Button(
            self, text="Connect", command=self.connect_to_node)
        self.connect_button.grid(row=2, column=2, padx=10)

        # Quit Button
        self.quit_button = tk.Button(self, text="Quit", command=self.quit)
        self.quit_button.grid(row=3, column=1, pady=10)

    def start_node(self):
        """Start the node."""
        try:
            port = int(self.port_entry.get())
            self.network.start_server(port)
            self.write_line(f"Node started on port {port}", "info")
        except ValueError:
            self.write_line("Invalid port number.", "error")

    def connect_to_node(self):
        """Connect to another node by establishing a direct socket connection."""
        try:
            port = int(self.connect_entry.get())
            success = self.network.connect_to_node(port)
            if success:
                self.write_line(f"Successfully connected to node on port {
                                port}", "success")
            else:
                self.write_line(
                    f"Failed to connect to node on port {port}", "error")
        except ValueError:
            self.write_line("Invalid port number.", "error")

    def write_line(self, message, tag="info"):
        """Write a message with formatting using the tuple-based approach."""
        self.text_area.config(state="normal")
        self.text_area.insert("end", message + "\n", tag)
        self.text_area.config(state="disabled")
        self.text_area.see("end")

    def mainloop(self, interval=1):
        """Overriding mainloop to process the message queue."""
        def process_queue():
            while not self.message_queue.empty():
                message, tag = self.message_queue.get()
                self.write_line(message, tag)
            self.after(interval, process_queue)

        process_queue()
        super().mainloop()
