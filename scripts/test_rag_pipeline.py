"""
Comprehensive RAG Pipeline Test Script
Tests retrieval, generation, and full pipeline performance.
"""
import time
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import setup_logging
from app.services.rag_service import get_rag_service

# Test Cases
TEST_CASES = [
    {
        "question": "What are prices of functiomed?",
        "answer": "30min Fr. 108.- 45min Fr. 159.- First consultation additional Fr. 20.- Emergency surcharge additional Fr. 40.-",
        "category": "pricing"
    }
]

def test_rag_pipeline():
    """Run comprehensive RAG pipeline tests"""

    print("\n" + "="*80)
    print("RAG PIPELINE TEST")
    print("="*80)

    # Initialize service
    try:
        rag_service = get_rag_service()
        health = rag_service.health_check()
        print(f"✓ Service initialized | Retrieval: {health['components']['retrieval']['status']} | LLM: {health['components']['llm']['status']}")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return

    for idx, test_case in enumerate(TEST_CASES, 1):
        question = test_case["question"]
        ground_truth = test_case["answer"]
        category = test_case.get("category", "general")

        print(f"\n{'='*80}")
        print(f"Test Category: {category}")
        print(f"Q: {question}")
        print(f"Expected: {ground_truth}")
        print(f"{'='*80}")

        try:
            start_time = time.time()
            response = rag_service.generate_answer(
                query=question,
                top_k=5,
                min_score=0.5
            )
            elapsed_time = time.time() - start_time

            # Response and key metrics
            print(f"\nAnswer: {response.answer}")
            print(f"\nPerformance: {elapsed_time:.2f}s total | Retrieval: {response.retrieval_time_ms:.0f}ms | Generation: {response.generation_time_ms:.0f}ms")
            print(f"Quality: {response.retrieval_results} chunks retrieved | Confidence: {response.confidence_score:.2%} | Tokens: {response.tokens_used}")

            # Sources with relevance scores
            if response.sources:
                print(f"\nTop {min(3, len(response.sources))} Sources:")
                for source in response.sources[:3]:
                    print(f"  • {source['document']} (relevance: {source['score']:.3f})")
            else:
                print("\n⚠ Warning: No sources retrieved - answer may be unreliable")

            # Citations check
            if not response.citations:
                print("⚠ Warning: No citations provided in answer")

        except Exception as e:
            print(f"\n❌ FAILED: {type(e).__name__}: {e}")
            import traceback
            print(f"\nTraceback:\n{traceback.format_exc()}")


if __name__ == "__main__":
    setup_logging("INFO")
    test_rag_pipeline()
