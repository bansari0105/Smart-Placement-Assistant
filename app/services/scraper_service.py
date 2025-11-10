"""
Web scraper service for extracting company information from websites.
Includes retry logic, rate limiting, robust HTML parsing, and name-based search.
"""
import time
import random
import logging
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse, quote_plus
import requests
from bs4 import BeautifulSoup
from firebase_admin import firestore
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScraperService:
    """Web scraper with retry logic, rate limiting, robust parsing, and search fallback."""
    
    def __init__(self, db: firestore.Client, max_retries: int = 3, delay_range: tuple = (1, 3)):
        self.db = db
        self.max_retries = max_retries
        self.delay_range = delay_range
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _delay(self):
        """Add random delay to avoid rate limiting."""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def _fetch_with_retry(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with retry logic and exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                self._delay()
                response = self.session.get(url, timeout=30, allow_redirects=True)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
        return None
    
    def _search_company_website(self, company_name: str) -> Optional[str]:
        """
        Search for company website using search engine.
        Returns the first official website URL found.
        """
        try:
            logger.info(f"Searching for website: {company_name}")
            
            # Try multiple search strategies
            search_queries = [
                f"{company_name} official website",
                f"{company_name} company",
                f"site:{company_name.lower().replace(' ', '')}.com",
            ]
            
            for search_query in search_queries:
                try:
                    # Use DuckDuckGo HTML search (no API key needed)
                    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
                    
                    self._delay()
                    response = self.session.get(search_url, timeout=15)
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try to find official website links
                    # DuckDuckGo results are in <a> tags
                    result_links = soup.find_all('a', href=True, limit=10)
                    
                    for link in result_links:
                        href = link.get('href', '')
                        
                        # Extract URL from DuckDuckGo redirect
                        if 'uddg=' in href:
                            import urllib.parse
                            try:
                                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                                if 'uddg' in parsed:
                                    url = parsed['uddg'][0]
                                    # Filter out social media and common non-official sites
                                    exclude_domains = ['linkedin.com', 'facebook.com', 'twitter.com', 
                                                      'instagram.com', 'wikipedia.org', 'glassdoor.com',
                                                      'indeed.com', 'crunchbase.com', 'youtube.com',
                                                      'reddit.com', 'pinterest.com']
                                    domain = urlparse(url).netloc.lower()
                                    
                                    # Check if it's likely an official website
                                    company_words = company_name.lower().split()
                                    domain_contains_company = any(word in domain for word in company_words if len(word) > 3)
                                    
                                    if not any(excluded in domain for excluded in exclude_domains):
                                        # Prefer domains that contain company name
                                        if domain_contains_company:
                                            logger.info(f"Found company website: {url}")
                                            return url
                            except Exception:
                                continue
                        
                        # Also check direct links
                        if href.startswith('http') and not any(excluded in href for excluded in ['linkedin.com', 'facebook.com', 'twitter.com']):
                            domain = urlparse(href).netloc.lower()
                            company_words = company_name.lower().split()
                            if any(word in domain for word in company_words if len(word) > 3):
                                logger.info(f"Found company website: {href}")
                                return href
                    
                except Exception as e:
                    logger.debug(f"Search query '{search_query}' failed: {e}")
                    continue
            
            logger.warning(f"Could not find website for company: {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for company website: {e}")
            return None
    
    def _extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Try multiple selectors to extract text, robust to DOM changes."""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        return text
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        return None
    
    def _extract_list_items(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extract list items (for roles, skills, etc.)."""
        items = []
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 2:
                        items.append(text)
                if items:
                    break
            except Exception:
                continue
        return items[:20]  # Limit to 20 items
    
    def _extract_company_info(self, url: str, html_content: str, company_name: str = None) -> Dict:
        """Extract company information from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        # Use provided company name or extract from page
        name = company_name
        if not name:
            name_selectors = [
                'h1',
                'title',
                'meta[property="og:title"]',
                '.company-name',
                '[class*="company"] h1',
                '[class*="brand"]',
            ]
            name = self._extract_text(soup, name_selectors)
            if not name:
                title_tag = soup.find('title')
                if title_tag:
                    name = title_tag.get_text(strip=True).split('|')[0].split('-')[0].strip()
        
        # Extract description
        description_selectors = [
            'meta[name="description"]',
            'meta[property="og:description"]',
            '.description',
            '[class*="about"] p',
            '[class*="description"]',
            'section[class*="about"]',
            'div[class*="about"]',
        ]
        description = None
        for selector in description_selectors:
            if selector.startswith('meta'):
                meta = soup.select_one(selector)
                if meta:
                    desc = meta.get('content', '').strip()
                    if desc and len(desc) > 50:
                        description = desc
                        break
            else:
                desc = self._extract_text(soup, [selector])
                if desc and len(desc) > 50:
                    description = desc
                    break
        
        # Extract skills - look for common patterns
        skills_keywords = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js', 'nodejs',
            'flask', 'django', 'spring', 'sql', 'mongodb', 'postgresql', 'mysql',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'linux',
            'data structures', 'algorithms', 'machine learning', 'ai', 'tensorflow',
            'c++', 'c#', '.net', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
            'html', 'css', 'sass', 'typescript', 'redux', 'graphql', 'rest api',
        ]
        found_skills = []
        content_lower = html_content.lower()
        
        # Also look for skills in structured data (lists, job descriptions)
        skills_selectors = [
            'ul[class*="skill"] li',
            'div[class*="skill"]',
            'span[class*="skill"]',
            'li[class*="requirement"]',
            'div[class*="requirement"]',
        ]
        skill_elements = self._extract_list_items(soup, skills_selectors)
        for skill_elem in skill_elements:
            skill_lower = skill_elem.lower()
            # Check if it matches known keywords
            for keyword in skills_keywords:
                if keyword in skill_lower:
                    found_skills.append(keyword.title())
        
        # Also check content for keywords
        for keyword in skills_keywords:
            if keyword in content_lower and keyword.title() not in found_skills:
                found_skills.append(keyword.title())
        
        # Extract roles/job titles
        roles_keywords = [
            'software engineer', 'developer', 'programmer', 'data scientist',
            'data analyst', 'machine learning engineer', 'devops engineer',
            'frontend developer', 'backend developer', 'full stack developer',
            'product manager', 'project manager', 'business analyst',
            'quality assurance', 'qa engineer', 'test engineer',
        ]
        found_roles = []
        roles_selectors = [
            'div[class*="role"]',
            'div[class*="position"]',
            'div[class*="job"]',
            'li[class*="job"]',
            'h2[class*="job"]',
            'h3[class*="job"]',
        ]
        role_elements = self._extract_list_items(soup, roles_selectors)
        for role_elem in role_elements:
            role_lower = role_elem.lower()
            for keyword in roles_keywords:
                if keyword in role_lower:
                    found_roles.append(role_elem)
                    break
        
        # Extract eligibility requirements
        eligibility_keywords = [
            'eligibility', 'requirements', 'qualifications', 'education',
            'experience', 'degree', 'bachelor', 'master', 'phd',
            'cgpa', 'percentage', 'years of experience',
        ]
        eligibility_text = None
        for keyword in eligibility_keywords:
            # Look for sections containing eligibility info
            eligibility_selectors = [
                f'div[class*="{keyword}"]',
                f'section[class*="{keyword}"]',
                f'div[id*="{keyword}"]',
                f'*:contains("{keyword}")',
            ]
            for selector in eligibility_selectors:
                try:
                    if ':contains' not in selector:
                        elem = soup.select_one(selector)
                        if elem:
                            text = elem.get_text(strip=True)
                            if text and len(text) > 20:
                                eligibility_text = text[:500]  # Limit length
                                break
                except:
                    continue
            if eligibility_text:
                break
        
        # Extract hiring process
        process_keywords = [
            'process', 'hiring', 'recruitment', 'interview', 'selection',
            'round', 'stage', 'step',
        ]
        process_text = None
        for keyword in process_keywords:
            process_selectors = [
                f'div[class*="{keyword}"]',
                f'section[class*="{keyword}"]',
                f'div[id*="{keyword}"]',
                f'ol[class*="{keyword}"]',
                f'ul[class*="{keyword}"]',
            ]
            for selector in process_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        if text and len(text) > 20:
                            process_text = text[:500]  # Limit length
                            break
                except:
                    continue
            if process_text:
                break
        
        # If process not found, try to extract from lists
        if not process_text:
            process_lists = soup.find_all(['ol', 'ul'], limit=5)
            for list_elem in process_lists:
                list_text = list_elem.get_text(strip=True).lower()
                if any(keyword in list_text for keyword in ['round', 'interview', 'process', 'step']):
                    process_text = list_elem.get_text(strip=True)[:500]
                    break
        
        return {
            'name': name or 'Unknown Company',
            'source_url': url,
            'scraped_at': firestore.SERVER_TIMESTAMP,
            'description': description or '',
            'roles': found_roles[:10] if found_roles else [],
            'skills': list(set(found_skills))[:15] if found_skills else [],
            'eligibility': eligibility_text or '',
            'process': process_text or '',
            'last_updated': firestore.SERVER_TIMESTAMP,
        }
    
    def scrape_company(self, url: str = None, company_name: str = None) -> Optional[Dict]:
        """
        Scrape company information from a URL or search by company name.
        
        Args:
            url: Company website URL (optional)
            company_name: Company name for search fallback (required if url is None)
        
        Returns:
            Dict with company information or None on failure
        """
        # If URL is provided, use it directly
        if url:
            logger.info(f"Scraping company from URL: {url}")
            response = self._fetch_with_retry(url)
            if not response:
                logger.error(f"Failed to fetch URL: {url}")
                return None
            
            try:
                company_data = self._extract_company_info(url, response.text, company_name)
                return company_data
            except Exception as e:
                logger.error(f"Error extracting company info from {url}: {e}")
                return None
        
        # If no URL, search for company website
        if not company_name:
            logger.error("Neither URL nor company_name provided")
            return None
        
        logger.info(f"Searching for company website: {company_name}")
        found_url = self._search_company_website(company_name)
        
        if not found_url:
            logger.error(f"Could not find website for company: {company_name}")
            # Return minimal data with company name
            return {
                'name': company_name,
                'source_url': '',
                'scraped_at': firestore.SERVER_TIMESTAMP,
                'description': f'Information for {company_name}',
                'roles': [],
                'skills': [],
                'eligibility': '',
                'process': '',
                'last_updated': firestore.SERVER_TIMESTAMP,
            }
        
        # Scrape the found URL
        return self.scrape_company(url=found_url, company_name=company_name)
    
    def save_to_firestore(self, company_id: str, company_data: Dict) -> bool:
        """
        Save scraped company data to Firestore under companies_scraped/<companyId>.
        
        Args:
            company_id: The document ID in companies_scraped collection
            company_data: Company data to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection('companies_scraped').document(company_id)
            
            # Prepare data with timestamps
            data = {
                **company_data,
                'last_updated': firestore.SERVER_TIMESTAMP,
            }
            
            # Use set with merge to update or create
            doc_ref.set(data, merge=True)
            logger.info(f"Saved company data to Firestore: {company_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving to Firestore: {e}")
            return False
    
    def scrape_and_save(self, company_id: str, url: str = None, company_name: str = None) -> bool:
        """
        Scrape company and save to Firestore in one operation.
        
        Args:
            company_id: The document ID in companies_scraped collection
            url: Company website URL (optional)
            company_name: Company name for search fallback (required if url is None)
        
        Returns:
            True if successful, False otherwise
        """
        company_data = self.scrape_company(url=url, company_name=company_name)
        if not company_data:
            return False
        
        return self.save_to_firestore(company_id, company_data)


def parse_company_html(html_content: str, url: str, company_name: str = None) -> Dict:
    """
    Unit-testable parsing function.
    Extracts company information from HTML content.
    """
    class DummyDB:
        pass
    
    scraper = ScraperService(DummyDB())
    return scraper._extract_company_info(url, html_content, company_name)
