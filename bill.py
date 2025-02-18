import sys
import sqlite3
import os
from PyQt6.QtCore import QRegularExpression, QTimer
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFileDialog
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import inflect

# Initialize inflect engine for converting numbers to words
p = inflect.engine()

class BillEntrySystem(QWidget):
    def __init__(self):
        super().__init__()
        
        print("Window Initialized")  # Ensure the initialization happens
        self.setWindowTitle("Bill Entry System")
        self.setGeometry(100, 100, 600, 400)

        self.init_db()
        self.init_ui()

        # Timer for price input formatting
        self.price_format_timer = QTimer(self)
        self.price_format_timer.setSingleShot(True)  # Execute only once after the delay
        self.price_format_timer.timeout.connect(self.format_price)

    def init_db(self):
        """Initialize SQLite Database"""
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bill_entries.db')
        print(f"Database Path: {db_path}")  # Debugging database path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS bill (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                item_name TEXT,
                                quantity REAL,
                                price REAL,
                                total REAL)''')
        self.conn.commit()

    def init_ui(self):
        """Initialize the User Interface"""
        main_layout = QVBoxLayout()

        # Bill Entry Layout (For item name, quantity, price)
        entry_layout = QHBoxLayout()
        self.item_input = self.create_input_layout(entry_layout, "Item Name:")
        
        # Corrected the Quantity validator regex
        quantity_validator = QRegularExpressionValidator(QRegularExpression(r"^\d{1,3}(\.\d{1,2})?$"))
        self.quantity_input = self.create_input_layout(entry_layout, "Quantity:", quantity_validator)
        
        # Corrected the Price validator regex
        price_validator = QRegularExpressionValidator(QRegularExpression(r"^\d{1,8}(\.\d{1,2})?$"))
        self.price_input = self.create_input_layout(entry_layout, "Price:", price_validator, self.on_price_input_changed)

        # Action Buttons (Add, Remove, Clear, Download)
        action_layout = self.create_action_buttons()

        # Table for displaying items
        self.table = self.create_table_widget()

        # Total Label and Calculation Button
        self.total_label = QLabel("Total: $0.00")
        self.calculate_button = QPushButton("Calculate Total")
        self.calculate_button.clicked.connect(self.calculate_total)

        main_layout.addLayout(entry_layout)
        main_layout.addLayout(action_layout)
        main_layout.addWidget(self.table)
        main_layout.addWidget(self.total_label)
        main_layout.addWidget(self.calculate_button)

        self.setLayout(main_layout)

        # Connect field changes to the function that checks validity
        self.item_input.textChanged.connect(self.check_fields)
        self.quantity_input.textChanged.connect(self.check_fields)
        self.price_input.textChanged.connect(self.check_fields)

    def create_input_layout(self, layout, label_text, validator=None, text_changed_func=None):
        """Helper function to create a labeled input field with optional validator and textChanged function"""
        label = QLabel(label_text)
        input_field = QLineEdit()
        if validator:
            input_field.setValidator(validator)
        if text_changed_func:
            input_field.textChanged.connect(text_changed_func)
        layout.addWidget(label)
        layout.addWidget(input_field)
        return input_field

    def create_action_buttons(self):
        """Create action buttons layout (Add, Remove, Clear, Download)"""
        action_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Item")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self.add_item)

        self.remove_button = QPushButton("Remove Item")
        self.remove_button.clicked.connect(self.remove_item)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_all)

        self.download_pdf_button = QPushButton("Download as PDF")
        self.download_pdf_button.clicked.connect(self.download_pdf)

        action_layout.addWidget(self.add_button)
        action_layout.addWidget(self.remove_button)
        action_layout.addWidget(self.clear_button)
        action_layout.addWidget(self.download_pdf_button)

        return action_layout

    def create_table_widget(self):
        """Create table for displaying the items"""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Item Name", "Quantity", "Price", "Total"])
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def on_price_input_changed(self):
        """Trigger format after a delay"""
        self.price_format_timer.stop()
        self.price_format_timer.start(500)  # 500 ms delay

    def format_price(self):
        """Format price with commas as the user types"""
        text = self.price_input.text().replace(",", "")
        try:
            value = float(text)
            formatted_value = "{:,.2f}".format(value)
            self.price_input.setText(formatted_value)
            self.price_input.setCursorPosition(len(formatted_value))  # Keep the cursor at the end
        except ValueError:
            self.price_input.setText("")  # Clear if invalid

    def check_fields(self):
        """Check if all fields are valid, and enable the 'Add Item' button"""
        item_name = self.item_input.text().strip()
        try:
            quantity = float(self.quantity_input.text().strip() or 1)  # Default to 1 if empty
            price = float(self.price_input.text().replace(",", ""))  # Clean price input
        except ValueError:
            self.add_button.setEnabled(False)
            return
        
        if item_name and quantity > 0 and price > 0:
            self.add_button.setEnabled(True)
        else:
            self.add_button.setEnabled(False)

    def add_item(self):
        item_name = self.item_input.text()
        quantity = float(self.quantity_input.text().strip() or 1)
        price = float(self.price_input.text().replace(",", ""))

        if item_name and quantity > 0 and price > 0:
            total = quantity * price
            self.save_item_to_db(item_name, quantity, price, total)

    def save_item_to_db(self, item_name, quantity, price, total):
        """Save the item to the database and update the table"""
        self.cursor.execute("INSERT INTO bill (item_name, quantity, price, total) VALUES (?, ?, ?, ?)",
                            (item_name, quantity, price, total))
        self.conn.commit()

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        self.table.setItem(row_position, 0, QTableWidgetItem(item_name))
        self.table.setItem(row_position, 1, QTableWidgetItem(str(quantity)))
        self.table.setItem(row_position, 2, QTableWidgetItem(str(price)))
        self.table.setItem(row_position, 3, QTableWidgetItem(str(total)))

        # Clear input fields
        self.item_input.clear()
        self.quantity_input.clear()
        self.price_input.clear()
        self.add_button.setEnabled(False)

    def remove_item(self):
        """Remove the selected item from the table and database"""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            item_id = self.table.item(selected_row, 0).text()
            self.cursor.execute("DELETE FROM bill WHERE item_name=?", (item_id,))
            self.conn.commit()

            self.table.removeRow(selected_row)

    def clear_all(self):
        """Clear all items from the table and database"""
        self.cursor.execute("DELETE FROM bill")
        self.conn.commit()
        self.table.setRowCount(0)
        self.total_label.setText("Total: $0.00")

    def calculate_total(self):
        total = sum(float(self.table.item(row, 3).text()) for row in range(self.table.rowCount()))
        self.total_label.setText(f"Total: ₹{total:,.2f}")

    def download_pdf(self):
        """Download the table data as a PDF file"""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if file_name:
            document = SimpleDocTemplate(file_name, pagesize=A4)
            data = [["Item Name", "Quantity", "Price", "Total"]]

            for row in range(self.table.rowCount()):
                data.append([self.table.item(row, col).text() for col in range(4)])

            table = Table(data)
            table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')]))

            # Add total in words at the end of the PDF
            total = sum(float(self.table.item(row, 3).text()) for row in range(self.table.rowCount()))
            total_in_words = self.convert_currency(total)
            styles = getSampleStyleSheet()
            total_in_words_paragraph = Paragraph(f"<b>Total in Words:</b> {total_in_words}", styles['Normal'])
            
            # Build the PDF document with the table and the total in words
            document.build([table, total_in_words_paragraph])

            print(f"PDF saved to {file_name}")

    def closeEvent(self, event):
        """Close the connection and ensure the thread is properly terminated"""
        self.conn.close()
        event.accept()

    def convert_currency(self, amount):
        # Split the amount into rupees and paise
        rupees = int(amount)
        paise = round((amount - rupees) * 100)

        # Convert the rupees part to words
        rupees_in_words = p.number_to_words(rupees)

        # Convert the paise part to words, if any
        if paise > 0:
            paise_in_words = p.number_to_words(paise)
            return f"{rupees_in_words} Rupees and {paise_in_words} Paise"
        else:
            return f"{rupees_in_words} Rupees"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BillEntrySystem()
    window.show()
    sys.exit(app.exec())
