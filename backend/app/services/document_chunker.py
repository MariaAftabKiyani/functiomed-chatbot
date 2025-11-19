"""
Document Chunker for RAG Pipeline
Hybrid semantic + recursive chunking approach for medical documents.
Optimized for German language with metadata preservation and quality enforcement.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk with metadata"""
    text: str
    metadata: Dict
    chunk_id: str
    chunk_index: int
    
    def __repr__(self):
        return f"Chunk(id={self.chunk_id}, index={self.chunk_index}, length={len(self.text)})"


class SemanticSplitter:
    """
    Splits text on semantic boundaries (headers, sections) before recursive splitting.
    Preserves document structure and logical relationships.
    """
    
    def __init__(self, min_section_size: int = 100):
        self.min_section_size = min_section_size
        
        # German medical document header patterns
        self.header_patterns = [
            r"^===\s+(.+?)\s+===$",      # Markdown === headers ===
            r"^##\s+(.+?)$",              # Markdown ## headers
            r"^#\s+(.+?)$",               # Markdown # headers
            r"^(\d+\.)\s+(.+?)$",         # Numbered sections: 1. Section
            r"^[A-Z]{2,}[\s\w\-]*:$",     # ALL CAPS labels: SECTION:
        ]
    
    def split_by_sections(self, text: str) -> List[Tuple[str, Optional[str]]]:
        """
        Split text by semantic sections (headers/boundaries).
        
        Args:
            text: Input text to split
            
        Returns:
            List of (content, header) tuples where header is the section title
        """
        sections = []
        current_section = []
        current_header = None
        
        lines = text.split('\n')
        
        for line in lines:
            # Check if line is a header
            is_header = False
            for pattern in self.header_patterns:
                if re.match(pattern, line.strip()):
                    # Save previous section if it has content
                    section_text = '\n'.join(current_section).strip()
                    if section_text and len(section_text) >= self.min_section_size:
                        sections.append((section_text, current_header))
                    elif section_text and sections:
                        # Small section: merge with previous section
                        prev_content, prev_header = sections.pop()
                        merged = f"{prev_content}\n\n{section_text}"
                        sections.append((merged, prev_header))
                    
                    # Start new section
                    current_header = line.strip()
                    current_section = []
                    is_header = True
                    break
            
            if not is_header:
                current_section.append(line)
        
        # Handle final section
        section_text = '\n'.join(current_section).strip()
        if section_text:
            if len(section_text) >= self.min_section_size:
                sections.append((section_text, current_header))
            elif sections:
                prev_content, prev_header = sections.pop()
                merged = f"{prev_content}\n\n{section_text}"
                sections.append((merged, prev_header))
            else:
                sections.append((section_text, current_header))
        
        return sections if sections else [(text, None)]


