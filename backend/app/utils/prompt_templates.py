# """
# Prompt templates for RAG pipeline.
# Engineered for medical domain with German/English support.
# """
# from typing import List, Dict, Any, Optional
# from dataclasses import dataclass


# @dataclass
# class PromptTemplate:
#     """Base prompt template structure"""
#     system: str
#     context_format: str
#     user_format: str
    
#     def build(
#         self,
#         context: List[Dict[str, Any]],
#         query: str,
#         language: str = "DE"
#     ) -> str:
#         """
#         Build complete prompt from components.
        
#         Args:
#             context: List of retrieved chunks with metadata
#             query: User question
#             language: DE or EN
            
#         Returns:
#             Formatted prompt string
#         """
#         # Format context section
#         context_str = self._format_context(context)
        
#         # Build complete prompt
#         prompt = f"""{self.system}

# {context_str}

# {self.user_format.format(query=query)}"""
        
#         return prompt
    
#     def _format_context(self, context: List[Dict[str, Any]]) -> str:
#         """Format retrieved chunks into context section"""
#         if not context:
#             return "KONTEXT:\nKeine relevanten Informationen verfügbar."
        
#         context_parts = []
#         for idx, chunk in enumerate(context, 1):
#             source = chunk.get('source_document', 'Unbekannt')
#             text = chunk.get('text', '')
#             score = chunk.get('score', 0.0)
            
#             # Format: [1] Quelle: filename.pdf (Relevanz: 0.85)
#             # Text content here...
#             part = self.context_format.format(
#                 index=idx,
#                 source=source,
#                 score=score,
#                 text=text
#             )
#             context_parts.append(part)
        
#         return "KONTEXT:\n" + "\n\n".join(context_parts)


# # ============================================================================
# # German Medical Assistant Template
# # ============================================================================

# GERMAN_MEDICAL_TEMPLATE = PromptTemplate(
#     system="""
# Du bist ein KI-Assistent für Functiomed, eine medizinische Praxis in München.

# AUFGABE:
# - Beantworte Fragen präzise basierend auf dem bereitgestellten KONTEXT
# - Antworte NUR auf Deutsch
# - Sei höflich, professionell und medizinisch korrekt
# - Strukturierte Antworten liefern

# REGELN:
# 1. Nutze NUR Informationen aus dem KONTEXT.
# 2. Wenn die Antwort nicht im KONTEXT ist, antworte: "Bitte kontaktieren Sie unseren Kundenservice für spezifische Informationen zu diesem Thema."
# 3. Gib KEINE medizinischen Diagnosen oder Behandlungsempfehlungen ohne Kontext.
# 4. Antworte ausführlich, klar und gut strukturiert. Erkläre relevante Details, Hintergründe und Beispiele, wenn möglich.

# ANTWORTFORMAT:
# - Kurze Absätze oder Aufzählungspunkte bei Bedarf
# - Beginne mit einem klaren zusammenfassenden Satz
# - Informationen logisch und präzise organisieren
# - Unnötige Details vermeiden
# """,
    
#     context_format="[{index}] Quelle: {source} (Relevanz: {score:.2f})\n{text}",
    
#     user_format="FRAGE:\n{query}\n\nANTWORT:"
# )


# # ============================================================================
# # English Medical Assistant Template
# # ============================================================================

# ENGLISH_MEDICAL_TEMPLATE = PromptTemplate(
#     system="""
# You are an AI assistant for Functiomed, a medical practice in Munich, Germany.

# TASK:
# - Answer questions based on the provided CONTEXT
# - Respond ONLY in English
# - Be polite, professional, and medically accurate
# - Always structure your response clearly

# RULES:
# 1. Use factual information from the CONTEXT.
# 2. If the answer is not in CONTEXT, respond: "Please contact our customer representative for specific guidance on this topic."
# 3. Do NOT give medical diagnoses or treatment recommendations without context.
# 4. Provide detailed, well-structured answers. Include explanations, examples, and context when relevant.


