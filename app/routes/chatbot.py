"""
Chatbot API Endpoint
POST /chatbot/query - Process user queries with AI, NLP, and web scraping
POST /chatbot/smart-query - Smart query with automatic scraping for ANY company
"""
import logging
from flask import Blueprint, jsonify, request
from app.services.firebase_service import get_db, token_required
from app.services.chatbot_engine import ChatbotEngine
from app.services.chatbot_scraper import ChatbotScraper
from app.services.scraper_company import CompanyScraper
from firebase_admin import firestore

logger = logging.getLogger(__name__)
chatbot_bp = Blueprint("chatbot_bp", __name__)


@chatbot_bp.route("/smart-query", methods=["POST"])
@token_required
def smart_query():
    """
    Smart query endpoint that automatically scrapes ANY company name.
    
    Request JSON:
    {
        "userMessage": "what is meril?"
    }
    
    Response:
    {
        "companyName": "Meril",
        "source": "scraped" | "knowledge_base",
        "data": {
            "description": "...",
            "skills": [...],
            "eligibility": "...",
            "process": "...",
            "salary": "..."
        },
        "response": "<formatted answer>"
    }
    """
    try:
        uid = request.user["uid"]
        data = request.get_json() or {}
        
        user_message = data.get("userMessage", "").strip()
        userId = data.get("userId") or uid
        
        if not user_message:
            return jsonify({"error": "Missing userMessage"}), 400
        
        db = get_db()
        engine = ChatbotEngine(db)
        
        # Extract company name from message
        company_name = engine.extract_company_name(user_message)
        
        if not company_name:
            return jsonify({
                "error": "Could not extract company name from message",
                "response": "Please mention a company name. For example: 'What is Meril?' or 'Tell me about Deloitte'"
            }), 400
        
        logger.info(f"Extracted company name: {company_name}")
        
        # Check knowledge base first
        knowledge = engine.search_knowledge_base(user_message, company_name)
        intent, _ = engine.classify_intent(user_message)
        message_lower = user_message.lower()
        
        # Check if specific data is missing for the requested intent
        needs_scraping = False
        if knowledge:
            # If asking for skills but skills data is missing/empty
            if (intent == 'skills' or 'skill' in message_lower) and \
               (not knowledge.get('skills') or len(knowledge.get('skills', [])) == 0):
                needs_scraping = True
                logger.info(f"Skills requested but missing for {company_name}, triggering scrape")
            
            # If asking for interview process but process data is missing/empty
            if (intent == 'interview' or 'interview process' in message_lower or 
                ('interview' in message_lower and 'process' in message_lower)) and \
               (not knowledge.get('process') or len(knowledge.get('process', '')) < 50):
                needs_scraping = True
                logger.info(f"Interview process requested but missing for {company_name}, triggering scrape")
            
            # If asking for location but location data is missing
            if (intent == 'location' or 'where' in message_lower or 'located' in message_lower) and \
               (not knowledge.get('location') or len(knowledge.get('location', '')) < 3):
                needs_scraping = True
                logger.info(f"Location requested but missing for {company_name}, triggering scrape")
        
        if knowledge and not needs_scraping:
            # Return from knowledge base
            return jsonify({
                "companyName": company_name,
                "source": "knowledge_base",
                "data": {
                    "description": knowledge.get('description', ''),
                    "skills": knowledge.get('skills', []),
                    "eligibility": knowledge.get('eligibility', ''),
                    "process": knowledge.get('process', ''),
                    "salary": knowledge.get('salary', ''),
                    "location": knowledge.get('location', ''),
                },
                "response": engine.generate_response_from_knowledge(intent, knowledge, user_message)
            }), 200
        
        # Not in knowledge base - trigger scraping
        logger.info(f"Company {company_name} not in knowledge base. Triggering scraping...")
        
        try:
            # Use dedicated CompanyScraper
            company_scraper = CompanyScraper(db)
            
            # Get optional URL from companies collection
            optional_url = None
            try:
                companies = db.collection('companies').where(
                    'company_name', '==', company_name
                ).limit(1).get()
                if companies:
                    optional_url = companies[0].to_dict().get('optional_url')
            except Exception as e:
                logger.debug(f"Could not get optional URL: {e}")
            
            # Scrape company using dedicated scraper
            scraped_data = company_scraper.scrape_company(company_name, optional_url)
            
            # Save to Firestore automatically (only if data quality is good)
            save_success = company_scraper.save_to_firestore(company_name, scraped_data)
            if not save_success:
                logger.warning(f"Did not save {company_name} to knowledge base - data quality too low")
            
            # Ensure all required fields exist
            if not scraped_data.get('description'):
                scraped_data['description'] = f"{company_name} is a company. Detailed information is being gathered."
            if not scraped_data.get('skills'):
                scraped_data['skills'] = []
            if not scraped_data.get('eligibility'):
                scraped_data['eligibility'] = "Eligibility criteria will be updated soon."
            if not scraped_data.get('process'):
                scraped_data['process'] = "Interview process details will be updated soon."
            if not scraped_data.get('salary'):
                scraped_data['salary'] = "Salary information will be updated soon."
            
            # Save to knowledge base
            success = engine.save_to_knowledge_base(company_name, scraped_data)
            
            if not success:
                logger.warning(f"Failed to save {company_name} to knowledge base")
            
            # Generate formatted response
            intent, _ = engine.classify_intent(user_message)
            formatted_response = engine.generate_response_from_knowledge(
                intent,
                scraped_data,
                user_message
            )
            
            # Save chat log
            engine.save_chat_log(
                userId,
                user_message,
                formatted_response,
                {
                    'intent': intent,
                    'company_name': company_name,
                    'source': 'scraped',
                }
            )
            
            return jsonify({
                "companyName": company_name,
                "source": "scraped",
                "data": {
                    "description": scraped_data.get('description', ''),
                    "skills": scraped_data.get('skills', []),
                    "eligibility": scraped_data.get('eligibility', ''),
                    "process": scraped_data.get('process', ''),
                    "salary": scraped_data.get('salary', ''),
                    "location": scraped_data.get('location', ''),
                },
                "response": formatted_response
            }), 200
            
        except Exception as e:
            logger.error(f"Error during scraping for {company_name}: {e}")
            return jsonify({
                "error": f"Failed to scrape information for {company_name}",
                "companyName": company_name,
                "source": "error",
                "response": f"I encountered an error while gathering information about {company_name}. Please try again later."
            }), 500
        
    except Exception as e:
        logger.error(f"Error in smart_query: {e}")
        return jsonify({
            "error": str(e),
            "response": "I apologize, but I encountered an error. Please try again."
        }), 500


