"""
BM25 Search Service for Keyword-based Retrieval
Provides traditional keyword matching to complement semantic search.
"""
import logging
import pickle
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from collections import Counter
import math

logger = logging.getLogger(__name__)


class BM25:
    """
    BM25 (Best Match 25) ranking function.

    Combines:
    - Term frequency (TF)
    - Inverse document frequency (IDF)
    - Document length normalization

    Formula:
    score(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))

    where:
    - qi = query term i
    - f(qi, D) = frequency of qi in document D
    - |D| = length of document D
    - avgdl = average document length
    - k1, b = tuning parameters
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25.

        Args:
            k1: Term frequency saturation parameter (1.2-2.0)
            b: Length normalization parameter (0.75 typical)
        """
        self.k1 = k1
        self.b = b

        # Index data
        self.corpus = []
        self.corpus_metadata = []
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self.avgdl = 0
        self.num_docs = 0

        logger.info(f"BM25 initialized with k1={k1}, b={b}")

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text with medical-aware processing.

        - Lowercase
        - Remove punctuation (except hyphens in medical terms)
        - Split on whitespace
        - Remove very short tokens
        """
        # Lowercase
        text = text.lower()

        # Preserve medical terms with hyphens (e.g., "colon-hydro-therapie")
        # Replace other punctuation with spaces
        text = re.sub(r'[^\w\s\-äöüßàâéèêëïôùûç]', ' ', text)

        # Split on whitespace
        tokens = text.split()

        # Remove very short tokens and numbers-only tokens
        tokens = [
            t for t in tokens
            if len(t) > 2 and not t.isdigit()
        ]

        return tokens

    def index(self, corpus: List[str], metadata: List[Dict[str, Any]]):
        """
        Index a corpus of documents.

        Args:
            corpus: List of document texts
            metadata: List of metadata dicts (must match corpus length)
        """
        logger.info(f"Indexing {len(corpus)} documents with BM25...")

        if len(corpus) != len(metadata):
            raise ValueError(f"Corpus ({len(corpus)}) and metadata ({len(metadata)}) length mismatch")

        self.corpus = corpus
        self.corpus_metadata = metadata
        self.num_docs = len(corpus)

        # Tokenize all documents
        self.doc_freqs = []
        self.doc_len = []

        for doc in corpus:
            tokens = self._tokenize(doc)
            self.doc_freqs.append(Counter(tokens))
            self.doc_len.append(len(tokens))

        # Calculate average document length
        self.avgdl = sum(self.doc_len) / self.num_docs if self.num_docs > 0 else 0

        # Calculate IDF for each term
        df = {}  # Document frequency for each term

        for doc_freq in self.doc_freqs:
            for term in doc_freq.keys():
                df[term] = df.get(term, 0) + 1

        # IDF(q) = ln((N - df(q) + 0.5) / (df(q) + 0.5) + 1)
        self.idf = {}
        for term, freq in df.items():
            self.idf[term] = math.log(
                (self.num_docs - freq + 0.5) / (freq + 0.5) + 1.0
            )

        logger.info(f"✓ BM25 index built: {self.num_docs} docs, {len(self.idf)} unique terms")
        logger.info(f"  Avg doc length: {self.avgdl:.1f} tokens")

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search corpus using BM25.

        Args:
            query: Search query
            top_k: Number of top results to return
            filters: Optional metadata filters (category, language, etc.)

        Returns:
            List of dicts with 'text', 'score', 'metadata', 'rank'
        """
        if self.num_docs == 0:
            logger.warning("BM25 index is empty")
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)

        if not query_tokens:
            logger.warning(f"Query tokenized to empty: '{query}'")
            return []

        # Calculate BM25 score for each document
        scores = []

        for doc_idx, doc_freq in enumerate(self.doc_freqs):
            # Apply filters if provided
            if filters:
                if not self._matches_filters(self.corpus_metadata[doc_idx], filters):
                    scores.append(0.0)
                    continue

            score = 0.0
            doc_length = self.doc_len[doc_idx]

            for term in query_tokens:
                if term not in doc_freq:
                    continue

                # Term frequency in document
                freq = doc_freq[term]

                # IDF component
                idf = self.idf.get(term, 0)

                # BM25 formula
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (
                    1 - self.b + self.b * (doc_length / self.avgdl)
                )

                score += idf * (numerator / denominator)

            scores.append(score)

        # Get top-k results
        # Normalize scores to [0, 1] range
        max_score = max(scores) if scores else 1.0
        if max_score > 0:
            scores = [s / max_score for s in scores]

        # Sort by score descending
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, 1):
            if scores[idx] > 0:  # Only include non-zero scores
                results.append({
                    'text': self.corpus[idx],
                    'score': float(scores[idx]),
                    'metadata': self.corpus_metadata[idx],
                    'rank': rank,
                    'doc_index': int(idx)
                })

        logger.debug(f"BM25 search: query='{query[:50]}...', results={len(results)}")

        return results

    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document metadata matches filters"""
        for key, value in filters.items():
            if key not in metadata:
                continue

            # Handle list values (OR logic)
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            # Handle single values
            elif metadata[key] != value:
                return False

        return True

    def save_index(self, filepath: str):
        """Save BM25 index to disk"""
        index_data = {
            'k1': self.k1,
            'b': self.b,
            'corpus': self.corpus,
            'corpus_metadata': self.corpus_metadata,
            'doc_freqs': self.doc_freqs,
            'idf': self.idf,
            'doc_len': self.doc_len,
            'avgdl': self.avgdl,
            'num_docs': self.num_docs
        }

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'wb') as f:
            pickle.dump(index_data, f)

        logger.info(f"✓ BM25 index saved to {filepath}")

    def load_index(self, filepath: str):
        """Load BM25 index from disk"""
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"BM25 index not found: {filepath}")

        with open(filepath, 'rb') as f:
            index_data = pickle.load(f)

        self.k1 = index_data['k1']
        self.b = index_data['b']
        self.corpus = index_data['corpus']
        self.corpus_metadata = index_data['corpus_metadata']
        self.doc_freqs = index_data['doc_freqs']
        self.idf = index_data['idf']
        self.doc_len = index_data['doc_len']
        self.avgdl = index_data['avgdl']
        self.num_docs = index_data['num_docs']

        logger.info(f"✓ BM25 index loaded from {filepath}: {self.num_docs} docs")


class HybridSearchFusion:
    """
    Combines BM25 (keyword) and semantic (vector) search results.

    Uses Reciprocal Rank Fusion (RRF) or weighted scoring.
    """

    @staticmethod
    def reciprocal_rank_fusion(
        bm25_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF).

        RRF score = Σ 1 / (k + rank)

        Args:
            bm25_results: Results from BM25 search
            semantic_results: Results from vector search
            k: RRF constant (typically 60)

        Returns:
            Fused results sorted by RRF score
        """
        # Build document index by chunk_id or text
        doc_scores = {}

        # Add BM25 scores
        for rank, result in enumerate(bm25_results, 1):
            doc_id = result['metadata'].get('chunk_id', result.get('text', ''))
            rrf_score = 1.0 / (k + rank)

            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'result': result,
                    'bm25_rrf': rrf_score,
                    'semantic_rrf': 0.0,
                    'bm25_rank': rank,
                    'semantic_rank': None
                }
            else:
                doc_scores[doc_id]['bm25_rrf'] = rrf_score
                doc_scores[doc_id]['bm25_rank'] = rank

        # Add semantic scores
        for rank, result in enumerate(semantic_results, 1):
            doc_id = result.get('payload', {}).get('chunk_id', result.get('text', ''))
            rrf_score = 1.0 / (k + rank)

            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'result': result,
                    'bm25_rrf': 0.0,
                    'semantic_rrf': rrf_score,
                    'bm25_rank': None,
                    'semantic_rank': rank
                }
            else:
                doc_scores[doc_id]['semantic_rrf'] = rrf_score
                doc_scores[doc_id]['semantic_rank'] = rank

        # Calculate final RRF scores
        for doc_id in doc_scores:
            doc_scores[doc_id]['final_score'] = (
                doc_scores[doc_id]['bm25_rrf'] +
                doc_scores[doc_id]['semantic_rrf']
            )

        # Sort by final score
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )

        return [item['result'] for item in sorted_docs]

    @staticmethod
    def weighted_fusion(
        bm25_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        alpha: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Weighted score fusion.

        Final score = alpha * semantic_score + (1 - alpha) * bm25_score

        Args:
            bm25_results: Results from BM25 search
            semantic_results: Results from vector search
            alpha: Weight for semantic search (0-1)

        Returns:
            Fused results sorted by weighted score
        """
        # Build document index
        doc_scores = {}

        # Add BM25 scores
        for result in bm25_results:
            doc_id = result['metadata'].get('chunk_id', result.get('text', ''))
            doc_scores[doc_id] = {
                'result': result,
                'bm25_score': result['score'],
                'semantic_score': 0.0
            }

        # Add semantic scores
        for result in semantic_results:
            payload = result.get('payload', {})
            doc_id = payload.get('chunk_id', result.get('text', ''))
            score = result.get('score', 0.0)

            if doc_id in doc_scores:
                doc_scores[doc_id]['semantic_score'] = score
            else:
                doc_scores[doc_id] = {
                    'result': result,
                    'bm25_score': 0.0,
                    'semantic_score': score
                }

        # Calculate weighted scores
        for doc_id in doc_scores:
            doc_scores[doc_id]['final_score'] = (
                alpha * doc_scores[doc_id]['semantic_score'] +
                (1 - alpha) * doc_scores[doc_id]['bm25_score']
            )

        # Sort by final score
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )

        return [item['result'] for item in sorted_docs]


# Singleton instance
_bm25_instance = None

def get_bm25_search(
    index_path: Optional[str] = None,
    k1: Optional[float] = None,
    b: Optional[float] = None
) -> BM25:
    """
    Get or create singleton BM25 instance.

    Args:
        index_path: Path to load/save BM25 index
        k1: BM25 k1 parameter
        b: BM25 b parameter

    Returns:
        Initialized BM25 instance
    """
    global _bm25_instance

    if _bm25_instance is None:
        from app.config import settings

        k1 = k1 or settings.BM25_K1
        b = b or settings.BM25_B

        _bm25_instance = BM25(k1=k1, b=b)

        # Try to load existing index
        if index_path and Path(index_path).exists():
            try:
                _bm25_instance.load_index(index_path)
                logger.info("Loaded existing BM25 index")
            except Exception as e:
                logger.warning(f"Failed to load BM25 index: {e}")

    return _bm25_instance