# RESPONSE FORMAT:
# - Use short paragraphs or bullet points if needed.
# - Begin with a clear summary sentence.
# - Organize information logically and concisely.
# - Avoid unnecessary details.
# """,
    
#     context_format="[{index}] Source: {source} (Relevance: {score:.2f})\n{text}",
    
#     user_format="QUESTION:\n{query}\n\nANSWER:"
# )



# # ============================================================================
# # Concise Response Template (Ultra-short)
# # ============================================================================

# CONCISE_TEMPLATE = PromptTemplate(
#     system="""Du bist ein KI-Assistent für functiomed.

# Antworte in maximal 2-3 kurzen Sätzen.
# Nutze nur den KONTEXT.
# Füge Quellen hinzu: [1], [2].
# Wenn keine Info verfügbar: "Diese Information liegt mir nicht vor." """,
    
#     context_format="[{index}] {source}\n{text}",
    
#     user_format="{query}\n\nAntwort:"
# )


# # ============================================================================
# # Template Selector
# # ============================================================================

# def get_template(
#     language: str = "DE",
#     style: str = "standard"
# ) -> PromptTemplate:
#     """
#     Get appropriate prompt template based on language and style.
    
#     Args:
#         language: DE or EN
#         style: standard, concise
        
#     Returns:
#         PromptTemplate instance
#     """
#     language = language.upper() if language else "DE"
#     style = style.lower() if style else "standard"
    
#     # Select template
#     if style == "concise":
#         return CONCISE_TEMPLATE
#     elif language == "EN":
#         return ENGLISH_MEDICAL_TEMPLATE
#     else:
#         return GERMAN_MEDICAL_TEMPLATE


# # ============================================================================
# # Prompt Builder Utility
# # ============================================================================

# class PromptBuilder:
#     """Utility class for building prompts with token management"""
    
#     def __init__(
#         self,
#         template: Optional[PromptTemplate] = None,
#         max_context_tokens: int = 4096
#     ):
#         """
#         Initialize prompt builder.
        
#         Args:
#             template: Prompt template to use
#             max_context_tokens: Maximum tokens for context section
#         """
#         self.template = template or GERMAN_MEDICAL_TEMPLATE
#         self.max_context_tokens = max_context_tokens
    
#     def build_prompt(
#         self,
#         context: List[Dict[str, Any]],
#         query: str,
#         language: str = "DE",
#         token_counter: Optional[callable] = None
#     ) -> str:
#         """
#         Build prompt with token limit enforcement.
        
#         Args:
#             context: Retrieved chunks
#             query: User question
#             language: DE or EN
#             token_counter: Optional function to count tokens
            
#         Returns:
#             Formatted prompt string
#         """
#         # Select template if language different
#         template = get_template(language=language, style="standard")
        
#         # Truncate context if needed
#         if token_counter:
#             context = self._truncate_context(context, token_counter)
        
#         # Build prompt
#         return template.build(context=context, query=query, language=language)
    
#     def _truncate_context(
#         self,
#         context: List[Dict[str, Any]],
#         token_counter: callable
#     ) -> List[Dict[str, Any]]:
#         """
#         Truncate context to fit within token limit.
        
#         Args:
#             context: List of chunks
#             token_counter: Function to count tokens
            
#         Returns:
#             Truncated context list
#         """
#         truncated = []
#         total_tokens = 0
        
#         for chunk in context:
#             # Estimate chunk tokens
#             chunk_text = chunk.get('text', '')
#             chunk_tokens = token_counter(chunk_text)
            
#             # Check if adding this chunk exceeds limit
#             if total_tokens + chunk_tokens > self.max_context_tokens:
#                 break
            
#             truncated.append(chunk)
#             total_tokens += chunk_tokens
        
#         return truncated


# # ============================================================================
# # Example Usage
# # ============================================================================

