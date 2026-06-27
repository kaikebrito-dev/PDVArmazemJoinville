import sqlite3

def init_db():
    conn = sqlite3.connect("pos_system.db")
    cursor = conn.cursor()

    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')

    # Create Sales table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
            total_amount REAL NOT NULL
        )
    ''')

    # Create Sale Items table (Links sales to products)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price_at_sale REAL,
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Add sample products if table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ("7891234567890", "Coca-Cola Lata", 3.50, 100),
            ("7891234567891", "Gudang Garam Maço", 40, 50),
            ("7891234567892", "Skol", 3.00, 40),
            ("7891234567893", "Cinzeiro", 80, 20)
        ]
        cursor.executemany("INSERT INTO products (barcode, name, price, stock) VALUES (?, ?, ?, ?)", sample_products)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")