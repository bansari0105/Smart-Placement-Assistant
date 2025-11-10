# backend/app/routes/companies.py
import logging
from flask import Blueprint, jsonify, request
from app.services.firebase_service import get_db, verify_user_token, token_required
from app.services.scraper_service import ScraperService
from firebase_admin import firestore

logger = logging.getLogger(__name__)
companies_bp = Blueprint("companies_bp", __name__)

@companies_bp.route("/", methods=["GET"])
def list_companies():
    """List all companies from companies collection (admin-inserted records)"""
    try:
        db = get_db()
        # Fetch from companies collection (admin-inserted)
        docs = db.collection("companies").get()
        companies = []
        for doc in docs:
            c = doc.to_dict()
            c["id"] = doc.id
            companies.append(c)
        return jsonify({"companies": companies}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@companies_bp.route("/scrape-company", methods=["POST"])
@token_required
def scrape_company_by_id():
    """
    Scrape a company by companyId.
    Looks up company from companies collection, then scrapes and saves to companies_scraped.
    
    Request JSON:
    {
        "companyId": "<company_id>"
    }
    """
    try:
        data = request.get_json() or {}
        company_id = data.get("companyId")
        
        if not company_id:
            return jsonify({"error": "Missing companyId"}), 400
        
        db = get_db()
        
        # Get company record from companies collection
        company_doc = db.collection("companies").document(company_id).get()
        if not company_doc.exists:
            return jsonify({"error": "Company not found"}), 404
        
        company_data = company_doc.to_dict()
        company_name = company_data.get("company_name") or company_data.get("name")
        optional_url = company_data.get("optional_url")
        
        if not company_name:
            return jsonify({"error": "Company name not found"}), 400
        
        # Initialize scraper
        scraper = ScraperService(db)
        
        # Scrape company (with URL if provided, otherwise search by name)
        success = scraper.scrape_and_save(
            company_id=company_id,
            url=optional_url,
            company_name=company_name
        )
        
        if success:
            # Get the scraped data
            scraped_doc = db.collection("companies_scraped").document(company_id).get()
            if scraped_doc.exists:
                scraped_data = scraped_doc.to_dict()
                scraped_data["id"] = company_id
                return jsonify({
                    "message": "Company scraped successfully",
                    "company": scraped_data
                }), 200
            else:
                return jsonify({
                    "message": "Scraping completed but data not found"
                }), 200
        else:
            return jsonify({"error": "Failed to scrape company"}), 500
            
    except Exception as e:
        logger.error(f"Error scraping company: {e}")
        return jsonify({"error": str(e)}), 500

@companies_bp.route("/scraped/<company_id>", methods=["GET"])
def get_scraped_company(company_id):
    """Get scraped company data from companies_scraped collection"""
    try:
        db = get_db()
        doc = db.collection("companies_scraped").document(company_id).get()
        if doc.exists:
            c = doc.to_dict()
            c["id"] = doc.id
            return jsonify(c), 200
        else:
            return jsonify({"error": "Scraped company data not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@companies_bp.route("/<company_id>", methods=["GET"])
def get_company(company_id):
    """Get company record from companies collection (admin-inserted)"""
    try:
        db = get_db()
        doc = db.collection("companies").document(company_id).get()
        if doc.exists:
            c = doc.to_dict()
            c["id"] = doc.id
            return jsonify(c), 200
        else:
            return jsonify({"error": "Company not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@companies_bp.route("/", methods=["POST"])
@token_required
def create_company():
    """
    Create a new company record (admin only).
    Required fields: company_name, visit_date, visit_time
    Optional fields: optional_url
    """
    data = request.get_json() or {}
    company_name = data.get("company_name")
    visit_date = data.get("visit_date")
    visit_time = data.get("visit_time")
    optional_url = data.get("optional_url", "")
    
    if not company_name or not visit_date or not visit_time:
        return jsonify({"error": "Missing required fields: company_name, visit_date, visit_time"}), 400
    
    try:
        db = get_db()
        doc_ref = db.collection("companies").document()
        doc_ref.set({
            "company_name": company_name,
            "visit_date": visit_date,
            "visit_time": visit_time,
            "optional_url": optional_url,
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        return jsonify({
            "message": "Company created successfully",
            "id": doc_ref.id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@companies_bp.route("/<company_id>", methods=["PUT"])
@token_required
def update_company(company_id):
    """Update company info (protected)"""
    data = request.get_json() or {}
    try:
        db = get_db()
        ref = db.collection("companies").document(company_id)
        ref.update(data)
        return jsonify({"message": "Company updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@companies_bp.route("/<company_id>", methods=["DELETE"])
@token_required
def delete_company(company_id):
    """Delete company (protected)"""
    try:
        db = get_db()
        db.collection("companies").document(company_id).delete()
        return jsonify({"message": "Company deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