# if __name__ == "__main__":
#     print("="*60)
#     print("PROMPT TEMPLATE TEST")
#     print("="*60)
    
#     # Sample context
#     sample_context = [
#         {
#             "text": "functiomed bietet Osteopathie, Physiotherapie und Ernährungsberatung an.",
#             "source_document": "angebote.pdf",
#             "score": 0.92
#         },
#         {
#             "text": "Die Praxis befindet sich in München, Musterstraße 123.",
#             "source_document": "praxis-info.pdf",
#             "score": 0.78
#         }
#     ]
    
#     sample_query = "Welche Behandlungen bietet functiomed an?"
    
#     # Test German template
#     print("\n[Test 1] German Standard Template")
#     print("-" * 60)
#     template_de = get_template(language="DE", style="standard")
#     prompt_de = template_de.build(sample_context, sample_query, language="DE")
#     print(prompt_de)
    
#     # Test English template
#     print("\n[Test 2] English Standard Template")
#     print("-" * 60)
#     template_en = get_template(language="EN", style="standard")
#     prompt_en = template_en.build(sample_context, sample_query, language="EN")
#     print(prompt_en)
    
#     # Test Concise template
#     print("\n[Test 3] Concise Template")
#     print("-" * 60)
#     template_concise = get_template(language="DE", style="concise")
#     prompt_concise = template_concise.build(sample_context, sample_query, language="DE")
#     print(prompt_concise)
    
#     print("\n" + "="*60)
#     print("✓ All template tests completed!")
#     print("="*60)

"""
Enhanced Prompt Templates for Verbose, Structured Responses
Generates responses similar to your desired format with proper structure and formatting
"""

GERMAN_VERBOSE_TEMPLATE = """Du bist ein professioneller medizinischer Assistent für functiomed, eine Schweizer Arztpraxis.

Deine Aufgabe ist es, detaillierte, gut strukturierte und professionelle Antworten zu erstellen.

ANTWORT-RICHTLINIEN:

1. STRUKTUR & FORMAT:
   - Beginne mit einer einleitenden Aussage (1-2 Sätze)
   - Organisiere Informationen in klare thematische Abschnitte mit Überschriften
   - Verwende Absätze statt Aufzählungszeichen für den Haupttext
   - Schließe mit einer zusammenfassenden Aussage ab, die den Nutzen für Patienten betont

2. SPRACHSTIL:
   - Schreibe in vollständigen, fließenden Sätzen
   - Verwende professionelle, aber zugängliche Sprache
   - Sei präzise und informativ ohne übermäßig technisch zu sein
   - Vermeide kurze, abgehackte Antworten

3. LÄNGE & TIEFE:
   - Strebe mindestens 150-250 Wörter an
   - Erkläre nicht nur WAS, sondern auch WARUM und WIE
   - Füge Kontext und zusätzliche relevante Details hinzu

4. FORMATIERUNG:
   - Verwende Überschriften für Hauptabschnitte (z.B. "Enthaltene Methoden", "Zielsetzung")
   - Gruppiere verwandte Informationen zusammen
   - Verwende Aufzählungslisten nur für kurze, spezifische Listen innerhalb von Abschnitten
   - Trenne verschiedene Themenbereiche durch Leerzeilen

VERFÜGBARE DOKUMENTE:
{context}

PATIENT FRAGE: {query}

Erstelle nun eine umfassende, professionelle Antwort im oben beschriebenen Format. Beginne direkt mit der Antwort ohne Meta-Kommentare."""


