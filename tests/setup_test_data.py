import shutil
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_sample_invoice(output_path: Path, invoice_type: str):
    """Create a sample invoice PDF for testing"""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    if invoice_type == "standard":
        c.drawString(100, 750, "STANDARD INVOICE")
        c.drawString(100, 700, "Invoice Number: INV-001")
        c.drawString(100, 650, "Amount: $1,234.56")
        c.drawString(100, 600, "Date: 2024-03-20")
        
    elif invoice_type == "international":
        c.drawString(100, 750, "INTERNATIONAL INVOICE")
        c.drawString(100, 700, "Invoice Number: INV-002")
        c.drawString(100, 650, "Amount: €1.234,56")
        c.drawString(100, 600, "Date: 20-03-2024")
        
    elif invoice_type == "handwritten":
        # Simulate handwritten text using a different font
        c.setFont("Courier", 12)
        c.drawString(100, 750, "HANDWRITTEN INVOICE")
        c.drawString(100, 700, "Invoice #: INV-003")
        c.drawString(100, 650, "Amount: $789.00")
        c.drawString(100, 600, "Date: 03/20/2024")
    
    c.save()

def setup_test_data():
    """Set up test data directory with sample invoices"""
    test_data_dir = Path(__file__).parent / "test_data" / "invoices"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample invoices for each type
    invoice_types = ["standard", "international", "handwritten"]
    for invoice_type in invoice_types:
        type_dir = test_data_dir / invoice_type
        type_dir.mkdir(exist_ok=True)
        
        sample_path = type_dir / f"sample_{invoice_type}.pdf"
        create_sample_invoice(sample_path, invoice_type)
    
    # Create test cases for error handling
    corrupted_path = test_data_dir / "corrupted.pdf"
    with open(corrupted_path, 'wb') as f:
        f.write(b'This is not a valid PDF file')
    
    empty_path = test_data_dir / "empty.pdf"
    canvas.Canvas(str(empty_path), pagesize=letter).save()

if __name__ == "__main__":
    setup_test_data()
