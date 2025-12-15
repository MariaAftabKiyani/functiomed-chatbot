"""
Complete Web Scraper for functiomed
Extracts ALL content: services, team, notfall, wissenswertes, kontakt, shop
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


class FunctiOMedScraperComplete:
    """Complete scraper for functiomed website - all sections"""
    
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
        
        # Define all sections to scrape
        self.sections_to_scrape = {
            'angebot': '/angebot/',      # Services (22 pages)
            'team': '/team',             # Team page
            'notfall': '/notfall',       # Emergency info
            'kontakt': '/kontakt',       # Contact
            # 'wissenswertes': '/wissenswertes',  # Knowledge (if exists)
            # 'shop': '/shop',            # Shop (if exists)
        }
    
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
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
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
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'div']):
            text = element.get_text(strip=True)
            
            # Filter out very short fragments and navigation items
            if text and len(text) > 20 and not any(skip in text.lower() for skip in ['cookie', 'datenschutz', 'impressum']):
                
                # Add formatting based on tag
                if element.name in ['h1', 'h2', 'h3', 'h4']:
                    text_parts.append(f"\n## {text}\n")
                elif element.name == 'li':
                    text_parts.append(f"- {text}")
                elif element.name == 'p':
                    text_parts.append(text)
        
        # Join and clean up extra whitespace
        full_text = '\n'.join(text_parts)
        
        # Remove excessive newlines
        while '\n\n\n' in full_text:
            full_text = full_text.replace('\n\n\n', '\n\n')
        
        return full_text.strip()
    
    def sanitize_filename(self, url: str, section: str) -> str:
        """Convert URL to safe filename with section prefix"""
        # Get last part of URL path
        path_parts = url.rstrip('/').split('/')
        
        if section == 'angebot':
            # For service pages, use the service name
            filename = path_parts[-1] if len(path_parts) > 0 else 'service'
        else:
            # For other sections, use section name
            filename = section
        
        # Replace special characters
        filename = filename.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
        filename = filename.replace('ß', 'ss')
        
        # Keep only alphanumeric and hyphens
        filename = ''.join(c if c.isalnum() or c == '-' else '_' for c in filename)
        
        return filename
    
    def get_section_from_url(self, url: str) -> str:
        """Determine which section a URL belongs to"""
        for section, path in self.sections_to_scrape.items():
            if path in url:
                return section
        return 'other'
    
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
        
        # Determine section
        section = self.get_section_from_url(url)
        
        # Create filename
        base_filename = self.sanitize_filename(url, section)
        filename = f"{base_filename}_{language}.txt"
        filepath = self.output_dir / filename
        
        # Add metadata header to file
        header = f"""Source: {url}
Section: {section}
Scraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Language: {language}
{'='*80}

"""
        
        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(header + text)
            
            logger.info(f"✓ Saved: {filename} ({len(text)} chars, {language}, {section})")
            
            # Track for metadata
            self.scraped_pages.append({
                'url': url,
                'filename': filename,
                'section': section,
                'language': language,
                'char_count': len(text),
                'scraped_at': datetime.now().isoformat()
            })
            
            return True
            
        except IOError as e:
            logger.error(f"Failed to write {filepath}: {e}")
            return False
    
    def discover_all_pages(self) -> List[str]:
        """Discover all relevant pages from website"""
        logger.info("Discovering all pages from website...")
        
        soup = self.get_page_content(self.base_url)
        if not soup:
            logger.error("Failed to load homepage")
            return []
        
        discovered_urls = set()
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if it matches any target section
            for section, path in self.sections_to_scrape.items():
                if path in href:
                    # Normalize URL
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = self.base_url + href
                    else:
                        full_url = self.base_url + '/' + href
                    
                    # Remove query parameters and fragments
                    full_url = full_url.split('?')[0].split('#')[0]
                    
                    # Skip English pages and certain patterns
                    if not any(skip in full_url for skip in ['/en/', '?page=']):
                        discovered_urls.add(full_url)
        
        # Add known important pages manually (in case they're not in navigation)
        important_pages = [
            f"{self.base_url}/team",
            f"{self.base_url}/notfall",
            f"{self.base_url}/kontakt",
        ]
        
        for page in important_pages:
            discovered_urls.add(page)
        
        urls = sorted(list(discovered_urls))
        
        # Log summary by section
        sections_count = {}
        for url in urls:
            section = self.get_section_from_url(url)
            sections_count[section] = sections_count.get(section, 0) + 1
        
        logger.info(f"Found {len(urls)} total pages:")
        for section, count in sorted(sections_count.items()):
            logger.info(f"  - {section}: {count} pages")
        
        return urls
    
    def scrape_all(self, urls: Optional[List[str]] = None, delay: float = 1.0):
        """
        Scrape all pages
        
        Args:
            urls: List of URLs to scrape. If None, auto-discover from homepage
            delay: Delay between requests in seconds (be polite!)
        """
        if urls is None:
            urls = self.discover_all_pages()
        
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
        self.print_summary(success_count, len(urls))
    
    def save_metadata(self):
        """Save scraping metadata to JSON file"""
        # Group by section
        sections = {}
        for page in self.scraped_pages:
            section = page['section']
            if section not in sections:
                sections[section] = []
            sections[section].append(page)
        
        metadata = {
            'scrape_date': datetime.now().isoformat(),
            'base_url': self.base_url,
            'total_pages': len(self.scraped_pages),
            'sections': {
                section: {
                    'count': len(pages),
                    'pages': pages
                }
                for section, pages in sections.items()
            }
        }
        
        metadata_file = self.output_dir / '_scrape_metadata.json'
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, indent=2, ensure_ascii=False, fp=f)
        
        logger.info(f"Metadata saved to: {metadata_file}")
    
    def print_summary(self, success_count: int, total_count: int):
        """Print scraping summary"""
        logger.info("\n" + "="*80)
        logger.info("SCRAPING COMPLETE")
        logger.info("="*80)
        logger.info(f"Successfully scraped: {success_count}/{total_count} pages")
        
        # Group by section
        sections = {}
        for page in self.scraped_pages:
            section = page['section']
            sections[section] = sections.get(section, 0) + 1
        
        logger.info("\nPages by section:")
        for section, count in sorted(sections.items()):
            logger.info(f"  - {section}: {count}")
        
        # Group by language
        languages = {}
        for page in self.scraped_pages:
            lang = page['language']
            languages[lang] = languages.get(lang, 0) + 1
        
        logger.info("\nPages by language:")
        for lang, count in sorted(languages.items()):
            logger.info(f"  - {lang}: {count}")
        
        logger.info(f"\nOutput directory: {self.output_dir.absolute()}")
        logger.info(f"Metadata saved: {self.output_dir / '_scrape_metadata.json'}")
        logger.info("="*80)


def main():
    """Main execution"""
    
    # Initialize scraper
    scraper = FunctiOMedScraperComplete(output_dir="output/scraped_content")
    
    # Option 1: Auto-discover and scrape all pages (RECOMMENDED)
    scraper.scrape_all(delay=1.0)
    
    # Option 2: Scrape specific sections only (uncomment to use)
    # specific_urls = [
    #     "https://www.functiomed.ch/team",
    #     "https://www.functiomed.ch/notfall",
    #     "https://www.functiomed.ch/kontakt",
    # ]
    # scraper.scrape_all(urls=specific_urls, delay=1.0)


if __name__ == "__main__":
    main()