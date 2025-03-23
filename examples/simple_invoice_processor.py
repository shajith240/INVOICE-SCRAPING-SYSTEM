import logging
import sys
from pathlib import Path

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.pdf_processor import PDFProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Use the sample invoice we just added
    invoice_path = Path("data/raw_invoices/sample_invoice.pdf")
    
    if not invoice_path.exists():
        logger.error(f"Invoice file not found at {invoice_path}")
        return
        
    logger.info(f"Starting to process invoice: {invoice_path}")
    
    # Create PDFProcessor instance
    processor = PDFProcessor()
    
    try:
        # Process the invoice
        result = processor.extract_invoice_data(str(invoice_path))
        
        # Check and display results
        if result.get('is_valid', True):
            logger.info("Invoice processed successfully!")
            print("\nExtracted Invoice Data:")
            print("-" * 40)
            
            # Format the output with proper currency symbols
            fields = ['invoice_number', 'date', 'total_amount', 'vendor', 'description']
            for field in fields:
                value = result.get(field, 'Not found')
                if field == 'total_amount' and value:
                    print(f"{field.replace('_', ' ').title()}: {value}€")
                else:
                    print(f"{field.replace('_', ' ').title()}: {value}")
        else:
            logger.warning("Validation failed!")
            print("\nValidation Errors:")
            print("-" * 40)
            for error in result.get('errors', []):
                print(f"- {error}")
            
    except Exception as e:
        logger.error(f"Error processing invoice: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()



