"""
Dedicated Company Scraper Module
Automatically scrapes ANY company name from multiple sources
"""
import time
import random
import logging
import re
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse, quote_plus
import requests
from bs4 import BeautifulSoup
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class CompanyScraper:
    """
    Dedicated scraper for company information.
    Searches Google/Bing, crawls official websites, and extracts structured data.
    """
    
    def __init__(self, db: firestore.Client, max_retries: int = 3, delay_range: tuple = (1, 3)):
        self.db = db
        self.max_retries = max_retries
        self.delay_range = delay_range
        self.session = requests.Session()
        
        # Rotate user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        self._update_user_agent()
    
    def _update_user_agent(self):
        """Rotate user agent to avoid detection."""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
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
                self._update_user_agent()
                response = self.session.get(url, timeout=30, allow_redirects=True)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
        return None
    
    def _validate_company_website(self, url: str, company_name: str) -> bool:
        """
        Validate that the website actually belongs to the company.
        Checks page title, meta tags, and content for company name.
        """
        try:
            response = self._fetch_with_retry(url)
            if not response:
                return False
            
            soup = BeautifulSoup(response.text, 'html.parser')
            content_lower = response.text.lower()
            company_lower = company_name.lower()
            
            # Check page title
            title = soup.find('title')
            if title:
                title_text = title.get_text().lower()
                if company_lower in title_text or any(word in title_text for word in company_lower.split() if len(word) > 3):
                    return True
            
            # Check meta tags
            og_site = soup.find('meta', property='og:site_name')
            if og_site:
                site_name = og_site.get('content', '').lower()
                if company_lower in site_name or any(word in site_name for word in company_lower.split() if len(word) > 3):
                    return True
            
            # Check if company name appears prominently in content (first 2000 chars)
            content_preview = content_lower[:2000]
            company_words = [w for w in company_lower.split() if len(w) > 3]
            if company_words:
                matches = sum(1 for word in company_words if word in content_preview)
                if matches >= len(company_words) * 0.6:  # At least 60% of words match
                    return True
            
            return False
        except Exception as e:
            logger.debug(f"Error validating website: {e}")
            return False
    
    def search_company_website(self, company_name: str) -> Optional[str]:
        """
        Search Google/Bing for company official website.
        Returns the most likely official website URL.
        Validates that the website actually belongs to the company.
        """
        try:
            # For well-known companies, try direct domain first
            well_known_companies = {
                'google': 'https://www.google.com',
                'microsoft': 'https://www.microsoft.com',
                'amazon': 'https://www.amazon.com',
                'apple': 'https://www.apple.com',
                'meta': 'https://www.meta.com',
                'facebook': 'https://www.facebook.com',
                'tcs': 'https://www.tcs.com',
                'infosys': 'https://www.infosys.com',
                'wipro': 'https://www.wipro.com',
                'accenture': 'https://www.accenture.com',
            }
            
            company_key = company_name.lower().strip()
            if company_key in well_known_companies:
                url = well_known_companies[company_key]
                if self._validate_company_website(url, company_name):
                    logger.info(f"Using well-known company URL: {url}")
                    return url
            
            search_queries = [
                f'"{company_name}" official website',
                f"{company_name} official website",
                f"{company_name} company careers",
                f"{company_name} website",
            ]
            
            for search_query in search_queries:
                try:
                    # Use DuckDuckGo (no API key needed)
                    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
                    response = self._fetch_with_retry(search_url)
                    
                    if response:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        links = soup.find_all('a', href=True, limit=20)
                        
                        for link in links:
                            href = link.get('href', '')
                            
                            # Extract from DuckDuckGo redirect
                            if 'uddg=' in href:
                                import urllib.parse
                                try:
                                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                                    if 'uddg' in parsed:
                                        url = parsed['uddg'][0]
                                        # Filter out social media
                                        exclude = [
                                            'linkedin.com', 'facebook.com', 'twitter.com',
                                            'wikipedia.org', 'glassdoor.com', 'indeed.com',
                                            'crunchbase.com', 'youtube.com', 'reddit.com'
                                        ]
                                        if not any(ex in url.lower() for ex in exclude):
                                            # Validate that this is actually the company's website
                                            if self._validate_company_website(url, company_name):
                                                logger.info(f"Found and validated official website: {url}")
                                                return url
                                            # Also check domain match as fallback
                                            company_slug = company_name.lower().replace(' ', '')
                                            domain = urlparse(url).netloc.lower().replace('www.', '')
                                            if company_slug[:5] in domain or domain.startswith(company_slug[:3]):
                                                logger.info(f"Found potential website (domain match): {url}")
                                                return url
                                except:
                                    continue
                            
                            # Check direct links
                            if href.startswith('http') and 'uddg' not in href:
                                exclude = ['linkedin.com', 'facebook.com', 'twitter.com', 'wikipedia.org']
                                if not any(ex in href.lower() for ex in exclude):
                                    # Validate website
                                    if self._validate_company_website(href, company_name):
                                        logger.info(f"Found and validated website: {href}")
                                        return href
                                    # Fallback: domain match
                                    domain = urlparse(href).netloc.lower()
                                    company_words = company_name.lower().split()
                                    if any(word in domain for word in company_words if len(word) > 3):
                                        logger.info(f"Found potential website (domain match): {href}")
                                        return href
                except Exception as e:
                    logger.debug(f"Search query '{search_query}' failed: {e}")
                    continue
            
            # Try common domain patterns
            company_slug = company_name.lower().replace(' ', '').replace('.', '').replace(',', '')
            common_domains = [
                f"https://www.{company_slug}.com",
                f"https://{company_slug}.com",
                f"https://www.{company_slug}.in",
                f"https://{company_slug}.in",
                f"https://www.{company_slug}.co.in",
            ]
            
            for domain in common_domains:
                try:
                    test_response = self.session.get(domain, timeout=5, allow_redirects=True)
                    if test_response.status_code == 200:
                        # Validate it's the right company
                        if self._validate_company_website(domain, company_name):
                            logger.info(f"Found and validated website via pattern: {domain}")
                            return domain
                except:
                    continue
            
        except Exception as e:
            logger.error(f"Error searching for website: {e}")
        
        return None
    
    def scrape_official_website(self, url: str, company_name: str) -> Dict:
        """Scrape company official website for information."""
        data = {
            'description': '',
            'skills': [],
            'eligibility': '',
            'process': '',
            'salary': '',
            'location': '',
            'source_url': url,
        }
        
        try:
            response = self._fetch_with_retry(url)
            if not response:
                return data
            
            soup = BeautifulSoup(response.text, 'html.parser')
            content_lower = response.text.lower()
            
            # Extract description - try multiple sources
            desc_selectors = [
                'meta[name="description"]',
                'meta[property="og:description"]',
                '.about-section',
                '.company-description',
                'section[class*="about"]',
                'div[class*="about"]',
                'p[class*="description"]',
                'div[id*="about"]',
            ]
            for selector in desc_selectors:
                if selector.startswith('meta'):
                    meta = soup.select_one(selector)
                    if meta:
                        desc = meta.get('content', '').strip()
                        if len(desc) > 50:
                            data['description'] = desc[:500]
                            break
                else:
                    elem = soup.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        if len(text) > 100:
                            data['description'] = text[:500]
                            break
            
            # Fallback: Extract from main content if no description found
            if not data['description'] or len(data['description']) < 50:
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    paragraphs = main_content.find_all('p', limit=5)
                    long_paragraphs = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 100]
                    if long_paragraphs:
                        data['description'] = ' '.join(long_paragraphs[:2])[:500]
            
            # Extract skills
            skills_keywords = [
                'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
                'flask', 'django', 'spring', 'sql', 'mongodb', 'postgresql',
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git',
                'data structures', 'algorithms', 'machine learning', 'ai',
            ]
            found_skills = []
            for skill in skills_keywords:
                if skill in content_lower:
                    found_skills.append(skill.title())
            data['skills'] = list(set(found_skills))[:15]
            
            # Extract eligibility
            eligibility_patterns = [
                r'eligibility[:\s]+([^\.]+)',
                r'qualification[:\s]+([^\.]+)',
                r'cgpa[:\s]+([0-9.]+)',
                r'percentage[:\s]+([0-9.]+)',
                r'education[:\s]+([^\.]+)',
            ]
            for pattern in eligibility_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    data['eligibility'] = match.group(1).strip()[:300]
                    break
            
            # Extract salary
            salary_patterns = [
                r'(\d+\.?\d*)\s*(lpa|lakh|lakhs|LPA)',
                r'salary[:\s]+([^\.]+)',
                r'package[:\s]+([^\.]+)',
                r'ctc[:\s]+([^\.]+)',
            ]
            for pattern in salary_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    data['salary'] = match.group(0).strip()[:200]
                    break
            
            # Extract interview process
            process_keywords = ['interview process', 'hiring process', 'selection process', 'round']
            process_sections = soup.find_all(['div', 'section'], 
                                            class_=re.compile('process|interview|hiring|selection', re.I))
            process_texts = []
            for section in process_sections[:3]:
                text = section.get_text(strip=True)
                if any(kw in text.lower() for kw in process_keywords):
                    process_texts.append(text[:300])
            if process_texts:
                data['process'] = ' | '.join(process_texts)[:1000]
            
            # Extract location/address - AGENTIC AI APPROACH
            location_found = False
            
            # Strategy 1: Look for structured data (JSON-LD, microdata)
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict):
                        address = json_data.get('address') or json_data.get('location') or json_data.get('headquarters')
                        if address:
                            if isinstance(address, dict):
                                location_parts = []
                                if address.get('addressLocality'):
                                    location_parts.append(address['addressLocality'])
                                if address.get('addressRegion'):
                                    location_parts.append(address['addressRegion'])
                                if address.get('addressCountry'):
                                    location_parts.append(address['addressCountry'])
                                if location_parts:
                                    data['location'] = ', '.join(location_parts)
                                    location_found = True
                                    break
                            elif isinstance(address, str):
                                data['location'] = address[:200]
                                location_found = True
                                break
                except:
                    continue
            
            # Strategy 2: Look for contact/address sections
            if not location_found:
                location_selectors = [
                    '.address', '.location', '.contact', '.headquarters',
                    '[class*="address"]', '[class*="location"]', '[class*="contact"]',
                    '[id*="address"]', '[id*="location"]', '[id*="contact"]',
                    'address', 'footer address',
                ]
                for selector in location_selectors:
                    elements = soup.select(selector)
                    for elem in elements[:3]:
                        text = elem.get_text(strip=True)
                        location_indicators = ['vapi', 'mumbai', 'delhi', 'bangalore', 'pune', 'hyderabad', 
                                            'chennai', 'kolkata', 'gurgaon', 'noida', 'india', 'usa', 'uk']
                        if any(indicator in text.lower() for indicator in location_indicators):
                            lines = [line.strip() for line in text.split('\n') if line.strip()]
                            for line in lines:
                                if any(indicator in line.lower() for indicator in location_indicators):
                                    data['location'] = line[:200]
                                    location_found = True
                                    break
                            if location_found:
                                break
                    if location_found:
                        break
            
            # Strategy 3: Search page content for location patterns
            if not location_found:
                location_patterns = [
                    r'located\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                    r'headquarters[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                    r'address[:\s]+([^\.\n]+(?:vapi|mumbai|delhi|bangalore|pune|hyderabad|chennai|kolkata|gurgaon|noida)[^\.\n]*)',
                    r'office[:\s]+([^\.\n]+(?:vapi|mumbai|delhi|bangalore|pune|hyderabad|chennai|kolkata|gurgaon|noida)[^\.\n]*)',
                    r'(vapi|mumbai|delhi|bangalore|pune|hyderabad|chennai|kolkata|gurgaon|noida)[^\.\n]*',
                ]
                for pattern in location_patterns:
                    matches = re.finditer(pattern, response.text, re.IGNORECASE)
                    for match in matches:
                        location_text = match.group(1 if match.lastindex else 0).strip()
                        if len(location_text) > 3 and len(location_text) < 200:
                            data['location'] = location_text[:200]
                            location_found = True
                            break
                    if location_found:
                        break
            
            # Strategy 4: Check meta tags
            if not location_found:
                location_meta = soup.find('meta', {'name': re.compile('location|address|city', re.I)})
                if location_meta:
                    data['location'] = location_meta.get('content', '')[:200]
                    location_found = True
            
            # Strategy 5: Search for "About Us" or "Contact Us" pages
            if not location_found:
                contact_links = soup.find_all('a', href=re.compile(r'contact|about|location|address', re.I))
                for link in contact_links[:3]:
                    contact_url = urljoin(url, link.get('href', ''))
                    try:
                        contact_response = self._fetch_with_retry(contact_url)
                        if contact_response:
                            contact_soup = BeautifulSoup(contact_response.text, 'html.parser')
                            location_elem = contact_soup.find(['div', 'p', 'span'], 
                                                              class_=re.compile('location|address|city', re.I))
                            if location_elem:
                                location_text = location_elem.get_text(strip=True)
                                if len(location_text) > 3 and len(location_text) < 200:
                                    data['location'] = location_text[:200]
                                    location_found = True
                                    break
                    except:
                        continue
        
        except Exception as e:
            logger.error(f"Error scraping official website: {e}")
        
        return data
    
    def scrape_company(self, company_name: str, optional_url: Optional[str] = None) -> Dict:
        """
        Main function to scrape company information.
        Searches for website, scrapes data, and returns structured information.
        
        Args:
            company_name: Name of the company to scrape
            optional_url: Optional direct URL to scrape
            
        Returns:
            Dictionary with company information:
            {
                "description": str,
                "skills": [str],
                "eligibility": str,
                "process": str,
                "salary": str,
                "source_url": str
            }
        """
        logger.info(f"Starting scrape for company: {company_name}")
        
        merged_data = {
            'description': '',
            'skills': [],
            'eligibility': '',
            'process': '',
            'salary': '',
            'location': '',
            'source_url': '',
            'collectedFrom': 'scraped',
        }
        
        # Get website URL
        target_url = optional_url
        if not target_url:
            target_url = self.search_company_website(company_name)
        
        # Scrape official website
        if target_url:
            official_data = self.scrape_official_website(target_url, company_name)
            merged_data.update(official_data)
        
        # Clean and validate data
        if not merged_data.get('description') or len(merged_data.get('description', '')) < 50:
            # Try to get better description from Wikipedia or other sources
            merged_data['description'] = self._get_company_description_fallback(company_name)
            if not merged_data['description']:
                # Don't save generic placeholder - return None to indicate scraping failed
                logger.warning(f"Could not extract meaningful description for {company_name}")
                merged_data['description'] = f"Information about {company_name} is being gathered. Please try again in a moment."
        
        # Remove duplicates from skills
        merged_data['skills'] = list(set(merged_data['skills']))[:20]
        
        # Ensure all fields have values
        if not merged_data.get('eligibility'):
            merged_data['eligibility'] = "Eligibility criteria will be updated soon."
        if not merged_data.get('process'):
            merged_data['process'] = "Interview process details will be updated soon."
        if not merged_data.get('salary'):
            merged_data['salary'] = "Salary information will be updated soon."
        
        logger.info(f"Scraping completed for {company_name}")
        return merged_data
    
    def _get_company_description_fallback(self, company_name: str) -> str:
        """Try to get company description from Wikipedia as fallback."""
        try:
            wiki_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"
            response = self._fetch_with_retry(wiki_url)
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Get first paragraph from Wikipedia
                first_para = soup.find('div', class_='mw-parser-output')
                if first_para:
                    paragraphs = first_para.find_all('p', limit=2)
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if len(text) > 100 and not text.startswith('Coordinates'):
                            return text[:500]
        except Exception as e:
            logger.debug(f"Wikipedia fallback failed: {e}")
        return ""
    
    def save_to_firestore(self, company_name: str, data: Dict) -> bool:
        """
        Save scraped company data to Firestore.
        Creates document if it doesn't exist, updates if it does.
        Only saves if data quality is good (has meaningful description).
        
        Args:
            company_name: Company name
            data: Company data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate data quality before saving
            description = data.get('description', '')
            if not description or len(description) < 50:
                logger.warning(f"Not saving {company_name} - description too short or generic")
                return False
            
            # Check if description is too generic
            generic_phrases = [
                'is a company',
                'detailed information is being gathered',
                'information is being gathered',
            ]
            if any(phrase in description.lower() for phrase in generic_phrases):
                logger.warning(f"Not saving {company_name} - generic description detected")
                return False
            
            # Create document ID from company name
            doc_id = re.sub(r'[^a-zA-Z0-9_-]', '_', company_name.lower())[:50]
            doc_ref = self.db.collection('company_knowledge_base').document(doc_id)
            
            # Prepare data
            firestore_data = {
                'companyName': company_name,
                'description': description,
                'skills': data.get('skills', []),
                'eligibility': data.get('eligibility', ''),
                'process': data.get('process', ''),
                'salary': data.get('salary', ''),
                'source_url': data.get('source_url', ''),
                'last_updated': firestore.SERVER_TIMESTAMP,
                'collectedFrom': data.get('collectedFrom', 'scraped'),
            }
            
            # Save to Firestore (merge if exists, create if not)
            doc_ref.set(firestore_data, merge=True)
            logger.info(f"Saved {company_name} to Firestore (ID: {doc_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to Firestore: {e}")
            return False

