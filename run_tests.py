import pytest
import sys
from pathlib import Path

def main():
    """Run all tests with coverage report"""
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Run pytest with coverage
    args = [
        "tests",
        "-v",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:coverage_report"
    ]
    
    return pytest.main(args)

if __name__ == "__main__":
    sys.exit(main())