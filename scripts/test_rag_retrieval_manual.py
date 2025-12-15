"""
RAG Retrieval Manual Review Script for Functiomed Chatbot

This script retrieves chunks for test queries and displays them for manual review.
No automatic accuracy metrics - you judge quality yourself by reading the results.

Usage:
    # Run with GPU (default)
    python scripts/test_rag_retrieval_manual.py

    # Run specific number of queries
    python scripts/test_rag_retrieval_manual.py --limit 10

    # Export to HTML for easier reading
    python scripts/test_rag_retrieval_manual.py --export-html review.html

    # Export to JSON
    python scripts/test_rag_retrieval_manual.py --export-json results.json
"""

import sys
import time
import json
import logging
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Force GPU usage if available
os.environ['EMBEDDING_DEVICE'] = 'cuda'

from app.services.retrieval_service import RetrievalService, get_retrieval_service
from app.config import settings

# Try to import torch to verify CUDA availability
try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        DEVICE_NAME = torch.cuda.get_device_name(0)
except ImportError:
    CUDA_AVAILABLE = False
    DEVICE_NAME = "CPU"

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Less verbose
    format='%(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestQuery:
    """A test query with expected results for manual review"""
    query: str
    language: str
    expected_categories: List[str]
    expected_documents: List[str]
    description: str
    relevance_threshold: float = 0.5


