"""
Simple RAG QA Test Script
Only prints ground truth, LLM response, and response time for each query.
"""
import time
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import setup_logging
from app.services.rag_service import get_rag_service

# Visana Document QA Test Cases
VISANA_QA_TESTS = [
    {
        "question": "Was beinhaltet die Komplementärmedizin bei functiomed?",
        "answer": "Unsere Komplementärmedizin umfasst Akupunktur, Homöopathie, medizinische Massagen und weitere alternative Heilmethoden. "
    },
    {
        "question": "What are prices of functiomed?",
        "answer": "30min Fr. 108.- 45min Fr. 159.- First consultation additional Fr. 20.- Emergency surcharge additional Fr. 40.-"
    }
#     {
#         "question": "Was sind Stammzellen aus Fettgewebe?",
#         "answer": "Stammzellen aus Fettgewebe – sogenannte mesenchymale Stammzellen – sind Zellen mit einem hohen regenerativen Potenzial. Sie können Gewebe reparieren, Entzündungen hemmen und Heilungsprozesse fördern."
#     },
#     {
#         "question": "When is hyaluronic acid therapy used?",
#         "answer": """The therapy is mainly used for joint irritation, cartilage damage, and osteoarthritis. Degenerative cartilage damage and osteoarthritis are typical signs of wear and tear of the joints and a natural consequence of the aging process. Destroyed cartilage tissue can no longer be replaced by the body itself.

#         Early signs of osteoarthritis include:
#         – Pain at the start of movement
#         – Grinding in the joint
#         – Limited mobility
#         – Rest and night pain
#         – Inflammation and swelling

#         Osteoarthritis is divided into 4 stages.

#         Goals of hyaluronic acid therapy:
#         – Reduction of pain
#         – Improved mobility
#         – Reduced need for pain medication
#         – Optimal patient satisfaction
#         – Increased hyaluronic acid in the joint fluid"""
#     },
#     {
#         "question": "Wie checken sich die Patienten ein und aus?",
#         "answer": "By holding their wrist badge or phone sticker to the reader at the entrance of the training area."
#     },
#     {
#         "question": "What should an employer do if an employee was treated for an accident at functiomed?",
#         "answer": "The employer should report the accident to their accident insurance as soon as possible. This ensures that functiomed can complete the administrative processing of the treatment. The employer can provide the required information either directly or through the employee."
#     },
#     {
#         "question": "Wer kann von der Einlagerung von Fettgewebe profitieren und warum ist es vorteilhaft, es frühzeitig zu speichern?",
#         "answer": "Die Einlagerung von Fettgewebe eignet sich für Erwachsene, die ihre eigenen biologischen Ressourcen für präventive oder therapeutische Zwecke sichern möchten. Besonders nützlich ist sie für Personen, die invasive Behandlungen aufschieben möchten, mehrere zukünftige Behandlungen planen, aber die Liposuktion nur einmal durchführen lassen wollen, oder über wenig Fettgewebe verfügen und sicherstellen möchten, dass ausreichend Material für spätere Anwendungen verfügbar ist. Die frühzeitige Speicherung des Fettgewebes gewährleistet eine optimale Zellqualität, da Stammzellen bei früher Gewinnung vitaler sind. Außerdem bietet sie eine persönliche biologische Reserve, die jederzeit für regenerative Therapien in der Orthopädie, Hautregeneration, ästhetische Anwendungen oder Schmerztherapie genutzt werden kann."
#     },
#     {
#         "question": "What types of massage services does functiomed offer, and what are their benefits?",
#         "answer": """Functiomed offers a variety of massage services, each with specific techniques and benefits:

#         Medical Massage: Aims to release tense and cramped muscles. Different massage techniques are used either broadly or on specific problem areas. Benefits include improved blood circulation, regulation of muscle tone, removal of waste products, and overall better well-being.
#         Classical Massage: Treats all muscles of the body using various massage techniques. Helps relieve muscle tension and stiffness, promotes relaxation, and improves circulation.
#         Hot Stone Massage: Considered mainly a wellness massage, but the hot stones can also be effectively used in a classical massage. The additional warmth helps to target tense muscles and stimulate circulation, particularly pleasant in colder seasons.
#         Sports Massage: Works deeper into the tissue with additional techniques compared to classical massage. Intended for athletes before and after competitions—activating muscles before and aiding recovery and detoxification afterward.
#         Japanese Facial Massage: Focuses on the face and décolleté to naturally reduce wrinkles and relax muscles. It firms the chin and facial contours, improves skin structure, and includes treatment of the neck, head, and décolleté. Noticeable improvements in facial appearance can be seen after a few sessions.
#         Lomi Lomi Massage (Hawaiian Deep Tissue Massage): Full-body massage that works deeply on muscles and gently mobilizes joints. Promotes deep relaxation and regeneration and is traditionally part of Hawaiian holistic healing practices.
#         Pregnancy Massage: Designed to relieve neck and lower back tension, reduce water retention, and support postnatal recovery. Performed in side or supported back positions with a pillow. Safe from week 13 of pregnancy.
#         Anti-Cellulite Massage: Targets areas like the buttocks, abdomen, and thighs. Special techniques stimulate circulation and lymph flow, break down adhesions, and firm the connective tissue. Regular treatments lead to smoother, tighter, and healthier-looking skin.
#         Foot Reflexology Massage: Focuses on the soles of the feet. Specific points on the feet correspond to body organs, which can be reflexively influenced. Promotes relaxation, general well-being, and supports self-healing.
#         Manual Lymphatic Drainage: Gentle technique to remove water retention, providing relief in affected areas. Stimulates lymph nodes and drains the targeted body part, improving tissue condition.
#         Shiatsu Massage: Japanese acupressure technique that applies pressure to specific points to release tension, mobilize joints, and harmonize energy flow (Chi). Supports physical, mental, and emotional balance, ideal for stress, muscle tension, or low energy. Light clothing such as a T-shirt and training pants is recommended.

#         Each massage at functiomed is designed to improve well-being, relieve tension, and support the body’s natural healing processes."""
#     }
]

def test_visana_qa():
    """Run simple QA test printing ground truth, LLM response, and response time"""
    
    print("\n" + "="*80)
    print("VISANA QA TESTS")
    print("="*80)
    
    rag_service = get_rag_service()
    
    for idx, test_case in enumerate(VISANA_QA_TESTS, 1):
        question = test_case["question"]
        ground_truth = test_case["answer"]
        
        print(f"\nTest {idx}/{len(VISANA_QA_TESTS)}")
        print("-"*80)
        print(f"Question: {question}")
        print(f"Ground Truth: {ground_truth}")
        
        try:
            start_time = time.time()
            response = rag_service.generate_answer(
                query=question,
                top_k=5,
                min_score=0.5
            )
            elapsed_time = time.time() - start_time
            
            print(f"LLM Response: {response.answer}")
            print(f"Response Time: {elapsed_time:.2f} seconds")
            
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Setup logging
    setup_logging("INFO")
    
    test_visana_qa()
