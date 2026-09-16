import os
import re
import logging
from typing import List, Dict, Any
import pdfplumber

# Configure basic logging for extraction failures
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_date(text: str) -> str:
    """Attempt to extract a date from the text using common regex patterns."""
    # Matches DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, or Month DD, YYYY
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return ""

def ingest_pdf(filepath: str) -> List[Dict[str, Any]]:
    """Extract text from a PDF file page by page, keeping metadata."""
    documents = []
    filename = os.path.basename(filepath)
    
    try:
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text or not text.strip():
                    logger.warning(f"Failed to extract text from {filename}, page {page_num}. It might be a scanned image.")
                    continue
                
                # Extract date from the first page typically, or just search the page text
                extracted_date = extract_date(text)
                
                documents.append({
                    "text": text.strip(),
                    "metadata": {
                        "source": filename,
                        "page_number": page_num,
                        "date": extracted_date
                    }
                })
    except Exception as e:
        logger.error(f"Error processing PDF {filename}: {e}")
        
    return documents

def ingest_txt(filepath: str) -> List[Dict[str, Any]]:
    """Extract text from a plain text file."""
    documents = []
    filename = os.path.basename(filepath)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            if not text or not text.strip():
                logger.warning(f"Failed to extract text from {filename}. File might be empty.")
                return documents
            
            extracted_date = extract_date(text)
            
            documents.append({
                "text": text.strip(),
                "metadata": {
                    "source": filename,
                    "page_number": 1,
                    "date": extracted_date
                }
            })
    except Exception as e:
        logger.error(f"Error processing TXT {filename}: {e}")
        
    return documents

def ingest_directory(directory_path: str) -> List[Dict[str, Any]]:
    """Ingest all supported files in a directory."""
    all_documents = []
    
    for filename in os.listdir(directory_path):
        filepath = os.path.join(directory_path, filename)
        if filename.lower().endswith('.pdf'):
            all_documents.extend(ingest_pdf(filepath))
        elif filename.lower().endswith('.txt'):
            all_documents.extend(ingest_txt(filepath))
        else:
            logger.info(f"Skipping unsupported file format: {filename}")
            
    return all_documents

if __name__ == "__main__":
    # Quick test if run directly
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    if os.path.exists(sample_dir):
        docs = ingest_directory(sample_dir)
        print(f"Extracted {len(docs)} pages/documents.")
