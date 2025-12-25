import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import time
from json import JSONDecodeError

# ССЫЛКА НА ТВОЮ БАЗУ (ОБЯЗАТЕЛЬНО ЗАМЕНИ НА СВОЮ ИЗ FIREBASE)
FIREBASE_URL = "https://cassa-simulator-4-default-rtdb.firebaseio.com"

class ProductManager:
    def __init__(self, filename="products.json"):
        self.filename = filename
        self.products = self.load_products()
    
    def load_products(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, JSONDecodeError):
                return []
        return []

    def save_products(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=4, ensure_ascii=False)
    
    def add_product(self, name, price):
        product_id = max([p["id"] for p in self.products], default=0) + 1
        self.products.append({"id": product_id, "name": name, "price": float(price)})
        self.save_products()
        return product_id
    
    def delete_product(self, product_id):
        self.products = [p for p in self.products if p["id"] != product_id]
        self.save_products()

class CashRegisterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Кассовая система 2025")
        self.root.geometry("900x650")
        
        self.product_manager = ProductManager()
        self.cart = []
        self.total = 0
        self.terminal_id = "" 
        
        # Настройка стилей
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", foreground="white", background="#21a038", font=("Arial", 10, "bold"))
        self.style.map("Accent.TButton", background=[('active', '#1a752c')])

        self.setup_ui()
        self.update_products_list()

    def setup_ui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_frame, text="Связь с терминалом:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.term_entry = ttk.Entry(top_frame, width=15)
        self.term_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="Привязать", command=self.bind_terminal).pack(side=tk.LEFT)
        self.status_circle = tk.Canvas(top_frame, width=20, height=20, highlightthickness=0)
        self.status_circle.pack(side=tk.LEFT, padx=10)
        self.status_led = self.status_circle.create_oval(5, 5, 15, 15, fill="red")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        sales_frame = ttk.Frame(notebook)
        products_frame = ttk.Frame(notebook)
        
        notebook.add(sales_frame, text="Продажи")
        notebook.add(products_frame, text="Товары")
        
        self.setup_sales_tab(sales_frame)
        self.setup_products_tab(products_frame)
        
    def setup_sales_tab(self, parent):
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        products_tree_frame = ttk.Frame(left_frame)
        products_tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar = ttk.Scrollbar(products_tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.prod_tree = ttk.Treeview(products_tree_frame, columns=("name", "price"), yscrollcommand=scrollbar.set, show="headings")
        self.prod_tree.heading("name", text="Название")
        self.prod_tree.heading("price", text="Цена")
        self.prod_tree.column("name", width=200)
        self.prod_tree.column("price", width=100)
        self.prod_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.prod_tree.bind("<Double-1>", self.add_to_cart)
        scrollbar.config(command=self.prod_tree.yview)

        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5, ipadx=10)
        ttk.Label(right_frame, text="Корзина:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        cart_tree_frame = ttk.Frame(right_frame)
        cart_tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        cart_scrollbar = ttk.Scrollbar(cart_tree_frame)
        cart_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cart_tree = ttk.Treeview(cart_tree_frame, columns=("name", "total"), yscrollcommand=cart_scrollbar.set, show="headings")
        self.cart_tree.heading("name", text="Товар")
        self.cart_tree.heading("total", text="Сумма")
        self.cart_tree.column("name", width=150)
        self.cart_tree.column("total", width=80)
        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cart_scrollbar.config(command=self.cart_tree.yview)

        cart_buttons_frame = ttk.Frame(right_frame)
        cart_buttons_frame.pack(fill=tk.X, pady=5)
        ttk.Button(cart_buttons_frame, text="Очистить", command=self.clear_cart).pack(fill=tk.X)
        
        total_frame = ttk.Frame(right_frame)
        total_frame.pack(fill=tk.X, pady=10)
        self.total_label = ttk.Label(total_frame, text="ИТОГО: 0.00 ₽", font=("Arial", 16, "bold"), foreground="blue")
        self.total_label.pack(anchor=tk.E)
        
        ttk.Button(right_frame, text="ОПЛАТИТЬ НА ТЕРМИНАЛЕ", style="Accent.TButton", command=self.send_to_terminal).pack(fill=tk.X, ipady=10, pady=5)


    def setup_products_tab(self, parent):
        controls_frame = ttk.LabelFrame(parent, text="Управление товарами")
        controls_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(controls_frame, text="Название:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_entry = ttk.Entry(controls_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(controls_frame, text="Цена (₽):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.price_entry = ttk.Entry(controls_frame, width=15)
        self.price_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        self.add_button = ttk.Button(controls_frame, text="Добавить товар", command=self.add_product_gui)
        self.add_button.grid(row=0, column=2, padx=10, pady=5, rowspan=2, sticky=tk.NS)
        
        self.delete_button = ttk.Button(controls_frame, text="Удалить выбранный", command=self.delete_product_gui)
        self.delete_button.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky=tk.EW)

        products_list_frame = ttk.Frame(parent)
        products_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(products_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.manager_tree = ttk.Treeview(products_list_frame, columns=("id", "name", "price"), 
                                         yscrollcommand=scrollbar.set, show="headings")
        self.manager_tree.heading("id", text="ID")
        self.manager_tree.heading("name", text="Название")
        self.manager_tree.heading("price", text="Цена")
        self.manager_tree.column("id", width=50, stretch=tk.NO)
        self.manager_tree.column("name", width=250)
        self.manager_tree.column("price", width=100)
        self.manager_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.manager_tree.yview)

    def add_product_gui(self):
        name = self.name_entry.get()
        price_str = self.price_entry.get()
        try:
            price = float(price_str)
            if name and price > 0:
                self.product_manager.add_product(name, price)
                self.update_products_list()
                self.name_entry.delete(0, tk.END)
                self.price_entry.delete(0, tk.END)
            else:
                messagebox.showwarning("Ввод", "Введите корректные название и цену.")
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Цена должна быть числом.")

    def delete_product_gui(self):
        selected_item = self.manager_tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Выберите товар для удаления.")
            return

        item_values = self.manager_tree.item(selected_item, 'values')
        product_id = int(item_values[0])
        self.product_manager.delete_product(product_id)
        self.update_products_list()


    def update_products_list(self):
        for item in self.prod_tree.get_children(): self.prod_tree.delete(item)
        for item in self.manager_tree.get_children(): self.manager_tree.delete(item)
        
        for p in self.product_manager.products:
            self.prod_tree.insert("", "end", values=(p['name'], f"{p['price']} ₽"))
            self.manager_tree.insert("", "end", values=(p['id'], p['name'], f"{p['price']} ₽"))


    def add_to_cart(self, event):
        item = self.prod_tree.selection()
        values = self.prod_tree.item(item, "values")
        if not values: return

        name, price_str = values
        price = float(price_str.split()[0])
        
        self.cart.append({"name": name, "price": price})
        self.cart_tree.insert("", "end", values=(name, f"{price} ₽"))
        self.total += price
        self.total_label.config(text=f"ИТОГО: {self.total:.2f} ₽")

    def clear_cart(self):
        self.cart = []
        self.total = 0
        for item in self.cart_tree.get_children(): self.cart_tree.delete(item)
        self.total_label.config(text="ИТОГО: 0.00 ₽")

    def bind_terminal(self):
        self.terminal_id = self.term_entry.get()
        if len(self.terminal_id) >= 4:
            self.status_circle.itemconfig(self.status_led, fill="green")
            messagebox.showinfo("Готово", f"Касса привязана к терминалу {self.terminal_id}")
        else:
            messagebox.showerror("Ошибка", "Введите корректный ID с экрана терминала")

    def send_to_terminal(self):
        if not self.terminal_id:
            messagebox.showwarning("Внимание", "Сначала привяжите терминал (введите ID сверху)")
            return
        if self.total <= 0: return

        data = {
            "command": "PAY",
            "amount": self.total,
            "status": "waiting",
            "timestamp": time.time()
        }
        
        try:
            url = f"{FIREBASE_URL}/terminals/{self.terminal_id}.json"
            requests.put(url, json=data)
            
            threading.Thread(target=self.wait_for_pay_confirm, daemon=True).start()
            messagebox.showinfo("Терминал", "Чек отправлен. Ожидайте оплаты клиентом.")
        except Exception as e:
            messagebox.showerror("Ошибка сети", "Не удалось связаться с базой данных Firebase")

    def wait_for_pay_confirm(self):
        url = f"{FIREBASE_URL}/terminals/{self.terminal_id}/status.json"
        while True:
            try:
                response = requests.get(url).json()
                if response == "SUCCESS":
                    self.root.after(0, self.payment_done_ui)
                    requests.put(url, json="waiting") # Очищаем статус
                    break
            except: break
            time.sleep(2)

    def payment_done_ui(self):
        messagebox.showinfo("УСПЕХ", "Оплата получена! Печать чека...")
        self.clear_cart()

if __name__ == "__main__":
    if not os.path.exists("products.json"):
        with open("products.json", "w", encoding='utf-8') as f:
            json.dump([{"id": 1, "name": "Бургер Тестовый", "price": 100.0}, {"id": 2, "name": "Кофе", "price": 50.0}], f)
            
    root = tk.Tk()
    app = CashRegisterApp(root)
    root.mainloop()