class DocumentChunker:
    """
    Hybrid semantic + recursive chunking for medical documents.
    
    Strategy:
    1. Split text by semantic sections (headers, logical boundaries)
    2. For sections larger than chunk_size, apply recursive splitting
    3. Enforce minimum chunk size (small chunks are merged with adjacent ones)
    4. Preserve metadata and maintain chunk relationships
    """
    
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        min_chunk_size: int = 200,
    ):
        """
        Initialize document chunker with hybrid approach.
        
        Args:
            chunk_size: Target size in characters (~200 tokens for German)
            chunk_overlap: Overlapping characters between chunks for context
            min_chunk_size: Minimum chunk size; smaller chunks are merged
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        self.semantic_splitter = SemanticSplitter(min_section_size=min_chunk_size)
        
        # Separators optimized for German medical documents
        # Priority: paragraphs > lines > sentences > clauses > words > characters
        separators = [
            "\n\n",      # Paragraph breaks (highest priority)
            "\n",        # Line breaks
            ". ",        # Sentences (German-friendly)
            "! ",        # Exclamations
            "? ",        # Questions
            ", ",        # Clauses
            " ",         # Words
            ""           # Characters (fallback)
        ]
        
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False
        )
        
        logger.info(
            f"DocumentChunker initialized (hybrid approach): "
            f"chunk_size={chunk_size}, overlap={chunk_overlap}, min_size={min_chunk_size}"
        )
    
    def _apply_recursive_split(self, text: str) -> List[str]:
        """
        Apply recursive splitting to text that exceeds chunk_size.
        
        Args:
            text: Text to split
            
        Returns:
            List of chunks
        """
        try:
            return self.recursive_splitter.split_text(text)
        except Exception as e:
            logger.error(f"Error in recursive split: {e}")
            # Fallback: return original text if splitting fails
            return [text]
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """
        Merge chunks smaller than min_chunk_size with adjacent chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Merged chunks meeting minimum size requirement
        """
        if not chunks:
            return []
        
        merged = []
        for chunk in chunks:
            if len(chunk) < self.min_chunk_size and merged:
                # Merge small chunk with previous one
                merged[-1] = f"{merged[-1]}\n\n{chunk}"
            else:
                merged.append(chunk)
        
        return merged
    
    def _chunk_section(self, section_text: str) -> List[str]:
        """
        Chunk a single semantic section using hybrid approach.
        
        Args:
            section_text: Text of a semantic section
            
        Returns:
            List of chunks from this section
        """
        # If section is within chunk_size, return as-is
        if len(section_text) <= self.chunk_size:
            return [section_text]
        
        # Section is too large: apply recursive splitting
        chunks = self._apply_recursive_split(section_text)
        
        # Enforce minimum chunk size
        chunks = self._merge_small_chunks(chunks)
        
        return chunks
    
    def chunk_document(self, document) -> List[Chunk]:
        """
        Chunk a single document using hybrid semantic + recursive approach.
        
        Args:
            document: Document object with text and metadata attributes
            
        Returns:
            List of Chunk objects with preserved metadata
            
        Raises:
            AttributeError: If document lacks required attributes
            ValueError: If document text is empty or too small
        """
        # Validate document
        if not hasattr(document, 'text'):
            logger.error(f"Document missing 'text' attribute")
            raise AttributeError("Document must have 'text' attribute")
        
        if not document.text or not document.text.strip():
            logger.warning(f"Document '{document.filename}' has empty text, skipping")
            raise ValueError(f"Document '{document.filename}' has no text content")
        
        try:
            # Step 1: Split by semantic sections
            sections = self.semantic_splitter.split_by_sections(document.text)
            logger.debug(f"'{document.filename}': split into {len(sections)} semantic sections")
            
            # Step 2: Chunk each section (respecting semantic boundaries)
            all_chunks = []
            for section_text, section_header in sections:
                section_chunks = self._chunk_section(section_text)
                all_chunks.extend(section_chunks)
            
            if not all_chunks:
                logger.warning(f"No chunks created for '{document.filename}'")
                return []
            
            # Step 3: Create Chunk objects with metadata
            chunk_objects = []
            for idx, chunk_text in enumerate(all_chunks):
                chunk_id = f"{document.filename}#{idx}"
                
                # Preserve all original metadata and add chunking info
                chunk_metadata = {
                    **document.metadata,
                    "chunk_index": idx,
                    "total_chunks": len(all_chunks),
                    "chunk_id": chunk_id,
                    "source_document": document.filename,
                    "filename": document.filename,
                    "category": document.category,
                    "language": document.language,
                    "source_type": document.metadata.get("source_type", "unknown"),
                }
                
                chunk = Chunk(
                    text=chunk_text,
                    metadata=chunk_metadata,
                    chunk_id=chunk_id,
                    chunk_index=idx
                )
                
                chunk_objects.append(chunk)
            
            avg_chunk_size = sum(len(c.text) for c in chunk_objects) // len(chunk_objects)
            logger.info(
                f"✓ '{document.filename}': {len(sections)} sections → {len(chunk_objects)} chunks "
                f"(avg {avg_chunk_size} chars)"
            )
            return chunk_objects
            
        except Exception as e:
            logger.error(f"Unexpected error chunking '{document.filename}': {type(e).__name__}: {e}")
            raise
    
    def chunk_documents(self, documents: List) -> List[Chunk]:
        """
        Chunk multiple documents with error handling.
        
        Args:
            documents: List of Document objects
            
        Returns:
            Flattened list of all chunks from all documents
        """
        logger.info(f"Starting to chunk {len(documents)} documents...")
        
        all_chunks = []
        failed_docs = []
        skipped_docs = []
        
        for doc in documents:
            try:
                doc_chunks = self.chunk_document(doc)
                all_chunks.extend(doc_chunks)
                
            except ValueError as e:
                # Empty or invalid documents
                logger.warning(f"⊘ Skipped '{doc.filename}' (empty): {e}")
                skipped_docs.append((doc.filename, "empty"))
                
            except AttributeError as e:
                # Missing required attributes
                logger.warning(f"⊘ Failed '{doc.filename}' (invalid structure): {e}")
                failed_docs.append((doc.filename, "invalid_structure"))
                
            except Exception as e:
                # Unexpected errors
                logger.error(f"⊘ Failed '{doc.filename}': {type(e).__name__}: {e}")
                failed_docs.append((doc.filename, str(type(e).__name__)))
        
        # Log summary
        success_count = len(documents) - len(failed_docs) - len(skipped_docs)
        logger.info(
            f"Chunking complete: {success_count}/{len(documents)} successful, "
            f"{len(skipped_docs)} skipped, {len(failed_docs)} failed"
        )
        
        if failed_docs:
            logger.warning(f"Failed: {', '.join([f[0] for f in failed_docs])}")
        if skipped_docs:
            logger.warning(f"Skipped: {', '.join([f[0] for f in skipped_docs])}")
        
        if all_chunks:
            self._print_statistics(all_chunks, documents)
        else:
            logger.warning("⚠ No chunks created from any documents")
        
        return all_chunks
    
    def _print_statistics(self, chunks: List[Chunk], documents: List):
        """Print detailed chunking statistics for quality verification."""
        
        if not chunks:
            logger.warning("No chunks to analyze")
            return
        
        # Calculate size statistics
        chunk_sizes = [len(c.text) for c in chunks]
        avg_chunk_size = sum(chunk_sizes) / len(chunks)
        min_chunk_size = min(chunk_sizes)
        max_chunk_size = max(chunk_sizes)
        
        # Count statistics
        avg_chunks_per_doc = len(chunks) / len(documents) if documents else 0
        
        # Group by metadata
        chunks_by_category = {}
        chunks_by_language = {}
        chunks_by_source = {}
        chunks_by_doc = {}
        
        for chunk in chunks:
            category = chunk.metadata.get("category", "unknown")
            language = chunk.metadata.get("language", "unknown")
            source = chunk.metadata.get("source_type", "unknown")
            doc = chunk.metadata.get("source_document", "unknown")
            
            chunks_by_category[category] = chunks_by_category.get(category, 0) + 1
            chunks_by_language[language] = chunks_by_language.get(language, 0) + 1
            chunks_by_source[source] = chunks_by_source.get(source, 0) + 1
            chunks_by_doc[doc] = chunks_by_doc.get(doc, 0) + 1
        
        # Quality check: identify problematic chunks
        very_small_chunks = [c for c in chunks if len(c.text) < self.min_chunk_size // 2]
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("CHUNKING STATISTICS")
        logger.info("="*60)
        logger.info(f"Total chunks created: {len(chunks)}")
        logger.info(f"Total documents processed: {len(documents)}")
        logger.info(f"Avg chunks per document: {avg_chunks_per_doc:.1f}")
        
        logger.info(f"\nChunk Size Statistics (characters):")
        logger.info(f"  Average: {avg_chunk_size:.0f}")
        logger.info(f"  Min: {min_chunk_size}")
        logger.info(f"  Max: {max_chunk_size}")
        logger.info(f"  Target: {self.chunk_size} (±{self.chunk_overlap})")
        
        logger.info(f"\nChunks by Category:")
        for category in sorted(chunks_by_category.keys()):
            count = chunks_by_category[category]
            logger.info(f"  {category}: {count}")
        
        logger.info(f"\nChunks by Language:")
        for language in sorted(chunks_by_language.keys()):
            count = chunks_by_language[language]
            logger.info(f"  {language}: {count}")
        
        logger.info(f"\nChunks by Source Type:")
        for source in sorted(chunks_by_source.keys()):
            count = chunks_by_source[source]
            logger.info(f"  {source}: {count}")
        
        # Quality warnings
        if very_small_chunks:
            logger.warning(
                f"\n⚠ Found {len(very_small_chunks)} very small chunks "
                f"(< {self.min_chunk_size // 2} chars). Consider reviewing merge logic."
            )
        
        logger.info("="*60 + "\n")
    
    def get_chunk_by_id(self, chunks: List[Chunk], chunk_id: str) -> Optional[Chunk]:
        """Retrieve a specific chunk by ID"""
        for chunk in chunks:
            if chunk.chunk_id == chunk_id:
                return chunk
        return None
    
    def get_chunks_by_document(self, chunks: List[Chunk], filename: str) -> List[Chunk]:
        """Get all chunks from a specific document"""
        return [c for c in chunks if c.metadata.get("source_document") == filename]
    
    def get_chunks_by_category(self, chunks: List[Chunk], category: str) -> List[Chunk]:
        """Get all chunks from a specific category"""
        return [c for c in chunks if c.metadata.get("category") == category]
    
    def get_chunks_by_language(self, chunks: List[Chunk], language: str) -> List[Chunk]:
        """Get all chunks in a specific language"""
        return [c for c in chunks if c.metadata.get("language") == language]


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Import DocumentProcessor
    sys.path.append(str(Path(__file__).parent))
    from document_processor import DocumentProcessor
    
    # Process documents
    print("Step 1: Processing documents...")
    base_path = Path(__file__).parent.parent.parent.parent / 'data' / 'documents'
    processor = DocumentProcessor(base_path=str(base_path))
    documents = processor.ingest_documents()
    
    # Chunk documents with hybrid approach
    print("\nStep 2: Chunking documents (hybrid semantic + recursive)...")
    chunker = DocumentChunker(chunk_size=800, chunk_overlap=150, min_chunk_size=200)
    chunks = chunker.chunk_documents(documents)
    
    # Show example chunks from different categories
    if chunks:
        # Group chunks by category
        chunks_by_cat = {}
        for chunk in chunks:
            cat = chunk.metadata.get('category')
            if cat not in chunks_by_cat:
                chunks_by_cat[cat] = []
            chunks_by_cat[cat].append(chunk)
        
        print("\n" + "="*70)
        print("EXAMPLE CHUNKS FROM EACH CATEGORY")
        print("="*70)
        
        for category in sorted(chunks_by_cat.keys()):
            example = chunks_by_cat[category][0]
            print(f"\n📌 Category: {category.upper()}")
            print(f"   ID: {example.chunk_id}")
            print(f"   Language: {example.metadata.get('language')} | Source: {example.metadata.get('source_type')}")
            print(f"   Chunk {example.chunk_index}/{example.metadata.get('total_chunks')-1}")
            print(f"   Size: {len(example.text)} chars")
            print(f"   Preview: {example.text[:150].strip()}...")
            print("-"*70)