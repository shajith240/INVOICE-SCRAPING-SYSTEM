# Document Processing System

An intelligent document processing system that categorizes and extracts information from various document types.

## Features

- Automatic document categorization
- Data extraction based on document type
- Support for multiple document formats
- Metadata extraction and processing
- Configurable processing pipeline
- Error handling and logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/USERNAME/REPO_NAME.git
cd REPO_NAME
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```python
from src.document_processor import DocumentProcessor

# Initialize processor with config
processor = DocumentProcessor('config.json')

# Process single document
result = processor.process_document('path/to/document.pdf')

# Process batch of documents
results = processor.process_batch('path/to/document/directory')
```

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.