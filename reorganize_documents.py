#!/usr/bin/env python3
"""
Script to reorganize documents from new_txt folder into structured directories
matching the txt folder structure.
"""

import os
import shutil
from pathlib import Path

# Define base paths
NEW_TXT_DIR = r"C:\Users\HomePC\Documents\Workspace\functiomed\Project\functiomed-chatbot\data\documents\new_txt"
TARGET_DIR = r"C:\Users\HomePC\Documents\Workspace\functiomed\Project\functiomed-chatbot\data\documents\new_txt_organized"

# Mapping of file patterns to target directories
FILE_MAPPINGS = {
    # Angebote (Offers/Services)
    'angebot': 'angebote',

    # Contact
    'kontakt': 'contact',

    # Emergency
    'notfall': 'emergency',

    # Nutrition (Ernaehrung)
    'erspe-institut': 'ernaehrung',
    'fitamara': 'ernaehrung',
    'ernaehrung': 'ernaehrung',

    # Team/Person
    'person': 'team',
    'team': 'team',

    # Therapies
    'mental-coaching': 'therapien',
    'ergotherapie': 'therapien',

    # Training
    'functiotraining': 'training',
    'functiokurse': 'training',

    # Departments (Abteilung) - these can go to angebote or create a new category
    'abteilung': 'angebote',

    # Special pages
    'functiosport': 'angebote',
    'kooperationen': 'angebote',
}

def determine_category(filename):
    """
    Determine the category/subdirectory for a file based on its name.
    Returns the subdirectory name or None if it should stay in root.
    """
    filename_lower = filename.lower()

    # Check for specific patterns
    for pattern, category in FILE_MAPPINGS.items():
        if pattern in filename_lower:
            return category

    # Special cases for specific files
    if 'termin-buchen' in filename_lower or 'online-termin' in filename_lower:
        return 'contact'

    if 'qualitaet' in filename_lower:
        return 'angebote'

    # Index pages stay in root
    if 'index' in filename_lower:
        return None

    # Default to angebote for most service-related content
    return 'angebote'

def create_directory_structure():
    """Create the directory structure in the target folder."""
    categories = [
        'angebote',
        'contact',
        'emergency',
        'ernaehrung',
        'FAQs',
        'notices',
        'patient_info',
        'team',
        'therapien',
        'therapy',
        'training'
    ]

    # Create target base directory
    os.makedirs(TARGET_DIR, exist_ok=True)

    # Create subdirectories
    for category in categories:
        category_path = os.path.join(TARGET_DIR, category)
        os.makedirs(category_path, exist_ok=True)
        print(f"Created directory: {category_path}")

def clean_filename(filename):
    """
    Clean up the filename by removing URL-like prefixes.
    Example: www_functiomed_ch_angebot_akupunktur.txt -> akupunktur_DE.txt
    """
    # Remove common prefixes
    prefixes = [
        'www_functiomed_ch_',
        'functiomed_thefotoloft_ch_',
    ]

    clean_name = filename
    for prefix in prefixes:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):]
            break

    # Remove intermediate path components
    clean_name = clean_name.replace('angebot_', '')
    clean_name = clean_name.replace('person_', '')
    clean_name = clean_name.replace('abteilung_', '')
    clean_name = clean_name.replace('pages_', '')

    # Add language suffix if not present (assume DE for German content)
    if not any(clean_name.endswith(f'_{lang}.txt') for lang in ['DE', 'EN', 'FR']):
        base, ext = os.path.splitext(clean_name)
        clean_name = f"{base}_DE{ext}"

    return clean_name

def reorganize_files():
    """Reorganize files from new_txt to new_txt_organized."""
    if not os.path.exists(NEW_TXT_DIR):
        print(f"Source directory not found: {NEW_TXT_DIR}")
        return

    # Create directory structure
    create_directory_structure()

    # Process each file
    files = [f for f in os.listdir(NEW_TXT_DIR) if f.endswith('.txt')]

    print(f"\nProcessing {len(files)} files...\n")

    for filename in files:
        source_path = os.path.join(NEW_TXT_DIR, filename)

        # Determine category
        category = determine_category(filename)

        # Clean filename
        new_filename = clean_filename(filename)

        # Determine target path
        if category:
            target_path = os.path.join(TARGET_DIR, category, new_filename)
        else:
            target_path = os.path.join(TARGET_DIR, new_filename)

        # Copy file
        try:
            shutil.copy2(source_path, target_path)
            print(f"[OK] {filename}")
            print(f"  -> {category or 'root'}/{new_filename}")
        except Exception as e:
            print(f"[ERROR] Error processing {filename}: {e}")

    print(f"\n[DONE] Reorganization complete!")
    print(f"Output directory: {TARGET_DIR}")

if __name__ == "__main__":
    reorganize_files()
