import sys
import sqlite3
import os
import datetime
from PyQt6.QtCore import QRegularExpression, QDate
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFileDialog, QDateEdit
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


class BillEntrySystem(QWidget):
    def __init__(self):
        super().__init__()

        print("Window Initialized")  # Ensure the initialization happens
        self.setWindowTitle("Bill Entry System")
        self.setGeometry(100, 100, 600, 400)

        self.init_db()
        self.init_ui()

        # Load data from the database when the app starts
        self.load_data_from_db()

    def init_db(self):
        """Initialize SQLite Database"""
        if getattr(sys, 'frozen', False):
            # Running as a packaged .exe
            app_data_path = os.getenv('APPDATA')
            db_folder = os.path.join(app_data_path, 'BillEntryApp')

            if not os.path.exists(db_folder):
                os.makedirs(db_folder)

            db_path = os.path.join(db_folder, 'bill_entries.db')
            print(f"Using packaged app database path: {db_path}")
        else:
            # Running in development mode
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bill_entries.db')
            print(f"Using development mode database path: {db_path}")

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS bill (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                item_name TEXT,
                                quantity REAL,
                                price REAL,
                                total REAL,
                                date TEXT)''')
        self.conn.commit()

    def load_data_from_db(self):
        """Load the saved data from the database into the table"""
        self.cursor.execute("SELECT item_name, quantity, price, total, date FROM bill")
        rows = self.cursor.fetchall()

        for row in rows:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            for col, value in enumerate(row):
                self.table.setItem(row_position, col, QTableWidgetItem(str(value)))

        self.calculate_total()

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
        self.price_input = self.create_input_layout(entry_layout, "Price:", price_validator)

        # Date input field (default to current date)
        self.date_input = QDateEdit(QDate.currentDate())  # Default to the current date
        self.date_input.setDisplayFormat("dd-MM-yyyy")  # Set format to dd-MM-yyyy
        self.date_input.setCalendarPopup(True)

        # Set minimum date to the current date to prevent future dates
        today = QDate.currentDate()
        self.date_input.setMinimumDate(today)  # No future date selection

        entry_layout.addWidget(QLabel("Date:"))
        entry_layout.addWidget(self.date_input)

        # Action Buttons (Add, Remove, Clear, Download)
        action_layout = self.create_action_buttons()

        # Table for displaying items
        self.table = self.create_table_widget()

        # Total Label and Calculation Button
        self.total_label = QLabel("Total: ₹0.00")
        self.total_in_words_label = QLabel("Total in Words: Zero Rupees")

        main_layout.addLayout(entry_layout)
        main_layout.addLayout(action_layout)
        main_layout.addWidget(self.table)
        main_layout.addWidget(self.total_label)
        main_layout.addWidget(self.total_in_words_label)

        self.setLayout(main_layout)

        # Connect field changes to the function that checks validity
        self.item_input.textChanged.connect(self.check_fields)
        self.quantity_input.textChanged.connect(self.check_fields)
        self.price_input.textChanged.connect(self.check_fields)

    def create_input_layout(self, layout, label_text, validator=None):
        """Helper function to create a labeled input field with optional validator"""
        label = QLabel(label_text)
        input_field = QLineEdit()
        if validator:
            input_field.setValidator(validator)
        layout.addWidget(label)
        layout.addWidget(input_field)
        return input_field

    def create_action_buttons(self):
        """Create action buttons layout (Add, Remove, Clear, Download)"""
        action_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Item")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self.add_item)
        self.add_button.clicked.connect(self.calculate_total)

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
        table.setColumnCount(5)  # Added an extra column for the date
        table.setHorizontalHeaderLabels(["Item Name", "Quantity", "Price", "Total", "Date"])
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

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
        date = self.date_input.date().toString("dd-MM-yyyy")  # Get the selected date in dd-MM-yyyy format

        if item_name and quantity > 0 and price > 0:
            total = quantity * price
            self.save_item_to_db(item_name, quantity, price, total, date)

    def save_item_to_db(self, item_name, quantity, price, total, date):
        """Save the item to the database and update the table"""
        self.cursor.execute("INSERT INTO bill (item_name, quantity, price, total, date) VALUES (?, ?, ?, ?, ?) ",
                            (item_name, quantity, price, total, date))
        self.conn.commit()

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        self.table.setItem(row_position, 0, QTableWidgetItem(item_name))
        self.table.setItem(row_position, 1, QTableWidgetItem(str(quantity)))
        self.table.setItem(row_position, 2, QTableWidgetItem(str(price)))
        self.table.setItem(row_position, 3, QTableWidgetItem(str(total)))
        self.table.setItem(row_position, 4, QTableWidgetItem(date))

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
        self.total_label.setText("Total: ₹0.00")
        self.total_in_words_label.setText("Total in Words: Zero Rupees")

    def calculate_total(self):
        total = sum(float(self.table.item(row, 3).text()) for row in range(self.table.rowCount()))
        total_in_words = self.convert_currency_to_words(total)
        self.total_label.setText(f"Total: ₹{total:,.2f}")
        self.total_in_words_label.setText(f"Total in Words: {total_in_words}")

    def download_pdf(self):
        """Download the table data as a PDF file with the current date as header"""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if file_name:
            document = SimpleDocTemplate(file_name, pagesize=A4)
            data = [
                [Paragraph("<b>Item Name</b>", getSampleStyleSheet()['Heading4']),
                 Paragraph("<b>Quantity</b>", getSampleStyleSheet()['Heading4']),
                 Paragraph("<b>Price</b>", getSampleStyleSheet()['Heading4']),
                 Paragraph("<b>Total</b>", getSampleStyleSheet()['Heading4']),
                 Paragraph("<b>Date</b>", getSampleStyleSheet()['Heading4'])]
            ]

            # Populate the table with data from the QTableWidget
            for row in range(self.table.rowCount()):
                data.append([self.table.item(row, col).text() for col in range(5)])

            table = Table(data)
            
            # Adding padding and style to the table
            table.setStyle(TableStyle([ 
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center-align the whole table
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('GRID', (0, 0), (-1, -1), 0.5, (0, 0, 0)),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center the header row
                ('TOPPADDING', (0, 0), (-1, 0), 12),  # Add space above the table
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),  # Add space below the table
            ]))

            total = sum(float(self.table.item(row, 3).text()) for row in range(self.table.rowCount()))
            total_in_words = self.convert_currency_to_words(total)

            total_numeric = f"Total: {total:,.2f}"
            styles = getSampleStyleSheet()

            total_paragraph = Paragraph(f"<b>{total_numeric}</b>", styles['Normal'])
            total_in_words_paragraph = Paragraph(f"<b>Total in Words:</b> {total_in_words}", styles['Normal'])

            current_date = datetime.datetime.now().strftime("%B %d, %Y")
            date_paragraph = Paragraph(f"<b>Date: {current_date}</b>", styles['Normal'])

            document.build([date_paragraph, table, total_paragraph, total_in_words_paragraph])

            print(f"PDF saved to {file_name}")

    def closeEvent(self, event):
        """Close the connection and ensure the thread is properly terminated"""
        self.conn.close()
        event.accept()

    def convert_currency_to_words(self, amount):
        """Convert a numeric amount to words (Indian numbering system)"""
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
                "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

        def convert_two_digits(n):
            """Convert a number less than 100 to words"""
            if n == 0:
                return ""
            elif n < 20:
                return units[n]
            else:
                return tens[n // 10] + ('' if n % 10 == 0 else ' ' + units[n % 10])

        def convert_three_digits(n):
            """Convert a number less than 1000 to words"""
            if n == 0:
                return ""
            elif n < 100:
                return convert_two_digits(n)
            else:
                return units[n // 100] + " Hundred" + ('' if n % 100 == 0 else ' ' + convert_two_digits(n % 100))

        def num_to_words(n):
            """Convert a number to words for Indian currency system"""
            if n == 0:
                return "Zero"

            crore = n // 10000000
            n %= 10000000

            lakh = n // 100000
            n %= 100000

            thousand = n // 1000
            n %= 1000

            hundred = n

            words = []
            if crore > 0:
                words.append(convert_two_digits(crore) + " Crore")
            if lakh > 0:
                words.append(convert_two_digits(lakh) + " Lakh")
            if thousand > 0:
                words.append(convert_two_digits(thousand) + " Thousand")
            if hundred > 0:
                words.append(convert_three_digits(hundred))

            return ' '.join(words).strip()

        rupees = int(amount)
        paise = round((amount - rupees) * 100)

        rupees_in_words = num_to_words(rupees)

        if paise > 0:
            paise_in_words = num_to_words(paise)
            return f"{rupees_in_words} Rupees and {paise_in_words} Paise"
        else:
            return f"{rupees_in_words} Rupees"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BillEntrySystem()
    window.show()
    sys.exit(app.exec())