@chatbot_bp.route("/query", methods=["POST"])
@token_required
def process_query():
    """
    Process chatbot query with NLP, knowledge base search, and web scraping.
    
    Request JSON:
    {
        "userId": "<user_id>",
        "message": "What skills does TCS need?"
    }
    
    Response:
    {
        "response": "<AI processed answer>",
        "source": "firestore" | "scraped" | "ai",
        "intent": "<intent>",
        "company_name": "<company_name>" or null
    }
    """
    try:
        uid = request.user["uid"]
        data = request.get_json() or {}
        
        message = data.get("message", "").strip()
        userId = data.get("userId") or uid
        
        if not message:
            return jsonify({"error": "Missing message"}), 400
        
        db = get_db()
        engine = ChatbotEngine(db)
        
        # Process query with NLP and intent classification
        result = engine.process_query(userId, message)
        
        # If scraping is needed, trigger it
        if result.get('needs_scraping') and result.get('company_name'):
            company_name = result['company_name']
            intent = result.get('intent', 'general')
            logger.info(f"Triggering scraping for: {company_name} (intent: {intent})")
            
            try:
                scraper = ChatbotScraper()
                
                # Get optional URL from companies collection
                optional_url = None
                try:
                    companies = db.collection('companies').where(
                        'company_name', '==', company_name
                    ).limit(1).get()
                    if companies:
                        optional_url = companies[0].to_dict().get('optional_url')
                except Exception as e:
                    logger.debug(f"Could not get optional URL: {e}")
                
                # Scrape from all sources
                scraped_data = scraper.scrape_all_sources(company_name, optional_url)
                
                # Save to knowledge base (merge with existing data if any)
                engine.save_to_knowledge_base(company_name, scraped_data)
                
                # Re-process query with updated knowledge base
                result = engine.process_query(userId, message)
                
                # If still no good response, provide ChatGPT-like fallback
                if not result.get('response') or len(result.get('response', '')) < 50:
                    knowledge = engine.search_knowledge_base(message, company_name)
                    if knowledge:
                        result['response'] = engine.generate_response_from_knowledge(intent, knowledge, message)
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                # ChatGPT-like: Still provide helpful response even on error
                knowledge = engine.search_knowledge_base(message, company_name)
                if knowledge:
                    result['response'] = engine.generate_response_from_knowledge(intent, knowledge, message)
                else:
                    result['response'] = (
                        f"I encountered an error while gathering information about {company_name}. "
                        f"However, here's what I can tell you:\n\n"
                        f"**About {company_name}:**\n"
                        f"To get the most accurate information, I recommend:\n"
                        f"• Visiting {company_name}'s official careers page\n"
                        f"• Checking job postings on LinkedIn, Naukri, or Indeed\n"
                        f"• Reading interview experiences on Glassdoor or GeeksforGeeks\n\n"
                        f"Would you like to try asking again, or ask a different question?"
                    )
                result['source'] = 'ai'
        
        # Save chat log
        engine.save_chat_log(
            userId,
            message,
            result['response'],
            {
                'intent': result.get('intent'),
                'company_name': result.get('company_name'),
                'source': result.get('source'),
            }
        )
        
        return jsonify({
            "response": result['response'],
            "source": result.get('source', 'ai'),
            "intent": result.get('intent', 'general'),
            "company_name": result.get('company_name'),
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing chatbot query: {e}")
        return jsonify({
            "error": str(e),
            "response": "I apologize, but I encountered an error. Please try again.",
            "source": "ai"
        }), 500


@chatbot_bp.route("/history", methods=["GET"])
@token_required
def get_chat_history():
    """Get chat history for the authenticated user."""
    try:
        uid = request.user["uid"]
        db = get_db()
        
        limit = request.args.get('limit', 50, type=int)
        
        logs = db.collection('chat_logs').where(
            'userId', '==', uid
        ).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).get()
        
        history = []
        for log in logs:
            log_data = log.to_dict()
            log_data['id'] = log.id
            history.append(log_data)
        
        history.reverse()  # Oldest first
        
        return jsonify({"history": history}), 200
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        return jsonify({"error": str(e)}), 500


@chatbot_bp.route("/knowledge-base/<company_name>", methods=["GET"])
@token_required
def get_knowledge_base_entry(company_name):
    """Get knowledge base entry for a company."""
    try:
        db = get_db()
        
        docs = db.collection('company_knowledge_base').where(
            'companyName', '==', company_name
        ).limit(1).get()
        
        if docs:
            data = docs[0].to_dict()
            data['id'] = docs[0].id
            return jsonify(data), 200
        else:
            return jsonify({"error": "Company not found in knowledge base"}), 404
            
    except Exception as e:
        logger.error(f"Error fetching knowledge base: {e}")
        return jsonify({"error": str(e)}), 500
