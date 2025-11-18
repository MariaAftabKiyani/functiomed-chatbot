"""
Simple Web Scraper for functiomed.ch
Extracts clean text from service pages and saves to .txt files
"""
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Optional
import time
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class FunctiOMedScraper:
    """Simple scraper for functiomed.ch website"""
    
    def __init__(self, output_dir: str = "output/scraped_content"):
        self.base_url = "https://www.functiomed.ch"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Request headers to mimic browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Track scraped pages
        self.scraped_pages: List[Dict] = []
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch page content with error handling"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words
        Returns 'DE' for German, 'EN' for English
        """
        # German indicators (more common in medical context)
        german_words = [
            'und', 'der', 'die', 'das', 'für', 'mit', 'bei', 'von', 
            'durch', 'behandlung', 'therapie', 'können', 'wird', 'auch'
        ]
        
        # English indicators
        english_words = [
            'the', 'and', 'for', 'with', 'treatment', 'therapy', 
            'can', 'will', 'also', 'our'
        ]
        
        text_lower = text.lower()
        
        german_count = sum(1 for word in german_words if f' {word} ' in text_lower)
        english_count = sum(1 for word in english_words if f' {word} ' in text_lower)
        
        # Default to German (primary language of site)
        return 'DE' if german_count >= english_count else 'EN'
    
    def clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text from page, removing navigation and footer"""
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Try to find main content area (common WordPress classes)
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_='content') or
            soup.find('div', class_='entry-content') or
            soup.find('body')
        )
        
        if not main_content:
            return ""
        
        # Extract text with structure preserved
        text_parts = []
        
        # Get title
        title = soup.find('h1')
        if title:
            text_parts.append(f"=== {title.get_text(strip=True)} ===\n")
        
        # Get all text content
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
            text = element.get_text(strip=True)
            if text and len(text) > 20:  # Filter out very short fragments
                
                # Add formatting based on tag
                if element.name in ['h1', 'h2', 'h3', 'h4']:
                    text_parts.append(f"\n## {text}\n")
                elif element.name == 'li':
                    text_parts.append(f"- {text}")
                else:
                    text_parts.append(text)
        
        # Join and clean up extra whitespace
        full_text = '\n'.join(text_parts)
        
        # Remove excessive newlines
        while '\n\n\n' in full_text:
            full_text = full_text.replace('\n\n\n', '\n\n')
        
        return full_text.strip()
    
    def sanitize_filename(self, url: str) -> str:
        """Convert URL to safe filename"""
        # Get last part of URL path
        filename = url.rstrip('/').split('/')[-1]
        
        # Replace special characters
        filename = filename.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
        filename = filename.replace('ß', 'ss')
        
        # Keep only alphanumeric and hyphens
        filename = ''.join(c if c.isalnum() or c == '-' else '_' for c in filename)
        
        return filename
    
    def scrape_page(self, url: str) -> bool:
        """Scrape a single page and save to file"""
        logger.info(f"Scraping: {url}")
        
        # Fetch content
        soup = self.get_page_content(url)
        if not soup:
            return False
        
        # Extract clean text
        text = self.clean_text(soup)
        if not text or len(text) < 100:
            logger.warning(f"Insufficient content extracted from {url}")
            return False
        
        # Detect language
        language = self.detect_language(text)
        
        # Create filename
        base_filename = self.sanitize_filename(url)
        filename = f"{base_filename}_{language}.txt"
        filepath = self.output_dir / filename
        
        # Add metadata header to file
        header = f"""Source: {url}
Scraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Language: {language}
{'='*80}

"""
        
        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(header + text)
            
            logger.info(f"✓ Saved: {filename} ({len(text)} chars, {language})")
            
            # Track for metadata
            self.scraped_pages.append({
                'url': url,
                'filename': filename,
                'language': language,
                'char_count': len(text),
                'scraped_at': datetime.now().isoformat()
            })
            
            return True
            
        except IOError as e:
            logger.error(f"Failed to write {filepath}: {e}")
            return False
    
    def discover_service_pages(self) -> List[str]:
        """Discover all service pages from homepage"""
        logger.info("Discovering service pages from homepage...")
        
        soup = self.get_page_content(self.base_url)
        if not soup:
            logger.error("Failed to load homepage")
            return []
        
        # Find all links to /angebot/ pages
        service_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if it's a service page
            if '/angebot/' in href:
                # Normalize URL
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = self.base_url + href
                else:
                    full_url = self.base_url + '/' + href
                
                # Remove query parameters and fragments
                full_url = full_url.split('?')[0].split('#')[0]
                service_urls.add(full_url)
        
        urls = sorted(list(service_urls))
        logger.info(f"Found {len(urls)} service pages")
        
        return urls
    
    def scrape_all(self, urls: Optional[List[str]] = None, delay: float = 1.0):
        """
        Scrape all pages
        
        Args:
            urls: List of URLs to scrape. If None, auto-discover from homepage
            delay: Delay between requests in seconds (be polite!)
        """
        if urls is None:
            urls = self.discover_service_pages()
        
        if not urls:
            logger.error("No URLs to scrape")
            return
        
        logger.info(f"Starting to scrape {len(urls)} pages...")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        
        success_count = 0
        
        for i, url in enumerate(urls, 1):
            logger.info(f"\n[{i}/{len(urls)}] Processing...")
            
            if self.scrape_page(url):
                success_count += 1
            
            # Be polite - delay between requests
            if i < len(urls):
                time.sleep(delay)
        
        # Save metadata
        self.save_metadata()
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("SCRAPING COMPLETE")
        logger.info("="*80)
        logger.info(f"Successfully scraped: {success_count}/{len(urls)} pages")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        logger.info(f"Metadata saved: {self.output_dir / '_scrape_metadata.json'}")
        logger.info("="*80)
    
    def save_metadata(self):
        """Save scraping metadata to JSON file"""
        metadata = {
            'scrape_date': datetime.now().isoformat(),
            'base_url': self.base_url,
            'total_pages': len(self.scraped_pages),
            'pages': self.scraped_pages
        }
        
        metadata_file = self.output_dir / '_scrape_metadata.json'
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, indent=2, ensure_ascii=False, fp=f)
        
        logger.info(f"Metadata saved to: {metadata_file}")


