from typing import Dict, List
from decimal import Decimal, InvalidOperation
from datetime import datetime
import re

class InvoiceValidator:
    """Validates extracted invoice data"""
    
    def __init__(self):
        self.validation_rules = {
            'invoice_number': self._validate_invoice_number,
            'date': self._validate_date,
            'total_amount': self._validate_amount,
            'line_items': self._validate_line_items
        }
    
    def validate(self, invoice_data: Dict) -> Dict:
        """
        Validate extracted invoice data
        
        Args:
            invoice_data: Dictionary containing extracted invoice fields
            
        Returns:
            Dictionary with validation results and cleaned data
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'cleaned_data': {}
        }
        
        # First pass: validate and clean individual fields
        for field, value in invoice_data.items():
            if field in self.validation_rules:
                try:
                    cleaned_value = self.validation_rules[field](value)
                    validation_results['cleaned_data'][field] = cleaned_value
                except ValueError as e:
                    # For missing or invalid fields, add a warning instead of failing
                    validation_results['warnings'].append(f"{field}: {str(e)}")
                    validation_results['cleaned_data'][field] = value
            else:
                # Copy non-validated fields as-is
                validation_results['cleaned_data'][field] = value
        
        # Second pass: cross-validate amounts if possible
        try:
            self._validate_amounts(validation_results['cleaned_data'], validation_results)
        except ValueError as e:
            validation_results['warnings'].append(str(e))
        
        # Only mark as invalid if there are errors (not warnings)
        validation_results['is_valid'] = len(validation_results['errors']) == 0
        
        return validation_results
    
    def _validate_invoice_number(self, value: str) -> str:
        """Validate invoice number format"""
        if not value:
            raise ValueError("Invoice number is required")
        # Allow alphanumeric characters, dashes, and slashes
        if not re.match(r'^[\w\-/]+$', value):
            raise ValueError("Invalid invoice number format")
        return value
    
    def _validate_date(self, value: str) -> str:
        """Validate and standardize date format"""
        if not value:
            raise ValueError("Date is required")
        try:
            # Try multiple date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    date_obj = datetime.strptime(value, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            raise ValueError("Invalid date format")
        except Exception:
            raise ValueError("Invalid date")
    
    def _validate_amount(self, value: str) -> Decimal:
        """Validate and standardize amount format"""
        if not value:
            raise ValueError("Amount is required")
        try:
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[^\d.,\-]', '', value)
            # Convert to Decimal
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid amount format")
    
    def _validate_line_items(self, items: List[Dict]) -> List[Dict]:
        """Validate line items with more lenient rules"""
        if not items:
            return []
            
        cleaned_items = []
        for item in items:
            try:
                # Ensure required fields exist
                required_fields = ['description', 'quantity', 'unit_price', 'total']
                missing_fields = [f for f in required_fields if f not in item]
                if missing_fields:
                    raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
                # Clean and validate numeric fields
                quantity = Decimal(str(item['quantity']))
                unit_price = Decimal(str(item['unit_price']))
                total = Decimal(str(item['total']))
                
                # Allow for small discrepancies (0.5% tolerance)
                calculated_total = quantity * unit_price
                difference = abs(calculated_total - total)
                tolerance = total * Decimal('0.005')  # 0.5% tolerance
                
                if difference > tolerance:
                    raise ValueError(
                        f"Line item total ({total}) differs significantly from "
                        f"calculated total ({calculated_total})"
                    )
                
                cleaned_items.append({
                    'description': str(item['description']),
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total': total
                })
                
            except (KeyError, ValueError, InvalidOperation) as e:
                raise ValueError(f"Invalid line item: {str(e)}")
            
        return cleaned_items
    
    def _validate_amounts(self, invoice_data: Dict, results: Dict) -> None:
        """Cross-validate amounts with tolerance"""
        total_amount = invoice_data.get('total_amount')
        line_items = invoice_data.get('line_items', [])
        
        if total_amount and line_items:
            try:
                line_items_total = sum(Decimal(str(item['total'])) for item in line_items)
                difference = abs(total_amount - line_items_total)
                tolerance = total_amount * Decimal('0.01')  # 1% tolerance
                
                if difference > tolerance:
                    results['warnings'].append(
                        f"Total amount ({total_amount}) differs from sum of line items ({line_items_total})"
                    )
            except (TypeError, InvalidOperation):
                results['warnings'].append("Could not validate total amounts")
