import sqlite3

class POS_System:
    def __init__(self, db_name="pos_system.db"):
        self.db_name = db_name
        self.cart = {} # Format: {product_id: {"name": x, "price": y, "qty": z}}
    
    def _get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def get_all_products(self):
        """Fetch and return all products from the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        conn.close()
        return products
    
    def add_to_cart(self, product_id, quantity):
        """Adds an item to the active cart if stock is available."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, stock FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()

        if not product:
            print("Product not found.")
            return False
        
        name, price, stock = product

        # Check if we already have some in the cart
        current_cart_qty = self.cart.get(product_id, {}).get("qty", 0)
        total_requested = current_cart_qty + quantity

        if total_requested > stock:
            print(current_cart_qty)
            print(f"Insufficient stock! Only {stock} available (You already have {current_cart_qty} in cart.)")
            return False
        
        if product_id in self.cart:
            self.cart[product_id]["qty"] += quantity
        else:
            self.cart[product_id] = {"name": name, "price": price, "qty": quantity}

        print(f"Added {quantity}x {name} to cart.")
        return True
    
    def show_cart(self):
        """Displays current items in the cart."""
        if not self.cart:
            print("\n Your cart is empty.")
            return 0

        print("\n--- Current Cart---")
        total = 0
        for p_id, item in self.cart.items():
            subtotal = item["price"] * item["qty"]
            total += subtotal
            print(f"ID: {p_id} | {item['name']} | {item['qty']}x @ ${item['price']:.2f} = ${subtotal:.2f}")
        print(f"Total: ${total:.2f}")
        print("--------------------")
        return total
    
    def checkout(self):
        """Processes the sale, updates database stock, and clears the cart."""
        if not self.cart:
            print("Cart is empty. Nothing to checkout.")
            return
        
        total_amount = sum(item["price"] * item["qty"] for item in self.cart.values())

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 1. Insert into Sales Table
            cursor.execute("INSERT INTO sales (total_amount) VALUES (?)", (total_amount,))
            sale_id = cursor.lastrowid

            # 2. Insert into Sale Items & Update Stock
            for product_id, item in self.cart.items():
                # Insert sale item record
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale)
                    VALUES (?, ?, ?, ?)
                ''', (sale_id, product_id, item["qty"], item["price"]))

                # Deduct stock
                cursor.execute('''
                    UPDATE products
                    SET stock = stock - ?
                    WHERE id = ?
                ''', (item["qty"], product_id))

            conn.commit()
            print(f"\n Transaction Succesful! Total Paid: ${total_amount:.2f}")
            self.cart.clear() # Reset cart

        except sqlite3.Error as e:
            conn.rollback()
            print(f"Transaction faile: {e}")
        finally:
            conn.close()

    def get_sales_report(self):
        '''Fetches total revenue and sales history.'''
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(total_amount) FROM sales")
        total_rev = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT * FROM sales ORDER BY timestamp DESC")
        all_sales = cursor.fetchall()
        conn.close()

        return total_rev, all_sales
    
    def remove_from_cart(self, product_id):
        """Removes an item completely from the cart."""
        if product_id in self.cart:
            removed_item = self.cart.pop(product_id)
            print(f"Removed {removed_item['name']} from cart.")
            return True
        return False
    
    def get_product_by_barcode(self, barcode_str):
        """Fetches product details based on a scanned barcode."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products WHERE barcode = ?", (barcode_str,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None