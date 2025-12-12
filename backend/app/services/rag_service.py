"""
RAG Service - Orchestrates Retrieval and LLM Generation
Combines document retrieval with Llama 3.1 for context-aware responses.
"""
import logging
import time
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import settings
from app.services.retrieval_service import RetrievalService, get_retrieval_service
from app.services.llm_service import LLMService, get_llm_service
from app.utils.prompt_templates import PromptBuilder, get_template
from app.schemas.retrieval import RetrievalResponse

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Complete RAG response with all metadata"""
    answer: str
    sources: List[Dict[str, Any]]
    query: str
    detected_language: Optional[str]
    retrieval_results: int
    citations: List[str]
    confidence_score: float
    total_time_ms: float
    retrieval_time_ms: float
    generation_time_ms: float
    tokens_used: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "answer": self.answer,
            "sources": self.sources,
            "query": self.query,
            "detected_language": self.detected_language,
            "retrieval_results": self.retrieval_results,
            "citations": self.citations,
            "confidence_score": round(self.confidence_score, 2),
            "metrics": {
                "total_time_ms": round(self.total_time_ms, 2),
                "retrieval_time_ms": round(self.retrieval_time_ms, 2),
                "generation_time_ms": round(self.generation_time_ms, 2),
                "tokens_used": self.tokens_used
            }
        }


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) Service.
    
    Pipeline:
    1. Retrieve relevant document chunks
    2. Build context-aware prompt
    3. Generate response with LLM
    4. Extract citations
    5. Validate and format response
    """
    
    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_service: Optional[LLMService] = None
    ):
        """
        Initialize RAG service.
        
        Args:
            retrieval_service: Optional pre-initialized retrieval service
            llm_service: Optional pre-initialized LLM service
        """
        self.retrieval_service = retrieval_service or get_retrieval_service()
        self.llm_service = llm_service or get_llm_service()
        self.prompt_builder = PromptBuilder(
            max_context_tokens=settings.RAG_MAX_CONTEXT_TOKENS
        )
        
        logger.info("RAGService initialized")
        logger.info(f"  Max context tokens: {settings.RAG_MAX_CONTEXT_TOKENS}")
        logger.info(f"  Max chunks: {settings.RAG_MAX_CHUNKS}")
        logger.info(f"  Min score: {settings.RAG_MIN_CHUNK_SCORE}")
    
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a simple greeting (handles typos)"""
        query_lower = query.lower().strip()

        # Exact matches
        greetings = [
            'hi', 'hello', 'hey', 'hallo', 'guten tag', 'guten morgen',
            'guten abend', 'grüß gott', 'servus', 'moin', 'bonjour',
            'salut', 'good morning', 'good afternoon', 'good evening', 'bonsoir'
        ]

        if query_lower in greetings:
            return True

        # Fuzzy matching for common typos (length <= 10 chars, contains greeting-like words)
        if len(query_lower) <= 10:
            # Check for partial matches with common greetings
            greeting_stems = ['hello', 'hi', 'hey', 'hallo', 'hall', 'bonjour', 'bonj', 'salut', 'guten', 'morgen', 'tag', 'abend']
            if any(stem in query_lower for stem in greeting_stems):
                return True

        return False

    def _is_acknowledgment(self, query: str) -> bool:
        """Check if query is a short acknowledgment/filler word"""
        query_lower = query.lower().strip()

        # Remove punctuation for matching
        query_clean = query_lower.strip('.,!?')

        # Exact acknowledgments
        acknowledgments = [
            # English
            'thanks', 'thank you', 'ok', 'okay', 'got it', 'understood',
            'alright', 'well', 'hmm', 'umm', 'sure', 'yeah', 'yep', 'yes',
            # German
            'danke', 'verstanden', 'alles klar', 'gut', 'okay', 'ok', 'ja',
            # French
            'merci', 'ok', 'd\'accord', 'bien', 'oui'
        ]

        # Match exact acknowledgments
        if query_clean in acknowledgments:
            return True

        # Match very short queries (1-2 words, max 15 chars) with acknowledgment stems
        if len(query_clean) <= 15 and len(query_lower.split()) <= 2:
            ack_stems = ['thank', 'ok', 'understood', 'got', 'alright', 'hmm', 'umm',
                        'danke', 'verstanden', 'merci', 'bien', 'gut']
            if any(stem in query_clean for stem in ack_stems):
                return True

        return False

    def _create_greeting_response(self, query: str, language: Optional[str]) -> RAGResponse:
        """Create response for greetings without retrieval"""
        # Use the language passed from UI, default to EN if not provided
        lang_to_use = language.upper() if language else "EN"

        if lang_to_use == "DE":
            answer = "Hallo! Willkommen bei Functiomed. Wie kann ich Ihnen helfen?"
        elif lang_to_use == "FR":
            answer = "Bonjour ! Bienvenue chez Functiomed. Comment puis-je vous aider ?"
        else:
            answer = "Hello! Welcome to Functiomed. How can I help you?"

        return RAGResponse(
            answer=answer,
            sources=[],
            query=query,
            detected_language=lang_to_use,
            retrieval_results=0,
            citations=[],
            confidence_score=1.0,
            total_time_ms=0.0,
            retrieval_time_ms=0.0,
            generation_time_ms=0.0,
            tokens_used=0
        )

    def _create_acknowledgment_response(self, query: str, language: Optional[str]) -> RAGResponse:
        """Create response for acknowledgments without retrieval"""
        # Use the language passed from UI, default to EN if not provided
        lang_to_use = language.upper() if language else "EN"

        if lang_to_use == "DE":
            answer = "Gerne! Lassen Sie mich wissen, wenn Sie weitere Fragen zu Functiomed haben."
        elif lang_to_use == "FR":
            answer = "D'accord ! N'hésitez pas si vous avez d'autres questions sur Functiomed."
        else:
            answer = "Alright! Let me know if you have any other questions about Functiomed."

        return RAGResponse(
            answer=answer,
            sources=[],
            query=query,
            detected_language=lang_to_use,
            retrieval_results=0,
            citations=[],
            confidence_score=1.0,
            total_time_ms=0.0,
            retrieval_time_ms=0.0,
            generation_time_ms=0.0,
            tokens_used=0
        )

    def generate_answer(
        self,
        query: str,
        top_k: Optional[int] = None,
        category: Optional[List[str]] = None,
        language: Optional[str] = None,
        source_type: Optional[str] = None,
        min_score: Optional[float] = None,
        response_style: str = "verbose"
    ) -> RAGResponse:
        """
        Generate answer using RAG pipeline.

        Args:
            query: User question
            top_k: Number of chunks to retrieve
            category: Filter by categories
            language: Filter by language (DE/EN)
            source_type: Filter by source type
            min_score: Minimum similarity score
            response_style: standard or concise

        Returns:
            RAGResponse with answer and metadata

        Raises:
            ValueError: If query is invalid
            RuntimeError: If RAG pipeline fails
        """
        start_time = time.time()

        # CRITICAL: Check for greetings FIRST, before retrieval
        if self._is_greeting(query):
            logger.info(f"Detected greeting - returning direct response in language={language}")
            return self._create_greeting_response(query, language)

        # Check for acknowledgments (thanks, ok, got it, etc.)
        if self._is_acknowledgment(query):
            logger.info(f"Detected acknowledgment - returning direct response in language={language}")
            return self._create_acknowledgment_response(query, language)

        # Use defaults
        top_k = top_k or settings.RAG_MAX_CHUNKS
        min_score = min_score if min_score is not None else settings.RAG_MIN_CHUNK_SCORE

        logger.info(f"RAG pipeline started for query: '{query[:50]}...'")
        logger.debug(f"  Parameters: top_k={top_k}, category={category}, language={language}")

        try:
            # Step 1: Retrieve relevant chunks
            logger.info("[1/4] Retrieving relevant documents...")
            retrieval_response = self._retrieve_context(
                query=query,
                top_k=top_k,
                category=category,
                language=language,
                source_type=source_type,
                min_score=min_score
            )
            
            # Check if we have results
            if not retrieval_response.results:
                logger.warning("No relevant documents found")
                return self._create_fallback_response(
                    query=query,
                    language=language or "DE",
                    retrieval_time_ms=retrieval_response.retrieval_time_ms
                )
            
            logger.info(f"  ✓ Retrieved {retrieval_response.total_results} chunks")
            
            # Step 2: Build prompt with context
            logger.info("[2/4] Building prompt with context...")
            prompt = self._build_prompt(
                retrieval_response=retrieval_response,
                query=query,
                language=language or retrieval_response.detected_language or "DE",
                style=response_style
            )
            logger.debug(f"  Prompt length: {len(prompt)} chars")
            
            # Step 3: Generate response with LLM
            logger.info("[3/4] Generating response with LLM...")
            llm_response = self._generate_response(prompt)
            logger.info(f"  ✓ Generated {llm_response['response_tokens']} tokens")
            
            # Step 4: Post-process and validate
            logger.info("[4/4] Processing and validating response...")
            processed_answer = self._post_process_response(
                llm_response['text'],
                retrieval_response
            )
            
            # Extract citations
            citations = self._extract_citations(llm_response['text'])
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                retrieval_response=retrieval_response,
                citations=citations
            )
            
            # Build complete response
            total_time_ms = (time.time() - start_time) * 1000
            
            rag_response = RAGResponse(
                answer=processed_answer,
                sources=self._format_sources(retrieval_response),
                query=query,
                detected_language=retrieval_response.detected_language,
                retrieval_results=retrieval_response.total_results,
                citations=citations,
                confidence_score=confidence,
                total_time_ms=total_time_ms,
                retrieval_time_ms=retrieval_response.retrieval_time_ms,
                generation_time_ms=llm_response['generation_time_ms'],
                tokens_used=llm_response['total_tokens']
            )
            
            logger.info(
                f"✓ RAG pipeline completed in {total_time_ms:.0f}ms "
                f"(retrieval: {retrieval_response.retrieval_time_ms:.0f}ms, "
                f"generation: {llm_response['generation_time_ms']:.0f}ms)"
            )
            
            return rag_response
            
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            raise
        except Exception as e:
            logger.error(f"RAG pipeline failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"RAG pipeline failed: {e}")
    
    def _retrieve_context(
        self,
        query: str,
        top_k: int,
        category: Optional[List[str]],
        language: Optional[str],
        source_type: Optional[str],
        min_score: float
    ) -> RetrievalResponse:
        """Retrieve relevant document chunks"""
        return self.retrieval_service.retrieve(
            query=query,
            top_k=top_k,
            category=category,
            language=language,
            source_type=source_type,
            min_score=min_score
        )
    
    def _build_prompt(
        self,
        retrieval_response: RetrievalResponse,
        query: str,
        language: str,
        style: str
    ) -> str:
        """Build prompt from retrieval results"""
        # Convert results to context format
        context = [
            {
                "text": result.text,
                "source_document": result.source_document,
                "score": result.score,
                "category": result.category
            }
            for result in retrieval_response.results
        ]

        # Log query token count
        query_tokens = self.llm_service.count_tokens(query)
        logger.info(f"📝 Query tokens: {query_tokens}")

        # Log context details
        context_text = "\n\n".join([c["text"] for c in context])
        context_tokens = self.llm_service.count_tokens(context_text)
        logger.info(f"📚 Retrieved context: {len(context)} chunks, {context_tokens} tokens")
        logger.info(f"📄 Context preview (first 200 chars): {context_text[:200]}...")

        # Get appropriate template
        template = get_template(language=language, style=style)
        self.prompt_builder.template = template

        # Build prompt with token management
        prompt = self.prompt_builder.build_prompt(
            context=context,
            query=query,
            language=language,
            token_counter=self.llm_service.count_tokens
        )

        # Log final prompt details
        prompt_tokens = self.llm_service.count_tokens(prompt)
        logger.info(f"🔧 Final prompt: {prompt_tokens} tokens")
        logger.info(f"📋 Full prompt:\n{'='*80}\n{prompt}\n{'='*80}")

        return prompt
    
    def _generate_response(self, prompt: str) -> Dict[str, Any]:
        """Generate response using LLM"""
        logger.info(f"🤖 Generating LLM response (max_tokens={settings.LLM_MAX_TOKENS}, temp={settings.LLM_TEMPERATURE})...")

        response = self.llm_service.generate(
            prompt=prompt,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE
        )

        # Log response details
        response_tokens = response.get('response_tokens', 0)
        response_text = response.get('text', '')
        logger.info(f"✅ LLM generated {response_tokens} tokens")
        logger.info(f"📝 Raw LLM response:\n{'='*80}\n{response_text}\n{'='*80}")

        return response
    
    def _post_process_response(
        self,
        response: str,
        retrieval_response: RetrievalResponse
    ) -> str:
        """
        Post-process and validate LLM response.

        - Remove leaked KONTEXT/source metadata
        - Preserve Markdown formatting
        - Clean up excessive whitespace
        """
        logger.info(f"🧹 Post-processing response ({len(response)} chars before cleaning)...")

        # Remove leading/trailing whitespace
        response = response.strip()

        # CRITICAL: Remove any leaked KONTEXT sections or source metadata
        # Remove "KONTEXT:" headers and everything after them if they appear
        response = re.sub(r'KONTEXT:.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'AVAILABLE INFORMATION:.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)

        # Remove standalone source citations like "[1] Source: filename.pdf (Relevance: 0.85)"
        # But keep markdown links and normal citations [1], [2]
        response = re.sub(r'\[\d+\]\s*(?:Source|Quelle):\s*[^\n]+\((?:Relevance|Relevanz|Pertinence):\s*[\d.]+\)', '', response, flags=re.IGNORECASE)

        # Remove unwanted remarks and notes at the end
        response = re.sub(r'CRITICAL REMARK:.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'IMPORTANT NOTE:.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'Please note that.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)

        # Remove leaked system instructions
        response = re.sub(r'REMEMBER:.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'Note: This is a sample.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'Never diagnose medical conditions.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'DO NOT (?:diagnose|provide|give).*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)

        # Clean up multiple newlines (max 2 consecutive for markdown spacing)
        response = re.sub(r'\n{3,}', '\n\n', response)

        # Clean up multiple spaces (but preserve markdown formatting)
        response = re.sub(r' {3,}', '  ', response)  # Allow 2 spaces for markdown line breaks

        # Ensure response is not empty
        if not response.strip():
            response = "Entschuldigung, ich konnte keine passende Antwort generieren."

        logger.info(f"✅ Post-processing complete ({len(response)} chars after cleaning)")
        logger.info(f"📝 Final response:\n{'='*80}\n{response}\n{'='*80}")

        return response.strip()
    
    def _extract_citations(self, text: str) -> List[str]:
        """
        Extract citation markers from text.
        
        Args:
            text: Response text
            
        Returns:
            List of unique citations like ['[1]', '[2]']
        """
        # Find all [N] patterns
        citations = re.findall(r'\[\d+\]', text)
        
        # Return unique citations in order
        seen = set()
        unique_citations = []
        for cite in citations:
            if cite not in seen:
                seen.add(cite)
                unique_citations.append(cite)
        
        return unique_citations
    
    def _calculate_confidence(
        self,
        retrieval_response: RetrievalResponse,
        citations: List[str]
    ) -> float:
        """
        Calculate confidence score for response.
        
        Factors:
        - Average retrieval score
        - Number of results
        - Citation usage
        
        Returns:
            Confidence score between 0-1
        """
        if not retrieval_response.results:
            return 0.0
        
        # Average retrieval score (weight: 0.6)
        avg_score = sum(r.score for r in retrieval_response.results) / len(retrieval_response.results)
        score_component = avg_score * 0.6
        
        # Number of results (weight: 0.2)
        # More results = higher confidence (up to 5 results)
        results_component = min(len(retrieval_response.results) / 5.0, 1.0) * 0.2
        
        # Citation usage (weight: 0.2)
        # Did LLM use citations? If yes, higher confidence
        citation_component = min(len(citations) / 3.0, 1.0) * 0.2
        
        confidence = score_component + results_component + citation_component
        
        return min(confidence, 1.0)
    
    def _format_sources(self, retrieval_response: RetrievalResponse) -> List[Dict[str, Any]]:
        """Format retrieval results as source list"""
        sources = []
        
        for idx, result in enumerate(retrieval_response.results, 1):
            source = {
                "index": idx,
                "document": result.source_document,
                "category": result.category,
                "score": round(result.score, 3),
                "chunk": f"{result.chunk_index}/{result.total_chunks}"
            }
            sources.append(source)
        
        return sources
    
    def _create_fallback_response(
        self,
        query: str,
        language: str,
        retrieval_time_ms: float
    ) -> RAGResponse:
        """Create fallback response when no context is found"""
        # Normalize language to uppercase for comparison
        lang_upper = language.upper() if language else "DE"

        if lang_upper == "EN":
            answer = settings.RAG_FALLBACK_RESPONSE_EN
        elif lang_upper == "FR":
            answer = settings.RAG_FALLBACK_RESPONSE_FR
        else:
            answer = settings.RAG_FALLBACK_RESPONSE_DE
        
        return RAGResponse(
            answer=answer,
            sources=[],
            query=query,
            detected_language=language,
            retrieval_results=0,
            citations=[],
            confidence_score=0.0,
            total_time_ms=retrieval_time_ms,
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=0.0,
            tokens_used=0
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of RAG service components"""
        health = {
            "service": "RAGService",
            "status": "healthy",
            "components": {}
        }
        
        # Check retrieval service
        try:
            retrieval_health = self.retrieval_service.health_check()
            health["components"]["retrieval"] = retrieval_health
            if retrieval_health["status"] != "healthy":
                health["status"] = "degraded"
        except Exception as e:
            health["components"]["retrieval"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
        
        # Check LLM service
        try:
            llm_health = self.llm_service.health_check()
            health["components"]["llm"] = llm_health
            if llm_health["status"] != "healthy":
                health["status"] = "degraded"
        except Exception as e:
            health["components"]["llm"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
        
        return health


# Singleton instance
_rag_service_instance = None

def get_rag_service() -> RAGService:
    """
    Get or create singleton RAGService instance.
    
    Returns:
        Initialized RAGService
    """
    global _rag_service_instance
    
    if _rag_service_instance is None:
        logger.info("Creating new RAGService instance")
        _rag_service_instance = RAGService()
    
    return _rag_service_instance