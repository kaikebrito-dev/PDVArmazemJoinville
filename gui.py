import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QMessageBox, QSpinBox, QStackedWidget, QShortcut
    )
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt
from pos import POS_System
from database import init_db

class POS_App(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db() # Ensure DB is ready
        self.pos = POS_System()
        self.barcode_buffer = ""

        self.setWindowTitle("Armazém Joinville")
        self.setGeometry(100, 100, 1024, 600)

        self.central_stacked = QStackedWidget()
        self.setCentralWidget(self.central_stacked)

        self.create_main_menu()
        self.create_pos_page()
        self.create_stock_page()
        self.create_reports_page()

        self.setup_shortcuts()

        self.central_stacked.setCurrentIndex(0)

    def create_main_menu(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Armazém Joinville")
        title.setStyleSheet("font-size: 32px; font-weight: bold; margin-bottom: 40px; color: #2c3e50;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # Menu Navigation Buttons
        btn_pos = QPushButton("Ponto de Venda")
        btn_stock = QPushButton("Estoque")
        btn_reports = QPushButton("Relatório de Vendas")

        # Design system for menu buttons
        btn_style = "font-size: 18px; font-weight: bold; padding: 15px; width: 300px; margin: 10px; background-color: #34495e; color: white; border-radius: 5px;"
        for btn in [btn_pos, btn_stock, btn_reports]:
            btn.setStyleSheet(btn_style)
            layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        # Connect buttons to change page index
        btn_pos.clicked.connect(lambda: self.central_stacked.setCurrentIndex(1))
        btn_stock.clicked.connect(lambda: [self.load_stock_inventory(), self.central_stacked.setCurrentIndex(2)])
        btn_reports.clicked.connect(lambda: [self.load_sales_reports(), self.central_stacked.setCurrentIndex(3)])

        self.central_stacked.addWidget(page)

    def setup_shortcuts(self):
# Confirm checkout
        self.checkout_shortcut = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.checkout_shortcut.activated.connect(self.handle_shortcut_checkout)
# Remove item
        self.remove_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.remove_shortcut.activated.connect(self.handle_remove_item)
# Back to menu
        self.back_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.back_shortcut.activated.connect(self.go_to_main_menu)

    def handle_shortcut_checkout(self):
        if self.central_stacked.currentIndex() == 1:
            self.handle_checkout()

    def go_to_main_menu(self):
        self.central_stacked.setCurrentIndex(0)
# ================= 1. Point OF SALE PAGE =================

    def create_pos_page(self):
        page = QWidget()
        main_layout = QHBoxLayout(page)

        # Left panel (Catalog)
        left_panel = QVBoxLayout()
        left_title = QHBoxLayout()
        lbl = QLabel("Catálogo de Produtos")
        lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        btn_back = QPushButton("Voltar ao Menu")
        btn_back.clicked.connect(lambda: self.central_stacked.setCurrentIndex(0))
        left_title.addWidget(lbl)
        left_title.addWidget(btn_back, alignment=Qt.AlignRight)
        left_panel.addLayout(left_title)

        self.prod_table = QTableWidget(0, 5)
        self.prod_table.setHorizontalHeaderLabels(["ID", "Código de Barras", "Nome do Produto", "Preço", "Estoque"])
        self.prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.prod_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.prod_table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_panel.addWidget(self.prod_table)

        # Barcode Entry Bar
        scan_bar_layout = QHBoxLayout()
        scan_bar_layout.addWidget(QLabel("Código de barras:"))
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Digite o código aqui e pressione Enter:....")
        self.scan_input.returnPressed.connect(self.handle_manual_scan)
        scan_bar_layout.addWidget(self.scan_input)
        left_panel.addLayout(scan_bar_layout)

        # Quantity Selector and Add Button
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantidade para adicionar:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setValue(1)
        qty_layout.addWidget(self.qty_spin)

        add_btn = QPushButton("Adicionar ao Carrinho")
        add_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 8px;")
        add_btn.clicked.connect(self.handle_add_to_cart)
        qty_layout.addWidget(add_btn)
        left_panel.addLayout(qty_layout)

# ================= RIGHT PANEL: CART & CHECKOUT =================

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Compra Atual"), alignment=Qt.AlignLeft)

        self.cart_table = QTableWidget(0, 5)
        self.cart_table.setHorizontalHeaderLabels(["ID", "Item", "Quantidade", "Preço", "Subtotal"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.setColumnHidden(0, True)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_panel.addWidget(self.cart_table)

        # Remove Button
        remove_btn = QPushButton("Remover o Item Selecionado")
        remove_btn.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 6px;")
        remove_btn.clicked.connect(self.handle_remove_item)
        right_panel.addWidget(remove_btn)

        # Total Display
        self.total_label = QLabel("Total: R$0.00")
        self.total_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #e74c3c; margin: 15px 0;")
        right_panel.addWidget(self.total_label, alignment=Qt.AlignRight)

        # Checkout Button
        checkout_btn = QPushButton("Concluir Venda")
        checkout_btn.setStyleSheet("background-color: #3498db; color: white; font-size: 16px; font-weight: bold; padding: 12px;")
        checkout_btn.clicked.connect(self.handle_checkout)
        right_panel.addWidget(checkout_btn)

        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addLayout(right_panel, stretch=1)

        self.central_stacked.addWidget(page)
        self.load_products()

# ================= 2. STOCK MANAGEMENT PAGE =================

    def create_stock_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        header = QHBoxLayout()
        title = QLabel("Inventário e Gerenciamento de Estoque")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        btn_back = QPushButton("Voltar ao Menu")
        btn_back.clicked.connect(lambda: self.central_stacked.setCurrentIndex(0))
        header.addWidget(title)
        header.addWidget(btn_back, alignment=Qt.AlignRight)
        layout.addLayout(header)

        self.stock_table = QTableWidget(0, 4)
        self.stock_table.setHorizontalHeaderLabels(["ID", "Código de Barras", "Nome do Produto", "Preço", "Estoque Atual"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stock_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.stock_table)

        self.central_stacked.addWidget(page)

    def load_stock_inventory(self):
        """Refreshes inventory overview."""
        self.stock_table.setRowCount(0)
        for row_idx, (p_id, barcode, name, price, stock) in enumerate(self.pos.get_all_products()):
            self.stock_table.insertRow(row_idx)
            self.stock_table.setItem(row_idx, 0, QTableWidgetItem(str(p_id)))
            self.stock_table.setItem(row_idx, 1, QTableWidgetItem(str(barcode)))
            self.stock_table.setItem(row_idx, 2, QTableWidgetItem(name))
            self.stock_table.setItem(row_idx, 3, QTableWidgetItem(f"R${price:.2f}"))
            self.stock_table.setItem(row_idx, 4, QTableWidgetItem(str(stock)))

# ================= 3. SALES REPORTS PAGE =================
    def create_reports_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        header = QHBoxLayout()
        title = QLabel("Relatório de Vendas")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        btn_back = QPushButton("Voltar ao Menu")
        btn_back.clicked.connect(lambda: self.central_stacked.setCurrentIndex(0))
        header.addWidget(title)
        header.addWidget(btn_back, alignment=Qt.AlignRight)
        layout.addLayout(header)

        self.revenue_label = QLabel("Total Bruto Acumulado: R$0.00")
        self.revenue_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60: margin:10 px 0;")
        layout.addWidget(self.revenue_label)

        self.report_table = QTableWidget(0, 3)
        self.report_table.setHorizontalHeaderLabels(["ID da Compra", "Data", "Valor"])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.report_table)

        self.central_stacked.addWidget(page)

    def load_sales_reports(self):
        """Queries the SQLite database through the POS backend to display financials."""
        self.report_table.setRowCount(0)
        total_rev, history = self.pos.get_sales_report()

        self.revenue_label.setText(f"Total de Renda Acumulada: R${total_rev:.2f}")
        for row_idx, (s_id, timestamp, total) in enumerate(history):
            self.report_table.insertRow(row_idx)
            self.report_table.setItem(row_idx, 0, QTableWidgetItem(str(s_id)))
            self.report_table.setItem(row_idx, 1, QTableWidgetItem(str(timestamp)))
            self.report_table.setItem(row_idx, 2, QTableWidgetItem(f"R${total:.2f}"))
    
    # ================= EXTRACTED PASSTHROUGH EVENT HANDLERS =================
    def load_products(self):
        self.prod_table.setRowCount(0)
        for row_idx, (p_id, barcode, name, price, stock) in enumerate(self.pos.get_all_products()):
            self.prod_table.insertRow(row_idx)
            self.prod_table.setItem(row_idx, 0, QTableWidgetItem(str(p_id)))
            self.prod_table.setItem(row_idx, 1, QTableWidgetItem(barcode))
            self.prod_table.setItem(row_idx, 2, QTableWidgetItem(name))
            self.prod_table.setItem(row_idx, 3, QTableWidgetItem(f"R${price:.2f}"))
            self.prod_table.setItem(row_idx, 4, QTableWidgetItem(str(stock)))

    def handle_manual_scan(self):
        barcode_text = self.scan_input.text().strip()
        if not barcode_text:
            return
        
        p_id = self.pos.get_product_by_barcode(barcode_text)
        if p_id and self.pos.add_to_cart(p_id, 1):
            self.update_cart_display()
            self.scan_input.clear()
        else:
            QMessageBox.warning(self, "ERRO", "Código de barras não reconhecido.")

    def handle_add_to_cart(self):
        selected_row = self.prod_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "ERRO", "Selecione um produto da lista primeiro")
            return
        
        p_id = int(self.prod_table.item(selected_row, 0).text())
        qty = self.qty_spin.value()

        # Call your existing pos.py backend logic!
        success = self.pos.add_to_cart(p_id, qty)
        if success:
            self.update_cart_display()
            self.qty_spin.setValue(1) # Reset spinbox

    def update_cart_display(self):
        self.cart_table.setRowCount(0)
        total = 0

        for row_idx, (p_id, item) in enumerate(self.pos.cart.items()):
            subtotal = item["price"] * item["qty"]
            total += subtotal

            self.cart_table.insertRow(row_idx)
            self.cart_table.setItem(row_idx, 0, QTableWidgetItem(str(p_id)))
            self.cart_table.setItem(row_idx, 1, QTableWidgetItem(item["name"]))
            self.cart_table.setItem(row_idx, 2, QTableWidgetItem(str(item["qty"])))
            self.cart_table.setItem(row_idx, 3, QTableWidgetItem(f"R${item['price']:.2f}"))
            self.cart_table.setItem(row_idx, 4, QTableWidgetItem(f"R${subtotal:.2f}"))
        self.total_label.setText(f"Total: ${total:.2f}")

    def handle_remove_item(self):
        """Finds selected row in the cart, extracts the hidden ID, and removes it."""
        selected_row = self.cart_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "ERRO", "Selecione um item para remover")
            return
        
        # Grab the hidden Product ID from column 0
        p_id = int(self.cart_table.item(selected_row, 0).text())

        # Call backend to drop it from dictionary
        if self.pos.remove_from_cart(p_id):
            self.update_cart_display()

    def handle_checkout(self):
        """Processes database transaction and clear the UI cart."""
        if not self.pos.cart:
            QMessageBox.warning(self, "Carrinho vazio", "Adicione um item")
            return
        
        reply = QMessageBox.question(self, "Confimar", "Completar venda?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.pos.checkout() # Existing database execution logic
            QMessageBox.information(self, "Sucesso", "Transação registrada com sucesso!")
            self.update_cart_display() # Clear cart UI
            self.load_products() # Refresh stock levels in product UI

    def keyPressEvent(self, event):
        """Captures hardware barcode scans typed directly to the window."""
        # 1. If 'Enter' or 'Return' is pressed, processing the accumulated barcode starts
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.barcode_buffer:
                self.process_barcode_scan(self.barcode_buffer)
                self.barcode_buffer = ""
        else:
            # 2. Otherwise, continuously collect typed numbers/letters into the buffer
            text = event.text()
            if text.isalnum(): # Filter out modifier keys like Shiift/Ctrl
                self.barcode_buffer += text

        # Always run the base key press event so normal widgets still work
        super().keyPressEvent(event)

    def process_barcode_scan(self, barcode_str):
        """Looks up the scanned barcode string and automatically updates the cart."""
        p_id = self.pos.get_product_by_barcode(barcode_str)

        if p_id:
            # Automatically add 1 item to the cart upon a succesful scan match
            success = self.pos.add_to_cart(p_id, quantity=1)
            if success:
                self.update_cart_display()
        else:
            # Optionally show an alert or play a sound error if product isn't found
            QMessageBox.warning(self, "ERRO", f"Produto não encontrado: {barcode_str}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POS_App()
    window.show()
    sys.exit(app.exec_())