def main():
    """Main execution"""
    
    # Initialize scraper
    scraper = FunctiOMedScraper(output_dir="output/scraped_content")
    
    # Option 1: Auto-discover and scrape all service pages
    scraper.scrape_all(delay=1.0)
    
    # Option 2: Scrape specific pages (uncomment to use)
    # specific_urls = [
    #     "https://www.functiomed.ch/angebot/orthopaedie-und-traumatologie",
    #     "https://www.functiomed.ch/angebot/rheumatologie-innere-medizin",
    # ]
    # scraper.scrape_all(urls=specific_urls, delay=1.0)


if __name__ == "__main__":
    main()


# Updated DocumentProcessor code to add below (for reference)
"""
Add these methods to your existing DocumentProcessor class:

def extract_text_from_txt(self, txt_path: Path) -> Dict:
    '''Extract text from .txt or .md files'''
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split header from content (if exists)
        if '='*40 in content:
            parts = content.split('='*40, 1)
            if len(parts) == 2:
                full_text = parts[1].strip()
            else:
                full_text = content
        else:
            full_text = content
        
        # Count lines as pseudo-pages
        lines = full_text.split('\n')
        num_pages = max(1, len(lines) // 50)  # ~50 lines per "page"
        
        return {
            "full_text": full_text,
            "page_texts": [{"page_number": 1, "text": full_text}],
            "num_pages": num_pages
        }
        
    except Exception as e:
        logger.error(f"Error reading text file {txt_path}: {e}")
        return {
            "full_text": "",
            "page_texts": [],
            "num_pages": 0,
            "error": str(e)
        }

def process_txt(self, txt_path: Path) -> Optional[Document]:
    '''Process a single .txt or .md file'''
    logger.info(f"Processing: {txt_path}")
    
    # Extract text
    extracted = self.extract_text_from_txt(txt_path)
    
    if not extracted["full_text"]:
        logger.warning(f"No text extracted from {txt_path}")
        return None
    
    # Get metadata
    filename = txt_path.name
    category = self.get_category_from_path(txt_path)
    language = self.detect_language(filename)
    
    metadata = {
        "filename": filename,
        "filepath": str(txt_path),
        "category": category,
        "language": language,
        "num_pages": extracted["num_pages"],
        "page_texts": extracted["page_texts"]
    }
    
    # Create Document object
    document = Document(
        text=extracted["full_text"],
        metadata=metadata,
        filename=filename,
        category=category,
        language=language
    )
    
    return document

# Update ingest_documents() method to include .txt and .md files:
def ingest_documents(self) -> List[Document]:
    '''Ingest all PDF and text documents from base path'''
    logger.info(f"Starting document ingestion from: {self.base_path}")
    
    if not self.base_path.exists():
        logger.error(f"Path does not exist: {self.base_path}")
        return []
    
    # Find all PDF, TXT, and MD files recursively
    pdf_files = list(self.base_path.rglob("*.pdf"))
    txt_files = list(self.base_path.rglob("*.txt"))
    md_files = list(self.base_path.rglob("*.md"))
    
    all_files = pdf_files + txt_files + md_files
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    logger.info(f"Found {len(txt_files)} TXT files")
    logger.info(f"Found {len(md_files)} MD files")
    logger.info(f"Total files to process: {len(all_files)}")
    
    # Process each file
    processed_count = 0
    for file_path in all_files:
        if file_path.suffix.lower() == '.pdf':
            document = self.process_pdf(file_path)
        else:  # .txt or .md
            document = self.process_txt(file_path)
        
        if document:
            self.documents.append(document)
            processed_count += 1
    
    logger.info(f"Successfully processed {processed_count}/{len(all_files)} documents")
    
    # Print summary
    self.print_summary()
    
    return self.documents
"""