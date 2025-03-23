from pathlib import Path
from typing import Dict
from datetime import datetime

class MetadataExtractor:
    def extract(self, file_path: Path) -> Dict:
        """Extract metadata from document"""
        stats = file_path.stat()
        return {
            'filename': file_path.name,
            'file_size': stats.st_size,
            'created_date': datetime.fromtimestamp(stats.st_ctime).isoformat(),
            'modified_date': datetime.fromtimestamp(stats.st_mtime).isoformat()
        }