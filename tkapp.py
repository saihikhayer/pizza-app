import tkinter as tk
import requests
import threading
import win32print
import win32ui
import datetime

class OrderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BSS Food Orders")
        self.root.geometry("450x600")
        self.root.configure(bg="#2b2b2b")
        self.root.iconbitmap("icon.ico")  # Dark background for modern look

        self.url = "http://saihikhayer.pythonanywhere.com/get_new_orders/"
        self.purl = "http://saihikhayer.pythonanywhere.com/is_print/"
        self.urld = "http://saihikhayer.pythonanywhere.com/get_delivery_orders/"
        self.purld = "http://saihikhayer.pythonanywhere.com/is_print_delivery/"

        # Title Label with Modern Font and Spacing
        title_label = tk.Label(self.root, text="Incoming Orders", font=("Helvetica Neue", 18, "bold"), 
                               bg="#2b2b2b", fg="#f5f5f5", pady=20)
        title_label.pack()

        # Listbox with Modern Styling
        self.order_list = tk.Listbox(self.root, width=45, height=15, font=("Helvetica", 12), bg="#393939",
                                     fg="#ffffff", selectbackground="#4e8ef7", borderwidth=0, highlightthickness=0)
        self.order_list.pack(pady=10, padx=20)

        # Modern Styled Button
        refresh_button = tk.Button(self.root, text="Refresh Orders", command=self.refresh_orders,
                                   font=("Helvetica Neue", 12), bg="#4e8ef7", fg="#ffffff",
                                   activebackground="#5aa9f8", activeforeground="#ffffff",
                                   relief="flat", padx=10, pady=5, borderwidth=0)
        refresh_button.pack(pady=(10, 20))

        # Start fetching orders in separate threads
        threading.Thread(target=lambda: self.fetch_orders(self.url, self.purl), daemon=True).start()
        threading.Thread(target=lambda: self.fetch_orders(self.urld, self.purld), daemon=True).start()

    def fetch_orders(self, url, purl):
        """Fetch new orders from the Django API and update the Listbox."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                orders_data = response.json().get('messages', [])
                if orders_data:
                    for order in orders_data:
                        self.root.after(0, self.update_order_list, order[1])
                        self.root.after(0, lambda o=order: self.print_ticket(o[1], o[2]))
                        self.mark_as_printed(order[0], purl)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching orders: {e}")

        self.root.after(5000, self.fetch_orders, url, purl)

    def refresh_orders(self):
        """Manual refresh button to retrieve latest orders."""
        self.fetch_orders(self.url, self.purl)
        self.fetch_orders(self.urld, self.purld)

    def update_order_list(self, order_message):
        """Update the Listbox with a new order message."""
        self.order_list.insert(tk.END, order_message)

    def mark_as_printed(self, order_id, url):
        """Send POST request to mark order as printed after printing."""
        try:
            if order_id:
                response = requests.post(url, data={'order_id': order_id})
                if response.status_code == 200:
                    print(f"Order {order_id} marked as printed.")
        except requests.exceptions.RequestException as e:
            print(f"Error marking order as printed: {e}")

    def print_ticket(self, text, total_price):
        """Print the formatted order message to an 80mm thermal printer with smaller text."""
        try:
            printer_name = win32print.GetDefaultPrinter()
            current_datetime = datetime.datetime.now()
            date_str = current_datetime.strftime("%Y-%m-%d")
            time_str = current_datetime.strftime("%H:%M:%S")

            try:
                total_price = float(total_price)
            except ValueError:
                print(f"Could not convert total_price '{total_price}' to float.")
                total_price = 0.0

            order_items = text.split("\n")
            formatted_text = [
                "=========================",
                "       BSS FOOD SERVICES   ",
                "                  WELCOME   ",
                "-------------------------------------------",
                f"Date: {date_str} Time: {time_str}",
                "===========================================",
                
            ]

            formatted_text.extend(order_items)
            formatted_text += [
                "----------------------------",
                f" TOTAL: {total_price} da ",
                "----------------------------",
                "          Thank you for sharing a delicious moment with us    ",
                "                         ",
                "======================================================",
              
                "      INSTAGRAM : bss_food_03     TEL : 0670814232                      ",

            
            ]

            printer = win32print.OpenPrinter(printer_name)
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            hdc.StartDoc("Order Ticket")
            hdc.StartPage()

            title_font = win32ui.CreateFont({"name": "Arial", "height": 40, "weight": 700})
            body_font = win32ui.CreateFont({"name": "Arial", "height": 24, "weight": 400})

            hdc.SelectObject(title_font)
            y_position = 40
            for line in formatted_text[:5]:
                hdc.TextOut(40, y_position, line)
                y_position += 60

            hdc.SelectObject(body_font)
            for line in formatted_text[5:]:
                hdc.TextOut(40, y_position, line)
                y_position += 40

            hdc.EndPage()
            hdc.EndDoc()
            print("Order has been sent to the printer with date and time!")
            win32print.ClosePrinter(printer)

        except Exception as e:
            print(f"Error printing: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = OrderApp(root)
    root.mainloop()