class ManualReviewTester:
    """Simple tester that shows retrieved chunks for manual review"""

    def __init__(self, retrieval_service: Optional[RetrievalService] = None):
        """Initialize tester with retrieval service"""
        self.retrieval_service = retrieval_service or get_retrieval_service()

        print("\n" + "="*100)
        print("RAG RETRIEVAL MANUAL REVIEW TESTER")
        print("="*100)
        print(f"Device: {DEVICE_NAME}")
        print(f"Top-K chunks per query: {settings.RAG_MAX_CHUNKS}")
        print(f"Min similarity score: {settings.RAG_MIN_CHUNK_SCORE}")
        print("="*100 + "\n")

    def create_test_queries(self) -> List[TestQuery]:
        """Create comprehensive test query dataset"""
        # Import the same queries from the accuracy script
        # This ensures consistency
        return [
            # Practice Admin
            TestQuery(
                query="Wie lautet die Adresse von Functiomed?",
                language="DE",
                expected_categories=["praxis-info"],
                expected_documents=["kontakt"],
                description="Practice address"
            ),
            TestQuery(
                query="Was sind die Öffnungszeiten?",
                language="DE",
                expected_categories=["praxis-info", "patient_info"],
                expected_documents=["kontakt", "FAQ"],
                description="Opening hours"
            ),
            TestQuery(
                query="Gibt es Parkmöglichkeiten?",
                language="DE",
                expected_categories=["patient_info"],
                expected_documents=["FAQ"],
                description="Parking availability"
            ),
            TestQuery(
                query="Wie kann ich einen Termin vereinbaren?",
                language="DE",
                expected_categories=["praxis-info", "patient_info"],
                expected_documents=["kontakt", "FAQ"],
                description="Appointment booking"
            ),

            # Staff & Doctors
            TestQuery(
                query="Wer ist der CEO von Functiomed?",
                language="DE",
                expected_categories=["praxis-info"],
                expected_documents=["team"],
                description="CEO identity"
            ),
            TestQuery(
                query="Wer ist Prof. Martin Spring?",
                language="DE",
                expected_categories=["praxis-info"],
                expected_documents=["team"],
                description="CEO details"
            ),
            TestQuery(
                query="Welche Ärzte arbeiten bei Functiomed?",
                language="DE",
                expected_categories=["praxis-info"],
                expected_documents=["team"],
                description="Doctors list"
            ),

            # Services & Therapies
            TestQuery(
                query="Was ist Osteopathie?",
                language="DE",
                expected_categories=["angebote", "patient_info"],
                expected_documents=["osteopathie", "FAQ"],
                description="Osteopathy definition"
            ),
            TestQuery(
                query="Welche Therapien bietet Functiomed an?",
                language="DE",
                expected_categories=["angebote", "patient_info"],
                expected_documents=["FAQ"],
                description="Available therapies"
            ),
            TestQuery(
                query="Was ist Kinderosteopathie?",
                language="DE",
                expected_categories=["angebote"],
                expected_documents=["kinderosteopathie"],
                description="Pediatric osteopathy"
            ),
            TestQuery(
                query="Was ist Akupunktur?",
                language="DE",
                expected_categories=["angebote", "patient_info"],
                expected_documents=["akupunktur", "FAQ"],
                description="Acupuncture info"
            ),
            TestQuery(
                query="Welche Massagen werden angeboten?",
                language="DE",
                expected_categories=["angebote", "patient_info"],
                expected_documents=["massage", "FAQ"],
                description="Massage types"
            ),
            TestQuery(
                query="Was ist integrative Medizin?",
                language="DE",
                expected_categories=["angebote", "patient_info"],
                expected_documents=["integrative_medizin", "FAQ"],
                description="Integrative medicine"
            ),
            TestQuery(
                query="Was behandelt die Rheumatologie?",
                language="DE",
                expected_categories=["angebote", "patient_info"],
                expected_documents=["rheumatologie", "FAQ"],
                description="Rheumatology treatments"
            ),
            TestQuery(
                query="Was ist Colon-Hydro-Therapie?",
                language="DE",
                expected_categories=["angebote"],
                expected_documents=["colon-hydro"],
                description="Colon hydro therapy"
            ),

            # Nutrition
            TestQuery(
                query="Welche Ernährungsberatung gibt es?",
                language="DE",
                expected_categories=["ernaehrung"],
                expected_documents=["erspe", "fitamara"],
                description="Nutrition counseling"
            ),

            # Training
            TestQuery(
                query="Was ist Functiotraining?",
                language="DE",
                expected_categories=["training"],
                expected_documents=["functiotraining"],
                description="Functiotraining program"
            ),

            # Billing & Insurance
            # TestQuery(
            #     query="Werden die Kosten von der Krankenkasse übernommen?",
            #     language="DE",
            #     expected_categories=["patient_info"],
            #     expected_documents=["FAQ"],
            #     description="Insurance coverage"
            # ),
            # TestQuery(
            #     query="Visana Patienten Informationen",
            #     language="DE",
            #     expected_categories=["patient_info"],
            #     expected_documents=["Visana"],
            #     description="Visana info"
            # ),
            # TestQuery(
            #     query="Benötige ich eine Überweisung?",
            #     language="DE",
            #     expected_categories=["patient_info"],
            #     expected_documents=["FAQ"],
            #     description="Referral requirement"
            # ),

            # # Policies
            # TestQuery(
            #     query="Datenschutz bei Functiomed",
            #     language="DE",
            #     expected_categories=["patient_info"],
            #     expected_documents=["Datenschutz"],
            #     description="Data protection"
            # ),
            # TestQuery(
            #     query="Wie melde ich mich als neuer Patient an?",
            #     language="DE",
            #     expected_categories=["patient_info"],
            #     expected_documents=["Anmeldung"],
            #     description="New patient registration"
            # ),

            # # FAQs
            # TestQuery(
            #     query="Wie viele Osteopathie-Sitzungen brauche ich?",
            #     language="DE",
            #     expected_categories=["patient_info"],
            #     expected_documents=["FAQ"],
            #     description="Number of sessions"
            # ),
            # TestQuery(
            #     query="Muss ich nüchtern zur Blutabnahme kommen?",
            #     language="DE",
            #     expected_categories=["patient_info"],
            #     expected_documents=["FAQ"],
            #     description="Fasting requirement"
            # ),

            # # Complex queries
            # TestQuery(
            #     query="Ich habe Rückenschmerzen, welche Behandlungen helfen?",
            #     language="DE",
            #     expected_categories=["angebote"],
            #     expected_documents=["physiotherapie", "osteopathie", "massage"],
            #     description="Symptom-based treatment"
            # ),
            # TestQuery(
            #     query="Welche Behandlungen für Schwangere gibt es?",
            #     language="DE",
            #     expected_categories=["angebote"],
            #     expected_documents=["schwangerschaft", "osteopathie"],
            #     description="Pregnancy treatments"
            # ),

            # # English queries
            # TestQuery(
            #     query="What is osteopathy?",
            #     language="EN",
            #     expected_categories=["angebote", "patient_info"],
            #     expected_documents=["osteopathie", "FAQ"],
            #     description="Osteopathy (English)"
            # ),
            # TestQuery(
            #     query="How can I book an appointment?",
            #     language="EN",
            #     expected_categories=["praxis-info"],
            #     expected_documents=["kontakt", "FAQ"],
            #     description="Appointment booking (English)"
            # ),

            # # Edge cases
            # TestQuery(
            #     query="Notfall",
            #     language="DE",
            #     expected_categories=["praxis-info"],
            #     expected_documents=["notfall"],
            #     description="Emergency (single word)"
            # ),
            # TestQuery(
            #     query="Öffnungszeiten",
            #     language="DE",
            #     expected_categories=["patient_info"],
            #     expected_documents=["FAQ"],
            #     description="Opening hours (single word)"
            # ),
        ]

    def test_query(self, test_query: TestQuery, top_k: int = 5) -> Dict[str, Any]:
        """
        Test a single query and return results for review.

        Returns dict with query, expected docs, and retrieved chunks.
        """
        start_time = time.time()

        try:
            # Retrieve chunks
            response = self.retrieval_service.retrieve(
                query=test_query.query,
                top_k=top_k,
                language=test_query.language,
                min_score=test_query.relevance_threshold
            )

            retrieval_time = (time.time() - start_time) * 1000

            # Format results
            retrieved_chunks = []
            for idx, result in enumerate(response.results, 1):
                retrieved_chunks.append({
                    "rank": idx,
                    "document": result.source_document,
                    "category": result.category,
                    "score": round(result.score, 4),
                    "chunk_index": f"{result.chunk_index}/{result.total_chunks}",
                    "text": result.text.strip()
                })

            return {
                "query": test_query.query,
                "description": test_query.description,
                "language": test_query.language,
                "expected_categories": test_query.expected_categories,
                "expected_documents": test_query.expected_documents,
                "retrieved_count": len(retrieved_chunks),
                "retrieved_chunks": retrieved_chunks,
                "retrieval_time_ms": round(retrieval_time, 2),
                "success": True
            }

        except Exception as e:
            return {
                "query": test_query.query,
                "description": test_query.description,
                "expected_documents": test_query.expected_documents,
                "error": str(e),
                "success": False
            }

    def print_review(self, result: Dict[str, Any]):
        """Print a single result for manual review"""
        print("\n" + "="*100)
        print(f"QUERY #{result.get('index', '?')}: {result['description']}")
        print("="*100)
        print(f"\n📝 Query: \"{result['query']}\"")
        print(f"🌍 Language: {result['language']}")

        # Ground truth
        print(f"\n✅ EXPECTED DOCUMENTS:")
        for doc in result['expected_documents']:
            print(f"   • {doc}")

        print(f"\n📂 EXPECTED CATEGORIES:")
        for cat in result['expected_categories']:
            print(f"   • {cat}")

        # Results
        if not result['success']:
            print(f"\n❌ ERROR: {result['error']}")
            return

        print(f"\n🔍 RETRIEVED: {result['retrieved_count']} chunks ({result['retrieval_time_ms']}ms)")
        print("\n" + "-"*100)

        # Show each retrieved chunk
        for chunk in result['retrieved_chunks']:
            print(f"\n📄 RANK #{chunk['rank']} | Score: {chunk['score']}")
            print(f"   Document: {chunk['document']}")
            print(f"   Category: {chunk['category']}")
            print(f"   Chunk: {chunk['chunk_index']}")
            print(f"\n   TEXT:")
            print("   " + "-"*96)
            # Wrap text nicely
            text_lines = chunk['text'].split('\n')
            for line in text_lines:
                if len(line) <= 96:
                    print(f"   {line}")
                else:
                    # Wrap long lines
                    words = line.split()
                    current_line = "   "
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 100:
                            current_line += word + " "
                        else:
                            print(current_line.rstrip())
                            current_line = "   " + word + " "
                    if current_line.strip():
                        print(current_line.rstrip())
            print("   " + "-"*96)

        print("\n" + "="*100)

    def export_to_json(self, results: List[Dict[str, Any]], filepath: str):
        """Export results to JSON file"""
        output = {
            "test_date": datetime.now().isoformat(),
            "device": DEVICE_NAME,
            "total_queries": len(results),
            "successful_queries": sum(1 for r in results if r['success']),
            "results": results
        }

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Results exported to: {output_path}")

    def export_to_html(self, results: List[Dict[str, Any]], filepath: str):
        """Export results to HTML file for easier reading"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RAG Retrieval Manual Review</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .query-card {
            background: white;
            padding: 25px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .query-title {
            font-size: 24px;
            color: #333;
            margin-bottom: 15px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        .query-text {
            font-size: 18px;
            color: #555;
            font-style: italic;
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
        }
        .expected {
            background: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .expected h3 {
            color: #2e7d32;
            margin-top: 0;
        }
        .expected ul {
            margin: 5px 0;
            padding-left: 25px;
        }
        .chunk {
            background: #fff9e6;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        .chunk-header {
            font-weight: bold;
            color: #f57c00;
            margin-bottom: 10px;
        }
        .chunk-meta {
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
        }
        .chunk-text {
            background: white;
            padding: 15px;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.6;
        }
        .score-high { color: #4caf50; font-weight: bold; }
        .score-medium { color: #ff9800; font-weight: bold; }
        .score-low { color: #f44336; font-weight: bold; }
        .stats {
            background: #fff;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 RAG Retrieval Manual Review</h1>
        <p>Test Date: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p>Device: """ + DEVICE_NAME + """</p>
        <p>Total Queries: """ + str(len(results)) + """</p>
    </div>
"""

        for idx, result in enumerate(results, 1):
            if not result['success']:
                html += f"""
    <div class="query-card">
        <div class="query-title">Query #{idx}: {result['description']}</div>
        <div class="query-text">{result['query']}</div>
        <p style="color: red;">❌ ERROR: {result.get('error', 'Unknown error')}</p>
    </div>
"""
                continue

            html += f"""
    <div class="query-card">
        <div class="query-title">Query #{idx}: {result['description']}</div>
        <div class="query-text">"{result['query']}"</div>

        <div class="stats">
            <strong>Language:</strong> {result['language']} |
            <strong>Retrieved:</strong> {result['retrieved_count']} chunks |
            <strong>Time:</strong> {result['retrieval_time_ms']}ms
        </div>

        <div class="expected">
            <h3>✅ Expected Results (Ground Truth)</h3>
            <strong>Documents:</strong> {', '.join(result['expected_documents'])}<br>
            <strong>Categories:</strong> {', '.join(result['expected_categories'])}
        </div>

        <h3>📄 Retrieved Chunks:</h3>
"""

            for chunk in result['retrieved_chunks']:
                score = chunk['score']
                score_class = 'score-high' if score >= 0.7 else 'score-medium' if score >= 0.5 else 'score-low'

                html += f"""
        <div class="chunk">
            <div class="chunk-header">
                Rank #{chunk['rank']} | Score: <span class="{score_class}">{chunk['score']}</span>
            </div>
            <div class="chunk-meta">
                📁 Document: {chunk['document']}<br>
                📂 Category: {chunk['category']}<br>
                📑 Chunk: {chunk['chunk_index']}
            </div>
            <div class="chunk-text">{chunk['text']}</div>
        </div>
"""

            html += """
    </div>
"""

        html += """
</body>
</html>
"""

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ HTML review exported to: {output_path}")
        print(f"   Open this file in your browser to review results visually")

    def run_tests(self, limit: Optional[int] = None, top_k: int = 5):
        """Run all tests and collect results"""
        queries = self.create_test_queries()

        if limit:
            queries = queries[:limit]

        print(f"\nRunning {len(queries)} test queries...\n")

        results = []
        for idx, query in enumerate(queries, 1):
            print(f"Testing [{idx}/{len(queries)}]: {query.description}...", end=' ')
            result = self.test_query(query, top_k=top_k)
            result['index'] = idx
            results.append(result)
            print("✓" if result['success'] else "✗")
            time.sleep(0.2)  # Brief pause

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manual review of RAG retrieval results"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of queries to test (default: all)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of chunks to retrieve per query (default: 5)'
    )
    parser.add_argument(
        '--export-json',
        type=str,
        default=None,
        help='Export results to JSON file'
    )
    parser.add_argument(
        '--export-html',
        type=str,
        default=None,
        help='Export results to HTML file for browser viewing'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='cuda',
        choices=['cuda', 'cpu'],
        help='Device for embeddings (default: cuda)'
    )
    parser.add_argument(
        '--print-all',
        action='store_true',
        help='Print all results to console (can be very long)'
    )

    args = parser.parse_args()

    # Set device
    if args.device:
        os.environ['EMBEDDING_DEVICE'] = args.device

    # Run tests
    tester = ManualReviewTester()
    results = tester.run_tests(limit=args.limit, top_k=args.top_k)

    # Print results to console if requested
    if args.print_all:
        print("\n\n" + "="*100)
        print("DETAILED RESULTS")
        print("="*100)
        for result in results:
            tester.print_review(result)

    # Export results
    if args.export_json:
        tester.export_to_json(results, args.export_json)

    if args.export_html:
        tester.export_to_html(results, args.export_html)

    # Summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful

    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Total queries tested: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if not args.export_html and not args.export_json:
        print("\n💡 TIP: Use --export-html to create an HTML file for easier review in your browser")
        print("   Example: python scripts/test_rag_retrieval_manual.py --export-html review.html")

    print("="*100 + "\n")


if __name__ == "__main__":
    main()
