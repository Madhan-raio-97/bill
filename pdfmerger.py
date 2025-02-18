import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QListWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from PyPDF2 import PdfMerger

class PDFMergerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Merger")
        self.setGeometry(100, 100, 600, 300)
        
        self.layout = QVBoxLayout()
        
        self.label = QLabel("No PDF files selected.")
        self.layout.addWidget(self.label)
        
        self.select_button = QPushButton("Select PDF Files")
        self.select_button.clicked.connect(self.select_pdfs)
        self.layout.addWidget(self.select_button)
        
        # QListWidget to display selected PDFs
        self.pdf_list_widget = QListWidget()
        self.layout.addWidget(self.pdf_list_widget)
        
        # Add buttons for reordering and removing PDFs
        self.button_layout = QHBoxLayout()
        self.remove_button = QPushButton("Remove Selected PDF")
        self.remove_button.clicked.connect(self.remove_pdf)
        self.button_layout.addWidget(self.remove_button)
        
        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.clicked.connect(self.move_up)
        self.button_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.clicked.connect(self.move_down)
        self.button_layout.addWidget(self.move_down_button)
        
        self.layout.addLayout(self.button_layout)
        
        self.merge_button = QPushButton("Merge PDFs")
        self.merge_button.clicked.connect(self.merge_pdfs)
        self.merge_button.setEnabled(False)  # Disable until files are selected
        self.layout.addWidget(self.merge_button)
        
        self.setLayout(self.layout)
        
        self.pdf_files = []

    def select_pdfs(self):
        # Open a file dialog to select one or multiple PDFs
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDFs", "", "PDF Files (*.pdf)")
        
        if files:
            self.pdf_files.extend(files)  # Add the newly selected files to the list
            self.update_pdf_list_widget()
            self.merge_button.setEnabled(True)

    def update_pdf_list_widget(self):
        """Update the QListWidget with the selected PDFs."""
        self.pdf_list_widget.clear()
        self.pdf_list_widget.addItems(self.pdf_files)

    def remove_pdf(self):
        """Remove selected PDF from the list."""
        selected_items = self.pdf_list_widget.selectedItems()
        if selected_items:
            for item in selected_items:
                self.pdf_files.remove(item.text())
                self.pdf_list_widget.takeItem(self.pdf_list_widget.row(item))
            if not self.pdf_files:
                self.merge_button.setEnabled(False)  # Disable merge button if no files are selected

    def move_up(self):
        """Move the selected PDF up in the list."""
        selected_items = self.pdf_list_widget.selectedItems()
        if selected_items:
            for item in selected_items:
                row = self.pdf_list_widget.row(item)
                if row > 0:
                    # Swap items in the list widget
                    self.pdf_files[row], self.pdf_files[row - 1] = self.pdf_files[row - 1], self.pdf_files[row]
                    self.update_pdf_list_widget()

    def move_down(self):
        """Move the selected PDF down in the list."""
        selected_items = self.pdf_list_widget.selectedItems()
        if selected_items:
            for item in selected_items:
                row = self.pdf_list_widget.row(item)
                if row < len(self.pdf_files) - 1:
                    # Swap items in the list widget
                    self.pdf_files[row], self.pdf_files[row + 1] = self.pdf_files[row + 1], self.pdf_files[row]
                    self.update_pdf_list_widget()

    def merge_pdfs(self):
        if not self.pdf_files:
            return
        
        # Ask user where to save the merged PDF
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "", "PDF Files (*.pdf)")
        
        if save_path:
            # Merge the selected PDFs
            merger = PdfMerger()
            for pdf in self.pdf_files:
                merger.append(pdf)
            
            # Write the merged PDF to the selected path
            merger.write(save_path)
            merger.close()
            
            self.label.setText(f"PDFs merged successfully!\nSaved to: {save_path}")
            self.pdf_files = []  # Clear the list after merging
            self.update_pdf_list_widget()  # Update the list widget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFMergerApp()
    window.show()
    sys.exit(app.exec())
