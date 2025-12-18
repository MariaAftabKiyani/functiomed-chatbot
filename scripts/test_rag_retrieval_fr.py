"""
Minimal RAG Retrieval Manual Review Script - French
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
    min_score: float = 0.0  # Set to 0 to debug - see all results regardless of score


def get_test_queries() -> List[TestQuery]:
    """
    French test queries for RAG retrieval evaluation - Praxis-info documents only.
    """
    return [
        TestQuery(
            query="Quelle est l'adresse de Functiomed?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["kontakt_FR"],
            description="Practice address",
        ),
        TestQuery(
            query="Quel est le numéro de téléphone de Functiomed?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["kontakt_FR"],
            description="Contact phone number",
        ),
        TestQuery(
            query="Quelle est l'adresse e-mail pour contacter Functiomed?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["kontakt_FR"],
            description="Contact email",
        ),
        TestQuery(
            query="Quels sont les horaires d'ouverture de Functiomed?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["FAQs_FR"],
            description="Opening hours",
        ),
        TestQuery(
            query="Qui est le CEO de Functiomed?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["team_FR"],
            description="CEO identity",
        ),
        TestQuery(
            query="Qui est Prof. Martin Spring?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["team_FR"],
            description="CEO details",
        ),
        TestQuery(
            query="Qui est Dr. Manuel Haag?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["team_FR"],
            description="Medical Director info",
        ),
        TestQuery(
            query="Quels médecins travaillent chez Functiomed?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["team_FR"],
            description="Doctors list",
        ),
        TestQuery(
            query="Quelles langues parle Dr. Christoph Lienhard?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["team_FR"],
            description="Doctor languages",
        ),
        TestQuery(
            query="Qui sont les ostéopathes chez Functiomed?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["team_FR"],
            description="Osteopathy team",
        ),
        TestQuery(
            query="Qui est le responsable de la physiothérapie?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["team_FR"],
            description="Physiotherapy leadership",
        ),
        TestQuery(
            query="Quels services d'urgence propose Functiomed?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["notfall_FR"],
            description="Emergency services",
        ),
        TestQuery(
            query="Avec quels hôpitaux Functiomed collabore-t-il?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["notfall_FR"],
            description="Hospital partnerships",
        ),
        TestQuery(
            query="Functiomed propose-t-il des diagnostics par échographie?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["notfall_FR"],
            description="Diagnostic services",
        ),
        TestQuery(
            query="Comment puis-je prendre rendez-vous chez Functiomed?",
            language="FR",
            expected_categories=["praxis-info"],
            expected_documents=["FAQs_FR"],
            description="Appointment booking",
        ),
    ]


def print_separator():
    print("=" * 100)


def run():
    service = get_retrieval_service()
    queries = get_test_queries()

    print_separator()
    print("RAG MANUAL RETRIEVAL REVIEW (TERMINAL) - FRENCH")
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
            language=None,  # Cross-lingual: match FR queries to DE/EN docs
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
