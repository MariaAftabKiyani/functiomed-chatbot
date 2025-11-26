import os
import fitz  
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Document:
    """Represents a processed document"""
    def __init__(
        self,
        text: str,
        metadata: Dict,
        filename: str,
        category: str,
        language: Optional[str] = None
    ):
        self.text = text
        self.metadata = metadata
        self.filename = filename
        self.category = category
        self.language = language

    def __repr__(self):
        return f"Document(filename={self.filename}, category={self.category}, lang={self.language})"


class DocumentProcessor:
    """Process PDF and text documents and extract text with metadata"""
    
    def __init__(self, base_path: str = r"C:\Users\HomePC\Documents\Workspace\functiomed\Project\functiomed-chatbot\data\documents"):
        """
        Initialize DocumentProcessor
        
        Args:
            base_path: Base directory containing subdirectories like pdfs/, txt/, web_content/
                      Default: data/documents/ (scans all subdirectories)
        """
        self.base_path = Path(base_path)
        self.documents: List[Document] = []
        
    def detect_language(self, filename: str) -> Optional[str]:
        """Detect language from filename suffix"""
        filename_lower = filename.lower()
        if filename_lower.endswith('_de.pdf') or filename_lower.endswith('_de.txt') or filename_lower.endswith('_de.md') or 'deutsch' in filename_lower:
            return "DE"
        elif filename_lower.endswith('_en.pdf') or filename_lower.endswith('_en.txt') or filename_lower.endswith('_en.md') or 'englisch' in filename_lower or 'english' in filename_lower:
            return "EN"
        return None
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Dict:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            
            # Extract text from all pages
            full_text = ""
            page_texts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                page_texts.append({
                    "page_number": page_num + 1,
                    "text": text
                })
                full_text += f"\n{text}"
            
            doc.close()
            
            return {
                "full_text": full_text.strip(),
                "page_texts": page_texts,
                "num_pages": len(page_texts)
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return {
                "full_text": "",
                "page_texts": [],
                "num_pages": 0,
                "error": str(e)
            }

    def extract_text_from_txt(self, txt_path: Path) -> Dict:
        """Extract text from .txt or .md files"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split header from content (if exists from scraper)
            if '='*40 in content:
                parts = content.split('='*40, 1)
                if len(parts) == 2:
                    full_text = parts[1].strip()
                else:
                    full_text = content
            else:
                full_text = content
            
            # Count lines as pseudo-pages (for consistency with PDF structure)
            lines = full_text.split('\n')
            num_pages = max(1, len(lines) // 50)  # Approximately 50 lines per "page"
            
            return {
                "full_text": full_text,
                "page_texts": [{"page_number": 1, "text": full_text}],
                "num_pages": num_pages
            }
            
        except Exception as e:
            logger.error(f"Error reading text file {txt_path}: {e}")
            return {
                "full_text": "",
                "page_texts": [],
                "num_pages": 0,
                "error": str(e)
            }
    
    def get_category_from_path(self, file_path: Path) -> str:
        """Extract category from directory structure"""
        # Get parent directory name as category
        return file_path.parent.name
    
    def process_pdf(self, pdf_path: Path) -> Optional[Document]:
        """Process a single PDF file"""
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        # Extract text
        extracted = self.extract_text_from_pdf(pdf_path)
        
        if not extracted["full_text"]:
            logger.warning(f"No text extracted from {pdf_path}")
            return None
        
        # Get metadata
        filename = pdf_path.name
        category = self.get_category_from_path(pdf_path)
        language = self.detect_language(filename)
        
        metadata = {
            "filename": filename,
            "filepath": str(pdf_path),
            "category": category,
            "language": language,
            "num_pages": extracted["num_pages"],
            "page_texts": extracted["page_texts"],
            "source_type": "pdf"
        }
        
        # Create Document object
        document = Document(
            text=extracted["full_text"],
            metadata=metadata,
            filename=filename,
            category=category,
            language=language
        )
        
        return document

    def process_txt(self, txt_path: Path) -> Optional[Document]:
        """Process a single .txt or .md file"""
        logger.info(f"Processing text file: {txt_path.name}")
        
        # Extract text
        extracted = self.extract_text_from_txt(txt_path)
        
        if not extracted["full_text"]:
            logger.warning(f"No text extracted from {txt_path}")
            return None
        
        # Get metadata
        filename = txt_path.name
        category = self.get_category_from_path(txt_path)
        language = self.detect_language(filename)
        
        metadata = {
            "filename": filename,
            "filepath": str(txt_path),
            "category": category,
            "language": language,
            "num_pages": extracted["num_pages"],
            "page_texts": extracted["page_texts"],
            "source_type": "text"
        }
        
        # Create Document object
        document = Document(
            text=extracted["full_text"],
            metadata=metadata,
            filename=filename,
            category=category,
            language=language
        )
        
        return document
    
    def ingest_documents(self) -> List[Document]:
        """Ingest all PDF and text documents from base path (recursively scans subdirectories)"""
        logger.info(f"Starting document ingestion from: {self.base_path}")
        
        if not self.base_path.exists():
            logger.error(f"Path does not exist: {self.base_path}")
            return []
        
        # Find all PDF, TXT, and MD files recursively from base path
        pdf_files = list(self.base_path.rglob("*.pdf"))
        txt_files = list(self.base_path.rglob("*.txt"))
        md_files = list(self.base_path.rglob("*.md"))

        # Filter out metadata files (files starting with _)
        txt_files = [f for f in txt_files if not f.name.startswith('_')]
        md_files = [f for f in md_files if not f.name.startswith('_')]
        
        all_files = pdf_files + txt_files + md_files

        logger.info(f"Found {len(pdf_files)} PDF files")
        logger.info(f"Found {len(txt_files)} TXT files")
        logger.info(f"Found {len(md_files)} MD files")
        logger.info(f"Total files to process: {len(all_files)}")

        # Process each file
        processed_count = 0
        for file_path in all_files:
            if file_path.suffix.lower() == '.pdf':
                document = self.process_pdf(file_path)
            else:  # .txt or .md
                document = self.process_txt(file_path)
            
            if document:
                self.documents.append(document)
                processed_count += 1
        
        logger.info(f"Successfully processed {processed_count}/{len(all_files)} documents")
        
        # Print summary
        self.print_summary()
        
        return self.documents
    
    def print_summary(self):
        """Print ingestion summary"""
        logger.info("\n" + "="*50)
        logger.info("INGESTION SUMMARY")
        logger.info("="*50)
        logger.info(f"Total documents processed: {len(self.documents)}")
        
        # Group by category
        categories = {}
        for doc in self.documents:
            categories[doc.category] = categories.get(doc.category, 0) + 1
        
        logger.info("\nDocuments by category:")
        for category, count in sorted(categories.items()):
            logger.info(f"  - {category}: {count}")
        
        # Group by language
        languages = {}
        for doc in self.documents:
            lang = doc.language or "Unknown"
            languages[lang] = languages.get(lang, 0) + 1

        logger.info("\nDocuments by language:")
        for lang, count in sorted(languages.items()):
            logger.info(f"  - {lang}: {count}")

        # Group by source type
        source_types = {}
        for doc in self.documents:
            source_type = doc.metadata.get("source_type", "pdf")  # Default to pdf for backwards compatibility
            source_types[source_type] = source_types.get(source_type, 0) + 1

        logger.info("\nDocuments by source type:")
        for source_type, count in sorted(source_types.items()):
            logger.info(f"  - {source_type}: {count}")
        
        logger.info("="*50 + "\n")
    
    def get_documents_by_category(self, category: str) -> List[Document]:
        """Get all documents from a specific category"""
        return [doc for doc in self.documents if doc.category == category]
    
    def get_documents_by_language(self, language: str) -> List[Document]:
        """Get all documents in a specific language"""
        return [doc for doc in self.documents if doc.language == language]

    def get_documents_by_source_type(self, source_type: str) -> List[Document]:
        """Get all documents from a specific source type (pdf or text)"""
        return [doc for doc in self.documents if doc.metadata.get("source_type") == source_type]


# Example usage
if __name__ == "__main__":
    # Now scans data/documents/ which includes both pdfs/ and txt/ subdirectories
    processor = DocumentProcessor()
    documents = processor.ingest_documents()
    
    # Print first document as example
    if documents:
        doc = documents[40]
        print(f"\nExample Document:")
        print(f"Filename: {doc.filename}")
        print(f"Category: {doc.category}")
        print(f"Language: {doc.language}")
        print(f"Source Type: {doc.metadata.get('source_type')}")
        print(f"Text preview (first 200 chars): {doc.text}")