import logging
from pathlib import Path
from src.pdf_processor import PDFProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def process_single_invoice(pdf_path: str) -> None:
    """Process a single invoice PDF and print results"""
    processor = PDFProcessor()
    
    try:
        results = processor.extract_invoice_data(pdf_path)
        
        if results.get('is_valid', True):
            print("\nSuccessfully extracted invoice data:")
            for field, value in results.items():
                print(f"{field}: {value}")
        else:
            print("\nValidation errors occurred:")
            for error in results.get('errors', []):
                print(f"- {error}")
            print("\nWarnings:")
            for warning in results.get('warnings', []):
                print(f"- {warning}")
            
    except Exception as e:
        print(f"Error processing invoice: {str(e)}")

def process_invoice_batch(directory: str) -> None:
    """Process all PDFs in a directory"""
    processor = PDFProcessor()
    
    try:
        results = processor.process_batch(directory)
        
        print(f"\nProcessed {len(results)} files:")
        for result in results:
            print(f"\nFile: {result['filename']}")
            if result.get('is_valid', True):
                print("Status: Valid")
                print("Extracted data:")
                for field, value in result.items():
                    if field not in ['filename', 'is_valid']:
                        print(f"  {field}: {value}")
            else:
                print("Status: Invalid")
                print("Errors:")
                for error in result.get('errors', []):
                    print(f"  - {error}")
                
    except Exception as e:
        print(f"Error processing batch: {str(e)}")

if __name__ == "__main__":
    # Example usage
    # Process single invoice
    invoice_path = "path/to/your/invoice.pdf"
    if Path(invoice_path).exists():
        process_single_invoice(invoice_path)
    
    # Process batch of invoices
    invoice_directory = "path/to/invoice/directory"
    if Path(invoice_directory).exists():
        process_invoice_batch(invoice_directory)