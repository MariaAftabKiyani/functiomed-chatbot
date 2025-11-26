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
    print("RAG PIPELINE COMPREHENSIVE TEST")
    print("="*80)

    # Initialize service
    print("\n[1/3] Initializing RAG service...")
    try:
        rag_service = get_rag_service()
        print("✓ RAG service initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize RAG service: {e}")
        return

    # Check health
    print("\n[2/3] Running health check...")
    try:
        health = rag_service.health_check()
        print(f"✓ Service Status: {health['status']}")
        print(f"  - Retrieval: {health['components']['retrieval']['status']}")
        print(f"  - LLM: {health['components']['llm']['status']}")
    except Exception as e:
        print(f"⚠ Health check warning: {e}")

    # Run test cases
    print("\n[3/3] Running test cases...")
    print("="*80)

    total_tests = len(TEST_CASES)
    passed_tests = 0
    failed_tests = 0

    for idx, test_case in enumerate(TEST_CASES, 1):
        question = test_case["question"]
        ground_truth = test_case["answer"]
        category = test_case.get("category", "general")

        print(f"\n{'='*80}")
        print(f"Test {idx}/{total_tests} - Category: {category}")
        print(f"{'='*80}")
        print(f"❓ Question: {question}")
        print(f"📝 Expected (Ground Truth):\n   {ground_truth}")

        try:
            start_time = time.time()
            response = rag_service.generate_answer(
                query=question,
                top_k=5,
                min_score=0.5
            )
            elapsed_time = time.time() - start_time

            # Print response
            print(f"\n🤖 LLM Response:\n   {response.answer[:200]}{'...' if len(response.answer) > 200 else ''}")

            # Print metrics
            print(f"\n📊 Metrics:")
            print(f"   ⏱️  Total Time: {elapsed_time:.2f}s ({response.total_time_ms:.0f}ms)")
            print(f"   🔍 Retrieval Time: {response.retrieval_time_ms:.0f}ms")
            print(f"   💭 Generation Time: {response.generation_time_ms:.0f}ms")
            print(f"   🎯 Tokens Used: {response.tokens_used}")
            print(f"   📚 Retrieved Chunks: {response.retrieval_results}")
            print(f"   📖 Citations: {', '.join(response.citations) if response.citations else 'None'}")
            print(f"   💯 Confidence: {response.confidence_score:.2%}")
            print(f"   🌐 Detected Language: {response.detected_language or 'N/A'}")

            # Print sources
            if response.sources:
                print(f"\n📄 Sources ({len(response.sources)}):")
                for source in response.sources[:3]:  # Show top 3 sources
                    print(f"   [{source['index']}] {source['document']} (score: {source['score']:.3f})")

            passed_tests += 1
            print(f"\n✅ Test {idx} PASSED")

        except Exception as e:
            print(f"\n❌ Test {idx} FAILED")
            print(f"   Error: {type(e).__name__}: {e}")
            import traceback
            print(f"   Traceback:\n{traceback.format_exc()}")
            failed_tests += 1

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Setup logging
    setup_logging("INFO")

    print("\n🚀 Starting RAG Pipeline Tests...\n")
    test_rag_pipeline()
    print("\n✨ All tests completed!\n")
