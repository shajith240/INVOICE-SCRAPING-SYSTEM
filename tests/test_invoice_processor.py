import pytest
import spacy
from pathlib import Path
from src.document_classifier import DocumentClassifier
from src.categorizer import DocumentCategorizer
from src.text_extractor import TextExtractor

class TestInvoiceProcessor:
    @pytest.fixture(scope="class")
    def nlp_model(self):
        """Load spaCy model with custom invoice-specific patterns"""
        nlp = spacy.load("en_core_web_sm")
        
        # Add custom invoice-specific patterns
        ruler = nlp.add_pipe("entity_ruler", before="ner")
        patterns = [
            {"label": "INVOICE_NUM", "pattern": [{"LOWER": "invoice"}, {"LOWER": "number"}, {"SHAPE": "ddd"}]},
            {"label": "AMOUNT", "pattern": [{"LIKE_NUM": True}, {"LOWER": {"IN": ["usd", "eur", "$", "€"]}}]},
            {"label": "DATE", "pattern": [{"SHAPE": "dd/dd/dddd"}]},
            # Add more patterns as needed
        ]
        ruler.add_patterns(patterns)
        return nlp

    @pytest.fixture
    def test_invoices_dir(self):
        """Set up directory with test invoice files"""
        return Path(__file__).parent / "test_data" / "invoices"

    def test_real_invoice_classification(self, test_invoices_dir, nlp_model):
        """Test classification on real invoice samples"""
        categorizer = DocumentCategorizer()
        
        for invoice_path in test_invoices_dir.glob("*.pdf"):
            result = categorizer.categorize(invoice_path)
            
            # Basic classification checks
            assert result["status"] == "processed"
            assert result["confidence"] > 0.5
            assert "invoice" in result["categories"]
            
            # Check extracted data structure
            assert "extracted_data" in result
            assert all(key in result["extracted_data"] for key in [
                "invoice_number", "date", "total_amount", "vendor"
            ])

    def test_nlp_extraction(self, test_invoices_dir, nlp_model):
        """Test NLP-based information extraction"""
        extractor = TextExtractor()
        
        for invoice_path in test_invoices_dir.glob("*.pdf"):
            # Extract text
            text_content = extractor.extract(invoice_path)
            doc = nlp_model(text_content)
            
            # Test entity recognition
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            assert any(ent[1] == "INVOICE_NUM" for ent in entities), f"No invoice number found in {invoice_path}"
            assert any(ent[1] == "AMOUNT" for ent in entities), f"No amount found in {invoice_path}"
            
            # Test key phrase matching
            amount_patterns = [
                "total amount",
                "total due",
                "balance due",
                "amount payable"
            ]
            found_amount = any(phrase in text_content.lower() for phrase in amount_patterns)
            assert found_amount, f"No amount-related phrase found in {invoice_path}"

    @pytest.mark.parametrize("vendor_type", ["standard", "international", "handwritten"])
    def test_vendor_specific_extraction(self, test_invoices_dir, nlp_model, vendor_type):
        """Test extraction for different vendor invoice formats"""
        invoice_path = test_invoices_dir / vendor_type / f"sample_{vendor_type}.pdf"
        if not invoice_path.exists():
            pytest.skip(f"No test file for {vendor_type} vendor type")
            
        categorizer = DocumentCategorizer()
        result = categorizer.categorize(invoice_path)
        
        # Basic assertions for all types
        assert result["status"] == "processed"
        assert "extracted_data" in result
        
        # Vendor-specific assertions
        if vendor_type == "standard":
            assert result["confidence"] > 0.8
            assert "$1,234.56" in result["extracted_data"]["total_amount"]
        elif vendor_type == "international":
            assert "€1.234,56" in result["extracted_data"]["total_amount"]
        elif vendor_type == "handwritten":
            assert result["confidence"] > 0.6
            assert "$789.00" in result["extracted_data"]["total_amount"]

    def test_data_validation(self, test_invoices_dir, nlp_model):
        """Test validation of extracted data"""
        categorizer = DocumentCategorizer()
        
        for invoice_path in test_invoices_dir.glob("*.pdf"):
            result = categorizer.categorize(invoice_path)
            data = result["extracted_data"]
            
            # Validate invoice number format
            if data["invoice_number"]:
                assert len(data["invoice_number"]) >= 3, "Invoice number too short"
                
            # Validate amount format
            if data["total_amount"]:
                amount = float(data["total_amount"].replace(",", ""))
                assert amount > 0, "Invalid amount"
                
            # Validate date format
            if data["date"]:
                from datetime import datetime
                try:
                    datetime.strptime(data["date"], "%Y-%m-%d")
                except ValueError:
                    pytest.fail(f"Invalid date format in {invoice_path}")

    def test_error_handling(self, test_invoices_dir):
        """Test handling of problematic invoices"""
        categorizer = DocumentCategorizer()
        
        # Test with corrupted PDF
        corrupted_path = test_invoices_dir / "corrupted.pdf"
        if corrupted_path.exists():
            result = categorizer.categorize(corrupted_path)
            assert result["status"] == "error"
            assert "error" in result
            
        # Test with empty PDF
        empty_path = test_invoices_dir / "empty.pdf"
        if empty_path.exists():
            result = categorizer.categorize(empty_path)
            assert result["confidence"] < 0.2

    @pytest.mark.slow
    def test_performance(self, test_invoices_dir, nlp_model):
        """Test processing performance with larger datasets"""
        import time
        categorizer = DocumentCategorizer()
        
        start_time = time.time()
        processed = 0
        
        for invoice_path in test_invoices_dir.glob("*.pdf"):
            categorizer.categorize(invoice_path)
            processed += 1
            
        total_time = time.time() - start_time
        avg_time = total_time / processed if processed > 0 else 0
        
        assert avg_time < 2.0, f"Average processing time ({avg_time:.2f}s) exceeds threshold"
