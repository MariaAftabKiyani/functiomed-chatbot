"""
Re-process all documents (PDFs + Web Content)
Run this after adding web content to ingest everything
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from app.services.document_processor import DocumentProcessor


def main():
    # Initialize processor with base path
    base_path = Path(__file__).parent.parent / 'data' / 'documents'
    
    # Create processor and ingest (it handles all logging)
    processor = DocumentProcessor(base_path=str(base_path))
    documents = processor.ingest_documents()
    
    # Simple completion message
    print(f"\n✅ Processing complete! Total: {len(documents)} documents\n")
    
    return documents


if __name__ == "__main__":
    documents = main()