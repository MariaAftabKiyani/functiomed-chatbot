#!/usr/bin/env python3
"""
Test script for retrieval pipeline.
Validates end-to-end functionality with real queries.
"""
import sys
from pathlib import Path
import logging

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.config import setup_logging
from app.services.retrieval_service import RetrievalService

# Setup logging
setup_logging("INFO")
logger = logging.getLogger(__name__)


def print_result(result, index):
    """Pretty print a single result"""
    print(f"\n{'='*70}")
    print(f"Result #{index + 1}")
    print(f"{'='*70}")
    print(f"Score: {result.score:.4f}")
    print(f"Source: {result.source_document}")
    print(f"Category: {result.category} | Language: {result.language}")
    print(f"Chunk: {result.chunk_index + 1}/{result.total_chunks}")
    print(f"\nText Preview:")
    print(f"{result.text[:300]}...")
    print(f"{'='*70}")


def test_retrieval():
    """Run test queries through retrieval pipeline"""
    
    print("\n" + "="*70)
    print("RETRIEVAL PIPELINE TEST")
    print("="*70)
    
    # Initialize service
    print("\n[1] Initializing RetrievalService...")
    try:
        service = RetrievalService()
        print("✓ Service initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return 1
    
    # Health check
    print("\n[2] Running health check...")
    health = service.health_check()
    print(f"Status: {health['status']}")
    for component, status in health['components'].items():
        print(f"  {component}: {status['status']}")
    
    if health['status'] != 'healthy':
        print("⚠ Service is not healthy, some tests may fail")
    
    # Test queries
    # test_cases = [
    #     {
    #         "name": "German query - Therapies",
    #         "query": "Welche Therapien bietet functiomed an?",
    #         "filters": {"category": ["angebote", "therapy"], "language": "DE"},
    #         "top_k": 3
    #     },
    #     {
    #         "name": "English query - Treatments",
    #         "query": "What treatments do you offer?",
    #         "filters": {"language": "EN"},
    #         "top_k": 3
    #     },
    #     {
    #         "name": "German query - Physiotherapy",
    #         "query": "Wie funktioniert die Physiotherapie?",
    #         "filters": {"category": ["angebote"]},
    #         "top_k": 2
    #     },
    #     {
    #         "name": "No filters - Patient info",
    #         "query": "patient information data privacy",
    #         "filters": {},
    #         "top_k": 3
    #     },
    #     {
    #         "name": "German query - Training",
    #         "query": "Was kostet das functiotraining?",
    #         "filters": {"category": ["training"]},
    #         "top_k": 2
    #     }
    # ]
    test_cases = [
        {
            "name": "Visana therapist list query",
            "query": "Which osteopaths at functiomed are listed on the Visana therapist list?",
            "filters": {"category": ["patient_info"]},
            "top_k": 3,  
            "min_score": 0.4  
        },
        {
            "name": "Uninsured costs explanation",
            "query": "Why does the patient have to pay an uninsured costs amount on the invoice?",
            "filters": {"category": ["patient_info"]},
            "top_k": 5,  
            "min_score": 0.4
        },
        {
            "name": "Medical history retention period",
            "query": "How long does functiomed keep a patient's medical history?",
            "filters": {"category": ["patient_info"]},
            "top_k": 5,  
            "min_score": 0.3  
        },
        {
            "name": "Data disclosure to third parties",
            "query": "When may functiomed disclose my personal or medical data to external third parties?",
            "filters": {"category": ["patient_info"]},
            "top_k": 5,  
            "min_score": 0.4
        }
    ]
    
    print(f"\n[3] Running {len(test_cases)} test queries...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'#'*70}")
        print(f"Test Case {i}: {test_case['name']}")
        print(f"{'#'*70}")
        print(f"Query: '{test_case['query']}'")
        print(f"Filters: {test_case['filters']}")
        print(f"Top K: {test_case['top_k']}")
        
        try:
            # Perform retrieval
            response = service.retrieve(
                query=test_case['query'],
                top_k=test_case['top_k'],
                **test_case['filters']
            )
            
            # Print summary
            print(f"\n✓ Retrieval successful!")
            print(f"  Normalized: '{response.normalized_query}'")
            print(f"  Detected Language: {response.detected_language}")
            print(f"  Results: {response.total_results}")
            print(f"  Time: {response.retrieval_time_ms:.1f}ms")
            
            # Print results
            if response.results:
                for idx, result in enumerate(response.results):
                    print_result(result, idx)
                
                # Test LLM context formatting
                print(f"\n{'='*70}")
                print("LLM Context Format:")
                print(f"{'='*70}")
                context = response.get_context_for_llm(max_tokens=500)
                print(context)
                # print(context[:500] + "..." if len(context) > 500 else context)
            else:
                print("\n⚠ No results found")
            
        except Exception as e:
            print(f"\n✗ Test failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("✓ ALL TESTS COMPLETE")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(test_retrieval())