import pytesseract
from PIL import Image
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Tesseract path using the confirmed working installation
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Print Tesseract version
try:
    print("Tesseract Version:", pytesseract.get_tesseract_version())
    print("Available Languages:", pytesseract.get_languages())
    print("Tesseract Configuration Successful!")
except Exception as e:
    print("Error:", str(e))