ENGLISH_VERBOSE_TEMPLATE = """You are a professional medical assistant for functiomed, a Swiss medical practice.

Your task is to create detailed, well-structured, and professional responses.

RESPONSE GUIDELINES:

1. STRUCTURE & FORMAT:
   - Begin with an introductory statement (1-2 sentences)
   - Organize information into clear thematic sections with headings
   - Use paragraphs instead of bullet points for main text
   - Close with a summary statement emphasizing patient benefits

2. LANGUAGE STYLE:
   - Write in complete, flowing sentences
   - Use professional but accessible language
   - Be precise and informative without being overly technical
   - Avoid short, choppy responses

3. LENGTH & DEPTH:
   - Aim for at least 150-250 words
   - Explain not just WHAT, but also WHY and HOW
   - Add context and additional relevant details

4. FORMATTING:
   - Use headings for main sections (e.g., "Included Methods", "Objectives")
   - Group related information together
   - Use bullet lists only for short, specific lists within sections
   - Separate different topic areas with blank lines

AVAILABLE DOCUMENTS:
{context}

PATIENT QUESTION: {query}

Now create a comprehensive, professional response in the format described above. Begin directly with the answer without meta-comments."""


CONCISE_GERMAN_TEMPLATE = """Du bist ein medizinischer Assistent für functiomed.

DOKUMENTE:
{context}

FRAGE: {query}

Gib eine präzise, direkte Antwort in 2-4 Sätzen."""


CONCISE_ENGLISH_TEMPLATE = """You are a medical assistant for functiomed.

DOCUMENTS:
{context}

QUESTION: {query}

Provide a precise, direct answer in 2-4 sentences."""


class PromptBuilder:
    """Builds prompts with proper token management and formatting"""
    
    def __init__(self, max_context_tokens: int = 3000):
        self.max_context_tokens = max_context_tokens
        self.template = GERMAN_VERBOSE_TEMPLATE
    
    def build_prompt(
        self,
        context: list,
        query: str,
        language: str = "DE",
        style: str = "verbose",
        token_counter=None
    ) -> str:
        """
        Build prompt from context and query.
        
        Args:
            context: List of retrieved document chunks
            query: User question
            language: DE or EN
            style: "verbose" or "concise"
            token_counter: Optional function to count tokens
            
        Returns:
            Formatted prompt string
        """
        # Select template
        if style == "verbose":
            template = GERMAN_VERBOSE_TEMPLATE if language == "DE" else ENGLISH_VERBOSE_TEMPLATE
        else:
            template = CONCISE_GERMAN_TEMPLATE if language == "DE" else CONCISE_ENGLISH_TEMPLATE
        
        # Format context
        context_text = self._format_context(context, token_counter)
        
        # Build final prompt
        prompt = template.format(
            context=context_text,
            query=query
        )
        
        return prompt
    
    def _format_context(self, context: list, token_counter=None) -> str:
        """Format context chunks with citations"""
        if not context:
            return "Keine relevanten Dokumente gefunden."
        
        formatted_chunks = []
        
        for idx, chunk in enumerate(context, 1):
            chunk_text = f"[{idx}] Quelle: {chunk.get('source_document', 'Unbekannt')}\n"
            chunk_text += f"Kategorie: {chunk.get('category', 'Allgemein')}\n"
            chunk_text += f"Inhalt: {chunk.get('text', '')}\n"
            
            formatted_chunks.append(chunk_text)
            
            # Check token limit if counter provided
            if token_counter:
                current_tokens = token_counter("\n\n".join(formatted_chunks))
                if current_tokens > self.max_context_tokens:
                    formatted_chunks.pop()  # Remove last chunk
                    break
        
        return "\n\n".join(formatted_chunks)


def get_template(language: str = "DE", style: str = "verbose") -> str:
    """
    Get appropriate template.
    
    Args:
        language: "DE" or "EN"
        style: "verbose" or "concise"
        
    Returns:
        Template string
    """
    if style == "verbose":
        return GERMAN_VERBOSE_TEMPLATE if language == "DE" else ENGLISH_VERBOSE_TEMPLATE
    else:
        return CONCISE_GERMAN_TEMPLATE if language == "DE" else CONCISE_ENGLISH_TEMPLATE