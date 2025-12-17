"""
Translate German documents to English and French using Helsinki-NLP models.
This creates parallel document sets for multilingual RAG.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import re
from tqdm import tqdm

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Disable MPS fallback
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Use CPU

try:
    from transformers import MarianMTModel, MarianTokenizer
    import torch
except ImportError:
    print("ERROR: transformers library not installed")
    print("Run: pip install transformers sentencepiece sacremoses")
    sys.exit(1)


class DocumentTranslator:
    """Translate documents using Helsinki-NLP MarianMT models."""

    def __init__(self):
        self.device = "cpu"  # Use CPU for compatibility
        self.models = {}
        self.tokenizers = {}

        print("Loading translation models...")
        self._load_models()

    def _load_models(self):
        """Load MarianMT translation models."""
        # DE -> EN
        print("  Loading DE->EN model...")
        de_en_name = "Helsinki-NLP/opus-mt-de-en"
        self.tokenizers['de-en'] = MarianTokenizer.from_pretrained(de_en_name)
        self.models['de-en'] = MarianMTModel.from_pretrained(de_en_name).to(self.device)

        # DE -> FR
        print("  Loading DE->FR model...")
        de_fr_name = "Helsinki-NLP/opus-mt-de-fr"
        self.tokenizers['de-fr'] = MarianTokenizer.from_pretrained(de_fr_name)
        self.models['de-fr'] = MarianMTModel.from_pretrained(de_fr_name).to(self.device)

        print("✓ Models loaded successfully\n")

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source to target language.

        Args:
            text: Text to translate
            source_lang: Source language code (de)
            target_lang: Target language code (en, fr)

        Returns:
            Translated text
        """
        model_key = f"{source_lang}-{target_lang}"

        if model_key not in self.models:
            raise ValueError(f"Translation pair {model_key} not supported")

        # Split long text into chunks (max 512 tokens)
        max_length = 500  # Leave some margin
        sentences = text.split('\n')

        translated_parts = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())

            if current_length + sentence_length > max_length and current_chunk:
                # Translate current chunk
                chunk_text = '\n'.join(current_chunk)
                translated = self._translate_chunk(chunk_text, model_key)
                translated_parts.append(translated)

                # Start new chunk
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Translate remaining chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            translated = self._translate_chunk(chunk_text, model_key)
            translated_parts.append(translated)

        return '\n'.join(translated_parts)

    def _translate_chunk(self, text: str, model_key: str) -> str:
        """Translate a single chunk of text."""
        tokenizer = self.tokenizers[model_key]
        model = self.models[model_key]

        # Tokenize
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Translate
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)

        # Decode
        translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translated

    def translate_document(self, source_path: Path, target_path: Path, target_lang: str):
        """
        Translate a document file from German to target language.

        Args:
            source_path: Path to source German document
            target_path: Path to save translated document
            target_lang: Target language (en or fr)
        """
        # Read source document
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata header (first 5 lines) and body
        lines = content.split('\n')
        header_lines = []
        body_start = 0

        # Keep metadata header unchanged
        for i, line in enumerate(lines[:10]):
            if line.startswith('Source:') or line.startswith('Section:') or \
               line.startswith('Scraped:') or line.startswith('Language:') or \
               line.startswith('='):
                header_lines.append(line)
                body_start = i + 1
            else:
                break

        # Update language in header
        header_text = '\n'.join(header_lines)
        header_text = re.sub(r'Language: DE', f'Language: {target_lang.upper()}', header_text)

        # Get body content
        body_text = '\n'.join(lines[body_start:])

        # Translate body
        print(f"  Translating {source_path.name} to {target_lang.upper()}...")
        translated_body = self.translate_text(body_text, 'de', target_lang)

        # Combine header and translated body
        final_content = header_text + '\n' + translated_body

        # Save translated document
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        print(f"  ✓ Saved to {target_path}")


def find_german_documents(base_path: Path) -> List[Path]:
    """Find all German documents (_DE.txt)."""
    return list(base_path.glob('**/*_DE.txt'))


def translate_all_documents(source_dir: Path, target_dir: Path):
    """
    Translate all German documents to English and French.

    Args:
        source_dir: Directory containing German documents
        target_dir: Directory to save translated documents
    """
    translator = DocumentTranslator()

    # Find all German documents
    german_docs = find_german_documents(source_dir)
    print(f"Found {len(german_docs)} German documents\n")

    if not german_docs:
        print("No German documents found!")
        return

    # Translate each document
    for doc_path in tqdm(german_docs, desc="Translating documents"):
        # Get relative path
        rel_path = doc_path.relative_to(source_dir)

        # Create EN and FR versions
        for lang in ['en', 'fr']:
            # Replace _DE with _EN or _FR
            target_name = rel_path.name.replace('_DE.txt', f'_{lang.upper()}.txt')
            target_path = target_dir / rel_path.parent / target_name

            # Translate
            translator.translate_document(doc_path, target_path, lang)

    print("\n✓ Translation complete!")
    print(f"  English documents: {target_dir}")
    print(f"  French documents: {target_dir}")


def main():
    """Main translation pipeline."""
    # Paths
    project_root = Path(__file__).parent.parent
    source_dir = project_root / "data" / "documents" / "txt"
    target_dir = project_root / "data" / "documents" / "txt"  # Same directory

    print("=" * 80)
    print("DOCUMENT TRANSLATION PIPELINE")
    print("=" * 80)
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    print("Languages: DE -> EN, FR")
    print("=" * 80)
    print()

    # Check source directory exists
    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        return

    # Confirm before proceeding
    response = input("Start translation? This may take 10-30 minutes. (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    # Run translation
    translate_all_documents(source_dir, target_dir)

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Review translated documents in data/documents/txt/")
    print("2. Run embedding script to index new EN and FR documents:")
    print("   python scripts/embed_documents.py")
    print("3. Test retrieval with EN and FR test scripts")
    print("=" * 80)


if __name__ == "__main__":
    main()
