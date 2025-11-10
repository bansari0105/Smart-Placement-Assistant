"""
Advanced Multi-Source Web Scraper for Company Information
Scrapes from: Official websites, Ambitionbox, GeeksForGeeks, Naukri, Careers pages
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


class ChatbotScraper:
    """Multi-source web scraper for company placement information."""
    
    def __init__(self, max_retries: int = 3, delay_range: tuple = (1, 3)):
        self.max_retries = max_retries
        self.delay_range = delay_range
        self.session = requests.Session()
        
        # Rotate user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
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
                self._update_user_agent()  # Rotate user agent
                response = self.session.get(url, timeout=30, allow_redirects=True)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
        return None
    
    def _search_company_website(self, company_name: str) -> Optional[str]:
        """Search for company official website using multiple strategies."""
        try:
            # Strategy 1: Try DuckDuckGo search
            search_queries = [
                f"{company_name} official website",
                f"{company_name} company careers",
                f"{company_name} website",
            ]
            
            for search_query in search_queries:
                try:
                    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
                    response = self._fetch_with_retry(search_url)
                    
                    if response:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        links = soup.find_all('a', href=True, limit=15)
                        
                        for link in links:
                            href = link.get('href', '')
                            
                            # Extract from DuckDuckGo redirect
                            if 'uddg=' in href:
                                import urllib.parse
                                try:
                                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                                    if 'uddg' in parsed:
                                        url = parsed['uddg'][0]
                                        # Filter out social media and common non-official sites
                                        exclude = [
                                            'linkedin.com', 'facebook.com', 'twitter.com', 
                                            'wikipedia.org', 'glassdoor.com', 'indeed.com',
                                            'crunchbase.com', 'youtube.com', 'reddit.com'
                                        ]
                                        if not any(ex in url.lower() for ex in exclude):
                                            # Prefer domains that contain company name
                                            company_words = company_name.lower().replace(' ', '')
                                            domain = urlparse(url).netloc.lower().replace('www.', '')
                                            if company_words[:5] in domain or domain.startswith(company_words[:3]):
                                                logger.info(f"Found official website: {url}")
                                                return url
                                except:
                                    continue
                            
                            # Check direct links
                            if href.startswith('http') and 'uddg' not in href:
                                exclude = ['linkedin.com', 'facebook.com', 'twitter.com', 'wikipedia.org']
                                if not any(ex in href.lower() for ex in exclude):
                                    domain = urlparse(href).netloc.lower()
                                    company_words = company_name.lower().split()
                                    # Check if domain contains company name
                                    if any(word in domain for word in company_words if len(word) > 3):
                                        logger.info(f"Found potential website: {href}")
                                        return href
                except Exception as e:
                    logger.debug(f"Search query '{search_query}' failed: {e}")
                    continue
            
            # Strategy 2: Try common domain patterns
            company_slug = company_name.lower().replace(' ', '').replace('.', '').replace(',', '')
            common_domains = [
                f"https://www.{company_slug}.com",
                f"https://{company_slug}.com",
                f"https://www.{company_slug}.in",
                f"https://{company_slug}.in",
            ]
            
            for domain in common_domains:
                try:
                    test_response = self.session.get(domain, timeout=5, allow_redirects=True)
                    if test_response.status_code == 200:
                        logger.info(f"Found website via pattern: {domain}")
                        return domain
                except:
                    continue
            
        except Exception as e:
            logger.error(f"Error searching for website: {e}")
        
        return None
    
    def scrape_official_website(self, url: str, company_name: str) -> Dict:
        """Scrape company official website."""
        data = {
            'description': '',
            'skills': [],
            'eligibility': '',
            'process': '',
            'salary': '',
            'location': '',
        }
        
        try:
            response = self._fetch_with_retry(url)
            if not response:
                return data
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract description
            desc_selectors = [
                'meta[name="description"]',
                'meta[property="og:description"]',
                '.about-section',
                '.company-description',
                'section[class*="about"]',
            ]
            for selector in desc_selectors:
                if selector.startswith('meta'):
                    meta = soup.select_one(selector)
                    if meta:
                        data['description'] = meta.get('content', '')[:500]
                        break
                else:
                    elem = soup.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        if len(text) > 100:
                            data['description'] = text[:500]
                            break
            
            # Extract location/address - AGENTIC AI APPROACH
            location_found = False
            
            # Strategy 1: Look for structured data (JSON-LD, microdata)
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict):
                        # Check for address in various formats
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
                    for elem in elements[:3]:  # Check first 3 matches
                        text = elem.get_text(strip=True)
                        # Look for location indicators
                        location_indicators = ['vapi', 'mumbai', 'delhi', 'bangalore', 'pune', 'hyderabad', 
                                            'chennai', 'kolkata', 'gurgaon', 'noida', 'india', 'usa', 'uk']
                        if any(indicator in text.lower() for indicator in location_indicators):
                            # Extract location (take first 200 chars)
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
                            # Look for location in contact page
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
            
            # Extract skills from careers/jobs page
            skills_keywords = [
                'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
                'flask', 'django', 'spring', 'sql', 'mongodb', 'postgresql',
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git',
                'data structures', 'algorithms', 'machine learning', 'ai',
            ]
            content_lower = response.text.lower()
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
            ]
            for pattern in eligibility_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    data['eligibility'] = match.group(1).strip()[:300]
                    break
            
            # Extract salary/package
            salary_patterns = [
                r'(\d+\.?\d*)\s*(lpa|lakh|lakhs|LPA)',
                r'salary[:\s]+([^\.]+)',
                r'package[:\s]+([^\.]+)',
            ]
            for pattern in salary_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    data['salary'] = match.group(0).strip()[:200]
                    break
            
        except Exception as e:
            logger.error(f"Error scraping official website: {e}")
        
        return data
    
    def scrape_ambitionbox(self, company_name: str) -> Dict:
        """Scrape Ambitionbox for company reviews and information."""
        data = {
            'description': '',
            'skills': [],
            'eligibility': '',
            'process': '',
            'salary': '',
        }
        
        try:
            search_url = f"https://www.ambitionbox.com/reviews/{company_name.lower().replace(' ', '-')}"
            response = self._fetch_with_retry(search_url)
            
            if not response or response.status_code != 200:
                return data
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract interview process
            process_section = soup.find('div', class_=re.compile('interview-process|process'))
            if process_section:
                data['process'] = process_section.get_text(strip=True)[:500]
            
            # Extract salary information
            salary_section = soup.find('div', class_=re.compile('salary|compensation'))
            if salary_section:
                salary_text = salary_section.get_text(strip=True)
                salary_match = re.search(r'(\d+\.?\d*)\s*(lpa|lakh)', salary_text, re.IGNORECASE)
                if salary_match:
                    data['salary'] = f"{salary_match.group(1)} {salary_match.group(2).upper()}"
            
        except Exception as e:
            logger.error(f"Error scraping Ambitionbox: {e}")
        
        return data
    
    def scrape_geeksforgeeks(self, company_name: str) -> Dict:
        """Scrape GeeksForGeeks for interview experiences."""
        data = {
            'description': '',
            'skills': [],
            'eligibility': '',
            'process': '',
            'salary': '',
        }
        
        try:
            search_url = f"https://www.geeksforgeeks.org/{company_name.lower().replace(' ', '-')}-interview-experience/"
            response = self._fetch_with_retry(search_url)
            
            if not response or response.status_code != 200:
                # Try alternative URL pattern
                search_url = f"https://www.geeksforgeeks.org/tag/{company_name.lower().replace(' ', '-')}/"
                response = self._fetch_with_retry(search_url)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract interview process from articles
                articles = soup.find_all('article', limit=3)
                process_texts = []
                for article in articles:
                    text = article.get_text(strip=True)
                    if 'round' in text.lower() or 'interview' in text.lower():
                        process_texts.append(text[:300])
                
                if process_texts:
                    data['process'] = ' | '.join(process_texts)[:500]
                
                # Extract skills mentioned
                content_lower = response.text.lower()
                skills_keywords = [
                    'python', 'java', 'javascript', 'react', 'angular', 'sql',
                    'data structures', 'algorithms', 'system design',
                ]
                found_skills = []
                for skill in skills_keywords:
                    if skill in content_lower:
                        found_skills.append(skill.title())
                data['skills'] = list(set(found_skills))[:10]
        
        except Exception as e:
            logger.error(f"Error scraping GeeksForGeeks: {e}")
        
        return data
    
    def scrape_naukri(self, company_name: str) -> Dict:
        """Scrape Naukri for job postings and requirements."""
        data = {
            'description': '',
            'skills': [],
            'eligibility': '',
            'process': '',
            'salary': '',
        }
        
        try:
            search_url = f"https://www.naukri.com/{company_name.lower().replace(' ', '-')}-jobs"
            response = self._fetch_with_retry(search_url)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract job descriptions
                job_cards = soup.find_all('div', class_=re.compile('job|listing'), limit=5)
                all_skills = set()
                
                for card in job_cards:
                    text = card.get_text(strip=True).lower()
                    
                    # Extract skills
                    skills_keywords = [
                        'python', 'java', 'javascript', 'react', 'angular', 'sql',
                        'aws', 'docker', 'kubernetes', 'machine learning',
                    ]
                    for skill in skills_keywords:
                        if skill in text:
                            all_skills.add(skill.title())
                    
                    # Extract salary
                    salary_match = re.search(r'(\d+\.?\d*)\s*(lpa|lakh)', text, re.IGNORECASE)
                    if salary_match and not data['salary']:
                        data['salary'] = f"{salary_match.group(1)} {salary_match.group(2).upper()}"
                
                data['skills'] = list(all_skills)[:15]
        
        except Exception as e:
            logger.error(f"Error scraping Naukri: {e}")
        
        return data
    
    def scrape_all_sources(self, company_name: str, official_url: Optional[str] = None) -> Dict:
        """
        Scrape from all sources and merge data.
        Returns comprehensive company information.
        """
        logger.info(f"Scraping information for: {company_name}")
        
        merged_data = {
            'description': '',
            'skills': [],
            'eligibility': '',
            'process': '',
            'salary': '',
            'location': '',
            'collectedFrom': 'scraped',
        }
        
        # Scrape official website
        if official_url:
            official_data = self.scrape_official_website(official_url, company_name)
            merged_data.update(official_data)
        else:
            # Search for official website
            found_url = self._search_company_website(company_name)
            if found_url:
                official_data = self.scrape_official_website(found_url, company_name)
                merged_data.update(official_data)
        
        # Scrape Ambitionbox
        ambitionbox_data = self.scrape_ambitionbox(company_name)
        if ambitionbox_data.get('process') and not merged_data.get('process'):
            merged_data['process'] = ambitionbox_data['process']
        if ambitionbox_data.get('salary') and not merged_data.get('salary'):
            merged_data['salary'] = ambitionbox_data['salary']
        
        # Scrape GeeksForGeeks
        gfg_data = self.scrape_geeksforgeeks(company_name)
        if gfg_data.get('process'):
            if merged_data.get('process'):
                merged_data['process'] += '\n\n' + gfg_data['process']
            else:
                merged_data['process'] = gfg_data['process']
        if gfg_data.get('skills'):
            merged_data['skills'].extend(gfg_data['skills'])
        
        # Scrape Naukri
        naukri_data = self.scrape_naukri(company_name)
        if naukri_data.get('skills'):
            merged_data['skills'].extend(naukri_data['skills'])
        if naukri_data.get('salary') and not merged_data.get('salary'):
            merged_data['salary'] = naukri_data['salary']
        
        # Clean and deduplicate
        merged_data['skills'] = list(set(merged_data['skills']))[:20]
        merged_data['description'] = merged_data.get('description', '')[:500]
        merged_data['process'] = merged_data.get('process', '')[:1000]
        merged_data['eligibility'] = merged_data.get('eligibility', '')[:300]
        merged_data['salary'] = merged_data.get('salary', '')[:200]
        merged_data['location'] = merged_data.get('location', '')[:200]
        
        return merged_data

