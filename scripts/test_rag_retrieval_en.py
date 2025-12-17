"""
Minimal RAG Retrieval Manual Review Script - English
Shows ground truth and retrieved context directly in terminal.
"""

import sys
import os
import time
from pathlib import Path
from typing import List
from dataclasses import dataclass

# Disable MPS on macOS to avoid mutex blocking issues
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

# Force CPU usage for sentence-transformers (avoids MPS issues on macOS)
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Set device to CPU for macOS compatibility
os.environ["EMBEDDING_DEVICE"] = "cpu"

from app.services.retrieval_service import get_retrieval_service
from app.config import settings


@dataclass
class TestQuery:
    query: str
    language: str
    expected_categories: List[str]
    expected_documents: List[str]
    description: str
    min_score: float = 0.5


def get_test_queries() -> List[TestQuery]:
    """
    English test queries for RAG retrieval evaluation - Praxis-info documents only.
    """
    return [
        TestQuery(
            query="What is the address of Functiomed?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["kontakt_EN"],
            description="Practice address",
        ),
        TestQuery(
            query="What is the phone number of Functiomed?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["kontakt_EN"],
            description="Contact phone number",
        ),
        TestQuery(
            query="What is the email address to contact Functiomed?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["kontakt_EN"],
            description="Contact email",
        ),
        TestQuery(
            query="What are the opening hours of Functiomed?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["FAQs_EN"],
            description="Opening hours",
        ),
        TestQuery(
            query="Who is the CEO of Functiomed?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["team_EN"],
            description="CEO identity",
        ),
        TestQuery(
            query="Who is Prof. Martin Spring?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["team_EN"],
            description="CEO details",
        ),
        TestQuery(
            query="Who is Dr. Manuel Haag?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["team_EN"],
            description="Medical Director info",
        ),
        TestQuery(
            query="Which doctors work at Functiomed?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["team_EN"],
            description="Doctors list",
        ),
        TestQuery(
            query="What languages does Dr. Christoph Lienhard speak?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["team_EN"],
            description="Doctor languages",
        ),
        TestQuery(
            query="Who are the osteopaths at Functiomed?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["team_EN"],
            description="Osteopathy team",
        ),
        TestQuery(
            query="Who is the Head of Physiotherapy?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["team_EN"],
            description="Physiotherapy leadership",
        ),
        TestQuery(
            query="What emergency services does Functiomed offer?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["notfall_EN"],
            description="Emergency services",
        ),
        TestQuery(
            query="Which hospitals does Functiomed collaborate with?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["notfall_EN"],
            description="Hospital partnerships",
        ),
        TestQuery(
            query="Does Functiomed offer ultrasound diagnostics?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["notfall_EN"],
            description="Diagnostic services",
        ),
        TestQuery(
            query="How can I book an appointment at Functiomed?",
            language="EN",
            expected_categories=["praxis-info"],
            expected_documents=["FAQs_EN"],
            description="Appointment booking",
        ),
    ]


def print_separator():
    print("=" * 100)


def run():
    service = get_retrieval_service()
    queries = get_test_queries()

    print_separator()
    print("RAG MANUAL RETRIEVAL REVIEW (TERMINAL) - ENGLISH")
    print(f"Top-K: {settings.RETRIEVAL_TOP_K}")
    print(f"Min score: {settings.RAG_MIN_CHUNK_SCORE}")
    print_separator()

    for idx, tq in enumerate(queries, 1):
        print(f"\n[{idx}] {tq.description}")
        print("-" * 100)
        print(f"Query: {tq.query}")
        print(f"Language: {tq.language}")

        print("\nEXPECTED DOCUMENTS:")
        for d in tq.expected_documents:
            print(f"  - {d}")

        print("EXPECTED CATEGORIES:")
        for c in tq.expected_categories:
            print(f"  - {c}")

        start = time.time()
        response = service.retrieve(
            query=tq.query,
            language=tq.language,
            top_k=settings.RETRIEVAL_TOP_K,
            min_score=tq.min_score,
        )
        duration = round((time.time() - start) * 1000, 1)

        print(f"\nRETRIEVED ({len(response.results)} chunks, {duration} ms)")
        print("-" * 100)

        if not response.results:
            print("❌ No chunks retrieved")
            print_separator()
            continue

        for rank, r in enumerate(response.results, 1):
            print(f"\nRANK #{rank} | score={round(r.score, 4)}")
            print(f"Document : {r.source_document}")
            print(f"Category : {r.category}")
            print(f"Chunk    : {r.chunk_index}/{r.total_chunks}")
            print("TEXT:")
            print("-" * 80)
            print(r.text.strip())
            print("-" * 80)

        print_separator()


if __name__ == "__main__":
    run()
