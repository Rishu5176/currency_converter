import requests
import threading
from tkinter import Tk, Label, Entry, Button, StringVar, ttk, messagebox

# Constants
CURRENCIES_URL = 'https://api.frankfurter.app/currencies'
CONVERT_URL = 'https://api.frankfurter.app/latest'

class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Currency Converter')
        self.root.geometry('420x300')
        self.root.resizable(False, False)

        # StringVars
        self.amount_var = StringVar(value='1')
        self.from_var = StringVar()
        self.to_var = StringVar()
        self.result_var = StringVar()

        # UI
        Label(root, text='Currency Converter', font=('Helvetica', 16, 'bold')).pack(pady=10)

        Label(root, text='Amount:').pack()
        self.amount_entry = Entry(root, textvariable=self.amount_var, justify='center', width=20)
        self.amount_entry.pack(pady=5)

        frame = ttk.Frame(root)
        frame.pack(pady=8)

        Label(frame, text='From:').grid(row=0, column=0, padx=6)
        self.from_combo = ttk.Combobox(frame, textvariable=self.from_var, width=10, state='readonly')
        self.from_combo.grid(row=0, column=1, padx=6)

        Label(frame, text='To:').grid(row=0, column=2, padx=6)
        self.to_combo = ttk.Combobox(frame, textvariable=self.to_var, width=10, state='readonly')
        self.to_combo.grid(row=0, column=3, padx=6)

        Button(root, text='Convert', command=self.on_convert, width=12).pack(pady=10)
        Button(root, text='Swap', command=self.swap_currencies, width=12).pack(pady=4)

        self.result_label = Label(root, textvariable=self.result_var, font=('Helvetica', 12, 'bold'))
        self.result_label.pack(pady=12)

        self.status_label = Label(root, text='Loading currencies...', fg='gray')
        self.status_label.pack(side='bottom', pady=6)

        # internal cache
        self.currencies = None

        # load currencies in a separate thread to avoid blocking UI
        threading.Thread(target=self.load_currencies, daemon=True).start()

    def load_currencies(self):
        try:
            res = requests.get(CURRENCIES_URL, timeout=10)
            res.raise_for_status()
            data = res.json()  # {'USD': 'United States Dollar', ...}

            # Sort currency codes for nicer UI
            codes = sorted(data.keys())
            self.currencies = codes

            # Update the comboboxes on the main thread
            def update_ui():
                self.from_combo['values'] = codes
                self.to_combo['values'] = codes
                # sensible defaults
                if 'USD' in codes:
                    self.from_var.set('USD')
                else:
                    self.from_var.set(codes[0])
                if 'INR' in codes:
                    self.to_var.set('INR')
                else:
                    self.to_var.set(codes[1] if len(codes) > 1 else codes[0])

                self.status_label.config(text='Ready')

            self.root.after(0, update_ui)

        except Exception as e:
            def show_error():
                self.status_label.config(text='Failed to load currencies')
                messagebox.showerror('Error', f'Could not load currencies list:\n{e}')

            self.root.after(0, show_error)

    def swap_currencies(self):
        a = self.from_var.get()
        b = self.to_var.get()
        self.from_var.set(b)
        self.to_var.set(a)

    def on_convert(self):
        # basic validation
        try:
            amount = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror('Invalid input', 'Please enter a numeric amount')
            return

        from_curr = self.from_var.get()
        to_curr = self.to_var.get()

        if not from_curr or not to_curr:
            messagebox.showwarning('Select currencies', 'Please select both From and To currencies')
            return

        # disable UI while fetching
        self.status_label.config(text='Converting...')
        threading.Thread(target=self.fetch_conversion, args=(amount, from_curr, to_curr), daemon=True).start()

    def fetch_conversion(self, amount, from_curr, to_curr):
        try:
            params = {'amount': amount, 'from': from_curr, 'to': to_curr}
            res = requests.get(CONVERT_URL, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()  # example: {'amount': 1.0, 'base': 'USD', 'date': '2023-10-10', 'rates': {'INR': 83.47}}

            # extract converted value
            rates = data.get('rates', {})
            converted = rates.get(to_curr)
            if converted is None:
                raise RuntimeError('Conversion rate not returned by API')

            text = f"{amount:.4f} {from_curr} = {converted:.4f} {to_curr}  (date: {data.get('date')})"

            def update_result():
                self.result_var.set(text)
                self.status_label.config(text='Ready')

            self.root.after(0, update_result)

        except Exception as e:
            def show_error():
                self.status_label.config(text='Ready')
                messagebox.showerror('Conversion Error', f'Could not convert currencies:\n{e}')

            self.root.after(0, show_error)


if __name__ == '__main__':
    root = Tk()
    app = CurrencyConverterApp(root)
    root.mainloop()
