"""
Build BM25 Index from Qdrant Collection

This script fetches all documents from Qdrant and builds a BM25 index
for hybrid search (BM25 + Semantic).

Usage:
    python scripts/build_bm25_index.py
"""
import sys
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.utils.qdrant_client import QdrantService
from app.utils.bm25_search import BM25

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_bm25_index():
    """Build BM25 index from Qdrant collection"""
    logger.info("="*80)
    logger.info("BM25 INDEX BUILDER")
    logger.info("="*80)

    # Initialize Qdrant service
    logger.info("\n[1/4] Connecting to Qdrant...")
    qdrant = QdrantService()
    collection_info = qdrant.get_collection_info()

    if not collection_info.get("exists", False):
        logger.error(f"Collection '{settings.QDRANT_COLLECTION}' does not exist!")
        logger.error("Please index documents first using the document ingestion script.")
        return False

    total_docs = collection_info.get("points_count", 0)
    logger.info(f"✓ Connected to Qdrant")
    logger.info(f"  Collection: {settings.QDRANT_COLLECTION}")
    logger.info(f"  Total documents: {total_docs}")

    if total_docs == 0:
        logger.error("No documents in collection! Nothing to index.")
        return False

    # Fetch all documents from Qdrant
    logger.info("\n[2/4] Fetching documents from Qdrant...")
    try:
        # Qdrant scroll API to get all points
        from qdrant_client import models

        all_points = []
        offset = None
        batch_size = 100

        while True:
            scroll_result = qdrant.client.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False  # We don't need vectors for BM25
            )

            points, next_offset = scroll_result

            if not points:
                break

            all_points.extend(points)
            logger.info(f"  Fetched {len(all_points)}/{total_docs} documents...")

            if next_offset is None:
                break

            offset = next_offset

        logger.info(f"✓ Fetched {len(all_points)} documents")

    except Exception as e:
        logger.error(f"Failed to fetch documents: {e}")
        return False

    # Extract text and metadata
    logger.info("\n[3/4] Extracting text and metadata...")
    corpus = []
    metadata_list = []

    for point in all_points:
        payload = point.payload

        # Extract text
        text = payload.get("text", "")
        if not text:
            logger.warning(f"Point {point.id} has no text, skipping")
            continue

        corpus.append(text)

        # Extract metadata
        metadata = {
            "chunk_id": payload.get("chunk_id"),
            "source_document": payload.get("source_document"),
            "category": payload.get("category"),
            "language": payload.get("language"),
            "source_type": payload.get("source_type"),
            "chunk_index": payload.get("chunk_index"),
            "total_chunks": payload.get("total_chunks")
        }
        metadata_list.append(metadata)

    logger.info(f"✓ Extracted {len(corpus)} text chunks")

    # Build BM25 index
    logger.info("\n[4/4] Building BM25 index...")
    logger.info(f"  Parameters: k1={settings.BM25_K1}, b={settings.BM25_B}")

    bm25 = BM25(k1=settings.BM25_K1, b=settings.BM25_B)
    bm25.index(corpus=corpus, metadata=metadata_list)

    # Save index
    index_path = Path(settings.DOCUMENTS_DIR).parent / "bm25_index.pkl"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    bm25.save_index(str(index_path))

    logger.info("\n" + "="*80)
    logger.info("✅ BM25 INDEX BUILT SUCCESSFULLY")
    logger.info("="*80)
    logger.info(f"Index saved to: {index_path}")
    logger.info(f"Total documents indexed: {bm25.num_docs}")
    logger.info(f"Unique terms: {len(bm25.idf)}")
    logger.info(f"Average document length: {bm25.avgdl:.1f} tokens")
    logger.info("\nYou can now use hybrid search in your retrieval service!")
    logger.info("="*80 + "\n")

    return True


def test_bm25_index():
    """Test the built BM25 index with sample queries"""
    logger.info("\n[TEST] Testing BM25 index with sample queries...")

    index_path = Path(settings.DOCUMENTS_DIR).parent / "bm25_index.pkl"

    if not index_path.exists():
        logger.error("BM25 index not found. Build it first.")
        return

    # Load index
    bm25 = BM25()
    bm25.load_index(str(index_path))

    # Test queries
    test_queries = [
        "Was ist Osteopathie?",
        "Öffnungszeiten Functiomed",
        "Prof. Martin Spring",
        "Akupunktur Behandlung",
        "Parkmöglichkeiten"
    ]

    for query in test_queries:
        logger.info(f"\nQuery: '{query}'")
        results = bm25.search(query, top_k=3)

        if results:
            for i, result in enumerate(results, 1):
                doc = result['metadata'].get('source_document', 'Unknown')
                score = result['score']
                text_preview = result['text'][:100] + "..."
                logger.info(f"  {i}. {doc} (score: {score:.4f})")
                logger.info(f"     {text_preview}")
        else:
            logger.info("  No results found")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build BM25 index for hybrid search"
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test the BM25 index after building'
    )

    args = parser.parse_args()

    # Build index
    success = build_bm25_index()

    if not success:
        sys.exit(1)

    # Test if requested
    if args.test:
        test_bm25_index()


if __name__ == "__main__":
    main()
