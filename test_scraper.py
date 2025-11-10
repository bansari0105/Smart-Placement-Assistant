"""
Test script for the scraper service.
Run this to test the scraper locally.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.scraper_service import parse_company_html, ScraperService
from firebase_admin import credentials, firestore, initialize_app
import json

def test_parser():
    """Test the HTML parser with a sample HTML"""
    sample_html = """
    <html>
    <head>
        <title>Tech Company Inc. - Careers</title>
        <meta name="description" content="Leading tech company offering software development roles">
    </head>
    <body>
        <h1>Tech Company Inc.</h1>
        <p class="description">We are a leading technology company specializing in software development.</p>
        <div class="location">San Francisco, CA</div>
        <a href="mailto:contact@techcompany.com">contact@techcompany.com</a>
        <a href="/careers">Careers</a>
        <a href="/jobs">Jobs</a>
    </body>
    </html>
    """
    
    url = "https://techcompany.com"
    result = parse_company_html(sample_html, url)
    
    print("Parsing Test Results:")
    print(json.dumps(result, indent=2, default=str))
    return result

def test_scraper_with_firestore():
    """Test the scraper with Firestore (requires service account key)"""
    try:
        # Initialize Firebase
        cred = credentials.Certificate('serviceaccountkey.json')
        app = initialize_app(cred)
        db = firestore.client()
        
        # Test scraping
        scraper = ScraperService(db)
        test_url = "https://www.google.com"  # Replace with actual company URL
        company_data = scraper.scrape_company(test_url)
        
        if company_data:
            print("Scraping Test Results:")
            print(json.dumps(company_data, indent=2, default=str))
            
            # Save to Firestore
            doc_id = scraper.save_to_firestore(company_data)
            print(f"\nSaved to Firestore with ID: {doc_id}")
        else:
            print("Failed to scrape company data")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure serviceaccountkey.json is in the backend directory")

if __name__ == "__main__":
    print("=" * 50)
    print("Scraper Test Script")
    print("=" * 50)
    
    # Test 1: Parser (no Firebase needed)
    print("\n1. Testing HTML Parser...")
    test_parser()
    
    # Test 2: Full scraper with Firestore (requires Firebase setup)
    print("\n2. Testing Full Scraper with Firestore...")
    print("(Skipping - requires Firebase setup)")
    # Uncomment to test with Firestore:
    # test_scraper_with_firestore()

