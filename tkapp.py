import tkinter as tk
import asyncio
import websockets
import json
import threading
from queue import Queue
import win32print
import win32ui


class OrderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chef Orders")

        # Create a Listbox to display orders
        self.order_list = tk.Listbox(self.root, width=50, height=20)
        self.order_list.pack(pady=20)

        # Queue to communicate between WebSocket thread and Tkinter
        self.order_queue = Queue()

        # Start the WebSocket listener in a separate thread
        threading.Thread(target=self.start_websocket, daemon=True).start()

        # Periodically check the queue and update the Listbox
        self.root.after(100, self.check_orders)

    async def listen_orders(self):
        uri = "ws://localhost:8000/ws/orders/"
        try:
            async with websockets.connect(uri) as websocket:
                while True:
                    message = await websocket.recv()
                    order_data = json.loads(message)

                    # Put the received message into the queue
                    self.order_queue.put(order_data['message'])
        except Exception as e:
            print(f"WebSocket error: {e}")
            self.order_queue.put(f"WebSocket error: {e}")

    def start_websocket(self):
        asyncio.run(self.listen_orders())

    def check_orders(self):
        """Check the queue and insert new orders into the Listbox."""
        while not self.order_queue.empty():
            order_message = self.order_queue.get()

            # Insert the message into the Listbox
            self.order_list.insert(tk.END, order_message)

            # Automatically print the formatted message
            self.print_ticket(order_message)

        # Re-run this method after 100 milliseconds
        self.root.after(100, self.check_orders)

    def print_ticket(self, text):
        """Print the formatted order message to the configured printer using a Canvas."""
        try:
            printer_name = win32print.GetDefaultPrinter()  # Use the default printer

            # Parse and format the order text (assuming comma-separated dishes)
            dishes = text.split("-")  # Assuming dishes are comma-separated in the text
            formatted_text = ["Order Ticket", "-------------------------"] + dishes + ["-------------------------", "Thank you for your order!"]

            # Open the printer
            printer = win32print.OpenPrinter(printer_name)
            try:
                # Set up the printer context
                hdc = win32ui.CreateDC()
                hdc.CreatePrinterDC(printer_name)
                hdc.StartDoc("Order Ticket")
                hdc.StartPage()

                # Set the font and text formatting
                font = win32ui.CreateFont({
                    "name": "Arial",
                    "height": 80,  # Font size for the ticket
                    "weight": 700,  # Bold font
                    "italic": 0
                })
                hdc.SelectObject(font)  # Select the font for the printer context

                # Define the starting position for printing the text
                x_position = 100  # Starting X position
                y_position = 100  # Starting Y position
                line_height = 120  # Distance between lines of text

                # Print each line of the formatted text
                for line in formatted_text:
                    hdc.TextOut(x_position, y_position, line)
                    y_position += line_height  # Move the Y position down for the next line

                # Add additional style elements (like lines to separate sections)
                hdc.MoveTo(x_position, y_position + 20)  # Start position of the line
                hdc.LineTo(x_position + 600, y_position + 20)  # Length of the line

                # End the page and the document
                hdc.EndPage()
                hdc.EndDoc()

                print("Order has been sent to the printer with professional formatting!")

            except Exception as e:
                print(f"Failed to print the order: {e}")

            finally:
                # Close the printer handle
                win32print.ClosePrinter(printer)

        except Exception as e:
            print(f"Error printing: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = OrderApp(root)
    root.mainloop()
