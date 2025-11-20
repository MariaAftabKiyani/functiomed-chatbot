#!/usr/bin/env python3
"""
Document Embedding Pipeline
Load → Chunk → Embed → Store
"""
import sys
import logging
import time
import argparse
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.config import settings, setup_logging
from app.utils.embeddings import EmbeddingService
from app.utils.qdrant_client import QdrantService
from app.services.document_processor import DocumentProcessor
from app.services.document_chunker import DocumentChunker

from pathlib import Path
print("DOCUMENTS_DIR:", Path(settings.DOCUMENTS_DIR).resolve())
print("Exists?", Path(settings.DOCUMENTS_DIR).resolve().exists())


logger = logging.getLogger(__name__)


def main():
    """Main pipeline"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Embed documents into Qdrant")
    parser.add_argument("--recreate", action="store_true", help="Recreate collection")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging("DEBUG" if args.verbose else "INFO")
    
    print("\n" + "="*70)
    print("DOCUMENT EMBEDDING PIPELINE")
    print("="*70 + "\n")
    
    start_time = time.time()
    
    try:
        # Step 1: Initialize services
        logger.info("Step 1: Initializing services...")
        embedding_service = EmbeddingService()
        qdrant_service = QdrantService()
        
        # Step 2: Setup Qdrant
        logger.info("\nStep 2: Setting up Qdrant...")
        qdrant_service.create_collection(recreate=args.recreate)
        
        # Step 3: Load documents
        logger.info("\nStep 3: Loading documents...")
        processor = DocumentProcessor(base_path=str(settings.DOCUMENTS_DIR))
        documents = processor.ingest_documents()
        
        if not documents:
            logger.error("No documents loaded!")
            return 1
        
        logger.info(f"✓ Loaded {len(documents)} documents")
        
        # Step 4: Chunk documents
        logger.info("\nStep 4: Chunking documents...")
        chunker = DocumentChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            min_chunk_size=settings.MIN_CHUNK_SIZE
        )
        chunks = chunker.chunk_documents(documents)
        
        if not chunks:
            logger.error("No chunks created!")
            return 1
        
        logger.info(f"✓ Created {len(chunks)} chunks")
        
        # Step 5: Generate embeddings
        logger.info("\nStep 5: Generating embeddings...")
        texts = [chunk.text for chunk in chunks]
        embeddings = embedding_service.embed_documents(texts)
        
        logger.info(f"✓ Generated {len(embeddings)} embeddings")
        
        # Step 6: Insert into Qdrant
        logger.info("\nStep 6: Inserting into Qdrant...")
        inserted = qdrant_service.insert_chunks(chunks, embeddings)
        
        # Step 7: Verify
        logger.info("\nStep 7: Verifying...")
        total = qdrant_service.count()
        logger.info(f"Total vectors in Qdrant: {total}")
        
        # Summary
        elapsed = time.time() - start_time
        
        print("\n" + "="*70)
        print("✓ PIPELINE COMPLETE")
        print("="*70)
        print(f"Documents: {len(documents)}")
        print(f"Chunks: {len(chunks)}")
        print(f"Embeddings: {len(embeddings)}")
        print(f"Inserted: {inserted}")
        print(f"Total vectors: {total}")
        print(f"Time: {elapsed:.1f}s")
        print("="*70 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        logger.error("\nInterrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())