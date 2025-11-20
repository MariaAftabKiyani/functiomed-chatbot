"""
Qdrant client for vector storage.
Simple, robust, with proper validation and error handling.
"""
import logging
import time
from typing import List
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import sys
from pathlib import Path

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Qdrant client with:
    - Connection validation
    - Collection management
    - Batch operations with retries
    """
    
    def __init__(self):
        """Connect to Qdrant"""
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect with retry logic"""
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}...")
        
        for attempt in range(settings.MAX_RETRIES):
            try:
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=settings.QDRANT_TIMEOUT
                )
                
                # Test connection
                self.client.get_collections()
                logger.info("✓ Connected to Qdrant")
                return
                
            except Exception as e:
                if attempt < settings.MAX_RETRIES - 1:
                    wait_time = settings.RETRY_DELAY * (attempt + 1)
                    logger.warning(f"Connection attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to connect after {settings.MAX_RETRIES} attempts")
                    raise RuntimeError(f"Qdrant connection failed: {e}")
    
    def collection_exists(self) -> bool:
        """Check if collection exists"""
        try:
            collections = self.client.get_collections()
            return any(c.name == settings.QDRANT_COLLECTION for c in collections.collections)
        except Exception as e:
            logger.error(f"Error checking collection: {e}")
            return False
    
    def create_collection(self, recreate: bool = False):
        """
        Create collection with vector configuration.
        
        Args:
            recreate: Delete existing collection first
        """
        collection_name = settings.QDRANT_COLLECTION
        exists = self.collection_exists()
        
        # Handle recreate
        if exists and recreate:
            logger.info(f"Deleting existing collection: {collection_name}")
            try:
                self.client.delete_collection(collection_name)
                logger.info("✓ Collection deleted")
            except Exception as e:
                raise RuntimeError(f"Failed to delete collection: {e}")
            exists = False
        
        # Collection already exists
        if exists:
            logger.info(f"Collection '{collection_name}' already exists")
            info = self.get_collection_info()
            logger.info(f"  Vectors: {info.get('points_count', 0)}")
            return
        
        # Create new collection
        logger.info(f"Creating collection: {collection_name}")
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=settings.QDRANT_VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
            logger.info("✓ Collection created")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise RuntimeError(f"Collection creation failed: {e}")
    
    def insert_chunks(self, chunks: List, embeddings: np.ndarray) -> int:
        """
        Insert chunks with embeddings into Qdrant.
        
        Args:
            chunks: List of Chunk objects
            embeddings: numpy array (n, 1024)
            
        Returns:
            Number of inserted vectors
        """
        # Validate inputs
        if not chunks or not len(chunks):
            raise ValueError("Chunks list is empty")
        
        if embeddings is None or len(embeddings) == 0:
            raise ValueError("Embeddings array is empty")
        
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunk count ({len(chunks)}) != embedding count ({len(embeddings)})")
        
        if embeddings.shape[1] != settings.QDRANT_VECTOR_SIZE:
            raise ValueError(f"Embedding dimension mismatch: {embeddings.shape[1]} != {settings.QDRANT_VECTOR_SIZE}")
        
        logger.info(f"Inserting {len(chunks)} chunks into Qdrant...")
        
        # Prepare points
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            try:
                point = PointStruct(
                    id=idx,
                    vector=embedding.tolist(),
                    payload={
                        "text": chunk.text,
                        "chunk_id": chunk.chunk_id,
                        "chunk_index": chunk.chunk_index,
                        "source_document": chunk.metadata.get("source_document", ""),
                        "filename": chunk.metadata.get("filename", ""),
                        "category": chunk.metadata.get("category", ""),
                        "language": chunk.metadata.get("language", ""),
                        "source_type": chunk.metadata.get("source_type", ""),
                    }
                )
                points.append(point)
            except Exception as e:
                logger.warning(f"Failed to create point {idx}: {e}")
                continue
        
        if not points:
            raise RuntimeError("No valid points created")
        
        # Insert in batches with retry
        total_inserted = 0
        batch_size = settings.UPLOAD_BATCH_SIZE
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(points) + batch_size - 1) // batch_size
            
            # Retry logic for batch
            for attempt in range(settings.MAX_RETRIES):
                try:
                    self.client.upsert(
                        collection_name=settings.QDRANT_COLLECTION,
                        points=batch
                    )
                    total_inserted += len(batch)
                    logger.info(f"  Batch {batch_num}/{total_batches}: Inserted {total_inserted}/{len(points)}")
                    break
                    
                except Exception as e:
                    if attempt < settings.MAX_RETRIES - 1:
                        wait_time = settings.RETRY_DELAY * (attempt + 1)
                        logger.warning(f"Batch {batch_num} failed (attempt {attempt + 1}): {e}. Retrying...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Batch {batch_num} failed after {settings.MAX_RETRIES} attempts")
                        raise RuntimeError(f"Batch insertion failed: {e}")
        
        logger.info(f"✓ Inserted {total_inserted} chunks")
        return total_inserted
    
    def count(self) -> int:
        """Get total vectors in collection"""
        try:
            if not self.collection_exists():
                return 0
            info = self.client.get_collection(settings.QDRANT_COLLECTION)
            return info.points_count
        except Exception as e:
            logger.error(f"Failed to count vectors: {e}")
            return 0
    
    def get_collection_info(self) -> dict:
        """Get collection information"""
        if not self.collection_exists():
            return {"exists": False, "name": settings.QDRANT_COLLECTION}
        
        try:
            info = self.client.get_collection(settings.QDRANT_COLLECTION)
            return {
                "exists": True,
                "name": settings.QDRANT_COLLECTION,
                "points_count": info.points_count,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance.name,
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"exists": True, "name": settings.QDRANT_COLLECTION, "error": str(e)}


if __name__ == "__main__":
    # Test
    from config import setup_logging
    setup_logging("INFO")
    
    print("\n" + "="*60)
    print("QDRANT SERVICE TEST")
    print("="*60)
    
    try:
        service = QdrantService()
        
        # Test collection info
        print("\n[Test 1] Collection info")
        info = service.get_collection_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Test create collection
        print("\n[Test 2] Create collection")
        service.create_collection(recreate=True)
        
        # Test count
        print("\n[Test 3] Count vectors")
        count = service.count()
        print(f"  Vectors: {count}")
        
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)